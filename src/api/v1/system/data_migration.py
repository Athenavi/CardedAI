"""
数据迁移 API 端点
提供从各种平台迁移内容的接口
"""

import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.services.integrations.migration_service import migration_service
from src.auth.auth_deps import admin_required as admin_required_api
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(prefix="/migrations", tags=["data-migration"])


@router.post("/wordpress", summary="从 WordPress 迁移")
async def migrate_from_wordpress(
        file: UploadFile = File(..., description="WordPress WXR 文件"),
        download_media: bool = Form(False, description="是否下载媒体文件"),
        import_comments: bool = Form(True, description="是否导入评论"),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    从 WordPress WXR (WordPress eXtended RSS) 文件迁移内容
    
    支持导入:
    - 文章和页面
    - 分类和标签
    - 评论
    - 媒体文件（可选）
    """
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        start_time = time.time()

        # 执行迁移
        result = await migration_service.migrate_from_wordpress(
            wxr_file=tmp_path,
            db_session=db,
            user_id=current_user.id,
            options={
                'download_media': download_media,
                'import_comments': import_comments,
            }
        )

        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)

        duration = time.time() - start_time

        return {
            'success': True,
            'data': result,
            'duration_seconds': round(duration, 2),
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


@router.post("/markdown", summary="从 Markdown 文件迁移 (Jekyll/Hexo)")
async def migrate_from_markdown(
        platform: str = Form('jekyll', description="平台类型: jekyll 或 hexo"),
        # 注意：这里需要用户上传 ZIP 文件或提供目录路径
        # 简化版本，实际应该支持文件上传
        current_user: User = Depends(admin_required_api)
):
    """
    从 Jekyll 或 Hexo 的 Markdown 文件迁移
    
    自动解析 YAML Front Matter 并导入文章
    """
    return {
        'success': False,
        'message': '此功能需要上传 ZIP 文件或指定目录路径，请使用 CLI 工具',
        'cli_command': f'python scripts/cli.py migrate --platform {platform} --source /path/to/posts',
    }


@router.post("/ghost", summary="从 Ghost 迁移")
async def migrate_from_ghost(
        file: UploadFile = File(..., description="Ghost JSON 导出文件"),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    从 Ghost CMS 导出的 JSON 文件迁移
    
    支持导入文章、标签、用户等
    """
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        start_time = time.time()

        # 执行迁移
        result = await migration_service.migrate_from_ghost(
            json_file=tmp_path,
            db_session=db,
            user_id=current_user.id
        )

        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)

        duration = time.time() - start_time

        return {
            'success': True,
            'data': result,
            'duration_seconds': round(duration, 2),
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


@router.post("/json", summary="从通用 JSON 文件迁移")
async def migrate_from_json(
        file: UploadFile = File(..., description="JSON 文件"),
        field_mapping: Optional[str] = Form(None, description="字段映射 JSON 字符串"),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    从通用 JSON 文件迁移
    
    可以通过 field_mapping 指定字段映射关系
    例如: {"title": "post_title", "content": "post_body"}
    """
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        start_time = time.time()

        # 解析字段映射
        mapping = None
        if field_mapping:
            import json
            mapping = json.loads(field_mapping)

        # 执行迁移
        result = await migration_service.migrate_from_json(
            json_file=tmp_path,
            db_session=db,
            user_id=current_user.id,
            mapping=mapping
        )

        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)

        duration = time.time() - start_time

        return {
            'success': True,
            'data': result,
            'duration_seconds': round(duration, 2),
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


@router.post("/csv", summary="从 CSV 文件迁移")
async def migrate_from_csv(
        file: UploadFile = File(..., description="CSV 文件"),
        delimiter: str = Form(',', description="分隔符"),
        encoding: str = Form('utf-8', description="文件编码"),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    从 CSV 文件迁移
    
    适用于从电子表格或其他系统导出的数据
    """
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        start_time = time.time()

        # 执行迁移
        result = await migration_service.migrate_from_csv(
            csv_file=tmp_path,
            db_session=db,
            user_id=current_user.id,
            delimiter=delimiter,
            encoding=encoding
        )

        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)

        duration = time.time() - start_time

        return {
            'success': True,
            'data': result,
            'duration_seconds': round(duration, 2),
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


@router.post("/redirects", summary="生成 URL 重定向规则")
async def generate_redirects(
        old_urls: list = Form(..., description="旧URL列表 JSON"),
        output_format: str = Form('nginx', description="输出格式: nginx/apache/json"),
        current_user: User = Depends(admin_required_api)
):
    """
    生成 URL 重定向规则
    
    用于在迁移后保持旧链接可访问
    
    示例输入:
    [
        {"old": "/2020/01/old-post", "new": "/articles/new-post"},
        {"old": "/category/tech", "new": "/categories/technology"}
    ]
    """
    try:
        redirects_config = migration_service.generate_redirect_map(
            old_urls=old_urls,
            output_format=output_format
        )

        return {
            'success': True,
            'data': {
                'config': redirects_config,
                'format': output_format,
                'total_rules': len(old_urls),
            },
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


@router.get("/supported-platforms", summary="获取支持的平台列表")
async def get_supported_platforms():
    """获取所有支持的迁移平台和格式"""
    return {
        'success': True,
        'data': {
            'platforms': [
                {
                    'id': 'wordpress',
                    'name': 'WordPress',
                    'format': 'WXR/XML',
                    'description': '从 WordPress 导出的 WXR 文件迁移',
                    'supports': ['posts', 'pages', 'categories', 'tags', 'comments', 'media'],
                },
                {
                    'id': 'jekyll',
                    'name': 'Jekyll',
                    'format': 'Markdown + YAML',
                    'description': '从 Jekyll 静态博客迁移',
                    'supports': ['posts', 'categories', 'tags'],
                },
                {
                    'id': 'hexo',
                    'name': 'Hexo',
                    'format': 'Markdown + YAML',
                    'description': '从 Hexo 静态博客迁移',
                    'supports': ['posts', 'categories', 'tags'],
                },
                {
                    'id': 'ghost',
                    'name': 'Ghost',
                    'format': 'JSON',
                    'description': '从 Ghost CMS 导出的 JSON 文件迁移',
                    'supports': ['posts', 'tags', 'users'],
                },
                {
                    'id': 'json',
                    'name': '通用 JSON',
                    'format': 'JSON',
                    'description': '从任意 JSON 格式迁移',
                    'supports': ['custom'],
                },
                {
                    'id': 'csv',
                    'name': 'CSV',
                    'format': 'CSV',
                    'description': '从 CSV 文件迁移',
                    'supports': ['custom'],
                },
            ],
        },
    }


@router.get("/guide/{platform}", summary="获取迁移指南")
async def get_migration_guide(platform: str):
    """获取特定平台的详细迁移指南"""
    guides = {
        'wordpress': {
            'title': 'WordPress 迁移指南',
            'steps': [
                '1. 在 WordPress 后台导出: Tools > Export > All content',
                '2. 下载生成的 .xml 文件',
                '3. 在此页面上传该文件',
                '4. 选择是否下载媒体文件和导入评论',
                '5. 点击开始迁移',
            ],
            'tips': [
                '确保 WordPress 版本 >= 4.0',
                '大型站点建议先在测试环境迁移',
                '媒体文件下载可能需要较长时间',
                '迁移后检查 URL 重定向是否正确',
            ],
        },
        'jekyll': {
            'title': 'Jekyll 迁移指南',
            'steps': [
                '1. 找到 Jekyll 站点的 _posts 目录',
                '2. 将所有 .md 文件打包为 ZIP',
                '3. 使用 CLI 工具进行迁移',
            ],
            'cli_command': 'python scripts/cli.py migrate --platform jekyll --source _posts',
        },
        'hexo': {
            'title': 'Hexo 迁移指南',
            'steps': [
                '1. 找到 Hexo 站点的 source/_posts 目录',
                '2. 将所有 .md 文件打包为 ZIP',
                '3. 使用 CLI 工具进行迁移',
            ],
            'cli_command': 'python scripts/cli.py migrate --platform hexo --source source/_posts',
        },
        'ghost': {
            'title': 'Ghost 迁移指南',
            'steps': [
                '1. 在 Ghost 后台导出: Settings > Labs > Export',
                '2. 下载生成的 .json 文件',
                '3. 在此页面上传该文件',
                '4. 点击开始迁移',
            ],
        },
    }

    guide = guides.get(platform)
    if not guide:
        return {
            'success': False,
            'error': f'Unsupported platform: {platform}',
        }

    return {
        'success': True,
        'data': guide,
    }
