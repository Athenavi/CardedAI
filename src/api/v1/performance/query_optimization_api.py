"""
查询优化管理 API
提供查询分析、性能监控等功能
"""

from fastapi import APIRouter, Depends, Query, Body

from shared.services.performance.query_optimizer import query_optimizer
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required
from src.extensions import get_db

router = APIRouter(tags=["query-optimization"])


@router.get("/report", summary="获取查询优化报告")
async def get_optimization_report(current_user=Depends(admin_required)):
    """
    获取数据库查询优化报告
    
    Returns:
        优化报告，包含慢查询、N+1问题等
    """
    try:
        report = query_optimizer.get_optimization_report()

        return ApiResponse(
            success=True,
            data=report
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取报告失败: {str(e)}")


@router.post("/analyze", summary="分析特定查询")
async def analyze_query(
        sql_query: str = Body(..., description="SQL查询语句"),
        current_user=Depends(admin_required),
        db=Depends(get_db)
):
    """
    分析特定SQL查询的执行计划
    
    Args:
        sql_query: SQL查询语句
        
    Returns:
        查询计划分析和优化建议
    """
    try:
        from src.utils.database.main import get_async_session

        async for session in get_async_session():
            result = await query_optimizer.analyze_query_plan(session, sql_query)

            if result['success']:
                return ApiResponse(
                    success=True,
                    data=result
                )
            else:
                return ApiResponse(
                    success=False,
                    error=result.get('error', '分析失败')
                )
    except Exception as e:
        return ApiResponse(success=False, error=f"分析查询失败: {str(e)}")


@router.get("/slow-queries", summary="获取慢查询列表")
async def get_slow_queries(
        limit: int = Query(50, ge=1, le=200, description="返回数量"),
        current_user=Depends(admin_required)
):
    """
    获取慢查询列表
    
    Args:
        limit: 返回数量
        
    Returns:
        慢查询列表
    """
    try:
        # 按耗时排序
        slow_queries = sorted(
            query_optimizer.slow_queries,
            key=lambda x: x['duration'],
            reverse=True
        )[:limit]

        return ApiResponse(
            success=True,
            data={
                'slow_queries': slow_queries,
                'count': len(slow_queries),
                'total': len(query_optimizer.slow_queries),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取慢查询失败: {str(e)}")


@router.get("/n-plus-one-warnings", summary="获取N+1查询警告")
async def get_n_plus_one_warnings(
        current_user=Depends(admin_required)
):
    """
    获取N+1查询问题警告
    
    Returns:
        N+1查询警告列表
    """
    try:
        return ApiResponse(
            success=True,
            data={
                'warnings': query_optimizer.n_plus_one_warnings,
                'count': len(query_optimizer.n_plus_one_warnings),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取警告失败: {str(e)}")


@router.post("/reset-stats", summary="重置统计数据")
async def reset_stats(current_user=Depends(admin_required)):
    """
    重置所有查询统计数据
    
    Returns:
        操作结果
    """
    try:
        query_optimizer.reset_stats()

        return ApiResponse(
            success=True,
            data={'message': '统计数据已重置'}
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"重置失败: {str(e)}")


@router.get("/query-stats", summary="获取查询统计")
async def get_query_stats(
        sort_by: str = Query('count', enum=['count', 'avg_time', 'total_time'], description="排序字段"),
        limit: int = Query(50, ge=1, le=200, description="返回数量"),
        current_user=Depends(admin_required)
):
    """
    获取查询统计数据
    
    Args:
        sort_by: 排序字段 (count/avg_time/total_time)
        limit: 返回数量
        
    Returns:
        查询统计列表
    """
    try:
        # 转换为列表并排序
        stats_list = [
            {'name': name, **stats}
            for name, stats in query_optimizer.query_stats.items()
        ]

        # 排序
        stats_list.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

        # 限制数量
        stats_list = stats_list[:limit]

        return ApiResponse(
            success=True,
            data={
                'stats': stats_list,
                'count': len(stats_list),
                'total': len(query_optimizer.query_stats),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


# 导入数据库会话
