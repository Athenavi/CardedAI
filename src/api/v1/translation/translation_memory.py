"""
翻译记忆API
提供翻译记忆的增删改查和相似度匹配功能
"""
import json
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, Body

from src.api.v1.core.responses import ApiResponse
from shared.models.user import User
from shared.services.translation.translation_manager.translation_memory import translation_memory_service
from src.auth.auth_deps import admin_required as admin_required_api

router = APIRouter()


@router.post("/add",
             summary="添加翻译",
             description="添加原文-译文对到翻译记忆库(仅管理员)",
             response_description="返回操作结果")
async def add_translation_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    添加翻译API
    
    Request Body:
    {
        "source_text": "Hello",
        "target_text": "你好",
        "source_lang": "en",
        "target_lang": "zh-CN",
        "context": "greeting"
    }
    """
    try:
        source_text = data.get('source_text', '')
        target_text = data.get('target_text', '')
        source_lang = data.get('source_lang', '')
        target_lang = data.get('target_lang', '')
        context = data.get('context', '')
        
        if not all([source_text, target_text, source_lang, target_lang]):
            return ApiResponse(success=False, error='缺少必要参数')
        
        success = translation_memory_service.add_translation(
            source_text, target_text, source_lang, target_lang, context
        )
        
        if success:
            return ApiResponse(
                success=True,
                message='翻译已添加到记忆库'
            )
        else:
            return ApiResponse(success=False, error='添加失败')
    except Exception as e:
        import traceback
        print(f"Error in add_translation_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/suggest",
             summary="获取翻译建议",
             description="基于相似度匹配获取翻译建议",
             response_description="返回相似翻译列表")
async def get_translation_suggestions_api(
        request: Request,
        data: Dict[str, Any] = Body(...)
):
    """
    获取翻译建议API
    
    Request Body:
    {
        "source_text": "Hello world",
        "source_lang": "en",
        "target_lang": "zh-CN",
        "threshold": 0.7
    }
    """
    try:
        source_text = data.get('source_text', '')
        source_lang = data.get('source_lang', '')
        target_lang = data.get('target_lang', '')
        threshold = data.get('threshold', 0.7)
        
        if not all([source_text, source_lang, target_lang]):
            return ApiResponse(success=False, error='缺少必要参数')
        
        suggestions = translation_memory_service.find_similar_translations(
            source_text, source_lang, target_lang, threshold
        )
        
        return ApiResponse(
            success=True,
            data={
                'suggestions': suggestions,
                'count': len(suggestions),
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_translation_suggestions_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/stats",
            summary="翻译记忆统计",
            description="获取翻译记忆库统计信息(仅管理员)",
            response_description="返回统计数据")
async def translation_stats_api(
        request: Request,
        current_user: User = Depends(admin_required_api)
):
    """
    翻译记忆统计API
    """
    try:
        stats = translation_memory_service.get_translation_stats()
        
        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        import traceback
        print(f"Error in translation_stats_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/export",
             summary="导出翻译记忆",
             description="导出翻译记忆为JSON格式(仅管理员)",
             response_description="返回JSON数据")
async def export_translation_memory_api(
        request: Request,
        current_user: User = Depends(admin_required_api)
):
    """
    导出翻译记忆API
    """
    try:
        json_str = translation_memory_service.export_memory()
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=json.loads(json_str),
            headers={
                'Content-Disposition': 'attachment; filename="translation_memory.json"',
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in export_translation_memory_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/import",
             summary="导入翻译记忆",
             description="从JSON导入翻译记忆(仅管理员)",
             response_description="返回操作结果")
async def import_translation_memory_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    导入翻译记忆API
    
    Request Body:
    {
        "json_data": {...},
        "merge": true
    }
    """
    try:
        json_data = data.get('json_data', {})
        merge = data.get('merge', True)
        
        import json
        json_str = json.dumps(json_data)
        
        success = translation_memory_service.import_memory(json_str, merge)
        
        if success:
            return ApiResponse(
                success=True,
                message='翻译记忆导入成功'
            )
        else:
            return ApiResponse(success=False, error='导入失败')
    except Exception as e:
        import traceback
        print(f"Error in import_translation_memory_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/clear",
             summary="清除翻译记忆",
             description="清除翻译记忆库(仅管理员)",
             response_description="返回操作结果")
async def clear_translation_memory_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    清除翻译记忆API
    
    Request Body:
    {
        "language_pair": "zh-CN_en" (可选,不传则清除全部)
    }
    """
    try:
        language_pair = data.get('language_pair', None)
        
        translation_memory_service.clear_memory(language_pair)
        
        return ApiResponse(
            success=True,
            message=f'已清除{"语言对: " + language_pair if language_pair else "全部"}翻译记忆'
        )
    except Exception as e:
        import traceback
        print(f"Error in clear_translation_memory_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/info",
            summary="翻译记忆信息",
            description="获取翻译记忆系统信息",
            response_description="返回系统信息")
async def translation_memory_info_api(request: Request):
    """
    翻译记忆信息API
    """
    return ApiResponse(
        success=True,
        data={
            'enabled': True,
            'features': [
                '翻译记忆存储',
                '相似度匹配(Levenshtein)',
                '自动建议',
                '导入/导出',
                '多语言对支持',
            ],
            'similarity_algorithm': 'Levenshtein Distance',
            'default_threshold': 0.7,
            'max_suggestions': 10,
        }
    )
