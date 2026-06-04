"""
分类扩展 API - 处理分类相关的高级功能
"""
import re

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import CategorySubscription
from shared.models.article import Article
from shared.models.category import Category
from src.api.v1.core.responses import ApiResponse
from src.api.v1.utils.article_utils import get_articles_with_filters
from src.auth import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(tags=["category"])


# 定义特定路径的路由，确保它们在动态路由之前注册
@router.get("/all")
async def get_all_categories_api(
        request: Request,
        current_user=None,  # 移除强制认证依赖
        page: int = Query(1, ge=1),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取所有分类API
    """
    try:
        per_page = 12

        # 计算偏移量
        offset = (page - 1) * per_page

        # 获取所有分类
        categories_query = select(Category).order_by(Category.name.asc())
        categories_result = await db.execute(categories_query.offset(offset).limit(per_page))
        categories = categories_result.scalars().all()

        total_categories_result = await db.execute(select(Category).select_from(Category))
        total_categories = len(total_categories_result.scalars().all())

        # 如果用户已登录，获取其订阅的分类ID
        subscribed_ids = []
        if current_user:
            # 检查current_user是否是有效的用户对象
            try:
                # 尝试获取用户ID来验证用户是否有效
                user_id = getattr(current_user, 'id', None)
                if user_id:
                    subscriptions_query = select(CategorySubscription).filter_by(subscriber=user_id)
                    subscriptions_result = await db.execute(subscriptions_query)
                    subscriptions = subscriptions_result.scalars().all()
                    subscribed_ids = [sub.category for sub in subscriptions]
            except Exception:
                # 如果获取用户ID失败，说明用户未登录，保持空列表
                subscribed_ids = []

        return ApiResponse(
            success=True,
            data={
                "categories": [{
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                } for category in categories],
                "subscribed_ids": subscribed_ids,
                "total_categories": total_categories,
                "page": page,
                "per_page": per_page
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_all_categories_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/public")  # 添加一个完全公开的分类API
async def get_public_categories_api(
        request: Request,
        page: int = Query(1, ge=1),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取所有公开分类API，无需认证
    """
    try:
        per_page = 12

        # 计算偏移量
        offset = (page - 1) * per_page

        # 获取所有分类
        categories_query = select(Category).order_by(Category.name.asc())
        categories_result = await db.execute(categories_query.offset(offset).limit(per_page))
        categories = categories_result.scalars().all()

        total_categories_result = await db.execute(select(Category).select_from(Category))
        total_categories = len(total_categories_result.scalars().all())

        return ApiResponse(
            success=True,
            data={
                "categories": [{
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                } for category in categories],
                "subscribed_ids": [],  # 对于未登录用户，没有订阅ID
                "total_categories": total_categories,
                "page": page,
                "per_page": per_page
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_public_categories_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


# 动态路由放在最后，使用正则表达式约束，避免匹配特定路径
@router.get("/{name}")
async def get_category_by_name_api(
        name: str,
        request: Request,
        current_user=None,  # 移除强制认证依赖，改为可选
        page: int = Query(1, ge=1),
        db: AsyncSession = Depends(get_async_session)
):
    """
    根据分类名称获取分类文章API
    """
    # 检查名称是否为预定义的路径，如果是则返回404
    if name in ['all', 'public', 'subscribe', 'unsubscribe']:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")

    try:
        # 检查分类名称的长度
        if len(name) > 50:
            return ApiResponse(success=False, error="Category name too long", data=None)

        # 检查分类名称的合法性，例如只允许中文字符、字母、数字、连字符和下划线
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_-]+$', name):
            return ApiResponse(success=False, error="Invalid category name", data=None)

        page_size = 45

        # 首先通过name从categories表中获取对应的id
        category_result = await db.execute(select(Category).filter_by(name=name))
        category = category_result.scalar_one_or_none()
        if not category:
            return ApiResponse(success=False, error="Category not found", data=None)

        # 使用获取到的id来过滤Article
        article_info, total_articles = await get_articles_with_filters([Article.category == category.id], db, page,
                                                                       page_size)

        # 准备分页数据
        pagination_data = {
            'current_page': page,
            'total_pages': (total_articles + page_size - 1) // page_size,
            'has_prev': page > 1,
            'has_next': page < (total_articles + page_size - 1) // page_size,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < (total_articles + page_size - 1) // page_size else None,
        }

        # 处理文章数据
        articles = [{
            'article_id': article[0],
            'title': article[1],
            'user_id': article[2],
            'views': article[3],
            'likes': article[4],
            'cover_image': article[5],
            'category_id': article[6],
            'excerpt': article[7],
            'is_featured': article[8],
            'tags': article[9].split(',') if article[9] else [],
            'slug': article[10],
            'updated_at': article[11].isoformat() if hasattr(article[11], 'isoformat') else str(article[11])
        } for article in article_info]

        # 获取用户的订阅ID列表
        subscribed_ids = []
        if current_user:
            # 检查current_user是否是有效的用户对象
            try:
                # 尝试获取用户ID来验证用户是否有效
                user_id = getattr(current_user, 'id', None)
                if user_id:
                    subscriptions_query = select(CategorySubscription).filter_by(subscriber=user_id)
                    subscriptions_result = await db.execute(subscriptions_query)
                    subscriptions = subscriptions_result.scalars().all()
                    subscribed_ids = [sub.category for sub in subscriptions]
            except Exception:
                # 如果获取用户ID失败，说明用户未登录，保持空列表
                subscribed_ids = []

        # 返回JSON数据
        return ApiResponse(
            success=True,
            data={
                'articles': articles,
                'pagination': pagination_data,
                'total_articles': total_articles,
                'description': f'{name}分类页面，这里有与{name}相关的技术文章和生活分享。当前第{page}页，共{pagination_data["total_pages"]}页。',
                'keywords': f'{name},分类,博客,技术,文章',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                },
                'subscribed_ids': subscribed_ids  # 添加订阅状态
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_category_by_name_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/")  # 获取所有分类的根路径
async def get_all_categories_root_api(
        request: Request,
        current_user=None,  # 移除强制认证依赖
        page: int = Query(1, ge=1),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取所有分类API（根路径版本）
    """
    try:
        per_page = 12

        # 计算偏移量
        offset = (page - 1) * per_page

        # 获取所有分类
        categories_query = select(Category).order_by(Category.name.asc())
        categories_result = await db.execute(categories_query.offset(offset).limit(per_page))
        categories = categories_result.scalars().all()

        total_categories_result = await db.execute(select(Category).select_from(Category))
        total_categories = len(total_categories_result.scalars().all())

        # 如果用户已登录，获取其订阅的分类ID
        subscribed_ids = []
        if current_user:
            # 检查current_user是否是有效的用户对象
            try:
                # 尝试获取用户ID来验证用户是否有效
                user_id = getattr(current_user, 'id', None)
                if user_id:
                    subscriptions_query = select(CategorySubscription).filter_by(subscriber=user_id)
                    subscriptions_result = await db.execute(subscriptions_query)
                    subscriptions = subscriptions_result.scalars().all()
                    subscribed_ids = [sub.category for sub in subscriptions]
            except Exception:
                # 如果获取用户ID失败，说明用户未登录，保持空列表
                subscribed_ids = []

        return ApiResponse(
            success=True,
            data={
                "categories": [{
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                } for category in categories],
                "subscribed_ids": subscribed_ids,
                "total_categories": total_categories,
                "page": page,
                "per_page": per_page
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_all_categories_root_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/subscribe")
async def subscribe_category_api(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    订阅分类API
    """
    try:
        # 尝试解析JSON数据，如果失败则尝试表单数据
        try:
            json_data = await request.json()
            category_id = int(json_data.get('category_id', 0))
        except Exception:
            # 如果JSON解析失败，则尝试表单数据
            form_data = await request.form()
            category_id = int(form_data.get('category_id', 0))

        if not category_id:
            return ApiResponse(success=False, error='分类ID不能为空', data=None)

        category_result = await db.execute(select(Category).filter_by(id=category_id))
        category = category_result.scalar_one_or_none()
        if not category:
            return ApiResponse(success=False, error="分类不存在", data=None)

        # 检查是否已经订阅
        existing_subscription_query = select(CategorySubscription).filter_by(
            subscriber_id=current_user.id,
            category_id=category_id
        )
        existing_subscription_result = await db.execute(existing_subscription_query)
        existing_subscription = existing_subscription_result.scalar_one_or_none()

        if existing_subscription:
            return ApiResponse(success=False, error='您已经订阅了该分类', data=None)

        # 创建新订阅
        subscription = CategorySubscription(
            subscriber_id=current_user.id,
            category_id=category_id
        )

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        return ApiResponse(
            success=True,
            data={
                'message': f'成功订阅分类: {category.name}'
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in subscribe_category_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/unsubscribe")
async def unsubscribe_category_api(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    取消订阅分类API
    """
    try:
        # 尝试解析JSON数据，如果失败则尝试表单数据
        try:
            json_data = await request.json()
            category_id = int(json_data.get('category_id', 0))
        except Exception:
            # 如果JSON解析失败，则尝试表单数据
            form_data = await request.form()
            category_id = int(form_data.get('category_id', 0))

        if not category_id:
            return ApiResponse(success=False, error='分类ID不能为空', data=None)

        subscription_query = select(CategorySubscription).filter_by(
            subscriber=current_user.id,
            category=category_id
        )
        subscription_result = await db.execute(subscription_query)
        subscription = subscription_result.scalar_one_or_none()

        if not subscription:
            return ApiResponse(success=False, error='您未订阅该分类', data=None)

        await db.delete(subscription)
        await db.commit()

        return ApiResponse(
            success=True,
            data={
                'message': '取消订阅成功'
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in unsubscribe_category_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
