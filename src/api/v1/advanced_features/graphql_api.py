"""
GraphQL API 支持模块
使用 Strawberry 提供 GraphQL 接口
"""

from datetime import datetime
from typing import List, Optional

import strawberry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.category import Category


# ============ GraphQL 类型定义 ============

@strawberry.type
class ArticleType:
    """文章类型"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    view_count: int
    like_count: int


@strawberry.type
class CategoryType:
    """分类类型"""
    id: int
    name: str
    slug: str
    description: Optional[str]


@strawberry.type
class UserType:
    """用户类型"""
    id: int
    username: str
    email: str
    avatar: Optional[str]


@strawberry.type
class ArticleConnection:
    """文章连接(分页)"""
    articles: List[ArticleType]
    total: int
    page: int
    per_page: int
    has_next: bool


# ============ Query 查询 ============

@strawberry.type
class Query:

    @strawberry.field(description="获取单篇文章")
    async def article(self, info: strawberry.types.Info, id: int) -> Optional[ArticleType]:
        """根据ID获取文章"""
        # 从上下文中获取数据库会话
        db: AsyncSession = info.context['db']

        stmt = select(Article).where(Article.id == id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()

        if not article:
            return None

        return ArticleType(
            id=article.id,
            title=article.title,
            slug=article.slug,
            excerpt=article.excerpt,
            status=article.status,
            created_at=article.created_at,
            updated_at=article.updated_at,
            view_count=article.view_count or 0,
            like_count=article.like_count or 0,
        )

    @strawberry.field(description="获取文章列表")
    async def articles(
            self,
            info: strawberry.types.Info,
            page: int = 1,
            per_page: int = 10,
            category_id: Optional[int] = None,
            search: Optional[str] = None
    ) -> ArticleConnection:
        """获取文章列表,支持分页和筛选"""
        from sqlalchemy import func

        # 从上下文中获取数据库会话
        db: AsyncSession = info.context['db']

        # 构建查询
        stmt = select(Article)
        count_stmt = select(func.count(Article.id))

        # 添加筛选条件
        if category_id:
            stmt = stmt.where(Article.category == category_id)
            count_stmt = count_stmt.where(Article.category == category_id)

        if search:
            stmt = stmt.where(Article.title.contains(search))
            count_stmt = count_stmt.where(Article.title.contains(search))

        # 只获取已发布的文章
        stmt = stmt.where(Article.status == 'published')
        count_stmt = count_stmt.where(Article.status == 'published')

        # 排序
        stmt = stmt.order_by(Article.created_at.desc())

        # 分页
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        # 执行查询
        result = await db.execute(stmt)
        articles = result.scalars().all()

        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 转换为GraphQL类型
        article_types = [
            ArticleType(
                id=a.id,
                title=a.title,
                slug=a.slug,
                excerpt=a.excerpt,
                status=a.status,
                created_at=a.created_at,
                updated_at=a.updated_at,
                view_count=a.view_count or 0,
                like_count=a.like_count or 0,
            )
            for a in articles
        ]

        return ArticleConnection(
            articles=article_types,
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total,
        )

    @strawberry.field(description="获取分类列表")
    async def categories(self, info: strawberry.types.Info) -> List[CategoryType]:
        """获取所有分类"""
        # 从上下文中获取数据库会话
        db: AsyncSession = info.context['db']

        stmt = select(Category)
        result = await db.execute(stmt)
        categories = result.scalars().all()

        return [
            CategoryType(
                id=c.id,
                name=c.name,
                slug=c.slug,
                description=c.description,
            )
            for c in categories
        ]

    @strawberry.field(description="获取单个分类")
    async def category(self, info: strawberry.types.Info, id: int) -> Optional[CategoryType]:
        """根据ID获取分类"""
        # 从上下文中获取数据库会话
        db: AsyncSession = info.context['db']

        stmt = select(Category).where(Category.id == id)
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()

        if not category:
            return None

        return CategoryType(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
        )


# ============ Mutation 变更 ============

@strawberry.type
class Mutation:

    @strawberry.mutation(description="创建文章")
    async def create_article(
            self,
            info: strawberry.types.Info,
            title: str,
            content: str,
            excerpt: Optional[str] = None,
            category_id: Optional[int] = None
    ) -> ArticleType:
        """创建新文章"""
        # 从上下文中获取数据库会话
        db: AsyncSession = info.context['db']

        # 添加认证检查
        user_id = info.context.get('user_id')
        if not user_id:
            raise Exception("未授权，请先登录")

        article = Article(
            title=title,
            slug=title.lower().replace(' ', '-'),
            excerpt=excerpt,
            status='draft',
            user_id=user_id,
            category_id=category_id,
        )

        db.add(article)
        await db.flush()

        # 创建文章内容
        from shared.models.article_content import ArticleContent
        now = datetime.now()
        article_content = ArticleContent(
            article=article.id,
            content=content,
            created_at=now,
            updated_at=now,
        )
        db.add(article_content)
        await db.commit()

        return ArticleType(
            id=article.id,
            title=article.title,
            slug=article.slug,
            excerpt=article.excerpt,
            status=article.status,
            created_at=article.created_at,
            updated_at=article.updated_at,
            view_count=0,
            like_count=0,
        )


# ============ Schema 定义 ============

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
