"""
翻译进度 API

提供翻译进度的查看和统计功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from shared.services.translation.translation_progress import translation_tracker
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/progress/{language_code}", summary="获取语言翻译进度", description="获取指定语言的翻译进度")
async def get_language_progress(
        language_code: str,
        current_user=Depends(jwt_required),
):
    """获取语言翻译进度"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    progress = translation_tracker.get_language_progress(language_code)

    return ApiResponse(
        success=True,
        data=progress
    )


@router.get("/progress", summary="获取所有语言进度", description="获取所有语言的翻译进度")
async def get_all_languages_progress(
        current_user=Depends(jwt_required),
):
    """获取所有语言进度"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    progress_list = translation_tracker.get_all_languages_progress()

    return ApiResponse(
        success=True,
        data={
            'languages': progress_list,
            'count': len(progress_list),
        }
    )


@router.get("/contributors", summary="获取贡献者统计", description="获取翻译贡献者统计")
async def get_contributor_stats(
        current_user=Depends(jwt_required),
):
    """获取贡献者统计"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    contributors = translation_tracker.get_contributor_stats()

    return ApiResponse(
        success=True,
        data={
            'contributors': contributors,
            'count': len(contributors),
        }
    )


@router.get("/report", summary="生成进度报告", description="生成完整的翻译进度报告")
async def generate_report(
        current_user=Depends(jwt_required),
):
    """生成进度报告"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    report = translation_tracker.generate_progress_report()

    return ApiResponse(
        success=True,
        data=report
    )


@router.get("/untranslated/{language_code}", summary="获取未翻译字符串", description="获取指定语言未翻译的字符串")
async def get_untranslated_strings(
        language_code: str,
        limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
        current_user=Depends(jwt_required),
):
    """获取未翻译字符串"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    untranslated = translation_tracker.get_untranslated_strings(language_code, limit)

    return ApiResponse(
        success=True,
        data={
            'language': language_code,
            'untranslated_keys': untranslated,
            'count': len(untranslated),
        }
    )


@router.post("/register", summary="注册翻译项", description="注册或更新翻译项")
async def register_translation(
        language_code: str = Body(..., description="语言代码"),
        translation_key: str = Body(..., description="翻译键"),
        is_translated: bool = Body(..., description="是否已翻译"),
        translator_id: Optional[int] = Body(None, description="翻译者ID"),
        translator_name: Optional[str] = Body(None, description="翻译者名称"),
        current_user=Depends(jwt_required),
):
    """注册翻译项"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    translation_tracker.register_translation(
        language_code=language_code,
        translation_key=translation_key,
        is_translated=is_translated,
        translator_id=translator_id,
        translator_name=translator_name,
    )

    return ApiResponse(
        success=True,
        message="Translation registered"
    )


@router.delete("/clear/{language_code}", summary="清空语言数据", description="清空指定语言的翻译数据")
async def clear_language(
        language_code: str,
        current_user=Depends(jwt_required),
):
    """清空语言数据"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    translation_tracker.clear_language(language_code)

    return ApiResponse(
        success=True,
        message=f"Language {language_code} cleared"
    )