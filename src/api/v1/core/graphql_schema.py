"""
GraphQL 接口入口 (Strawberry)
提供 Headless CMS 的 GraphQL 查询支持
"""
from typing import List, Optional

import strawberry


@strawberry.type
class Article:
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    content: Optional[str]


@strawberry.type
class Query:
    @strawberry.field
    def articles(self) -> List[Article]:
        # 实际实现应查询数据库并返回 Article 列表
        return []


schema = strawberry.Schema(query=Query)
