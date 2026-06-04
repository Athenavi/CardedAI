"""
SQLAlchemy 模型定义 - Ad
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base


class Ad(Base):
    """广告模型模型"""
    __tablename__ = 'ads'


    __table_args__ = (
        Index('idx_ads_placement_id', 'placement_id'),
        Index('idx_ads_is_active', 'is_active'),
        Index('idx_ads_dates', 'start_date', 'end_date'),
        Index('idx_ads_priority', 'priority'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='广告 ID')

    title = Column(String(200), nullable=True, doc='广告标题')

    content = Column(Text, nullable=True, doc='广告内容 (HTML/JavaScript代码)')


    image_url = Column(String(500), nullable=True, doc='广告图片URL')

    link_url = Column(String(500), nullable=True, doc='广告链接URL')

    alt_text = Column(String(200), nullable=True, doc='图片替代文本')

    ad_type = Column(String(20), default='html', doc='广告类型: html, image, google_adsense, baidu_union')

    placement_id = Column(BigInteger, ForeignKey('ad_placements.id'), nullable=True, doc='广告位ID')


    start_date = Column(DateTime, nullable=True, doc='广告开始时间')

    end_date = Column(DateTime, nullable=True, doc='广告结束时间')

    click_count = Column(BigInteger, default=0, doc='点击次数')


    impression_count = Column(BigInteger, default=0, doc='展示次数')


    budget = Column(Numeric(10, 2), nullable=True, doc='广告预算')


    cost_per_click = Column(Numeric(10, 2), nullable=True, doc='每次点击费用')


    cost_per_impression = Column(Numeric(10, 2), nullable=True, doc='每千次展示费用')


    is_active = Column(Boolean, default=True, doc='是否激活')


    priority = Column(Integer, default=0, doc='优先级 (数字越大优先级越高)')


    target_audience = Column(String(100), default='all', doc='目标受众 (all, registered, vip等)')

    device_targeting = Column(String(50), default='all', doc='设备定位: all, desktop, mobile')

    geo_targeting = Column(String(200), nullable=True, doc='地理定位 (国家/地区代码，逗号分隔)')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'link_url': self.link_url,
            'alt_text': self.alt_text,
            'ad_type': self.ad_type,
            'placement_id': self.placement_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'click_count': self.click_count,
            'impression_count': self.impression_count,
            'budget': self.budget,
            'cost_per_click': self.cost_per_click,
            'cost_per_impression': self.cost_per_impression,
            'is_active': self.is_active,
            'priority': self.priority,
            'target_audience': self.target_audience,
            'device_targeting': self.device_targeting,
            'geo_targeting': self.geo_targeting,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<Ad id={self.id}>'


