"""
评论配置API端点
用于Next.js前端访问评论配置功能
"""
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import SystemSettings
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter()


@router.get("")
async def get_comment_config(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取评论配置
    """
    try:
        # 检查用户权限 - 只有管理员可以访问
        if not getattr(current_user, 'is_superuser', False):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "权限不足"
                }
            )

        # 获取所有评论相关的系统设置
        comment_settings = db.query(SystemSettings).filter(
            SystemSettings.key.like('giscus_%')
        ).all()

        # 转换为字典格式
        config = {setting.key: setting.value for setting in comment_settings}

        # 如果没有任何配置，返回默认值
        if not config:
            config = {
                'giscus_repo': '',
                'giscus_repo_id': '',
                'giscus_category': '',
                'giscus_category_id': '',
                'giscus_mapping': 'pathname',
                'giscus_strict': '0',
                'giscus_reactions_enabled': '1',
                'giscus_emit_metadata': '0',
                'giscus_input_position': 'top',
                'giscus_theme': 'preferred_color_scheme',
                'giscus_lang': 'zh-CN',
                'giscus_loading': 'lazy'
            }

        return ApiResponse(
            success=True,
            data=config
        )
    except HTTPException as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": e.detail
            }
        )
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@router.post("")
async def update_comment_config(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新评论配置
    """
    try:
        # 检查用户权限 - 只有管理员可以访问
        if not getattr(current_user, 'is_superuser', False):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "权限不足"
                }
            )

        data = await request.json()

        # 验证必需字段
        required_fields = ['giscus_repo', 'giscus_mapping', 'giscus_theme']
        for field in required_fields:
            if field not in data:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": f"缺少必需字段: {field}"
                    }
                )

        from sqlalchemy import select

        # 更新或创建评论配置
        for key, value in data.items():
            if key.startswith('giscus_'):  # 确保只更新giscus相关的设置
                setting_query = select(SystemSettings).where(SystemSettings.key == key)
                setting_result = await db.execute(setting_query)
                setting = setting_result.scalar_one_or_none()

                if setting:
                    setting.value = str(value)  # 确保值是字符串
                    setting.updated_at = datetime.now()
                    setting.updated_by = current_user.id
                else:
                    setting = SystemSettings(
                        key=key,
                        value=str(value),
                        updated_at=datetime.now(),
                        updated_by=current_user.id
                    )
                    db.add(setting)

        await db.commit()

        return ApiResponse(
            success=True,
            data={"message": "评论配置更新成功"}
        )
    except HTTPException as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": e.detail
            }
        )
    except Exception as e:
        await db.rollback()
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )
