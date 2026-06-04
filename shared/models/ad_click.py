"""
SQLAlchemy 模型定义 - AdClick
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class AdClick(Base):
    """广告点击记录模型模型"""
    __tablename__ = 'ad_clicks'


    __table_args__ = (
        Index('idx_ad_clicks_ad_id', 'ad_id'),
        Index('idx_ad_clicks_clicked_at', 'clicked_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='点击记录 ID')

    ad_id = Column(BigInteger, ForeignKey('ads.id'), doc='广告ID')


    user_id = Column(BigInteger, nullable=True, doc='用户ID (如果已登录)')


    ip_address = Column(String(45), nullable=True, doc='IP地址')

    user_agent = Column(Text, nullable=True, doc='用户代理')


    referrer = Column(String(500), nullable=True, doc='来源页面')

    clicked_at = Column(DateTime, doc='点击时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'ad_id': self.ad_id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'referrer': self.referrer,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<AdClick id={self.id}>'


