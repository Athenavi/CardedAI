"""
翻译管理 API 端点
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File

from src.api.v1.core.responses import ApiResponse
from shared.services.translation.translation_manager.translation_manager import translation_manager
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["translations"])


@router.get("/locales")
async def list_supported_locales(
    current_user=Depends(jwt_required)
):
    """获取支持的语言列表"""
    try:
        return ApiResponse(
            success=True,
            data={"locales": translation_manager.supported_languages}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/progress")
async def get_translation_progress(
    locale: str = Query(..., description="语言代码"),
    current_user=Depends(jwt_required)
):
    """获取指定语言的翻译进度"""
    try:
        progress = translation_manager.get_translation_progress(locale)
        
        return ApiResponse(
            success=True,
            data={"progress": progress}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/progress/all")
async def get_all_locales_progress(
    current_user=Depends(jwt_required)
):
    """获取所有语言的翻译进度"""
    try:
        progress_list = translation_manager.get_all_locales_progress()
        
        return ApiResponse(
            success=True,
            data={"progress": progress_list}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/pending")
async def get_pending_translations(
    locale: str = Query(..., description="语言代码"),
    limit: int = Query(50, description="限制数量"),
    current_user=Depends(jwt_required)
):
    """获取待翻译的内容"""
    try:
        pending = translation_manager.get_pending_translations(locale, limit)
        
        return ApiResponse(
            success=True,
            data={
                "pending": pending,
                "total": len(pending)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/save")
async def save_translation(
    locale: str = Query(..., description="语言代码"),
    key: str = Query(..., description="翻译键"),
    value: str = Query(..., description="翻译值"),
    status: str = Query("translated", description="状态"),
    current_user=Depends(jwt_required)
):
    """保存单个翻译"""
    try:
        success = translation_manager.save_translation(locale, key, value, status=status)
        
        if success:
            return ApiResponse(
                success=True,
                message="翻译已保存"
            )
        else:
            return ApiResponse(
                success=False,
                error="保存失败"
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/batch-translate")
async def batch_translate(
    source_locale: str = Query(..., description="源语言"),
    target_locale: str = Query(..., description="目标语言"),
    translations: dict = None,
    current_user=Depends(jwt_required)
):
    """批量翻译"""
    try:
        if not translations:
            return ApiResponse(
                success=False,
                error="请提供翻译数据"
            )
        
        result = translation_manager.batch_translate(
            source_locale,
            target_locale,
            translations
        )
        
        return ApiResponse(
            success=result["success"],
            message=f"成功翻译 {result['success_count']}/{result['total']} 条",
            data=result
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/export/{locale}")
async def export_translations(
    locale: str,
    format: str = Query("json", description="导出格式"),
    current_user=Depends(jwt_required)
):
    """导出翻译文件"""
    try:
        file_path = translation_manager.export_translations(locale, format)
        
        if file_path:
            return ApiResponse(
                success=True,
                data={"file_path": file_path}
            )
        else:
            return ApiResponse(
                success=False,
                error="翻译文件不存在"
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/import/{locale}")
async def import_translations(
    locale: str,
    file: UploadFile = File(...),
    merge: bool = Query(False, description="是否合并"),
    current_user=Depends(jwt_required)
):
    """导入翻译文件"""
    try:
        # 保存上传的文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # 导入翻译
        result = translation_manager.import_translations(locale, tmp_path, merge)
        
        # 清理临时文件
        os.unlink(tmp_path)
        
        if result["success"]:
            return ApiResponse(
                success=True,
                message=result["message"],
                data={"count": result["count"]}
            )
        else:
            return ApiResponse(
                success=False,
                error=result["error"]
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
