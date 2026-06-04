"""
文章定时发布 API
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.articles.scheduled_publish import create_scheduled_publish_service
from src.utils.database.main import get_async_session

router = APIRouter(tags=["scheduled-publish"])


class ScheduleArticleRequest(BaseModel):
    """定时发布请求"""
    article_id: int
    publish_at: str  # ISO format datetime


@router.post("/schedule")
async def schedule_article(
        request: ScheduleArticleRequest,
        db: AsyncSession = Depends(get_async_session)
):
    """
    设置文章定时发布
    
    Args:
        request: 定时发布请求
        db: 数据库会话
        
    Returns:
        调度结果
    """
    try:
        # 解析发布时间
        publish_at = datetime.fromisoformat(request.publish_at)

        service = create_scheduled_publish_service(db)
        result = await service.schedule_article(
            article_id=request.article_id,
            publish_at=publish_at
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel/{article_id}")
async def cancel_scheduled_publish(
        article_id: int,
        db: AsyncSession = Depends(get_async_session)
):
    """
    取消文章定时发布
    
    Args:
        article_id: 文章ID
        db: 数据库会话
        
    Returns:
        取消结果
    """
    try:
        service = create_scheduled_publish_service(db)
        result = await service.cancel_scheduled_publish(article_id)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish-due")
async def publish_due_articles(
        db: AsyncSession = Depends(get_async_session)
):
    """
    发布所有到期的定时文章
    
    Args:
        db: 数据库会话
        
    Returns:
        发布结果统计
    """
    try:
        service = create_scheduled_publish_service(db)
        result = await service.publish_due_articles()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_scheduled_articles(
        limit: int = Query(50, ge=1, le=200, description="返回数量"),
        offset: int = Query(0, ge=0, description="偏移量"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取待发布的文章列表
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
        db: 数据库会话
        
    Returns:
        待发布文章列表
    """
    try:
        service = create_scheduled_publish_service(db)
        articles = await service.get_scheduled_articles(limit, offset)

        return {
            'success': True,
            'data': articles,
            'count': len(articles),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
async def get_upcoming_publishes(
        hours: int = Query(24, ge=1, le=168, description="小时数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取即将发布的文章
    
    Args:
        hours: 未来多少小时内
        db: 数据库会话
        
    Returns:
        即将发布的文章列表
    """
    try:
        service = create_scheduled_publish_service(db)
        articles = await service.get_upcoming_publishes(hours)

        return {
            'success': True,
            'data': articles,
            'count': len(articles),
            'hours': hours,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
