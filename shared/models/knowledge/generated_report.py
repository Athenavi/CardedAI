"""
SQLAlchemy 模型定义 - GeneratedReport
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class GeneratedReport(Base):
    """生成的报告模型"""
    __tablename__ = 'knowledge_generated_reports'


    __table_args__ = (
        Index('idx_gr_template', 'template_id'),
        Index('idx_gr_status', 'status'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='报告 ID')

    template_id = Column(BigInteger, ForeignKey('knowledge_report_templates.id'), nullable=True, doc='使用的模板 ID')


    title = Column(String(500), nullable=True, doc='报告标题')

    content = Column(Text, nullable=True, doc='生成的报告内容 (Markdown)')


    knowledge_base_ids = Column(Text, nullable=True, doc='引用的知识库 ID 列表 (JSON)')


    status = Column(String(20), default='generating', doc='状态 (generating/completed/failed)')

    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建用户')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'template_id': self.template_id,
            'title': self.title,
            'content': self.content,
            'knowledge_base_ids': self.knowledge_base_ids,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<GeneratedReport id={self.id}>'


