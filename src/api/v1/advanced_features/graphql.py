"""
GraphQL API 路由

提供 GraphQL endpoint 和 GraphiQL 界面
"""
from strawberry.fastapi import GraphQLRouter

from src.api.v1.graphql_schema import schema

# 创建 GraphQL router（GraphiQL 界面默认启用）
graphql_app = GraphQLRouter(schema)

# 导出为 FastAPI router
router = graphql_app
