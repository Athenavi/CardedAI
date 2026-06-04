"""
站点配额管理服务

管理每个站点的资源配额（文章数、用户数、存储空间等）
"""
from typing import Dict
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.site import Site

logger = logging.getLogger(__name__)


class SiteQuotaService:
    """站点配额服务"""

    # 默认配额限制
    DEFAULT_QUOTAS = {
        'max_articles': 10000,  # 最大文章数
        'max_users': 1000,  # 最大用户数
        'max_media_size_mb': 5000,  # 最大媒体存储空间 (MB)
        'max_categories': 500,  # 最大分类数
        'max_plugins': 50,  # 最大插件数
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_site_quota(self, site_id: int) -> Dict:
        """
        获取站点配额信息

        Args:
            site_id: 站点ID

        Returns:
            配额信息，包括限制和当前使用量
        """
        # 获取站点
        stmt = select(Site).where(Site.id == site_id)
        result = await self.db.execute(stmt)
        site = result.scalar_one_or_none()

        if not site:
            raise ValueError(f"Site {site_id} not found")

        # 从 settings 中获取自定义配额，或使用默认值
        quotas = site.settings.get('quotas', self.DEFAULT_QUOTAS) if site.settings else self.DEFAULT_QUOTAS

        usage = await self._calculate_usage(site_id)

        return {
            'site_id': site_id,
            'site_name': site.name,
            'quotas': quotas,
            'usage': usage,
            'utilization': {
                key: round((usage.get(key, 0) / quotas[key]) * 100, 2) if quotas[key] > 0 else 0
                for key in quotas.keys()
            }
        }

    async def _calculate_usage(self, site_id: int) -> Dict:
        """
        计算站点资源使用量

        Args:
            site_id: 站点ID

        Returns:
            使用量字典
        """
        from shared.models.article import Article
        from shared.models.user import User
        from shared.models.media import Media
        from shared.models.category import Category
        from sqlalchemy import select, func

        usage = {
            'articles': 0,
            'users': 0,
            'media_size_mb': 0,
            'categories': 0,
            'plugins': 0,
        }

        try:
            # 统计文章数
            article_result = await self.db.execute(
                select(func.count(Article.id)).where(Article.site_id == site_id)
            )
            usage['articles'] = article_result.scalar() or 0

            # 统计用户数
            user_result = await self.db.execute(
                select(func.count(User.id)).where(User.site_id == site_id)
            )
            usage['users'] = user_result.scalar() or 0

            # 统计媒体文件大小
            media_result = await self.db.execute(
                select(func.sum(Media.file_size)).where(Media.site_id == site_id)
            )
            total_size_bytes = media_result.scalar() or 0
            usage['media_size_mb'] = round(total_size_bytes / (1024 * 1024), 2)

            # 统计分类数
            category_result = await self.db.execute(
                select(func.count(Category.id)).where(Category.site_id == site_id)
            )
            usage['categories'] = category_result.scalar() or 0

            # 统计插件数（从 site.settings 中获取）
            stmt = select(Site).where(Site.id == site_id)
            result = await self.db.execute(stmt)
            site = result.scalar_one_or_none()
            if site and site.settings:
                plugins = site.settings.get('plugins', [])
                usage['plugins'] = len(plugins)

        except Exception as e:
            logger.warning(f"Failed to calculate usage for site {site_id}: {e}")

        return usage

    async def check_quota_available(self, site_id: int, resource_type: str, requested_amount: int = 1) -> Dict:
        """
        检查是否有可用配额

        Args:
            site_id: 站点ID
            resource_type: 资源类型 (articles/users/media_size_mb/categories/plugins)
            requested_amount: 请求的数量

        Returns:
            检查结果
        """
        quota_info = await self.get_site_quota(site_id)

        if resource_type not in quota_info['quotas']:
            return {
                'available': True,
                'message': f'Unknown resource type: {resource_type}'
            }

        max_limit = quota_info['quotas'][resource_type]
        current_usage = quota_info['usage'].get(resource_type, 0)
        available = max_limit - current_usage

        is_available = available >= requested_amount

        return {
            'available': is_available,
            'resource_type': resource_type,
            'max_limit': max_limit,
            'current_usage': current_usage,
            'available_amount': available,
            'requested_amount': requested_amount,
            'message': 'Quota available' if is_available else f'Quota exceeded. Available: {available}, Requested: {requested_amount}'
        }

    async def update_site_quota(self, site_id: int, quotas: Dict) -> Dict:
        """
        更新站点配额

        Args:
            site_id: 站点ID
            quotas: 新的配额设置

        Returns:
            更新结果
        """
        stmt = select(Site).where(Site.id == site_id)
        result = await self.db.execute(stmt)
        site = result.scalar_one_or_none()

        if not site:
            raise ValueError(f"Site {site_id} not found")

        # 更新 settings 中的 quotas
        if not site.settings:
            site.settings = {}

        site.settings['quotas'] = {**self.DEFAULT_QUOTAS, **quotas}

        await self.db.commit()

        return {
            'success': True,
            'message': 'Quotas updated successfully',
            'quotas': site.settings['quotas']
        }


def create_site_quota_service(db: AsyncSession) -> SiteQuotaService:
    """创建站点配额服务实例"""
    return SiteQuotaService(db)
