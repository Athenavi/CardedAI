"""
向量数据库服务

支持三种后端，通过环境变量 VECTOR_DB_TYPE 切换：
- local（默认）：内置 SQLite 本地向量存储，零外部依赖
- milvus：Milvus 向量数据库（需安装 pymilvus 并运行服务）
- qdrant：Qdrant 向量数据库（需安装 qdrant-client 并运行服务）

提供集合创建、向量插入、相似性搜索、向量删除等核心操作。
"""

import json
import os
import pickle
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.unified_logger import default_logger as logger


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """纯 Python 余弦相似度（零依赖）"""
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))


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


class LocalBackend(VectorStoreBackend):
    """内置 SQLite 本地向量后端（零外部依赖，默认降级方案）

    存储: SQLite 文件（默认 data/vector_store.db，可用 LOCAL_VECTOR_DB_PATH 覆盖）
    检索: 全量加载 + 纯 Python 余弦相似度（O(n*d)），
          适合个人站规模（万级 chunk 内，单次检索数十毫秒）。
    """

    def __init__(self):
        self._db_path = os.getenv("LOCAL_VECTOR_DB_PATH", "data/vector_store.db")
        self._conn = None

    async def _get_conn(self):
        if self._conn is None:
            import aiosqlite
            db_path = self._db_path
            parent = os.path.dirname(os.path.abspath(db_path))
            os.makedirs(parent, exist_ok=True)
            self._conn = await aiosqlite.connect(db_path)
            await self._conn.execute(
                "CREATE TABLE IF NOT EXISTS collections ("
                " name TEXT PRIMARY KEY, dimension INTEGER, metric TEXT, created_at TEXT)"
            )
            await self._conn.execute(
                "CREATE TABLE IF NOT EXISTS vectors ("
                " collection TEXT, id TEXT, vector BLOB, metadata TEXT,"
                " PRIMARY KEY (collection, id))"
            )
            await self._conn.commit()
            logger.info(f"本地向量存储已就绪: {os.path.abspath(db_path)}")
        return self._conn

    async def create_collection(self, collection_name: str, dimension: int = 1536,
                                 metric_type: str = "COSINE") -> bool:
        try:
            conn = await self._get_conn()
            import datetime
            await conn.execute(
                "INSERT OR REPLACE INTO collections (name, dimension, metric, created_at)"
                " VALUES (?, ?, ?, ?)",
                (collection_name, dimension, metric_type,
                 datetime.datetime.now().isoformat(timespec="seconds")),
            )
            await conn.commit()
            logger.info(f"本地向量集合已创建: {collection_name} (dim={dimension})")
            return True
        except Exception as e:
            logger.error(f"本地向量集合创建失败: {e}")
            return False

    async def insert(self, collection_name: str, vectors: List[List[float]],
                     metadata: List[Dict[str, Any]]) -> List[str]:
        try:
            conn = await self._get_conn()
            if vectors:
                await self.create_collection(collection_name, len(vectors[0]))
            ids = []
            for vec, meta in zip(vectors, metadata):
                vid = str(uuid.uuid4())
                await conn.execute(
                    "INSERT INTO vectors (collection, id, vector, metadata) VALUES (?, ?, ?, ?)",
                    (collection_name, vid, pickle.dumps(vec), json.dumps(meta, ensure_ascii=False)),
                )
                ids.append(vid)
            await conn.commit()
            return ids
        except Exception as e:
            logger.error(f"本地向量插入失败: {e}")
            return []

    async def search(self, collection_name: str, query_vector: List[float],
                     top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            conn = await self._get_conn()
            cursor = await conn.execute(
                "SELECT id, vector, metadata FROM vectors WHERE collection = ?", (collection_name,)
            )
            rows = await cursor.fetchall()
            results = []
            for rid, blob, meta_json in rows:
                vec = pickle.loads(blob)
                meta = json.loads(meta_json) if meta_json else {}
                if filters and not all(meta.get(k) == v for k, v in filters.items()):
                    continue
                score = _cosine_similarity(query_vector, vec)
                results.append({"id": rid, "score": score, "metadata": meta})
            results.sort(key=lambda r: r["score"], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"本地向量搜索失败: {e}")
            return []

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        try:
            conn = await self._get_conn()
            for vid in ids:
                await conn.execute(
                    "DELETE FROM vectors WHERE collection = ? AND id = ?", (collection_name, vid)
                )
            await conn.commit()
            return True
        except Exception as e:
            logger.error(f"本地向量删除失败: {e}")
            return False

    async def drop_collection(self, collection_name: str) -> bool:
        try:
            conn = await self._get_conn()
            await conn.execute("DELETE FROM vectors WHERE collection = ?", (collection_name,))
            await conn.execute("DELETE FROM collections WHERE name = ?", (collection_name,))
            await conn.commit()
            return True
        except Exception as e:
            logger.error(f"本地向量集合删除失败: {e}")
            return False

    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        try:
            conn = await self._get_conn()
            cursor = await conn.execute(
                "SELECT name, dimension, metric FROM collections WHERE name = ?", (collection_name,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM vectors WHERE collection = ?", (collection_name,)
            )
            count = (await cursor.fetchone())[0]
            return {"name": row[0], "dimension": row[1], "metric": row[2], "vector_count": count}
        except Exception as e:
            logger.error(f"本地向量集合信息获取失败: {e}")
            return None


class VectorStoreService:
    """
    向量数据库服务（支持 本地 SQLite / Milvus / Qdrant）

    通过环境变量 VECTOR_DB_TYPE 切换后端：
    - local（默认，零外部依赖）
    - milvus
    - qdrant
    """

    def __init__(self):
        db_type = os.getenv("VECTOR_DB_TYPE", "local").lower()
        if db_type == "qdrant":
            self._backend = QdrantBackend()
            logger.info("向量数据库后端: Qdrant")
        elif db_type == "milvus":
            self._backend = MilvusBackend()
            logger.info("向量数据库后端: Milvus")
        else:
            self._backend = LocalBackend()
            logger.info("向量数据库后端: 内置本地存储 (local)")

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
