"""
向量数据库服务

支持 Milvus（主）和 Qdrant（备）双后端，通过环境变量 VECTOR_DB_TYPE 切换。
提供集合创建、向量插入、相似性搜索、向量删除等核心操作。
"""

import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.unified_logger import default_logger as logger


class VectorStoreBackend(ABC):
    """向量数据库后端抽象基类"""

    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int = 1536,
                                 metric_type: str = "COSINE") -> bool:
        """创建向量集合"""
        ...

    @abstractmethod
    async def insert(self, collection_name: str, vectors: List[List[float]],
                     metadata: List[Dict[str, Any]]) -> List[str]:
        """插入向量，返回向量 ID 列表"""
        ...

    @abstractmethod
    async def search(self, collection_name: str, query_vector: List[float],
                     top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """相似性搜索，返回结果列表 [{id, score, metadata}]"""
        ...

    @abstractmethod
    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """根据 ID 列表删除向量"""
        ...

    @abstractmethod
    async def drop_collection(self, collection_name: str) -> bool:
        """删除整个集合"""
        ...

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """获取集合信息"""
        ...


class MilvusBackend(VectorStoreBackend):
    """Milvus 向量数据库后端"""

    def __init__(self):
        self._client = None
        self._host = os.getenv("MILVUS_HOST", "localhost")
        self._port = int(os.getenv("MILVUS_PORT", "19530"))

    async def _get_client(self):
        """延迟初始化 Milvus 客户端"""
        if self._client is None:
            try:
                from pymilvus import MilvusClient
                self._client = MilvusClient(uri=f"http://{self._host}:{self._port}")
                logger.info(f"Milvus 客户端已连接: {self._host}:{self._port}")
            except ImportError:
                raise ImportError("请安装 pymilvus: pip install pymilvus")
            except Exception as e:
                logger.error(f"Milvus 连接失败: {e}")
                raise
        return self._client

    async def create_collection(self, collection_name: str, dimension: int = 1536,
                                 metric_type: str = "COSINE") -> bool:
        try:
            client = await self._get_client()
            from pymilvus import CollectionSchema, FieldSchema, DataType

            # 检查集合是否已存在
            if client.has_collection(collection_name):
                logger.info(f"Milvus 集合已存在: {collection_name}")
                return True

            # 创建集合
            schema = CollectionSchema(fields=[
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ], description=f"FastBlog vector collection: {collection_name}")

            client.create_collection(
                collection_name=collection_name,
                schema=schema,
            )

            # 创建向量索引
            index_params = client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="IVF_FLAT",
                metric_type=metric_type,
                params={"nlist": 1024},
            )
            client.create_index(collection_name, index_params)

            logger.info(f"Milvus 集合已创建: {collection_name} (dim={dimension})")
            return True
        except Exception as e:
            logger.error(f"Milvus 创建集合失败: {e}")
            return False

    async def insert(self, collection_name: str, vectors: List[List[float]],
                     metadata: List[Dict[str, Any]]) -> List[str]:
        try:
            client = await self._get_client()
            ids = [str(uuid.uuid4()) for _ in vectors]
            data = [
                {"id": vid, "vector": vec, "meta": meta}
                for vid, vec, meta in zip(ids, vectors, metadata)
            ]
            client.insert(collection_name=collection_name, data=data)
            logger.debug(f"Milvus 插入 {len(vectors)} 条向量到 {collection_name}")
            return ids
        except Exception as e:
            logger.error(f"Milvus 插入失败: {e}")
            return []

    async def search(self, collection_name: str, query_vector: List[float],
                     top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            client = await self._get_client()
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 16}}

            filter_expr = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(f'metadata["{key}"] == "{value}"')
                    else:
                        conditions.append(f'metadata["{key}"] == {value}')
                filter_expr = " and ".join(conditions)

            results = client.search(
                collection_name=collection_name,
                data=[query_vector],
                limit=top_k,
                output_fields=["id", "metadata"],
                search_params=search_params,
                filter=filter_expr,
            )

            hits = []
            for hits_batch in results:
                for hit in hits_batch:
                    hits.append({
                        "id": hit.get("id", ""),
                        "score": hit.get("distance", 0.0),
                        "metadata": hit.get("entity", {}).get("metadata", {}),
                    })
            return hits
        except Exception as e:
            logger.error(f"Milvus 搜索失败: {e}")
            return []

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        try:
            client = await self._get_client()
            client.delete(collection_name=collection_name, ids=ids)
            logger.debug(f"Milvus 删除 {len(ids)} 条向量从 {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Milvus 删除失败: {e}")
            return False

    async def drop_collection(self, collection_name: str) -> bool:
        try:
            client = await self._get_client()
            client.drop_collection(collection_name)
            logger.info(f"Milvus 集合已删除: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Milvus 删除集合失败: {e}")
            return False

    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        try:
            client = await self._get_client()
            if not client.has_collection(collection_name):
                return None
            info = client.describe_collection(collection_name)
            stats = client.get_collection_stats(collection_name)
            return {
                "name": collection_name,
                "schema": info,
                "stats": stats,
            }
        except Exception as e:
            logger.error(f"Milvus 获取集合信息失败: {e}")
            return None


