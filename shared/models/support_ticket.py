"""
SQLAlchemy 模型定义 - SupportTicket
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class SupportTicket(Base):
    """技术支持工单模型模型"""
    __tablename__ = 'support_tickets'


    __table_args__ = (
        Index('idx_ticket_number', 'ticket_number', unique=True),
        Index('idx_ticket_user', 'user_id'),
        Index('idx_ticket_status', 'status'),
        Index('idx_ticket_priority', 'priority'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='工单 ID')

    ticket_number = Column(String(50), unique=True, nullable=True, doc='工单编号')

    user_id = Column(BigInteger, ForeignKey('users.id'), doc='用户 ID')


    license_id = Column(BigInteger, ForeignKey('enterprise_licenses.id'), nullable=True, doc='关联的许可证 ID')

    subject = Column(String(255), nullable=True, doc='工单主题')

    description = Column(Text, nullable=False, doc='问题描述')

    priority = Column(String(20), default='medium', doc='优先级')

    status = Column(String(20), default='open', doc='工单状态')

    category = Column(String(50), nullable=True, doc='问题分类')

    assigned_to = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='分配给的技术支持人员 ID')

    resolved_at = Column(DateTime, nullable=True, doc='解决时间')

    closed_at = Column(DateTime, nullable=True, doc='关闭时间')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'user_id': self.user_id,
            'license_id': self.license_id,
            'subject': self.subject,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'category': self.category,
            'assigned_to': self.assigned_to,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
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
        return f'<SupportTicket id={self.id}>'
