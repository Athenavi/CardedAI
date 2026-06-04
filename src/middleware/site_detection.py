"""
多站点支持 - 站点检测中间件
自动识别当前请求所属的站点
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SiteDetectionMiddleware(BaseHTTPMiddleware):
    """
    站点检测中间件
    
    功能:
    1. 基于域名识别站点
    2. 基于路径前缀识别站点
    3. 注入站点信息到 request.state
    4. 提供默认站点回退
    """

    async def dispatch(self, request: Request, call_next):
        # 尝试识别站点
        site = await self.detect_site(request)

        # 注入站点信息
        request.state.site = site
        request.state.site_id = site.id if site else None

        # 继续处理请求
        response = await call_next(request)

        # 添加站点信息到响应头（可选，用于调试）
        if site:
            response.headers['X-Site-ID'] = str(site.id)
            response.headers['X-Site-Slug'] = site.slug

        return response

    async def detect_site(self, request: Request):
        """
        检测当前请求所属的站点
        
        优先级:
        1. 域名匹配
        2. 路径前缀匹配
        3. 默认站点
        """
        from shared.models.site import Site
        from src.extensions import get_sync_db
        from sqlalchemy import select, or_

        host = request.headers.get('host', '')
        path = request.url.path

        # 移除端口号
        if ':' in host:
            host = host.split(':')[0]

        with next(get_sync_db()) as db:
            # 1. 尝试通过域名匹配
            if host:
                stmt = select(Site).where(
                    Site.domain == host,
                    Site.is_active == True
                )
                result = db.execute(stmt)
                site = result.scalar_one_or_none()

                if site:
                    return site

            # 2. 尝试通过路径前缀匹配
            # 例如: /site1/articles -> 匹配 path='/site1'
            path_parts = [p for p in path.split('/') if p]
            if path_parts:
                potential_slug = path_parts[0]

                stmt = select(Site).where(
                    Site.slug == potential_slug,
                    Site.is_active == True,
                    Site.path.like(f'/{potential_slug}%')
                )
                result = db.execute(stmt)
                site = result.scalar_one_or_none()

                if site:
                    return site

            # 3. 返回默认站点
            stmt = select(Site).where(
                Site.is_default == True,
                Site.is_active == True
            )
            result = db.execute(stmt)
            site = result.scalar_one_or_none()

            if site:
                return site

            # 4. 返回第一个激活的站点
            stmt = select(Site).where(
                Site.is_active == True
            ).order_by(Site.id.asc()).limit(1)
            result = db.execute(stmt)
            site = result.scalar_one_or_none()

            return site


def get_current_site(request: Request):
    """
    获取当前站点
    
    Args:
        request: FastAPI Request 对象
        
    Returns:
        Site 对象或 None
    """
    return getattr(request.state, 'site', None)


def require_site(request: Request):
    """
    要求必须有站点上下文
    
    Args:
        request: FastAPI Request 对象
        
    Returns:
        Site 对象
        
    Raises:
        HTTPException: 如果没有检测到站点
    """
    from fastapi import HTTPException, status

    site = get_current_site(request)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    return site
