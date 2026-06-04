"""
CSS优化API
提供关键CSS提取和缓存管理功能
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, Body

from shared.models.user import User
from shared.services.performance.css_optimizer import css_optimizer_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api

router = APIRouter()


@router.post("/extract",
             summary="提取关键CSS",
             description="从HTML内容中提取Above-the-fold关键CSS(仅管理员)",
             response_description="返回关键CSS")
async def extract_critical_css_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    提取关键CSS API
    
    Request Body:
    {
        "html_content": "<html>...",
        "css_files": ["/path/to/style.css"],
        "page_type": "article"
    }
    """
    try:
        html_content = data.get('html_content', '')
        css_files = data.get('css_files', [])
        page_type = data.get('page_type', 'article')
        
        if not html_content:
            return ApiResponse(success=False, error='缺少HTML内容')
        
        result = css_optimizer_service.optimize_page_css(html_content, css_files, page_type)
        
        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in extract_critical_css_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/cache/stats",
            summary="缓存统计",
            description="获取CSS缓存统计信息(仅管理员)",
            response_description="返回缓存统计")
async def css_cache_stats_api(
        request: Request,
        current_user: User = Depends(admin_required_api)
):
    """
    CSS缓存统计API
    """
    try:
        stats = css_optimizer_service.get_cache_stats()
        
        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        import traceback
        print(f"Error in css_cache_stats_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/cache/clear",
             summary="清除缓存",
             description="清除所有CSS缓存(仅管理员)",
             response_description="返回操作结果")
async def clear_css_cache_api(
        request: Request,
        current_user: User = Depends(admin_required_api)
):
    """
    清除CSS缓存API
    """
    try:
        success = css_optimizer_service.clear_cache()
        
        if success:
            return ApiResponse(
                success=True,
                message='缓存已清除'
            )
        else:
            return ApiResponse(
                success=False,
                error='清除缓存失败'
            )
    except Exception as e:
        import traceback
        print(f"Error in clear_css_cache_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/info",
            summary="CSS优化信息",
            description="获取CSS优化配置和建议",
            response_description="返回优化信息")
async def css_optimization_info_api(request: Request):
    """
    CSS优化信息API
    """
    return ApiResponse(
        success=True,
        data={
            'enabled': True,
            'features': [
                '关键CSS提取',
                '异步CSS加载',
                '缓存管理',
                'FOUC预防',
            ],
            'recommendations': [
                '将首屏必需的CSS内联到<head>',
                '非关键CSS使用异步加载',
                '使用preload预加载字体和资源',
                '定期清理过期缓存',
            ],
            'cache_dir': str(css_optimizer_service.cache_dir),
        }
    )
