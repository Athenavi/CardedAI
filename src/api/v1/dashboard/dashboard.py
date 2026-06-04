"""
仪表板相关 API
"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy import desc
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import VIPPlan, VIPFeature
from shared.models.article import Article
from shared.models.category import Category
from shared.models.file_hash import FileHash
from shared.models.media import Media
from shared.models.notification import Notification
from shared.models.user import User
# 导入 SQLAlchemy 模型和服务
from shared.models.user import User as UserModel
from shared.models.user_activity import UserActivity
from shared.models.vip_subscription import VIPSubscription
# 注意：避免在此处直接导入 article_service，防止循环依赖
# article_service 的导入已移至使用位置
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api, jwt_required_dependency as jwt_required, \
    get_current_active_user
from src.extensions import get_async_db_session as get_async_db

router = APIRouter()


@router.get("/activities")
async def get_activities(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(8, ge=1, le=50),
    current_user: User = Depends(admin_required_api),
    db: AsyncSession = Depends(get_async_db)
):
    """获取最近用户活动列表"""
    offset = (page - 1) * per_page
    query = select(UserActivity).order_by(desc(UserActivity.created_at)).offset(offset).limit(per_page)
    result = await db.execute(query)
    activities = result.scalars().all()

    data = [
        {
            "message": f"{a.activity_type or ''} - {a.details or ''}",
            "action": a.activity_type,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in activities
    ]
    return ApiResponse.success_response(data=data)


@router.get("/stats")
async def get_dashboard_stats(
        request: Request,
        current_user: User = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取仪表板统计数据
    """
    try:
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        # 计算总用户数
        total_users_query = select(func.count()).select_from(User)
        total_users_result = await db.execute(total_users_query)
        total_users = total_users_result.scalar()

        # 计算总文章数
        total_articles_query = select(func.count()).select_from(Article)
        total_articles_result = await db.execute(total_articles_query)
        total_articles = total_articles_result.scalar()

        # 计算总点赞数 (使用Article模型中的likes字段)
        total_likes_query = select(func.sum(Article.likes))
        total_likes_result = await db.execute(total_likes_query)
        total_likes = total_likes_result.scalar() or 0

        # 计算总浏览量
        total_views_query = select(func.sum(Article.views))
        total_views_result = await db.execute(total_views_query)
        total_views = total_views_result.scalar() or 0

        # 获取最近一周的用户注册数
        week_ago = datetime.now() - timedelta(days=7)
        new_users_query = select(func.count()).select_from(User).where(User.date_joined >= week_ago)
        new_users_result = await db.execute(new_users_query)
        new_users = new_users_result.scalar()

        stats_data = {
            "visitors": total_views,  # 使用真实浏览量
            "articles": total_articles,
            "comments": 0,  # 暂时设为0，因为评论模型未定义
            "likes": total_likes,
            "users": total_users,
            "new_users": new_users
        }

        return ApiResponse(
            success=True,
            data=stats_data
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/recent-articles")
async def __get_recent_articles(
        request: Request,
        current_user: User = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取最近的文章
    """
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from sqlalchemy import desc

        # 查询最近的文章（按创建时间排序），使用预加载来避免N+1问题
        recent_articles_query = select(Article).order_by(
            desc(Article.created_at)).limit(4)
        recent_articles_result = await db.execute(recent_articles_query)
        recent_articles = recent_articles_result.scalars().all()

        articles_data = []
        for article in recent_articles:
            # 获取作者信息（由于 author 关系已注释，使用 user_id）
            author_username = "Unknown"  # 暂时显示 Unknown
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "author": author_username,
                "views": getattr(article, 'views', 0),
                "comments": 0,  # 暂时设为 0，因为评论模型未定义
                "created_at": article.created_at.isoformat() if hasattr(article.created_at, 'isoformat') else str(
                    article.created_at),
                "status": "published" if getattr(article, 'status', 0) == 1 else "draft"  # status 为 1 表示 published
            })

        return ApiResponse(
            success=True,
            data=articles_data
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/traffic")
async def get_traffic_data(
        request: Request,
        current_user: User = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取流量数据
    """
    try:
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        # 计算过去7天每天的文章浏览量
        traffic_data = []
        for i in range(7):
            date_start = datetime.now() - timedelta(days=i)
            date_end = date_start + timedelta(days=1)
            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_end.replace(hour=0, minute=0, second=0, microsecond=0)

            # 计算当天的文章浏览量总和
            daily_views_query = select(func.sum(Article.views)).where(
                Article.created_at >= date_start,
                Article.created_at < date_end
            )
            daily_views_result = await db.execute(daily_views_query)
            daily_views = daily_views_result.scalar() or 0

            traffic_data.append({
                "date": date_start.strftime("%m-%d"),
                "visitors": daily_views
            })

        # 按日期升序排列
        traffic_data.reverse()

        return ApiResponse(
            success=True,
            data=traffic_data
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/blog-management/articles")
async def get_blog_management_articles(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        status: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        category_id: Optional[int] = Query(None),
        current_user: User = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取博客管理文章列表
    """
    try:
        # 使用SQLAlchemy异步查询语法
        from sqlalchemy import select, func

        # 构建基础查询（category 是外键字段，不是 relationship，不能直接使用 selectinload）
        query = select(Article)

        # 根据状态过滤
        if status:
            # 转换为小写以匹配映射
            status_lower = status.lower()
            status_map = {'published': 1, 'draft': 0, 'deleted': -1}
            if status_lower in status_map:
                query = query.where(Article.status == status_map[status_lower])

        # 根据搜索词过滤
        if search:
            query = query.where(Article.title.contains(search))

        # 根据分类ID过滤
        if category_id:
            query = query.where(Article.category == category_id)

        # 计算总数
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar()

        # 分页查询
        offset = (page - 1) * per_page
        articles_query = query.offset(offset).limit(per_page)
        articles_result = await db.execute(articles_query)
        articles = articles_result.scalars().all()

        articles_data = []
        for article in articles:
            # 使用模型的 to_dict() 方法获取基础数据
            article_dict = article.to_dict()

            # 确定文章状态（转换为字符串）
            article_status = 'draft'
            if article.status == 1:
                article_status = 'published'
            elif article.status == 0:
                article_status = 'draft'
            elif article.status == -1:
                article_status = 'deleted'

            # 获取作者信息（由于 author 关系已注释，需要手动查询）
            from sqlalchemy import select
            from shared.models.user import User
            author_query = select(User).where(User.id == article.user)
            author_result = await db.execute(author_query)
            author = author_result.scalar_one_or_none()
            author_info = {
                "id": author.id if author else article.user,
                "username": getattr(author, 'username', 'Unknown') if author else 'Unknown',
                "email": getattr(author, 'email', '') if author else ''
            }

            # 获取分类信息
            category_info = None
            if article.category:
                category_query = select(Category).where(Category.id == article.category)
                category_result = await db.execute(category_query)
                category = category_result.scalar_one_or_none()
                if category:
                    category_info = {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description
                    }

            # 处理标签（将 tags_list 字符串转换为数组，支持逗号和分号分隔符）
            tags_list = []
            if article_dict.get('tags_list'):
                if isinstance(article_dict['tags_list'], str):
                    tags_list = [tag.strip() for tag in re.split(r'[,;]', article_dict['tags_list']) if tag.strip()]
                else:
                    tags_list = article_dict['tags_list']

            # 构建响应数据，在 to_dict() 基础上添加关联数据
            articles_data.append({
                **article_dict,  # 展开模型的基础字段
                "summary": article_dict.get('excerpt', ''),  # summary 是 excerpt 的别名
                "tags": tags_list,  # 转换后的标签数组
                "views_count": article_dict.get('views', 0),  # 前端期望的字段名
                "status": article_status,  # 覆盖为字符串状态
                "author": author_info,  # 添加作者信息
                "category": category_info,  # 添加分类信息
            })

        return ApiResponse(
            success=True,
            data=articles_data,
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
        print(f"Error in get_blog_management_articles: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/my/articles")
async def get_my_articles(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        status: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        hidden: Optional[bool] = Query(None),
    category_id: Optional[int] = Query(None, description="按分类 ID 筛选"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取我的文章列表
    """
    try:
        from sqlalchemy import select, func, or_
        from sqlalchemy.orm import selectinload

        # 构建基础查询，预加载关联的作者信息
        query = select(Article).join(User, Article.user == User.id).where(
            Article.user == current_user.id)

        # 根据状态过滤
        if status:
            # 转换为小写以匹配映射
            status_lower = status.lower()
            status_map = {'published': 1, 'draft': 0, 'deleted': -1}
            if status_lower in status_map:
                query = query.where(Article.status == status_map[status_lower])

        # 根据隐藏状态过滤
        if hidden is not None:
            query = query.where(Article.hidden == hidden)

        # 根据分类过滤
        if category_id is not None:
            query = query.where(Article.category == category_id)

        # 根据标签过滤（在 tags_list 字段中搜索）
        if tag:
            query = query.where(Article.tags_list.contains(tag))

        # 搜索功能
        if search:
            query = query.where(
                or_(
                    Article.title.contains(search),
                    Article.excerpt.contains(search)
                )
            )

        # 计算总数
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar()

        # 分页查询
        offset = (page - 1) * per_page
        articles_query = query.offset(offset).limit(per_page)
        articles_result = await db.execute(articles_query)
        articles = articles_result.scalars().all()

        # 批量查询分类名称（避免 N+1 查询）
        from shared.models.category import Category
        category_ids = list(set(a.category for a in articles if a.category))
        categories_dict = {}
        if category_ids:
            cat_result = await db.execute(
                select(Category).where(Category.id.in_(category_ids))
            )
            for cat in cat_result.scalars().all():
                categories_dict[cat.id] = cat.name

        articles_data = []
        for article in articles:
            # 使用模型的 to_dict() 方法获取基础数据
            article_dict = article.to_dict()

            # 确定文章状态（转换为字符串）
            article_status = 'draft'
            if article.status == 1:
                article_status = 'published'
            elif article.status == 0:
                article_status = 'draft'
            elif article.status == -1:
                article_status = 'deleted'

            # 处理标签（将 tags_list 字符串转换为数组，支持逗号和分号分隔符）
            tags_list = []
            if article_dict.get('tags_list'):
                if isinstance(article_dict['tags_list'], str):
                    tags_list = [t.strip() for t in re.split(r'[,;]', article_dict['tags_list']) if t.strip()]
                else:
                    tags_list = article_dict['tags_list']

            # 获取分类名称
            category_name = categories_dict.get(article.category, '')

            # 检查文章是否有密码保护
            has_password = False
            try:
                from sqlalchemy import select as sel
                from shared.models.article_content import ArticleContent
                content_query = sel(ArticleContent).where(ArticleContent.article == article.id)
                content_result = await db.execute(content_query)
                content = content_result.scalar_one_or_none()
                has_password = bool(content and content.passwd)
            except Exception as e:
                print(f"检查文章密码状态失败: {e}")

            articles_data.append({
                **article_dict,  # 展开模型的基础字段
                "summary": article_dict.get('excerpt', ''),  # 前端期望的字段名
                "tags": tags_list,  # 转换后的标签数组
                "status": article_status,  # 覆盖为字符串状态
                "has_password": has_password,  # 添加密码保护状态
                "category_id": article.category,  # 分类 ID
                "category_name": category_name,  # 分类名称
                "author": {
                    "id": article.user,
                    "username": "未知作者"  # 由于 author 关系已注释，暂时显示未知
                },
                "comments": 0  # 暂时设为 0，因为评论模型未定义
            })

        return ApiResponse(
            success=True,
            data=articles_data,
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
        return ApiResponse(success=False, error=str(e))


@router.get("/my/messages")
async def get_my_messages(
        request: Request,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取我的消息列表
    返回收件箱、已发送和通知三种类型的消息
    """
    try:
        from sqlalchemy import select

        # 获取用户的所有通知
        notifications_query = select(Notification).where(
            Notification.recipient_id == current_user.id
        ).order_by(desc(Notification.created_at))
        notifications_result = await db.execute(notifications_query)
        notifications = notifications_result.scalars().all()

        # 转换通知数据为前端期望的格式
        notification_list = []
        for notif in notifications:
            notification_list.append({
                "id": notif.id,
                "title": notif.title,
                "content": notif.message,
                "date": notif.created_at.isoformat(),
                "type": notif.type,
                "read": notif.is_read,
                "avatar": f"/avatars/{current_user.username}.jpg",  # 使用用户头像
                "sender": "System",  # 系统通知
                "recipient": current_user.username
            })

        return ApiResponse(
            success=True,
            data=notification_list
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/media-management/files")
async def get_media_management_files(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        file_type: Optional[str] = Query(None, alias="type"),
        sort_by: Optional[str] = Query("time", alias="sort"),
        sort_order: Optional[str] = Query("desc", alias="order"),
        q: Optional[str] = Query(None, alias="q"),
        current_user: User = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取媒体管理文件列表
    """
    try:
        from sqlalchemy import select, func

        # 基础查询：JOIN FileHash 获取媒体文件的类型和路径信息
        base_query = (
            select(Media, FileHash)
            .join(FileHash, Media.hash == FileHash.hash, isouter=True)
            .where(Media.user == current_user.id)
        )

        # 根据文件类型过滤
        if file_type:
            if file_type == 'images':
                base_query = base_query.where(FileHash.mime_type.like('image/%'))
            elif file_type == 'documents':
                base_query = base_query.where(FileHash.mime_type.in_([
                    'application/pdf', 'application/msword', 'application/vnd.ms-excel', 'application/vnd.ms-powerpoint'
                ]))
            elif file_type == 'videos':
                base_query = base_query.where(FileHash.mime_type.like('video/%'))

        # 搜索（按文件名模糊匹配）
        if q:
            base_query = base_query.where(Media.original_filename.ilike(f'%{q}%'))

        # 计算总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页查询
        offset = (page - 1) * per_page
        # 排序
        sort_column = Media.original_filename if sort_by == 'name' else Media.created_at
        order_fn = sort_column.asc if sort_order == 'asc' else sort_column.desc
        ordered_query = base_query.order_by(order_fn()).offset(offset).limit(per_page)
        result = await db.execute(ordered_query)
        rows = result.all()

        # 转换文件数据
        files_data = []
        for media, fh in rows:
            file_ext = media.original_filename.split('.')[-1].lower() if '.' in media.original_filename else ''
            mime_type = fh.mime_type if fh else ''
            storage_path = fh.storage_path if fh else ''
            file_size = fh.file_size if fh else 0

            ftype = 'document'
            if mime_type.startswith('image/'):
                ftype = 'image'
            elif mime_type.startswith('video/'):
                ftype = 'video'
            elif file_ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf']:
                ftype = 'document'
            elif file_ext in ['mp3', 'wav', 'ogg', 'flac']:
                ftype = 'audio'

            files_data.append({
                "id": media.id,
                "name": media.original_filename,
                "url": f"/media/{storage_path}/{media.original_filename}" if storage_path else '',
                "size": file_size,
                "upload_date": media.created_at.isoformat() if media.created_at else '',
                "type": ftype,
                "extension": file_ext,
                "mime_type": mime_type
            })

        # 构建 PaginationInfo 对象
        pages = (total + per_page - 1) // per_page if per_page > 0 else 1
        pagination_info = {
            "current_page": page,
            "total_pages": pages,
            "total": total,
            "has_prev": page > 1,
            "has_next": page < pages,
            "per_page": per_page,
        }

        return ApiResponse(
            success=True,
            data={
                "media_items": [{
                    "id": item["id"],
                    "original_filename": item["name"],
                    "hash": "",
                    "mime_type": item["mime_type"],
                    "file_size": item["size"],
                    "created_at": item["upload_date"]
                } for item in files_data],
                "users": [],
            },
            pagination=pagination_info
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/user-management/users")
async def get_users(
        request: Request,
        current_user: UserModel = Depends(get_current_active_user),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        search: Optional[str] = Query(None),
        db: AsyncSession = Depends(get_async_db)
):
    """获取所有用户信息（管理员专用）"""
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="权限不足")

        # 构建查询条件
        base_query = select(UserModel)
        if search:
            base_query = base_query.where(
                UserModel.username.contains(search) | UserModel.email.contains(search)
            )

        # 获取总数
        total_query = select(func.count()).select_from(UserModel)
        if search:
            total_query = total_query.where(
                UserModel.username.contains(search) | UserModel.email.contains(search)
            )
        total_result = await db.execute(total_query)
        total = total_result.scalar()

        # 获取分页数据
        offset = (page - 1) * per_page
        users_query = base_query.offset(offset).limit(per_page)
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()

        # 构建响应数据
        users_data = []
        for user in users:
            # 查询用户的角色
            from shared.models.user_role import UserRole
            from shared.models.role import Role
            import json

            roles_query = select(Role).join(
                UserRole, Role.id == UserRole.role_id
            ).where(
                UserRole.user_id == user.id
            )
            roles_result = await db.execute(roles_query)
            user_roles = roles_result.scalars().all()

            print(f"DEBUG: User {user.username} (ID: {user.id}) has {len(user_roles)} roles")

            # 构建角色数据
            roles_data = []
            for role in user_roles:
                # 解析权限列表
                try:
                    permissions_list = json.loads(role.permissions) if role.permissions else []
                except Exception as e:
                    print(f"DEBUG: Error parsing permissions for role {role.id}: {e}")
                    permissions_list = []

                print(f"DEBUG: Role {role.name} (ID: {role.id}) has permissions: {permissions_list}")

                roles_data.append({
                    "id": role.id,
                    "name": role.name,
                    "slug": role.slug,
                    "description": role.description or "",
                    "permissions": permissions_list  # 添加权限列表
                })

            print(f"DEBUG: User {user.username} roles_data: {roles_data}")

            # 这里可以添加计算用户存储使用量的逻辑
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "bio": user.bio,
                "profile_picture": user.profile_picture,
                "created_at": user.date_joined.isoformat() if user.date_joined else None,
                "last_login": getattr(user, 'last_login', None),
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "storage_used": 0,  # 占位符，实际应计算存储使用量
                "roles": roles_data  # 添加角色信息
            })

        return ApiResponse(
            success=True,
            data={
                "users": users_data,
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page,
                    "has_next": page < (total + per_page - 1) // per_page,
                    "has_prev": page > 1
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=f"获取用户列表失败: {str(e)}")


@router.get("/system-settings")
async def get_system_settings(
        request: Request,
        current_user: User = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取系统设置
    """
    try:
        # 返回系统设置数据
        # 注意：实际应用中这些设置通常存储在配置表中
        settings_data = {
            "general": {
                "site_name": "FastBlog",
                "site_description": "一个快速的博客系统",
                "site_url": "http://localhost:3000",
                "default_language": "zh-CN"
            },
            "security": {
                "max_login_attempts": 5,
                "session_timeout": 120,  # 分钟
                "enable_two_factor_auth": False
            },
            "email": {
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_username": "",
                "smtp_password": "",  # 实际应用中不会返回密码
                "from_email": "noreply@example.com"
            }
        }

        return ApiResponse(
            success=True,
            data=settings_data
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/system-settings")
async def update_system_settings(
        request: Request,
        current_user: User = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新系统设置
    """
    try:
        data = await request.json()
        # 在实际实现中，需要验证和保存设置到数据库
        # 这里只是示例，实际应用中应将设置保存到系统配置表中

        return ApiResponse(
            success=True,
            data={"message": "System settings updated successfully"}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/vip-management")
async def get_vip_management_data(
        request: Request,
        current_user: User = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取VIP管理数据 — 返回 stats / members / plans / features
    """
    try:
        from datetime import datetime, timedelta
        now = datetime.now()
        month_ago = now - timedelta(days=30)

        # 统计
        total_result = await db.execute(select(func.count(VIPSubscription.id)))
        total_count = total_result.scalar() or 0

        monthly_result = await db.execute(
            select(func.count(VIPSubscription.id)).where(VIPSubscription.created_at >= month_ago)
        )
        monthly_new = monthly_result.scalar() or 0

        # 查询所有订阅
        subscriptions_query = (
            select(VIPSubscription)
            .join(VIPPlan, VIPSubscription.plan == VIPPlan.id, isouter=True)
        )
        subscriptions_result = await db.execute(subscriptions_query)
        subscriptions = subscriptions_result.scalars().all()

        monthly_revenue = 0.0
        members_data = []
        for sub in subscriptions:
            amt = float(sub.payment_amount) if sub.payment_amount else 0.0
            if sub.created_at and sub.created_at >= month_ago:
                monthly_revenue += amt
            is_active = bool(sub.status == 1 and sub.expires_at and sub.expires_at > now)
            username = sub.user.username if sub.user else "Unknown"
            plan_name = sub.plan.name if sub.plan else "Unknown"
            level = sub.plan.level if sub.plan else 0
            members_data.append({
                "id": sub.id,
                "user_id": sub.user_id,
                "username": username,
                "plan_name": plan_name,
                "level": level,
                "starts_at": sub.starts_at.isoformat() if sub.starts_at else None,
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
                "is_active": is_active,
                "amount": amt,
                "transaction_id": sub.transaction_id,
                "status": "active" if sub.status == 1 else "inactive",
            })

        active_members = sum(1 for m in members_data if m['is_active'])
        renewal_rate = round(active_members / total_count * 100, 1) if total_count > 0 else 0

        # 所有计划
        plans_result = await db.execute(select(VIPPlan).order_by(VIPPlan.level))
        plans = plans_result.scalars().all()

        # 所有功能
        features_result = await db.execute(select(VIPFeature).order_by(VIPFeature.required_level))
        features = features_result.scalars().all()

        return ApiResponse(success=True, data={
            "stats": {
                "total_vip_count": total_count,
                "active_count": active_members,
                "monthly_new": monthly_new,
                "monthly_revenue": round(monthly_revenue, 2),
                "renewal_rate": renewal_rate,
            },
            "members": members_data,
            "plans": [p.to_dict() for p in plans],
            "features": [f.to_dict() for f in features],
        })
    except Exception as e:
        import traceback
        print(f"VIP management error: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.get("/blog-management/articles/stats")
async def get_blog_management_articles_stats(
        request: Request,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取博客管理文章统计信息
    """
    try:
        # 计算文章总数
        from sqlalchemy import select
        total_articles_query = select(func.count(Article.id))
        total_articles_result = await db.execute(total_articles_query)
        total_articles = total_articles_result.scalar()

        # 计算已发布文章数
        from sqlalchemy import select
        published_articles_query = select(func.count(Article.id)).where(Article.status == 1)
        published_articles_result = await db.execute(published_articles_query)
        published_articles = published_articles_result.scalar()

        # 计算草稿文章数
        from sqlalchemy import select
        draft_articles_query = select(func.count(Article.id)).where(Article.status == 0)
        draft_articles_result = await db.execute(draft_articles_query)
        draft_articles = draft_articles_result.scalar()

        # 计算总浏览量
        from sqlalchemy import select
        total_views_query = select(func.sum(Article.views))
        total_views_result = await db.execute(total_views_query)
        total_views = total_views_result.scalar() or 0

        stats_data = {
            "total_articles": total_articles,
            "published_articles": published_articles,
            "draft_articles": draft_articles,
            "total_views": total_views
        }

        return ApiResponse(
            success=True,
            data=stats_data
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/blog-management/articles/{article_id}")
async def delete_blog_management_article(
        request: Request,
        article_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除博客管理文章
    """
    try:
        from sqlalchemy import select, delete
        from shared.models.article_content import ArticleContent
        from shared.models.article_revision import ArticleRevision

        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        if not article:
            return ApiResponse(success=False, error="Article not found")

        # 检查权限 - 只有超级用户或文章作者可以删除
        if not current_user.is_superuser and article.user != current_user.id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Permission denied")

        # 级联删除评论投票（先于评论删除，避免孤立记录）
        from shared.models.comment import Comment
        from shared.models.comment_vote import CommentVote
        from shared.models.comment_subscription import CommentSubscription

        comment_ids_result = await db.execute(
            select(Comment.id).where(Comment.article_id == article_id)
        )
        comment_ids = [row[0] for row in comment_ids_result.all()]
        if comment_ids:
            await db.execute(
                delete(CommentVote).where(CommentVote.comment_id.in_(comment_ids))
            )

        # 级联删除评论订阅
        await db.execute(
            delete(CommentSubscription).where(CommentSubscription.article_id == article_id)
        )

        # 级联删除评论
        await db.execute(
            delete(Comment).where(Comment.article_id == article_id)
        )

        # 级联删除修订历史
        revisions_query = select(ArticleRevision).where(ArticleRevision.article_id == article_id)
        revisions_result = await db.execute(revisions_query)
        for revision in revisions_result.scalars().all():
            await db.delete(revision)

        # 级联删除内容
        content_query = select(ArticleContent).where(ArticleContent.article == article_id)
        content_result = await db.execute(content_query)
        for content in content_result.scalars().all():
            await db.delete(content)

        await db.delete(article)
        await db.commit()

        return ApiResponse(
            success=True,
            data={"message": "Article deleted successfully"}
        )
    except Exception as e:
        import traceback
        print(f"Error in delete_blog_management_article: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ====== VIP 计划管理 (Admin) ======

@router.post("/vip/plans")
async def admin_create_vip_plan(
    request: Request,
    current_user: User = Depends(admin_required_api),
    db: AsyncSession = Depends(get_async_db)
):
    """创建 VIP 套餐"""
    try:
        form = await request.form()
        plan = VIPPlan(
            name=form.get('name'),
            description=form.get('description', ''),
            price=float(form.get('price', 0)),
            original_price=float(form.get('original_price', 0)) if form.get('original_price') else None,
            duration_days=int(form.get('duration_days', 30)),
            level=int(form.get('level', 1)),
            features=form.get('features', '[]'),
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return ApiResponse(success=True, data=plan.to_dict())
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/vip/plans/{plan_id}")
async def admin_update_vip_plan(
    request: Request,
    plan_id: int,
    current_user: User = Depends(admin_required_api),
    db: AsyncSession = Depends(get_async_db)
):
    """更新 VIP 套餐"""
    try:
        result = await db.execute(select(VIPPlan).where(VIPPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            return ApiResponse(success=False, error="套餐不存在")

        form = await request.form()
        plan.name = form.get('name', plan.name)
        plan.description = form.get('description', plan.description)
        plan.price = float(form.get('price', plan.price))
        plan.original_price = float(form.get('original_price', plan.original_price)) if form.get('original_price') else plan.original_price
        plan.duration_days = int(form.get('duration_days', plan.duration_days))
        plan.level = int(form.get('level', plan.level))
        plan.features = form.get('features', plan.features)
        is_active = form.get('is_active')
        if is_active is not None:
            plan.is_active = is_active in ('1', 'true', 'True', True)
        await db.commit()
        await db.refresh(plan)
        return ApiResponse(success=True, data=plan.to_dict())
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/vip/plans/{plan_id}")
async def admin_delete_vip_plan(
    plan_id: int,
    current_user: User = Depends(admin_required_api),
    db: AsyncSession = Depends(get_async_db)
):
    """删除 VIP 套餐"""
    try:
        result = await db.execute(select(VIPPlan).where(VIPPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            return ApiResponse(success=False, error="套餐不存在")
        await db.delete(plan)
        await db.commit()
        return ApiResponse(success=True, data={"message": "已删除"})
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ====== VIP 功能管理 (Admin) ======

@router.post("/vip/features")
async def admin_create_vip_feature(
    request: Request,
    current_user: User = Depends(admin_required_api),
    db: AsyncSession = Depends(get_async_db)
):
    """创建 VIP 功能"""
    try:
        form = await request.form()
        feature = VIPFeature(
            code=form.get('code'),
            name=form.get('name'),
            description=form.get('description', ''),
            required_level=int(form.get('required_level', 1)),
        )
        db.add(feature)
        await db.commit()
        await db.refresh(feature)
        return ApiResponse(success=True, data=feature.to_dict())
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/vip/features/{feature_id}")
async def admin_update_vip_feature(
    request: Request,
    feature_id: int,
    current_user: User = Depends(admin_required_api),
    db: AsyncSession = Depends(get_async_db)
):
    """更新 VIP 功能"""
    try:
        result = await db.execute(select(VIPFeature).where(VIPFeature.id == feature_id))
        feature = result.scalar_one_or_none()
        if not feature:
            return ApiResponse(success=False, error="功能不存在")

        form = await request.form()
        feature.code = form.get('code', feature.code)
        feature.name = form.get('name', feature.name)
        feature.description = form.get('description', feature.description)
        feature.required_level = int(form.get('required_level', feature.required_level))
        is_active = form.get('is_active')
        if is_active is not None:
            feature.is_active = is_active in ('1', 'true', 'True', True)
        await db.commit()
        await db.refresh(feature)
        return ApiResponse(success=True, data=feature.to_dict())
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/vip/features/{feature_id}")
async def admin_delete_vip_feature(
    feature_id: int,
    current_user: User = Depends(admin_required_api),
    db: AsyncSession = Depends(get_async_db)
):
    """删除 VIP 功能"""
    try:
        result = await db.execute(select(VIPFeature).where(VIPFeature.id == feature_id))
        feature = result.scalar_one_or_none()
        if not feature:
            return ApiResponse(success=False, error="功能不存在")
        await db.delete(feature)
        await db.commit()
        return ApiResponse(success=True, data={"message": "已删除"})
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/admin/dashboard")
async def admin_dashboard(current_user: User = Depends(admin_required_api)):
    """
    管理员面板入口

    Returns:
        管理员面板信息
    """
    return {
        'success': True,
        'message': '管理员面板',
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'is_staff': getattr(current_user, 'is_staff', False),
            'is_superuser': getattr(current_user, 'is_superuser', False)
        }
    }
