"""
SQLAlchemy 模型定义 - PayoutRequest
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, Index

from . import Base  # 使用统一的 Base


class PayoutRequest(Base):
    """提现申请模型模型"""
    __tablename__ = 'payout_requests'


    __table_args__ = (
        Index('idx_payout_requests_user_id', 'user_id'),
        Index('idx_payout_requests_status', 'status'),
        Index('idx_payout_requests_created_at', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='提现申请 ID')

    user_id = Column(BigInteger, doc='用户ID')


    amount = Column(Numeric(10, 2), doc='提现金额')


    payment_method = Column(String(50), nullable=True, doc='支付方式: alipay, wechat, bank_transfer')

    payment_account = Column(String(200), nullable=True, doc='支付账号')

    account_name = Column(String(100), nullable=True, doc='账户姓名')

    status = Column(String(20), default='pending', doc='状态: pending, approved, rejected, completed')

    admin_notes = Column(Text, nullable=True, doc='管理员备注')


    processed_by = Column(BigInteger, nullable=True, doc='处理人ID')


    processed_at = Column(DateTime, nullable=True, doc='处理时间')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'payment_account': self.payment_account,
            'account_name': self.account_name,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'processed_by': self.processed_by,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
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
        return f'<PayoutRequest id={self.id}>'


