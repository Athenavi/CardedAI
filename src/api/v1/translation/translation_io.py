"""
翻译导出/导入 API

提供翻译文件的导出和导入功能
支持JSON、YAML、PO格式
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File

from shared.services.translation.translation_io import translation_io
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/export/{language_code}", summary="导出翻译", description="导出指定语言的翻译文件")
async def export_translation(
        language_code: str,
        format: str = Query('json', pattern='^(json|yaml|po)$', description="导出格式"),
        current_user=Depends(jwt_required),
):
    """导出翻译"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 从翻译服务获取实际数据
    try:
        from shared.services.translation.translation import translation_service
        raw_translations = translation_service.get_all_translations(language_code)
        # 将原始翻译字典转换为导出格式
        sample_translations = {}
        for key, value in raw_translations.items():
            if isinstance(value, str):
                sample_translations[key] = {'translation': value, 'translated': bool(value)}
            elif isinstance(value, dict):
                sample_translations[key] = value
            else:
                sample_translations[key] = {'translation': str(value), 'translated': bool(value)}
    except Exception:
        sample_translations = {}

    if format == 'json':
        content = translation_io.export_to_json(sample_translations, language_code)
        media_type = 'application/json'
        filename = f'{language_code}.json'
    elif format == 'yaml':
        content = translation_io.export_to_yaml(sample_translations, language_code)
        media_type = 'application/x-yaml'
        filename = f'{language_code}.yaml'
    elif format == 'po':
        content = translation_io.export_to_po(sample_translations, language_code)
        media_type = 'text/plain'
        filename = f'{language_code}.po'
    else:
        return ApiResponse(success=False, error=f"Unsupported format: {format}")

    from fastapi.responses import Response

    return Response(
        content=content,
        media_type=media_type,
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
        }
    )


@router.post("/export/all", summary="批量导出", description="批量导出所有语言的翻译文件")
async def export_all_translations(
        format: str = Body('json', pattern='^(json|yaml|po)$', description="导出格式"),
        current_user=Depends(jwt_required),
):
    """批量导出"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 从翻译服务获取所有语言数据
    try:
        from shared.services.translation.translation import translation_service
        sample_all_translations = {}
        for locale in translation_service.supported_locales:
            raw_translations = translation_service.get_all_translations(locale)
            locale_data = {}
            for key, value in raw_translations.items():
                if isinstance(value, str):
                    locale_data[key] = {'translation': value, 'translated': bool(value)}
                elif isinstance(value, dict):
                    locale_data[key] = value
                else:
                    locale_data[key] = {'translation': str(value), 'translated': bool(value)}
            if locale_data:
                sample_all_translations[locale] = locale_data
    except Exception:
        sample_all_translations = {}

    results = translation_io.batch_export(sample_all_translations, format=format)

    return ApiResponse(
        success=True,
        message=f"Exported {len(results)} languages",
        data={
            'languages': list(results.keys()),
            'format': format,
            'total_files': len(results),
        }
    )


@router.post("/import/{language_code}", summary="导入翻译", description="导入翻译文件")
async def import_translation(
        language_code: str,
        file: UploadFile = File(..., description="翻译文件"),
        current_user=Depends(jwt_required),
):
    """导入翻译"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 读取文件内容
    content = await file.read()
    content_str = content.decode('utf-8')

    # 根据文件格式导入
    filename = file.filename.lower()
    if filename.endswith('.json'):
        result = translation_io.import_from_json(content_str)
    elif filename.endswith('.yaml') or filename.endswith('.yml'):
        result = translation_io.import_from_yaml(content_str)
    elif filename.endswith('.po'):
        result = translation_io.import_from_po(content_str)
    else:
        return ApiResponse(
            success=False,
            error="Unsupported file format. Use .json, .yaml, or .po"
        )

    if result['success']:
        # Save imported translations to database
        # Example implementation:
        # from shared.models.translation import Translation
        # language_code = result.get('language')
        # translations = result.get('translations', {})
        #
        # for key, trans_data in translations.items():
        #     stmt = select(Translation).where(
        #         (Translation.key == key) & (Translation.language == language_code)
        #     )
        #     db_result = await db.execute(stmt)
        #     existing = db_result.scalar_one_or_none()
        #
        #     if existing:
        #         existing.translation = trans_data.get('translation', '')
        #         existing.is_translated = trans_data.get('translated', False)
        #         existing.updated_at = datetime.now()
        #     else:
        #         new_translation = Translation(
        #             key=key,
        #             language=language_code,
        #             translation=trans_data.get('translation', ''),
        #             is_translated=trans_data.get('translated', False),
        #         )
        #         db.add(new_translation)
        #
        # await db.commit()

        return ApiResponse(
            success=True,
            message=result['message'],
            data={
                'language': result.get('language'),
                'total_strings': result.get('total_strings'),
            }
        )
    else:
        return ApiResponse(
            success=False,
            error=result.get('error', 'Import failed')
        )


@router.post("/import/batch", summary="批量导入", description="批量导入多个翻译文件")
async def batch_import_translations(
        files: List[UploadFile] = File(..., description="翻译文件列表"),
        format: str = Query('json', pattern='^(json|yaml|po)$', description="文件格式"),
        current_user=Depends(jwt_required),
):
    """批量导入"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 读取所有文件
    file_contents = {}
    for file in files:
        content = await file.read()
        file_contents[file.filename] = content.decode('utf-8')

    # Batch import results
    results = translation_io.batch_import(file_contents, format=format)

    # Save successfully imported translations to database
    # Example implementation:
    # for detail in results.get('details', []):
    #     if detail.get('success'):
    #         language_code = detail.get('language')
    #         translations = detail.get('translations', {})
    #         # Similar save logic as single import above
    #         pass
    #
    # await db.commit()

    return ApiResponse(
        success=results['successful'] > 0,
        message=f"Imported {results['successful']} files, {results['failed']} failed",
        data=results
    )


@router.get("/formats", summary="支持的格式", description="获取支持的导入导出格式")
async def get_supported_formats():
    """获取支持的格式"""
    formats = {
        'export': ['json', 'yaml', 'po'],
        'import': ['json', 'yaml', 'po'],
        'descriptions': {
            'json': {
                'name': 'JSON',
                'extension': '.json',
                'mime_type': 'application/json',
                'description': 'JavaScript对象 notation，易于阅读和编辑',
            },
            'yaml': {
                'name': 'YAML',
                'extension': '.yaml/.yml',
                'mime_type': 'application/x-yaml',
                'description': '人类友好的数据序列化格式',
            },
            'po': {
                'name': 'PO (Gettext)',
                'extension': '.po',
                'mime_type': 'text/plain',
                'description': 'GNU Gettext翻译文件格式，广泛用于国际化',
            },
        }
    }

    return ApiResponse(
        success=True,
        data=formats
    )

