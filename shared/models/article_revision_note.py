"""
SQLAlchemy 模型定义 - ArticleRevisionNote
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class ArticleRevisionNote(Base):
    """文章修订注释模型（为每次修订添加说明和备注）模型"""
    __tablename__ = 'article_revision_notes'

    __table_args__ = (
        Index('idx_revision_notes_revision', 'revision_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='注释 ID')

    revision_id = Column(BigInteger, ForeignKey('article_revisions.id'), doc='关联的修订版本 ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), doc='添加注释的用户 ID')

    note_content = Column(Text, nullable=False, doc='注释内容')

    created_at = Column(DateTime, doc='创建时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'revision_id': self.revision_id,
            'user_id': self.user_id,
            'note_content': self.note_content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ArticleRevisionNote id={self.id}>'
