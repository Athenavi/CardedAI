"""
SQLAlchemy 模型定义 - ApprovalStep
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class ApprovalStep(Base):
    """审批步骤模型模型"""
    __tablename__ = 'approval_steps'


    __table_args__ = (
        Index('idx_approval_steps_record', 'record_id'),
        Index('idx_approval_steps_approver', 'approver_id'),
        Index('idx_approval_steps_level', 'level'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='审批步骤 ID')

    record_id = Column(BigInteger, ForeignKey('approval_records.id'), doc='审批记录 ID')


    level = Column(Integer, index=True, doc='审批级别')


    approver_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='审批人 ID')


    action = Column(String(20), nullable=True, doc='操作（approved/rejected）')

    comment = Column(Text, nullable=True, doc='审批意见')


    reviewed_at = Column(DateTime, nullable=True, doc='审核时间')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'record_id': self.record_id,
            'level': self.level,
            'approver_id': self.approver_id,
            'action': self.action,
            'comment': self.comment,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ApprovalStep id={self.id}>'
