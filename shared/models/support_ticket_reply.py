"""
SQLAlchemy 模型定义 - SupportTicketReply
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class SupportTicketReply(Base):
    """工单回复模型模型"""
    __tablename__ = 'support_ticket_replies'


    __table_args__ = (
        Index('idx_reply_ticket', 'ticket_id'),
        Index('idx_reply_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='回复 ID')

    ticket_id = Column(BigInteger, ForeignKey('support_tickets.id'), doc='工单 ID')


    user_id = Column(BigInteger, ForeignKey('users.id'), doc='回复者用户 ID')

    content = Column(Text, nullable=False, doc='回复内容')

    is_staff = Column(Boolean, default=False, doc='是否为工作人员回复')

    attachments = Column(Text, nullable=True, doc='附件列表（JSON格式）')

    created_at = Column(DateTime, doc='创建时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'content': self.content,
            'is_staff': self.is_staff,
            'attachments': self.attachments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<SupportTicketReply id={self.id}>'
