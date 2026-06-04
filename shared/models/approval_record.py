"""
SQLAlchemy 模型定义 - ApprovalRecord
内容审批记录模型
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class ApprovalRecord(Base):
    """内容审批记录模型"""
    __tablename__ = 'approval_records'

    __table_args__ = (
        Index('idx_approval_records_content', 'content_type', 'content_id'),
        Index('idx_approval_records_applicant_id', 'applicant_id'),
        Index('idx_approval_records_status', 'status'),
        Index('idx_approval_records_created_at', 'created_at'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='审批记录 ID')

    content_type = Column(String(50), nullable=False, doc='内容类型 (article/comment)')

    content_id = Column(BigInteger, nullable=False, doc='内容 ID')

    applicant_id = Column(BigInteger, ForeignKey('users.id'), nullable=False, doc='申请人 ID')

    current_level = Column(Integer, default=1, nullable=False, doc='当前审批级别')

    max_level = Column(Integer, default=1, nullable=False, doc='最大审批级别')

    status = Column(String(20), default='pending', nullable=False, doc='审批状态 (pending/approved/rejected/cancelled)')

    created_at = Column(DateTime, nullable=True, doc='创建时间')

    completed_at = Column(DateTime, nullable=True, doc='完成时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'applicant_id': self.applicant_id,
            'current_level': self.current_level,
            'max_level': self.max_level,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ApprovalRecord id={self.id} status={self.status}>'
