"""
审计日志 API
提供审计日志查询、导出和管理功能
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.security.audit_log_service import AuditLog as AuditLogModel
from shared.services.security.audit_log_service import AuditLogAction, AuditLogLevel, audit_log_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["audit-log"])


@router.get("/logs", summary="查询审计日志")
async def get_audit_logs(
        user_id: Optional[int] = Query(None, description="用户ID过滤"),
        action: Optional[str] = Query(None, description="操作类型过滤"),
        level: Optional[str] = Query(None, description="日志级别过滤"),
        resource_type: Optional[str] = Query(None, description="资源类型过滤"),
        resource_id: Optional[str] = Query(None, description="资源ID过滤"),
        ip_address: Optional[str] = Query(None, description="IP地址过滤"),
        start_date: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
        end_date: Optional[str] = Query(None, description="结束日期 (ISO格式)"),
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(50, ge=1, le=200, description="每页数量"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    查询审计日志
    
    Args:
        user_id: 用户ID过滤
        action: 操作类型 (login, logout, create, update, delete等)
        level: 日志级别 (info, warning, error, critical)
        resource_type: 资源类型 (article, user, category等)
        resource_id: 资源ID
        ip_address: IP地址
        start_date: 开始日期 (ISO格式字符串)
        end_date: 结束日期 (ISO格式字符串)
        page: 页码
        per_page: 每页数量
        
    Returns:
        审计日志列表和分页信息
    """
    try:
        # 解析日期
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return ApiResponse(success=False, error="Invalid start_date format")

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return ApiResponse(success=False, error="Invalid end_date format")

        # 解析枚举值
        action_enum = None
        if action:
            try:
                action_enum = AuditLogAction(action)
            except ValueError:
                return ApiResponse(success=False, error=f"Invalid action: {action}")

        level_enum = None
        if level:
            try:
                level_enum = AuditLogLevel(level)
            except ValueError:
                return ApiResponse(success=False, error=f"Invalid level: {level}")

        # 查询日志
        result = await audit_log_service.get_logs(
            db=db,
            user_id=user_id,
            action=action_enum,
            level=level_enum,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            start_date=start_dt,
            end_date=end_dt,
            page=page,
            per_page=per_page
        )

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/export", summary="导出审计日志")
async def export_audit_logs(
        format: str = Query("json", pattern="^(json|csv)$", description="导出格式 (json或csv)"),
        user_id: Optional[int] = Query(None, description="用户ID过滤"),
        action: Optional[str] = Query(None, description="操作类型过滤"),
        level: Optional[str] = Query(None, description="日志级别过滤"),
        resource_type: Optional[str] = Query(None, description="资源类型过滤"),
        resource_id: Optional[str] = Query(None, description="资源ID过滤"),
        ip_address: Optional[str] = Query(None, description="IP地址过滤"),
        start_date: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
        end_date: Optional[str] = Query(None, description="结束日期 (ISO格式)"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    导出审计日志
    
    Args:
        format: 导出格式 (json或csv)
        user_id: 用户ID过滤
        action: 操作类型
        level: 日志级别
        resource_type: 资源类型
        resource_id: 资源ID
        ip_address: IP地址
        start_date: 开始日期 (ISO格式字符串)
        end_date: 结束日期 (ISO格式字符串)
        
    Returns:
        导出的数据（JSON或CSV格式）
    """
    try:
        # 解析日期
        filters = {}

        if user_id:
            filters['user_id'] = user_id

        if action:
            try:
                filters['action'] = AuditLogAction(action)
            except ValueError:
                return ApiResponse(success=False, error=f"Invalid action: {action}")

        if level:
            try:
                filters['level'] = AuditLogLevel(level)
            except ValueError:
                return ApiResponse(success=False, error=f"Invalid level: {level}")

        if resource_type:
            filters['resource_type'] = resource_type

        if resource_id:
            filters['resource_id'] = resource_id

        if ip_address:
            filters['ip_address'] = ip_address

        if start_date:
            try:
                filters['start_date'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return ApiResponse(success=False, error="Invalid start_date format")

        if end_date:
            try:
                filters['end_date'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return ApiResponse(success=False, error="Invalid end_date format")

        # 导出日志
        exported_data = await audit_log_service.export_logs(
            db=db,
            output_format=format,
            **filters
        )

        return ApiResponse(
            success=True,
            data={
                'format': format,
                'content': exported_data,
                'count': len(exported_data.split('\n')) if format == 'csv' else len(eval(exported_data))
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/stats", summary="获取审计日志统计")
async def get_audit_log_stats(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取审计日志统计数据
    
    Args:
        days: 统计天数
        
    Returns:
        统计数据
    """
    try:
        from sqlalchemy import func, select

        cutoff_date = datetime.now() - timedelta(days=days)

        # 总日志数
        total_query = select(func.count()).select_from(AuditLogModel).where(
            AuditLogModel.created_at >= cutoff_date
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()

        # 按操作类型统计
        action_query = select(
            AuditLogModel.action,
            func.count().label('count')
        ).where(
            AuditLogModel.created_at >= cutoff_date
        ).group_by(AuditLogModel.action)

        action_result = await db.execute(action_query)
        action_stats = [
            {'action': row[0], 'count': row[1]}
            for row in action_result.all()
        ]

        # 按日志级别统计
        level_query = select(
            AuditLogModel.level,
            func.count().label('count')
        ).where(
            AuditLogModel.created_at >= cutoff_date
        ).group_by(AuditLogModel.level)

        level_result = await db.execute(level_query)
        level_stats = [
            {'level': row[0], 'count': row[1]}
            for row in level_result.all()
        ]

        # 活跃用户数
        users_query = select(
            func.count(func.distinct(AuditLogModel.user_id))
        ).where(
            AuditLogModel.created_at >= cutoff_date
        )
        users_result = await db.execute(users_query)
        active_users = users_result.scalar()

        return ApiResponse(
            success=True,
            data={
                'period_days': days,
                'total_logs': total_count,
                'active_users': active_users,
                'by_action': action_stats,
                'by_level': level_stats
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/cleanup", summary="清理旧日志")
async def cleanup_old_logs(
        days: int = Query(90, ge=1, description="保留天数"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    清理旧的审计日志
    
    Args:
        days: 保留天数，超过此天数的日志将被删除
        
    Returns:
        清理结果
    """
    try:
        await audit_log_service.cleanup_old_logs(db, days)

        return ApiResponse(
            success=True,
            message=f"已清理{days}天前的审计日志"
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))
