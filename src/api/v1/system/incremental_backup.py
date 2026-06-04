"""
增量备份 API 端点
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.system.incremental_backup_service import incremental_backup_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["Incremental Backup"])


@router.post("/create")
async def create_incremental_backup(
        request: Request,
        current_user=Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建增量备份
    
    Body参数:
        base_backup_id: 基础备份ID（可选，默认使用最新完整备份）
        tables: 要备份的表列表（可选，默认全部）
    """
    try:
        body = await request.json()
        base_backup_id = body.get('base_backup_id')
        tables = body.get('tables')

        # 获取数据库配置
        import os
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'fast_blog'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
        }

        result = await incremental_backup_service.create_incremental_backup(
            db_config,
            base_backup_id,
            tables
        )

        if result['success']:
            return ApiResponse(
                success=True,
                data=result,
                message=result.get('message', '增量备份创建成功')
            )
        else:
            return ApiResponse(
                success=False,
                error=result.get('error', '未知错误')
            )

    except Exception as e:
        import traceback
        print(f"Error creating incremental backup: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/create-differential")
async def create_differential_backup(
        request: Request,
        current_user=Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建差异备份
    
    Body参数:
        base_backup_id: 基础备份ID（可选，默认使用最新完整备份）
        tables: 要备份的表列表（可选，默认全部）
    """
    try:
        body = await request.json()
        base_backup_id = body.get('base_backup_id')
        tables = body.get('tables')

        # 获取数据库配置
        import os
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'fast_blog'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
        }

        result = await incremental_backup_service.create_differential_backup(
            db_config,
            base_backup_id,
            tables
        )

        if result['success']:
            return ApiResponse(
                success=True,
                data=result,
                message=result.get('message', '差异备份创建成功')
            )
        else:
            return ApiResponse(
                success=False,
                error=result.get('error', '未知错误')
            )

    except Exception as e:
        import traceback
        print(f"Error creating differential backup: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/restore")
async def restore_incremental_backup(
        request: Request,
        current_user=Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    恢复增量备份链
    
    Body参数:
        target_backup_id: 目标备份ID
    """
    try:

        body = await request.json()
        target_backup_id = body.get('target_backup_id')

        if not target_backup_id:
            return ApiResponse(success=False, error='target_backup_id is required')

        # 获取备份链
        backup_chain = incremental_backup_service.get_backup_chain(target_backup_id)
        if not backup_chain:
            return ApiResponse(success=False, error=f'无法找到备份链: {target_backup_id}')

        # 获取数据库配置
        import os
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'fast_blog'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
        }

        result = await incremental_backup_service.restore_incremental_backup(
            backup_chain,
            db_config
        )

        if result['success']:
            return ApiResponse(
                success=True,
                data=result,
                message=result.get('message', '备份恢复成功')
            )
        else:
            return ApiResponse(
                success=False,
                error=result.get('error', '恢复失败'),
                data={'restored_so_far': result.get('restored_so_far', [])}
            )

    except Exception as e:
        import traceback
        print(f"Error restoring incremental backup: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/statistics")
async def get_backup_statistics(
        current_user=Depends(admin_required_api)
):
    """
    获取备份统计信息
    """
    try:

        stats = incremental_backup_service.get_backup_statistics()

        return ApiResponse(
            success=True,
            data=stats
        )

    except Exception as e:
        import traceback
        print(f"Error getting backup statistics: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/chain/{backup_id}")
async def get_backup_chain(
        backup_id: str,
        current_user=Depends(admin_required_api)
):
    """
    获取恢复到指定备份所需的备份链
    
    Args:
        backup_id: 备份ID
    """
    try:

        chain = incremental_backup_service.get_backup_chain(backup_id)

        if not chain:
            return ApiResponse(
                success=False,
                error=f'无法找到备份链: {backup_id}'
            )

        # 获取每个备份的详细信息
        chain_details = []
        for bid in chain:
            backup_info = incremental_backup_service.metadata.get(bid)
            if backup_info:
                chain_details.append({
                    'id': bid,
                    'type': backup_info.get('type'),
                    'filename': backup_info.get('filename'),
                    'created_at': backup_info.get('created_at')
                })

        return ApiResponse(
            success=True,
            data={
                'backup_id': backup_id,
                'chain': chain_details,
                'chain_length': len(chain)
            }
        )

    except Exception as e:
        import traceback
        print(f"Error getting backup chain: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/cleanup")
async def cleanup_old_backups(
        request: Request,
        current_user=Depends(admin_required_api)
):
    """
    清理旧备份
    
    Body参数:
        keep_days: 保留天数（默认30天）
    """
    try:

        body = await request.json()
        keep_days = body.get('keep_days', 30)

        result = incremental_backup_service.cleanup_old_backups(keep_days)

        return ApiResponse(
            success=True,
            data=result,
            message=result.get('message', '清理完成')
        )

    except Exception as e:
        import traceback
        print(f"Error cleaning up old backups: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
