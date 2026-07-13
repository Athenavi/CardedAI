"""
SQLAlchemy 模型定义 - ReportTemplate
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class ReportTemplate(Base):
    """报告模板模型"""
    __tablename__ = 'knowledge_report_templates'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='模板 ID')

    name = Column(String(200), nullable=True, doc='模板名称')

    description = Column(Text, nullable=True, doc='模板描述')


    template_content = Column(Text, nullable=True, doc='模板内容 (Markdown/Jinja2)')


    sections = Column(Text, nullable=True, doc='模板章节定义 (JSON)')


    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建用户')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, nullable=True, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_content': self.template_content,
            'sections': self.sections,
            'created_by': self.created_by,
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
        return f'<ReportTemplate id={self.id}>'


