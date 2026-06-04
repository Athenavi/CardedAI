"""
FastBlog 性能优化引擎

覆盖4项核心优化:
1. 采集任务队列 (Redis Streams) — 分布式采集调度
2. RAG 检索缓存 (Redis) — 向量检索结果缓存 + 索引优化
3. 工作流并发控制 (asyncio.Semaphore) — 节点级并发限制
4. 批量 Embedding 处理 — 批量向量化 + 异步后台索引
"""

import asyncio
import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis 连接辅助
# ---------------------------------------------------------------------------

_redis_client = None
_redis_check_done = False  # 哨兵标记：防止失败后反复重试连接


def _get_redis():
    """延迟获取 Redis 客户端（兼容无 Redis 环境）"""
    global _redis_client, _redis_check_done
    if _redis_check_done:
        return _redis_client
    _redis_check_done = True
    try:
        import os
        import redis
        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", 6379))
        db = int(os.environ.get("REDIS_DB", 0))
        password = os.environ.get("REDIS_PASSWORD")
        _redis_client = redis.Redis(
            host=host, port=port, db=db,
            password=password, decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _redis_client.ping()
        logger.info("[EngineOptimizer] Redis 连接成功: %s:%s", host, port)
        return _redis_client
    except Exception as e:
        logger.warning("[EngineOptimizer] Redis 不可用 (%s), 降级为内存模式", e)
        _redis_client = None
        return None


# ═════════════════════════════════════════════════════════════════════════════
# 1. 采集任务队列 — Redis Streams
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class CollectionTask:
    """采集任务数据"""
    source_id: int
    source_type: str
    url: str
    config: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": str(self.source_id),
            "source_type": self.source_type,
            "url": self.url,
            "config": json.dumps(self.config),
            "priority": str(self.priority),
            "created_at": self.created_at or datetime.utcnow().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "CollectionTask":
        return cls(
            source_id=int(data.get("source_id", 0)),
            source_type=data.get("source_type", ""),
            url=data.get("url", ""),
            config=json.loads(data.get("config", "{}")),
            priority=int(data.get("priority", 0)),
            created_at=data.get("created_at", ""),
        )


class CollectionTaskQueue:
    """
    基于 Redis Streams 的采集任务队列

    - XADD 提交任务
    - XREADGROUP 消费任务（支持消费者组）
    - XACK 确认任务完成
    - 无 Redis 时降级为 asyncio.Queue
    """

    STREAM_KEY = "fastblog:collection:tasks"
    GROUP_NAME = "collectors"
    CONSUMER_PREFIX = "collector-"
    RESULT_STREAM = "fastblog:collection:results"
    MAX_STREAM_LEN = 10000

    def __init__(self, consumer_id: Optional[str] = None):
        self._redis = _get_redis()
        self._consumer_id = consumer_id or f"{self.CONSUMER_PREFIX}{int(time.time())}"
        self._fallback_queue: asyncio.Queue = asyncio.Queue()
        self._group_initialized = False

    def _ensure_group(self):
        """确保消费者组存在"""
        if self._group_initialized or self._redis is None:
            return
        try:
            self._redis.xgroup_create(
                self.STREAM_KEY, self.GROUP_NAME, id="0", mkstream=True
            )
        except Exception:
            pass  # 组已存在
        self._group_initialized = True

    async def enqueue(self, task: CollectionTask) -> Optional[str]:
        """提交采集任务到队列"""
        if self._redis:
            try:
                msg_id = self._redis.xadd(
                    self.STREAM_KEY,
                    task.to_dict(),
                    maxlen=self.MAX_STREAM_LEN,
                )
                logger.info("[CollectionQueue] 任务已入队: source=%d, id=%s", task.source_id, msg_id)
                return msg_id
            except Exception as e:
                logger.error("[CollectionQueue] Redis XADD 失败: %s", e)

        # 降级: asyncio.Queue
        await self._fallback_queue.put(task)
        logger.info("[CollectionQueue] 任务已入内存队列: source=%d", task.source_id)
        return None

    async def dequeue(self, count: int = 1, block_ms: int = 5000) -> List[Tuple[str, CollectionTask]]:
        """从队列消费任务"""
        if self._redis:
            self._ensure_group()
            try:
                entries = self._redis.xreadgroup(
                    self.GROUP_NAME,
                    self._consumer_id,
                    {self.STREAM_KEY: ">"},
                    count=count,
                    block=block_ms,
                )
                tasks = []
                if entries:
                    for stream_name, messages in entries:
                        for msg_id, fields in messages:
                            task = CollectionTask.from_dict(fields)
                            tasks.append((msg_id, task))
                return tasks
            except Exception as e:
                logger.error("[CollectionQueue] Redis XREADGROUP 失败: %s", e)
                return []

        # 降级: asyncio.Queue
        tasks = []
        for _ in range(count):
            try:
                task = await asyncio.wait_for(
                    self._fallback_queue.get(), timeout=block_ms / 1000
                )
                tasks.append((None, task))
            except asyncio.TimeoutError:
                break
        return tasks

    async def ack(self, msg_id: str):
        """确认任务完成"""
        if self._redis and msg_id:
            try:
                self._redis.xack(self.STREAM_KEY, self.GROUP_NAME, msg_id)
            except Exception as e:
                logger.error("[CollectionQueue] Redis XACK 失败: %s", e)

    async def report_result(self, task: CollectionTask, result: Dict[str, Any]):
        """提交采集结果到结果流"""
        payload = {
            "source_id": str(task.source_id),
            "status": result.get("status", "unknown"),
            "items_count": str(result.get("items_count", 0)),
            "error": result.get("error", ""),
            "completed_at": datetime.utcnow().isoformat(),
        }
        if self._redis:
            try:
                self._redis.xadd(
                    self.RESULT_STREAM, payload, maxlen=self.MAX_STREAM_LEN
                )
            except Exception:
                pass

    @property
    def pending_count(self) -> int:
        """队列中待处理任务数"""
        if self._redis:
            try:
                info = self._redis.xinfo_stream(self.STREAM_KEY)
                return info.get("length", 0)
            except Exception:
                return 0
        return self._fallback_queue.qsize()


# ═════════════════════════════════════════════════════════════════════════════
# 2. RAG 检索缓存
# ═════════════════════════════════════════════════════════════════════════════

class RAGCacheService:
    """
    RAG 检索结果缓存服务

    - 对语义搜索结果进行 Redis 缓存
    - 支持 TTL 过期 + 手动失效
    - 缓存键基于 (collection, query_hash, top_k) 生成
    """

    CACHE_PREFIX = "fastblog:rag:search:"
    DEFAULT_TTL = 600  # 10 分钟
    STALE_TTL = 1800   # 30 分钟（陈旧数据窗口）

    def __init__(self):
        self._redis = _get_redis()
        self._local_cache: Dict[str, Tuple[Any, float]] = {}
        self._local_ttl = 120  # 本地缓存 2 分钟
        self._stats = {"hits": 0, "misses": 0, "local_hits": 0}

    @staticmethod
    def _make_key(collection: str, query: str, top_k: int, filters: Optional[Dict] = None) -> str:
        """生成缓存键"""
        raw = f"{collection}|{query}|{top_k}|{json.dumps(filters or {}, sort_keys=True)}"
        h = hashlib.md5(raw.encode()).hexdigest()[:16]
        return f"{RAGCacheService.CACHE_PREFIX}{collection}:{h}"

    async def get_cached_search(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
    ) -> Optional[List[Dict]]:
        """获取缓存的搜索结果"""
        key = self._make_key(collection, query, top_k, filters)

        # 本地缓存优先
        if key in self._local_cache:
            value, ts = self._local_cache[key]
            if time.time() - ts < self._local_ttl:
                self._stats["local_hits"] += 1
                return value
            del self._local_cache[key]

        # Redis 缓存
        if self._redis:
            try:
                cached = self._redis.get(key)
                if cached:
                    self._stats["hits"] += 1
                    result = json.loads(cached)
                    self._local_cache[key] = (result, time.time())
                    return result
            except Exception as e:
                logger.warning("[RAGCache] Redis GET 失败: %s", e)

        self._stats["misses"] += 1
        return None

    async def set_cached_search(
        self,
        collection: str,
        query: str,
        top_k: int,
        results: List[Dict],
        ttl: int = DEFAULT_TTL,
        filters: Optional[Dict] = None,
    ):
        """缓存搜索结果"""
        key = self._make_key(collection, query, top_k, filters)

        # 写入本地缓存
        self._local_cache[key] = (results, time.time())

        # 写入 Redis
        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(results, ensure_ascii=False))
            except Exception as e:
                logger.warning("[RAGCache] Redis SET 失败: %s", e)

    async def invalidate_collection(self, collection: str):
        """使指定集合的所有缓存失效（文档更新时调用）"""
        if self._redis:
            try:
                pattern = f"{self.CACHE_PREFIX}{collection}:*"
                cursor = 0
                while True:
                    cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        self._redis.delete(*keys)
                    if cursor == 0:
                        break
                logger.info("[RAGCache] 已清除集合 '%s' 的所有缓存", collection)
            except Exception as e:
                logger.warning("[RAGCache] Redis 批量清除失败: %s", e)

        # 清除本地缓存
        to_remove = [k for k in self._local_cache if f":{collection}:" in k]
        for k in to_remove:
            del self._local_cache[k]

    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        total = self._stats["hits"] + self._stats["misses"] + self._stats["local_hits"]
        hit_rate = (self._stats["hits"] + self._stats["local_hits"]) / max(total, 1)
        return {**self._stats, "total": total, "hit_rate": round(hit_rate, 4)}


