"""
SQLAlchemy 模型定义 - CryptoPayment
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base



class CryptoPayment(Base):
    """加密货币支付模型模型"""
    __tablename__ = 'crypto_payments'


    __table_args__ = (
        Index('idx_crypto_payment_transaction', 'transaction'),
        Index('idx_crypto_payment_wallet', 'wallet_address'),
        Index('idx_crypto_payment_tx_hash', 'tx_hash', unique=True),
        Index('idx_crypto_payment_status', 'status'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='加密支付 ID')

    transaction = Column(BigInteger, ForeignKey('payment_transactions.id'), doc='关联的交易记录')


    wallet_address = Column(String(255), nullable=True, doc='钱包地址')

    blockchain = Column(String(50), nullable=True, doc='区块链网络 (ethereum, bitcoin, etc.)')

    token_symbol = Column(String(10), nullable=True, doc='代币符号 (ETH, BTC, USDT, etc.)')

    tx_hash = Column(String(255), nullable=True, doc='区块链交易哈希')

    confirmations = Column(Integer, default=0, doc='确认数')


    required_confirmations = Column(Integer, default=6, doc='所需确认数')

    exchange_rate = Column(Numeric(10, 2), nullable=True, doc='兑换汇率')

    crypto_amount = Column(Numeric(10, 2), nullable=True, doc='加密货币金额')

    status = Column(String(20), default='waiting_payment', doc='支付状态')

    expires_at = Column(DateTime, nullable=True, doc='支付过期时间')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'transaction': self.transaction,
            'wallet_address': self.wallet_address,
            'blockchain': self.blockchain,
            'token_symbol': self.token_symbol,
            'tx_hash': self.tx_hash,
            'confirmations': self.confirmations,
            'required_confirmations': self.required_confirmations,
            'exchange_rate': self.exchange_rate,
            'crypto_amount': self.crypto_amount,
            'status': self.status,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
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
        return f'<CryptoPayment id={self.id}>'
