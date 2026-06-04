"""
移动端分类API
提供适合移动端的分类相关接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.category import Category
from src.api.v1.core.responses import ApiResponse
from src.utils.database.main import get_async_session

router = APIRouter(tags=["mobile-categories"])


@router.get("/list")
async def get_mobile_categories(
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取分类列表（移动端）
    """
    try:
        query = select(Category).order_by(Category.name)
        result = await db.execute(query)
        categories = result.scalars().all()

        categories_data = [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "slug": c.slug,
                "parent_id": c.parent
            }
            for c in categories
        ]

        return ApiResponse(
            success=True,
            data={"categories": categories_data}
        )
    except Exception as e:
        import traceback
        print(f"Error in get_mobile_categories: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))
