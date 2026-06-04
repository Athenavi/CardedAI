"""
SQLAlchemy 模型定义 - ShareStat
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class ShareStat(Base):
    """分享统计模型模型"""
    __tablename__ = 'share_stats'


    __table_args__ = (
        Index('idx_share_stats_article_platform', 'article_id', 'platform'),
        Index('idx_share_stats_created', 'created_at'),
        Index('idx_share_stats_article_created', 'article_id', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='统计 ID')

    article_id = Column(BigInteger, ForeignKey('articles.id'), doc='文章 ID')


    platform = Column(String(50), index=True, nullable=True, doc='分享平台 (wechat, weibo, twitter, facebook, linkedin, zhihu, juejin, segmentfault, telegram, copy)')

    shared_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='分享者用户 ID')


    ip_address = Column(String(45), nullable=True, doc='分享者 IP 地址')

    user_agent = Column(String(500), nullable=True, doc='用户代理')

    created_at = Column(DateTime, doc='分享时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'article_id': self.article_id,
            'platform': self.platform,
            'shared_by': self.shared_by,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ShareStat id={self.id}>'


