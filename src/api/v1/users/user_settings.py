from typing import Optional

from fastapi import Request, Depends, APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from src.api.v1.user_utils.user_entities import check_user_conflict, change_username, bind_email, db_save_bio, \
    save_uploaded_avatar
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db
from src.utils.security.safe import valid_language_codes
from src.utils.send_email import request_email_change


class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    profile_private: Optional[bool] = None
    locale: Optional[str] = None


class ChangeEmailRequest(BaseModel):
    email: str


class ChangePrivacyRequest(BaseModel):
    profile_private: bool = False


class ChangeLocaleRequest(BaseModel):
    locale: str = "zh_CN"


async def setting_profiles_back(user_id: int, user_info, cache_instance, avatar_url_api: str,
                                db: AsyncSession):
    try:
        if user_info is None:
            return JSONResponse(content={"error": "用户信息未找到"}, status_code=404)

        # 获取用户对象
        from sqlalchemy import select
        user_query = select(User).where(User.id == user_id)
        user_result = db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            return JSONResponse(content={"error": "用户不存在"}, status_code=404)

        avatar_url = user.profile_picture if user.profile_picture else avatar_url_api
        bio = user.bio or "这人很懒，什么也没留下"

        # 这里简化处理，返回JSON响应，实际应用中可能需要返回HTML模板
        return {
            'avatar_url': avatar_url,
            'username': user.username,
            'limit_username_lock': cache_instance.get(f'limit_username_lock_{user_id}'),
            'bio': bio,
            'user_email': user.email,
            'profile_private': user.profile_private,
        }
    except Exception as e:
        print(f"Error in setting_profiles_back: {e}")
        return JSONResponse(content={"error": "服务器内部错误"}, status_code=500)


