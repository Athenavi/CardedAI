"""
SQLAlchemy 模型定义 - User
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class User(Base):
    """用户模型模型"""
    __tablename__ = 'users'


    __table_args__ = (
        Index('idx_users_username', 'username', unique=True),
        Index('idx_users_email', 'email', unique=True),
        Index('idx_users_is_active', 'is_active'),
        Index('idx_users_vip_level', 'vip_level'),
        Index('idx_users_date_joined', 'date_joined'),
        Index('idx_users_is_superuser', 'is_superuser'),
        Index('idx_users_last_login', 'last_login_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='用户 ID')

    username = Column(String(255), unique=True, nullable=True, doc='用户名')

    email = Column(String(255), nullable=True, doc='邮箱')

    password = Column(String(255), nullable=True, doc='密码（哈希后存储）')

    profile_picture = Column(String(255), nullable=True, doc='个人资料图片')

    bio = Column(String(255), nullable=True, doc='个人简介')

    profile_private = Column(Boolean, default=False, doc='是否私密资料')


    vip_level = Column(BigInteger, default=0, doc='VIP 等级')


    vip_expires_at = Column(DateTime, nullable=True, doc='VIP 过期时间')

    is_active = Column(Boolean, default=True, doc='是否激活')


    is_superuser = Column(Boolean, default=False, doc='是否为超级管理员')


    date_joined = Column(DateTime, doc='注册时间')

    last_login_at = Column(DateTime, nullable=True, doc='上次登录时间')

    locale = Column(String(255), default='zh_CN', doc='语言设置')

    is_staff = Column(Boolean, default=False, doc='是否为工作人员')


    last_login_ip = Column(String(255), nullable=True, doc='上次登录 IP')

    register_ip = Column(String(255), nullable=True, doc='注册 IP')

    is_2fa_enabled = Column(Boolean, default=False, doc='是否启用双因素认证')


    totp_secret = Column(String(32), nullable=True, doc='TOTP 密钥')

    backup_codes = Column(Text, nullable=True, doc='备用码(JSON格式存储)')



    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'profile_private': self.profile_private,
            'vip_level': self.vip_level,
            'vip_expires_at': self.vip_expires_at.isoformat() if self.vip_expires_at else None,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,
            'date_joined': self.date_joined.isoformat() if self.date_joined else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'locale': self.locale,
            'is_staff': self.is_staff,
            'last_login_ip': self.last_login_ip,
            'register_ip': self.register_ip,
            'is_2fa_enabled': self.is_2fa_enabled,
            'totp_secret': self.totp_secret,
            'backup_codes': self.backup_codes,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<User id={self.id}>'


