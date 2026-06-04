"""
性能优化模块

提供 FastBlog 核心引擎的性能优化组件：
- CollectionTaskQueue: 基于 Redis Streams 的采集任务队列
- RAGCacheService: RAG 检索结果缓存（Redis + 本地双层）
- WorkflowConcurrencyManager: 工作流并发控制（asyncio.Semaphore）
- BatchEmbeddingProcessor: 批量 Embedding 处理器
"""

from shared.services.performance.engine_optimizer import (
    CollectionTaskQueue,
    CollectionTask,
    RAGCacheService,
    WorkflowConcurrencyManager,
    BatchEmbeddingProcessor,
    EmbeddingJob,
    get_collection_queue,
    get_rag_cache,
    get_concurrency_manager,
    get_batch_processor,
    get_all_performance_stats,
)

__all__ = [
    "CollectionTaskQueue",
    "CollectionTask",
    "RAGCacheService",
    "WorkflowConcurrencyManager",
    "BatchEmbeddingProcessor",
    "EmbeddingJob",
    "get_collection_queue",
    "get_rag_cache",
    "get_concurrency_manager",
    "get_batch_processor",
    "get_all_performance_stats",
]
