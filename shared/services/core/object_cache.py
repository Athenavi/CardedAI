"""
对象缓存服务

提供数据库查询结果的对象级缓存
支持缓存标签、批量操作和智能失效
"""

from functools import wraps
from typing import Any, Dict, List, Optional, Callable

from shared.services.core.multi_level_cache import MultiLevelCache, multi_level_cache



class ObjectCacheService:
    """
    对象缓存服务
    
    用于缓存数据库查询结果、ORM对象等
    支持基于标签的批量失效
    """

    def __init__(self, cache: Optional[MultiLevelCache] = None):
        """
        初始化对象缓存服务
        
        Args:
            cache: 多级缓存实例
        """
        self.cache = cache or multi_level_cache
        self.cache_prefix = "object_cache:"
        self.tag_index_prefix = "cache_tags:"
        self.default_ttl = 600  # 10分钟默认TTL

    def _generate_object_key(self, model_name: str, object_id: Any,
                             field: Optional[str] = None) -> str:
        """
        生成对象缓存键
        
        Args:
            model_name: 模型名称
            object_id: 对象ID
            field: 字段名（可选，用于缓存特定字段）
        
        Returns:
            缓存键
        """
        key = f"{self.cache_prefix}{model_name}:{object_id}"
        if field:
            key += f":{field}"
        return key

    def _generate_query_key(self, query_type: str, params: Dict[str, Any]) -> str:
        """
        生成查询结果缓存键
        
        Args:
            query_type: 查询类型（如 'list', 'count'）
            params: 查询参数字典
        
        Returns:
            缓存键
        """
        import hashlib
        import json

        # 对参数排序并序列化
        params_str = json.dumps(params, sort_keys=True, default=str)
        hash_key = hashlib.md5(params_str.encode()).hexdigest()[:16]

        return f"{self.cache_prefix}query:{query_type}:{hash_key}"

    async def get_object(self, model_name: str, object_id: Any,
                         field: Optional[str] = None) -> Optional[Any]:
        """
        获取缓存的对象
        
        Args:
            model_name: 模型名称
            object_id: 对象ID
            field: 字段名（可选）
        
        Returns:
            缓存的对象数据
        """
        cache_key = self._generate_object_key(model_name, object_id, field)
        return self.cache.get(cache_key)

    async def set_object(self, model_name: str, object_id: Any,
                         data: Any, field: Optional[str] = None,
                         ttl: Optional[int] = None,
                         tags: Optional[List[str]] = None) -> None:
        """
        缓存对象数据
        
        Args:
            model_name: 模型名称
            object_id: 对象ID
            data: 对象数据
            field: 字段名（可选）
            ttl: TTL(秒)
            tags: 缓存标签列表
        """
        if ttl is None:
            ttl = self.default_ttl

        cache_key = self._generate_object_key(model_name, object_id, field)
        self.cache.set(cache_key, data, ttl)

        # 注册标签索引
        if tags:
            await self._add_to_tag_index(cache_key, tags)

    async def delete_object(self, model_name: str, object_id: Any,
                            field: Optional[str] = None) -> None:
        """
        删除对象缓存
        
        Args:
            model_name: 模型名称
            object_id: 对象ID
            field: 字段名（可选）
        """
        cache_key = self._generate_object_key(model_name, object_id, field)
        self.cache.delete(cache_key)

    async def get_query_result(self, query_type: str,
                               params: Dict[str, Any]) -> Optional[Any]:
        """
        获取缓存的查询结果
        
        Args:
            query_type: 查询类型
            params: 查询参数
        
        Returns:
            缓存的查询结果
        """
        cache_key = self._generate_query_key(query_type, params)
        return self.cache.get(cache_key)

    async def set_query_result(self, query_type: str, params: Dict[str, Any],
                               data: Any, ttl: Optional[int] = None,
                               tags: Optional[List[str]] = None) -> None:
        """
        缓存查询结果
        
        Args:
            query_type: 查询类型
            params: 查询参数
            data: 查询结果数据
            ttl: TTL(秒)
            tags: 缓存标签列表
        """
        if ttl is None:
            ttl = self.default_ttl

        cache_key = self._generate_query_key(query_type, params)
        self.cache.set(cache_key, data, ttl)

        # 注册标签索引
        if tags:
            await self._add_to_tag_index(cache_key, tags)

    async def invalidate_by_tag(self, tag: str) -> int:
        """
        根据标签使缓存失效
        
        Args:
            tag: 缓存标签
        
        Returns:
            失效的缓存数量
        """
        index_key = f"{self.tag_index_prefix}{tag}"
        cache_keys = self.cache.get(index_key)

        if not cache_keys:
            return 0

        deleted_count = 0
        for cache_key in cache_keys:
            self.cache.delete(cache_key)
            deleted_count += 1

        # 清除标签索引
        self.cache.delete(index_key)

        print(f"[ObjectCache] Invalidated {deleted_count} objects with tag: {tag}")
        return deleted_count

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """
        根据多个标签使缓存失效
        
        Args:
            tags: 缓存标签列表
        
        Returns:
            失效的缓存总数
        """
        total_deleted = 0
        for tag in tags:
            count = await self.invalidate_by_tag(tag)
            total_deleted += count

        return total_deleted

    async def _add_to_tag_index(self, cache_key: str, tags: List[str]) -> None:
        """
        将缓存键添加到标签索引
        
        Args:
            cache_key: 缓存键
            tags: 标签列表
        """
        for tag in tags:
            index_key = f"{self.tag_index_prefix}{tag}"

            # 获取现有的键列表
            existing_keys = self.cache.get(index_key) or []

            # 添加新键（避免重复）
            if cache_key not in existing_keys:
                existing_keys.append(cache_key)
                self.cache.set(index_key, existing_keys, ttl=3600)  # 索引TTL 1小时

    def cache_object(self, model_name: str, field: Optional[str] = None,
                     ttl: Optional[int] = None, tags: Optional[List[str]] = None):
        """
        对象缓存装饰器
        
        用于自动缓存函数返回的对象数据
        
        Args:
            model_name: 模型名称
            field: 字段名（可选）
            ttl: TTL(秒)
            tags: 缓存标签
        
        Returns:
            装饰器函数
        """

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 尝试从第一个参数获取对象ID
                object_id = None
                if args:
                    # 假设第二个参数是object_id（第一个是self）
                    if len(args) > 1:
                        object_id = args[1]

                # 或者从kwargs获取
                if not object_id:
                    object_id = kwargs.get('object_id') or kwargs.get('id')

                if not object_id:
                    # 无法确定ID，直接调用原函数
                    return await func(*args, **kwargs)

                # 尝试从缓存获取
                cached = await self.get_object(model_name, object_id, field)
                if cached is not None:
                    return cached

                # 执行原函数
                result = await func(*args, **kwargs)

                # 缓存结果
                if result is not None:
                    await self.set_object(model_name, object_id, result,
                                          field, ttl, tags)

                return result

            return wrapper

        return decorator

    def cache_query(self, query_type: str, ttl: Optional[int] = None,
                    tags: Optional[List[str]] = None):
        """
        查询结果缓存装饰器
        
        用于自动缓存查询结果
        
        Args:
            query_type: 查询类型
            ttl: TTL(秒)
            tags: 缓存标签
        
        Returns:
            装饰器函数
        """

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 构建查询参数
                params = {
                    'args': [str(arg) for arg in args if not isinstance(arg, type(lambda: None))],
                    'kwargs': {k: str(v) for k, v in kwargs.items()},
                }

                # 尝试从缓存获取
                cached = await self.get_query_result(query_type, params)
                if cached is not None:
                    return cached

                # 执行原函数
                result = await func(*args, **kwargs)

                # 缓存结果
                if result is not None:
                    await self.set_query_result(query_type, params, result, ttl, tags)

                return result

            return wrapper

        return decorator

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取对象缓存统计信息
        
        Returns:
            统计信息字典
        """
        cache_stats = self.cache.get_stats()

        return {
            "prefix": self.cache_prefix,
            "default_ttl": self.default_ttl,
            "cache_stats": cache_stats,
        }


# 全局实例
object_cache_service = ObjectCacheService()

# 导出
__all__ = ['ObjectCacheService', 'object_cache_service']
