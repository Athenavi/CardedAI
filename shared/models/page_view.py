"""
SQLAlchemy 模型定义 - PageView

由 config/models.yaml 的 PageView 定义落地（等价于代码生成器产物）。
用于记录页面访问明细，支撑真实 PV/UV、流量来源与停留时长统计。
"""

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from . import Base


class PageView(Base):
    """访问明细（页面浏览事件）"""
    __tablename__ = 'page_views'

    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='主键ID')

    path = Column(String(512), index=True, doc='访问路径')

    article_id = Column(BigInteger, nullable=True, index=True, doc='关联文章ID（非文章页为空）')

    user_id = Column(BigInteger, nullable=True, index=True, doc='已登录用户ID（匿名访问为空）')

    visitor_hash = Column(String(64), index=True, doc='访客指纹（IP+UA 哈希，用于 UV 去重）')

    referrer = Column(String(512), nullable=True, doc='来源页面')

    user_agent = Column(String(512), nullable=True, doc='User-Agent（用于设备分类）')

    country = Column(String(64), nullable=True, doc='国家/地区')

    duration_ms = Column(Integer, nullable=True, doc='停留时长（毫秒）')

    created_at = Column(DateTime, index=True, doc='记录时间')

    def to_dict(self):
        return {
            'id': self.id,
            'path': self.path,
            'article_id': self.article_id,
            'user_id': self.user_id,
            'referrer': self.referrer,
            'country': self.country,
            'duration_ms': self.duration_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<PageView id={self.id} path={self.path}>'
