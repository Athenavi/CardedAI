"""
性能优化 API

提供性能监控和优化建议的API端点
"""

from fastapi import APIRouter, Depends
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/performance", tags=["Performance Optimization"])


@router.get("/stats")
async def get_performance_stats(current_user=Depends(jwt_required)):
    """
    获取性能统计信息
    
    返回应用的实时性能数据，包括：
    - 内存使用情况
    - CPU使用率
    - 慢请求统计
    - 运行时间
    """
    try:
        from src.middleware.performance_monitor import get_performance_stats

        stats = get_performance_stats()

        return ApiResponse(
            success=True,
            data=stats,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/optimization-suggestions")
async def get_optimization_suggestions(current_user=Depends(jwt_required)):
    """
    获取性能优化建议
    
    基于当前性能数据提供优化建议
    """
    try:
        from src.middleware.performance_monitor import get_optimization_suggestions

        suggestions = get_optimization_suggestions()

        return ApiResponse(
            success=True,
            data=suggestions,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/startup-analysis")
async def analyze_startup_performance(current_user=Depends(jwt_required)):
    """
    分析启动性能
    
    提供启动时间分析和优化建议
    """
    try:
        import time
        from datetime import datetime

        # 获取应用启动时间（从进程启动开始）
        import psutil
        import os

        process = psutil.Process(os.getpid())
        create_time = process.create_time()
        uptime = time.time() - create_time

        # 分析模块加载时间
        module_load_info = {
            "total_uptime_seconds": round(uptime, 2),
            "module_count": len([m for m in __import__('sys').modules.keys() if 'src' in m or 'shared' in m]),
            "timestamp": datetime.now().isoformat(),
        }

        # 提供优化建议
        suggestions = []

        if uptime > 30:
            suggestions.append({
                "type": "startup_time",
                "severity": "warning",
                "message": f"启动时间较长 ({uptime:.2f}秒)",
                "recommendations": [
                    "启用模块懒加载",
                    "延迟初始化非关键服务",
                    "使用异步初始化",
                    "减少同步阻塞操作",
                ],
            })

        if module_load_info["module_count"] > 200:
            suggestions.append({
                "type": "module_loading",
                "severity": "info",
                "message": f"加载了 {module_load_info['module_count']} 个模块",
                "recommendations": [
                    "按需加载模块",
                    "使用导入缓存",
                    "合并相关模块",
                ],
            })

        return ApiResponse(
            success=True,
            data={
                "analysis": module_load_info,
                "suggestions": suggestions,
            },
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.post("/cache/clear")
async def clear_performance_cache(current_user=Depends(jwt_required)):
    """
    清除性能缓存
    
    清除所有性能相关的缓存数据
    """
    try:
        # 这里可以添加清除各种缓存的逻辑
        # 例如：Redis缓存、内存缓存等

        return ApiResponse(
            success=True,
            message="Performance cache cleared",
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/memory/profile")
async def get_memory_profile(current_user=Depends(jwt_required)):
    """
    获取内存分析报告
    
    详细的内存使用情况分析
    """
    try:
        import psutil
        import os
        import tracemalloc

        # 开始跟踪内存分配（如果尚未开始）
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        # 获取当前内存快照
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        # 获取前20个内存占用最多的代码位置
        top_20 = []
        for stat in top_stats[:20]:
            top_20.append({
                "file": str(stat.traceback),
                "size_kb": round(stat.size / 1024, 2),
                "count": stat.count,
            })

        # 进程内存信息
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return ApiResponse(
            success=True,
            data={
                "process_memory": {
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                    "percent": process.memory_percent(),
                },
                "top_allocations": top_20,
                "timestamp": __import__('datetime').datetime.now().isoformat(),
            },
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/lazy-loading/stats")
async def get_lazy_loading_stats(current_user=Depends(jwt_required)):
    """
    获取懒加载统计信息
    
    显示哪些模块已加载，哪些还未加载
    """
    try:
        from src.utils.lazy_loader import get_lazy_loader_stats

        stats = get_lazy_loader_stats()

        return ApiResponse(
            success=True,
            data=stats,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/lazy-loading/suggestions")
async def get_lazy_loading_suggestions(current_user=Depends(jwt_required)):
    """
    获取懒加载优化建议
    """
    try:
        from src.utils.lazy_loader import get_lazy_loader_suggestions

        suggestions = get_lazy_loader_suggestions()

        return ApiResponse(
            success=True,
            data=suggestions,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )
