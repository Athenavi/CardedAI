"""
文章搜索优化服务

功能：
1. 全文搜索（标题、内容、摘要）
2. 搜索结果高亮
3. 高级过滤（分类、标签、日期、作者）
4. 搜索建议（自动完成）
5. 搜索历史
6. 热门搜索统计
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.article_content import ArticleContent
from shared.models.category import Category
from shared.models.search_history import SearchHistory


class ArticleSearchService:
    """
    文章搜索优化服务
    
    提供高性能的全文搜索、高亮、过滤等功能
    """

    async def search_articles(
            self,
            db: AsyncSession,
            query: str,
            category_id: Optional[int] = None,
            author_id: Optional[int] = None,
            date_from: Optional[datetime] = None,
            date_to: Optional[datetime] = None,
            status: str = "published",
            page: int = 1,
            per_page: int = 20,
            sort_by: str = "relevance"
    ) -> Dict:
        """
        搜索文章
        
        Args:
            db: 数据库会话
            query: 搜索关键词
            category_id: 分类ID过滤
            author_id: 作者ID过滤
            date_from: 起始日期
            date_to: 结束日期
            status: 文章状态
            page: 页码
            per_page: 每页数量
            sort_by: 排序方式 (relevance, date, views)
            
        Returns:
            搜索结果和分页信息
        """
        # 构建基础查询
        stmt = (
            select(Article)
            .join(ArticleContent, Article.id == ArticleContent.article_id, isouter=True)
            .where(Article.status == status)
        )

        # 全文搜索条件
        if query:
            search_conditions = [
                Article.title.ilike(f"%{query}%"),
                Article.excerpt.ilike(f"%{query}%"),
            ]

            # 如果有关联内容，也搜索内容
            search_conditions.append(
                ArticleContent.content.ilike(f"%{query}%")
            )

            stmt = stmt.where(or_(*search_conditions))

        # 分类过滤
        if category_id:
            stmt = stmt.where(Article.category_id == category_id)

        # 作者过滤
        if author_id:
            stmt = stmt.where(Article.author_id == author_id)

        # 日期范围过滤
        if date_from:
            stmt = stmt.where(Article.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Article.created_at <= date_to)

        # 排序
        if sort_by == "date":
            stmt = stmt.order_by(desc(Article.created_at))
        elif sort_by == "views":
            stmt = stmt.order_by(desc(Article.views))
        else:  # relevance - 默认按相关性（这里简化为按创建时间）
            stmt = stmt.order_by(desc(Article.created_at))

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # 分页
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        result = await db.execute(stmt)
        articles = result.scalars().all()

        # 高亮搜索结果
        highlighted_articles = []
        for article in articles:
            article_dict = article.to_dict()

            # 添加高亮字段
            if query:
                article_dict['highlighted_title'] = self._highlight_text(
                    article.title, query
                )
                article_dict['highlighted_excerpt'] = self._highlight_text(
                    article.excerpt or "", query
                )
            else:
                article_dict['highlighted_title'] = article.title
                article_dict['highlighted_excerpt'] = article.excerpt

            highlighted_articles.append(article_dict)

        # 记录搜索历史
        if query:
            await self.record_search_history(db, query)

        return {
            'articles': highlighted_articles,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'query': query,
        }

    def _highlight_text(self, text: str, query: str, max_length: int = 200) -> str:
        """
        高亮文本中的搜索关键词
        
        Args:
            text: 原始文本
            query: 搜索关键词
            max_length: 最大长度
            
        Returns:
            高亮后的文本
        """
        if not query or not text:
            return text

        # 查找关键词位置
        query_lower = query.lower()
        text_lower = text.lower()

        # 找到第一个匹配位置
        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:max_length] + "..." if len(text) > max_length else text

        # 截取上下文
        start = max(0, pos - 50)
        end = min(len(text), pos + len(query) + 150)

        snippet = text[start:end]

        # 添加省略号
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        # 高亮关键词（使用 HTML 标签）
        highlighted = snippet.replace(
            query,
            f"<mark>{query}</mark>",
            1  # 只替换第一个
        )

        return highlighted

    async def get_search_suggestions(
            self,
            db: AsyncSession,
            query: str,
            limit: int = 5
    ) -> List[str]:
        """
        获取搜索建议（自动完成）
        
        Args:
            db: 数据库会话
            query: 搜索前缀
            limit: 返回数量
            
        Returns:
            搜索建议列表
        """
        # 从热门文章标题中获取建议
        stmt = (
            select(Article.title)
            .where(
                Article.status == "published",
                Article.title.ilike(f"{query}%")
            )
            .order_by(desc(Article.views))
            .limit(limit)
        )

        result = await db.execute(stmt)
        titles = result.scalars().all()

        return list(titles)

    async def record_search_history(
            self,
            db: AsyncSession,
            query: str,
            user_id: Optional[int] = None
    ):
        """
        记录搜索历史
        
        Args:
            db: 数据库会话
            query: 搜索关键词
            user_id: 用户ID（可选）
        """
        # 检查是否已存在相同的搜索记录（最近1小时内）
        one_hour_ago = datetime.now() - timedelta(hours=1)

        stmt = select(SearchHistory).where(
            SearchHistory.query == query,
            SearchHistory.created_at >= one_hour_ago
        )

        if user_id:
            stmt = stmt.where(SearchHistory.user_id == user_id)

        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # 更新计数
            existing.count += 1
            existing.updated_at = datetime.now()
        else:
            # 创建新记录
            history = SearchHistory(
                query=query,
                user_id=user_id,
                count=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(history)

        await db.commit()

    async def get_popular_searches(
            self,
            db: AsyncSession,
            days: int = 7,
            limit: int = 10
    ) -> List[Dict]:
        """
        获取热门搜索
        
        Args:
            db: 数据库会话
            days: 统计天数
            limit: 返回数量
            
        Returns:
            热门搜索列表
        """
        since = datetime.now() - timedelta(days=days)

        stmt = (
            select(
                SearchHistory.query,
                func.sum(SearchHistory.count).label('total_count')
            )
            .where(SearchHistory.created_at >= since)
            .group_by(SearchHistory.query)
            .order_by(desc('total_count'))
            .limit(limit)
        )

        result = await db.execute(stmt)
        rows = result.all()

        return [
            {'query': row.query, 'count': row.total_count}
            for row in rows
        ]

    async def clear_old_search_history(
            self,
            db: AsyncSession,
            days: int = 30
    ):
        """
        清理旧的搜索历史
        
        Args:
            db: 数据库会话
            days: 保留天数
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        stmt = (
            select(SearchHistory)
            .where(SearchHistory.updated_at < cutoff_date)
        )

        result = await db.execute(stmt)
        old_records = result.scalars().all()

        for record in old_records:
            await db.delete(record)

        await db.commit()


# 全局实例
article_search_service = ArticleSearchService()
