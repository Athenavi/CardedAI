"""
引擎优化器

为情报/知识/工作流引擎提供共享的性能组件：
- 采集任务队列（Redis Streams，Redis 不可用时自动降级为内存队列）
- RAG 搜索缓存（带 TTL 与集合级失效）
- 工作流并发控制
- 批量 Embedding 处理器（带真实统计）
"""

import asyncio
import json
import os
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.unified_logger import default_logger as logger


# ============ Collection Task ============

@dataclass
class CollectionTask:
    """采集任务

    入队时通常只需要 ``source_id``；``source_type`` / ``url`` 会在消费端由
    ``CollectorEngine.run_collection`` 依据数据源配置从数据库读取，因此这里
    允许为空，避免入队阶段因缺少展示性字段而失败。
    """
    source_id: int
    source_type: str = ''
    url: str = ''
    config: dict = field(default_factory=dict)
    task_id: Optional[str] = None
    status: str = 'pending'
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'source_id': self.source_id,
            'source_type': self.source_type,
            'url': self.url,
            'config': self.config,
            'status': self.status,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CollectionTask':
        return cls(
            source_id=data['source_id'],
            source_type=data.get('source_type', ''),
            url=data.get('url', ''),
            config=data.get('config', {}) or {},
            task_id=data.get('task_id'),
            status=data.get('status', 'pending'),
            created_at=float(data.get('created_at') or 0.0),
        )


# ============ Queue Backends ============

class _QueueBackend:
    """队列后端抽象"""

    mode = 'abstract'

    async def enqueue(self, task: CollectionTask) -> str:
        raise NotImplementedError

    async def dequeue(self, count: int = 1, block_ms: int = 5000) -> List[Tuple[str, CollectionTask]]:
        raise NotImplementedError

    async def ack(self, msg_id: str) -> None:
        raise NotImplementedError

    async def pending_count(self) -> int:
        raise NotImplementedError

    async def close(self) -> None:
        return None


class _InMemoryQueueBackend(_QueueBackend):
    """内存队列后端（Redis 不可用时的降级方案）"""

    mode = 'memory'

    def __init__(self) -> None:
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: Dict[str, CollectionTask] = {}

    @staticmethod
    def _new_task_id() -> str:
        return f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"

    async def enqueue(self, task: CollectionTask) -> str:
        if not task.task_id:
            task.task_id = self._new_task_id()
        if not task.created_at:
            task.created_at = time.time()
        self._tasks[task.task_id] = task
        await self._queue.put(task)
        return task.task_id

    async def dequeue(self, count: int = 1, block_ms: int = 5000) -> List[Tuple[str, CollectionTask]]:
        results: List[Tuple[str, CollectionTask]] = []
        deadline = time.time() + block_ms / 1000
        for _ in range(count):
            remaining = deadline - time.time()
            if remaining <= 0 and results:
                break
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=max(0.001, remaining))
            except asyncio.TimeoutError:
                break
            results.append((task.task_id, task))
        return results

    async def ack(self, msg_id: str) -> None:
        self._tasks.pop(msg_id, None)

    async def pending_count(self) -> int:
        return self._queue.qsize()


class _RedisStreamsQueueBackend(_QueueBackend):
    """Redis Streams 队列后端

    使用消费者组（consumer group）保证：
    - 多消费者并发消费不重复
    - 未 ACK 的消息进入 PEL，可被重新投递
    """

    mode = 'redis'
    STREAM_KEY = 'intel:collection:tasks'
    GROUP_NAME = 'intel-collectors'

    def __init__(self, client: Any) -> None:
        self._client = client
        self._consumer = f"collector-{os.getpid()}-{uuid.uuid4().hex[:6]}"

    async def ensure_group(self) -> None:
        """创建消费者组（stream 不存在时自动创建）"""
        try:
            await self._client.xgroup_create(
                self.STREAM_KEY, self.GROUP_NAME, id='0', mkstream=True
            )
        except Exception as e:  # BUSYGROUP 表示组已存在，属正常情况
            if 'BUSYGROUP' not in str(e):
                raise

    async def enqueue(self, task: CollectionTask) -> str:
        if not task.task_id:
            task.task_id = f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
        if not task.created_at:
            task.created_at = time.time()
        msg_id = await self._client.xadd(
            self.STREAM_KEY,
            {'payload': json.dumps(task.to_dict(), ensure_ascii=False)},
        )
        task.task_id = msg_id
        return msg_id

    async def dequeue(self, count: int = 1, block_ms: int = 5000) -> List[Tuple[str, CollectionTask]]:
        try:
            resp = await self._client.xreadgroup(
                self.GROUP_NAME, self._consumer,
                {self.STREAM_KEY: '>'},
                count=count, block=block_ms,
            )
        except Exception as e:
            logger.error(f"Redis Streams 读取失败: {e}")
            return []

        results: List[Tuple[str, CollectionTask]] = []
        for _stream, entries in (resp or []):
            for msg_id, fields in entries:
                try:
                    payload = fields.get('payload', '{}')
                    task = CollectionTask.from_dict(json.loads(payload))
                    task.task_id = msg_id
                    results.append((msg_id, task))
                except Exception as e:
                    logger.error(f"解析采集任务失败 msg_id={msg_id}: {e}")
                    await self.ack(msg_id)
        return results

    async def ack(self, msg_id: str) -> None:
        try:
            await self._client.xack(self.STREAM_KEY, self.GROUP_NAME, msg_id)
        except Exception as e:
            logger.error(f"Redis Streams ACK 失败 msg_id={msg_id}: {e}")

    async def pending_count(self) -> int:
        try:
            return int(await self._client.xlen(self.STREAM_KEY))
        except Exception:
            return 0

    async def close(self) -> None:
        try:
            await self._client.aclose()
        except Exception:
            pass


