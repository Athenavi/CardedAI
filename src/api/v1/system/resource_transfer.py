"""
外部资源转存API
提供下载任务管理、进度查询等功能
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.download_task import DownloadTask
from src.api.v1.core.responses import ApiResponse
from shared.services.performance.resource_transfer_service import ResourceTransferService
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["resource-transfer"])


@router.post("/download", summary="创建下载任务")
async def create_download_task(
        url: str = Query(..., description="资源URL"),
        resource_type: str = Query("image", description="资源类型: image/video/audio/document/other"),
        priority: int = Query(0, description="优先级（数字越小优先级越高）"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建外部资源下载任务
    
    - **url**: 资源的完整URL地址
    - **resource_type**: 资源类型（image/video/audio/document/other）
    - **priority**: 优先级，数字越小优先级越高
    """
    try:
        service = ResourceTransferService(db)
        task = await service.create_download_task(
            user_id=current_user.id,
            source_url=url,
            resource_type=resource_type,
            priority=priority
        )

        return ApiResponse(
            success=True,
            data={
                "task_id": task.id,
                "status": task.status,
                "message": "下载任务已创建"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/download/batch", summary="批量创建下载任务")
async def create_batch_download_tasks(
        urls: List[str] = Query(..., description="资源URL列表"),
        resource_type: str = Query("image", description="资源类型"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """批量创建下载任务"""
    try:
        service = ResourceTransferService(db)
        tasks = []

        for url in urls:
            task = await service.create_download_task(
                user_id=current_user.id,
                source_url=url,
                resource_type=resource_type,
                priority=0
            )
            tasks.append({
                "task_id": task.id,
                "url": url,
                "status": task.status
            })

        return ApiResponse(
            success=True,
            data={
                "tasks": tasks,
                "total": len(tasks),
                "message": f"已创建 {len(tasks)} 个下载任务"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量创建任务失败: {str(e)}")


@router.get("/tasks", summary="获取下载任务列表")
async def get_download_tasks(
        status: Optional[str] = Query(None, description="状态过滤"),
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户的下载任务列表"""
    try:
        # 构建查询
        query = select(DownloadTask).where(
            DownloadTask.user_id == current_user.id
        )

        if status:
            query = query.where(DownloadTask.status == status)

        # 总数
        count_query = select(DownloadTask).where(
            DownloadTask.user_id == current_user.id
        )
        if status:
            count_query = count_query.where(DownloadTask.status == status)

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # 分页
        offset = (page - 1) * per_page
        query = query.order_by(desc(DownloadTask.created_at)).offset(offset).limit(per_page)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 序列化
        tasks_data = []
        for task in tasks:
            tasks_data.append({
                "id": task.id,
                "source_url": task.source_url,
                "resource_type": task.resource_type,
                "filename": task.filename,
                "status": task.status,
                "progress": task.progress,
                "total_size": task.total_size,
                "downloaded_size": task.downloaded_size,
                "error_message": task.error_message,
                "media_id": task.media_id,
                "retry_count": task.retry_count,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                "tasks": tasks_data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/tasks/{task_id}", summary="获取任务详情")
async def get_task_detail(
        task_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取单个任务的详细信息"""
    try:
        service = ResourceTransferService(db)
        task_data = await service.get_task_status(task_id)

        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 验证权限
        result = await db.execute(
            select(DownloadTask).where(DownloadTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task or task.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        return ApiResponse(
            success=True,
            data=task_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.post("/tasks/{task_id}/cancel", summary="取消任务")
async def cancel_task(
        task_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """取消正在进行的下载任务"""
    try:
        service = ResourceTransferService(db)
        success = await service.cancel_task(task_id, current_user.id)

        if not success:
            raise HTTPException(status_code=400, detail="无法取消任务（可能已完成或不存在）")

        return ApiResponse(
            success=True,
            message="任务已取消"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.post("/tasks/{task_id}/retry", summary="重试失败的任务")
async def retry_task(
        task_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """重试失败的下载任务"""
    try:
        # 获取任务
        result = await db.execute(
            select(DownloadTask).where(
                DownloadTask.id == task_id,
                DownloadTask.user_id == current_user.id
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.status != "failed":
            raise HTTPException(status_code=400, detail="只能重试失败的任务")

        # 重置任务状态
        from sqlalchemy import update
        from datetime import datetime

        await db.execute(
            update(DownloadTask)
            .where(DownloadTask.id == task_id)
            .values(
                status="pending",
                error_message=None,
                progress=0,
                downloaded_size=0,
                updated_at=datetime.now()
            )
        )
        await db.commit()

        return ApiResponse(
            success=True,
            message="任务已重置为待处理状态"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重试任务失败: {str(e)}")


@router.post("/process-queue", summary="处理下载队列")
async def process_download_queue(
        limit: int = Query(5, ge=1, le=20, description="同时处理的最大任务数"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    处理下载队列（通常由后台任务调用）
    
    注意：此接口仅供管理员使用
    """
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        # 获取待处理的任务
        result = await db.execute(
            select(DownloadTask)
            .where(DownloadTask.status == "pending")
            .order_by(DownloadTask.priority, DownloadTask.created_at)
            .limit(limit)
        )
        pending_tasks = result.scalars().all()

        processed = []
        for task in pending_tasks:
            service = ResourceTransferService(db)
            media = await service.execute_download(task.id)

            if media:
                processed.append({
                    "task_id": task.id,
                    "status": "completed",
                    "media_id": media.id
                })
            else:
                processed.append({
                    "task_id": task.id,
                    "status": "failed"
                })

        return ApiResponse(
            success=True,
            data={
                "processed": len(processed),
                "results": processed
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理队列失败: {str(e)}")


@router.get("/stats", summary="获取下载统计")
async def get_download_stats(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """获取用户的下载统计信息"""
    try:
        from sqlalchemy import func

        # 各状态的任务数量
        status_counts = {}
        for status in ["pending", "downloading", "completed", "failed", "cancelled"]:
            result = await db.execute(
                select(func.count(DownloadTask.id))
                .where(
                    DownloadTask.user_id == current_user.id,
                    DownloadTask.status == status
                )
            )
            status_counts[status] = result.scalar() or 0

        # 总下载量
        result = await db.execute(
            select(func.sum(DownloadTask.downloaded_size))
            .where(
                DownloadTask.user_id == current_user.id,
                DownloadTask.status == "completed"
            )
        )
        total_downloaded = result.scalar() or 0

        return ApiResponse(
            success=True,
            data={
                "status_counts": status_counts,
                "total_downloaded_bytes": total_downloaded,
                "total_downloaded_mb": round(total_downloaded / 1024 / 1024, 2)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
