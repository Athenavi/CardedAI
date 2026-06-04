"""
用户模块 - 统一入口
整合所有用户相关功能：资料管理、设置、关注、屏蔽等

按照 RESTful 最佳实践重新组织路由结构：
- /me: 当前用户操作
- /{user_id}: 其他用户公开信息
- 子路径用于特定功能（如 follow, block, settings 等）
"""
import os
# 导入用户关系和屏蔽服务
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.models.user_block import UserBlock
# 导入原有服务
from shared.services.users.user_manager import user_csv_service
# 导入核心依赖
from src.api.v1.core.responses import ApiResponse
from src.api.v1.user_utils.password_utils import validate_password_async, update_password
from src.api.v1.user_utils.user_entities import check_user_conflict_async, change_username, db_save_bio, \
    save_uploaded_avatar
from src.auth.auth_deps import admin_required as admin_required_api, jwt_required_dependency as jwt_required, \
    get_current_active_user
from src.extensions import cache
from src.extensions import get_async_db_session as get_async_db
from src.setting import app_config
from src.utils.security.forms import ChangePasswordForm
from src.utils.security.ip_utils import get_client_ip
from src.utils.security.safe import is_valid_iso_language_code
from src.utils.send_email import request_email_change

router = APIRouter(tags=["users"])


# ==================== 用户列表和管理员功能 ====================

@router.get("/",
            summary="获取用户列表",
            description="获取用户列表，支持分页和搜索功能（仅管理员）",
            response_description="返回用户列表和分页信息")
async def get_users_list_api(
        request: Request,
        page: int = Query(1, ge=1, description="页码，从 1 开始"),
        per_page: int = Query(10, ge=1, le=100, description="每页显示数量，1-100 之间"),
        search: str = Query("", description="搜索关键词，用于用户名或邮箱搜索"),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """获取用户列表 API (仅管理员)"""
    try:
        query = select(User)

        if search:
            query = query.filter(
                User.username.contains(search) |
                User.email.contains(search)
            )

        # 分页
        offset = (page - 1) * per_page
        # 获取总数
        total_query = select(func.count(User.id))
        if search:
            total_query = total_query.where(
                User.username.contains(search) |
                User.email.contains(search)
            )
        total_result = await db.execute(total_query)
        total = total_result.scalar()

        # 获取分页数据
        users_query = select(User)
        if search:
            users_query = users_query.where(
                User.username.contains(search) |
                User.email.contains(search)
            )
        users_query = users_query.offset(offset).limit(per_page)
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()

        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_superuser": getattr(user, 'is_superuser', False),
                "created_at": user.date_joined.isoformat() if hasattr(user,
                                                                      'date_joined') and user.date_joined else None,
                "last_login": getattr(user, 'last_login', None).isoformat() if getattr(user, 'last_login',
                                                                                       None) else None
            })

        return ApiResponse(
            success=True,
            data=users_data,
            pagination={
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "has_next": page < (total + per_page - 1) // per_page,
                "has_prev": page > 1
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_users_list_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/import-csv",
             summary="导入用户CSV",
             description="从CSV文件导入用户（仅管理员）",
             response_description="返回导入结果")
async def import_users_csv_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """从CSV文件导入用户"""
    try:
        # 读取上传的文件
        form_data = await request.form()
        csv_file = form_data.get('file')

        if not csv_file:
            return ApiResponse(success=False, error='未提供CSV文件')

        # 读取文件内容
        csv_content = await csv_file.read()
        csv_text = csv_content.decode('utf-8-sig')

        # 解析CSV
        result = user_csv_service.parse_csv_import(csv_text)

        if result['errors']:
            return ApiResponse(
                success=False,
                error='CSV解析错误',
                data={
                    'errors': result['errors'],
                    'valid_count': result.get('valid_count', 0),
                    'error_count': result.get('error_count', 0)
                }
            )

        # 实际创建用户
        created_count = 0
        failed_count = 0
        failed_users = []

        for user_data in result['users']:
            try:
                # 检查用户名是否已存在
                existing_user_query = select(User).where(User.username == user_data['username'])
                existing_user_result = await db.execute(existing_user_query)
                if existing_user_result.scalar_one_or_none():
                    failed_users.append(f"用户名已存在: {user_data['username']}")
                    failed_count += 1
                    continue

                # 检查邮箱是否已存在
                existing_email_query = select(User).where(User.email == user_data['email'])
                existing_email_result = await db.execute(existing_email_query)
                if existing_email_result.scalar_one_or_none():
                    failed_users.append(f"邮箱已存在: {user_data['email']}")
                    failed_count += 1
                    continue

                # 创建新用户
                from datetime import datetime
                new_user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    is_active=True,
                    date_joined=datetime.now(),
                )

                # 设置密码(如果提供)
                if user_data.get('password'):
                    new_user.set_password(user_data['password'])
                else:
                    # 生成随机密码
                    import secrets
                    random_password = secrets.token_urlsafe(8)
                    new_user.set_password(random_password)

                db.add(new_user)
                created_count += 1

            except Exception as e:
                failed_users.append(f"{user_data.get('username', 'Unknown')}: {str(e)}")
                failed_count += 1

        # 提交事务
        if created_count > 0:
            await db.commit()

        message = f'成功导入{created_count}个用户'
        if failed_count > 0:
            message += f', {failed_count}个失败'

        return ApiResponse(
            success=True,
            data={
                'message': message,
                'created_count': created_count,
                'failed_count': failed_count,
                'failed_users': failed_users[:10],  # 只返回前10个错误
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in import_users_csv_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/export-csv",
            summary="导出用户CSV",
            description="导出用户列表为CSV格式（仅管理员）",
            response_description="返回CSV文件内容")
async def export_users_csv_api(
        request: Request,
        fields: str = Query(None, description="要导出的字段，逗号分隔"),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """导出用户列表为CSV"""
    try:
        # 获取所有用户
        users_query = select(User)
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()

        # 转换为字典
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'role': getattr(user, 'role', 'user'),
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'last_login': getattr(user, 'last_login', None),
            })

        # 解析字段
        field_list = fields.split(',') if fields else None

        # 生成CSV
        csv_content = user_csv_service.export_users_to_csv(users_data, field_list)

        # 返回CSV文件
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type='text/csv; charset=utf-8-sig',
            headers={
                'Content-Disposition': 'attachment; filename=users.csv'
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in export_users_csv_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/download-sample-csv",
            summary="下载示例CSV文件",
            description="下载用户导入的示例CSV模板")
