"""
FastBlog API Python SDK (V2)
提供同步和异步客户端
FastBlog V0.3.26.0521+ 兼容
"""

from .client import FastBlogClient, AsyncFastBlogClient

__version__ = "2.0.0"
__all__ = ["FastBlogClient", "AsyncFastBlogClient"]
