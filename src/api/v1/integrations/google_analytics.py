"""
Google Analytics 集成 API

提供 Google Analytics 配置管理和追踪代码生成功能
"""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.analytics.google_analytics_service import google_analytics_service
from src.api.v1.core.responses import ApiResponse
from src.api.v1.system.multisite import check_admin_permission
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["google-analytics"])


@router.get("/config", summary="获取 Google Analytics 配置")
async def get_ga_config(
        site_id: Optional[int] = Query(None, description="站点 ID（为空则获取全局配置）"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取 Google Analytics 配置
    
    Args:
        site_id: 站点 ID（可选）
        
    Returns:
        Google Analytics 配置
    """
    try:
        config = await google_analytics_service.get_config(db, site_id)

        if not config:
            return ApiResponse(
                success=True,
                data=None,
                message="No Google Analytics configuration found"
            )

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'site_id': config.site_id,
                'tracking_id': config.tracking_id,
                'measurement_id': config.measurement_id,
                'enable_page_view_tracking': config.enable_page_view_tracking,
                'enable_event_tracking': config.enable_event_tracking,
                'enable_user_behavior_analysis': config.enable_user_behavior_analysis,
                'anonymize_ip': config.anonymize_ip,
                'sample_rate': config.sample_rate,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/config", summary="创建 Google Analytics 配置")
async def create_ga_config(
        tracking_id: str = Body(..., description="Tracking ID (如 G-XXXXXXXXXX)"),
        measurement_id: Optional[str] = Body(None, description="GA4 Measurement ID"),
        api_secret: Optional[str] = Body(None, description="API Secret"),
        site_id: Optional[int] = Body(None, description="站点 ID（可选）"),
        enable_page_view_tracking: bool = Body(True, description="是否启用页面浏览追踪"),
        enable_event_tracking: bool = Body(True, description="是否启用事件追踪"),
        enable_user_behavior_analysis: bool = Body(False, description="是否启用用户行为分析"),
        anonymize_ip: bool = Body(True, description="是否匿名化 IP"),
        sample_rate: float = Body(100.0, description="采样率（0-100）"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建 Google Analytics 配置
    
    Returns:
        创建的配置
    """
    try:
        # 检查权限（需要admin权限）

        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await google_analytics_service.create_config(
            db=db,
            tracking_id=tracking_id,
            measurement_id=measurement_id,
            api_secret=api_secret,
            site_id=site_id,
            enable_page_view_tracking=enable_page_view_tracking,
            enable_event_tracking=enable_event_tracking,
            enable_user_behavior_analysis=enable_user_behavior_analysis,
            anonymize_ip=anonymize_ip,
            sample_rate=sample_rate,
        )

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'tracking_id': config.tracking_id,
                'measurement_id': config.measurement_id,
            },
            message="Google Analytics configuration created successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/config/{config_id}", summary="更新 Google Analytics 配置")
async def update_ga_config(
        config_id: int,
        updates: Dict[str, Any] = Body(..., description="更新字段"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新 Google Analytics 配置
    
    Args:
        config_id: 配置 ID
        updates: 更新字段
        
    Returns:
        更新后的配置
    """
    try:
        # 检查权限

        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await google_analytics_service.update_config(db, config_id, updates)

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'tracking_id': config.tracking_id,
            },
            message="Google Analytics configuration updated successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/config/{config_id}", summary="停用 Google Analytics 配置")
async def deactivate_ga_config(
        config_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    停用 Google Analytics 配置
    
    Args:
        config_id: 配置 ID
        
    Returns:
        操作结果
    """
    try:
        # 检查权限
        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        await google_analytics_service.deactivate_config(db, config_id)

        return ApiResponse(
            success=True,
            message="Google Analytics configuration deactivated successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/tracking-code", summary="获取 Google Analytics 追踪代码")
async def get_tracking_code(
        site_id: Optional[int] = Query(None, description="站点 ID（为空则获取全局配置）"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取 Google Analytics 追踪代码（用于前端嵌入）
    
    Args:
        site_id: 站点 ID（可选）
        
    Returns:
        HTML/JavaScript 追踪代码
    """
    try:
        config = await google_analytics_service.get_config(db, site_id)

        if not config or not config.is_active:
            return ApiResponse(
                success=True,
                data={'tracking_code': ''},
                message="Google Analytics is not configured or inactive"
            )

        tracking_code = google_analytics_service.generate_tracking_code(config)

        return ApiResponse(
            success=True,
            data={
                'tracking_code': tracking_code,
                'config': {
                    'tracking_id': config.tracking_id,
                    'measurement_id': config.measurement_id,
                    'enable_page_view_tracking': config.enable_page_view_tracking,
                    'enable_event_tracking': config.enable_event_tracking,
                    'anonymize_ip': config.anonymize_ip,
                }
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/event-tracking-code", summary="生成事件追踪代码")
async def generate_event_code(
        event_name: str = Body(..., description="事件名称"),
        event_params: Optional[Dict[str, Any]] = Body(None, description="事件参数"),
        current_user=Depends(jwt_required),
):
    """
    生成 Google Analytics 事件追踪代码
    
    Args:
        event_name: 事件名称
        event_params: 事件参数
        
    Returns:
        JavaScript 事件追踪代码
    """
    try:
        event_code = google_analytics_service.generate_event_tracking_code(event_name, event_params)

        return ApiResponse(
            success=True,
            data={
                'event_code': event_code,
                'event_name': event_name,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/configs", summary="获取所有 Google Analytics 配置")
async def get_all_configs(
        include_inactive: bool = Query(False, description="是否包含非活动配置"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取所有 Google Analytics 配置（管理员用）
    
    Args:
        include_inactive: 是否包含非活动配置
        
    Returns:
        配置列表
    """
    try:
        # 检查权限

        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        configs = await google_analytics_service.get_all_configs(db, include_inactive)

        configs_list = []
        for config in configs:
            configs_list.append({
                'id': config.id,
                'site_id': config.site_id,
                'tracking_id': config.tracking_id,
                'measurement_id': config.measurement_id,
                'enable_page_view_tracking': config.enable_page_view_tracking,
                'enable_event_tracking': config.enable_event_tracking,
                'enable_user_behavior_analysis': config.enable_user_behavior_analysis,
                'anonymize_ip': config.anonymize_ip,
                'sample_rate': config.sample_rate,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat() if config.created_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                'configs': configs_list,
                'total': len(configs_list)
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))
