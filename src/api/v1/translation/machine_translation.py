"""
机器翻译 API 端点
"""

from fastapi import APIRouter, Depends, Query

from shared.services.translation.translation_manager import machine_translation_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["machine-translation"])


@router.post("/translate")
async def translate_text(
    text: str = Query(..., description="要翻译的文本"),
    source_lang: str = Query(..., description="源语言代码"),
    target_lang: str = Query(..., description="目标语言代码"),
    provider: str = Query("baidu", description="翻译提供商 (baidu/youdao/deepl)"),
    api_key: str = Query(None, description="API 密钥（可选）"),
    secret_key: str = Query(None, description="密钥（可选）"),
    current_user=Depends(jwt_required)
):
    """翻译单段文本"""
    try:
        result = await machine_translation_service.translate_text(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            provider=provider,
            api_key=api_key,
            secret_key=secret_key
        )
        
        if result["success"]:
            return ApiResponse(
                success=True,
                data=result
            )
        else:
            return ApiResponse(
                success=False,
                error=result["error"]
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.post("/batch-translate")
async def batch_translate_texts(
    texts: list = None,
    source_lang: str = Query(..., description="源语言"),
    target_lang: str = Query(..., description="目标语言"),
    provider: str = Query("baidu", description="翻译提供商"),
    delay: float = Query(1.0, description="请求间隔（秒）"),
    current_user=Depends(jwt_required)
):
    """批量翻译文本"""
    try:
        if not texts:
            return ApiResponse(
                success=False,
                error="请提供要翻译的文本列表"
            )
        
        result = await machine_translation_service.batch_translate(
            texts=texts,
            source_lang=source_lang,
            target_lang=target_lang,
            provider=provider,
            delay_between_requests=delay
        )
        
        return ApiResponse(
            success=result["success"],
            message=f"成功翻译 {result['success_count']}/{result['total']} 条",
            data=result
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.get("/memory/stats")
async def get_translation_memory_stats(
    current_user=Depends(jwt_required)
):
    """获取翻译记忆库统计"""
    try:
        stats = machine_translation_service.get_translation_memory_stats()
        
        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/memory/clear")
async def clear_translation_memory(
    current_user=Depends(jwt_required)
):
    """清空翻译记忆库"""
    try:
        result = machine_translation_service.clear_translation_memory()
        
        return ApiResponse(
            success=result["success"],
            message=result["message"]
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/providers")
async def list_translation_providers():
    """获取支持的翻译提供商列表"""
    try:
        providers = [
            {
                "key": key,
                "name": config["name"],
                "requires_key": config["requires_key"]
            }
            for key, config in machine_translation_service.providers.items()
        ]
        
        return ApiResponse(
            success=True,
            data={"providers": providers}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
