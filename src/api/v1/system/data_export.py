"""
数据导出 API
提供CSV、Excel等格式的数据导出功能
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.services.system.data_export_service import data_export_service
from src.api.v1.core.responses import ApiResponse
from src.utils.database.main import get_async_session

from shared.models.user import User as UserModel
from src.auth.auth_deps import admin_required as admin_required_api

router = APIRouter(tags=["export"])
logger = logging.getLogger(__name__)


@router.get("/users", summary="导出用户列表")
async def export_users(
        format: str = Query('csv', enum=['csv', 'excel'], description="导出格式"),
        limit: int = Query(1000, ge=1, le=10000, description="导出数量"),
        current_user: UserModel = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_session)
):
    """
    导出用户列表为CSV或Excel文件
    
    Args:
        format: 导出格式(csv/excel)
        limit: 导出数量(1-10000)
        
    Returns:
        文件下载
    """
    try:
        from shared.models.user import User
        
        stmt = select(User).limit(limit)
        result = await db.execute(stmt)
        users_db = result.scalars().all()
        
        users = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': getattr(user, 'phone', ''),
            'is_active': user.is_active,
            'is_verified': getattr(user, 'is_verified', False),
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else '',
            'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else '',
        } for user in users_db]

        # 导出数据
        if format == 'excel':
            file_bytes = data_export_service.export_user_list(users, format='excel')
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'users.xlsx'
        else:
            file_bytes = data_export_service.export_user_list(users, format='csv')
            media_type = 'text/csv'
            filename = 'users.csv'

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
            }
        )

    except Exception as e:
        logger.error(f"导出用户列表失败: {str(e)}")
        return ApiResponse(success=False, error=f"导出失败: {str(e)}")


@router.get("/articles", summary="导出文章列表")
async def export_articles(
        format: str = Query('csv', enum=['csv', 'excel'], description="导出格式"),
        status: Optional[str] = Query(None, description="文章状态过滤"),
        limit: int = Query(1000, ge=1, le=10000, description="导出数量"),
        current_user: UserModel = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_session)
):
    """
    导出文章列表为CSV或Excel文件
    
    Args:
        format: 导出格式(csv/excel)
        status: 文章状态过滤(published/draft/archived)
        limit: 导出数量(1-10000)
        
    Returns:
        文件下载
    """
    try:
        from shared.models.article import Article
        
        stmt = select(Article).limit(limit)
        if status:
            stmt = stmt.where(Article.status == status)
        result = await db.execute(stmt)
        articles_db = result.scalars().all()
        
        articles = [{
            'id': article.id,
            'title': article.title,
            'author_id': getattr(article, 'user_id', ''),
            'category_id': getattr(article, 'category_id', ''),
            'status': getattr(article, 'status', ''),
            'view_count': getattr(article, 'view_count', 0),
            'created_at': article.created_at.isoformat() if hasattr(article, 'created_at') and article.created_at else '',
            'updated_at': article.updated_at.isoformat() if hasattr(article, 'updated_at') and article.updated_at else '',
        } for article in articles_db]

        # 导出数据
        if format == 'excel':
            file_bytes = data_export_service.export_articles(articles, format='excel')
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'articles.xlsx'
        else:
            file_bytes = data_export_service.export_articles(articles, format='csv')
            media_type = 'text/csv'
            filename = 'articles.csv'

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
            }
        )

    except Exception as e:
        logger.error(f"导出文章列表失败: {str(e)}")
        return ApiResponse(success=False, error=f"导出失败: {str(e)}")


@router.get("/comments", summary="导出评论列表")
async def export_comments(
        format: str = Query('csv', enum=['csv', 'excel'], description="导出格式"),
        article_id: Optional[int] = Query(None, description="文章ID过滤"),
        limit: int = Query(1000, ge=1, le=10000, description="导出数量"),
        current_user: UserModel = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_session)
):
    """
    导出评论列表为CSV或Excel文件
    
    Args:
        format: 导出格式(csv/excel)
        article_id: 文章ID过滤
        limit: 导出数量(1-10000)
        
    Returns:
        文件下载
    """
    try:
        from shared.models.article import Article as ArticleModel
        
        stmt = select(ArticleModel).limit(limit)
        if article_id:
            stmt = stmt.where(ArticleModel.id == article_id)
        result = await db.execute(stmt)
        comments_db = result.scalars().all()
        
        comments = [{
            'id': comment.id,
            'article_id': getattr(comment, 'article_id', ''),
            'user_id': getattr(comment, 'user_id', ''),
            'content': getattr(comment, 'content', ''),
            'created_at': comment.created_at.isoformat() if hasattr(comment, 'created_at') and comment.created_at else '',
        } for comment in comments_db]

        # 导出数据
        if format == 'excel':
            file_bytes = data_export_service.export_comments(comments, format='excel')
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'comments.xlsx'
        else:
            file_bytes = data_export_service.export_comments(comments, format='csv')
            media_type = 'text/csv'
            filename = 'comments.csv'

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
            }
        )

    except Exception as e:
        logger.error(f"导出评论列表失败: {str(e)}")
        return ApiResponse(success=False, error=f"导出失败: {str(e)}")


@router.get("/analytics", summary="导出分析数据")
async def export_analytics(
        format: str = Query('csv', enum=['csv', 'excel'], description="导出格式"),
        report_type: str = Query('visits', enum=['visits', 'users', 'articles'], description="报表类型"),
        start_date: Optional[str] = Query(None, description="开始日期(YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="结束日期(YYYY-MM-DD)"),
        current_user: UserModel = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_session)
):
    """
    导出分析数据报表
    
    Args:
        format: 导出格式(csv/excel)
        report_type: 报表类型(visits/users/articles)
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        文件下载
    """
    try:
        from datetime import datetime
        from shared.models.article import Article
        
        stmt = select(Article).limit(1000)
        if start_date and hasattr(Article, 'created_at'):
            stmt = stmt.where(Article.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date and hasattr(Article, 'created_at'):
            stmt = stmt.where(Article.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
        result = await db.execute(stmt)
        data_rows = result.scalars().all()
        
        analytics_data = [{
            'id': row.id,
            'title': getattr(row, 'title', ''),
            'created_at': row.created_at.isoformat() if hasattr(row, 'created_at') and row.created_at else '',
        } for row in data_rows]

        sheet_name = f'{report_type.title()} Report'

        # 导出数据
        if format == 'excel':
            file_bytes = data_export_service.export_analytics(
                analytics_data,
                format='excel',
                sheet_name=sheet_name
            )
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'{report_type}_report.xlsx'
        else:
            file_bytes = data_export_service.export_analytics(
                analytics_data,
                format='csv'
            )
            media_type = 'text/csv'
            filename = f'{report_type}_report.csv'

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
            }
        )

    except Exception as e:
        logger.error(f"导出分析数据失败: {str(e)}")
        return ApiResponse(success=False, error=f"导出失败: {str(e)}")


@router.get("/templates", summary="获取导出模板")
async def get_export_templates(
        current_user: UserModel = Depends(admin_required_api)
):
    """
    获取可用的导出模板和字段
    
    Returns:
        模板列表
    """
    try:
        templates = data_export_service.get_export_templates()

        return ApiResponse(
            success=True,
            data={
                'templates': templates,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取模板失败: {str(e)}")


@router.post("/custom", summary="自定义数据导出")
async def export_custom_data(
        data_type: str = Query(..., description="数据类型"),
        format: str = Query('csv', enum=['csv', 'excel'], description="导出格式"),
        fields: list = Query(..., description="导出字段列表"),
        filters: dict = None,
        current_user: UserModel = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_session)
):
    """
    自定义数据导出
    
    Args:
        data_type: 数据类型(users/articles/comments/analytics)
        format: 导出格式(csv/excel)
        fields: 导出字段列表
        filters: 过滤条件
        
    Returns:
        文件下载
    """
    try:
        if data_type == 'users':
            from shared.models.user import User
            stmt = select(User)
            result = await db.execute(stmt.limit(1000))
            data = [{k: v for k, v in row.__dict__.items() if k in fields and not k.startswith('_')} for row in result.scalars().all()]
        elif data_type == 'articles':
            from shared.models.article import Article
            stmt = select(Article)
            result = await db.execute(stmt.limit(1000))
            data = [{k: v for k, v in row.__dict__.items() if k in fields and not k.startswith('_')} for row in result.scalars().all()]
        else:
            data = [{field: f'{field}_sample' for field in fields}]

        # 导出数据
        if format == 'excel':
            file_bytes = data_export_service.export_to_excel(
                data,
                sheet_name=data_type.title()
            )
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'{data_type}_export.xlsx'
        else:
            file_bytes = data_export_service.export_to_csv(data)
            media_type = 'text/csv'
            filename = f'{data_type}_export.csv'

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
            }
        )

    except Exception as e:
        logger.error(f"自定义导出失败: {str(e)}")
        return ApiResponse(success=False, error=f"导出失败: {str(e)}")
