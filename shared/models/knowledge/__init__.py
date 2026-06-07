"""
knowledge 子模块 - 模型定义
由代码生成器自动生成 - 请勿手动修改
"""

# 导入所有 knowledge 模型，确保表注册到 Base.metadata
from shared.models.knowledge.knowledge_base import KnowledgeBase
from shared.models.knowledge.knowledge_document import KnowledgeDocument
from shared.models.knowledge.document_chunk import DocumentChunk
from shared.models.knowledge.generated_report import GeneratedReport
from shared.models.knowledge.report_template import ReportTemplate

__all__ = [
    'KnowledgeBase',
    'KnowledgeDocument',
    'DocumentChunk',
    'GeneratedReport',
    'ReportTemplate',
]
