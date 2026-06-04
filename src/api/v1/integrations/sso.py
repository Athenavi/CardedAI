"""
SSO单点登录 API
提供OAuth2.0、SAML和LDAP认证功能
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.integrations.sso_service import sso_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["sso"])


# ==================== OAuth2.0 ====================

@router.get("/oauth/{provider}/authorize", summary="OAuth2授权")
async def oauth_authorize(
        provider: str,
        redirect_uri: str = Query(..., description="回调URL"),
        state: Optional[str] = Query(None, description="状态参数"),
):
    """
    获取OAuth2授权URL并重定向
    
    Args:
        provider: OAuth提供商 (google/github/microsoft)
        redirect_uri: 回调URL
        state: 状态参数
        
    Returns:
        重定向到OAuth提供商
    """
    try:
        authorization_url = await sso_service.get_oauth_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
            state=state
        )

        return RedirectResponse(url=authorization_url)

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/oauth/{provider}/callback", summary="OAuth2回调处理")
async def oauth_callback(
        provider: str,
        code: str = Body(..., description="授权码"),
        redirect_uri: str = Body(..., description="回调URL"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    处理OAuth2回调
    
    Args:
        provider: OAuth提供商
        code: 授权码
        redirect_uri: 回调URL
        
    Returns:
        用户信息和令牌
    """
    try:
        result = await sso_service.handle_oauth_callback(
            db=db,
            provider=provider,
            code=code,
            redirect_uri=redirect_uri
        )

        # 这里应该生成JWT令牌
        # 简化处理，返回用户信息

        return ApiResponse(
            success=True,
            data={
                'user_id': result['user'].id,
                'username': result['user'].username,
                'email': result['user'].email,
                'provider': result['provider'],
                'message': 'Authentication successful'
            },
            message="OAuth authentication successful"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/oauth/providers", summary="获取支持的OAuth提供商")
async def get_oauth_providers():
    """
    获取所有支持的OAuth提供商列表
    
    Returns:
        提供商列表
    """
    try:
        providers = []
        for name, config in sso_service.oauth_providers.items():
            if config.get('client_id'):  # 只返回已配置的提供商
                providers.append({
                    'name': name,
                    'display_name': name.title(),
                    'configured': True,
                })
            else:
                providers.append({
                    'name': name,
                    'display_name': name.title(),
                    'configured': False,
                })

        return ApiResponse(
            success=True,
            data={
                'providers': providers,
                'total': len(providers)
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== LDAP ====================

@router.post("/ldap/authenticate", summary="LDAP认证")
async def ldap_authenticate(
        username: str = Body(..., description="用户名"),
        password: str = Body(..., description="密码"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    LDAP认证
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        认证结果
    """
    try:
        userinfo = await sso_service.authenticate_ldap(username, password)

        if not userinfo:
            return ApiResponse(success=False, error="Invalid credentials")

        # 查找或创建用户
        from sqlalchemy import select
        from shared.models.user import User

        stmt = select(User).where(User.email == userinfo.get('email'))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # 创建新用户
            user = User(
                username=userinfo['username'],
                email=userinfo.get('email') or f"{userinfo['username']}@company.com",
                password='',  # LDAP用户不需要本地密码
                is_active=True,
                auth_method='ldap',
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"New user created via LDAP: {userinfo['username']}")

        return ApiResponse(
            success=True,
            data={
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'auth_method': 'ldap',
            },
            message="LDAP authentication successful"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== SAML ====================

@router.get("/saml/login", summary="SAML登录")
async def saml_login():
    """
    发起SAML登录请求
    
    Returns:
        SAML登录请求数据
    """
    try:
        result = await sso_service.create_saml_login_request()

        if 'error' in result:
            return ApiResponse(success=False, error=result['error'])

        return ApiResponse(
            success=True,
            data=result,
            message="SAML login request created"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/saml/acs", summary="SAML断言消费者服务")
async def saml_acs(
        saml_response: str = Body(..., description="SAML响应"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    处理SAML响应（ACS端点）
    
    Args:
        saml_response: SAML响应数据
        
    Returns:
        认证结果
    """
    try:
        userinfo = await sso_service.handle_saml_response(db, saml_response)

        if not userinfo:
            return ApiResponse(success=False, error="SAML authentication failed")

        return ApiResponse(
            success=True,
            data=userinfo,
            message="SAML authentication successful"
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== SSO会话管理 ====================

@router.post("/session/create", summary="创建SSO会话")
async def create_sso_session(
        user_id: int = Body(..., description="用户ID"),
        session_id: str = Body(..., description="会话ID"),
        current_user=Depends(jwt_required)
):
    """
    创建SSO会话
    
    Args:
        user_id: 用户ID
        session_id: 会话ID
        
    Returns:
        SSO令牌
    """
    try:
        sso_token = await sso_service.create_sso_session(user_id, session_id)

        return ApiResponse(
            success=True,
            data={
                'sso_token': sso_token,
                'user_id': user_id,
            },
            message="SSO session created"
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/session/validate", summary="验证SSO令牌")
async def validate_sso_token(
        sso_token: str = Body(..., description="SSO令牌"),
):
    """
    验证SSO令牌
    
    Args:
        sso_token: SSO令牌
        
    Returns:
        验证结果
    """
    try:
        user_id = await sso_service.validate_sso_token(sso_token)

        if not user_id:
            return ApiResponse(success=False, error="Invalid or expired SSO token")

        return ApiResponse(
            success=True,
            data={
                'valid': True,
                'user_id': user_id,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 配置管理 ====================

@router.get("/config", summary="获取SSO配置状态")
async def get_sso_config(current_user=Depends(jwt_required)):
    """
    获取SSO配置状态
    
    Returns:
        配置状态
    """
    try:
        config = {
            'oauth': {
                'google': bool(sso_service.oauth_providers['google']['client_id']),
                'github': bool(sso_service.oauth_providers['github']['client_id']),
                'microsoft': bool(sso_service.oauth_providers['microsoft']['client_id']),
            },
            'saml': bool(sso_service.saml_config['entity_id']),
            'ldap': bool(sso_service.ldap_config['server']),
        }

        return ApiResponse(
            success=True,
            data=config
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# 导入logger


from src.unified_logger import default_logger as logger
