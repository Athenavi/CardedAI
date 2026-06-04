"""
WordPress 导入 API 端点
"""

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import User
from shared.services.integrations.wordpress_import import WordPressImportService
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["wordpress-import"])


@router.post("/parse")
async def parse_wordpress_xml(
        file: UploadFile = File(...),
        current_user: User = Depends(jwt_required)
):
    """
    解析 WordPress XML 文件
    
    Args:
        file: 上传的 WXR 文件
        
    Returns:
        解析结果和统计信息
    """
    try:


        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # 解析文件
            from shared.services.integrations.wordpress_import import WordPressImportService
            importer = WordPressImportService()
            result = importer.parse_wxr_file(tmp_path)

            if not result['success']:
                return JSONResponse(
                    status_code=400,
                    content={
                        'success': False,
                        'error': result.get('error', '解析失败')
                    }
                )

            return {
                'success': True,
                'data': result['data'],
                'stats': result['stats']
            }

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        import traceback
        print(f"Error parsing WordPress XML: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )


@router.post("/import")
async def import_wordpress_data(
        file: UploadFile = File(...),
        user_mapping: Optional[str] = Form(None),
        download_media: bool = Form(False),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    导入 WordPress 数据到数据库
    
    Args:
        file: 上传的 WXR 文件
        user_mapping: 作者映射 JSON 字符串 {"wp_author_id": system_user_id}
        download_media: 是否下载媒体文件
        
    Returns:
        导入结果
    """
    try:
        import json

        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # 解析文件
            importer = WordPressImportService()
            parse_result = importer.parse_wxr_file(tmp_path)

            if not parse_result['success']:
                return JSONResponse(
                    status_code=400,
                    content={
                        'success': False,
                        'error': parse_result.get('error', '解析失败')
                    }
                )

            # 解析用户映射
            mapping_dict = {}
            if user_mapping:
                try:
                    mapping_dict = json.loads(user_mapping)
                except:
                    pass

            # 导入到数据库
            import_result = await importer.import_to_database(
                parsed_data=parse_result['data'],
                db_session=db,
                user_mapping=mapping_dict
            )

            # 如果需要，下载媒体文件
            if download_media and import_result['success']:
                media_list = parse_result['data'].get('media', [])
                if media_list:
                    media_result = await importer.download_media_files(media_list)
                    import_result['media_download'] = media_result

            # 生成导入报告
            report = importer.generate_import_report(import_result)
            import_result['report'] = report

            return import_result

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        import traceback
        print(f"Error importing WordPress data: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )


@router.get("/template")
async def get_import_template():
    """
    获取导入模板和说明
    
    Returns:
        导入指南
    """
    return {
        'success': True,
        'data': {
            'instructions': [
                '1. 在 WordPress 后台进入 工具 > 导出',
                '2. 选择 "所有内容" 并下载导出文件',
                '3. 上传下载的 .xml 文件到这里',
                '4. 预览导入内容',
                '5. 配置作者映射(可选)',
                '6. 开始导入'
            ],
            'supported_content': [
                '文章(Post)',
                '页面(Page)',
                '分类(Categories)',
                '标签(Tags)',
                '评论(Comments)',
                '媒体引用(Media references)'
            ],
            'notes': [
                '媒体文件不会自动下载,仅保留引用链接',
                '需要手动重新上传媒体文件或使用媒体迁移工具',
                '导入前建议备份当前数据',
                '重复的文章(slug相同)会被跳过'
            ]
        }
    }
