"""
广告管理服务
提供广告的增删改查、统计和展示功能
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from shared.models import AdPlacement, Ad, AdClick, AdImpression


class AdManagementService:
    """广告管理服务类"""

    def __init__(self, db_session: Session):
        self.db = db_session

    # ==================== 广告位管理 ====================

    def create_ad_placement(self, name: str, code: str, position: str,
                            description: str = None, width: int = None,
                            height: int = None) -> AdPlacement:
        """创建广告位"""
        placement = AdPlacement(
            name=name,
            code=code,
            position=position,
            description=description,
            width=width,
            height=height,
            is_active=True
        )
        self.db.add(placement)
        self.db.commit()
        self.db.refresh(placement)
        return placement

    def get_ad_placement(self, placement_id: int) -> Optional[AdPlacement]:
        """获取广告位"""
        return self.db.query(AdPlacement).filter(AdPlacement.id == placement_id).first()

    def get_ad_placement_by_code(self, code: str) -> Optional[AdPlacement]:
        """根据代码获取广告位"""
        return self.db.query(AdPlacement).filter(AdPlacement.code == code).first()

    def list_ad_placements(self, active_only: bool = False,
                           skip: int = 0, limit: int = 100) -> List[AdPlacement]:
        """获取广告位列表"""
        query = self.db.query(AdPlacement)
        if active_only:
            query = query.filter(AdPlacement.is_active == True)

        return query.order_by(AdPlacement.created_at.desc()).offset(skip).limit(limit).all()

    def update_ad_placement(self, placement_id: int, **kwargs) -> Optional[AdPlacement]:
        """更新广告位"""
        placement = self.get_ad_placement(placement_id)
        if not placement:
            return None

        for key, value in kwargs.items():
            if hasattr(placement, key):
                setattr(placement, key, value)

        placement.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(placement)
        return placement

    def delete_ad_placement(self, placement_id: int) -> bool:
        """删除广告位"""
        placement = self.get_ad_placement(placement_id)
        if not placement:
            return False

        self.db.delete(placement)
        self.db.commit()
        return True

    # ==================== 广告管理 ====================

    def create_ad(self, title: str, ad_type: str = 'html',
                  content: str = None, image_url: str = None,
                  link_url: str = None, placement_id: int = None,
                  start_date: datetime = None, end_date: datetime = None,
                  budget: float = None, priority: int = 0,
                  target_audience: str = 'all', device_targeting: str = 'all',
                  geo_targeting: str = None, alt_text: str = None) -> Ad:
        """创建广告"""
        ad = Ad(
            title=title,
            ad_type=ad_type,
            content=content,
            image_url=image_url,
            link_url=link_url,
            alt_text=alt_text,
            placement_id=placement_id,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            priority=priority,
            target_audience=target_audience,
            device_targeting=device_targeting,
            geo_targeting=geo_targeting,
            is_active=True
        )
        self.db.add(ad)
        self.db.commit()
        self.db.refresh(ad)
        return ad

    def get_ad(self, ad_id: int) -> Optional[Ad]:
        """获取广告"""
        return self.db.query(Ad).filter(Ad.id == ad_id).first()

    def list_ads(self, placement_id: int = None, active_only: bool = False,
                 skip: int = 0, limit: int = 100) -> List[Ad]:
        """获取广告列表"""
        query = self.db.query(Ad)

        if placement_id:
            query = query.filter(Ad.placement_id == placement_id)

        if active_only:
            query = query.filter(Ad.is_active == True)
            now = datetime.now()
            query = query.filter(
                or_(
                    Ad.start_date == None,
                    Ad.start_date <= now
                ),
                or_(
                    Ad.end_date == None,
                    Ad.end_date >= now
                )
            )

        return query.order_by(Ad.priority.desc(), Ad.created_at.desc()).offset(skip).limit(limit).all()

    def get_active_ads_for_placement(self, placement_code: str,
                                     device_type: str = 'all',
                                     user_type: str = 'all',
                                     country: str = None) -> List[Ad]:
        """获取指定广告位的活跃广告"""
        placement = self.get_ad_placement_by_code(placement_code)
        if not placement or not placement.is_active:
            return []

        now = datetime.now()
        query = self.db.query(Ad).filter(
            Ad.placement_id == placement.id,
            Ad.is_active == True,
            or_(Ad.start_date == None, Ad.start_date <= now),
            or_(Ad.end_date == None, Ad.end_date >= now)
        )

        # 设备定位过滤
        if device_type != 'all':
            query = query.filter(
                or_(
                    Ad.device_targeting == 'all',
                    Ad.device_targeting == device_type
                )
            )

        # 用户类型过滤
        if user_type != 'all':
            query = query.filter(
                or_(
                    Ad.target_audience == 'all',
                    Ad.target_audience == user_type
                )
            )

        # 地理定位过滤
        if country:
            query = query.filter(
                or_(
                    Ad.geo_targeting == None,
                    Ad.geo_targeting == '',
                    func.find_in_set(country, Ad.geo_targeting) > 0
                )
            )

        return query.order_by(Ad.priority.desc()).all()

    def update_ad(self, ad_id: int, **kwargs) -> Optional[Ad]:
        """更新广告"""
        ad = self.get_ad(ad_id)
        if not ad:
            return None

        for key, value in kwargs.items():
            if hasattr(ad, key):
                setattr(ad, key, value)

        ad.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(ad)
        return ad

    def delete_ad(self, ad_id: int) -> bool:
        """删除广告"""
        ad = self.get_ad(ad_id)
        if not ad:
            return False

        self.db.delete(ad)
        self.db.commit()
        return True

    # ==================== 广告统计 ====================

    def record_impression(self, ad_id: int, user_id: int = None,
                          ip_address: str = None, user_agent: str = None,
                          page_url: str = None) -> AdImpression:
        """记录广告展示"""
        impression = AdImpression(
            ad_id=ad_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            page_url=page_url
        )
        self.db.add(impression)

        # 更新广告展示计数
        ad = self.get_ad(ad_id)
        if ad:
            ad.impression_count = (ad.impression_count or 0) + 1

        self.db.commit()
        return impression

    def record_click(self, ad_id: int, user_id: int = None,
                     ip_address: str = None, user_agent: str = None,
                     referrer: str = None) -> AdClick:
        """记录广告点击"""
        click = AdClick(
            ad_id=ad_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )
        self.db.add(click)

        # 更新广告点击计数
        ad = self.get_ad(ad_id)
        if ad:
            ad.click_count = (ad.click_count or 0) + 1

        self.db.commit()
        return click

    def get_ad_stats(self, ad_id: int,
                     start_date: datetime = None,
                     end_date: datetime = None) -> Dict[str, Any]:
        """获取广告统计数据"""
        query_impressions = self.db.query(func.count(AdImpression.id)).filter(
            AdImpression.ad_id == ad_id
        )
        query_clicks = self.db.query(func.count(AdClick.id)).filter(
            AdClick.ad_id == ad_id
        )

        if start_date:
            query_impressions = query_impressions.filter(AdImpression.displayed_at >= start_date)
            query_clicks = query_clicks.filter(AdClick.clicked_at >= start_date)

        if end_date:
            query_impressions = query_impressions.filter(AdImpression.displayed_at <= end_date)
            query_clicks = query_clicks.filter(AdClick.clicked_at <= end_date)

        impressions = query_impressions.scalar() or 0
        clicks = query_clicks.scalar() or 0

        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        return {
            'impressions': impressions,
            'clicks': clicks,
            'ctr': round(ctr, 2),  # 点击率
        }

    def get_placement_stats(self, placement_id: int,
                            start_date: datetime = None,
                            end_date: datetime = None) -> Dict[str, Any]:
        """获取广告位统计数据"""
        # 获取该广告位下的所有广告
        ads = self.db.query(Ad).filter(Ad.placement_id == placement_id).all()

        total_impressions = 0
        total_clicks = 0

        for ad in ads:
            stats = self.get_ad_stats(ad.id, start_date, end_date)
            total_impressions += stats['impressions']
            total_clicks += stats['clicks']

        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

        return {
            'total_ads': len(ads),
            'active_ads': sum(1 for ad in ads if ad.is_currently_active),
            'impressions': total_impressions,
            'clicks': total_clicks,
            'ctr': round(ctr, 2),
        }

    def get_revenue_stats(self, start_date: datetime = None,
                          end_date: datetime = None) -> Dict[str, Any]:
        """获取收益统计"""
        query = self.db.query(Ad).filter(Ad.is_active == True)

        if start_date:
            query = query.filter(Ad.created_at >= start_date)
        if end_date:
            query = query.filter(Ad.created_at <= end_date)

        ads = query.all()

        total_revenue = 0
        for ad in ads:
            # 计算收益：点击数 * 每次点击费用 + 展示数 * 每千次展示费用 / 1000
            cpc_revenue = (ad.click_count or 0) * (ad.cost_per_click or 0)
            cpm_revenue = (ad.impression_count or 0) * (ad.cost_per_impression or 0) / 1000
            total_revenue += cpc_revenue + cpm_revenue

        return {
            'total_revenue': round(total_revenue, 2),
            'total_ads': len(ads),
            'total_clicks': sum(ad.click_count or 0 for ad in ads),
            'total_impressions': sum(ad.impression_count or 0 for ad in ads),
        }
