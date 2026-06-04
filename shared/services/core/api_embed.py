"""
API嵌入服务

支持_embed参数，允许客户端在单个请求中获取关联资源
避免N+1查询问题，提高API效率
"""

import re
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class APIEmbedService:
    """
    API嵌入服务

    提供资源的嵌入式加载功能
    支持常见的关联关系预加载
    """

    def __init__(self, db: AsyncSession):
        """
        初始化嵌入服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def embed_article_relations(
            self,
            articles: List[Any],
            embed_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        嵌入文章关联数据

        Args:
            articles: 文章列表
            embed_fields: 要嵌入的字段列表

        Returns:
            包含嵌入数据的文章列表
        """
        if not articles:
            return []

        # 收集需要加载的ID
        user_ids = set()
        category_ids = set()

        for article in articles:
            if 'author' in embed_fields and hasattr(article, 'user'):
                user_ids.add(article.user)
            if 'category' in embed_fields and hasattr(article, 'category'):
                category_ids.add(article.category)

        # 批量加载用户
        users_dict = {}
        if 'author' in embed_fields and user_ids:
            from shared.models.user import User
            result = await self.db.execute(
                select(User).where(User.id.in_(user_ids))
            )
            users_dict = {u.id: u for u in result.scalars().all()}

        # 批量加载分类
        categories_dict = {}
        if 'category' in embed_fields and category_ids:
            from shared.models.category import Category
            result = await self.db.execute(
                select(Category).where(Category.id.in_(category_ids))
            )
            categories_dict = {c.id: c for c in result.scalars().all()}

        # 构建结果
        result = []
        for article in articles:
            article_data = self._serialize_article(article)

            # 嵌入作者信息
            if 'author' in embed_fields and hasattr(article, 'user'):
                user = users_dict.get(article.user)
                if user:
                    article_data['_embedded'] = article_data.get('_embedded', {})
                    article_data['_embedded']['author'] = {
                        'id': user.id,
                        'username': user.username,
                        'profile_picture': user.profile_picture,
                        'bio': user.bio,
                    }

            # 嵌入分类信息
            if 'category' in embed_fields and hasattr(article, 'category'):
                category = categories_dict.get(article.category)
                if category:
                    article_data['_embedded'] = article_data.get('_embedded', {})
                    article_data['_embedded']['category'] = {
                        'id': category.id,
                        'name': category.name,
                        'slug': category.slug,
                        'description': category.description,
                    }

            result.append(article_data)

        return result

    def _serialize_article(self, article: Any) -> Dict[str, Any]:
        """序列化文章对象"""
        return {
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'excerpt': article.excerpt,
            'cover_image': article.cover_image,
            'tags': [t.strip() for t in re.split(r'[,;]', article.tags_list) if t.strip()] if article.tags_list else [],
            'views': article.views or 0,
            'likes': article.likes or 0,
            'status': article.status,
            'created_at': article.created_at.isoformat() if article.created_at else None,
            'updated_at': article.updated_at.isoformat() if article.updated_at else None,
        }

    @staticmethod
    def parse_embed_param(embed_param: str) -> List[str]:
        """
        解析_embed参数

        Args:
            embed_param: _embed参数值，逗号分隔

        Returns:
            嵌入字段列表
        """
        if not embed_param:
            return []

        return [field.strip() for field in embed_param.split(',') if field.strip()]

    @staticmethod
    def validate_embed_fields(
            requested_fields: List[str],
            allowed_fields: List[str]
    ) -> List[str]:
        """
        验证嵌入字段

        Args:
            requested_fields: 请求的字段列表
            allowed_fields: 允许的字段列表

        Returns:
            有效的字段列表
        """
        return [field for field in requested_fields if field in allowed_fields]


# 导出
__all__ = ['APIEmbedService']
