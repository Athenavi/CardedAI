"""
企业管理管理员端点 - V2增强
提供许可证、工单、部署脚本、监控告警的管理CRUD功能
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.deployment_log import DeploymentLog
from shared.models.deployment_script import DeploymentScript
from shared.models.enterprise_license import EnterpriseLicense
from shared.models.monitoring_alert import MonitoringAlert
from shared.models.monitoring_metric import MonitoringMetric
from shared.models.support_ticket import SupportTicket
from shared.models.support_ticket_reply import SupportTicketReply
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["enterprise-admin"])


async def _check_admin(current_user) -> bool:
    """检查管理员权限"""
    from shared.services.security.rbac_service import rbac_service
    return await rbac_service.check_permission(None, current_user.id, 'settings:update')


# ==================== 许可证管理（管理员） ====================

@router.get("/licenses", summary="获取所有企业许可证列表")
async def list_licenses(
    license_type: Optional[str] = Query(None, description="许可证类型过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取所有企业许可证列表"""
    try:
        stmt = select(EnterpriseLicense).order_by(desc(EnterpriseLicense.created_at))

        if license_type:
            stmt = stmt.where(EnterpriseLicense.license_type == license_type)
        if is_active is not None:
            stmt = stmt.where(EnterpriseLicense.is_active == is_active)

        # 计算总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await db.execute(stmt)
        licenses = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                'items': [lic.to_dict() for lic in licenses],
                'total': total,
                'page': page,
                'page_size': page_size,
                'pages': (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/licenses/{license_id}", summary="获取许可证详情")
async def get_license_detail(
    license_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取许可证详情"""
    try:
        stmt = select(EnterpriseLicense).where(EnterpriseLicense.id == license_id)
        result = await db.execute(stmt)
        license_obj = result.scalar_one_or_none()

        if not license_obj:
            return ApiResponse(success=False, error="License not found")

        return ApiResponse(success=True, data=license_obj.to_dict())
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/licenses/{license_id}", summary="更新许可证")
async def update_license(
    license_id: int,
    company_name: Optional[str] = Body(None),
    contact_email: Optional[str] = Body(None),
    max_sites: Optional[int] = Body(None),
    support_level: Optional[str] = Body(None),
    sla_enabled: Optional[bool] = Body(None),
    sla_uptime_guarantee: Optional[float] = Body(None),
    is_active: Optional[bool] = Body(None),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：更新许可证信息"""
    try:
        stmt = select(EnterpriseLicense).where(EnterpriseLicense.id == license_id)
        result = await db.execute(stmt)
        license_obj = result.scalar_one_or_none()

        if not license_obj:
            return ApiResponse(success=False, error="License not found")

        if company_name is not None:
            license_obj.company_name = company_name
        if contact_email is not None:
            license_obj.contact_email = contact_email
        if max_sites is not None:
            license_obj.max_sites = max_sites
        if support_level is not None:
            license_obj.support_level = support_level
        if sla_enabled is not None:
            license_obj.sla_enabled = sla_enabled
        if sla_uptime_guarantee is not None:
            license_obj.sla_uptime_guarantee = sla_uptime_guarantee
        if is_active is not None:
            license_obj.is_active = is_active

        license_obj.updated_at = datetime.now()
        await db.commit()
        await db.refresh(license_obj)

        return ApiResponse(
            success=True,
            data=license_obj.to_dict(),
            message="License updated successfully"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/licenses/{license_id}", summary="停用许可证")
async def deactivate_license(
    license_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：停用许可证"""
    try:
        stmt = select(EnterpriseLicense).where(EnterpriseLicense.id == license_id)
        result = await db.execute(stmt)
        license_obj = result.scalar_one_or_none()

        if not license_obj:
            return ApiResponse(success=False, error="License not found")

        license_obj.is_active = False
        license_obj.updated_at = datetime.now()
        await db.commit()

        return ApiResponse(success=True, message="License deactivated")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 技术支持工单管理（管理员） ====================

@router.get("/tickets", summary="获取所有工单列表")
async def list_all_tickets(
    status: Optional[str] = Query(None, description="状态过滤"),
    priority: Optional[str] = Query(None, description="优先级过滤"),
    category: Optional[str] = Query(None, description="分类过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取所有工单列表"""
    try:
        stmt = select(SupportTicket).order_by(desc(SupportTicket.created_at))

        if status:
            stmt = stmt.where(SupportTicket.status == status)
        if priority:
            stmt = stmt.where(SupportTicket.priority == priority)
        if category:
            stmt = stmt.where(SupportTicket.category == category)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await db.execute(stmt)
        tickets = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                'items': [t.to_dict() for t in tickets],
                'total': total,
                'page': page,
                'page_size': page_size,
                'pages': (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/tickets/{ticket_id}", summary="获取工单详情（含回复）")
async def get_ticket_detail(
    ticket_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取工单详情及所有回复"""
    try:
        stmt = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return ApiResponse(success=False, error="Ticket not found")

        # 获取回复
        reply_stmt = (
            select(SupportTicketReply)
            .where(SupportTicketReply.ticket_id == ticket_id)
            .order_by(SupportTicketReply.created_at)
        )
        reply_result = await db.execute(reply_stmt)
        replies = reply_result.scalars().all()

        ticket_data = ticket.to_dict()
        ticket_data['replies'] = [r.to_dict() for r in replies]

        return ApiResponse(success=True, data=ticket_data)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/tickets/{ticket_id}", summary="更新工单状态")
async def update_ticket(
    ticket_id: int,
    status: Optional[str] = Body(None, description="工单状态"),
    priority: Optional[str] = Body(None, description="优先级"),
    assigned_to: Optional[int] = Body(None, description="分配给"),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：更新工单状态、优先级或分配"""
    try:
        stmt = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return ApiResponse(success=False, error="Ticket not found")

        if status is not None:
            ticket.status = status
            if status == 'resolved':
                ticket.resolved_at = datetime.now()
            elif status == 'closed':
                ticket.closed_at = datetime.now()
        if priority is not None:
            ticket.priority = priority
        if assigned_to is not None:
            ticket.assigned_to = assigned_to

        ticket.updated_at = datetime.now()
        await db.commit()
        await db.refresh(ticket)

        return ApiResponse(
            success=True,
            data=ticket.to_dict(),
            message="Ticket updated successfully"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 部署脚本管理（管理员） ====================

@router.get("/scripts", summary="获取所有部署脚本列表")
async def list_scripts(
    script_type: Optional[str] = Query(None, description="脚本类型过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取所有部署脚本列表"""
    try:
        stmt = select(DeploymentScript).order_by(desc(DeploymentScript.created_at))

        if script_type:
            stmt = stmt.where(DeploymentScript.script_type == script_type)
        if is_active is not None:
            stmt = stmt.where(DeploymentScript.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await db.execute(stmt)
        scripts = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                'items': [s.to_dict() for s in scripts],
                'total': total,
                'page': page,
                'page_size': page_size,
                'pages': (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/scripts/{script_id}", summary="获取脚本详情")
async def get_script_detail(
    script_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取部署脚本详情"""
    try:
        stmt = select(DeploymentScript).where(DeploymentScript.id == script_id)
        result = await db.execute(stmt)
        script = result.scalar_one_or_none()

        if not script:
            return ApiResponse(success=False, error="Script not found")

        return ApiResponse(success=True, data=script.to_dict())
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/scripts/{script_id}", summary="更新部署脚本")
async def update_script(
    script_id: int,
    name: Optional[str] = Body(None),
    content: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    version: Optional[str] = Body(None),
    is_active: Optional[bool] = Body(None),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：更新部署脚本"""
    try:
        stmt = select(DeploymentScript).where(DeploymentScript.id == script_id)
        result = await db.execute(stmt)
        script = result.scalar_one_or_none()

        if not script:
            return ApiResponse(success=False, error="Script not found")

        if name is not None:
            script.name = name
        if content is not None:
            script.content = content
        if description is not None:
            script.description = description
        if version is not None:
            script.version = version
        if is_active is not None:
            script.is_active = is_active

        script.updated_at = datetime.now()
        await db.commit()
        await db.refresh(script)

        return ApiResponse(
            success=True,
            data=script.to_dict(),
            message="Script updated successfully"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/scripts/{script_id}", summary="删除部署脚本")
async def delete_script(
    script_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：删除部署脚本"""
    try:
        stmt = select(DeploymentScript).where(DeploymentScript.id == script_id)
        result = await db.execute(stmt)
        script = result.scalar_one_or_none()

        if not script:
            return ApiResponse(success=False, error="Script not found")

        await db.delete(script)
        await db.commit()

        return ApiResponse(success=True, message="Script deleted")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 部署日志管理 ====================

@router.get("/logs", summary="获取部署日志列表")
async def list_deployment_logs(
    script_id: Optional[int] = Query(None, description="脚本ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取部署日志列表"""
    try:
        stmt = select(DeploymentLog).order_by(desc(DeploymentLog.created_at))

        if script_id:
            stmt = stmt.where(DeploymentLog.script_id == script_id)
        if status:
            stmt = stmt.where(DeploymentLog.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await db.execute(stmt)
        logs = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                'items': [log.to_dict() for log in logs],
                'total': total,
                'page': page,
                'page_size': page_size,
                'pages': (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 监控告警管理（管理员增强） ====================

@router.get("/alerts", summary="获取所有监控告警")
async def list_alerts(
    severity: Optional[str] = Query(None, description="严重程度过滤"),
    alert_type: Optional[str] = Query(None, description="告警类型过滤"),
    is_resolved: Optional[bool] = Query(None, description="解决状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取所有监控告警（带分页）"""
    try:
        stmt = select(MonitoringAlert).order_by(desc(MonitoringAlert.created_at))

        if severity:
            stmt = stmt.where(MonitoringAlert.severity == severity)
        if alert_type:
            stmt = stmt.where(MonitoringAlert.alert_type == alert_type)
        if is_resolved is not None:
            stmt = stmt.where(MonitoringAlert.is_resolved == is_resolved)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await db.execute(stmt)
        alerts = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                'items': [a.to_dict() for a in alerts],
                'total': total,
                'page': page,
                'page_size': page_size,
                'pages': (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/alerts/{alert_id}/resolve", summary="标记告警为已解决")
async def resolve_alert(
    alert_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：标记告警为已解决"""
    try:
        stmt = select(MonitoringAlert).where(MonitoringAlert.id == alert_id)
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()

        if not alert:
            return ApiResponse(success=False, error="Alert not found")

        alert.is_resolved = True
        alert.resolved_at = datetime.now()
        alert.updated_at = datetime.now()
        await db.commit()

        return ApiResponse(success=True, message="Alert resolved")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/alerts/{alert_id}", summary="删除告警")
async def delete_alert(
    alert_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：删除告警"""
    try:
        stmt = select(MonitoringAlert).where(MonitoringAlert.id == alert_id)
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()

        if not alert:
            return ApiResponse(success=False, error="Alert not found")

        await db.delete(alert)
        await db.commit()

        return ApiResponse(success=True, message="Alert deleted")
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 监控指标查询 ====================

@router.get("/metrics", summary="获取监控指标列表")
async def list_metrics(
    metric_name: Optional[str] = Query(None, description="指标名称过滤"),
    metric_type: Optional[str] = Query(None, description="指标类型过滤"),
    hours: int = Query(24, description="最近N小时的数据"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取监控指标数据"""
    try:
        stmt = select(MonitoringMetric).order_by(desc(MonitoringMetric.timestamp))

        if metric_name:
            stmt = stmt.where(MonitoringMetric.metric_name == metric_name)
        if metric_type:
            stmt = stmt.where(MonitoringMetric.metric_type == metric_type)
        if hours > 0:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(hours=hours)
            stmt = stmt.where(MonitoringMetric.timestamp >= cutoff)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await db.execute(stmt)
        metrics = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                'items': [m.to_dict() for m in metrics],
                'total': total,
                'page': page,
                'page_size': page_size,
                'pages': (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 企业管理概览统计 ====================

@router.get("/overview", summary="企业管理概览统计")
async def get_enterprise_overview(
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """管理员：获取企业管理概览统计"""
    try:
        # 许可证统计
        license_total = (await db.execute(select(func.count(EnterpriseLicense.id)))).scalar() or 0
        license_active = (await db.execute(
            select(func.count(EnterpriseLicense.id)).where(EnterpriseLicense.is_active == True)
        )).scalar() or 0

        # 工单统计
        ticket_total = (await db.execute(select(func.count(SupportTicket.id)))).scalar() or 0
        ticket_open = (await db.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == 'open')
        )).scalar() or 0
        ticket_in_progress = (await db.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == 'in_progress')
        )).scalar() or 0

        # 部署脚本统计
        script_total = (await db.execute(select(func.count(DeploymentScript.id)))).scalar() or 0
        log_total = (await db.execute(select(func.count(DeploymentLog.id)))).scalar() or 0
        log_failed = (await db.execute(
            select(func.count(DeploymentLog.id)).where(DeploymentLog.status == 'failed')
        )).scalar() or 0

        # 监控告警统计
        alert_total = (await db.execute(select(func.count(MonitoringAlert.id)))).scalar() or 0
        alert_unresolved = (await db.execute(
            select(func.count(MonitoringAlert.id)).where(MonitoringAlert.is_resolved == False)
        )).scalar() or 0

        return ApiResponse(
            success=True,
            data={
                'licenses': {
                    'total': license_total,
                    'active': license_active,
                },
                'tickets': {
                    'total': ticket_total,
                    'open': ticket_open,
                    'in_progress': ticket_in_progress,
                },
                'scripts': {
                    'total': script_total,
                    'deployments': log_total,
                    'failed': log_failed,
                },
                'alerts': {
                    'total': alert_total,
                    'unresolved': alert_unresolved,
                }
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
