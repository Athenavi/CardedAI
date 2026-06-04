"""
多站点管理服务
提供站点配置隔离、独立域名绑定、共享用户体系和跨站点内容同步功能
"""
import json

from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete as sqlalchemy_delete

from shared.models.site import Site
from shared.models.site_user import SiteUser
from shared.models.content_mapping import ContentMapping

from src.unified_logger import default_logger as logger




class MultiSiteService:
    """
    多站点管理服务
    
    功能:
    1. 站点配置隔离
    2. 独立域名绑定
    3. 共享用户体系
    4. 跨站点内容同步
    """

    def __init__(self):
        pass

    async def create_site(self, db, name: str, slug: str, domain: str,
                          description: str = None, is_default: bool = False,
                          settings: Dict = None) -> Site:
        """
        创建新站点
        
        Args:
            db: 数据库会话
            name: 站点名称
            slug: 站点标识
            domain: 主域名
            description: 描述
            is_default: 是否为默认站点
            settings: 站点设置
            
        Returns:
            创建的站点
        """
        from sqlalchemy import select

        # 检查slug是否已存在
        stmt = select(Site).where(Site.slug == slug)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"Site with slug '{slug}' already exists")

        # 检查域名是否已存在
        stmt = select(Site).where(Site.domain == domain)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"Site with domain '{domain}' already exists")

        # 如果设置为默认站点，取消其他站点的默认状态
        if is_default:
            stmt = select(Site).where(Site.is_default == True)
            result = await db.execute(stmt)
            default_sites = result.scalars().all()
            for site in default_sites:
                site.is_default = False

        # 创建站点
        site = Site(
            name=name,
            slug=slug,
            domain=domain,
            description=description,
            is_default=is_default,
            settings=str(settings) if settings else None
        )

        db.add(site)
        await db.commit()
        await db.refresh(site)

        logger.info(f"Site created: {slug} ({domain})")
        return site

    async def update_site(self, db, site_id: int, updates: Dict[str, Any]) -> Site:
        """
        更新站点配置
        
        Args:
            db: 数据库会话
            site_id: 站点ID
            updates: 更新字段
            
        Returns:
            更新后的站点
        """
        site = await db.get(Site, site_id)
        if not site:
            raise ValueError("Site not found")

        for key, value in updates.items():
            if hasattr(site, key):
                setattr(site, key, value)

        await db.commit()
        await db.refresh(site)

        logger.info(f"Site updated: {site.slug}")
        return site

    async def delete_site(self, db, site_id: int):
        """
        删除站点
        
        Args:
            db: 数据库会话
            site_id: 站点ID
        """
        site = await db.get(Site, site_id)
        if not site:
            raise ValueError("Site not found")

        # 不能删除默认站点
        if site.is_default:
            raise ValueError("Cannot delete default site")

        # 删除站点-用户关联
        stmt = sqlalchemy_delete(SiteUser).where(SiteUser.site_id == site_id)
        await db.execute(stmt)

        # 删除内容映射
        stmt = sqlalchemy_delete(ContentMapping).where(
            (ContentMapping.source_site_id == site_id) |
            (ContentMapping.target_site_id == site_id)
        )
        await db.execute(stmt)

        # 删除站点
        await db.delete(site)
        await db.commit()

        logger.info(f"Site deleted: {site.slug}")

    async def add_domain(self, db, site_id: int, domain: str):
        """
        添加附加域名
        
        Args:
            db: 数据库会话
            site_id: 站点ID
            domain: 域名
        """
        import json

        site = await db.get(Site, site_id)
        if not site:
            raise ValueError("Site not found")

        # 解析现有附加域名
        additional_domains = []
        if site.additional_domains:
            try:
                additional_domains = json.loads(site.additional_domains)
            except:
                additional_domains = []

        # 检查域名是否已存在
        if domain in additional_domains:
            raise ValueError("Domain already added")

        # 检查域名是否被其他站点使用
        from sqlalchemy import select
        stmt = select(Site).where(Site.domain == domain)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("Domain is used as primary domain by another site")

        # 添加域名
        additional_domains.append(domain)
        site.additional_domains = json.dumps(additional_domains)

        await db.commit()

        logger.info(f"Domain added to site {site.slug}: {domain}")

    async def remove_domain(self, db, site_id: int, domain: str):
        """
        移除附加域名
        
        Args:
            db: 数据库会话
            site_id: 站点ID
            domain: 域名
        """
        import json

        site = await db.get(Site, site_id)
        if not site:
            raise ValueError("Site not found")

        if site.additional_domains:
            try:
                additional_domains = json.loads(site.additional_domains)
                if domain in additional_domains:
                    additional_domains.remove(domain)
                    site.additional_domains = json.dumps(additional_domains)
                    await db.commit()
                    logger.info(f"Domain removed from site {site.slug}: {domain}")
            except:
                pass

    async def get_site_by_domain(self, db, domain: str) -> Optional[Site]:
        """
        根据域名获取站点
        
        Args:
            db: 数据库会话
            domain: 域名
            
        Returns:
            站点对象
        """
        import json
        from sqlalchemy import select

        # 检查主域名
        stmt = select(Site).where(Site.domain == domain, Site.is_active == True)
        result = await db.execute(stmt)
        site = result.scalar_one_or_none()

        if site:
            return site

        # 检查附加域名
        stmt = select(Site).where(Site.is_active == True)
        result = await db.execute(stmt)
        sites = result.scalars().all()

        for site in sites:
            if site.additional_domains:
                try:
                    additional_domains = json.loads(site.additional_domains)
                    if domain in additional_domains:
                        return site
                except:
                    pass

        # 返回默认站点
        stmt = select(Site).where(Site.is_default == True, Site.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_user_to_site(self, db, site_id: int, user_id: int, role: str = 'subscriber'):
        """
        添加用户到站点（共享用户体系）
        
        Args:
            db: 数据库会话
            site_id: 站点ID
            user_id: 用户ID
            role: 在该站点的角色
        """
        from sqlalchemy import select

        # 检查是否已存在
        stmt = select(SiteUser).where(
            SiteUser.site_id == site_id,
            SiteUser.user_id == user_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.role = role
            existing.is_active = True
        else:
            site_user = SiteUser(
                site_id=site_id,
                user_id=user_id,
                role=role
            )
            db.add(site_user)

        await db.commit()

        logger.info(f"User {user_id} added to site {site_id} as {role}")

    async def remove_user_from_site(self, db, site_id: int, user_id: int):
        """
        从站点移除用户
        
        Args:
            db: 数据库会话
            site_id: 站点ID
            user_id: 用户ID
        """
        from sqlalchemy import select

        stmt = select(SiteUser).where(
            SiteUser.site_id == site_id,
            SiteUser.user_id == user_id
        )
        result = await db.execute(stmt)
        site_user = result.scalar_one_or_none()

        if site_user:
            site_user.is_active = False
            await db.commit()

            logger.info(f"User {user_id} removed from site {site_id}")

    async def get_user_sites(self, db, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户所属的所有站点
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            站点列表
        """
        from sqlalchemy import select

        stmt = (
            select(Site, SiteUser)
            .join(SiteUser, Site.id == SiteUser.site_id)
            .where(
                SiteUser.user_id == user_id,
                SiteUser.is_active == True,
                Site.is_active == True
            )
        )

        result = await db.execute(stmt)
        rows = result.all()

        sites = []
        for site, site_user in rows:
            sites.append({
                'id': site.id,
                'name': site.name,
                'slug': site.slug,
                'domain': site.domain,
                'role': site_user.role,
                'joined_at': site_user.joined_at.isoformat() if site_user.joined_at else None,
            })

        return sites

    async def sync_content(self, db, source_site_id: int, target_site_id: int,
                           content_type: str, source_content_id: int,
                           sync_mode: str = 'manual') -> ContentMapping:
        """
        同步内容到其他站点
        
        Args:
            db: 数据库会话
            source_site_id: 源站点ID
            target_site_id: 目标站点ID
            content_type: 内容类型
            source_content_id: 源内容ID
            sync_mode: 同步模式 (manual/auto)
            
        Returns:
            内容映射记录
        """
        from sqlalchemy import select

        # 检查是否已有映射
        stmt = select(ContentMapping).where(
            ContentMapping.source_site_id == source_site_id,
            ContentMapping.target_site_id == target_site_id,
            ContentMapping.content_type == content_type,
            ContentMapping.source_content_id == source_content_id
        )
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if mapping:
            mapping.sync_mode = sync_mode
            mapping.last_synced_at = datetime.now()
        else:
            mapping = ContentMapping(
                source_site_id=source_site_id,
                target_site_id=target_site_id,
                content_type=content_type,
                source_content_id=source_content_id,
                sync_mode=sync_mode
            )
            db.add(mapping)

        await db.commit()
        await db.refresh(mapping)

        logger.info(
            f"Content synced: {content_type}#{source_content_id} from site {source_site_id} to {target_site_id}")
        return mapping

    async def get_all_sites(self, db, include_inactive: bool = False) -> List[Site]:
        """
        获取所有站点
        
        Args:
            db: 数据库会话
            include_inactive: 是否包含非活动站点
            
        Returns:
            站点列表
        """
        from sqlalchemy import select

        query = select(Site)
        if not include_inactive:
            query = query.where(Site.is_active == True)

        result = await db.execute(query)
        return result.scalars().all()


# 全局实例
multisite_service = MultiSiteService()
