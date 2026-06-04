"""
P8-3: 备份管理 API
提供备份创建、恢复、列表查询等功能
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from shared.services.ops.backup_manager import backup_manager
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from shared.models.user import User

router = APIRouter(prefix="/backup", tags=["Backup Management"])


@router.post("/database")
async def create_database_backup(
        backup_type: str = Query("daily", regex="^(daily|weekly|monthly)$"),
        current_user: User = Depends(jwt_required)
):
    """
    P8-3: 创建数据库备份
    
    Args:
        backup_type: 备份类型 (daily/weekly/monthly)
        
    Returns:
        备份信息
    """
    result = await backup_manager.create_database_backup(backup_type)

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', '备份失败'))

    return result


@router.post("/files")
async def create_files_backup(current_user: User = Depends(jwt_required)):
    """
    P8-3: 创建文件备份
    
    Returns:
        备份信息
    """
    result = await backup_manager.create_files_backup()

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', '备份失败'))

    return result


@router.post("/restore/{backup_filename}")
async def restore_database_backup(
        backup_filename: str,
        confirmation: bool = False,
        current_user: User = Depends(jwt_required)
):
    """
    P8-3: 恢复数据库备份
    
    Args:
        backup_filename: 备份文件名
        confirmation: 确认恢复（必须为 True）
        
    Returns:
        恢复结果
    """
    if not confirmation:
        raise HTTPException(
            status_code=400,
            detail="需要确认恢复操作。请设置 confirmation=true"
        )

    result = await backup_manager.restore_database_backup(backup_filename)

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', '恢复失败'))

    return result


@router.get("/list")
async def list_backups(
        limit: int = Query(20, ge=1, le=100),
        current_user: User = Depends(jwt_required)
):
    """
    P8-3: 列出备份文件
    
    Args:
        limit: 返回数量限制
        
    Returns:
        备份文件列表
    """
    backups = backup_manager.list_backups(limit)

    return {
        "backups": backups,
        "total": len(backups)
    }


@router.delete("/{backup_filename}")
async def delete_backup(
        backup_filename: str,
        current_user: User = Depends(jwt_required)
):
    """
    P8-3: 删除备份文件
    
    Args:
        backup_filename: 备份文件名
        
    Returns:
        删除结果
    """
    from pathlib import Path

    backup_path = backup_manager.backup_dir / backup_filename

    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")

    backup_path.unlink()

    return {
        "success": True,
        "message": f"备份文件已删除: {backup_filename}"
    }
