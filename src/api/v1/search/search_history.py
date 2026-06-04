"""
搜索历史 API
提供用户搜索历史的查询功能
"""


from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.search_history import SearchHistory
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

from src.unified_logger import default_logger as logger

router = APIRouter(tags=["search-history"])


@router.get('/history')
async def get_search_history(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取用户的搜索历史
    """
    try:
        # 获取当前用户的搜索历史，按时间倒序排列，最多返回 10 条
        query = select(SearchHistory).where(
            SearchHistory.user_id == current_user.id
        ).order_by(desc(SearchHistory.created_at)).limit(10)

        result = await db.execute(query)
        history_list = result.scalars().all()

        # 转换为字典列表
        history_data = [history.to_dict() for history in history_list]

        return {
            'success': True,
            'data': history_data
        }
    except Exception as e:
        logger.error(f"获取搜索历史失败：{str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@router.delete('/history')
async def clear_search_history(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    清除用户的所有搜索历史
    """
    try:
        # 删除当前用户的所有搜索历史
        query = SearchHistory.__table__.delete().where(
            SearchHistory.user_id == current_user.id
        )
        await db.execute(query)
        await db.commit()

        return {
            'success': True,
            'message': '搜索历史已清除'
        }
    except Exception as e:
        logger.error(f"清除搜索历史失败：{str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@router.delete('/history/{item_id}')
async def delete_search_history_item(
        item_id: int,
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除单条搜索历史记录
    
    Args:
        item_id: 搜索历史记录的 ID
    """
    try:
        # 查询并删除指定的搜索历史记录（确保只能删除自己的记录）
        query = select(SearchHistory).where(
            SearchHistory.id == item_id,
            SearchHistory.user_id == current_user.id
        )
        result = await db.execute(query)
        history_item = result.scalar_one_or_none()

        if not history_item:
            return {
                'success': False,
                'error': '搜索历史记录不存在或无权删除'
            }

        await db.delete(history_item)
        await db.commit()

        return {
            'success': True,
            'message': '搜索历史记录已删除'
        }
    except Exception as e:
        logger.error(f"删除搜索历史记录失败：{str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
