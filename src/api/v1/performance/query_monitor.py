"""
数据库查询监控API
提供查询分析、性能统计等调试功能
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.services.performance.query_monitor import query_monitor_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api
from src.extensions import get_async_db_session as get_async_db

router = APIRouter()


@router.get("/summary",
            summary="查询摘要",
            description="获取数据库查询的摘要统计(仅管理员)",
            response_description="返回查询摘要")
async def query_summary_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    查询摘要API
    """
    try:
        summary = query_monitor_service.get_summary()
        
        return ApiResponse(
            success=True,
            data=summary
        )
    except Exception as e:
        import traceback
        print(f"Error in query_summary_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/analysis",
            summary="查询分析",
            description="获取详细的查询分析报告(仅管理员)",
            response_description="返回查询分析")
async def query_analysis_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    查询分析API
    """
    try:
        # 注意: 由于FastAPI的异步特性,这里返回的是累积的统计数据
        # 实际使用中需要在请求开始时调用start_recording(),结束时调用stop_recording()
        
        return ApiResponse(
            success=True,
            data={
                'message': '查询监控已启用',
                'note': '详细查询记录需要在中间件层面实现',
                'tip': '查看响应头 X-Query-Count 和 X-Request-Time 获取当前请求的查询信息',
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in query_analysis_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/test-query",
             summary="测试查询",
             description="执行测试查询以验证监控功能(仅管理员)",
             response_description="返回测试结果")
async def test_query_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    测试查询API - 用于演示查询监控功能
    """
    try:
        import time
        from sqlalchemy import select, text
        
        # 开始记录
        query_monitor_service.start_recording()
        
        # 执行一些测试查询
        start = time.time()
        
        # 查询1: 简单查询
        result = await db.execute(text("SELECT 1"))
        duration = time.time() - start
        query_monitor_service.record_query("SELECT 1", duration, "test_query_api")
        
        # 查询2: 模拟慢查询
        start = time.time()
        await db.execute(text("SELECT pg_sleep(0.15)"))  # PostgreSQL休眠150ms
        duration = time.time() - start
        query_monitor_service.record_query("SELECT pg_sleep(0.15)", duration, "test_query_api")
        
        # 查询3: 重复查询模式
        for i in range(6):
            start = time.time()
            result = await db.execute(text(f"SELECT {i}"))
            duration = time.time() - start
            query_monitor_service.record_query(f"SELECT {i}", duration, "test_query_api")
        
        # 停止记录并获取分析
        analysis = query_monitor_service.stop_recording()
        
        return ApiResponse(
            success=True,
            data={
                'message': '测试查询完成',
                'analysis': analysis,
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in test_query_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/recommendations",
            summary="优化建议",
            description="获取数据库优化建议(仅管理员)",
            response_description="返回优化建议")
async def optimization_recommendations_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    优化建议API
    """
    try:
        recommendations = []
        
        # 检查索引使用情况
        try:
            from sqlalchemy import text
            result = await db.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_scan ASC
                LIMIT 10
            """))
            
            unused_indexes = result.fetchall()
            if unused_indexes:
                recommendations.append({
                    'type': 'warning',
                    'title': '未使用的索引',
                    'message': f'发现{len(unused_indexes)}个很少使用的索引,考虑删除以提升写入性能',
                    'details': [
                        f"{row[1]}.{row[2]} (扫描次数: {row[3]})"
                        for row in unused_indexes[:5]
                    ],
                })
        except Exception:
            # 如果不是PostgreSQL,跳过
            pass
        
        # 通用建议
        recommendations.extend([
            {
                'type': 'info',
                'title': '使用select_related',
                'message': '对于外键关联查询,使用select_related可以减少N+1问题',
                'example': 'await db.execute(select(Article).options(joinedload(Article.author)))',
            },
            {
                'type': 'info',
                'title': '使用prefetch_related',
                'message': '对于一对多关联,使用prefetch_related更高效',
                'example': 'await db.execute(select(Category).options(joinedload(Category.articles)))',
            },
            {
                'type': 'tip',
                'title': '添加数据库索引',
                'message': '为频繁查询的字段添加索引可以显著提升性能',
                'suggestion': '检查慢查询日志,为WHERE条件和JOIN字段添加索引',
            },
            {
                'type': 'tip',
                'title': '使用缓存',
                'message': '对于不经常变化的数据,使用Redis缓存可以减少数据库查询',
                'suggestion': '文章列表、分类信息等可以使用缓存',
            },
        ])
        
        return ApiResponse(
            success=True,
            data={
                'recommendations': recommendations,
                'count': len(recommendations),
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in optimization_recommendations_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
