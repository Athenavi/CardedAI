"""
数据库迁移管理API
提供迁移执行、状态查询等功能
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.services.system.migration_manager import migration_manager
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api
from src.extensions import get_async_db_session as get_async_db

router = APIRouter()


@router.get("/status",
            summary="获取迁移状态",
            description="查看当前数据库版本和待处理迁移(仅管理员)",
            response_description="返回迁移状态")
async def migration_status_api(
        request: Request,
        current_user: User = Depends(admin_required_api)
):
    """
    迁移状态API
    """
    try:
        status = migration_manager.get_migration_status()
        
        return ApiResponse(
            success=True,
            data=status
        )
    except Exception as e:
        import traceback
        print(f"Error in migration_status_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/apply",
             summary="执行迁移",
             description="执行所有待处理的数据库迁移(仅管理员)",
             response_description="返回执行结果")
async def apply_migrations_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    执行迁移API
    """
    try:
        result = await migration_manager.apply_all_migrations(db)
        
        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message'],
                data={
                    'applied_count': result['applied_count'],
                    'total_pending': result['total_pending'],
                    'results': result['results'],
                }
            )
        else:
            return ApiResponse(
                success=False,
                error=result.get('message', 'Migration failed'),
                data=result
            )
    except Exception as e:
        import traceback
        print(f"Error in apply_migrations_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/create",
             summary="创建迁移文件",
             description="生成新的Alembic迁移文件(仅管理员)",
             response_description="返回文件路径")
async def create_migration_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    创建迁移文件API
    
    Request Body:
    {
        "message": "Add user avatar column",
        "autogenerate": false
    }
    """
    try:
        message = data.get('message', '')
        autogenerate = data.get('autogenerate', False)
        
        if not message:
            return ApiResponse(success=False, error='缺少迁移描述')
        
        result = migration_manager.create_migration(message, autogenerate)
        
        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message'],
                data={
                    'file': result.get('file'),
                }
            )
        else:
            return ApiResponse(success=False, error=result.get('error', '创建失败'))
    except Exception as e:
        import traceback
        print(f"Error in create_migration_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/rollback",
             summary="回滚迁移",
             description="回滚指定步数的迁移(仅管理员)",
             response_description="返回回滚结果")
async def rollback_migration_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    回滚迁移API
    
    Request Body:
    {
        "steps": 1
    }
    """
    try:
        steps = data.get('steps', 1)
        
        result = migration_manager.rollback_migration(steps)
        
        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message']
            )
        else:
            return ApiResponse(success=False, error=result.get('error', '回滚失败'))
    except Exception as e:
        import traceback
        print(f"Error in rollback_migration_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/info",
            summary="迁移系统信息",
            description="获取 Alembic 迁移系统配置和功能说明",
            response_description="返回系统信息")
async def migration_info_api(request: Request):
    """
    迁移系统信息API
    """
    return ApiResponse(
        success=True,
        data={
            'enabled': True,
            'backend': 'alembic',
            'features': [
                '自动迁移检测',
                '版本管理',
                '迁移文件生成',
                '回滚支持',
                '自动生成(autogenerate)',
            ],
            'config': {
                'alembic_ini': str(migration_manager.alembic_ini),
                'migrations_dir': str(migration_manager.migrations_dir),
                'versions_dir': str(migration_manager.versions_dir),
            },
            'usage': {
                'apply': 'POST /api/v1/migrations/apply - 执行所有待处理迁移 (alembic upgrade head)',
                'status': 'GET /api/v1/migrations/status - 查看迁移状态',
                'create': 'POST /api/v1/migrations/create - 创建迁移文件',
                'rollback': 'POST /api/v1/migrations/rollback - 回滚迁移 (指定步数)',
                'cli_upgrade': 'alembic upgrade head - CLI执行迁移',
                'cli_downgrade': 'alembic downgrade -1 - CLI回滚一步',
                'cli_history': 'alembic history - 查看迁移历史',
                'cli_current': 'alembic current - 查看当前版本',
            },
            'environment_variables': {
                'DATABASE_URL': '完整数据库URL (最高优先级)',
                'DB_ENGINE': '数据库引擎 (postgresql/sqlite)',
                'DB_NAME': '数据库名称',
                'DB_USER': '数据库用户名',
                'DB_PASSWORD': '数据库密码',
                'DB_HOST': '数据库主机',
                'DB_PORT': '数据库端口',
            },
        }
    )
