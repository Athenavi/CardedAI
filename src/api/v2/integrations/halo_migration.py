"""
Halo 博客迁移 API - V2 版本
提供完整的 Halo 博客内容迁移功能
"""
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.services.integrations.halo_import import HaloImportService
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(prefix="/halo", tags=["Halo Migration"])


@router.post("/connect", summary="连接到 Halo 博客")
async def connect_to_halo(
        halo_url: str,
        api_token: str,
        current_user: User = Depends(jwt_required)
):
    """
    测试与 Halo 博客的连接
    
    参数:
    - halo_url: Halo 博客的 URL (例如: https://your-halo-blog.com)
    - api_token: Halo API Token
    
    返回连接状态和基本信息
    """
    try:
        service = HaloImportService(halo_url=halo_url, api_token=api_token)

        # 测试获取文章列表
        result = await service.fetch_posts(page=1, size=1)

        if not result['success']:
            return ApiResponse(
                success=False,
                error=f"连接失败: {result.get('error')}"
            )

        return ApiResponse(
            success=True,
            data={
                'connected': True,
                'total_posts': result.get('total', 0),
                'halo_url': halo_url
            },
            message="成功连接到 Halo 博客"
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"连接失败: {str(e)}"
        )


@router.get("/preview", summary="预览 Halo 博客内容")
async def preview_halo_content(
        halo_url: str,
        api_token: str,
        current_user: User = Depends(jwt_required)
):
    """
    预览 Halo 博客的可迁移内容
    
    返回统计信息，包括文章数、分类数等
    """
    try:
        service = HaloImportService(halo_url=halo_url, api_token=api_token)

        # 获取文章统计
        posts_result = await service.fetch_posts(page=1, size=1)

        # 获取分类
        categories_result = await service.fetch_categories()

        # 获取标签
        tags_result = await service.fetch_tags()

        stats = {
            'total_posts': posts_result.get('total', 0) if posts_result['success'] else 0,
            'total_categories': len(categories_result.get('data', [])) if categories_result['success'] else 0,
            'total_tags': len(tags_result.get('data', [])) if tags_result['success'] else 0,
        }

        return ApiResponse(
            success=True,
            data={
                'stats': stats,
                'halo_url': halo_url
            }
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"预览失败: {str(e)}"
        )


@router.post("/import", summary="导入 Halo 博客数据")
async def import_halo_data(
        background_tasks: BackgroundTasks,
        halo_url: str,
        api_token: str,
        user_mapping: Optional[str] = None,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    从 Halo 博客导入数据到 FastBlog
    
    参数:
    - halo_url: Halo 博客的 URL
    - api_token: Halo API Token
    - user_mapping: 用户映射 JSON (可选)
    
    导入内容:
    - 文章和页面
    - 分类
    - 标签
    """
    import json

    try:
        service = HaloImportService(halo_url=halo_url, api_token=api_token)

        # 解析用户映射
        mapping_dict = {}
        if user_mapping:
            try:
                mapping_dict = json.loads(user_mapping)
            except json.JSONDecodeError:
                return ApiResponse(
                    success=False,
                    error="用户映射格式错误，请使用有效的 JSON 格式"
                )

        # 进度回调
        progress_data = {'current': 0, 'total': 0}

        def progress_callback(current, total):
            progress_data['current'] = current
            progress_data['total'] = total
            print(f"Halo 导入进度: {current}/{total}")

        # 导入数据
        import_result = await service.import_to_database(
            db_session=db,
            user_mapping=mapping_dict,
            progress_callback=progress_callback
        )

        if not import_result['success']:
            return ApiResponse(
                success=False,
                error=import_result.get('error', '导入失败'),
                data=import_result.get('results', {})
            )

        # 生成报告
        report = service.generate_import_report(import_result)

        return ApiResponse(
            success=True,
            data={
                'results': import_result['results'],
                'report': report,
                'progress': progress_data
            },
            message=f"成功导入 {import_result['results']['imported_articles']} 篇文章"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(
            success=False,
            error=f"导入失败: {str(e)}"
        )


@router.get("/guide", summary="获取 Halo 迁移指南")
async def get_halo_migration_guide():
    """
    获取 Halo 博客迁移指南
    
    返回详细的迁移步骤和注意事项
    """
    return ApiResponse(
        success=True,
        data={
            'title': 'Halo 博客迁移指南',
            'prerequisites': [
                '确保 Halo 博客正在运行且可访问',
                '获取 Halo API Token（在 Halo 后台 > 系统设置 > API 设置中生成）',
                '确保 API Token 有读取文章、分类、标签的权限'
            ],
            'steps': [
                {
                    'step': 1,
                    'title': '准备 Halo API',
                    'description': '在 Halo 后台生成 API Token，并记录 Halo 博客的 URL'
                },
                {
                    'step': 2,
                    'title': '测试连接',
                    'description': '使用 /connect 接口测试与 Halo 博客的连接'
                },
                {
                    'step': 3,
                    'title': '预览内容',
                    'description': '使用 /preview 接口查看可迁移的内容统计'
                },
                {
                    'step': 4,
                    'title': '配置映射',
                    'description': '配置作者映射（如果需要将 Halo 作者映射到 FastBlog 用户）'
                },
                {
                    'step': 5,
                    'title': '开始迁移',
                    'description': '使用 /import 接口开始迁移，系统会自动获取所有文章并导入'
                }
            ],
            'supported_content': [
                {'type': 'article', 'name': '文章', 'description': '包括标题、内容、摘要、状态等'},
                {'type': 'category', 'name': '分类', 'description': '文章分类'},
                {'type': 'tag', 'name': '标签', 'description': '文章标签'}
            ],
            'not_supported': [
                {'type': 'comments', 'name': '评论', 'reason': 'Halo 评论结构复杂，暂不支持'},
                {'type': 'media', 'name': '媒体文件', 'reason': '需要手动重新上传'},
                {'type': 'theme', 'name': '主题', 'reason': '主题配置需要手动重新设置'}
            ],
            'important_notes': [
                '迁移前建议备份当前数据库',
                '重复的文章（slug 相同）会被自动跳过',
                'URL 重定向规则会自动创建，帮助 SEO 保持连续性',
                '大型博客迁移可能需要较长时间，请耐心等待',
                'Halo API 可能有速率限制，大量文章时请注意',
                '建议在测试环境先进行迁移测试'
            ],
            'api_token_guide': {
                'title': '如何获取 Halo API Token',
                'steps': [
                    '登录 Halo 管理后台',
                    '进入 系统设置 > API 设置',
                    '点击 "生成新 Token"',
                    '选择所需的权限（至少需要读取文章、分类、标签）',
                    '复制生成的 Token 并妥善保存'
                ]
            }
        }
    )
