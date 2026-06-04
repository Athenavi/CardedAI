"""
维护模式管理API
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel

from shared.services.system.maintenance_mode import maintenance_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


class MaintenanceEnableRequest(BaseModel):
    """启用维护模式请求"""
    message: Optional[str] = "系统正在维护中，请稍后访问"
    whitelist_ips: Optional[List[str]] = []
    retry_after: int = 3600


class ScheduleMaintenanceRequest(BaseModel):
    """计划维护请求"""
    start_time: str
    end_time: str
    message: Optional[str] = "系统将在指定时间进行维护"
    whitelist_ips: Optional[List[str]] = []


@router.get("/status",
            summary="获取维护模式状态",
            description="获取当前维护模式的状态信息",
            response_description="返回维护模式状态")
async def get_maintenance_status_api(
        current_user=Depends(jwt_required)
):
    """获取维护模式状态"""
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        status = maintenance_service.get_status()
        
        return ApiResponse(
            success=True,
            data=status
        )
    except Exception as e:
        import traceback
        print(f"Error in get_maintenance_status_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/enable",
             summary="启用维护模式",
             description="立即启用维护模式",
             response_description="返回操作结果")
async def enable_maintenance_api(
        request: MaintenanceEnableRequest,
        current_user=Depends(jwt_required)
):
    """启用维护模式"""
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        config = maintenance_service.enable_maintenance(
            message=request.message,
            whitelist_ips=request.whitelist_ips,
            retry_after=request.retry_after
        )
        
        return ApiResponse(
            success=True,
            data={
                "message": "Maintenance mode enabled successfully",
                "config": config
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in enable_maintenance_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/disable",
             summary="禁用维护模式",
             description="关闭维护模式",
             response_description="返回操作结果")
async def disable_maintenance_api(
        current_user=Depends(jwt_required)
):
    """禁用维护模式"""
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        config = maintenance_service.disable_maintenance()
        
        return ApiResponse(
            success=True,
            data={
                "message": "Maintenance mode disabled successfully",
                "config": config
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in disable_maintenance_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/schedule",
             summary="计划维护时间",
             description="设置计划的维护时间段",
             response_description="返回操作结果")
async def schedule_maintenance_api(
        request: ScheduleMaintenanceRequest,
        current_user=Depends(jwt_required)
):
    """计划维护时间"""
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        config = maintenance_service.schedule_maintenance(
            start_time=request.start_time,
            end_time=request.end_time,
            message=request.message,
            whitelist_ips=request.whitelist_ips
        )
        
        return ApiResponse(
            success=True,
            data={
                "message": "Maintenance scheduled successfully",
                "config": config
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in schedule_maintenance_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/whitelist/add",
             summary="添加IP到白名单",
             description="将指定IP添加到维护模式白名单",
             response_description="返回操作结果")
async def add_whitelist_ip_api(
        ip: str = Body(..., embed=True, description="IP地址"),
        current_user=Depends(jwt_required)
):
    """添加IP到白名单"""
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        config = maintenance_service.add_whitelist_ip(ip)
        
        return ApiResponse(
            success=True,
            data={
                "message": f"IP {ip} added to whitelist",
                "config": config
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in add_whitelist_ip_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/whitelist/remove",
             summary="从白名单移除IP",
             description="从维护模式白名单中移除指定IP",
             response_description="返回操作结果")
async def remove_whitelist_ip_api(
        ip: str = Body(..., embed=True, description="IP地址"),
        current_user=Depends(jwt_required)
):
    """从白名单移除IP"""
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        config = maintenance_service.remove_whitelist_ip(ip)
        
        return ApiResponse(
            success=True,
            data={
                "message": f"IP {ip} removed from whitelist",
                "config": config
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in remove_whitelist_ip_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.put("/message",
            summary="更新维护提示信息",
            description="更新维护模式的提示信息",
            response_description="返回操作结果")
async def update_message_api(
        message: str = Body(..., embed=True, description="维护提示信息"),
        current_user=Depends(jwt_required)
):
    """更新维护提示信息"""
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        config = maintenance_service.update_message(message)
        
        return ApiResponse(
            success=True,
            data={
                "message": "Message updated successfully",
                "config": config
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in update_message_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
