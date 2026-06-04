"""
OAuth 第三方登录 API 端点
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.integrations.oauth_service import oauth_service
from src.api.v1.core.responses import ApiResponse
from src.auth import create_access_token
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["oauth"])


@router.get("/providers")
async def list_oauth_providers():
    """获取支持的OAuth提供商列表"""
    try:
        providers = oauth_service.get_supported_providers()
        
        return ApiResponse(
            success=True,
            data={"providers": providers}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/authorize/{provider}")
async def authorize(
    provider: str,
    request: Request,
    state: str = Query(..., description="CSRF状态")
):
    """
    生成OAuth授权URL
    
    Args:
        provider: 提供商名称 (github/google/wechat/qq/weibo)
        state: CSRF保护状态
        
    Returns:
        授权URL
    """
    try:
        # 从环境变量或配置获取client_id和redirect_uri
        import os
        
        client_id = os.getenv(f"OAUTH_{provider.upper()}_CLIENT_ID", "")
        redirect_uri = request.url_for("oauth_callback", provider=provider).__str__()
        
        if not client_id:
            return ApiResponse(
                success=False,
                error=f"未配置 {provider} 的 Client ID"
            )
        
        auth_url = oauth_service.get_authorization_url(
            provider=provider,
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state
        )
        
        return ApiResponse(
            success=True,
            data={
                "authorization_url": auth_url,
                "provider": provider
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    request: Request,
    code: str = Query(..., description="授权码"),
    state: str = Query(..., description="CSRF状态"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    OAuth回调处理
    
    Args:
        provider: 提供商名称
        code: 授权码
        state: CSRF状态
        
    Returns:
        用户信息和JWT令牌
    """
    try:
        import os
        from src.extensions import cache
        
        # 验证state（防止CSRF攻击）
        if not state:
            return ApiResponse(success=False, error="缺少state参数")
        
        # 从 Redis 获取存储的 state
        stored_state = await cache.get(f"oauth_state:{state}")
        if not stored_state:
            return ApiResponse(success=False, error="state已过期或无效")
        
        # 验证后删除state(一次性使用)
        await cache.delete(f"oauth_state:{state}")
        
        # 获取配置
        client_id = os.getenv(f"OAUTH_{provider.upper()}_CLIENT_ID", "")
        client_secret = os.getenv(f"OAUTH_{provider.upper()}_CLIENT_SECRET", "")
        redirect_uri = request.url_for("oauth_callback", provider=provider).__str__()
        
        if not client_id or not client_secret:
            return ApiResponse(
                success=False,
                error=f"未配置 {provider} 的 Client ID/Secret"
            )

        # 1. 用授权码交换访问令牌
        token_result = await oauth_service.exchange_code_for_token(
            provider=provider,
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )

        if not token_result.get("success"):
            return ApiResponse(
                success=False,
                error=token_result.get("error", "获取令牌失败")
            )

        access_token = token_result["access_token"]

        # 2. 获取用户信息
        user_info_result = await oauth_service.get_user_info(
            provider=provider,
            access_token=access_token
        )

        if not user_info_result.get("success"):
            return ApiResponse(
                success=False,
                error=user_info_result.get("error", "获取用户信息失败")
            )

        user_info = user_info_result["user"]

        # 3. 查找或创建用户
        from shared.models.user import User
        from shared.models.o_auth_account import OAuthAccount
        from sqlalchemy import select
        from datetime import datetime

        # 先查找OAuth关联记录
        oauth_query = select(OAuthAccount).where(
            (OAuthAccount.provider == provider) &
            (OAuthAccount.provider_user_id == str(user_info.get('provider_id')))
        )
        oauth_result = await db.execute(oauth_query)
        oauth_account = oauth_result.scalar_one_or_none()

        user = None

        if oauth_account:
            # OAuth账号已存在，直接获取关联的用户
            user_query = select(User).where(User.id == oauth_account.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if not user:
                return ApiResponse(success=False, error="关联的用户不存在")

            # 更新OAuth令牌
            oauth_account.access_token = access_token
            oauth_account.updated_at = datetime.now()

        else:
            # OAuth账号不存在，尝试通过邮箱查找现有用户
            email = user_info.get('email')

            if email:
                email_query = select(User).where(User.email == email)
                email_result = await db.execute(email_query)
                user = email_result.scalar_one_or_none()

            if user:
                # 找到现有用户，创建OAuth关联（账号绑定）
                print(f"[OAuth] Binding {provider} account to existing user: {user.username}")

                oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=str(user_info.get('provider_id')),
                    access_token=access_token,
                    created_at=datetime.now()
                )
                db.add(oauth_account)

            else:
                # 创建新用户
                print(f"[OAuth] Creating new user from {provider}")

                # 生成唯一用户名
                username = user_info.get('username') or user_info.get(
                    'name') or f"{provider}_{user_info.get('provider_id')}"

                # 检查用户名是否已存在
                existing_username = await db.execute(
                    select(User).where(User.username == username)
                )
                if existing_username.scalar_one_or_none():
                    username = f"{username}_{int(datetime.now().timestamp())}"

                user = User(
                    username=username,
                    email=email,
                    nickname=user_info.get('name', ''),
                    avatar_url=user_info.get('avatar', ''),
                    is_active=True,
                    created_at=datetime.now()
                )
                db.add(user)
                await db.flush()  # 获取user.id

                # 创建OAuth关联记录
                oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=str(user_info.get('provider_id')),
                    access_token=access_token,
                    created_at=datetime.now()
                )
                db.add(oauth_account)

        await db.commit()

        # 4. 生成JWT令牌
        from src.auth import create_access_token
        jwt_token = create_access_token(data={"sub": str(user.id)})

        # 返回用户信息
        return ApiResponse(
            success=True,
            message=f"{provider} 登录成功",
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "nickname": user.nickname,
                    "avatar_url": user.avatar_url
                },
                "access_token": jwt_token,
                "token_type": "Bearer",
                "is_new_user": oauth_account and oauth_account.created_at == oauth_account.updated_at
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.post("/bind-account")
async def bind_oauth_account(
        request: Request,
        provider: str = Query(..., description="OAuth提供商"),
        code: str = Query(..., description="授权码"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    绑定OAuth账号到当前登录用户
    
    用于将第三方账号绑定到现有账户，实现统一账号管理
    
    Args:
        provider: OAuth提供商
        code: 授权码
        
    Returns:
        绑定结果
    """
    try:
        import os
        from shared.models.o_auth_account import OAuthAccount
        from sqlalchemy import select
        from datetime import datetime

        # 获取配置
        client_id = os.getenv(f"OAUTH_{provider.upper()}_CLIENT_ID", "")
        client_secret = os.getenv(f"OAUTH_{provider.upper()}_CLIENT_SECRET", "")
        redirect_uri = str(request.base_url) + f"api/v1/oauth/callback/{provider}"

        if not client_id or not client_secret:
            return ApiResponse(
                success=False,
                error=f"未配置 {provider} 的 Client ID/Secret"
            )

        # 1. 用授权码交换访问令牌
        token_result = await oauth_service.exchange_code_for_token(
            provider=provider,
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )

        if not token_result.get("success"):
            return ApiResponse(
                success=False,
                error=token_result.get("error", "获取令牌失败")
            )

        access_token = token_result["access_token"]

        # 2. 获取用户信息
        user_info_result = await oauth_service.get_user_info(
            provider=provider,
            access_token=access_token
        )

        if not user_info_result.get("success"):
            return ApiResponse(
                success=False,
                error=user_info_result.get("error", "获取用户信息失败")
            )

        user_info = user_info_result["user"]
        provider_user_id = str(user_info.get('provider_id'))

        # 3. 检查该OAuth账号是否已被其他用户绑定
        existing_oauth = await db.execute(
            select(OAuthAccount).where(
                (OAuthAccount.provider == provider) &
                (OAuthAccount.provider_user_id == provider_user_id)
            )
        )
        existing = existing_oauth.scalar_one_or_none()

        if existing:
            if existing.user_id == current_user.id:
                return ApiResponse(
                    success=False,
                    error=f"此{provider}账号已经绑定到您的账户"
                )
            else:
                return ApiResponse(
                    success=False,
                    error=f"此{provider}账号已绑定到其他账户"
                )

        # 4. 检查当前用户是否已绑定该提供商的账号
        existing_binding = await db.execute(
            select(OAuthAccount).where(
                (OAuthAccount.user_id == current_user.id) &
                (OAuthAccount.provider == provider)
            )
        )
        if existing_binding.scalar_one_or_none():
            return ApiResponse(
                success=False,
                error=f"您的账户已绑定{provider}账号，请先解绑"
            )

        # 5. 创建绑定关系
        new_oauth = OAuthAccount(
            user_id=current_user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            access_token=access_token,
            created_at=datetime.now()
        )
        db.add(new_oauth)
        await db.commit()

        return ApiResponse(
            success=True,
            message=f"成功绑定{provider}账号",
            data={
                "provider": provider,
                "provider_user_id": provider_user_id,
                "bound_at": datetime.now().isoformat()
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.post("/unbind-account")
async def unbind_oauth_account(
        provider: str = Query(..., description="OAuth提供商"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    解绑OAuth账号
    
    Args:
        provider: OAuth提供商
        
    Returns:
        解绑结果
    """
    try:
        from shared.models.o_auth_account import OAuthAccount
        from sqlalchemy import select, delete

        # 查找绑定记录
        result = await db.execute(
            select(OAuthAccount).where(
                (OAuthAccount.user_id == current_user.id) &
                (OAuthAccount.provider == provider)
            )
        )
        oauth_account = result.scalar_one_or_none()

        if not oauth_account:
            return ApiResponse(
                success=False,
                error=f"未找到绑定的{provider}账号"
            )

        # 删除绑定关系
        await db.execute(
            delete(OAuthAccount).where(OAuthAccount.id == oauth_account.id)
        )
        await db.commit()

        return ApiResponse(
            success=True,
            message=f"已解绑{provider}账号"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.get("/linked-accounts")
async def get_linked_accounts(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户绑定的所有OAuth账号
    
    Returns:
        绑定的账号列表
    """
    try:
        from shared.models.o_auth_account import OAuthAccount
        from sqlalchemy import select

        result = await db.execute(
            select(OAuthAccount).where(OAuthAccount.user_id == current_user.id)
        )
        accounts = result.scalars().all()

        linked = []
        for account in accounts:
            linked.append({
                "provider": account.provider,
                "provider_name": oauth_service.providers.get(account.provider, {}).get("name", account.provider),
                "provider_user_id": account.provider_user_id,
                "bound_at": account.created_at.isoformat() if account.created_at else None
            })

        return ApiResponse(
            success=True,
            data={
                "linked_accounts": linked,
                "total": len(linked)
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))

        if not client_id or not client_secret:
            return ApiResponse(
                success=False,
                error=f"未配置 {provider} 的凭证"
            )
        
        # 交换授权码为访问令牌
        token_result = await oauth_service.exchange_code_for_token(
            provider=provider,
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        
        if not token_result["success"]:
            return ApiResponse(
                success=False,
                error=token_result["error"]
            )
        
        access_token = token_result["access_token"]
        
        # 获取用户信息
        user_result = await oauth_service.get_user_info(
            provider=provider,
            access_token=access_token
        )
        
        if not user_result["success"]:
            return ApiResponse(
                success=False,
                error=user_result["error"]
            )
        
        user_info = user_result["user"]
        
        # 1. 检查用户是否已存在（根据provider + provider_id）
        from shared.models import OAuthAccount
        from shared.models import User
        from sqlalchemy import select
        from datetime import datetime
        
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == user_info.get('id')
        )
        result = await db.execute(stmt)
        oauth_account = result.scalar_one_or_none()
        
        if oauth_account:
            # 2. 如果存在，获取关联的用户
            stmt = select(User).where(User.id == oauth_account.user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return ApiResponse(success=False, error="用户不存在")
        else:
            # 3. 如果不存在，创建新用户
            # 检查邮箱是否已存在
            email = user_info.get('email', '')
            if email:
                stmt = select(User).where(User.email == email)
                result = await db.execute(stmt)
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    user = existing_user
                else:
                    # 创建新用户
                    user = User(
                        username=user_info.get('username', f"{provider}_{user_info.get('id')}"),
                        email=email,
                        nickname=user_info.get('name', ''),
                        avatar_url=user_info.get('avatar', ''),
                        is_active=True,
                        created_at=datetime.now()
                    )
                    db.add(user)
                    await db.flush()  # 获取user.id
            else:
                return ApiResponse(success=False, error="未获取到邮箱信息")
            
            # 创建OAuth关联记录
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_user_id=str(user_info.get('id')),
                access_token=access_token,
                created_at=datetime.now()
            )
            db.add(oauth_account)
        
        await db.commit()
        
        # 4. 生成JWT令牌
        jwt_token = create_access_token(data={"sub": str(user.id)})
        
        # 临时返回用户信息
        return ApiResponse(
            success=True,
            message=f"{provider} 登录成功",
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "nickname": user.nickname,
                    "avatar_url": user.avatar_url
                },
                "access_token": jwt_token,
                "token_type": "Bearer"
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.post("/unlink/{provider}")
async def unlink_oauth_account(
    provider: str,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """
    解绑OAuth账号
    
    Args:
        provider: 提供商名称
        
    Returns:
        解绑结果
    """
    try:
        from shared.models import OAuthAccount, User
        from sqlalchemy import select, func
        
        # 1. 从数据库中删除用户的OAuth关联
        stmt = select(OAuthAccount).where(
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.provider == provider
        )
        result = await db.execute(stmt)
        oauth_account = result.scalar_one_or_none()
        
        if not oauth_account:
            return ApiResponse(success=False, error=f"未绑定 {provider} 账号")
        
        # 2. 确保用户至少有一个登录方式
        # 检查是否还有其他OAuth账号或密码
        stmt = select(func.count(OAuthAccount.id)).where(
            OAuthAccount.user_id == current_user.id
        )
        result = await db.execute(stmt)
        oauth_count = result.scalar() or 0
        
        # 检查是否有密码
        user_stmt = select(User).where(User.id == current_user.id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        has_password = user and user.password_hash
        
        # 如果只有这一个OAuth账号且没有密码，不允许解绑
        if oauth_count <= 1 and not has_password:
            return ApiResponse(
                success=False, 
                error="至少需要保留一个登录方式，请先设置密码"
            )
        
        # 删除OAuth关联
        await db.delete(oauth_account)
        await db.commit()
        
        return ApiResponse(
            success=True,
            message=f"已解绑 {provider} 账号"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
