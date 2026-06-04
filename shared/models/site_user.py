"""
SQLAlchemy 模型定义 - SiteUser
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class SiteUser(Base):
    """站点用户关联模型模型"""
    __tablename__ = 'site_users'


    __table_args__ = (
        Index('idx_site_users_site', 'site_id'),
        Index('idx_site_users_user', 'user_id'),
        Index('idx_site_users_unique', 'site_id', 'user_id', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='关联 ID')

    site_id = Column(BigInteger, ForeignKey('sites.id'), doc='站点 ID')


    user_id = Column(BigInteger, ForeignKey('users.id'), doc='用户 ID')


    role = Column(String(50), default='subscriber', doc='在该站点的角色')

    is_active = Column(Boolean, default=True, doc='是否激活')


    joined_at = Column(DateTime, doc='加入时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'site_id': self.site_id,
            'user_id': self.user_id,
            'role': self.role,
            'is_active': self.is_active,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<SiteUser id={self.id}>'
