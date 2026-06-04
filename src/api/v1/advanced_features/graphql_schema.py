"""
GraphQL Schema 定义

使用 Strawberry 实现 GraphQL API
"""
from datetime import datetime
from typing import List, Optional

import strawberry

from shared.models.article import Article as ArticleModel
from shared.models.category import Category as CategoryModel
from shared.models.user import User as UserModel
from src.extensions import get_async_db_session


# ==================== 类型定义 ====================

@strawberry.type
class UserType:
    """用户类型"""
    id: int
    username: str
    email: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    date_joined: Optional[datetime] = None

    @strawberry.field
    def display_name(self) -> str:
        return self.username


@strawberry.type
class CategoryType:
    """分类类型"""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


@strawberry.type
class ArticleType:
    """文章类型"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    status: str = "published"
    views: int = 0
    likes: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author_id: Optional[int] = None
    category_id: Optional[int] = None

    # 关联数据
    author: Optional[UserType] = None
    category: Optional[CategoryType] = None

    @strawberry.field
    async def content(self) -> Optional[str]:
        """获取文章内容（懒加载）"""
        from shared.models.article_content import ArticleContent
        from sqlalchemy import select

        db = get_async_db_session()
        stmt = select(ArticleContent).where(ArticleContent.article == self.id)
        result = await db.execute(stmt)
        content_obj = result.scalar_one_or_none()

        if content_obj:
            return content_obj.content
        return None

    @strawberry.field
    async def tags(self) -> List[str]:
        """获取文章标签"""
        # Query tags from database
        # Example implementation:
        # from shared.models.article_tag import ArticleTag
        # from shared.models.tag import Tag
        # from sqlalchemy import select
        # 
        # stmt = (
        #     select(Tag.name)
        #     .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        #     .where(ArticleTag.article_id == self.id)
        # )
        # result = await db.execute(stmt)
        # tags = [row[0] for row in result.all()]
        # return tags

        # For now, return empty list
        return []


# ==================== 查询 ====================

@strawberry.type
class Query:
    """GraphQL 查询"""

    @strawberry.field
    async def article(self, info: strawberry.types.Info, id: int) -> Optional[ArticleType]:
        """获取单篇文章"""
        from sqlalchemy import select

        db = get_async_db_session()
        stmt = select(ArticleModel).where(ArticleModel.id == id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()

        if not article:
            return None

        # 转换为 GraphQL 类型
        return ArticleType(
            id=article.id,
            title=article.title,
            slug=article.slug,
            excerpt=article.excerpt,
            status=article.status,
            views=article.views or 0,
            likes=article.likes or 0,
            created_at=article.created_at,
            updated_at=article.updated_at,
            author_id=article.author_id,
            category_id=article.category_id,
        )

    @strawberry.field
    async def articles(
            self,
            info: strawberry.types.Info,
            page: int = 1,
            per_page: int = 10,
            category_id: Optional[int] = None,
            status: Optional[str] = "published"
    ) -> List[ArticleType]:
        """获取文章列表"""
        from sqlalchemy import select

        db = get_async_db_session()
        stmt = select(ArticleModel)

        if category_id:
            stmt = stmt.where(ArticleModel.category == category_id)

        if status:
            stmt = stmt.where(ArticleModel.status == status)

        stmt = stmt.order_by(ArticleModel.created_at.desc())
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        result = await db.execute(stmt)
        articles = result.scalars().all()

        return [
            ArticleType(
                id=article.id,
                title=article.title,
                slug=article.slug,
                excerpt=article.excerpt,
                status=article.status,
                views=article.views or 0,
                likes=article.likes or 0,
                created_at=article.created_at,
                updated_at=article.updated_at,
                author_id=article.author_id,
                category_id=article.category_id,
            )
            for article in articles
        ]

    @strawberry.field
    async def user(self, info: strawberry.types.Info, id: int) -> Optional[UserType]:
        """获取用户信息"""
        from sqlalchemy import select

        db = get_async_db_session()
        stmt = select(UserModel).where(UserModel.id == id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return UserType(
            id=user.id,
            username=user.username,
            email=user.email,
            profile_picture=user.profile_picture,
            bio=user.bio,
            is_active=user.is_active,
            date_joined=user.date_joined,
        )

    @strawberry.field
    async def categories(self, info: strawberry.types.Info) -> List[CategoryType]:
        """获取分类列表"""
        from sqlalchemy import select

        db = get_async_db_session()
        stmt = select(CategoryModel).order_by(CategoryModel.name)
        result = await db.execute(stmt)
        categories = result.scalars().all()

        return [
            CategoryType(
                id=category.id,
                name=category.name,
                slug=category.slug,
                description=category.description,
                parent_id=category.parent_id,
            )
            for category in categories
        ]


# ==================== Schema ====================

schema = strawberry.Schema(query=Query)
