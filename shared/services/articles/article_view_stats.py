"""
文章阅读统计优化服务

功能：
1. 使用 Redis 缓存阅读量计数（减少数据库写入压力）
2. 异步批量同步到数据库
3. 防刷机制（同一用户/IP 短时间内只计一次）
4. 支持实时查询和定期刷新
"""
from typing import Optional

from src.extensions import cache


class ArticleViewStatsService:
    """
    文章阅读统计服务
    
    使用 Redis 进行高性能计数，定期批量同步到数据库
    """

    def __init__(self):
        # Redis key 前缀
        self.VIEW_COUNT_KEY = "article:view_count:{}"  # article_id -> count
        self.VIEW_RECORD_KEY = "article:view_record:{}:{}"  # article_id:user_or_ip
        # 防刷时间窗口（秒）- 同一用户/IP 在此时间内只计一次
        self.ANTI_SPAM_WINDOW = 300  # 5分钟
        # 批量同步阈值 - 达到此数量时同步到数据库
        self.BATCH_SYNC_THRESHOLD = 100
        # 定时同步间隔（秒）
        self.SYNC_INTERVAL = 60  # 1分钟

    async def record_view(self, article_id: int, user_id: Optional[int] = None, ip: Optional[str] = None) -> bool:
        """
        记录文章阅读
        
        Args:
            article_id: 文章ID
            user_id: 用户ID（如果已登录）
            ip: 用户IP
            
        Returns:
            是否成功记录（False 表示被防刷机制拦截）
        """
        # 生成唯一标识（优先使用用户ID，其次使用IP）
        identifier = f"user:{user_id}" if user_id else f"ip:{ip}"

        # 检查防刷
        view_record_key = self.VIEW_RECORD_KEY.format(article_id, identifier)
        exists = await cache.get(view_record_key)

        if exists:
            # 在防刷时间窗口内，不重复计数
            return False

        # 增加阅读计数
        view_count_key = self.VIEW_COUNT_KEY.format(article_id)
        await cache.incr(view_count_key)

        # 设置防刷记录（过期时间为防刷窗口）
        await cache.set(view_record_key, "1", ex=self.ANTI_SPAM_WINDOW)

        return True

    async def get_view_count(self, article_id: int) -> int:
        """
        获取文章阅读量（从 Redis 缓存）
        
        Args:
            article_id: 文章ID
            
        Returns:
            阅读量
        """
        view_count_key = self.VIEW_COUNT_KEY.format(article_id)
        count = await cache.get(view_count_key)

        if count is None:
            # 如果 Redis 中没有，返回 0
            return 0

        return int(count)

    async def sync_to_database(self, article_id: int, db_session):
        """
        同步阅读量到数据库
        
        Args:
            article_id: 文章ID
            db_session: 数据库会话
        """
        from shared.models.article import Article
        from sqlalchemy import select

        # 获取 Redis 中的计数
        view_count_key = self.VIEW_COUNT_KEY.format(article_id)
        redis_count = await cache.get(view_count_key)

        if redis_count is None or int(redis_count) == 0:
            return

        # 获取文章当前阅读量
        stmt = select(Article).where(Article.id == article_id)
        result = await db_session.execute(stmt)
        article = result.scalar_one_or_none()

        if not article:
            return

        # 更新数据库
        article.views = (article.views or 0) + int(redis_count)

        # 清空 Redis 计数
        await cache.delete(view_count_key)

        await db_session.commit()

    async def batch_sync_all(self, db_session):
        """
        批量同步所有文章的阅读量到数据库
        
        Args:
            db_session: 数据库会话
        """
        from shared.models.article import Article
        from sqlalchemy import select

        # 获取所有有阅读计数的文章
        pattern = self.VIEW_COUNT_KEY.format("*")
        keys = []

        # 检查是否是 Redis 缓存（具有 redis 属性）
        if hasattr(cache, 'redis'):
            # 使用 Redis 的 scan_iter 方法
            async for key in cache.redis.scan_iter(match=pattern):
                keys.append(key)
        else:
            # 对于 SimpleCache，我们需要遍历所有键来匹配模式
            import re
            pattern_regex = pattern.replace('*', '.*')
            for key in cache._cache.keys():
                if re.match(pattern_regex, key):
                    keys.append(key)

        if not keys:
            return {
                "synced": 0,
                "errors": []
            }

        synced_count = 0
        errors = []

        for key in keys:
            try:
                # 提取 article_id
                article_id = int(key.split(":")[-1])

                # 获取计数
                redis_count = await cache.get(key)
                if redis_count is None or int(redis_count) == 0:
                    continue

                # 更新数据库
                stmt = select(Article).where(Article.id == article_id)
                result = await db_session.execute(stmt)
                article = result.scalar_one_or_none()

                if article:
                    article.views = (article.views or 0) + int(redis_count)
                    synced_count += 1

                # 清空 Redis 计数
                await cache.delete(key)

            except Exception as e:
                errors.append(f"Article {key}: {str(e)}")

        # 提交事务
        if synced_count > 0:
            await db_session.commit()

        return {
            "synced": synced_count,
            "errors": errors
        }

    async def get_top_articles(self, limit: int = 10) -> list:
        """
        获取热门文章（基于 Redis 计数）
        
        Args:
            limit: 返回数量
            
        Returns:
            热门文章列表 [(article_id, view_count), ...]
        """
        pattern = self.VIEW_COUNT_KEY.format("*")
        articles = []

        # 检查是否是 Redis 缓存（具有 redis 属性）
        if hasattr(cache, 'redis'):
            # 使用 Redis 的 scan_iter 方法
            async for key in cache.redis.scan_iter(match=pattern):
                count = await cache.get(key)
                if count and int(count) > 0:
                    article_id = int(key.split(":")[-1])
                    articles.append((article_id, int(count)))
        else:
            # 对于 SimpleCache，我们需要遍历所有键来匹配模式
            import re
            pattern_regex = pattern.replace('*', '.*')
            for key in cache._cache.keys():
                if re.match(pattern_regex, key):
                    count = await cache.get(key)
                    if count and int(count) > 0:
                        article_id = int(key.split(":")[-1])
                        articles.append((article_id, int(count)))

        # 按阅读量排序
        articles.sort(key=lambda x: x[1], reverse=True)

        return articles[:limit]

    async def reset_article_views(self, article_id: int):
        """
        重置文章阅读计数
        
        Args:
            article_id: 文章ID
        """
        view_count_key = self.VIEW_COUNT_KEY.format(article_id)
        await cache.delete(view_count_key)

        # 同时清除防刷记录
        pattern = f"article:view_record:{article_id}:*"

        # 检查是否是 Redis 缓存（具有 redis 属性）
        if hasattr(cache, 'redis'):
            # 使用 Redis 的 scan_iter 方法
            async for key in cache.redis.scan_iter(match=pattern):
                await cache.delete(key)
        else:
            # 对于 SimpleCache，我们需要遍历所有键来匹配模式
            import re
            pattern_regex = pattern.replace('*', '.*')
            for key in cache._cache.keys():
                if re.match(pattern_regex, key):
                    await cache.delete(key)


# 全局实例
article_view_stats = ArticleViewStatsService()
