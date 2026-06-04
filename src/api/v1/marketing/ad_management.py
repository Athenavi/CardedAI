"""
广告管理 API
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from shared.services.marketing.ad_management_service import AdManagementService
from src.extensions import get_db

router = APIRouter(tags=["广告管理"])


# ==================== Pydantic 模型 ====================

class AdPlacementCreate(BaseModel):
    """创建广告位请求"""
    name: str = Field(..., description="广告位名称")
    code: str = Field(..., description="广告位代码")
    position: str = Field(..., description="广告位置")
    description: Optional[str] = Field(None, description="广告位描述")
    width: Optional[int] = Field(None, description="广告位宽度")
    height: Optional[int] = Field(None, description="广告位高度")


class AdPlacementUpdate(BaseModel):
    """更新广告位请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    position: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    is_active: Optional[bool] = None


class AdCreate(BaseModel):
    """创建广告请求"""
    title: str = Field(..., description="广告标题")
    ad_type: str = Field(default='html', description="广告类型")
    content: Optional[str] = Field(None, description="广告内容")
    image_url: Optional[str] = Field(None, description="广告图片URL")
    link_url: Optional[str] = Field(None, description="广告链接URL")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    placement_id: Optional[int] = Field(None, description="广告位ID")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    budget: Optional[float] = Field(None, description="预算")
    cost_per_click: Optional[float] = Field(None, description="每次点击费用")
    cost_per_impression: Optional[float] = Field(None, description="每千次展示费用")
    priority: int = Field(default=0, description="优先级")
    target_audience: str = Field(default='all', description="目标受众")
    device_targeting: str = Field(default='all', description="设备定位")
    geo_targeting: Optional[str] = Field(None, description="地理定位")


