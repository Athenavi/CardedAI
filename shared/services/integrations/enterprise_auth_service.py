"""
企业认证服务（SAML/LDAP/SSO）

功能：
1. SAML 2.0 配置管理和认证
2. LDAP 集成和用户同步
3. SSO 单点登录支持
"""

from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.models.ldap_config import LDAPConfig
from shared.models.saml_config import SAMLConfig
from shared.models.sso_provider import SSOProvider

from src.unified_logger import default_logger as logger


class EnterpriseAuthService:
    """
    企业认证服务
    
    支持 SAML 2.0、LDAP 和 SSO
    """

    def __init__(self):
        pass

    # ==================== SAML 相关 ====================

    async def get_saml_config(self, db: AsyncSession, site_id: Optional[int] = None) -> Optional[SAMLConfig]:
        """获取 SAML 配置"""
        query = select(SAMLConfig).where(
            SAMLConfig.is_active == True
        )

        if site_id:
            query = query.where(SAMLConfig.site_id == site_id)
        else:
            query = query.where(SAMLConfig.site_id.is_(None))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_saml_config(
            self,
            db: AsyncSession,
            entity_id: str,
            acs_url: str,
            idp_entity_id: str,
            idp_sso_url: str,
            idp_certificate: str,
            site_id: Optional[int] = None,
            **kwargs
    ) -> SAMLConfig:
        """创建 SAML 配置"""
        config = SAMLConfig(
            site_id=site_id,
            entity_id=entity_id,
            acs_url=acs_url,
            idp_entity_id=idp_entity_id,
            idp_sso_url=idp_sso_url,
            idp_certificate=idp_certificate,
            **kwargs
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        logger.info(f"SAML config created for site {site_id}")
        return config

    async def update_saml_config(
            self,
            db: AsyncSession,
            config_id: int,
            updates: Dict[str, Any],
    ) -> SAMLConfig:
        """更新 SAML 配置"""
        config = await db.get(SAMLConfig, config_id)
        if not config:
            raise ValueError("SAML configuration not found")

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await db.commit()
        await db.refresh(config)
        return config

    async def deactivate_saml_config(self, db: AsyncSession, config_id: int):
        """停用 SAML 配置"""
        config = await db.get(SAMLConfig, config_id)
        if not config:
            raise ValueError("SAML configuration not found")

        config.is_active = False
        await db.commit()

    # ==================== LDAP 相关 ====================

    async def get_ldap_config(self, db: AsyncSession, site_id: Optional[int] = None) -> Optional[LDAPConfig]:
        """获取 LDAP 配置"""
        query = select(LDAPConfig).where(
            LDAPConfig.is_active == True
        )

        if site_id:
            query = query.where(LDAPConfig.site_id == site_id)
        else:
            query = query.where(LDAPConfig.site_id.is_(None))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_ldap_config(
            self,
            db: AsyncSession,
            server_url: str,
            bind_dn: str,
            bind_password: str,
            base_dn: str,
            site_id: Optional[int] = None,
            **kwargs
    ) -> LDAPConfig:
        """创建 LDAP 配置"""
        config = LDAPConfig(
            site_id=site_id,
            server_url=server_url,
            bind_dn=bind_dn,
            bind_password=bind_password,
            base_dn=base_dn,
            **kwargs
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        logger.info(f"LDAP config created for site {site_id}")
        return config

    async def update_ldap_config(
            self,
            db: AsyncSession,
            config_id: int,
            updates: Dict[str, Any],
    ) -> LDAPConfig:
        """更新 LDAP 配置"""
        config = await db.get(LDAPConfig, config_id)
        if not config:
            raise ValueError("LDAP configuration not found")

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await db.commit()
        await db.refresh(config)
        return config

    async def deactivate_ldap_config(self, db: AsyncSession, config_id: int):
        """停用 LDAP 配置"""
        config = await db.get(LDAPConfig, config_id)
        if not config:
            raise ValueError("LDAP configuration not found")

        config.is_active = False
        await db.commit()

    async def test_ldap_connection(self, config: LDAPConfig) -> bool:
        """测试 LDAP 连接"""
        try:
            import ldap3

            server = ldap3.Server(
                config.server_url,
                use_ssl=config.use_ssl,
                get_info=ldap3.NONE
            )

            conn = ldap3.Connection(
                server,
                user=config.bind_dn,
                password=config.bind_password,
                auto_bind=True
            )

            conn.unbind()
            logger.info("LDAP connection test successful")
            return True
        except Exception as e:
            logger.error(f"LDAP connection test failed: {e}")
            return False

    # ==================== SSO 相关 ====================

    async def get_sso_providers(self, db: AsyncSession, site_id: Optional[int] = None) -> List[SSOProvider]:
        """获取 SSO 提供商列表"""
        query = select(SSOProvider).where(
            SSOProvider.is_active == True
        )

        if site_id:
            query = query.where(SSOProvider.site_id == site_id)
        else:
            query = query.where(SSOProvider.site_id.is_(None))

        result = await db.execute(query)
        return result.scalars().all()

    async def create_sso_provider(
            self,
            db: AsyncSession,
            provider_type: str,
            name: str,
            client_id: str,
            client_secret: str,
            redirect_uri: str,
            site_id: Optional[int] = None,
            **kwargs
    ) -> SSOProvider:
        """创建 SSO 提供商配置"""
        provider = SSOProvider(
            site_id=site_id,
            provider_type=provider_type,
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            **kwargs
        )

        db.add(provider)
        await db.commit()
        await db.refresh(provider)

        logger.info(f"SSO provider '{name}' created for site {site_id}")
        return provider

    async def update_sso_provider(
            self,
            db: AsyncSession,
            provider_id: int,
            updates: Dict[str, Any],
    ) -> SSOProvider:
        """更新 SSO 提供商配置"""
        provider = await db.get(SSOProvider, provider_id)
        if not provider:
            raise ValueError("SSO provider not found")

        for key, value in updates.items():
            if hasattr(provider, key):
                setattr(provider, key, value)

        await db.commit()
        await db.refresh(provider)
        return provider

    async def deactivate_sso_provider(self, db: AsyncSession, provider_id: int):
        """停用 SSO 提供商"""
        provider = await db.get(SSOProvider, provider_id)
        if not provider:
            raise ValueError("SSO provider not found")

        provider.is_active = False
        await db.commit()


# 全局实例
enterprise_auth_service = EnterpriseAuthService()
