"""
分类管理API - 处理分类的创建、更新和删除
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.category import Category
from shared.models.category_subscription import CategorySubscription
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(tags=["category-management"])


@router.post("/")
async def create_category_api(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    创建分类API
    """
    try:
        # 检查用户权限 - 只有超级用户才能创建分类
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        form_data = await request.json()
        name = form_data.get('name')
        description = form_data.get('description', '')

        if not name:
            return ApiResponse(success=False, error='分类名称不能为空', data=None)

        # 检查分类名称是否已存在
        existing_category_result = await db.execute(select(Category).filter_by(name=name))
        existing_category = existing_category_result.scalar_one_or_none()
        if existing_category:
            return ApiResponse(success=False, error='分类名称已存在', data=None)

        # 创建新分类
        category = Category(
            name=name,
            description=description
        )

        db.add(category)
        await db.commit()
        await db.refresh(category)

        return ApiResponse(
            success=True,
            data={
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'created_at': category.created_at.isoformat() if category.created_at else None,
                'updated_at': category.updated_at.isoformat() if category.updated_at else None
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in create_category_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.put("/{category_id}")
async def update_category_api(
        category_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    更新分类API
    """
    try:
        # 检查用户权限 - 只有超级用户才能更新分类
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        category_result = await db.execute(select(Category).filter_by(id=category_id))
        category = category_result.scalar_one_or_none()
        if not category:
            return ApiResponse(success=False, error="分类不存在", data=None)

        form_data = await request.json()
        name = form_data.get('name')
        description = form_data.get('description', '')

        if not name:
            return ApiResponse(success=False, error='分类名称不能为空', data=None)

        # 检查新名称是否与其他分类冲突
        existing_category_result = await db.execute(
            select(Category).filter_by(name=name).filter(Category.id != category_id))
        existing_category = existing_category_result.scalar_one_or_none()
        if existing_category:
            return ApiResponse(success=False, error='分类名称已存在', data=None)

        # 更新分类
        category.name = name
        category.description = description

        await db.commit()
        await db.refresh(category)

        return ApiResponse(
            success=True,
            data={
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'created_at': category.created_at.isoformat() if category.created_at else None,
                'updated_at': category.updated_at.isoformat() if category.updated_at else None
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in update_category_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("")
async def get_categories_with_stats_api(
        current_user=Depends(jwt_required),
        page: int = 1,
        per_page: int = 10,
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取分类列表及统计信息API
    """
    try:
        # 检查用户权限 - 只有超级用户才能访问
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        # 计算偏移量
        offset = (page - 1) * per_page

        # 查询分类及其关联的统计信息
        category_stats_query = (
            select(
                Category,
                func.coalesce(func.count(func.distinct(Article.id)), 0).label('article_count'),
                func.coalesce(func.count(func.distinct(CategorySubscription.id)), 0).label('subscriber_count')
            )
            .select_from(
                Category.__table__.outerjoin(Article.__table__, Category.id == Article.category)
                .outerjoin(CategorySubscription.__table__, Category.id == CategorySubscription.category)
            )
            .group_by(Category.id)
            .order_by(Category.sort_order.asc(), Category.name.asc())
        )
        category_stats = await db.execute(category_stats_query)

        # 获取总数
        total_categories_query = await db.execute(select(func.count()).select_from(Category))
        total_categories = total_categories_query.scalar()

        # 应用分页
        categories_with_stats_query = category_stats_query.offset(offset).limit(per_page)
        categories_with_stats_result = await db.execute(categories_with_stats_query)
        categories_with_stats = categories_with_stats_result.all()

        # 构建返回数据
        categories_data = []
        for item in categories_with_stats:
            category = item[0]
            article_count = item[1]
            subscriber_count = item[2]

            categories_data.append({
                "category": {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'created_at': category.created_at.isoformat() if category.created_at else None,
                    'updated_at': category.updated_at.isoformat() if category.updated_at else None
                },
                "article_count": article_count,
                "subscriber_count": subscriber_count
            })

        return ApiResponse(
            success=True,
            data={
                "categories": categories_data,
                "pagination": {
                    "current_page": page,
                    "pages": (total_categories + per_page - 1) // per_page,
                    "total": total_categories,
                    "has_next": page < (total_categories + per_page - 1) // per_page,
                    "has_prev": page > 1,
                    "per_page": per_page
                }
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_categories_with_stats_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/{category_id}")
async def delete_category_api(
        category_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    删除分类API
    """
    try:
        # 检查用户权限 - 只有超级用户才能删除分类
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        category_result = await db.execute(select(Category).filter_by(id=category_id))
        category = category_result.scalar_one_or_none()
        if not category:
            return ApiResponse(success=False, error="分类不存在", data=None)

        # 检查是否有文章属于这个分类
        articles_count_query = await db.execute(
            select(func.count()).select_from(Article).filter_by(category=category_id))
        articles_count = articles_count_query.scalar()
        if articles_count > 0:
            return ApiResponse(success=False, error="无法删除：该分类下还有文章", data=None)

        # 删除分类
        await db.delete(category)
        await db.commit()

        return ApiResponse(
            success=True,
            data={'message': '分类删除成功'}
        )
    except Exception as e:
        import traceback
        print(f"Error in delete_category_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


# ---------- 分类拖拽排序 ----------
@router.post("/reorder")
async def reorder_categories_api(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    分类拖拽排序
    
    请求体格式：
    {
        "categories": [
            {"id": 1, "sort_order": 0},
            {"id": 2, "sort_order": 1},
            ...
        ]
    }
    """
    try:
        # 检查用户权限 - 只有超级用户才能排序分类
        if not current_user.is_superuser:
            from fastapi import HTTPException
            from fastapi import status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        body = await request.json()
        categories_data = body.get('categories', [])

        if not categories_data:
            return ApiResponse(success=False, error="缺少分类数据")

        # 提取分类ID列表
        category_ids = [item['id'] for item in categories_data]

        # 查询所有分类
        query = select(Category).where(Category.id.in_(category_ids))
        result = await db.execute(query)
        categories = {category.id: category for category in result.scalars().all()}

        # 更新排序
        updated_count = 0
        for item in categories_data:
            category_id = item['id']
            new_sort_order = item.get('sort_order', 0)

            if category_id in categories:
                categories[category_id].sort_order = new_sort_order
                updated_count += 1

        await db.commit()

        return ApiResponse(
            success=True,
            data={
                "message": "分类排序更新成功",
                "updated_count": updated_count
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in reorder_categories_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))
