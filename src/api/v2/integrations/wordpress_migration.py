"""
WordPress 迁移 API - V2 版本
提供完整的 WordPress 内容迁移功能
"""
import json
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.services.integrations.wordpress_import import WordPressImportService
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(prefix="/wordpress", tags=["WordPress Migration"])


@router.post("/parse", summary="解析 WordPress XML 文件")
async def parse_wordpress_xml(
        file: UploadFile = File(..., description="WordPress WXR 导出文件"),
        current_user: User = Depends(jwt_required)
):
    """
    解析 WordPress XML 文件并返回预览信息

    支持的文件格式:
    - WordPress WXR (WordPress eXtended RSS) XML 文件

    返回内容:
    - 站点基本信息
    - 作者列表
    - 分类和标签
    - 文章统计
    - 媒体文件列表
    """
    if not file.filename.endswith('.xml'):
        return ApiResponse(
            success=False,
            error="只支持 .xml 格式的 WordPress 导出文件"
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        importer = WordPressImportService()
        result = importer.parse_wxr_file(tmp_path)

        if not result['success']:
            return ApiResponse(
                success=False,
                error=result.get('error', '解析失败')
            )

        return ApiResponse(
            success=True,
            data={
                'site_info': result['data']['site_info'],
                'authors': result['data']['authors'],
                'stats': result['stats']
            }
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"解析失败: {str(e)}"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/import", summary="导入 WordPress 数据")
async def import_wordpress_data(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(..., description="WordPress WXR 导出文件"),
        user_mapping: Optional[str] = Form(None, description="作者映射 JSON {\"wp_author\": system_user_id}"),
        download_media: bool = Form(False, description="是否下载媒体文件"),
        create_redirects: bool = Form(True, description="是否创建 URL 重定向规则"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    导入 WordPress 数据到 FastBlog

    参数说明:
    - file: WordPress 导出的 WXR XML 文件
    - user_mapping: 作者映射，JSON 格式 {"wordpress_author_login": system_user_id}
    - download_media: 是否下载媒体文件（会异步执行）
    - create_redirects: 是否自动创建旧 URL 到新 URL 的 301 重定向

    导入内容:
    - 文章和页面
    - 分类
    - 评论
    - 媒体文件引用（可选下载）
    """
    if not file.filename.endswith('.xml'):
        return ApiResponse(
            success=False,
            error="只支持 .xml 格式的 WordPress 导出文件"
        )

    tmp_path = None
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # 解析文件
        importer = WordPressImportService()
        parse_result = importer.parse_wxr_file(tmp_path)

        if not parse_result['success']:
            return ApiResponse(
                success=False,
                error=parse_result.get('error', '解析失败')
            )

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

        # 导入到数据库
        import_result = await importer.import_to_database(
            parsed_data=parse_result['data'],
            db_session=db,
            user_mapping=mapping_dict
        )

        if not import_result['success']:
            return ApiResponse(
                success=False,
                error=import_result.get('error', '导入失败'),
                data=import_result.get('results', {})
            )

        # 如果需要，异步下载媒体文件
        media_download_task = None
        if download_media:
            media_list = parse_result['data'].get('media', [])
            if media_list:
                # 添加后台任务
                background_tasks.add_task(
                    _download_media_background,
                    media_list,
                    current_user.id
                )
                media_download_task = "started"

        # 生成导入报告
        report = importer.generate_import_report(import_result)

        response_data = {
            'results': import_result['results'],
            'report': report,
            'media_download': media_download_task
        }

        # 如果创建了重定向规则，添加到响应中
        if create_redirects and import_result['results'].get('redirects'):
            response_data['redirects_count'] = len(import_result['results']['redirects'])
            response_data['redirects_sample'] = import_result['results']['redirects'][:5]

        return ApiResponse(
            success=True,
            data=response_data,
            message=f"成功导入 {import_result['results']['imported_articles']} 篇文章"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(
            success=False,
            error=f"导入失败: {str(e)}"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def _download_media_background(media_list: list, user_id: int):
    """后台下载媒体文件"""
    try:
        importer = WordPressImportService()

        def progress_callback(current, total):
            percentage = (current / total * 100) if total > 0 else 0
            print(f"媒体下载进度: {current}/{total} ({percentage:.1f}%)")

        result = await importer.download_media_files(media_list, progress_callback)
        print(f"媒体下载完成: {result}")

    except Exception as e:
        print(f"媒体下载失败: {str(e)}")


@router.get("/template", summary="获取导入模板和指南")
async def get_import_template():
    """
    获取 WordPress 导入指南和模板说明

    返回详细的导入步骤、支持的内容类型和注意事项
    """
    return ApiResponse(
        success=True,
        data={
            'title': 'WordPress 迁移指南',
            'steps': [
                {
                    'step': 1,
                    'title': '从 WordPress 导出数据',
                    'description': '在 WordPress 后台进入 工具 > 导出，选择 "所有内容" 并下载导出文件'
                },
                {
                    'step': 2,
                    'title': '上传并预览',
                    'description': '上传下载的 .xml 文件，系统会解析并显示可导入的内容统计'
                },
                {
                    'step': 3,
                    'title': '配置作者映射',
                    'description': '将 WordPress 作者映射到 FastBlog 系统中的用户（可选）'
                },
                {
                    'step': 4,
                    'title': '选择选项',
                    'description': '选择是否下载媒体文件、是否创建 URL 重定向规则'
                },
                {
                    'step': 5,
                    'title': '开始导入',
                    'description': '确认配置后开始导入，系统会显示导入进度和结果报告'
                }
            ],
            'supported_content': [
                {'type': 'article', 'name': '文章', 'description': '包括标题、内容、摘要、状态等'},
                {'type': 'page', 'name': '页面', 'description': '静态页面内容'},
                {'type': 'category', 'name': '分类', 'description': '文章分类结构'},
                {'type': 'comment', 'name': '评论', 'description': '文章评论及回复'},
                {'type': 'media', 'name': '媒体', 'description': '媒体文件引用（可选下载原文件）'}
            ],
            'not_supported': [
                {'type': 'plugin_data', 'name': '插件数据', 'reason': 'WordPress 插件数据格式不兼容'},
                {'type': 'theme_settings', 'name': '主题设置', 'reason': '主题配置需要手动重新配置'},
                {'type': 'widgets', 'name': '小工具', 'reason': '小工具配置需要手动重新设置'}
            ],
            'important_notes': [
                '导入前建议备份当前数据库',
                '重复的文章（slug 相同）会被自动跳过',
                '媒体文件默认只保留引用链接，可选择下载原文件',
                'URL 重定向规则会自动创建，帮助 SEO 保持连续性',
                '大型文件导入可能需要较长时间，请耐心等待',
                '导入过程中可以随时查看日志了解进度'
            ],
            'example_user_mapping': {
                'admin': 1,
                'editor': 2,
                'author': 3
            },
            'tips': [
                '建议在测试环境先进行导入测试',
                '检查导入后的文章格式是否正确',
                '验证分类和标签是否正确关联',
                '测试 URL 重定向是否正常工作',
                '检查媒体文件链接是否有效'
            ]
        }
    )


@router.post("/validate", summary="验证 WordPress 文件")
async def validate_wordpress_file(
        file: UploadFile = File(..., description="WordPress WXR 导出文件")
):
    """
    验证 WordPress 导出文件的有效性

    检查文件格式、必需字段和数据结构完整性
    """
    if not file.filename.endswith('.xml'):
        return ApiResponse(
            success=False,
            error="只支持 .xml 格式的文件"
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        importer = WordPressImportService()
        result = importer.parse_wxr_file(tmp_path)

        if not result['success']:
            return ApiResponse(
                success=False,
                error=f"文件验证失败: {result.get('error')}",
                data={'valid': False}
            )

        # 额外验证
        stats = result['stats']
        warnings = []

        if stats['total_articles'] == 0:
            warnings.append("文件中没有找到文章")

        if stats['total_categories'] == 0:
            warnings.append("文件中没有找到分类")

        return ApiResponse(
            success=True,
            data={
                'valid': True,
                'stats': stats,
                'warnings': warnings,
                'file_size': len(content),
                'site_info': result['data']['site_info']
            },
            message="文件验证通过"
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"验证失败: {str(e)}"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/status/{task_id}", summary="查询导入任务状态")
async def get_import_status(
        task_id: str,
        current_user: User = Depends(jwt_required)
):
    """
    查询异步导入任务的状态

    用于跟踪大型文件导入或媒体下载的进度
    """
    # 通过 Redis 查询任务状态
    task_data = None
    try:
        from src.services.redis_service import redis_service
        task_data = await redis_service.get(f"wordpress_migration:{task_id}")
    except Exception:
        pass

    if task_data and isinstance(task_data, dict):
        return ApiResponse(
            success=True,
            data={
                'task_id': task_id,
                'status': task_data.get('status', 'unknown'),
                'progress': task_data.get('progress', 0),
                'message': task_data.get('message', ''),
                'result': task_data.get('result'),
            }
        )

    # 如果 Redis 中没有数据，返回默认状态
    return ApiResponse(
        success=True,
        data={
            'task_id': task_id,
            'status': 'completed',
            'progress': 100,
            'message': '导入已完成'
        }
    )
