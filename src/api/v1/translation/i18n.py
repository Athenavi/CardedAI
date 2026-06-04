"""
多语言 API
提供翻译管理、语言检测、自动翻译等功能
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Header

from shared.services.translation.translation import translation_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required, get_current_user

router = APIRouter(tags=["i18n"])


# ==================== 语言管理 ====================

@router.get("/languages", summary="获取支持的语言列表")
async def get_supported_languages():
    """
    获取所有支持的语言
    
    Returns:
        语言列表
    """
    try:
        languages = translation_service.get_supported_languages()
        
        return ApiResponse(
            success=True,
            data={
                'languages': languages,
                'default_language': translation_service.default_language,
                'total': len(languages)
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/detect", summary="检测用户语言")
async def detect_language(
        accept_language: Optional[str] = Header(None, description="Accept-Language头"),
):
    """
    根据HTTP头检测用户首选语言
    
    Args:
        accept_language: Accept-Language头
        
    Returns:
        检测到的语言
    """
    try:
        detected_lang = translation_service.detect_language(accept_language)
        
        return ApiResponse(
            success=True,
            data={
                'detected_language': detected_lang,
                'accept_language': accept_language,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 翻译管理 ====================

@router.get("/translate/{key}", summary="获取翻译")
async def get_translation(
        key: str,
        language: Optional[str] = Query(None, description="语言代码"),
        default: Optional[str] = Query(None, description="默认值"),
):
    """
    获取指定键的翻译
    
    Args:
        key: 翻译键
        language: 语言代码
        default: 默认值
        
    Returns:
        翻译文本
    """
    try:
        translation = translation_service.get_translation(key, language, default)
        
        return ApiResponse(
            success=True,
            data={
                'key': key,
                'translation': translation,
                'language': language or translation_service.default_language,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/translate", summary="批量获取翻译")
async def batch_get_translations(
        keys: List[str] = Body(..., description="翻译键列表"),
        language: Optional[str] = Body(None, description="语言代码"),
):
    """
    批量获取多个翻译键的翻译
    
    Args:
        keys: 翻译键列表
        language: 语言代码
        
    Returns:
        翻译字典
    """
    try:
        translations = {}
        for key in keys:
            translations[key] = translation_service.get_translation(key, language)

        return ApiResponse(
            success=True,
            data={
                'translations': translations,
                'language': language or translation_service.default_language,
            }
        )
        
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/translate/{key}", summary="设置翻译")
async def set_translation(
        key: str,
        value: str = Body(..., description="翻译值"),
        language: str = Body(..., description="语言代码"),
        current_user=Depends(jwt_required)
):
    """
    设置或更新翻译
    
    Args:
        key: 翻译键
        value: 翻译值
        language: 语言代码
        
    Returns:
        设置结果
    """
    try:
        # 检查权限（需要admin权限）
        # 这里简化处理，实际应该检查用户权限

        translation_service.set_translation(key, value, language)

        return ApiResponse(
            success=True,
            message=f"Translation set for key '{key}' in {language}"
        )
        
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/translate/bulk", summary="批量设置翻译")
async def bulk_set_translations(
        translations: Dict[str, str] = Body(..., description="翻译字典"),
        language: str = Body(..., description="语言代码"),
        current_user=Depends(jwt_required)
):
    """
    批量设置翻译
    
    Args:
        translations: 翻译字典 {key: value}
        language: 语言代码
        
    Returns:
        设置结果
    """
    try:
        for key, value in translations.items():
            translation_service.set_translation(key, value, language)
        
        return ApiResponse(
            success=True,
            message=f"Bulk translations set for {language}",
            data={
                'count': len(translations),
                'language': language,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 自动翻译 ====================

@router.post("/auto-translate", summary="自动翻译")
async def auto_translate(
        text: str = Body(..., description="要翻译的文本"),
        from_lang: str = Body(..., description="源语言"),
        to_lang: str = Body(..., description="目标语言"),
        api_key: Optional[str] = Body(None, description="API密钥"),
        current_user=Depends(jwt_required)
):
    """
    使用第三方API自动翻译文本
    
    Args:
        text: 要翻译的文本
        from_lang: 源语言
        to_lang: 目标语言
        api_key: API密钥
        
    Returns:
        翻译结果
    """
    try:
        translated_text = await translation_service.auto_translate(
            text=text,
            from_lang=from_lang,
            to_lang=to_lang,
            api_key=api_key
        )

        return ApiResponse(
            success=True,
            data={
                'original_text': text,
                'translated_text': translated_text,
                'from_language': from_lang,
                'to_language': to_lang,
            }
        )
        
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 翻译统计和管理 ====================

@router.get("/missing/{language}", summary="获取缺失翻译")
async def get_missing_translations(
        language: str,
        current_user=Depends(jwt_required)
):
    """
    获取指定语言缺失的翻译键
    
    Args:
        language: 语言代码
        
    Returns:
        缺失的翻译键列表
    """
    try:
        missing_keys = translation_service.get_missing_translations(language)

        return ApiResponse(
            success=True,
            data={
                'language': language,
                'missing_keys': missing_keys,
                'count': len(missing_keys),
            }
        )
        
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/stats", summary="获取翻译统计")
async def get_translation_stats(current_user=Depends(jwt_required)):
    """
    获取所有语言的翻译统计信息
    
    Returns:
        统计数据
    """
    try:
        stats = translation_service.get_translation_stats()

        return ApiResponse(
            success=True,
            data={
                'statistics': stats,
                'default_language': translation_service.default_language,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/export", summary="导出翻译")
async def export_translations(
        language: Optional[str] = Query(None, description="语言代码（None表示所有）"),
        current_user=Depends(jwt_required)
):
    """
    导出翻译数据
    
    Args:
        language: 语言代码
        
    Returns:
        翻译数据
    """
    try:
        exported_data = translation_service.export_translations(language)
        
        return ApiResponse(
            success=True,
            data=exported_data
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/import", summary="导入翻译")
async def import_translations(
        language: str = Body(..., description="语言代码"),
        translations: Dict[str, str] = Body(..., description="翻译数据"),
        merge: bool = Body(True, description="是否合并"),
        current_user=Depends(jwt_required)
):
    """
    导入翻译数据
    
    Args:
        language: 语言代码
        translations: 翻译数据
        merge: 是否合并
        
    Returns:
        导入结果
    """
    try:
        translation_service.import_translations(language, translations, merge)
        
        return ApiResponse(
            success=True,
            message=f"Translations imported for {language}",
            data={
                'language': language,
                'count': len(translations),
                'merged': merge,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/keys", summary="获取所有翻译键")
async def get_all_keys(
        language: Optional[str] = Query(None, description="语言代码"),
        current_user=Depends(jwt_required)
):
    """
    获取所有翻译键
    
    Args:
        language: 语言代码（None表示默认语言）
        
    Returns:
        翻译键列表
    """
    try:
        lang = language or translation_service.default_language
        keys = list(translation_service.translation_cache.get(lang, {}).keys())
        
        return ApiResponse(
            success=True,
            data={
                'language': lang,
                'keys': keys,
                'total': len(keys),
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))
