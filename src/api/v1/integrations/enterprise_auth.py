"""
企业认证 API（SAML/LDAP/SSO）

提供 SAML、LDAP 和 SSO 配置管理功能
"""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.integrations.enterprise_auth_service import enterprise_auth_service
from src.api.v1.core.responses import ApiResponse
from src.api.v1.system.multisite import check_admin_permission
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["enterprise-auth"])


# ==================== SAML 管理 ====================

@router.get("/saml/config", summary="获取 SAML 配置")
async def get_saml_config(
        site_id: Optional[int] = Query(None, description="站点 ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取 SAML 2.0 配置"""
    try:
        config = await enterprise_auth_service.get_saml_config(db, site_id)

        if not config:
            return ApiResponse(success=True, data=None, message="No SAML configuration found")

        return ApiResponse(success=True, data={
            'id': config.id,
            'entity_id': config.entity_id,
            'acs_url': config.acs_url,
            'idp_entity_id': config.idp_entity_id,
            'idp_sso_url': config.idp_sso_url,
            'enable_slo': config.enable_slo,
            'auto_provision_users': config.auto_provision_users,
            'is_active': config.is_active,
        })
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/saml/config", summary="创建 SAML 配置")
async def create_saml_config(
        entity_id: str = Body(...),
        acs_url: str = Body(...),
        idp_entity_id: str = Body(...),
        idp_sso_url: str = Body(...),
        idp_certificate: str = Body(...),
        site_id: Optional[int] = Body(None),
        enable_slo: bool = Body(False),
        auto_provision_users: bool = Body(True),
        default_role: str = Body("subscriber"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """创建 SAML 2.0 配置"""
    try:
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await enterprise_auth_service.create_saml_config(
            db, entity_id, acs_url, idp_entity_id, idp_sso_url, idp_certificate,
            site_id, enable_slo=enable_slo, auto_provision_users=auto_provision_users,
            default_role=default_role
        )

        return ApiResponse(success=True, data={'id': config.id}, message="SAML configuration created")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/saml/config/{config_id}", summary="更新 SAML 配置")
async def update_saml_config(
        config_id: int,
        updates: Dict[str, Any] = Body(...),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """更新 SAML 配置"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await enterprise_auth_service.update_saml_config(db, config_id, updates)
        return ApiResponse(success=True, message="SAML configuration updated")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/saml/config/{config_id}", summary="停用 SAML 配置")
async def deactivate_saml_config(
        config_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """停用 SAML 配置"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        await enterprise_auth_service.deactivate_saml_config(db, config_id)
        return ApiResponse(success=True, message="SAML configuration deactivated")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== LDAP 管理 ====================

@router.get("/ldap/config", summary="获取 LDAP 配置")
async def get_ldap_config(
        site_id: Optional[int] = Query(None, description="站点 ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取 LDAP 配置"""
    try:
        config = await enterprise_auth_service.get_ldap_config(db, site_id)

        if not config:
            return ApiResponse(success=True, data=None, message="No LDAP configuration found")

        return ApiResponse(success=True, data={
            'id': config.id,
            'server_url': config.server_url,
            'bind_dn': config.bind_dn,
            'base_dn': config.base_dn,
            'use_ssl': config.use_ssl,
            'auto_sync_users': config.auto_sync_users,
            'is_active': config.is_active,
        })
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/ldap/config", summary="创建 LDAP 配置")
async def create_ldap_config(
        server_url: str = Body(...),
        bind_dn: str = Body(...),
        bind_password: str = Body(...),
        base_dn: str = Body(...),
        site_id: Optional[int] = Body(None),
        use_ssl: bool = Body(False),
        auto_sync_users: bool = Body(False),
        default_role: str = Body("subscriber"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """创建 LDAP 配置"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await enterprise_auth_service.create_ldap_config(
            db, server_url, bind_dn, bind_password, base_dn, site_id,
            use_ssl=use_ssl, auto_sync_users=auto_sync_users, default_role=default_role
        )

        return ApiResponse(success=True, data={'id': config.id}, message="LDAP configuration created")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/ldap/config/{config_id}", summary="更新 LDAP 配置")
async def update_ldap_config(
        config_id: int,
        updates: Dict[str, Any] = Body(...),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """更新 LDAP 配置"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await enterprise_auth_service.update_ldap_config(db, config_id, updates)
        return ApiResponse(success=True, message="LDAP configuration updated")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/ldap/config/{config_id}", summary="停用 LDAP 配置")
async def deactivate_ldap_config(
        config_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """停用 LDAP 配置"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        await enterprise_auth_service.deactivate_ldap_config(db, config_id)
        return ApiResponse(success=True, message="LDAP configuration deactivated")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/ldap/test-connection", summary="测试 LDAP 连接")
async def test_ldap_connection(
        config_id: int = Body(...),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """测试 LDAP 连接"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        from shared.models.ldap_config import LDAPConfig
        config = await db.get(LDAPConfig, config_id)

        if not config:
            return ApiResponse(success=False, error="LDAP configuration not found")

        success = await enterprise_auth_service.test_ldap_connection(config)

        if success:
            return ApiResponse(success=True, message="LDAP connection successful")
        else:
            return ApiResponse(success=False, error="LDAP connection failed")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== SSO 管理 ====================

@router.get("/sso/providers", summary="获取 SSO 提供商列表")
async def get_sso_providers(
        site_id: Optional[int] = Query(None, description="站点 ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取 SSO 提供商列表"""
    try:
        providers = await enterprise_auth_service.get_sso_providers(db, site_id)

        providers_list = []
        for provider in providers:
            providers_list.append({
                'id': provider.id,
                'provider_type': provider.provider_type,
                'name': provider.name,
                'client_id': provider.client_id,
                'redirect_uri': provider.redirect_uri,
                'is_active': provider.is_active,
            })

        return ApiResponse(success=True, data={'providers': providers_list, 'total': len(providers_list)})
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/sso/providers", summary="创建 SSO 提供商")
async def create_sso_provider(
        provider_type: str = Body(...),
        name: str = Body(...),
        client_id: str = Body(...),
        client_secret: str = Body(...),
        redirect_uri: str = Body(...),
        site_id: Optional[int] = Body(None),
        authorization_url: Optional[str] = Body(None),
        token_url: Optional[str] = Body(None),
        userinfo_url: Optional[str] = Body(None),
        scope: str = Body("openid profile email"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """创建 SSO 提供商配置"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        provider = await enterprise_auth_service.create_sso_provider(
            db, provider_type, name, client_id, client_secret, redirect_uri,
            site_id, authorization_url=authorization_url, token_url=token_url,
            userinfo_url=userinfo_url, scope=scope
        )

        return ApiResponse(success=True, data={'id': provider.id}, message="SSO provider created")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/sso/providers/{provider_id}", summary="更新 SSO 提供商")
async def update_sso_provider(
        provider_id: int,
        updates: Dict[str, Any] = Body(...),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """更新 SSO 提供商配置"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        provider = await enterprise_auth_service.update_sso_provider(db, provider_id, updates)
        return ApiResponse(success=True, message="SSO provider updated")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/sso/providers/{provider_id}", summary="停用 SSO 提供商")
async def deactivate_sso_provider(
        provider_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """停用 SSO 提供商"""
    try:
        
        if not await check_admin_permission(db, current_user.id):
            return ApiResponse(success=False, error="Insufficient permissions")

        await enterprise_auth_service.deactivate_sso_provider(db, provider_id)
        return ApiResponse(success=True, message="SSO provider deactivated")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
