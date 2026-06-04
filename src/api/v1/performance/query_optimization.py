"""
查询优化 API

提供查询分析、性能监控和优化建议功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.performance.query_monitor import query_monitor_service
from shared.services.performance.query_optimizer import query_optimizer
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/analysis", summary="查询分析", description="分析最近的数据库查询，检测性能问题")
async def analyze_queries(
        limit: int = Query(100, ge=1, le=1000, description="分析的查询数量"),
        current_user=Depends(jwt_required),
):
    """
    分析数据库查询
    
    检测N+1问题、慢查询和其他性能问题
    """
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 获取最近的查询日志
    recent_queries = query_monitor_service.queries[-limit:]

    if not recent_queries:
        return ApiResponse(
            success=True,
            data={
                'message': 'No queries to analyze',
                'total_queries': 0,
            }
        )

    # 分析查询
    analysis = query_optimizer.analyze_queries(recent_queries)

    return ApiResponse(
        success=True,
        data=analysis
    )


@router.get("/monitor/stats", summary="查询监控统计", description="获取查询监控的统计信息")
async def get_query_stats(
        current_user=Depends(jwt_required),
):
    """获取查询监控统计"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    stats = query_monitor_service.get_summary()

    return ApiResponse(
        success=True,
        data=stats
    )


@router.post("/optimize/article-query", summary="优化文章查询", description="使用优化的方式查询文章列表")
async def optimize_article_query(
        page: int = Body(1, ge=1, description="页码"),
        per_page: int = Body(10, ge=1, le=100, description="每页数量"),
        category_id: Optional[int] = Body(None, description="分类ID"),
        status: Optional[int] = Body(None, description="状态"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(lambda: None),  # 需要实际的session依赖
):
    """
    优化的文章查询示例
    
    演示如何使用预加载避免N+1问题
    """
    try:
        from shared.models.article import Article

        # 构建过滤条件
        filters = {}
        if category_id is not None:
            filters['category'] = category_id
        if status is not None:
            filters['status'] = status

        # 执行优化查询
        articles, total = await query_optimizer.optimize_article_query(
            db=db,
            page=page,
            per_page=per_page,
            **filters
        )

        # 序列化结果
        articles_data = []
        for article in articles:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'excerpt': article.excerpt,
                'author': {
                    'id': article.author.id if article.author else None,
                    'username': article.author.username if article.author else None,
                } if hasattr(article, 'author') else None,
                'category': {
                    'id': article.category.id if article.category else None,
                    'name': article.category.name if article.category else None,
                } if hasattr(article, 'category') else None,
                'created_at': article.created_at.isoformat() if article.created_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                'articles': articles_data,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': (total + per_page - 1) // per_page if per_page > 0 else 0,
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query optimization failed: {str(e)}")


@router.get("/recommendations", summary="优化建议", description="获取数据库优化建议")
async def get_optimization_recommendations(
        current_user=Depends(jwt_required),
):
    """获取数据库优化建议"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    recommendations = [
        {
            'type': 'index',
            'priority': 'high',
            'title': '添加索引',
            'description': '为频繁查询的字段添加索引',
            'suggestions': [
                '为 articles.status 字段添加索引',
                '为 articles.category_id 字段添加索引',
                '为 articles.created_at 字段添加索引',
                '为 user_activities.user_id 字段添加索引',
            ]
        },
        {
            'type': 'eager_loading',
            'priority': 'high',
            'title': '使用预加载',
            'description': '使用joinedload或selectinload避免N+1查询',
            'example': '''
# 外键关联
query = select(Article).options(joinedload(Article.author))

# 一对多关联
query = select(Category).options(selectinload(Category.articles))
            '''.strip()
        },
        {
            'type': 'caching',
            'priority': 'medium',
            'title': '使用缓存',
            'description': '对频繁访问的数据使用多级缓存',
            'suggestions': [
                '缓存热门文章列表',
                '缓存分类信息',
                '缓存用户权限数据',
                '使用Redis作为L2缓存',
            ]
        },
        {
            'type': 'batch_operations',
            'priority': 'medium',
            'title': '批量操作',
            'description': '使用批量查询和更新减少数据库往返',
            'example': '''
# 批量查询
ids = [1, 2, 3, 4, 5]
result = await db.execute(
    select(User).where(User.id.in_(ids))
)

# 批量更新
await db.execute(
    update(Article)
    .where(Article.id.in_(article_ids))
    .values(status=1)
)
            '''.strip()
        },
        {
            'type': 'pagination',
            'priority': 'low',
            'title': '优化分页',
            'description': '对于大数据集使用游标分页替代偏移量分页',
            'suggestion': '当数据量超过10万条时，考虑使用基于ID或时间戳的游标分页'
        },
    ]

    return ApiResponse(
        success=True,
        data=recommendations
    )


@router.post("/reset-monitor", summary="重置监控", description="重置查询监控数据")
async def reset_query_monitor(
        current_user=Depends(jwt_required),
):
    """重置查询监控"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    query_monitor_service.queries.clear()

    return ApiResponse(
        success=True,
        message="Query monitor reset successfully"
    )
