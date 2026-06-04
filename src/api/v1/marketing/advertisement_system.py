"""
广告管理系统 API
提供广告位管理、广告投放、统计等功能
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body

from shared.models.user import User as UserModel
from shared.services.marketing.advertisement_system import advertisement_system
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required

router = APIRouter(tags=["advertisements"])


@router.get("/slots", summary="获取所有广告位")
async def get_ad_slots():
    """
    获取所有可用的广告位信息
    
    Returns:
        广告位列表
    """
    try:
        slots = advertisement_system.get_all_slots()

        return ApiResponse(
            success=True,
            data={
                'slots': slots,
                'count': len(slots),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取广告位失败: {str(e)}")


@router.post("/create", summary="创建广告")
async def create_ad(
        title: str = Body(..., description="广告标题"),
        slot_id: str = Body(..., description="广告位ID"),
        ad_type: str = Body('image', enum=['image', 'html', 'adsense', 'baidu'], description="广告类型"),
        content: str = Body('', description="广告内容"),
        image_url: str = Body(None, description="图片URL"),
        link_url: str = Body(None, description="跳转链接"),
        html_code: str = Body(None, description="HTML代码"),
        start_date: str = Body(None, description="开始时间(ISO格式)"),
        end_date: str = Body(None, description="结束时间(ISO格式)"),
        priority: int = Body(5, ge=1, le=10, description="优先级"),
        budget: float = Body(None, description="预算上限"),
        current_user: UserModel = Depends(admin_required)
):
    """
    创建新广告
    
    Args:
        title: 广告标题
        slot_id: 广告位ID
        ad_type: 广告类型(image/html/adsense/baidu)
        content: 广告内容
        image_url: 图片URL
        link_url: 跳转链接
        html_code: HTML代码
        start_date: 开始时间
        end_date: 结束时间
        priority: 优先级(1-10)
        budget: 预算上限
        
    Returns:
        创建结果
    """
    try:
        # 解析时间
        parsed_start = datetime.fromisoformat(start_date) if start_date else None
        parsed_end = datetime.fromisoformat(end_date) if end_date else None

        ad = advertisement_system.create_ad(
            title=title,
            slot_id=slot_id,
            ad_type=ad_type,
            content=content,
            image_url=image_url,
            link_url=link_url,
            html_code=html_code,
            start_date=parsed_start,
            end_date=parsed_end,
            priority=priority,
            budget=budget,
        )

        return ApiResponse(
            success=True,
            message='广告创建成功',
            data={
                'ad_id': ad['ad_id'],
                'title': ad['title'],
                'slot_id': ad['slot_id'],
            }
        )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"创建广告失败: {str(e)}")


@router.get("/list", summary="获取广告列表")
async def get_ads(
        slot_id: str = Query(None, description="广告位ID过滤"),
        status: str = Query(None, enum=['active', 'paused', 'expired'], description="状态过滤"),
        current_user: UserModel = Depends(admin_required)
):
    """
    获取广告列表
    
    Args:
        slot_id: 广告位ID过滤
        status: 状态过滤
        
    Returns:
        广告列表
    """
    try:
        ads = advertisement_system.get_user_ads()

        # 过滤
        if slot_id:
            ads = [ad for ad in ads if ad['slot_id'] == slot_id]
        if status:
            ads = [ad for ad in ads if ad['status'] == status]

        return ApiResponse(
            success=True,
            data={
                'ads': ads,
                'count': len(ads),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取广告列表失败: {str(e)}")


@router.post("/{ad_id}/pause", summary="暂停广告")
async def pause_ad(
        ad_id: str,
        current_user: UserModel = Depends(admin_required)
):
    """
    暂停指定广告
    
    Args:
        ad_id: 广告ID
        
    Returns:
        操作结果
    """
    try:
        success = advertisement_system.pause_ad(ad_id)

        if success:
            return ApiResponse(
                success=True,
                message='广告已暂停'
            )
        else:
            return ApiResponse(success=False, error='广告不存在')
    except Exception as e:
        return ApiResponse(success=False, error=f"暂停广告失败: {str(e)}")


@router.post("/{ad_id}/activate", summary="激活广告")
async def activate_ad(
        ad_id: str,
        current_user: UserModel = Depends(admin_required)
):
    """
    激活指定广告
    
    Args:
        ad_id: 广告ID
        
    Returns:
        操作结果
    """
    try:
        success = advertisement_system.activate_ad(ad_id)

        if success:
            return ApiResponse(
                success=True,
                message='广告已激活'
            )
        else:
            return ApiResponse(success=False, error='广告不存在')
    except Exception as e:
        return ApiResponse(success=False, error=f"激活广告失败: {str(e)}")


@router.delete("/{ad_id}", summary="删除广告")
async def delete_ad(
        ad_id: str,
        current_user: UserModel = Depends(admin_required)
):
    """
    删除指定广告
    
    Args:
        ad_id: 广告ID
        
    Returns:
        操作结果
    """
    try:
        success = advertisement_system.delete_ad(ad_id)

        if success:
            return ApiResponse(
                success=True,
                message='广告已删除'
            )
        else:
            return ApiResponse(success=False, error='广告不存在')
    except Exception as e:
        return ApiResponse(success=False, error=f"删除广告失败: {str(e)}")


@router.get("/{ad_id}/stats", summary="获取广告统计")
async def get_ad_stats(
        ad_id: str,
        current_user: UserModel = Depends(admin_required)
):
    """
    获取广告统计数据
    
    Args:
        ad_id: 广告ID
        
    Returns:
        统计数据
    """
    try:
        stats = advertisement_system.get_ad_stats(ad_id)

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


# ==================== 广告联盟配置 API ====================

@router.post("/network/configure", summary="配置广告联盟")
async def configure_ad_network(
        network: str = Body(..., enum=['adsense', 'baidu'], description="广告联盟名称"),
        config: dict = Body(..., description="配置信息"),
        current_user: UserModel = Depends(admin_required)
):
    """
    配置广告联盟（AdSense/百度）
    
    Args:
        network: 广告联盟名称
        config: 配置信息
        
    Returns:
        配置结果
    """
    try:
        success = advertisement_system.configure_ad_network(network, config)

        if success:
            return ApiResponse(
                success=True,
                message=f'{network} 配置成功'
            )
        else:
            return ApiResponse(success=False, error='不支持的广告联盟')
    except Exception as e:
        return ApiResponse(success=False, error=f"配置失败: {str(e)}")


@router.get("/network/{network}/config", summary="获取广告联盟配置")
async def get_ad_network_config(
        network: str,
        current_user: UserModel = Depends(admin_required)
):
    """
    获取广告联盟配置
    
    Args:
        network: 广告联盟名称
        
    Returns:
        配置信息
    """
    try:
        config = advertisement_system.get_ad_network_config(network)

        return ApiResponse(
            success=True,
            data=config
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取配置失败: {str(e)}")


@router.get("/network/adsense/code", summary="生成AdSense代码")
async def generate_adsense_code(
        slot_id: str = Query(..., description="广告位ID"),
        ad_format: str = Query('auto', enum=['auto', 'display', 'article', 'match_content'], description="广告格式"),
        current_user: UserModel = Depends(admin_required)
):
    """
    生成 Google AdSense 广告代码
    
    Args:
        slot_id: 广告位ID
        ad_format: 广告格式
        
    Returns:
        HTML代码
    """
    try:
        code = advertisement_system.generate_adsense_code(slot_id, ad_format)
        
        return ApiResponse(
            success=True,
            data={
                'code': code,
                'slot_id': slot_id,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"生成代码失败: {str(e)}")


@router.get("/network/baidu/code", summary="生成百度联盟代码")
async def generate_baidu_code(
        slot_id: str = Query(..., description="广告位ID"),
        current_user: UserModel = Depends(admin_required)
):
    """
    生成百度联盟广告代码
    
    Args:
        slot_id: 广告位ID
        
    Returns:
        HTML代码
    """
    try:
        code = advertisement_system.generate_baidu_code(slot_id)

        return ApiResponse(
            success=True,
            data={
                'code': code,
                'slot_id': slot_id,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"生成代码失败: {str(e)}")


@router.get("/revenue/report", summary="获取收益报表")
async def get_revenue_report(
        start_date: str = Query(None, description="开始日期(ISO格式)"),
        end_date: str = Query(None, description="结束日期(ISO格式)"),
        current_user: UserModel = Depends(admin_required)
):
    """
    获取广告收益报表
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        收益统计数据
    """
    try:
        parsed_start = datetime.fromisoformat(start_date) if start_date else None
        parsed_end = datetime.fromisoformat(end_date) if end_date else None

        report = advertisement_system.get_revenue_report(parsed_start, parsed_end)

        return ApiResponse(
            success=True,
            data=report
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取报表失败: {str(e)}")
