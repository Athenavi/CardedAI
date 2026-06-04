"""
Embedding 服务

支持两种后端：
1. sentence-transformers 本地模型（默认）
2. OpenAI text-embedding-3-small API

通过环境变量 EMBEDDING_PROVIDER 切换：
- local（默认）：使用 sentence-transformers 本地模型
- openai：使用 OpenAI API

通过环境变量 EMBEDDING_MODEL 指定模型名称：
- 本地默认: all-MiniLM-L6-v2
- OpenAI 默认: text-embedding-3-small
"""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.unified_logger import default_logger as logger

# 性能优化：批量 Embedding 处理器（延迟导入避免循环依赖）
def _get_batch_processor():
    """延迟获取批量 Embedding 处理器"""
    try:
        from shared.services.performance.engine_optimizer import get_batch_processor
        return get_batch_processor()
    except Exception:
        return None


class EmbeddingBackend(ABC):
    """Embedding 后端抽象基类"""

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为向量列表"""
        ...

    @abstractmethod
    def get_dimension(self) -> int:
        """返回向量维度"""
        ...


class LocalEmbeddingBackend(EmbeddingBackend):
    """
    基于 sentence-transformers 的本地 Embedding 后端

    首次使用时延迟加载模型，避免启动时阻塞。
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._dimension: Optional[int] = None

    def _load_model(self):
        """延迟加载 sentence-transformers 模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Embedding 模型已加载: {self._model_name} (dim={self._dimension})")
            except ImportError:
                raise ImportError("请安装 sentence-transformers: pip install sentence-transformers")
            except Exception as e:
                logger.error(f"Embedding 模型加载失败: {e}")
                raise

    async def embed(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        try:
            # sentence-transformers 的 encode 是同步的，用 run_in_executor 包装
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"本地 Embedding 生成失败: {e}")
            return []

    def get_dimension(self) -> int:
        self._load_model()
        return self._dimension


class OpenAIEmbeddingBackend(EmbeddingBackend):
    """
    基于 OpenAI API 的 Embedding 后端

    需要设置环境变量 OPENAI_API_KEY。
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self._model_name = model_name
        self._dimension = 1536  # text-embedding-3-small 默认维度
        self._api_key = os.getenv("OPENAI_API_KEY", "")
        self._base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not self._api_key:
            logger.error("OPENAI_API_KEY 未设置")
            return []

        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._base_url}/embeddings",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={"input": texts, "model": self._model_name},
                )
                response.raise_for_status()
                data = response.json()

                # 按 index 排序，确保顺序与输入一致
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]
        except Exception as e:
            logger.error(f"OpenAI Embedding 生成失败: {e}")
            return []

    def get_dimension(self) -> int:
        return self._dimension


class EmbeddingService:
    """
    Embedding 服务

    提供文本向量化能力，支持本地模型和 OpenAI API 两种后端。
    """

    def __init__(self):
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()

        if provider == "openai":
            model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            self._backend = OpenAIEmbeddingBackend(model_name)
            logger.info(f"Embedding 服务: OpenAI ({model_name})")
        else:
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self._backend = LocalEmbeddingBackend(model_name)
            logger.info(f"Embedding 服务: 本地 ({model_name})")

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为向量列表

        Args:
            texts: 文本列表

        Returns:
            向量列表，每个向量为 float 列表
        """
        if not texts:
            return []
        return await self._backend.embed(texts)

    async def embed_single(self, text: str) -> List[float]:
        """
        将单个文本转换为向量

        Args:
            text: 文本

        Returns:
            向量（float 列表）
        """
        results = await self.embed([text])
        return results[0] if results else []

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self._backend.get_dimension()

    async def embed_batch_background(
        self,
        texts: List[str],
        ids: List[str],
        collection_name: str,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        提交批量 Embedding 任务到后台处理器

        使用 BatchEmbeddingProcessor 将多个文本合并为批量请求，
        适用于文档导入等不需要立即返回结果的场景。

        Args:
            texts: 文本列表
            ids: 对应的 ID 列表
            collection_name: 向量集合名称
            metadata: 元数据列表（可选）

        Returns:
            提交状态 {"status": "submitted", "count": N}
        """
        from shared.services.performance.engine_optimizer import EmbeddingJob, get_batch_processor

        processor = get_batch_processor(embedding_service=self, batch_size=64)
        job = EmbeddingJob(
            texts=texts,
            ids=ids,
            collection_name=collection_name,
            metadata=metadata,
        )
        await processor.submit(job)
        return {"status": "submitted", "count": len(texts)}

    async def embed_batch_immediate(
        self,
        texts: List[str],
        ids: List[str],
        collection_name: str,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        立即执行批量 Embedding 并写入向量数据库

        适用于文档上传后需要立即可搜索的场景。
        自动分批处理避免单次请求过大。

        Args:
            texts: 文本列表
            ids: 对应的 ID 列表
            collection_name: 向量集合名称
            metadata: 元数据列表（可选）

        Returns:
            处理结果 {"status": "completed", "texts_embedded": N, "batches": M}
        """
        from shared.services.performance.engine_optimizer import get_batch_processor

        try:
            from shared.services.knowledge.vector_store import vector_store
        except ImportError:
            vector_store = None

        processor = get_batch_processor(
            embedding_service=self,
            vector_store=vector_store,
            batch_size=64,
        )
        return await processor.process_immediate(
            texts=texts,
            ids=ids,
            collection_name=collection_name,
            metadata=metadata,
        )


# 全局单例
embedding_service = EmbeddingService()
