"""
文章查询服务 - 处理文章查询、排序和过滤逻辑
"""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func, desc, or_, and_, case, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.user import User


class ArticleQueryService:
    """文章查询服务（优化版）"""

    # 类级别缓存粘性条件，避免重复构建
    _sticky_condition = None

    @staticmethod
    def _get_sticky_condition():
        """
        获取粘性文章判断条件（带简单缓存）
        
        Returns:
            SQLAlchemy condition object
        """
        if ArticleQueryService._sticky_condition is None:
            now = datetime.now()
            ArticleQueryService._sticky_condition = and_(
                Article.is_sticky == True,
                or_(
                    Article.sticky_until == None,
                    Article.sticky_until > now
                )
            )
        return ArticleQueryService._sticky_condition
    
    @staticmethod
    async def get_articles_list(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        include_sticky: bool = True,
        is_admin: bool = False
    ) -> Tuple[List[Article], int]:
        """
        获取文章列表（支持粘性文章优先排序）
        
        Args:
            db: 数据库会话
            page: 页码
            per_page: 每页数量
            search: 搜索关键词
            category_id: 分类ID
            user_id: 用户ID
            status: 状态筛选 (draft/published/deleted)
            include_sticky: 是否包含粘性文章并优先排序
            is_admin: 是否为管理员
            
        Returns:
            (文章列表, 总数)
        """
        # 构建基础查询
        query = select(Article).join(User, Article.user == User.id)
        
        # 非管理员只能查看已发布且非隐藏的文章
        if not is_admin:
            query = query.where(
                Article.status == 1,
                Article.hidden == False
            )
        
        # 搜索功能
        if search:
            query = query.where(
                or_(
                    Article.title.contains(search),
                    Article.excerpt.contains(search)
                )
            )
        
        # 分类筛选
        if category_id:
            query = query.where(Article.category == category_id)
        
        # 用户筛选
        if user_id:
            query = query.where(Article.user == user_id)
        
        # 状态筛选
        if status:
            if status == 'draft':
                query = query.where(Article.status == 0)
            elif status == 'published':
                query = query.where(Article.status == 1)
            elif status == 'deleted':
                query = query.where(Article.status == -1)

        # 获取总数 - 使用简单的 COUNT 查询，避免子查询
        count_query = select(func.count(Article.id))
        if not is_admin:
            count_query = count_query.where(
                Article.hidden == False,
                Article.status == 1
            )
        if category_id:
            count_query = count_query.where(Article.category == category_id)
        if user_id:
            count_query = count_query.where(Article.user == user_id)
        if status:
            if status == 'draft':
                count_query = count_query.where(Article.status == 0)
            elif status == 'published':
                count_query = count_query.where(Article.status == 1)
            elif status == 'deleted':
                count_query = count_query.where(Article.status == -1)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 排序逻辑：粘性文章优先，然后按sort_order和创建时间排序
        if include_sticky:
            sticky_condition = ArticleQueryService._get_sticky_condition()

            # 排序：粘性文章在前，然后按sort_order升序，最后按创建时间降序
            query = query.order_by(
                desc(case((sticky_condition, 1), else_=0)),
                Article.sort_order.asc(),
                desc(Article.created_at)
            )
        else:
            # 普通排序：按sort_order升序，然后按创建时间降序
            query = query.order_by(
                Article.sort_order.asc(),
                desc(Article.created_at)
            )
        
        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        # 执行查询
        result = await db.execute(query)
        articles = result.scalars().all()
        
        return list(articles), total
    
    @staticmethod
    async def get_homepage_articles(
        db: AsyncSession,
        limit: int = 10
    ) -> List[Article]:
        """
        获取首页文章列表（粘性文章优先）
        
        Args:
            db: 数据库会话
            limit: 返回数量限制
            
        Returns:
            文章列表
        """
        sticky_condition = ArticleQueryService._get_sticky_condition()
        
        query = select(Article).where(
            Article.status == 1,
            Article.hidden == False,
            Article.is_vip_only == False
        ).order_by(
            desc(case((sticky_condition, 1), else_=0)),
            Article.sort_order.asc(),
            desc(Article.created_at)
        ).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_category_articles(
        db: AsyncSession,
        category_id: int,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[Article], int]:
        """
        获取分类下的文章列表（支持粘性文章）
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            page: 页码
            per_page: 每页数量
            
        Returns:
            (文章列表, 总数)
        """
        return await ArticleQueryService.get_articles_list(
            db=db,
            page=page,
            per_page=per_page,
            category_id=category_id,
            include_sticky=True,
            is_admin=False
        )
    
    @staticmethod
    async def toggle_sticky_status(
        db: AsyncSession,
        article_id: int,
        is_sticky: bool,
        sticky_until: Optional[datetime] = None
    ) -> Optional[Article]:
        """
        切换文章粘性状态
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            is_sticky: 是否置顶
            sticky_until: 置顶过期时间
            
        Returns:
            更新后的文章对象
        """
        query = select(Article).where(Article.id == article_id)
        result = await db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return None
        
        article.is_sticky = is_sticky
        article.sticky_until = sticky_until
        
        await db.commit()
        await db.refresh(article)
        
        return article
    
    @staticmethod
    async def clean_expired_sticky_articles(db: AsyncSession) -> int:
        """
        清理过期的粘性文章（批量更新优化）
        
        Args:
            db: 数据库会话
            
        Returns:
            清理的文章数量
        """
        now = datetime.now()

        # 使用批量 UPDATE 代替逐条更新
        result = await db.execute(
            update(Article)
            .where(
                Article.is_sticky == True,
                Article.sticky_until != None,
                Article.sticky_until <= now
            )
            .values(is_sticky=False, sticky_until=None)
        )

        if result.rowcount > 0:
            await db.commit()

        return result.rowcount or 0


# 全局实例
article_query_service = ArticleQueryService()
