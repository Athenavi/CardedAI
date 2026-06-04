"""
SQLAlchemy 模型定义 - SensitiveWord
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class SensitiveWord(Base):
    """敏感词模型模型"""
    __tablename__ = 'sensitive_words'


    __table_args__ = (
        Index('idx_sensitive_word_level', 'level'),
        Index('idx_sensitive_word_category', 'category'),
        Index('idx_sensitive_word_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='敏感词 ID')

    word = Column(String(100), unique=True, nullable=True, doc='敏感词内容')

    level = Column(Integer, default=1, doc='敏感级别 (1:低, 2:中, 3:高)')


    action = Column(String(50), default='block', doc='处理方式 (block:拦截, replace:替换, warn:警告)')

    replacement = Column(String(100), nullable=True, doc='替换词（当action为replace时使用）')

    category = Column(String(50), nullable=True, doc='分类（政治、色情、暴力等）')

    is_active = Column(Boolean, default=True, doc='是否激活')


    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建者用户ID')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'word': self.word,
            'level': self.level,
            'action': self.action,
            'replacement': self.replacement,
            'category': self.category,
            'is_active': self.is_active,
            'created_by': self.created_by,
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
        return f'<SensitiveWord id={self.id}>'


