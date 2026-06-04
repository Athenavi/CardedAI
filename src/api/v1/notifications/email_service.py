"""
邮件服务集成 API（SendGrid/Mailgun/SMTP）

提供邮件服务配置管理和邮件发送功能
"""
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.notifications.email_service_integration import email_service_integration
from src.api.v1.core.responses import ApiResponse
from src.api.v1.system.multisite import check_admin_permission
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["email-service"])


@router.get("/config/{provider}", summary="获取邮件服务配置")
async def get_email_config(
        provider: str,
        site_id: Optional[int] = Query(None, description="站点 ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取邮件服务配置
    
    Args:
        provider: 邮件提供商（sendgrid/mailgun/smtp）
        site_id: 站点 ID
        
    Returns:
        邮件服务配置
    """
    try:
        config = await email_service_integration.get_config(db, provider, site_id)

        if not config:
            return ApiResponse(
                success=True,
                data=None,
                message=f"No {provider} configuration found"
            )

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'provider': config.provider,
                'from_email': config.from_email,
                'from_name': config.from_name,
                'enable_batch_sending': config.enable_batch_sending,
                'batch_size': config.batch_size,
                'daily_limit': config.daily_limit,
                'is_active': config.is_active,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/config/{provider}", summary="创建邮件服务配置")
async def create_email_config(
        provider: str,
        from_email: str = Body(..., description="发件人邮箱"),
        api_key: Optional[str] = Body(None, description="API Key（SendGrid/Mailgun）"),
        smtp_host: Optional[str] = Body(None, description="SMTP 主机"),
        smtp_port: Optional[int] = Body(None, description="SMTP 端口"),
        smtp_username: Optional[str] = Body(None, description="SMTP 用户名"),
        smtp_password: Optional[str] = Body(None, description="SMTP 密码"),
        from_name: Optional[str] = Body(None, description="发件人名称"),
        site_id: Optional[int] = Body(None, description="站点 ID"),
        enable_batch_sending: bool = Body(False, description="批量发送"),
        batch_size: int = Body(50, description="批量大小"),
        daily_limit: Optional[int] = Body(None, description="每日限制"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建邮件服务配置
    
    Args:
        provider: 邮件提供商（sendgrid/mailgun/smtp）
        
    Returns:
        创建的配置
    """
    try:
        # 检查权限
        
        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await email_service_integration.create_config(
            db=db,
            provider=provider,
            from_email=from_email,
            api_key=api_key,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            from_name=from_name,
            site_id=site_id,
            enable_batch_sending=enable_batch_sending,
            batch_size=batch_size,
            daily_limit=daily_limit,
        )

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'provider': config.provider,
            },
            message=f"{provider.capitalize()} configuration created successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/config/{config_id}", summary="更新邮件服务配置")
async def update_email_config(
        config_id: int,
        updates: Dict[str, Any] = Body(..., description="更新字段"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新邮件服务配置
    
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

        config = await email_service_integration.update_config(db, config_id, updates)

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'provider': config.provider,
            },
            message="Email service configuration updated successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/config/{config_id}", summary="停用邮件服务配置")
async def deactivate_email_config(
        config_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    停用邮件服务配置
    
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

        await email_service_integration.deactivate_config(db, config_id)

        return ApiResponse(
            success=True,
            message="Email service configuration deactivated successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/send", summary="发送邮件")
async def send_email(
        provider: str = Body(..., description="邮件提供商"),
        to_email: str = Body(..., description="收件人邮箱"),
        subject: str = Body(..., description="邮件主题"),
        html_content: str = Body(..., description="HTML 内容"),
        text_content: Optional[str] = Body(None, description="纯文本内容"),
        from_name: Optional[str] = Body(None, description="发件人名称"),
        site_id: Optional[int] = Body(None, description="站点 ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    发送邮件
    
    Args:
        provider: 邮件提供商
        
    Returns:
        发送结果
    """
    try:
        config = await email_service_integration.get_config(db, provider, site_id)

        if not config:
            return ApiResponse(
                success=False,
                error=f"No {provider} configuration found"
            )

        success = await email_service_integration.send_email(
            config,
            to_email,
            subject,
            html_content,
            text_content,
            from_name,
        )

        if success:
            return ApiResponse(
                success=True,
                message="Email sent successfully"
            )
        else:
            return ApiResponse(
                success=False,
                error="Failed to send email"
            )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/send-batch", summary="批量发送邮件")
async def send_batch_emails(
        provider: str = Body(..., description="邮件提供商"),
        recipients: List[Dict[str, str]] = Body(..., description="收件人列表"),
        subject: str = Body(..., description="邮件主题"),
        html_content: str = Body(..., description="HTML 内容"),
        text_content: Optional[str] = Body(None, description="纯文本内容"),
        site_id: Optional[int] = Body(None, description="站点 ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    批量发送邮件
    
    Args:
        provider: 邮件提供商
        recipients: 收件人列表 [{'email': '...', 'name': '...'}]
        
    Returns:
        发送结果统计
    """
    try:
        config = await email_service_integration.get_config(db, provider, site_id)

        if not config:
            return ApiResponse(
                success=False,
                error=f"No {provider} configuration found"
            )

        result = await email_service_integration.send_batch_emails(
            config,
            recipients,
            subject,
            html_content,
            text_content,
        )

        return ApiResponse(
            success=True,
            data=result,
            message=f"Batch email completed: {result['success']} succeeded, {result['failed']} failed"
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/configs", summary="获取所有邮件服务配置")
async def get_all_configs(
        include_inactive: bool = Query(False, description="是否包含非活动配置"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取所有邮件服务配置
    
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

        configs = await email_service_integration.get_all_configs(db, include_inactive)

        configs_list = []
        for config in configs:
            configs_list.append({
                'id': config.id,
                'provider': config.provider,
                'site_id': config.site_id,
                'from_email': config.from_email,
                'from_name': config.from_name,
                'enable_batch_sending': config.enable_batch_sending,
                'batch_size': config.batch_size,
                'daily_limit': config.daily_limit,
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
