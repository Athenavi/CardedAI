"""
翻译管理 API
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from shared.services.translation.translation import translation_service

router = APIRouter(tags=["translations"])


@router.get("/items/{locale}/{key}")
async def get_translation(
        locale: str,
        key: str,
        default: Optional[str] = None
):
    """
    获取单个翻译
    
    Args:
        locale: 语言代码
        key: 翻译键
        default: 默认值
        
    Returns:
        翻译文本
    """
    try:
        value = translation_service.get_translation(locale, key, default)

        return {
            'success': True,
            'data': {
                'locale': locale,
                'key': key,
                'value': value,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/{locale}/{key}")
async def set_translation(
        locale: str,
        key: str,
        value: str
):
    """
    设置翻译
    
    Args:
        locale: 语言代码
        key: 翻译键
        value: 翻译值
        
    Returns:
        操作结果
    """
    try:
        translation_service.set_translation(locale, key, value)

        return {
            'success': True,
            'message': 'Translation updated',
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{locale}")
async def get_all_translations(locale: str):
    """
    获取所有翻译
    
    Args:
        locale: 语言代码
        
    Returns:
        翻译字典
    """
    try:
        translations = translation_service.get_all_translations(locale)

        return {
            'success': True,
            'data': translations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress")
async def get_translation_progress(
        source_locale: str = Query('zh-CN', description="源语言")
):
    """
    获取翻译进度
    
    Args:
        source_locale: 源语言
        
    Returns:
        各语言的翻译进度
    """
    try:
        progress = translation_service.get_translation_progress(source_locale)

        return {
            'success': True,
            'data': progress,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/missing/{locale}")
async def get_missing_translations(
        locale: str,
        source_locale: str = Query('zh-CN', description="源语言")
):
    """
    获取缺失的翻译
    
    Args:
        locale: 目标语言
        source_locale: 源语言
        
    Returns:
        缺失的翻译键列表
    """
    try:
        missing = translation_service.get_missing_translations(locale, source_locale)

        return {
            'success': True,
            'data': {
                'locale': locale,
                'missing_keys': missing,
                'count': len(missing),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_translations(
        format: str = Query('json', enum=['json'], description="导出格式")
):
    """
    导出所有翻译
    
    Args:
        format: 导出格式
        
    Returns:
        导出的文件
    """
    try:
        content = translation_service.export_translations(format)

        return {
            'success': True,
            'data': content.decode('utf-8'),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