class AdUpdate(BaseModel):
    """更新广告请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    alt_text: Optional[str] = None
    ad_type: Optional[str] = None
    placement_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    cost_per_click: Optional[float] = None
    cost_per_impression: Optional[float] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    target_audience: Optional[str] = None
    device_targeting: Optional[str] = None
    geo_targeting: Optional[str] = None


# ==================== 依赖注入 ====================

def get_ad_service(db: Session = Depends(get_db)) -> AdManagementService:
    """获取广告服务实例"""
    return AdManagementService(db)


# ==================== 广告位 API ====================

@router.post("/placements", response_model=dict)
def create_ad_placement(
        placement: AdPlacementCreate,
        service: AdManagementService = Depends(get_ad_service)
):
    """创建广告位"""
    try:
        new_placement = service.create_ad_placement(
            name=placement.name,
            code=placement.code,
            position=placement.position,
            description=placement.description,
            width=placement.width,
            height=placement.height
        )
        return {
            "success": True,
            "data": {
                "id": new_placement.id,
                "name": new_placement.name,
                "code": new_placement.code,
            },
            "message": "广告位创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/placements", response_model=dict)
def list_ad_placements(
        active_only: bool = Query(False, description="仅显示激活的广告位"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        service: AdManagementService = Depends(get_ad_service)
):
    """获取广告位列表"""
    placements = service.list_ad_placements(
        active_only=active_only,
        skip=skip,
        limit=limit
    )

    return {
        "success": True,
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "position": p.position,
                "description": p.description,
                "width": p.width,
                "height": p.height,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in placements
        ],
        "total": len(placements)
    }


@router.get("/placements/{placement_id}", response_model=dict)
def get_ad_placement(
        placement_id: int,
        service: AdManagementService = Depends(get_ad_service)
):
    """获取广告位详情"""
    placement = service.get_ad_placement(placement_id)
    if not placement:
        raise HTTPException(status_code=404, detail="广告位不存在")

    return {
        "success": True,
        "data": {
            "id": placement.id,
            "name": placement.name,
            "code": placement.code,
            "position": placement.position,
            "description": placement.description,
            "width": placement.width,
            "height": placement.height,
            "is_active": placement.is_active,
            "created_at": placement.created_at.isoformat() if placement.created_at else None,
            "updated_at": placement.updated_at.isoformat() if placement.updated_at else None,
        }
    }


@router.put("/placements/{placement_id}", response_model=dict)
def update_ad_placement(
        placement_id: int,
        placement: AdPlacementUpdate,
        service: AdManagementService = Depends(get_ad_service)
):
    """更新广告位"""
    updated = service.update_ad_placement(placement_id, **placement.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="广告位不存在")

    return {
        "success": True,
        "data": {"id": updated.id},
        "message": "广告位更新成功"
    }


@router.delete("/placements/{placement_id}", response_model=dict)
def delete_ad_placement(
        placement_id: int,
        service: AdManagementService = Depends(get_ad_service)
):
    """删除广告位"""
    success = service.delete_ad_placement(placement_id)
    if not success:
        raise HTTPException(status_code=404, detail="广告位不存在")

    return {
        "success": True,
        "message": "广告位删除成功"
    }


# ==================== 广告 API ====================

@router.post("/", response_model=dict)
def create_ad(
        ad: AdCreate,
        service: AdManagementService = Depends(get_ad_service)
):
    """创建广告"""
    try:
        new_ad = service.create_ad(
            title=ad.title,
            ad_type=ad.ad_type,
            content=ad.content,
            image_url=ad.image_url,
            link_url=ad.link_url,
            alt_text=ad.alt_text,
            placement_id=ad.placement_id,
            start_date=ad.start_date,
            end_date=ad.end_date,
            budget=ad.budget,
            priority=ad.priority,
            target_audience=ad.target_audience,
            device_targeting=ad.device_targeting,
            geo_targeting=ad.geo_targeting
        )
        return {
            "success": True,
            "data": {"id": new_ad.id},
            "message": "广告创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=dict)
def list_ads(
        placement_id: Optional[int] = Query(None, description="广告位ID"),
        active_only: bool = Query(False, description="仅显示活跃广告"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        service: AdManagementService = Depends(get_ad_service)
):
    """获取广告列表"""
    ads = service.list_ads(
        placement_id=placement_id,
        active_only=active_only,
        skip=skip,
        limit=limit
    )

    return {
        "success": True,
        "data": [
            {
                "id": a.id,
                "title": a.title,
                "ad_type": a.ad_type,
                "placement_id": a.placement_id,
                "is_active": a.is_active,
                "priority": a.priority,
                "click_count": a.click_count,
                "impression_count": a.impression_count,
                "start_date": a.start_date.isoformat() if a.start_date else None,
                "end_date": a.end_date.isoformat() if a.end_date else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in ads
        ],
        "total": len(ads)
    }


@router.get("/{ad_id}", response_model=dict)
def get_ad(
        ad_id: int,
        service: AdManagementService = Depends(get_ad_service)
):
    """获取广告详情"""
    ad = service.get_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="广告不存在")

    return {
        "success": True,
        "data": {
            "id": ad.id,
            "title": ad.title,
            "ad_type": ad.ad_type,
            "content": ad.content,
            "image_url": ad.image_url,
            "link_url": ad.link_url,
            "alt_text": ad.alt_text,
            "placement_id": ad.placement_id,
            "start_date": ad.start_date.isoformat() if ad.start_date else None,
            "end_date": ad.end_date.isoformat() if ad.end_date else None,
            "click_count": ad.click_count,
            "impression_count": ad.impression_count,
            "budget": ad.budget,
            "cost_per_click": ad.cost_per_click,
            "cost_per_impression": ad.cost_per_impression,
            "is_active": ad.is_active,
            "priority": ad.priority,
            "target_audience": ad.target_audience,
            "device_targeting": ad.device_targeting,
            "geo_targeting": ad.geo_targeting,
            "created_at": ad.created_at.isoformat() if ad.created_at else None,
            "updated_at": ad.updated_at.isoformat() if ad.updated_at else None,
        }
    }


@router.put("/{ad_id}", response_model=dict)
def update_ad(
        ad_id: int,
        ad: AdUpdate,
        service: AdManagementService = Depends(get_ad_service)
):
    """更新广告"""
    updated = service.update_ad(ad_id, **ad.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="广告不存在")

    return {
        "success": True,
        "data": {"id": updated.id},
        "message": "广告更新成功"
    }


@router.delete("/{ad_id}", response_model=dict)
def delete_ad(
        ad_id: int,
        service: AdManagementService = Depends(get_ad_service)
):
    """删除广告"""
    success = service.delete_ad(ad_id)
    if not success:
        raise HTTPException(status_code=404, detail="广告不存在")

    return {
        "success": True,
        "message": "广告删除成功"
    }


# ==================== 广告展示 API ====================

@router.get("/display/{placement_code}", response_model=dict)
def get_ads_for_display(
        placement_code: str,
        request: Request,
        device_type: str = Query('all', description="设备类型"),
        user_type: str = Query('all', description="用户类型"),
        country: Optional[str] = Query(None, description="国家代码"),
        service: AdManagementService = Depends(get_ad_service)
):
    """获取用于展示的广告"""
    ads = service.get_active_ads_for_placement(
        placement_code=placement_code,
        device_type=device_type,
        user_type=user_type,
        country=country
    )

    # 记录展示
    for ad in ads:
        service.record_impression(
            ad_id=ad.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            page_url=str(request.url)
        )

    return {
        "success": True,
        "data": [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "image_url": a.image_url,
                "link_url": a.link_url,
                "alt_text": a.alt_text,
                "ad_type": a.ad_type,
            }
            for a in ads
        ]
    }


@router.post("/{ad_id}/click", response_model=dict)
def record_ad_click(
        ad_id: int,
        request: Request,
        service: AdManagementService = Depends(get_ad_service)
):
    """记录广告点击"""
    ad = service.get_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="广告不存在")

    click = service.record_click(
        ad_id=ad_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer")
    )

    return {
        "success": True,
        "data": {"click_id": click.id},
        "redirect_url": ad.link_url
    }


# ==================== 统计 API ====================

@router.get("/{ad_id}/stats", response_model=dict)
def get_ad_stats(
        ad_id: int,
        start_date: Optional[datetime] = Query(None, description="开始日期"),
        end_date: Optional[datetime] = Query(None, description="结束日期"),
        service: AdManagementService = Depends(get_ad_service)
):
    """获取广告统计"""
    ad = service.get_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="广告不存在")

    stats = service.get_ad_stats(ad_id, start_date, end_date)

    return {
        "success": True,
        "data": stats
    }


@router.get("/stats/revenue", response_model=dict)
def get_revenue_stats(
        start_date: Optional[datetime] = Query(None, description="开始日期"),
        end_date: Optional[datetime] = Query(None, description="结束日期"),
        service: AdManagementService = Depends(get_ad_service)
):
    """获取收益统计"""
    stats = service.get_revenue_stats(start_date, end_date)

    return {
        "success": True,
        "data": stats
    }
