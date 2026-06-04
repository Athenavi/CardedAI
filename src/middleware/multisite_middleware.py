"""
多站点中间件

根据请求的域名或路径确定当前站点
"""
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from shared.models.site import Site


class MultiSiteMiddleware(BaseHTTPMiddleware):
    """
    多站点中间件

    功能：
    1. 根据请求域名匹配站点
    2. 根据请求路径前缀匹配站点（子目录模式）
    3. 将当前站点信息注入到 request.state
    """

    async def dispatch(self, request: Request, call_next):
        # 跳过静态文件和 API 文档
        path = request.url.path
        if path.startswith('/api/v2/static/') or path in ['/api/v2/docs', '/api/v2/redoc', '/api/v2/openapi.json']:
            return await call_next(request)

        # 获取数据库会话
        from src.extensions import get_async_db_session

        try:
            async with get_async_db_session()() as db:
                current_site = await self._resolve_site(request, db)
                request.state.current_site = current_site
        except Exception as e:
            # 如果无法解析站点，使用默认站点
            request.state.current_site = None

        response = await call_next(request)
        return response

    async def _resolve_site(self, request: Request, db: AsyncSession) -> Site:
        """
        解析当前请求对应的站点

        优先级：
        1. 子域名匹配 (site1.example.com)
        2. 完整域名匹配 (example.com)
        3. 路径前缀匹配 (/site1/...)
        4. 默认站点
        """
        host = request.headers.get('host', '').split(':')[0]  # 移除端口号
        path = request.url.path

        # 1. 尝试通过域名匹配
        if host:
            # 精确匹配域名
            stmt = select(Site).where(
                Site.domain == host,
                Site.is_active == True
            )
            result = await db.execute(stmt)
            site = result.scalar_one_or_none()

            if site:
                return site

            # 尝试匹配子域名
            if '.' in host:
                parts = host.split('.')
                if len(parts) >= 3:
                    # 提取子域名部分 (例如: site1.example.com -> site1)
                    subdomain = parts[0]
                    stmt = select(Site).where(
                        Site.slug == subdomain,
                        Site.is_active == True
                    )
                    result = await db.execute(stmt)
                    site = result.scalar_one_or_none()

                    if site:
                        return site

        # 2. 尝试通过路径前缀匹配
        if path.startswith('/'):
            path_parts = [p for p in path.split('/') if p]
            if path_parts:
                first_segment = path_parts[0]

                # 检查是否是有效的站点 slug
                stmt = select(Site).where(
                    Site.slug == first_segment,
                    Site.is_active == True,
                    Site.path != '/'  # 排除根路径站点
                )
                result = await db.execute(stmt)
                site = result.scalar_one_or_none()

                if site:
                    return site

        # 3. 返回默认站点
        stmt = select(Site).where(
            Site.is_default == True,
            Site.is_active == True
        )
        result = await db.execute(stmt)
        site = result.scalar_one_or_none()

        if site:
            return site

        # 4. 如果没有默认站点，返回第一个激活的站点
        stmt = select(Site).where(
            Site.is_active == True
        ).order_by(Site.id.asc()).limit(1)
        result = await db.execute(stmt)
        site = result.scalar_one_or_none()

        return site


def get_current_site(request: Request) -> Site:
    """
    获取当前请求对应的站点

    Usage:
        from src.middleware.multisite_middleware import get_current_site
        current_site = get_current_site(request)
    """
    return getattr(request.state, 'current_site', None)