async def change_profiles_back(
        request: Request,
        user_id: int,
        cache_instance,
        domain: str,
        db: AsyncSession
):
    data = await request.json()
    change_type = data.get('change_type')

    if not change_type:
        return JSONResponse(content={'error': 'Change type is required'}, status_code=400)

    if change_type not in ['avatar', 'username', 'email', 'password', 'bio', 'privacy', 'locale']:
        return JSONResponse(content={'error': 'Invalid change type'}, status_code=400)

    # 清除缓存
    # cache_instance.delete_memoized(current_app.view_functions['api.api_user_profile'], user_id=user_id)

    from sqlalchemy import select
    user_query = select(User).where(User.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    if not user:
        return JSONResponse(content={'error': 'User not found'}, status_code=404)

    if change_type == 'username':
        form_data = data.get('form_data', {})
        username = form_data.get('username')

        # 检查用户名修改限制
        limit_username_lock = cache_instance.get(f'limit_username_lock_{user_id}')
        if limit_username_lock:
            return JSONResponse(content={'error': 'Cannot change username more than once a week'}, status_code=400)

        # 检查用户名冲突
        if check_user_conflict('username', username, db):
            return JSONResponse(content={'error': 'Username already exists'}, status_code=400)

        # 更新用户名
        await change_username(user_id, username, db)
        cache_instance.set(f'limit_username_lock_{user_id}', True, ex=604800)
        return JSONResponse(content={'message': 'Username updated successfully'})

    elif change_type == 'email':
        form_data = data.get('form_data', {})
        email = form_data.get('email')

        # 检查邮箱冲突
        if check_user_conflict('email', email, db):
            return JSONResponse(content={'error': 'Email already exists'}, status_code=400)

        # 请求邮箱变更
        await request_email_change(user_id, cache_instance, domain, email)
        return JSONResponse(content={'message': 'Email updated successfully'})

    elif change_type == 'bio':
        form_data = data.get('form_data', {})
        bio = form_data.get('bio')
        await db_save_bio(user_id, bio, db)
        return JSONResponse(content={'message': 'Bio updated successfully'})

    elif change_type == 'privacy':
        # 重新获取用户对象以确保在当前会话中
        from sqlalchemy import select
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            return JSONResponse(content={'error': 'User not found'}, status_code=404)

        profile_private = data.get('profile_private', False)
        user.profile_private = bool(profile_private)
        await db.commit()
        return JSONResponse(content={'message': 'Privacy settings updated successfully'})

    elif change_type == 'locale':
        # 重新获取用户对象以确保在当前会话中
        from sqlalchemy import select
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            return JSONResponse(content={'error': 'User not found'}, status_code=404)

        locale = data.get('locale', 'zh_CN')
        if not valid_language_codes(locale):
            return JSONResponse(content={'error': 'Invalid locale'}, status_code=400)
        user.locale = locale
        await db.commit()
        return JSONResponse(content={'message': 'Locale updated successfully'})

    else:
        # 调用编辑配置文件函数
        return await update_setting_profiles(request, change_type, user_id, db)


async def confirm_email_back(
        user_id: int,
        cache_instance,
        token: str,
        db: AsyncSession
):
    # 从缓存获取临时邮箱信息
    temp_email_data = cache_instance.get(f"temp_email_{user_id}")
    if not temp_email_data:
        return JSONResponse(content={"error": "Invalid verification data"}, status_code=400)

    new_email = temp_email_data.get('new_email')
    token_value = temp_email_data.get('token')

    # 验证令牌匹配
    if token != token_value:
        return JSONResponse(content={"error": "Invalid verification data"}, status_code=400)

    await bind_email(user_id, new_email, db)
    # cache_instance.delete_memoized(current_app.view_functions['api.api_user_profile'], user_id=user_id)

    return {"status": "success", "message": "Email updated successfully"}


# 创建API路由器
router = APIRouter(tags=["user-settings"])


@router.post("/profile/avatar", response_model_exclude_none=True)
async def update_avatar_api(
        file: UploadFile = File(..., description="头像文件"),
        current_user=Depends(jwt_required)
):
    """
    更新用户头像API

    Args:
        file: 上传的头像文件（JPG、PNG、WEBP格式，最大5MB）

    Returns:
        JSON响应，包含成功状态和头像URL
    """
    try:
        # 调试日志
        print(f"[Avatar Upload] === START ===")
        print(f"[Avatar Upload] Received request from user: {current_user.id}")
        print(f"[Avatar Upload] File name: {file.filename}")
        print(f"[Avatar Upload] Content type: {file.content_type}")
        print(f"[Avatar Upload] File size attr: {file.size if hasattr(file, 'size') else 'unknown'}")

        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
        if file.content_type not in allowed_types:
            print(f"[Avatar Upload] Invalid content type: {file.content_type}")
            return JSONResponse(
                content={"success": False, "error": "不支持的文件类型"},
                status_code=400
            )

        # 验证文件大小 (最大5MB)
        file_content = await file.read()
        print(f"[Avatar Upload] Actual file size: {len(file_content)} bytes")
        if len(file_content) > 5 * 1024 * 1024:
            return JSONResponse(
                content={"success": False, "error": "文件大小不能超过5MB"},
                status_code=400
            )

        # 重置文件指针，因为我们需要再次读取文件
        await file.seek(0)

        # 获取数据库会话
        from src.extensions import get_async_db_session
        db = await get_async_db_session().__anext__()
        try:
            result = await save_uploaded_avatar(file, current_user.id, db)
        finally:
            await db.close()

        # 构建头像 URL
        avatar_url = f"/api/v2/static/avatar/{result}.webp"
        print(f"[Avatar Upload] Success! Avatar URL: {avatar_url}")
        print(f"[Avatar Upload] === END ===")
        return JSONResponse(content={"success": True, "avatar_url": avatar_url})
    except Exception as e:
        import traceback
        print(f"[Avatar Upload] Error: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(content={"error": f"头像更新失败: {str(e)}"}, status_code=500)


@router.put("/profiles")
async def update_setting_profiles(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新设置资料API - 处理用户名、简介、隐私设置等更新
    """
    try:
        from src.extensions import cache
        from src.setting import app_config

        # 调用现有的处理函数
        result = await change_profiles_back(
            request=request,
            user_id=current_user.id,
            cache_instance=cache,
            domain=app_config.domain,
            db=db,
        )

        return result
    except Exception as e:
        import traceback
        print(f"Error in update_setting_profiles: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)