# ═════════════════════════════════════════════════════════════════════════════
# 3. 工作流并发控制
# ═════════════════════════════════════════════════════════════════════════════

class WorkflowConcurrencyManager:
    """
    工作流并发控制器

    使用 asyncio.Semaphore 限制同层并行节点数，
    防止单个工作流耗尽系统资源。
    """

    def __init__(self, max_concurrent_nodes: int = 10, max_concurrent_workflows: int = 5):
        """
        Args:
            max_concurrent_nodes: 单个工作流同层最大并行节点数
            max_concurrent_workflows: 全局最大并发工作流数
        """
        self._node_semaphore = asyncio.Semaphore(max_concurrent_nodes)
        self._workflow_semaphore = asyncio.Semaphore(max_concurrent_workflows)
        self._active_workflows: Dict[int, datetime] = {}
        self._node_stats: Dict[str, Dict[str, Any]] = {}

    async def acquire_workflow(self, workflow_id: int) -> bool:
        """获取工作流执行许可"""
        acquired = self._workflow_semaphore.locked()
        await self._workflow_semaphore.acquire()
        self._active_workflows[workflow_id] = datetime.utcnow()
        logger.info(
            "[ConcurrencyMgr] 工作流 %d 获得许可, 活跃数: %d",
            workflow_id, len(self._active_workflows),
        )
        return True

    def release_workflow(self, workflow_id: int):
        """释放工作流执行许可"""
        self._active_workflows.pop(workflow_id, None)
        self._workflow_semaphore.release()
        logger.info("[ConcurrencyMgr] 工作流 %d 释放许可", workflow_id)

    async def run_node_with_limit(self, coro, node_id: str, node_type: str = ""):
        """
        在信号量限制下执行节点协程

        Args:
            coro: 节点执行协程
            node_id: 节点 ID
            node_type: 节点类型（用于统计）

        Returns:
            节点执行结果
        """
        start = time.monotonic()
        async with self._node_semaphore:
            logger.debug("[ConcurrencyMgr] 节点 %s 开始执行 (type=%s)", node_id, node_type)
            try:
                result = await coro
                elapsed = time.monotonic() - start
                self._record_node_stat(node_id, node_type, elapsed, True)
                return result
            except Exception as e:
                elapsed = time.monotonic() - start
                self._record_node_stat(node_id, node_type, elapsed, False)
                raise

    def _record_node_stat(self, node_id: str, node_type: str, elapsed: float, success: bool):
        """记录节点执行统计"""
        key = f"{node_type}:{node_id}"
        if key not in self._node_stats:
            self._node_stats[key] = {"count": 0, "total_time": 0.0, "failures": 0}
        stats = self._node_stats[key]
        stats["count"] += 1
        stats["total_time"] += elapsed
        if not success:
            stats["failures"] += 1

    @property
    def active_workflow_count(self) -> int:
        return len(self._active_workflows)

    def get_stats(self) -> Dict[str, Any]:
        """获取并发管理统计"""
        return {
            "active_workflows": self.active_workflow_count,
            "node_stats": dict(self._node_stats),
        }


