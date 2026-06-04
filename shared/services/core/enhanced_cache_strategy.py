"""
增强缓存策略服务
提供智能缓存、分层缓存和缓存预热功能
"""

import asyncio
import hashlib
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from shared.services.cache_service import CacheService
except ImportError:
    CacheService = None


class EnhancedCacheStrategy:
    """
    增强缓存策略
    
    特性：
    1. 分层缓存（L1内存 + L2 Redis）
    2. 智能过期策略
    3. 缓存预热
    4. 缓存标签管理
    5. 统计信息收集
    """

    def __init__(self, cache_service=None):
        """
        初始化增强缓存策略
        
        Args:
            cache_service: CacheService实例
        """
        self.cache = cache_service or CacheService()

        # 缓存统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
        }

        # 缓存标签映射 (tag -> [keys])
        self.tag_map: Dict[str, set] = {}

        # 默认TTL配置（秒）
        self.default_ttls = {
            'article': 3600,  # 文章缓存1小时
            'user': 1800,  # 用户信息30分钟
            'category': 7200,  # 分类2小时
            'comment': 300,  # 评论5分钟
            'stats': 600,  # 统计数据10分钟
            'config': 86400,  # 配置24小时
            'session': 3600,  # 会话1小时
            'api_response': 60,  # API响应1分钟
        }

    def get_with_stats(self, key: str) -> Optional[Any]:
        """获取缓存并记录统计"""
        value = self.cache.get(key)

        if value is not None:
            self.stats['hits'] += 1
        else:
            self.stats['misses'] += 1

        return value

    def set_with_stats(self, key: str, value: Any, ttl: int = None, tags: List[str] = None):
        """设置缓存并记录统计和标签"""
        if ttl is None:
            # 根据key前缀自动选择TTL
            ttl = self._get_auto_ttl(key)

        self.cache.set(key, value, ttl)
        self.stats['sets'] += 1

        # 记录标签
        if tags:
            for tag in tags:
                if tag not in self.tag_map:
                    self.tag_map[tag] = set()
                self.tag_map[tag].add(key)

    def delete_with_tags(self, tags: Union[str, List[str]]):
        """根据标签删除缓存"""
        if isinstance(tags, str):
            tags = [tags]

        deleted_keys = set()

        for tag in tags:
            if tag in self.tag_map:
                for key in self.tag_map[tag]:
                    self.cache.delete(key)
                    deleted_keys.add(key)
                    self.stats['deletes'] += 1

                # 清空标签映射
                del self.tag_map[tag]

        return list(deleted_keys)

    def invalidate_by_pattern(self, pattern: str):
        """根据模式删除缓存（支持通配符）"""
        # 注意：这个操作在Redis中需要使用SCAN命令
        # 这里简化实现，只处理内存缓存
        keys_to_delete = []

        for key in list(self.cache.cache.keys()):
            if self._match_pattern(pattern, key):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            self.cache.delete(key)
            self.stats['deletes'] += 1

        return keys_to_delete

    async def warmup_cache(self, keys_and_fetchers: List[Dict]):
        """
        缓存预热
        
        Args:
            keys_and_fetchers: 列表，每个元素包含：
                - key: 缓存键
                - fetcher: 异步函数，用于获取数据
                - ttl: 可选的TTL
                - tags: 可选的标签列表
        """
        tasks = []

        for item in keys_and_fetchers:
            key = item['key']
            fetcher = item['fetcher']
            ttl = item.get('ttl')
            tags = item.get('tags')

            task = self._warmup_single(key, fetcher, ttl, tags)
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _warmup_single(self, key: str, fetcher: Callable, ttl: int = None, tags: List[str] = None):
        """预热单个缓存"""
        try:
            # 检查是否已存在
            if self.cache.get(key) is not None:
                return

            # 获取数据
            data = await fetcher()

            if data is not None:
                self.set_with_stats(key, data, ttl, tags)
        except Exception as e:
            print(f"[CacheWarmup] Failed to warmup {key}: {e}")

    def cached(self, key_template: str, ttl: int = None, tags: List[str] = None):
        """
        装饰器：自动缓存函数结果
        
        Usage:
            @cache_strategy.cached("article:{article_id}", ttl=3600, tags=["article"])
            async def get_article(article_id: int):
                ...
        """

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                key = key_template.format(*args, **kwargs)

                # 尝试从缓存获取
                cached_value = self.get_with_stats(key)
                if cached_value is not None:
                    return cached_value

                # 执行函数
                result = await func(*args, **kwargs)

                # 存入缓存
                if result is not None:
                    actual_ttl = ttl or self._get_auto_ttl(key)
                    self.set_with_stats(key, result, actual_ttl, tags)

                return result

            return wrapper

        return decorator

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': f"{hit_rate:.2f}%",
            'tagged_keys': sum(len(keys) for keys in self.tag_map.values()),
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
        }

    def _get_auto_ttl(self, key: str) -> int:
        """根据key前缀自动获取TTL"""
        if key.startswith('article:'):
            return self.default_ttls['article']
        elif key.startswith('user:'):
            return self.default_ttls['user']
        elif key.startswith('category:'):
            return self.default_ttls['category']
        elif key.startswith('comment:'):
            return self.default_ttls['comment']
        elif key.startswith('stats:'):
            return self.default_ttls['stats']
        elif key.startswith('config:'):
            return self.default_ttls['config']
        elif key.startswith('session:'):
            return self.default_ttls['session']
        elif key.startswith('api:'):
            return self.default_ttls['api_response']
        else:
            return self.cache.default_ttl

    @staticmethod
    def _match_pattern(pattern: str, key: str) -> bool:
        """简单的模式匹配（支持*通配符）"""
        if '*' not in pattern:
            return pattern == key

        # 转换为正则表达式
        import re
        regex = pattern.replace('*', '.*')
        return bool(re.match(f'^{regex}$', key))

    @staticmethod
    def generate_cache_key(prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键字符串
        """
        # 将参数序列化为字符串
        args_str = ':'.join(str(arg) for arg in args)
        kwargs_str = ':'.join(f"{k}={v}" for k, v in sorted(kwargs.items()))

        parts = [prefix]
        if args_str:
            parts.append(args_str)
        if kwargs_str:
            parts.append(kwargs_str)

        key = ':'.join(parts)

        # 如果key太长，使用哈希
        if len(key) > 200:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{prefix}:{key_hash}"

        return key


# 全局实例
enhanced_cache = EnhancedCacheStrategy()