async def download_sample_csv_api(
        request: Request,
):
    """下载示例CSV文件API"""
    try:
        # 生成示例CSV
        csv_content = user_csv_service.generate_sample_csv()

        # 返回CSV文件
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type='text/csv; charset=utf-8',
            headers={
                'Content-Disposition': 'attachment; filename=user_import_sample.csv'
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in download_sample_csv_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


# ==================== 当前用户操作 (/me) ====================

@router.get("/me",
            summary="获取当前用户信息",
            description="获取当前认证用户的详细信息，如果访问令牌即将过期则自动刷新",
            response_description="返回当前用户信息及可能的新访问令牌")
async def get_current_user_api(
        request: Request,
        current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息，支持自动刷新即将过期的访问令牌"""
    try:
        # 检查是否在请求处理过程中生成了新的访问令牌
        new_access_token = getattr(request.state, 'new_access_token', None)

        # 构建基础 URL
        base_url = str(request.url).split('/me')[0]
        if base_url.endswith('/'):
            base_url = base_url.rsplit('/', 1)[0]

        # 安全地构建头像 URL，确保路径正确
        avatar_url = None
        if current_user.profile_picture:
            # 移除 profile_picture 中可能的路径分隔符和特殊字符
            safe_filename = current_user.profile_picture.replace('\\', '/').split('/')[-1]
            # 确保文件名不包含可能破坏 JSON 的特殊字符
            safe_filename = safe_filename.replace('"', '').replace("'", "").strip()
            if safe_filename:  # 只有在处理后仍有内容时才使用
                # 直接返回相对路径，让前端自己拼接完整URL
                avatar_url = f"/api/v2/static/avatar/{safe_filename}.webp"

        user_data = {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "avatar": avatar_url,
            "is_active": current_user.is_active,
            "is_superuser": current_user.is_superuser,
            "created_at": current_user.date_joined.isoformat() if hasattr(current_user,
                                                                          'date_joined') and current_user.date_joined else None,
            "last_login": getattr(current_user, 'last_login', None).isoformat() if getattr(current_user, 'last_login',
                                                                                           None) else None
        }

        response_data = {
            "success": True,
            "data": user_data
        }

        # 如果有新的访问令牌，将其添加到响应中
        if new_access_token:
            response_data["new_access_token"] = new_access_token

        # 返回JSONResponse以便设置响应头
        response = JSONResponse(content=response_data)

        # 如果有新的访问令牌，将其设置在响应头中
        if new_access_token:
            # 根据环境自动设置 Cookie 安全标志
            is_https = str(app_config.domain).startswith('https://') or os.environ.get('DEBUG',
                                                                                       'False').lower() == 'false'
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=is_https,  # 生产环境（HTTPS）设为 True
                samesite="strict",
                max_age=3600  # 1 小时
            )

        return response
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)})


@router.put("/me",
            summary="更新当前用户资料",
            description="更新当前认证用户的基本资料信息",
            response_description="返回更新后的用户资料信息")
async def update_current_user_profile_api(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
):
    """更新用户资料API"""
    try:
        data = await request.json()

        # 从当前会话中重新获取用户对象，确保对象在会话中
        from sqlalchemy import select
        user_query = select(User).where(User.id == current_user.id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return ApiResponse(success=False, error='User not found')

        # 更新用户信息
        for field in ['username', 'email', 'bio', 'profile_private', 'locale']:
            if field in data:
                if field == 'username':
                    # 检查用户名修改限制
                    limit_username_lock = cache.get(f'limit_username_lock_{user.id}')
                    if limit_username_lock:
                        return ApiResponse(success=False, error='Cannot change username more than once a week')

                    # 检查用户名冲突
                    if await check_user_conflict_async('username', data[field], db):
                        return ApiResponse(success=False, error='Username already exists')

                    await change_username(user.id, data[field], db)
                    cache.set(f'limit_username_lock_{user.id}', True, ex=604800)
                elif field == 'email':
                    # 检查邮箱冲突
                    if await check_user_conflict_async('email', data[field], db):
                        return ApiResponse(success=False, error='Email already exists')
                    # 请求邮箱变更
                    await request_email_change(user.id, cache, app_config.domain, data[field])
                elif field == 'bio':
                    await db_save_bio(user.id, data[field], db)
                elif field == 'locale':
                    if not is_valid_iso_language_code(data[field]):
                        return ApiResponse(success=False, error='Invalid locale')
                    user.locale = data[field]
                else:
                    setattr(user, field, data[field])

        await db.commit()
        await db.refresh(user)

        # 构建头像 URL
        avatar_url = None
        if user.profile_picture:
            safe_filename = user.profile_picture.replace('\\', '/').split('/')[-1]
            safe_filename = safe_filename.replace('"', '').replace("'", "").strip()
            if safe_filename:
                # 直接返回相对路径，让前端自己拼接完整URL
                avatar_url = f"/api/v2/static/avatar/{safe_filename}.webp"

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": avatar_url,
            "bio": user.bio,
            "profile_private": user.profile_private,
            "locale": user.locale,
            "last_login": getattr(user, 'last_login', None).isoformat() if getattr(user, 'last_login',
                                                                                   None) else None
        }

        return ApiResponse(
            success=True,
            data=user_data
        )
    except Exception as e:
        import traceback
        print(f"Error in update_current_user_profile_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/me/change-password",
             summary="修改密码",
             description="修改当前认证用户的密码",
             response_description="返回密码修改结果")
async def change_password_api(
        request: Request,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """修改密码 API"""
    try:
        form_data = await request.form()
        form = ChangePasswordForm(data=dict(form_data))

        if not form.validate():
            return ApiResponse(
                success=False,
                error=' '.join(error for errors in form.errors.values() for error in errors)
            )

        # 验证当前密码是否正确
        is_valid = await validate_password_async(
            current_user.id,
            form.current_password.data,
            db
        )

        if not is_valid:
            return ApiResponse(success=False, error='当前密码不正确')

        ip = get_client_ip(request)
        success = await update_password(
            current_user.id,
            new_password=form.new_password.data,
            confirm_password=form.confirm_password.data,
            ip=ip,
            db=db
        )

        if not success:
            return ApiResponse(success=False, error='密码修改失败')

        # 清除临时标记
        cache_key = f"password_change_verified_{current_user.id}"
        cache.delete(cache_key)

        return ApiResponse(
            success=True,
            data={'message': '密码修改成功！现在需要重新登录。'}
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in change_password_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=f"密码修改失败: {str(e)}")


@router.post("/me/avatar",
             summary="更新用户头像",
             description="上传并更新用户头像",
             response_description="返回成功状态和头像URL")
async def update_avatar_api(
        file: UploadFile = File(..., description="头像文件"),
        current_user=Depends(jwt_required)
):
    """更新用户头像API"""
    try:
        # 调试日志
        print(f"[Avatar Upload] === START ===")
        print(f"[Avatar Upload] Received request from user: {current_user.id}")
        print(f"[Avatar Upload] File name: {file.filename}")
        print(f"[Avatar Upload] Content type: {file.content_type}")

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


@router.get("/me/settings",
            summary="获取当前用户设置",
            description="获取当前用户的个人设置")
async def get_user_settings_api(
        current_user: User = Depends(get_current_active_user)
):
    """获取用户设置"""
    try:
        return ApiResponse(
            success=True,
            data={
                "profile_private": current_user.profile_private,
                "locale": current_user.locale,
                "bio": current_user.bio,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/me/settings",
            summary="更新当前用户设置",
            description="更新当前用户的个人设置（隐私、语言等）")
async def update_user_settings_api(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
):
    """更新用户设置"""
    try:
        data = await request.json()

        if 'profile_private' in data:
            current_user.profile_private = bool(data['profile_private'])

        if 'locale' in data:
            if not is_valid_iso_language_code(data['locale']):
                return ApiResponse(success=False, error='Invalid locale')
            current_user.locale = data['locale']

        await db.commit()

        return ApiResponse(
            success=True,
            message="设置更新成功",
            data={
                "profile_private": current_user.profile_private,
                "locale": current_user.locale,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 关注和粉丝功能 ====================

# 使用内存存储关注关系(生产环境应使用数据库)
follows_db = {}
followers_db = {}


@router.get("/me/followers",
            summary="获取当前用户的粉丝列表")
async def get_followers(
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户的粉丝列表"""
    try:
        # 从内存中获取粉丝
        fans_dict = followers_db.get(current_user.id, {})

        # 构建粉丝列表
        fans_list = []
        for follower_id, follow_time in fans_dict.items():
            # 查询用户信息
            user_query = select(User).where(User.id == int(follower_id))
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                fans_list.append({
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "bio": user.bio,
                        "profile_picture": user.profile_picture
                    },
                    "created_at": datetime.fromtimestamp(follow_time).isoformat()
                })

        # 按关注时间倒序排列
        fans_list.sort(key=lambda x: x['created_at'], reverse=True)

        return ApiResponse(
            success=True,
            data={
                "fans_list": fans_list,
                "fans_count": len(fans_list)
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_followers: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/me/following",
            summary="获取当前用户关注的用户列表")
async def get_following(
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户关注的用户列表"""
    try:
        # 从内存中获取关注的用户
        following_dict = follows_db.get(current_user.id, {})

        # 构建关注列表
        following_list = []
        for following_id, follow_time in following_dict.items():
            # 查询用户信息
            user_query = select(User).where(User.id == int(following_id))
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                following_list.append({
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "bio": user.bio,
                        "profile_picture": user.profile_picture
                    },
                    "created_at": datetime.fromtimestamp(follow_time).isoformat()
                })

        # 按关注时间倒序排列
        following_list.sort(key=lambda x: x['created_at'], reverse=True)

        return ApiResponse(
            success=True,
            data={
                "following_list": following_list,
                "following_count": len(following_list)
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_following: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/me/blocked",
            summary="获取我屏蔽的用户列表")
async def get_blocked_users(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取我屏蔽的用户列表"""
    try:
        offset = (page - 1) * per_page

        # 查询总数
        count_query = (
            select(func.count())
            .select_from(UserBlock)
            .where(UserBlock.blocker == current_user.id)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 查询屏蔽列表
        query = (
            select(UserBlock, User.username, User.profile_picture)
            .join(User, UserBlock.blocked_user == User.id)
            .where(UserBlock.blocker == current_user.id)
            .order_by(UserBlock.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )

        result = await db.execute(query)
        blocked_list = []

        for row in result.fetchall():
            block_record = row[0]
            blocked_list.append({
                "block_id": block_record.id,
                "user_id": block_record.blocked_user,
                "username": row[1],
                "avatar": row[2],
                "reason": block_record.reason,
                "blocked_at": block_record.created_at.isoformat()
            })

        return ApiResponse(
            success=True,
            data={
                "blocked_users": blocked_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_blocked_users: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/me/block/{user_id}",
             summary="屏蔽指定用户")
async def block_user(
        user_id: int,
        reason: Optional[str] = Query(None, description="屏蔽原因"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """屏蔽/拉黑指定用户"""
    try:
        # 不能屏蔽自己
        if user_id == current_user.id:
            return ApiResponse(success=False, error="不能屏蔽自己")

        # 验证被屏蔽用户是否存在
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        blocked_user = user_result.scalar_one_or_none()

        if not blocked_user:
            return ApiResponse(success=False, error="用户不存在")

        # 检查是否已经屏蔽
        existing_query = select(UserBlock).where(
            and_(
                UserBlock.blocker == current_user.id,
                UserBlock.blocked_user == user_id
            )
        )
        existing_result = await db.execute(existing_query)
        existing_block = existing_result.scalar_one_or_none()

        if existing_block:
            return ApiResponse(success=False, error="已经屏蔽了该用户")

        # 创建屏蔽记录
        new_block = UserBlock(
            blocker=current_user.id,
            blocked_user=user_id,
            reason=reason,
            created_at=datetime.now()
        )

        db.add(new_block)
        await db.commit()

        return ApiResponse(
            success=True,
            message="屏蔽成功"
        )
    except Exception as e:
        import traceback
        print(f"Error in block_user: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/me/block/{user_id}",
               summary="取消屏蔽指定用户")
async def unblock_user(
        user_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """取消屏蔽指定用户"""
    try:
        # 查询屏蔽记录
        query = select(UserBlock).where(
            and_(
                UserBlock.blocker == current_user.id,
                UserBlock.blocked_user == user_id
            )
        )
        result = await db.execute(query)
        block_record = result.scalar_one_or_none()

        if not block_record:
            return ApiResponse(success=False, error="未找到屏蔽记录")

        # 删除屏蔽记录
        await db.delete(block_record)
        await db.commit()

        return ApiResponse(
            success=True,
            message="取消屏蔽成功"
        )
    except Exception as e:
        import traceback
        print(f"Error in unblock_user: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


# ==================== 其他用户公开信息 (/{user_id}) ====================

@router.get("/{user_id}",
            summary="获取其他用户公开资料",
            description="获取指定用户的公开资料信息")
async def get_user_profile_api(
        user_id: int,
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
):
    """获取用户公开资料"""
    try:
        # 查询用户
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return ApiResponse(success=False, error="用户不存在")

        # 安全地处理 profile_picture
        avatar_url = None
        if user.profile_picture:
            safe_filename = user.profile_picture.replace('\\', '/').split('/')[-1]
            safe_filename = safe_filename.replace('"', '').replace("'", "").strip()
            if safe_filename:
                base_url = str(request.url).rsplit('/', 1)[0]
                avatar_url = f"{base_url}/api/v2/static/avatar/{safe_filename}.webp"

        user_data = {
            "id": user.id,
            "username": user.username,
            "avatar": avatar_url,
            "bio": user.bio,
            "created_at": user.date_joined.isoformat() if hasattr(user,
                                                                  'date_joined') and user.date_joined else None,
        }

        return ApiResponse(
            success=True,
            data=user_data
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{user_id}/follow",
             summary="关注指定用户")
async def follow_user(
        user_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """关注指定用户"""
    try:
        # 不能关注自己
        if user_id == current_user.id:
            return ApiResponse(success=False, error="不能关注自己")

        # 验证目标用户是否存在
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        target_user = user_result.scalar_one_or_none()

        if not target_user:
            return ApiResponse(success=False, error="目标用户不存在")

        # 初始化数据结构
        if current_user.id not in follows_db:
            follows_db[current_user.id] = {}
        if user_id not in followers_db:
            followers_db[user_id] = {}

        # 检查是否已经关注
        if user_id in follows_db[current_user.id]:
            return ApiResponse(success=False, error="已经关注过该用户")

        # 添加关注关系
        current_time = datetime.now().timestamp()
        follows_db[current_user.id][user_id] = current_time
        followers_db[user_id][current_user.id] = current_time

        return ApiResponse(
            success=True,
            data={"message": "关注成功"},
            message="关注成功"
        )
    except Exception as e:
        import traceback
        print(f"Error in follow_user: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/{user_id}/follow",
               summary="取消关注指定用户")
async def unfollow_user(
        user_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """取消关注指定用户"""
    try:
        # 验证目标用户是否存在
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        target_user = user_result.scalar_one_or_none()

        if not target_user:
            return ApiResponse(success=False, error="目标用户不存在")

        # 检查是否已关注
        if current_user.id not in follows_db or user_id not in follows_db[current_user.id]:
            return ApiResponse(success=False, error="尚未关注该用户")

        # 移除关注关系
        del follows_db[current_user.id][user_id]
        if user_id in followers_db:
            if current_user.id in followers_db[user_id]:
                del followers_db[user_id][current_user.id]

        return ApiResponse(
            success=True,
            data={"message": "取消关注成功"},
            message="取消关注成功"
        )
    except Exception as e:
        import traceback
        print(f"Error in unfollow_user: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/{user_id}/followers",
            summary="获取指定用户的粉丝列表")
async def get_user_followers(
        user_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
):
    """获取指定用户的粉丝列表"""
    try:
        # 从内存中获取粉丝
        fans_dict = followers_db.get(user_id, {})

        # 构建粉丝列表
        fans_list = []
        for follower_id, follow_time in fans_dict.items():
            # 查询用户信息
            user_query = select(User).where(User.id == int(follower_id))
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                fans_list.append({
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "bio": user.bio,
                        "profile_picture": user.profile_picture
                    },
                    "created_at": datetime.fromtimestamp(follow_time).isoformat()
                })

        # 按关注时间倒序排列
        fans_list.sort(key=lambda x: x['created_at'], reverse=True)

        return ApiResponse(
            success=True,
            data={
                "fans_list": fans_list,
                "fans_count": len(fans_list)
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_user_followers: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/{user_id}/following",
            summary="获取指定用户关注的用户列表")
async def get_user_following(
        user_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
):
    """获取指定用户关注的用户列表"""
    try:
        # 从内存中获取关注的用户
        following_dict = follows_db.get(user_id, {})

        # 构建关注列表
        following_list = []
        for following_id, follow_time in following_dict.items():
            # 查询用户信息
            user_query = select(User).where(User.id == int(following_id))
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                following_list.append({
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "bio": user.bio,
                        "profile_picture": user.profile_picture
                    },
                    "created_at": datetime.fromtimestamp(follow_time).isoformat()
                })

        # 按关注时间倒序排列
        following_list.sort(key=lambda x: x['created_at'], reverse=True)

        return ApiResponse(
            success=True,
            data={
                "following_list": following_list,
                "following_count": len(following_list)
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_user_following: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/{user_id}/activity",
            summary="获取用户活跃度",
            description="获取用户活跃度等级和评分（仅管理员或用户本人）")
async def get_user_activity(
        user_id: int,
        days: int = Query(30, ge=7, le=90, description="统计天数"),
        current_user=Depends(get_current_active_user)
):
    """获取用户活跃度等级和评分"""
    try:
        from shared.services.users.user_profile_service import user_profile_service
        activity = user_profile_service.get_activity_level(user_id, days)

        return ApiResponse(
            success=True,
            data=activity
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取活跃度失败: {str(e)}")


@router.get("/{user_id}/interests",
            summary="获取用户兴趣标签",
            description="基于用户的阅读历史、点赞、收藏等行为分析得出（仅管理员或用户本人）")
async def get_user_interests(
        user_id: int,
        top_n: int = Query(10, ge=1, le=50, description="返回标签数量"),
        current_user=Depends(get_current_active_user)
):
    """获取用户兴趣标签列表"""
    try:
        from shared.services.users.user_profile_service import user_profile_service
        interests = user_profile_service.get_user_interests(user_id, top_n)

        return ApiResponse(
            success=True,
            data={
                'interests': interests,
                'count': len(interests),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取兴趣标签失败: {str(e)}")


# ==================== 用户推荐（原 discover）===================

@router.get("/recommendations",
            summary="推荐用户",
            description="获取推荐用户列表用于发现其他用户（排除当前用户）。\n\n注意：此端点返回的是用户推荐，不是文章或内容推荐。")
async def recommend_users(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取推荐用户列表(用于发现用户)"""
    try:
        offset = (page - 1) * per_page

        # 查询所有用户(排除自己)
        query = (
            select(User)
            .where(User.id != current_user.id)
            .offset(offset)
            .limit(per_page)
        )

        result = await db.execute(query)
        users = result.scalars().all()

        # 获取总数
        count_query = (
            select(func.count())
            .select_from(User)
            .where(User.id != current_user.id)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 构建用户列表
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "bio": user.bio,
                "profile_picture": user.profile_picture
            })

        # 获取当前用户已关注的用户ID
        following_dict = follows_db.get(current_user.id, {})
        following_ids = [int(uid) for uid in following_dict.keys()]

        return ApiResponse(
            success=True,
            data={
                "users": user_list,
                "following_ids": following_ids,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in recommend_users: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))



