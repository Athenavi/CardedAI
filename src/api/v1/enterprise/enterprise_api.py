"""
企业版功能 API
提供许可证管理、技术支持、SLA保障、部署脚本和监控告警等功能
"""
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.enterprise.enterprise_service import enterprise_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["enterprise"])


# ==================== 许可证管理 ====================

@router.post("/license", summary="创建企业许可证")
async def create_license(
        license_type: str = Body('professional', description="许可证类型"),
        company_name: str = Body('', description="公司名称"),
        contact_email: str = Body('', description="联系邮箱"),
        max_sites: int = Body(-1, description="最大站点数（-1表示无限）"),
        valid_days: int = Body(365, description="有效天数"),
        support_level: str = Body('standard', description="支持级别"),
        sla_enabled: bool = Body(False, description="是否启用SLA"),
        sla_uptime_guarantee: float = Body(99.9, description="SLA可用性保证"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """创建企业许可证（需要管理员权限）"""
    try:
        # 检查管理员权限
        from shared.services.security.rbac_service import rbac_service
        has_permission = await rbac_service.check_permission(db, current_user.id, 'settings:update')
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        license_obj = await enterprise_service.create_license(
            db=db,
            license_type=license_type,
            company_name=company_name,
            contact_email=contact_email,
            max_sites=max_sites,
            valid_days=valid_days,
            support_level=support_level,
            sla_enabled=sla_enabled,
            sla_uptime_guarantee=sla_uptime_guarantee
        )

        return ApiResponse(
            success=True,
            data={
                'license_key': license_obj.license_key,
                'license_type': license_obj.license_type,
                'company_name': license_obj.company_name,
                'max_sites': license_obj.max_sites,
                'valid_from': license_obj.valid_from.isoformat(),
                'valid_until': license_obj.valid_until.isoformat() if license_obj.valid_until else None,
                'support_level': license_obj.support_level,
                'sla_enabled': license_obj.sla_enabled,
            },
            message="License created successfully"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/license/validate", summary="验证许可证")
async def validate_license(
        license_key: str = Query(..., description="许可证密钥"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """验证许可证有效性"""
    try:
        license_info = await enterprise_service.get_license_info(db, license_key)

        if not license_info:
            return ApiResponse(success=False, error="Invalid or expired license")

        return ApiResponse(success=True, data=license_info)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 技术支持工单 ====================

@router.post("/support/ticket", summary="创建技术支持工单")
async def create_support_ticket(
        subject: str = Body(..., description="工单主题"),
        description: str = Body(..., description="问题描述"),
        priority: str = Body('medium', description="优先级"),
        category: str = Body('general', description="分类"),
        license_id: Optional[int] = Body(None, description="许可证ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """创建技术支持工单"""
    try:
        ticket = await enterprise_service.create_support_ticket(
            db=db,
            user_id=current_user.id,
            subject=subject,
            description=description,
            priority=priority,
            category=category,
            license_id=license_id
        )

        return ApiResponse(
            success=True,
            data={
                'ticket_number': ticket.ticket_number,
                'id': ticket.id,
                'status': ticket.status,
                'priority': ticket.priority,
            },
            message="Support ticket created successfully"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/support/tickets", summary="获取我的工单列表")
async def get_my_tickets(
        status: Optional[str] = Query(None, description="状态过滤"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户的工单列表"""
    try:
        tickets = await enterprise_service.get_user_tickets(db, current_user.id, status)

        tickets_list = []
        for ticket in tickets:
            tickets_list.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'status': ticket.status,
                'priority': ticket.priority,
                'category': ticket.category,
                'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                'tickets': tickets_list,
                'total': len(tickets_list)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/support/ticket/{ticket_id}/reply", summary="回复工单")
async def reply_to_ticket(
        ticket_id: int,
        content: str = Body(..., description="回复内容"),
        attachments: Optional[List[str]] = Body(None, description="附件列表"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """回复技术支持工单"""
    try:
        # 检查用户是否为工作人员
        is_staff = current_user.is_staff or current_user.is_superuser

        reply = await enterprise_service.add_ticket_reply(
            db=db,
            ticket_id=ticket_id,
            user_id=current_user.id,
            content=content,
            is_staff=is_staff,
            attachments=attachments
        )

        return ApiResponse(
            success=True,
            data={
                'id': reply.id,
                'created_at': reply.created_at.isoformat() if reply.created_at else None,
            },
            message="Reply added successfully"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 部署脚本管理 ====================

@router.post("/deployment/script", summary="创建部署脚本")
async def create_deployment_script(
        name: str = Body(..., description="脚本名称"),
        script_type: str = Body(..., description="脚本类型"),
        content: str = Body(..., description="脚本内容"),
        version: str = Body('1.0.0', description="版本"),
        description: Optional[str] = Body(None, description="描述"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """创建部署脚本（需要管理员权限）"""
    try:
        # 检查管理员权限
        from shared.services.security.rbac_service import rbac_service
        has_permission = await rbac_service.check_permission(db, current_user.id, 'settings:update')
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        script = await enterprise_service.create_deployment_script(
            db=db,
            name=name,
            script_type=script_type,
            content=content,
            version=version,
            description=description,
            created_by=current_user.id
        )

        return ApiResponse(
            success=True,
            data={
                'id': script.id,
                'name': script.name,
                'version': script.version,
            },
            message="Deployment script created successfully"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/deployment/script/{script_id}/execute", summary="执行部署脚本")
async def execute_deployment_script(
        script_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """执行部署脚本（需要管理员权限）"""
    try:
        # 检查管理员权限
        from shared.services.security.rbac_service import rbac_service
        has_permission = await rbac_service.check_permission(db, current_user.id, 'settings:update')
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        log = await enterprise_service.execute_deployment_script(
            db=db,
            script_id=script_id,
            user_id=current_user.id
        )

        return ApiResponse(
            success=True,
            data={
                'log_id': log.id,
                'status': log.status,
                'started_at': log.started_at.isoformat() if log.started_at else None,
            },
            message="Deployment script execution started"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 监控告警 ====================

@router.get("/monitoring/alerts", summary="获取监控告警列表")
async def get_monitoring_alerts(
        severity: Optional[str] = Query(None, description="严重程度过滤"),
        is_resolved: Optional[bool] = Query(None, description="解决状态过滤"),
        limit: int = Query(50, description="返回数量限制"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取监控告警列表（需要管理员权限）"""
    try:
        from sqlalchemy import select

        stmt = select(MonitoringAlert).order_by(MonitoringAlert.created_at.desc()).limit(limit)

        if severity:
            stmt = stmt.where(MonitoringAlert.severity == severity)

        if is_resolved is not None:
            stmt = stmt.where(MonitoringAlert.is_resolved == is_resolved)

        result = await db.execute(stmt)
        alerts = result.scalars().all()

        alerts_list = []
        for alert in alerts:
            alerts_list.append({
                'id': alert.id,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'is_resolved': alert.is_resolved,
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                'alerts': alerts_list,
                'total': len(alerts_list)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/monitoring/metric", summary="记录监控指标")
async def record_monitoring_metric(
        metric_name: str = Body(..., description="指标名称"),
        metric_value: float = Body(..., description="指标值"),
        metric_type: str = Body(..., description="指标类型"),
        site_id: Optional[int] = Body(None, description="站点ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """记录监控指标"""
    try:
        metric = await enterprise_service.record_monitoring_metric(
            db=db,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            site_id=site_id
        )

        return ApiResponse(
            success=True,
            data={'id': metric.id},
            message="Metric recorded successfully"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# 导入MonitoringAlert用于类型提示
from shared.models.monitoring_alert import MonitoringAlert
