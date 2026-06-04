"""
文章定时发布服务

功能：
1. 定时发布调度器
2. 自动发布到期文章
3. 发布队列管理
4. 发布历史记录
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class ScheduledPublishService:
    """
    文章定时发布服务
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_article(
            self,
            article_id: int,
            publish_at: datetime
    ) -> Dict:
        """
        设置文章定时发布
        
        Args:
            article_id: 文章ID
            publish_at: 发布时间
            
        Returns:
            调度结果
        """
        from shared.models.article import Article

        # 验证文章存在
        article = await self.db.get(Article, article_id)

        if not article:
            return {
                'success': False,
                'message': '文章不存在',
            }

        # 验证发布时间
        if publish_at <= datetime.now():
            return {
                'success': False,
                'message': '发布时间必须晚于当前时间',
            }

        # 更新文章的定时发布时间
        article.scheduled_publish_at = publish_at
        article.status = 0  # 设置为草稿状态
        article.updated_at = datetime.now()

        await self.db.commit()

        return {
            'success': True,
            'message': f'文章已安排在 {publish_at.strftime("%Y-%m-%d %H:%M")} 发布',
            'article_id': article_id,
            'publish_at': publish_at.isoformat(),
        }

    async def cancel_scheduled_publish(self, article_id: int) -> Dict:
        """
        取消定时发布
        
        Args:
            article_id: 文章ID
            
        Returns:
            取消结果
        """
        from shared.models.article import Article

        article = await self.db.get(Article, article_id)

        if not article:
            return {
                'success': False,
                'message': '文章不存在',
            }

        if not article.scheduled_publish_at:
            return {
                'success': False,
                'message': '文章未设置定时发布',
            }

        # 清除定时发布时间
        article.scheduled_publish_at = None
        article.updated_at = datetime.now()

        await self.db.commit()

        return {
            'success': True,
            'message': '已取消定时发布',
            'article_id': article_id,
        }

    async def publish_due_articles(self) -> Dict:
        """
        发布所有到期的定时文章
        
        Returns:
            发布结果统计
        """
        from shared.models.article import Article

        now = datetime.now()

        # 查询所有到期的定时发布文章
        stmt = select(Article).where(
            Article.scheduled_publish_at.isnot(None),
            Article.scheduled_publish_at <= now,
            Article.status == 0  # 草稿状态
        )

        result = await self.db.execute(stmt)
        articles = result.scalars().all()

        published_count = 0
        failed_articles = []

        for article in articles:
            try:
                # 发布文章
                article.status = 1  # 已发布
                article.published_at = now
                article.scheduled_publish_at = None
                article.updated_at = now

                published_count += 1
            except Exception as e:
                failed_articles.append({
                    'article_id': article.id,
                    'error': str(e),
                })

        await self.db.commit()

        return {
            'success': True,
            'published_count': published_count,
            'failed_count': len(failed_articles),
            'failed_articles': failed_articles,
        }

    async def get_scheduled_articles(
            self,
            limit: int = 50,
            offset: int = 0
    ) -> List[Dict]:
        """
        获取待发布的文章列表
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            待发布文章列表
        """
        from shared.models.article import Article
        from shared.models.user import User

        now = datetime.now()

        # 查询所有已设置定时发布的文章
        stmt = (
            select(Article, User.username)
            .join(User, Article.author_id == User.id, isouter=True)
            .where(
                Article.scheduled_publish_at.isnot(None),
                Article.status == 0
            )
            .order_by(Article.scheduled_publish_at.asc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'author': username or 'Unknown',
                'scheduled_publish_at': article.scheduled_publish_at.isoformat(),
                'status': 'scheduled',
                'time_until_publish': self._calculate_time_until(article.scheduled_publish_at),
            }
            for article, username in rows
        ]

    async def get_upcoming_publishes(self, hours: int = 24) -> List[Dict]:
        """
        获取即将发布的文章（未来N小时内）
        
        Args:
            hours: 小时数
            
        Returns:
            即将发布的文章列表
        """
        from shared.models.article import Article

        now = datetime.now()
        future_time = now + timedelta(hours=hours)

        stmt = select(Article).where(
            Article.scheduled_publish_at.isnot(None),
            Article.scheduled_publish_at > now,
            Article.scheduled_publish_at <= future_time,
            Article.status == 0
        ).order_by(Article.scheduled_publish_at.asc())

        result = await self.db.execute(stmt)
        articles = result.scalars().all()

        return [
            {
                'id': article.id,
                'title': article.title,
                'scheduled_publish_at': article.scheduled_publish_at.isoformat(),
                'hours_until': (article.scheduled_publish_at - now).total_seconds() / 3600,
            }
            for article in articles
        ]

    def _calculate_time_until(self, publish_at: datetime) -> str:
        """
        计算距离发布还有多久
        
        Args:
            publish_at: 发布时间
            
        Returns:
            时间描述字符串
        """
        now = datetime.now()
        delta = publish_at - now

        if delta.total_seconds() < 0:
            return '已过期'

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f'{days}天{hours}小时后'
        elif hours > 0:
            return f'{hours}小时{minutes}分钟后'
        else:
            return f'{minutes}分钟后'


def create_scheduled_publish_service(db: AsyncSession) -> ScheduledPublishService:
    return ScheduledPublishService(db)
