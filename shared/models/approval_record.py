"""
审批记录模型

手动创建 - 不要重新生成此文件
"""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String, func
from shared.models import Base


class ApprovalRecord(Base):
    """审批记录模型"""

    __tablename__ = 'approval_records'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    content_type = Column(String(50), nullable=False)
    content_id = Column(BigInteger, nullable=False)
    applicant_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    current_level = Column(Integer, nullable=False, default=1)
    max_level = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default='pending')
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_approval_records_applicant_id', 'applicant_id'),
        Index('idx_approval_records_content', 'content_type', 'content_id'),
        Index('idx_approval_records_created_at', 'created_at'),
        Index('idx_approval_records_status', 'status'),
        {'extend_existing': True}
    )

    def to_dict(self, exclude_sensitive=True):
        """序列化为字典"""
        result = {
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
        return result
