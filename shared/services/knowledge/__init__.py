"""
知识引擎服务模块

提供文档解析、向量存储、Embedding、RAG 检索、研报生成等核心能力。

核心组件：
- DocumentParser: 通用文档解析器（PDF/DOCX/HTML/TXT/URL）
- DocumentChunker: 文档切片器（recursive/semantic/sentence 策略）
- EmbeddingService: 文本向量化服务（本地模型 + OpenAI API）
- VectorStoreService: 向量数据库服务（Milvus + Qdrant）
- RAGChain: RAG 检索增强生成链
- ReportGenerator: AI 研报生成器
"""

# 延迟导入，避免循环依赖和启动阻塞
__all__ = [
    "DocumentParser",
    "DocumentChunker",
    "EmbeddingService",
    "VectorStoreService",
    "RAGChain",
    "ReportGenerator",
    # 全局单例
    "document_parser",
    "document_chunker",
    "embedding_service",
    "vector_store",
    "rag_chain",
    "report_generator",
]


def __getattr__(name):
    """懒加载机制，按需导入"""
    _lazy_imports = {
        "DocumentParser": ("shared.services.knowledge.document_parser", "DocumentParser"),
        "document_parser": ("shared.services.knowledge.document_parser", "document_parser"),
        "DocumentChunker": ("shared.services.knowledge.chunker", "DocumentChunker"),
        "document_chunker": ("shared.services.knowledge.chunker", "document_chunker"),
        "EmbeddingService": ("shared.services.knowledge.embedding_service", "EmbeddingService"),
        "embedding_service": ("shared.services.knowledge.embedding_service", "embedding_service"),
        "VectorStoreService": ("shared.services.knowledge.vector_store", "VectorStoreService"),
        "vector_store": ("shared.services.knowledge.vector_store", "vector_store"),
        "RAGChain": ("shared.services.knowledge.rag_chain", "RAGChain"),
        "rag_chain": ("shared.services.knowledge.rag_chain", "rag_chain"),
        "ReportGenerator": ("shared.services.knowledge.report_generator", "ReportGenerator"),
        "report_generator": ("shared.services.knowledge.report_generator", "report_generator"),
    }

    if name in _lazy_imports:
        module_path, attr_name = _lazy_imports[name]
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, attr_name)

    raise AttributeError(f"module 'shared.services.knowledge' has no attribute '{name}'")
