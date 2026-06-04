"""
系统管理API
包括健康检查、系统信息等
"""
import os

from fastapi import APIRouter, Depends, Query, Request

from src.api.v1.core.responses import ApiResponse
from shared.models.user import User
from src.auth.auth_deps import admin_required as admin_required_api

router = APIRouter()


@router.get("/health",
            summary="站点健康检查",
            description="运行完整的站点健康检查,返回各项指标和评分(仅管理员)",
            response_description="返回健康检查结果")
async def site_health_check_api(
        request: Request,
        format: str = Query('json', description="报告格式: json或text"),
        current_user: User = Depends(admin_required_api)
):
    """
    站点健康检查API
    """
    try:
        from shared.services.system.site_health import site_health_service
        if format == 'text':
            report = site_health_service.generate_report('text')
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=report)
        
        # 默认返回JSON
        health_data = site_health_service.run_full_check()
        
        return ApiResponse(
            success=True,
            data=health_data
        )
    except Exception as e:
        import traceback
        print(f"Error in site_health_check_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/info",
            summary="系统信息",
            description="获取系统基本信息(仅管理员)",
            response_description="返回系统信息")
async def system_info_api(
        request: Request,
        current_user: User = Depends(admin_required_api)
):
    """
    系统信息API
    """
    try:
        import platform
        import sys
        from pathlib import Path
        
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        
        info = {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': f"{platform.system()} {platform.release()}",
            'base_dir': str(base_dir),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug_mode': os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes'),
        }
        
        return ApiResponse(
            success=True,
            data=info
        )
    except Exception as e:
        import traceback
        print(f"Error in system_info_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