def _redis_config() -> Dict[str, Any]:
    """从环境变量构建 Redis 连接参数（与 token 黑名单保持一致）"""
    return {
        'host': os.environ.get('REDIS_HOST', 'localhost'),
        'port': int(os.environ.get('REDIS_PORT', 6379)),
        'db': int(os.environ.get('REDIS_DB', 0)),
        'password': os.environ.get('REDIS_PASSWORD') or None,
    }


async def _try_connect_redis() -> Optional[Any]:
    """尝试建立 Redis 异步连接；失败返回 None（由调用方降级）"""
    try:
        import redis.asyncio as aioredis
    except ImportError:
        logger.info("redis.asyncio 不可用，采集任务队列使用内存后端")
        return None

    client = None
    try:
        client = aioredis.Redis(
            **_redis_config(),
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=2,
        )
        await client.ping()
        return client
    except Exception as e:
        logger.info(f"Redis 连接不可用，采集任务队列降级为内存后端: {e}")
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass
        return None


# ============ Collection Task Queue ============

class CollectionTaskQueue:
    """采集任务队列门面

    首次使用时尝试连接 Redis 并切换到 Streams 后端；
    若 Redis 不可用则透明降级为进程内内存队列。
    """

    def __init__(self) -> None:
        self._stats: Dict[str, int] = {
            'enqueued': 0,
            'dequeued': 0,
            'acked': 0,
            'completed': 0,
            'success': 0,
            'failed': 0,
        }
        self._memory = _InMemoryQueueBackend()
        self._backend: _QueueBackend = self._memory
        self._redis_backend: Optional[_RedisStreamsQueueBackend] = None
        self._redis_checked = False
        self._lock = asyncio.Lock()

    async def _ensure_backend(self) -> None:
        if self._redis_checked:
            return
        async with self._lock:
            if self._redis_checked:
                return
            client = await _try_connect_redis()
            if client is not None:
                backend = _RedisStreamsQueueBackend(client)
                try:
                    await backend.ensure_group()
                    self._redis_backend = backend
                    self._backend = backend
                    logger.info("采集任务队列已启用 Redis Streams 后端")
                except Exception as e:
                    logger.warning(f"Redis Streams 初始化失败，降级为内存队列: {e}")
                    await backend.close()
            else:
                logger.info("采集任务队列使用内存后端")
            self._redis_checked = True

    @property
    def mode(self) -> str:
        """当前生效的后端类型：'redis' 或 'memory'"""
        return self._backend.mode

    async def enqueue(self, task: CollectionTask) -> str:
        await self._ensure_backend()
        msg_id = await self._backend.enqueue(task)
        self._stats['enqueued'] += 1
        return msg_id

    async def dequeue(self, count: int = 1, block_ms: int = 5000) -> List[Tuple[str, CollectionTask]]:
        await self._ensure_backend()
        results = await self._backend.dequeue(count=count, block_ms=block_ms)
        self._stats['dequeued'] += len(results)
        return results

    async def ack(self, msg_id: str) -> None:
        await self._ensure_backend()
        await self._backend.ack(msg_id)
        self._stats['acked'] += 1

    async def report_result(self, task: CollectionTask, result: dict) -> None:
        """记录任务执行结果（供统计端点使用）"""
        self._stats['completed'] += 1
        succeeded = bool(result.get('success')) or result.get('status') == 'completed'
        if succeeded:
            self._stats['success'] += 1
        else:
            self._stats['failed'] += 1

    async def pending_count(self) -> int:
        await self._ensure_backend()
        return await self._backend.pending_count()

    def get_stats(self) -> dict:
        stats = dict(self._stats)
        stats['backend'] = self._backend.mode
        return stats

    async def close(self) -> None:
        if self._redis_backend is not None:
            await self._redis_backend.close()


