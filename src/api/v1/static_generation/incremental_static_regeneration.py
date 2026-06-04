"""
增量静态再生成（ISR）API端点

提供ISR管理的REST API接口
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import admin_required
from shared.services.static_generation.incremental_static_regeneration import isr_service
from shared.services.static_generation.static_site_generator import ssg_service
from src.utils.database.unified_manager import db_manager
from src.api.v1.core.responses import ApiResponse

router = APIRouter(tags=["Incremental Static Regeneration"])


@router.on_event("startup")
async def startup_isr():
    """启动时初始化ISR服务"""
    await isr_service.start()


@router.on_event("shutdown")
async def shutdown_isr():
    """关闭时停止ISR服务"""
    await isr_service.stop()


@router.get("/page/{page_path:path}", summary="获取ISR页面")
async def get_isr_page(
        page_path: str,
        revalidate_time: int = Query(60, ge=10, le=3600, description="重新验证时间（秒）"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """
    获取ISR页面（自动处理缓存和重新验证）
    
    - **page_path**: 页面路径（如 articles/2024/01/my-post.html）
    - **revalidate_time**: 重新验证时间间隔（秒）
    
    返回内容可能是：
    - 新鲜缓存（未过期）
    - 过期缓存（后台正在重新验证）
    - 新生成的内容
    """
    try:
        # 定义页面生成函数
        async def generate_page():
            # 根据路径判断页面类型并生成
            if page_path.startswith('articles/'):
                # 提取文章ID或slug
                parts = page_path.split('/')
                slug_or_id = parts[-1].replace('.html', '')

                # 尝试通过slug查询
                from shared.models.article import Article
                from sqlalchemy import select

                result = await db.execute(
                    select(Article).where(
                        (Article.slug == slug_or_id) |
                        (Article.id.cast(String) == slug_or_id)
                    )
                )
                article = result.scalar_one_or_none()

                if article:
                    return await ssg_service.generate_article_page(db, article.id, force=True)

            elif page_path.startswith('categories/'):
                # 分类页面
                parts = page_path.split('/')
                slug_or_id = parts[-1].replace('.html', '').replace('_page_', '')

                from shared.models.category import Category
                from sqlalchemy import select

                result = await db.execute(
                    select(Category).where(
                        (Category.slug == slug_or_id) |
                        (Category.id.cast(String) == slug_or_id)
                    )
                )
                category = result.scalar_one_or_none()

                if category:
                    page_num = 1
                    if '_page_' in parts[-1]:
                        page_num = int(parts[-1].split('_page_')[-1].replace('.html', ''))

                    return await ssg_service.generate_category_page(
                        db, category.id, page=page_num, force=True
                    )

            elif page_path == 'index.html':
                # 首页
                return await ssg_service.generate_homepage(db, force=True)

            return {'success': False, 'error': f'Unknown page type: {page_path}'}

        # 获取或生成页面
        result = await isr_service.get_or_generate_page(
            page_path,
            generate_page,
            revalidate_time=revalidate_time
        )

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '获取页面失败'))

        return ApiResponse(
            success=True,
            data={
                'content': result.get('content'),
                'path': result.get('path'),
                'cached': result.get('cached', False),
                'stale': result.get('stale', False),
                'is_revalidating': result.get('is_revalidating', False),
                'last_generated': result.get('last_generated'),
                'next_revalidate': result.get('next_revalidate'),
                'message': result.get('message')
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取页面失败: {str(e)}")


@router.post("/revalidate/{page_path:path}", summary="强制重新验证页面")
async def force_revalidate_page(
        page_path: str,
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """
    强制重新验证指定页面
    
    - **page_path**: 页面路径
    """
    try:
        # 定义重新生成函数
        async def regenerate_page():
            if page_path.startswith('articles/'):
                parts = page_path.split('/')
                slug_or_id = parts[-1].replace('.html', '')

                from shared.models.article import Article
                from sqlalchemy import select, String

                result = await db.execute(
                    select(Article).where(
                        (Article.slug == slug_or_id) |
                        (Article.id.cast(String) == slug_or_id)
                    )
                )
                article = result.scalar_one_or_none()

                if article:
                    return await ssg_service.generate_article_page(db, article.id, force=True)

            elif page_path == 'index.html':
                return await ssg_service.generate_homepage(db, force=True)

            return {'success': False, 'error': f'Cannot regenerate: {page_path}'}

        result = await isr_service.force_revalidate(page_path, regenerate_page)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '重新验证失败'))

        return ApiResponse(
            success=True,
            data={
                'path': result.get('path'),
                'last_generated': result.get('last_generated'),
                'next_revalidate': result.get('next_revalidate')
            },
            message='页面重新验证成功'
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"重新验证失败: {str(e)}")


@router.post("/invalidate/{page_path:path}", summary="使页面缓存失效")
async def invalidate_page(
        page_path: str,
        current_user=Depends(admin_required)
):
    """
    使指定页面的缓存失效（删除文件）
    
    - **page_path**: 页面路径
    """
    try:
        result = await isr_service.invalidate_page(page_path)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '失效操作失败'))

        return ApiResponse(
            success=True,
            message=result.get('message', '页面已失效')
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"失效操作失败: {str(e)}")


@router.post("/invalidate-pattern", summary="批量使页面失效")
async def invalidate_by_pattern(
        pattern: str = Body(..., embed=True, description="路径模式（支持*通配符）"),
        current_user=Depends(admin_required)
):
    """
    按模式批量使页面失效
    
    - **pattern**: 路径模式，如 "articles/*" 或 "categories/*.html"
    """
    try:
        result = await isr_service.invalidate_by_pattern(pattern)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '批量失效失败'))

        return ApiResponse(
            success=True,
            data={
                'invalidated_count': result.get('invalidated_count', 0),
                'pattern': pattern
            },
            message=f'已使{result.get("invalidated_count")}个页面失效'
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"批量失效失败: {str(e)}")


@router.get("/info/{page_path:path}", summary="获取页面信息")
async def get_page_info(
        page_path: str,
        current_user=Depends(admin_required)
):
    """
    获取ISR页面的详细信息
    
    - **page_path**: 页面路径
    """
    try:
        info = isr_service.get_page_info(page_path)

        if not info:
            return ApiResponse(success=False, error=f'Page not found: {page_path}')

        return ApiResponse(success=True, data=info)

    except Exception as e:
        return ApiResponse(success=False, error=f"获取信息失败: {str(e)}")


@router.get("/stats", summary="获取ISR统计信息")
async def get_isr_stats(current_user=Depends(admin_required)):
    """获取ISR服务的统计信息"""
    try:
        stats = isr_service.get_stats()
        return ApiResponse(success=True, data=stats)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.get("/config", summary="获取ISR配置")
async def get_isr_config(current_user=Depends(admin_required)):
    """获取ISR配置信息"""
    try:
        config = {
            'output_dir': str(isr_service.output_dir),
            'max_concurrent_revalidations': isr_service.max_concurrent,
            'default_revalidate_time': 60,
            'supported_page_types': [
                'articles',
                'categories',
                'homepage'
            ],
            'features': [
                'stale-while-revalidate',
                'background_regeneration',
                'concurrent_control',
                'pattern_invalidation'
            ]
        }
        return ApiResponse(success=True, data=config)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取配置失败: {str(e)}")
