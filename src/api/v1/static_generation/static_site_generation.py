"""
静态页面生成（SSG）API端点

提供静态站点生成的REST API接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.static_generation.static_site_generator import ssg_service
from src.api.v1.core.responses import ApiResponse
from src.auth import admin_required
from src.utils.database.unified_manager import db_manager

router = APIRouter(tags=["Static Site Generation"])


@router.post("/articles/{article_id}", summary="生成文章静态页面")
async def generate_article_page(
        article_id: int,
        force: bool = Query(False, description="是否强制重新生成"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """
    生成单个文章的静态页面
    
    - **article_id**: 文章ID
    - **force**: 是否强制重新生成（忽略缓存）
    """
    try:
        result = await ssg_service.generate_article_page(db, article_id, force)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '生成失败'))

        return ApiResponse(
            success=True,
            data={
                'article_id': article_id,
                'path': result.get('path'),
                'url': result.get('url'),
                'cached': result.get('cached', False)
            },
            message='静态页面生成成功'
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"生成失败: {str(e)}")


@router.post("/categories/{category_id}", summary="生成分类列表页")
async def generate_category_page(
        category_id: int,
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        force: bool = Query(False, description="是否强制重新生成"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """
    生成分类列表页的静态页面
    
    - **category_id**: 分类ID
    - **page**: 页码
    - **per_page**: 每页文章数量
    - **force**: 是否强制重新生成
    """
    try:
        result = await ssg_service.generate_category_page(db, category_id, page, per_page, force)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '生成失败'))

        return ApiResponse(
            success=True,
            data={
                'category_id': category_id,
                'page': page,
                'path': result.get('path'),
                'url': result.get('url'),
                'cached': result.get('cached', False)
            },
            message='分类页面生成成功'
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"生成失败: {str(e)}")


@router.post("/homepage", summary="生成首页")
async def generate_homepage(
        per_page: int = Query(20, ge=1, le=100, description="显示文章数量"),
        force: bool = Query(False, description="是否强制重新生成"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """
    生成首页静态页面
    
    - **per_page**: 首页显示的文章数量
    - **force**: 是否强制重新生成
    """
    try:
        result = await ssg_service.generate_homepage(db, per_page, force)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '生成失败'))

        return ApiResponse(
            success=True,
            data={
                'path': result.get('path'),
                'url': result.get('url'),
                'cached': result.get('cached', False)
            },
            message='首页生成成功'
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"生成失败: {str(e)}")


@router.post("/articles/batch", summary="批量生成所有文章")
async def generate_all_articles(
        batch_size: int = Query(50, ge=1, le=200, description="批次大小"),
        force: bool = Query(False, description="是否强制重新生成"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """
    批量生成所有已发布文章的静态页面
    
    - **batch_size**: 每批处理的文章数量
    - **force**: 是否强制重新生成所有文章
    """
    try:
        result = await ssg_service.generate_all_articles(db, batch_size, force)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '批量生成失败'))

        return ApiResponse(
            success=True,
            data={
                'total': result.get('total', 0),
                'generated': result.get('generated', 0),
                'cached': result.get('cached', 0),
                'failed': result.get('failed', 0)
            },
            message=f"批量生成完成，共{result.get('total')}篇文章"
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"批量生成失败: {str(e)}")


@router.delete("/clean", summary="清理旧的静态文件")
async def clean_old_files(
        max_age_days: int = Query(30, ge=1, le=365, description="最大保留天数"),
        current_user=Depends(admin_required)
):
    """
    清理超过指定天数的静态文件
    
    - **max_age_days**: 文件最大保留天数
    """
    try:
        result = await ssg_service.clean_old_files(max_age_days)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '清理失败'))

        return ApiResponse(
            success=True,
            data={
                'cleaned_count': result.get('cleaned_count', 0)
            },
            message=f"清理了{result.get('cleaned_count')}个旧文件"
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"清理失败: {str(e)}")


@router.get("/stats", summary="获取生成统计")
async def get_generation_stats(current_user=Depends(admin_required)):
    """获取静态页面生成统计信息"""
    try:
        stats = ssg_service.get_generation_stats()
        return ApiResponse(success=True, data=stats)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.get("/config", summary="获取配置信息")
async def get_config(current_user=Depends(admin_required)):
    """获取SSG配置信息"""
    try:
        config = {
            'output_dir': str(ssg_service.output_dir),
            'template_dir': str(ssg_service.template_dir),
            'cache_enabled': True,
            'cache_ttl_hours': 24,
            'batch_size_default': 50,
            'supported_pages': [
                'article',
                'category',
                'homepage'
            ]
        }
        return ApiResponse(success=True, data=config)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取配置失败: {str(e)}")