# ============ RAG Cache ============

def _make_cache_key(collection: str, query: str, top_k: int, filters: Optional[dict]) -> str:
    """构造缓存键

    使用 NUL 作为分隔符，避免集合名互为前缀（如 kb_1 / kb_10）时误命中。
    """
    filter_part = json.dumps(filters, sort_keys=True, ensure_ascii=False) if filters else ''
    return f"{collection}\x00{query}\x00{top_k}\x00{filter_part}"


class RAGCacheService:
    """内存 RAG 检索缓存（带 TTL 与集合级失效）"""

    def __init__(self, default_ttl: int = 300) -> None:
        self._cache: Dict[str, dict] = {}
        self._stats = {'hits': 0, 'misses': 0, 'evictions': 0, 'sets': 0}
        self._default_ttl = default_ttl

    async def get_cached_search(self, collection: str, query: str, top_k: int,
                                filters: Optional[dict] = None) -> Optional[list]:
        key = _make_cache_key(collection, query, top_k, filters)
        entry = self._cache.get(key)
        if entry is None:
            self._stats['misses'] += 1
            return None
        if entry['expires'] <= time.time():
            self._cache.pop(key, None)
            self._stats['evictions'] += 1
            self._stats['misses'] += 1
            return None
        self._stats['hits'] += 1
        return entry['results']

    async def set_cached_search(self, collection: str, query: str, top_k: int,
                                results: list, filters: Optional[dict] = None,
                                ttl: Optional[int] = None) -> None:
        key = _make_cache_key(collection, query, top_k, filters)
        self._cache[key] = {
            'results': results,
            'expires': time.time() + (ttl if ttl is not None else self._default_ttl),
        }
        self._stats['sets'] += 1

    async def invalidate_collection(self, collection: str) -> None:
        prefix = f"{collection}\x00"
        self._cache = {k: v for k, v in self._cache.items() if not k.startswith(prefix)}

    def purge_expired(self) -> int:
        """清理已过期条目，返回清理数量"""
        now = time.time()
        expired = [k for k, v in self._cache.items() if v['expires'] <= now]
        for k in expired:
            self._cache.pop(k, None)
        self._stats['evictions'] += len(expired)
        return len(expired)

    def get_stats(self) -> dict:
        stats = dict(self._stats)
        stats['size'] = len(self._cache)
        return stats

    def clear(self) -> None:
        self._cache.clear()


# ============ Concurrency Manager ============

class ConcurrencyManager:
    """并发控制管理器"""

    def __init__(self, max_concurrent_nodes: int = 10, max_concurrent_workflows: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent_nodes)
        self._active_workflows: set = set()
        self._max_workflows = max_concurrent_workflows
        self._stats = defaultdict(int)

    async def acquire_workflow(self, workflow_id: int) -> bool:
        if len(self._active_workflows) >= self._max_workflows:
            return False
        self._active_workflows.add(workflow_id)
        return True

    def release_workflow(self, workflow_id: int) -> None:
        self._active_workflows.discard(workflow_id)

    async def run_node_with_limit(self, coro, node_id: str, node_type: str = ''):
        async with self._semaphore:
            start = time.time()
            try:
                result = await coro
                self._stats['success'] += 1
                return result
            except Exception:
                self._stats['failed'] += 1
                raise
            finally:
                elapsed = time.time() - start
                self._stats[f'type_{node_type}_total'] += elapsed
                self._stats[f'type_{node_type}_count'] += 1

    def active_workflow_count(self) -> int:
        return len(self._active_workflows)

    def get_stats(self) -> dict:
        stats = dict(self._stats)
        stats['active_workflows'] = len(self._active_workflows)
        return stats


# ============ Batch Embedding Processor ============

@dataclass
class EmbeddingJob:
    """嵌入任务

    ``texts`` 为待嵌入文本；``ids`` / ``collection_name`` / ``metadata``
    在需要写入向量库时提供。
    """
    texts: List[str]
    ids: Optional[List[str]] = None
    collection_name: Optional[str] = None
    metadata: Optional[List[Dict[str, Any]]] = None
    callback: Optional[Any] = None
    job_id: Optional[str] = None