# ═════════════════════════════════════════════════════════════════════════════
# 4. 批量 Embedding 处理器
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class EmbeddingJob:
    """Embedding 批处理作业"""
    texts: List[str]
    ids: List[str]
    collection_name: str
    metadata: Optional[List[Dict[str, Any]]] = None


class BatchEmbeddingProcessor:
    """
    批量 Embedding 处理器

    - 将多个文本合并为批量请求，减少 API 调用次数
    - 支持异步后台索引写入
    - 自动分批处理（避免单次请求过大）
    """

    DEFAULT_BATCH_SIZE = 64
    MAX_QUEUE_SIZE = 10000

    def __init__(self, embedding_service=None, vector_store=None, batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Args:
            embedding_service: EmbeddingService 实例
            vector_store: VectorStoreService 实例
            batch_size: 每批处理的文本数量
        """
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._batch_size = batch_size
        self._job_queue: asyncio.Queue = asyncio.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._stats = {"batches_processed": 0, "texts_embedded": 0, "errors": 0}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="embedding")

    async def start(self):
        """启动后台批处理工作线程"""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("[BatchEmbedding] 后台批处理器已启动 (batch_size=%d)", self._batch_size)

    async def stop(self):
        """停止后台批处理"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._executor.shutdown(wait=False)
        logger.info("[BatchEmbedding] 后台批处理器已停止")

    async def submit(self, job: EmbeddingJob):
        """提交 Embedding 作业到队列"""
        if self._job_queue.full():
            logger.warning("[BatchEmbedding] 队列已满，丢弃作业 (collection=%s)", job.collection_name)
            return
        await self._job_queue.put(job)
        logger.debug(
            "[BatchEmbedding] 作业已提交: collection=%s, texts=%d",
            job.collection_name, len(job.texts),
        )

    async def process_immediate(
        self,
        texts: List[str],
        ids: List[str],
        collection_name: str,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        立即处理 Embedding（同步等待完成）

        适用于需要立即使用向量的场景（如文档上传后立即搜索）。
        """
        if not self._embedding_service:
            raise RuntimeError("EmbeddingService 未配置")

        all_vectors = []
        total = len(texts)

        for i in range(0, total, self._batch_size):
            batch_texts = texts[i: i + self._batch_size]
            try:
                vectors = await self._embedding_service.embed(batch_texts)
                all_vectors.extend(vectors)
            except Exception as e:
                logger.error("[BatchEmbedding] 批量 Embedding 失败 (batch %d-%d): %s", i, i + len(batch_texts), e)
                self._stats["errors"] += 1
                raise

        # 写入向量数据库
        if self._vector_store and all_vectors:
            try:
                batch_ids = ids[: len(all_vectors)]
                batch_meta = metadata[: len(all_vectors)] if metadata else None
                await self._vector_store.insert(
                    collection_name, all_vectors, batch_ids, batch_meta
                )
            except Exception as e:
                logger.error("[BatchEmbedding] 向量写入失败: %s", e)
                self._stats["errors"] += 1
                raise

        self._stats["batches_processed"] += 1
        self._stats["texts_embedded"] += total

        return {
            "status": "completed",
            "texts_embedded": total,
            "batches": (total + self._batch_size - 1) // self._batch_size,
        }

    async def _worker_loop(self):
        """后台工作循环：从队列取作业并批量处理"""
        logger.info("[BatchEmbedding] 工作循环已启动")
        while self._running:
            try:
                # 收集一批作业
                jobs: List[EmbeddingJob] = []
                try:
                    job = await asyncio.wait_for(self._job_queue.get(), timeout=5.0)
                    jobs.append(job)
                except asyncio.TimeoutError:
                    continue

                # 尝试多取几个凑批
                while not self._job_queue.empty() and len(jobs) < 10:
                    try:
                        jobs.append(self._job_queue.get_nowait())
                    except asyncio.QueueEmpty:
                        break

                # 合并文本
                all_texts = []
                all_ids = []
                all_meta = []
                collections = set()
                for job in jobs:
                    all_texts.extend(job.texts)
                    all_ids.extend(job.ids)
                    if job.metadata:
                        all_meta.extend(job.metadata)
                    collections.add(job.collection_name)

                if not all_texts:
                    continue

                logger.info(
                    "[BatchEmbedding] 处理批次: %d 个作业, %d 条文本, 集合: %s",
                    len(jobs), len(all_texts), collections,
                )

                # 分批 Embedding
                if self._embedding_service:
                    for i in range(0, len(all_texts), self._batch_size):
                        batch = all_texts[i: i + self._batch_size]
                        batch_ids = all_ids[i: i + self._batch_size]
                        batch_meta = all_meta[i: i + self._batch_size] if all_meta else None

                        try:
                            vectors = await self._embedding_service.embed(batch)

                            # 写入向量数据库
                            if self._vector_store and vectors:
                                for coll in collections:
                                    await self._vector_store.insert(
                                        coll, vectors, batch_ids, batch_meta
                                    )

                            self._stats["texts_embedded"] += len(batch)
                        except Exception as e:
                            logger.error("[BatchEmbedding] 批处理失败: %s", e)
                            self._stats["errors"] += 1

                    self._stats["batches_processed"] += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("[BatchEmbedding] 工作循环异常: %s", e)
                self._stats["errors"] += 1
                await asyncio.sleep(1)

    def get_stats(self) -> Dict[str, Any]:
        """获取批处理统计"""
        return {
            **self._stats,
            "queue_size": self._job_queue.qsize(),
            "running": self._running,
        }


# ═════════════════════════════════════════════════════════════════════════════
# 全局单例
# ═════════════════════════════════════════════════════════════════════════════

# 惰性初始化的全局实例
_collection_queue: Optional[CollectionTaskQueue] = None
_rag_cache: Optional[RAGCacheService] = None
_concurrency_manager: Optional[WorkflowConcurrencyManager] = None
_batch_processor: Optional[BatchEmbeddingProcessor] = None


def get_collection_queue() -> CollectionTaskQueue:
    """获取全局采集任务队列"""
    global _collection_queue
    if _collection_queue is None:
        _collection_queue = CollectionTaskQueue()
    return _collection_queue


def get_rag_cache() -> RAGCacheService:
    """获取全局 RAG 缓存服务"""
    global _rag_cache
    if _rag_cache is None:
        _rag_cache = RAGCacheService()
    return _rag_cache


def get_concurrency_manager(
    max_nodes: int = 10,
    max_workflows: int = 5,
) -> WorkflowConcurrencyManager:
    """获取全局并发管理器"""
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = WorkflowConcurrencyManager(
            max_concurrent_nodes=max_nodes,
            max_concurrent_workflows=max_workflows,
        )
    return _concurrency_manager


def get_batch_processor(
    embedding_service=None,
    vector_store=None,
    batch_size: int = BatchEmbeddingProcessor.DEFAULT_BATCH_SIZE,
) -> BatchEmbeddingProcessor:
    """获取全局批量 Embedding 处理器"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchEmbeddingProcessor(
            embedding_service=embedding_service,
            vector_store=vector_store,
            batch_size=batch_size,
        )
    return _batch_processor


def get_all_performance_stats() -> Dict[str, Any]:
    """获取所有性能组件的统计信息"""
    return {
        "collection_queue": {"pending": get_collection_queue().pending_count},
        "rag_cache": get_rag_cache().get_stats(),
        "concurrency_manager": get_concurrency_manager().get_stats(),
        "batch_processor": get_batch_processor().get_stats(),
    }
