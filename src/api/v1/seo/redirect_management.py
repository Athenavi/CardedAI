"""
重定向管理 API 端点
"""

from fastapi import APIRouter, Depends, Query

from shared.services.seo.redirect_manager import redirect_manager
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["redirects"])


@router.get("/", summary="获取所有重定向规则")
async def list_redirects(
    enabled_only: bool = Query(False, description="只显示启用的"),
    page: int = Query(1, description="页码"),
    per_page: int = Query(50, description="每页数量"),
    current_user=Depends(jwt_required)
):
    """获取所有重定向规则"""
    try:
        result = redirect_manager.get_all_redirects(
            enabled_only=enabled_only,
            page=page,
            per_page=per_page
        )
        
        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/", summary="创建重定向规则")
async def create_redirect(
    source_url: str = Query(..., description="源URL"),
    target_url: str = Query(..., description="目标URL"),
    redirect_type: int = Query(301, description="重定向类型"),
        match_type: str = Query('exact', description="匹配类型 (exact/wildcard/regex)"),
    enabled: bool = Query(True, description="是否启用"),
    note: str = Query("", description="备注"),
    current_user=Depends(jwt_required)
):
    """创建重定向规则"""
    try:
        result = redirect_manager.add_redirect(
            source_url=source_url,
            target_url=target_url,
            redirect_type=redirect_type,
            match_type=match_type,
            enabled=enabled,
            note=note
        )
        
        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message'],
                data=result['redirect']
            )
        else:
            return ApiResponse(
                success=False,
                error=result['error']
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/{redirect_id}")
async def update_redirect(
    redirect_id: int,
    source_url: str = Query(None, description="源URL"),
    target_url: str = Query(None, description="目标URL"),
    redirect_type: int = Query(None, description="重定向类型"),
    enabled: bool = Query(None, description="是否启用"),
    note: str = Query(None, description="备注"),
    current_user=Depends(jwt_required)
):
    """更新重定向规则"""
    try:
        result = redirect_manager.update_redirect(
            redirect_id=redirect_id,
            source_url=source_url,
            target_url=target_url,
            redirect_type=redirect_type,
            enabled=enabled,
            note=note
        )
        
        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message'],
                data=result['redirect']
            )
        else:
            return ApiResponse(
                success=False,
                error=result['error']
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/{redirect_id}")
async def delete_redirect(
    redirect_id: int,
    current_user=Depends(jwt_required)
):
    """删除重定向规则"""
    try:
        result = redirect_manager.delete_redirect(redirect_id)
        
        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message']
            )
        else:
            return ApiResponse(
                success=False,
                error=result['error']
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/bulk-import")
async def bulk_import_redirects(
    redirects_data: list,
    current_user=Depends(jwt_required)
):
    """批量导入重定向规则"""
    try:
        result = redirect_manager.bulk_import(redirects_data)
        
        return ApiResponse(
            success=result['success'],
            message=f"成功导入 {result['success_count']}/{result['total']} 条规则",
            data=result
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/export")
async def export_redirects(
    current_user=Depends(jwt_required)
):
    """导出所有重定向规则"""
    try:
        redirects = redirect_manager.export_redirects()
        
        return ApiResponse(
            success=True,
            data={"redirects": redirects}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/404-suggestions")
async def get_404_suggestions(
    recent_404s: list = None,
    current_user=Depends(jwt_required)
):
    """从404错误中获取重定向建议"""
    try:
        if not recent_404s:
            return ApiResponse(
                success=False,
                error="请提供404 URL列表"
            )
        
        suggestions = redirect_manager.detect_404_candidates(recent_404s)
        
        return ApiResponse(
            success=True,
            data={
                "suggestions": suggestions,
                "total": len(suggestions)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/statistics")
async def get_redirect_statistics(
        current_user=Depends(jwt_required)
):
    """获取重定向统计信息"""
    try:
        stats = redirect_manager.get_statistics()

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/test")
async def test_redirect_url(
        url: str = Query(..., description="要测试的URL"),
        current_user=Depends(jwt_required)
):
    """测试URL是否需要重定向"""
    try:
        result = redirect_manager.test_redirect(url)

        if result:
            return ApiResponse(
                success=True,
                data={
                    "matched": True,
                    "redirect": result
                }
            )
        else:
            return ApiResponse(
                success=True,
                data={
                    "matched": False,
                    "message": "没有匹配的重定向规则"
                }
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
