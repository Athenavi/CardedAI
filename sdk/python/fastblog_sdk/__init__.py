"""
FastBlog API Python SDK (V2)
提供同步和异步客户端，以及情报、知识、工作流扩展模块
FastBlog V0.3.26.0521+ 兼容
"""

from .client import FastBlogClient, AsyncFastBlogClient
from .intel import IntelMixin, AsyncIntelMixin
from .knowledge import KnowledgeMixin, AsyncKnowledgeMixin
from .workflow import WorkflowMixin, AsyncWorkflowMixin

__version__ = "2.0.0"
__all__ = [
    "FastBlogClient",
    "AsyncFastBlogClient",
    "IntelMixin",
    "AsyncIntelMixin",
    "KnowledgeMixin",
    "AsyncKnowledgeMixin",
    "WorkflowMixin",
    "AsyncWorkflowMixin",
]