class BatchEmbeddingProcessor:
    """批量 Embedding 处理器

    将文本按 batch_size 分批嵌入；当同时提供 ``collection_name`` 与
    ``vector_store`` 时，会把向量（含 chunk 元数据）写入向量库。
    记录提交/批次/文本数/已嵌入数/已入库数与失败数等真实统计。
    """

    def __init__(self, embedding_service=None, vector_store=None, batch_size: int = 16):
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._batch_size = max(1, int(batch_size))
        self._running = False
        self._stats = {
            'submitted': 0, 'batches': 0, 'texts': 0,
            'embedded': 0, 'stored': 0, 'failed': 0,
        }

    async def start(self) -> None:
        """标记处理器为运行状态"""
        self._running = True
        logger.info(f"BatchEmbeddingProcessor started (batch_size={self._batch_size})")

    async def stop(self) -> None:
        self._running = False
        logger.info("BatchEmbeddingProcessor stopped")

    async def submit(self, job: EmbeddingJob) -> Dict[str, Any]:
        """处理嵌入任务（分批嵌入 + 可选写入向量库）"""
        return await self.process_immediate(
            texts=job.texts,
            ids=job.ids,
            collection_name=job.collection_name,
            metadata=job.metadata,
        )

    async def process_immediate(
        self,
        texts: List[str],
        ids: Optional[List[str]] = None,
        collection_name: Optional[str] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """分批嵌入（并在需要时写入向量库），返回处理统计"""
        if not self._embedding_service or not texts:
            return {'status': 'completed', 'texts_embedded': 0, 'batches': 0, 'stored': 0}

        self._stats['submitted'] += 1
        total = len(texts)
        embedded_count = 0
        stored_count = 0
        batches = 0
        errors = 0

        for offset in range(0, total, self._batch_size):
            batch = texts[offset:offset + self._batch_size]
            batch_ids = ids[offset:offset + self._batch_size] if ids else None
            batch_meta = metadata[offset:offset + self._batch_size] if metadata else None

            try:
                vectors = await self._embedding_service.embed(batch)
                if not vectors:
                    raise ValueError("embedding 服务返回空结果")
            except Exception as e:
                logger.error(f"批量嵌入失败 (offset={offset}): {e}")
                errors += 1
                continue

            batches += 1
            embedded_count += len(vectors)
            self._stats['embedded'] += len(vectors)

            # 可选：写入向量库
            if collection_name and self._vector_store:
                metas: List[Dict[str, Any]] = []
                for i in range(len(vectors)):
                    meta = dict(batch_meta[i]) if batch_meta and i < len(batch_meta) else {}
                    if batch_ids and i < len(batch_ids) and 'chunk_id' not in meta:
                        meta['chunk_id'] = batch_ids[i]
                    metas.append(meta)
                try:
                    await self._vector_store.insert(collection_name, vectors, metas)
                    stored_count += len(vectors)
                    self._stats['stored'] += len(vectors)
                except Exception as e:
                    logger.error(f"向量写入失败 (collection={collection_name}): {e}")
                    errors += 1

        self._stats['batches'] += batches
        self._stats['texts'] += total
        if errors:
            self._stats['failed'] += errors

        return {
            'status': 'completed',
            'texts_embedded': embedded_count,
            'batches': batches,
            'stored': stored_count,
        }

    def get_stats(self) -> dict:
        return dict(self._stats)


# ============ Factory Functions ============

_collection_queue: Optional[CollectionTaskQueue] = None
_rag_cache: Optional[RAGCacheService] = None
_batch_processor: Optional[BatchEmbeddingProcessor] = None
_concurrency_manager: Optional[ConcurrencyManager] = None


def get_collection_queue() -> CollectionTaskQueue:
    global _collection_queue
    if _collection_queue is None:
        _collection_queue = CollectionTaskQueue()
    return _collection_queue


def get_rag_cache() -> RAGCacheService:
    global _rag_cache
    if _rag_cache is None:
        _rag_cache = RAGCacheService()
    return _rag_cache


def get_concurrency_manager(max_concurrent_nodes: int = 10, max_concurrent_workflows: int = 5) -> ConcurrencyManager:
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager(max_concurrent_nodes, max_concurrent_workflows)
    return _concurrency_manager


def get_batch_processor(embedding_service=None, vector_store=None, batch_size: int = 16) -> BatchEmbeddingProcessor:
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchEmbeddingProcessor(embedding_service, vector_store, batch_size)
    return _batch_processor


def get_engine_stats() -> dict:
    """汇总引擎优化组件统计（供全局性能统计端点使用）"""
    return {
        'collection_queue': get_collection_queue().get_stats(),
        'rag_cache': get_rag_cache().get_stats(),
        'batch_embedding': _batch_processor.get_stats() if _batch_processor else {},
        'concurrency': _concurrency_manager.get_stats() if _concurrency_manager else {},
    }
