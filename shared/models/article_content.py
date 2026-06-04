"""
SQLAlchemy 模型定义 - ArticleContent
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey

from . import Base  # 使用统一的 Base



class ArticleContent(Base):
    """文章内容模型模型"""
    __tablename__ = 'article_content'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='ID')

    article = Column(BigInteger, ForeignKey('articles.id'), doc='文章')


    passwd = Column(String(255), nullable=True, doc='访问密码')

    content = Column(Text, nullable=False, doc='文章内容')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    language_code = Column(String(255), default='zh-CN', doc='语言代码（文章国际化）')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'article': self.article,
            'passwd': self.passwd,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'language_code': self.language_code,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ArticleContent id={self.id}>'


