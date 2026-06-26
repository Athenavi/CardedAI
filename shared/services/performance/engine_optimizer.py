"""简化的引擎优化器（个人站长轻量版 - 无Redis依赖）"""
import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

# ============ Collection Task Queue ============

@dataclass
class CollectionTask:
    """采集任务"""
    source_id: int
    source_type: str
    url: str
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
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CollectionTask':
        return cls(
            source_id=data['source_id'],
            source_type=data['source_type'],
            url=data['url'],
            config=data.get('config', {}),
            task_id=data.get('task_id'),
            status=data.get('status', 'pending'),
        )


class CollectionTaskQueue:
    """内存采集任务队列"""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: dict[str, CollectionTask] = {}

    async def enqueue(self, task: CollectionTask) -> str:
        task.task_id = str(int(time.time() * 1000000))
        task.created_at = time.time()
        self._tasks[task.task_id] = task
        await self._queue.put(task)
        return task.task_id

    async def dequeue(self, count: int = 1, block_ms: int = 5000) -> list[tuple[str, CollectionTask]]:
        results = []
        try:
            for _ in range(count):
                task = await asyncio.wait_for(self._queue.get(), timeout=block_ms / 1000)
                results.append((task.task_id, task))
        except asyncio.TimeoutError:
            pass
        return results

    async def ack(self, msg_id: str) -> None:
        self._tasks.pop(msg_id, None)

    async def report_result(self, task: CollectionTask, result: dict) -> None:
        pass

    def pending_count(self) -> int:
        return self._queue.qsize()


# ============ RAG Cache ============

class RAGCacheService:
    """内存RAG缓存服务"""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._stats = {'hits': 0, 'misses': 0}

    @staticmethod
    def _make_key(collection: str, query: str, top_k: int, filters: Optional[dict] = None) -> str:
        return f'{collection}:{query}:{top_k}'

    async def get_cached_search(self, collection: str, query: str, top_k: int,
                                filters: Optional[dict] = None) -> Optional[list]:
        key = self._make_key(collection, query, top_k, filters)
        if key in self._cache:
            self._stats['hits'] += 1
            return self._cache[key].get('results')
        self._stats['misses'] += 1
        return None

    async def set_cached_search(self, collection: str, query: str, top_k: int,
                                results: list, filters: Optional[dict] = None, ttl: int = 300) -> None:
        key = self._make_key(collection, query, top_k, filters)
        self._cache[key] = {'results': results, 'expires': time.time() + ttl}

    async def invalidate_collection(self, collection: str) -> None:
        self._cache = {k: v for k, v in self._cache.items() if not k.startswith(collection)}

    def get_stats(self) -> dict:
        return dict(self._stats)


# ============ Concurrency Manager ============

class ConcurrencyManager:
    """并发控制管理器"""

    def __init__(self, max_concurrent_nodes: int = 10, max_concurrent_workflows: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent_nodes)
        self._active_workflows: set[int] = set()
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
        return dict(self._stats)


# ============ Batch Embedding Processor ============

@dataclass
class EmbeddingJob:
    """嵌入任务"""
    texts: list[str]
    callback: Optional[Any] = None
    job_id: Optional[str] = None


class BatchEmbeddingProcessor:
    """批量嵌入处理器（简化版 - 同步处理）"""

    def __init__(self, embedding_service=None, vector_store=None, batch_size: int = 16):
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._batch_size = batch_size

    async def start(self):
        pass

    async def stop(self):
        pass

    async def submit(self, job: EmbeddingJob):
        await self.process_immediate(job.texts)

    async def process_immediate(self, texts: list[str]) -> list[list[float]]:
        if not self._embedding_service:
            return []
        results = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]
            embeddings = await self._embedding_service.embed(batch)
            results.extend(embeddings)
        return results

    def get_stats(self) -> dict:
        return {'processed': 0}


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