class QdrantBackend(VectorStoreBackend):
    """Qdrant 向量数据库后端"""

    def __init__(self):
        self._client = None
        self._host = os.getenv("QDRANT_HOST", "localhost")
        self._port = int(os.getenv("QDRANT_PORT", "6333"))

    async def _get_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(host=self._host, port=self._port)
                logger.info(f"Qdrant 客户端已连接: {self._host}:{self._port}")
            except ImportError:
                raise ImportError("请安装 qdrant-client: pip install qdrant-client")
        return self._client

    async def create_collection(self, collection_name: str, dimension: int = 1536,
                                 metric_type: str = "COSINE") -> bool:
        try:
            client = await self._get_client()
            from qdrant_client.models import Distance, VectorParams

            collections = [c.name for c in client.get_collections().collections]
            if collection_name in collections:
                logger.info(f"Qdrant 集合已存在: {collection_name}")
                return True

            distance_map = {"COSINE": Distance.COSINE, "L2": Distance.EUCLID, "IP": Distance.DOT}
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=distance_map.get(metric_type, Distance.COSINE)),
            )
            logger.info(f"Qdrant 集合已创建: {collection_name} (dim={dimension})")
            return True
        except Exception as e:
            logger.error(f"Qdrant 创建集合失败: {e}")
            return False

    async def insert(self, collection_name: str, vectors: List[List[float]],
                     metadata: List[Dict[str, Any]]) -> List[str]:
        try:
            client = await self._get_client()
            from qdrant_client.models import PointStruct

            ids = [str(uuid.uuid4()) for _ in vectors]
            points = [
                PointStruct(id=vid, vector=vec, payload=meta)
                for vid, vec, meta in zip(ids, vectors, metadata)
            ]
            client.upsert(collection_name=collection_name, points=points)
            return ids
        except Exception as e:
            logger.error(f"Qdrant 插入失败: {e}")
            return []

    async def search(self, collection_name: str, query_vector: List[float],
                     top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            client = await self._get_client()
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            query_filter = None
            if filters:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filters.items()
                ]
                query_filter = Filter(must=conditions)

            results = client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
            )
            return [
                {"id": str(hit.id), "score": hit.score, "metadata": hit.payload or {}}
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Qdrant 搜索失败: {e}")
            return []

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        try:
            client = await self._get_client()
            client.delete(collection_name=collection_name, points_selector=ids)
            return True
        except Exception as e:
            logger.error(f"Qdrant 删除失败: {e}")
            return False

    async def drop_collection(self, collection_name: str) -> bool:
        try:
            client = await self._get_client()
            client.delete_collection(collection_name)
            return True
        except Exception as e:
            logger.error(f"Qdrant 删除集合失败: {e}")
            return False

    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        try:
            client = await self._get_client()
            info = client.get_collection(collection_name)
            return {"name": collection_name, "info": info.dict() if hasattr(info, 'dict') else str(info)}
        except Exception as e:
            logger.error(f"Qdrant 获取集合信息失败: {e}")
            return None


class VectorStoreService:
    """
    向量数据库服务（支持 Milvus / Qdrant）

    通过环境变量 VECTOR_DB_TYPE 切换后端：
    - milvus（默认）
    - qdrant
    """

    def __init__(self):
        db_type = os.getenv("VECTOR_DB_TYPE", "milvus").lower()
        if db_type == "qdrant":
            self._backend = QdrantBackend()
            logger.info("向量数据库后端: Qdrant")
        else:
            self._backend = MilvusBackend()
            logger.info("向量数据库后端: Milvus")

    async def create_collection(self, collection_name: str, dimension: int = 1536,
                                 metric_type: str = "COSINE") -> bool:
        """创建向量集合"""
        return await self._backend.create_collection(collection_name, dimension, metric_type)

    async def insert(self, collection_name: str, vectors: List[List[float]],
                     metadata: List[Dict[str, Any]]) -> List[str]:
        """插入向量，返回向量 ID 列表"""
        return await self._backend.insert(collection_name, vectors, metadata)

    async def search(self, collection_name: str, query_vector: List[float],
                     top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """相似性搜索"""
        return await self._backend.search(collection_name, query_vector, top_k, filters)

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """删除向量"""
        return await self._backend.delete(collection_name, ids)

    async def drop_collection(self, collection_name: str) -> bool:
        """删除整个集合"""
        return await self._backend.drop_collection(collection_name)

    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """获取集合信息"""
        return await self._backend.get_collection_info(collection_name)


# 全局单例
vector_store = VectorStoreService()
