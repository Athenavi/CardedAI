"""
移动端认证API
提供适合移动端的登录、注册等认证接口
"""
import re

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User as UserModel
from src.api.v1.auth import create_jwt_token
from src.api.v1.core.responses import ApiResponse
from src.utils.database.main import get_async_session
from src.utils.security.password_validator import verify_password, hash_password

router = APIRouter(tags=["mobile-auth"])


@router.post("/login")
async def mobile_login(
        request: Request,
        db: AsyncSession = Depends(get_async_session)
):
    """
    移动端登录
    支持用户名或邮箱登录
    """
    try:
        # 读取原始请求体进行调试
        body_bytes = await request.body()
        content_type = request.headers.get('content-type', '')

        print(f"\n{'=' * 60}")
        print(f"[Mobile Login] Raw body bytes: {body_bytes}")
        print(f"[Mobile Login] Content-Type: {content_type}")
        print(f"{'=' * 60}\n")

        # 根据Content-Type解析请求体
        if 'application/json' in content_type:
            # JSON格式
            body = await request.json()
        elif 'application/x-www-form-urlencoded' in content_type:
            # 表单格式
            form_data = await request.form()
            body = dict(form_data)
        else:
            # 尝试作为JSON解析
            try:
                body = await request.json()
            except:
                form_data = await request.form()
                body = dict(form_data)

        print(f"[Mobile Login] Parsed body: {body}")
        
        username_or_email = body.get('username') or body.get('email')
        password = body.get('password')

        if not username_or_email or not password:
            return ApiResponse(success=False, error="缺少用户名或密码")

        # 查找用户
        result = await db.execute(
            select(UserModel).where(
                (UserModel.username == username_or_email) |
                (UserModel.email == username_or_email)
            )
        )
        user = result.scalar_one_or_none()

        if not user or not user.password:
            return ApiResponse(success=False, error="用户名或密码错误")

        # 验证密码
        if not verify_password(password, user.password):
            return ApiResponse(success=False, error="用户名或密码错误")

        if not user.is_active:
            return ApiResponse(success=False, error="账户已被禁用")

        # 生成token
        access_token = create_jwt_token(subject=str(user.id), token_type="access")
        refresh_token = create_jwt_token(subject=str(user.id), token_type="refresh")

        return ApiResponse(
            success=True,
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.profile_picture,
                    "vip_level": getattr(user, "vip_level", 0)
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "message": "登录成功"
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in mobile_login: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.post("/register")
async def mobile_register(
        request: Request,
        db: AsyncSession = Depends(get_async_session)
):
    """
    移动端注册
    """
    try:
        content_type = request.headers.get('content-type', '')

        # 根据Content-Type解析请求体
        if 'application/json' in content_type:
            body = await request.json()
        elif 'application/x-www-form-urlencoded' in content_type:
            form_data = await request.form()
            body = dict(form_data)
        else:
            try:
                body = await request.json()
            except:
                form_data = await request.form()
                body = dict(form_data)
        username = body.get('username')
        email = body.get('email')
        password = body.get('password')

        # 验证必填字段
        if not username or not email or not password:
            return ApiResponse(success=False, error="缺少必填字段")

        # 基础校验
        if len(username) < 3:
            return ApiResponse(success=False, error="用户名至少需要3个字符")

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return ApiResponse(success=False, error="邮箱格式不正确")

        if len(password) < 8:
            return ApiResponse(success=False, error="密码至少需要8个字符")

        # 检查重名
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        if result.scalar_one_or_none():
            return ApiResponse(success=False, error="用户名已存在")

        result = await db.execute(select(UserModel).where(UserModel.email == email))
        if result.scalar_one_or_none():
            return ApiResponse(success=False, error="邮箱已被注册")

        # 创建用户
        from datetime import datetime
        new_user = UserModel(
            username=username,
            email=email,
            password=hash_password(password),  # 使用 hash_password 函数
            is_active=True,
            date_joined=datetime.now()
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # 生成token
        access_token = create_jwt_token(subject=str(new_user.id), token_type="access")
        refresh_token = create_jwt_token(subject=str(new_user.id), token_type="refresh")

        return ApiResponse(
            success=True,
            data={
                "user": {
                    "id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "message": "注册成功"
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in mobile_register: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))
