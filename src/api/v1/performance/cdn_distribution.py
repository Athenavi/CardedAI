"""
CDN智能分发API端点

提供CDN管理的REST API接口
"""
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, Query, Body, UploadFile, File

from auth import admin_required
from shared.services.performance.cdn_distributor import cdn_service
from src.api.v1.core.responses import ApiResponse

router = APIRouter(tags=["CDN Distribution"])


@router.post("/upload", summary="上传文件到CDN")
async def upload_to_cdn(
        file: UploadFile = File(..., description="要上传的文件"),
        cache_ttl: int = Query(86400, ge=60, le=2592000, description="缓存时间（秒）"),
        provider: str = Query(None, description="指定CDN提供商"),
        current_user=Depends(admin_required)
):
    """
    上传文件到CDN
    
    - **file**: 要上传的文件
    - **cache_ttl**: 缓存时间（秒），默认24小时
    - **provider**: 指定CDN提供商（可选）
    """
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # 上传到CDN
            result = await cdn_service.upload_to_cdn(tmp_path, cache_ttl, provider)

            if not result.get('success'):
                return ApiResponse(success=False, error=result.get('error', '上传失败'))

            return ApiResponse(
                success=True,
                data={
                    'cdn_url': result.get('cdn_url'),
                    'original_filename': file.filename,
                    'file_size': len(content),
                    'cache_ttl': result.get('cache_ttl'),
                    'provider': result.get('provider'),
                    'etag': result.get('etag')
                },
                message='文件上传成功'
            )
        finally:
            # 清理临时文件
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        return ApiResponse(success=False, error=f"上传失败: {str(e)}")


@router.post("/purge", summary="清除CDN缓存")
async def purge_cdn_cache(
        urls: List[str] = Body(..., embed=True, description="要清除的URL列表"),
        provider: str = Query(None, description="指定CDN提供商"),
        current_user=Depends(admin_required)
):
    """
    清除CDN缓存
    
    - **urls**: 要清除的URL列表
    - **provider**: 指定CDN提供商（可选）
    """
    try:
        result = await cdn_service.purge_cache(urls, provider)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '清除失败'))

        return ApiResponse(
            success=True,
            data={
                'purged_count': result.get('purged_count', 0),
                'provider': result.get('provider')
            },
            message=f'已清除{result.get("purged_count")}个URL的缓存'
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"清除失败: {str(e)}")


@router.post("/prefetch", summary="预取URL到CDN")
async def prefetch_urls(
        urls: List[str] = Body(..., embed=True, description="要预取的URL列表"),
        provider: str = Query(None, description="指定CDN提供商"),
        current_user=Depends(admin_required)
):
    """
    预取URL到CDN（预热缓存）
    
    - **urls**: 要预取的URL列表
    - **provider**: 指定CDN提供商（可选）
    """
    try:
        result = await cdn_service.prefetch_urls(urls, provider)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '预取失败'))

        return ApiResponse(
            success=True,
            data={
                'prefetched_count': result.get('prefetched_count', 0),
                'provider': result.get('provider')
            },
            message=f'已预取{result.get("prefetched_count")}个URL'
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"预取失败: {str(e)}")


@router.get("/url/{file_path:path}", summary="获取最优CDN URL")
async def get_optimal_url(
        file_path: str,
        user_region: str = Query(None, description="用户所在地区"),
        current_user=Depends(admin_required)
):
    """
    获取文件的最优CDN URL
    
    - **file_path**: 文件路径
    - **user_region**: 用户所在地区（可选）
    """
    try:
        url = await cdn_service.get_optimal_url(file_path, user_region)

        if not url:
            return ApiResponse(success=False, error='Resource not found in CDN')

        return ApiResponse(
            success=True,
            data={
                'cdn_url': url,
                'file_path': file_path,
                'user_region': user_region
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取URL失败: {str(e)}")


@router.post("/health-check", summary="执行CDN健康检查")
async def health_check(
        provider: str = Query(None, description="指定CDN提供商（None则检查所有）"),
        current_user=Depends(admin_required)
):
    """
    执行CDN健康检查
    
    - **provider**: 指定CDN提供商（可选）
    """
    try:
        results = await cdn_service.health_check(provider)
        return ApiResponse(success=True, data=results)
    except Exception as e:
        return ApiResponse(success=False, error=f"健康检查失败: {str(e)}")


@router.post("/switch-provider", summary="切换CDN提供商")
async def switch_provider(
        provider_name: str = Body(..., embed=True, description="新的CDN提供商名称"),
        current_user=Depends(admin_required)
):
    """
    切换到备用CDN提供商（故障切换）
    
    - **provider_name**: 新的CDN提供商名称
    """
    try:
        result = await cdn_service.switch_provider(provider_name)

        if not result.get('success'):
            return ApiResponse(success=False, error=result.get('error', '切换失败'))

        return ApiResponse(
            success=True,
            data={
                'old_provider': result.get('old_provider'),
                'new_provider': result.get('new_provider')
            },
            message=f'已切换到 {result.get("new_provider")}'
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"切换失败: {str(e)}")


@router.get("/resource/{file_path:path}", summary="获取资源信息")
async def get_resource_info(
        file_path: str,
        current_user=Depends(admin_required)
):
    """
    获取CDN资源的详细信息
    
    - **file_path**: 文件路径
    """
    try:
        info = cdn_service.get_resource_info(file_path)

        if not info:
            return ApiResponse(success=False, error='Resource not found')

        return ApiResponse(success=True, data=info)

    except Exception as e:
        return ApiResponse(success=False, error=f"获取信息失败: {str(e)}")


@router.get("/stats", summary="获取CDN统计信息")
async def get_cdn_stats(current_user=Depends(admin_required)):
    """获取CDN服务的统计信息"""
    try:
        stats = cdn_service.get_stats()
        return ApiResponse(success=True, data=stats)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.get("/config", summary="获取CDN配置")
async def get_cdn_config(current_user=Depends(admin_required)):
    """获取CDN配置信息"""
    try:
        config = cdn_service.get_config()
        return ApiResponse(success=True, data=config)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取配置失败: {str(e)}")


@router.post("/providers", summary="添加CDN提供商")
async def add_provider(
        name: str = Body(..., embed=True, description="提供商名称"),
        provider_type: str = Body(..., embed=True, description="提供商类型"),
        config: dict = Body(..., embed=True, description="配置信息"),
        is_default: bool = Body(False, embed=True, description="是否为默认提供商"),
        current_user=Depends(admin_required)
):
    """
    添加CDN提供商
    
    - **name**: 提供商名称
    - **provider_type**: 提供商类型 (cloudflare, aws_cloudfront, aliyun, tencent)
    - **config**: 配置信息
    - **is_default**: 是否为默认提供商
    """
    try:
        cdn_service.add_provider(name, provider_type, config, is_default)

        return ApiResponse(
            success=True,
            data={
                'name': name,
                'type': provider_type,
                'is_default': is_default
            },
            message=f'CDN提供商 {name} 添加成功'
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"添加失败: {str(e)}")
