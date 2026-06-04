"""
专业翻译服务API
集成Google Translate、DeepL等翻译服务商
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, Body

from src.api.v1.core.responses import ApiResponse
from shared.models.user import User
from shared.utils.translation_api_clients import (
    translation_service_manager,
    GoogleTranslateClient,
    DeepLClient,
)
from src.auth.auth_deps import admin_required as admin_required_api

router = APIRouter()


@router.post("/translate",
             summary="翻译文本",
             description="使用配置的翻译服务API翻译文本(仅管理员)",
             response_description="返回翻译结果")
async def translate_text_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    翻译文本API
    
    Request Body:
    {
        "text": "Hello world",
        "target_lang": "zh-CN",
        "source_lang": "en",
        "provider": "google" (可选)
    }
    """
    try:
        text = data.get('text', '')
        target_lang = data.get('target_lang', '')
        source_lang = data.get('source_lang', 'auto')
        provider = data.get('provider', None)
        
        if not text or not target_lang:
            return ApiResponse(success=False, error='缺少必要参数')
        
        # 转换语言代码
        lang_map = {
            'zh-CN': 'zh',
            'en': 'en',
            'ja': 'ja',
            'ko': 'ko',
            'ar': 'ar',
            'he': 'he',
        }
        
        target_code = lang_map.get(target_lang, target_lang)
        source_code = lang_map.get(source_lang, source_lang) if source_lang != 'auto' else 'auto'
        
        result = translation_service_manager.translate(text, target_code, source_code, provider)
        
        if result['success']:
            return ApiResponse(
                success=True,
                data={
                    'translated_text': result['translated_text'],
                    'detected_source': result.get('detected_source', ''),
                    'provider': result['provider'],
                }
            )
        else:
            return ApiResponse(success=False, error=result.get('error', '翻译失败'))
    except Exception as e:
        import traceback
        print(f"Error in translate_text_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/detect-language",
             summary="检测语言",
             description="自动检测文本语言(仅管理员)",
             response_description="返回检测结果")
async def detect_language_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    检测语言API
    
    Request Body:
    {
        "text": "Hello world",
        "provider": "google" (可选)
    }
    """
    try:
        text = data.get('text', '')
        provider = data.get('provider', 'google')
        
        if not text:
            return ApiResponse(success=False, error='缺少文本')
        
        # 目前只有Google支持语言检测
        if provider == 'google' and 'google' in translation_service_manager.clients:
            client = translation_service_manager.clients['google']
            result = client.detect_language(text)
            
            if result['success']:
                return ApiResponse(
                    success=True,
                    data={
                        'language': result['language'],
                        'confidence': result['confidence'],
                        'provider': result['provider'],
                    }
                )
            else:
                return ApiResponse(success=False, error=result.get('error', '检测失败'))
        else:
            return ApiResponse(success=False, error='当前提供商不支持语言检测')
    except Exception as e:
        import traceback
        print(f"Error in detect_language_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/providers",
            summary="获取可用提供商",
            description="获取已配置的翻译服务提供商列表(仅管理员)",
            response_description="返回提供商列表")
async def get_providers_api(
        request: Request,
        current_user: User = Depends(admin_required_api)
):
    """
    获取可用提供商API
    """
    try:
        providers = translation_service_manager.get_available_providers()
        default = translation_service_manager.default_provider
        
        return ApiResponse(
            success=True,
            data={
                'providers': providers,
                'default_provider': default,
                'count': len(providers),
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_providers_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/configure",
             summary="配置翻译服务",
             description="配置翻译服务提供商API密钥(仅管理员)",
             response_description="返回配置结果")
async def configure_translation_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        current_user: User = Depends(admin_required_api)
):
    """
    配置翻译服务API
    
    Request Body:
    {
        "provider": "google",
        "api_key": "your-api-key",
        "set_as_default": true
    }
    """
    try:
        provider = data.get('provider', '')
        api_key = data.get('api_key', '')
        set_as_default = data.get('set_as_default', False)
        
        if not provider or not api_key:
            return ApiResponse(success=False, error='缺少必要参数')
        
        # 注册客户端
        if provider == 'google':
            client = GoogleTranslateClient(api_key)
            translation_service_manager.register_client('google', client)
        elif provider == 'deepl':
            client = DeepLClient(api_key)
            translation_service_manager.register_client('deepl', client)
        else:
            return ApiResponse(success=False, error=f'不支持的提供商: {provider}')
        
        if set_as_default:
            translation_service_manager.set_default_provider(provider)
        
        return ApiResponse(
            success=True,
            message=f'{provider}翻译服务配置成功'
        )
    except Exception as e:
        import traceback
        print(f"Error in configure_translation_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/info",
            summary="翻译服务信息",
            description="获取翻译服务系统信息",
            response_description="返回系统信息")
async def translation_service_info_api(request: Request):
    """
    翻译服务信息API
    """
    return ApiResponse(
        success=True,
        data={
            'enabled': True,
            'supported_providers': [
                'Google Translate',
                'DeepL',
            ],
            'features': [
                '多语言翻译',
                '自动语言检测',
                '批量翻译',
                'API密钥管理',
            ],
            'pricing_note': '需要自行申请API密钥并付费',
            'documentation': {
                'google': 'https://cloud.google.com/translate/docs',
                'deepl': 'https://www.deepl.com/docs-api',
            },
        }
    )
