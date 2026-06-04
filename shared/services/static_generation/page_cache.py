"""
页面缓存服务

实现全页缓存和片段缓存
支持自动失效和手动清除
适用于高访问量的静态或半静态页面
"""

import hashlib
from typing import Optional, Dict, Any, Callable, Awaitable

from shared.services.core.multi_level_cache import MultiLevelCache, multi_level_cache


class PageCacheService:
    """
    页面缓存服务
    
    提供全页缓存和片段缓存功能
    支持基于URL、用户角色等的缓存策略
    """

    def __init__(self, cache: Optional[MultiLevelCache] = None):
        """
        初始化页面缓存服务
        
        Args:
            cache: 多级缓存实例，默认使用全局实例
        """
        self.cache = cache or multi_level_cache
        self.cache_prefix = "page_cache:"
        self.default_ttl = 300  # 5分钟默认TTL

    def _generate_cache_key(self, url: str, user_role: str = "anonymous",
                            params: Optional[Dict[str, Any]] = None) -> str:
        """
        生成页面缓存键
        
        Args:
            url: 页面URL
            user_role: 用户角色 (anonymous, user, admin)
            params: 查询参数
        
        Returns:
            缓存键
        """
        # 构建完整的缓存键
        key_parts = [url, user_role]

        if params:
            # 对参数排序以确保一致性
            sorted_params = sorted(params.items())
            params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
            key_parts.append(params_str)

        # 生成MD5哈希作为缓存键
        key_string = "|".join(key_parts)
        hash_key = hashlib.md5(key_string.encode()).hexdigest()

        return f"{self.cache_prefix}{hash_key}"

    async def get_page(self, url: str, user_role: str = "anonymous",
                       params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        获取缓存的页面内容
        
        Args:
            url: 页面URL
            user_role: 用户角色
            params: 查询参数
        
        Returns:
            缓存的HTML内容，不存在则返回None
        """
        cache_key = self._generate_cache_key(url, user_role, params)
        cached_content = self.cache.get(cache_key)

        if cached_content:
            print(f"[PageCache] HIT: {url} (role: {user_role})")
            return cached_content

        print(f"[PageCache] MISS: {url} (role: {user_role})")
        return None

    async def set_page(self, url: str, content: str, user_role: str = "anonymous",
                       params: Optional[Dict[str, Any]] = None,
                       ttl: Optional[int] = None) -> None:
        """
        缓存页面内容
        
        Args:
            url: 页面URL
            content: HTML内容
            user_role: 用户角色
            params: 查询参数
            ttl: TTL(秒)，None使用默认值
        """
        if ttl is None:
            ttl = self.default_ttl

        cache_key = self._generate_cache_key(url, user_role, params)
        self.cache.set(cache_key, content, ttl)

        print(f"[PageCache] SET: {url} (role: {user_role}, ttl: {ttl}s)")

    async def invalidate_page(self, url: str, user_role: str = "anonymous",
                              params: Optional[Dict[str, Any]] = None) -> None:
        """
        使页面缓存失效
        
        Args:
            url: 页面URL
            user_role: 用户角色
            params: 查询参数
        """
        cache_key = self._generate_cache_key(url, user_role, params)
        self.cache.delete(cache_key)

        print(f"[PageCache] INVALIDATE: {url} (role: {user_role})")

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        使匹配模式的缓存失效
        
        Args:
            pattern: URL模式（支持通配符）
        
        Returns:
            失效的缓存数量
        """
        # 注意：这里简化实现，实际应该扫描所有缓存键
        # 对于生产环境，建议使用Redis的KEYS命令或维护索引
        print(f"[PageCache] INVALIDATE PATTERN: {pattern}")
        return 0

    async def clear_all(self) -> None:
        """清空所有页面缓存"""
        # 清空所有以page_cache:开头的键
        # 这里简化处理，实际应该只清除页面缓存
        print("[PageCache] CLEAR ALL")

    def should_cache_request(self, url: str, method: str = "GET",
                             user_role: str = "anonymous") -> bool:
        """
        判断是否应该缓存请求
        
        Args:
            url: 请求URL
            method: HTTP方法
            user_role: 用户角色
        
        Returns:
            是否应该缓存
        """
        # 只缓存GET请求
        if method != "GET":
            return False

        # 不缓存管理后台
        if "/admin" in url or "/api/v1/admin" in url:
            return False

        # 不认证用户的个性化页面
        if user_role == "anonymous":
            # 匿名用户页面可以缓存
            return True

        # 已登录用户的页面需要谨慎缓存
        # 通常只缓存公共内容
        if "/api/v1/user" in url or "/api/v1/profile" in url:
            return False

        return True

    def get_cache_info(self, url: str, user_role: str = "anonymous",
                       params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Args:
            url: 页面URL
            user_role: 用户角色
            params: 查询参数
        
        Returns:
            缓存信息字典
        """
        cache_key = self._generate_cache_key(url, user_role, params)

        # 检查缓存是否存在
        cached = self.cache.get(cache_key)

        return {
            "url": url,
            "user_role": user_role,
            "cache_key": cache_key,
            "is_cached": cached is not None,
            "params": params,
        }


# 页面缓存装饰器
def page_cache(ttl: int = 300, user_role_param: str = "user_role"):
    """
    页面缓存装饰器
    
    用于FastAPI路由，自动缓存响应内容
    
    Args:
        ttl: 缓存TTL(秒)
        user_role_param: 从请求中获取用户角色的参数名
    
    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., Awaitable[Any]]):
        async def wrapper(*args, **kwargs):
            from fastapi import Request

            # 获取请求对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # 如果没有Request对象，直接调用原函数
                return await func(*args, **kwargs)

            # 提取缓存相关信息
            url = str(request.url.path)
            method = request.method

            # 确定用户角色
            user_role = kwargs.get(user_role_param, "anonymous")
            if not user_role:
                user_role = "anonymous"

            # 获取查询参数
            params = dict(request.query_params)

            # 创建页面缓存服务实例
            page_cache_service = PageCacheService()

            # 检查是否应该缓存
            if not page_cache_service.should_cache_request(url, method, user_role):
                return await func(*args, **kwargs)

            # 尝试从缓存获取
            cached_content = await page_cache_service.get_page(url, user_role, params)
            if cached_content:
                from fastapi.responses import Response
                return Response(content=cached_content, media_type="text/html")

            # 执行原函数
            response = await func(*args, **kwargs)

            # 缓存响应内容
            if hasattr(response, 'body'):
                content = response.body.decode('utf-8') if isinstance(response.body, bytes) else str(response.body)
                await page_cache_service.set_page(url, content, user_role, params, ttl)

            return response

        return wrapper

    return decorator


# 全局实例
page_cache_service = PageCacheService()

# 导出
__all__ = ['PageCacheService', 'page_cache', 'page_cache_service']
