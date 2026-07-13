"""
SQLAlchemy 模型定义 - AlertRule
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class AlertRule(Base):
    """预警规则模型"""
    __tablename__ = 'intel_alert_rules'


    __table_args__ = (
        Index('idx_intel_ar_severity', 'severity'),
        Index('idx_intel_ar_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='规则 ID')

    name = Column(String(200), nullable=True, doc='规则名称')

    conditions = Column(Text, nullable=True, doc='触发条件 (JSON)')


    keywords = Column(Text, nullable=True, doc='关键词列表 (JSON)')


    severity = Column(String(20), nullable=True, doc='严重程度 (low/medium/high/critical)')

    actions = Column(Text, nullable=True, doc='触发动作 (JSON)')


    is_active = Column(Boolean, default=True, doc='是否启用')


    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建用户')


    last_triggered_at = Column(DateTime, nullable=True, doc='最后触发时间')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'conditions': self.conditions,
            'keywords': self.keywords,
            'severity': self.severity,
            'actions': self.actions,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<AlertRule id={self.id}>'


