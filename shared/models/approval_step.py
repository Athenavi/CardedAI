"""
审批步骤模型

手动创建 - 不要重新生成此文件
"""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from shared.models import Base


class ApprovalStep(Base):
    """审批步骤模型"""

    __tablename__ = 'approval_steps'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, ForeignKey('approval_records.id'), nullable=False)
    level = Column(Integer, nullable=False)
    approver_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    action = Column(String(20), nullable=True)
    comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_approval_steps_approver_id', 'approver_id'),
        Index('idx_approval_steps_record_id', 'record_id'),
        Index('idx_approval_steps_record_level', 'record_id', 'level'),
        {'extend_existing': True}
    )

    def to_dict(self, exclude_sensitive=True):
        """序列化为字典"""
        result = {
            'id': self.id,
            'record_id': self.record_id,
            'level': self.level,
            'approver_id': self.approver_id,
            'action': self.action,
            'comment': self.comment,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        return result
