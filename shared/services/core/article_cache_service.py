"""
文章缓存服务 - 为文章列表和详情提供缓存支持
"""

from typing import Optional, Dict, Any, List

from src.services.redis_service import redis_service

from src.unified_logger import default_logger as logger


class ArticleCacheService:
    """文章缓存服务"""

    # 缓存键前缀
    ARTICLE_LIST_PREFIX = "article:list"
    ARTICLE_DETAIL_PREFIX = "article:detail"
    ARTICLE_COUNT_PREFIX = "article:count"

    # 默认 TTL (秒)
    LIST_TTL = 300  # 5分钟
    DETAIL_TTL = 600  # 10分钟
    COUNT_TTL = 60  # 1分钟

    async def get_article_list(
            self,
            page: int,
            per_page: int,
            search: str = "",
            category_id: Optional[int] = None,
            user_id: Optional[int] = None,
            status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的文章列表"""
        try:
            cache_key = self._build_list_key(page, per_page, search, category_id, user_id, status)
            cached_data = await redis_service.get(cache_key)

            if cached_data is not None:
                logger.debug(f"文章列表缓存命中: {cache_key}")
                return cached_data

            logger.debug(f"文章列表缓存未命中: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"获取文章列表缓存失败: {e}")
            return None

    async def set_article_list(
            self,
            page: int,
            per_page: int,
            data: Dict[str, Any],
            search: str = "",
            category_id: Optional[int] = None,
            user_id: Optional[int] = None,
            status: Optional[str] = None,
            ttl: Optional[int] = None,
    ):
        """设置文章列表缓存"""
        try:
            cache_key = self._build_list_key(page, per_page, search, category_id, user_id, status)
            await redis_service.set(cache_key, data, expire=ttl or self.LIST_TTL)
            logger.debug(f"文章列表已缓存: {cache_key}, TTL={ttl or self.LIST_TTL}s")
        except Exception as e:
            logger.error(f"设置文章列表缓存失败: {e}")

    async def get_article_detail(self, article_id: int) -> Optional[Dict[str, Any]]:
        """获取缓存的文章详情"""
        try:
            cache_key = f"{self.ARTICLE_DETAIL_PREFIX}:{article_id}"
            cached_data = await redis_service.get(cache_key)

            if cached_data is not None:
                logger.debug(f"文章详情缓存命中: {article_id}")
                return cached_data

            logger.debug(f"文章详情缓存未命中: {article_id}")
            return None
        except Exception as e:
            logger.error(f"获取文章详情缓存失败: {e}")
            return None

    async def set_article_detail(self, article_id: int, data: Dict[str, Any], ttl: Optional[int] = None):
        """设置文章详情缓存"""
        try:
            cache_key = f"{self.ARTICLE_DETAIL_PREFIX}:{article_id}"
            await redis_service.set(cache_key, data, expire=ttl or self.DETAIL_TTL)
            logger.debug(f"文章详情已缓存: {article_id}, TTL={ttl or self.DETAIL_TTL}s")
        except Exception as e:
            logger.error(f"设置文章详情缓存失败: {e}")

    async def invalidate_article(self, article_id: int):
        """使文章相关缓存失效"""
        try:
            # 删除文章详情缓存
            detail_key = f"{self.ARTICLE_DETAIL_PREFIX}:{article_id}"
            await redis_service.delete(detail_key)

            # 删除所有文章列表缓存（简化处理，实际应该更精细）
            pattern = f"{self.ARTICLE_LIST_PREFIX}:*"
            keys = await self._find_keys_by_pattern(pattern)
            if keys:
                await redis_service.delete(*keys)

            # 删除计数缓存
            count_key = f"{self.ARTICLE_COUNT_PREFIX}:all"
            await redis_service.delete(count_key)

            logger.info(f"文章 {article_id} 相关缓存已失效")
        except Exception as e:
            logger.error(f"使文章缓存失效失败: {e}")

    async def invalidate_category_articles(self, category_id: int):
        """使分类下的文章列表缓存失效"""
        try:
            pattern = f"{self.ARTICLE_LIST_PREFIX}:*category:{category_id}:*"
            keys = await self._find_keys_by_pattern(pattern)
            if keys:
                await redis_service.delete(*keys)
                logger.info(f"分类 {category_id} 文章列表缓存已失效")
        except Exception as e:
            logger.error(f"使分类文章缓存失效失败: {e}")

    async def get_article_count(self, status: str = "published") -> Optional[int]:
        """获取缓存的文章数量"""
        try:
            cache_key = f"{self.ARTICLE_COUNT_PREFIX}:{status}"
            cached_count = await redis_service.get(cache_key)

            if cached_count is not None:
                return int(cached_count)

            return None
        except Exception as e:
            logger.error(f"获取文章数量缓存失败: {e}")
            return None

    async def set_article_count(self, count: int, status: str = "published", ttl: Optional[int] = None):
        """设置文章数量缓存"""
        try:
            cache_key = f"{self.ARTICLE_COUNT_PREFIX}:{status}"
            await redis_service.set(cache_key, count, expire=ttl or self.COUNT_TTL)
        except Exception as e:
            logger.error(f"设置文章数量缓存失败: {e}")

    def _build_list_key(
            self,
            page: int,
            per_page: int,
            search: str = "",
            category_id: Optional[int] = None,
            user_id: Optional[int] = None,
            status: Optional[str] = None,
    ) -> str:
        """构建文章列表缓存键"""
        parts = [self.ARTICLE_LIST_PREFIX, f"page:{page}", f"per:{per_page}"]

        if search:
            parts.append(f"search:{search}")
        if category_id:
            parts.append(f"category:{category_id}")
        if user_id:
            parts.append(f"user:{user_id}")
        if status:
            parts.append(f"status:{status}")

        return ":".join(parts)

    async def _find_keys_by_pattern(self, pattern: str) -> List[str]:
        """查找匹配模式的键"""
        try:
            keys = []
            cursor = 0
            while True:
                cursor, batch = await redis_service.redis.scan(cursor=cursor, match=pattern, count=100)
                keys.extend(batch)
                if cursor == 0:
                    break
            return keys
        except Exception as e:
            logger.error(f"查找键失败: {e}")
            return []


# 全局实例
article_cache_service = ArticleCacheService()
