"""
API响应模型
"""
from typing import Any, Optional

from pydantic import BaseModel


class PaginationInfo(BaseModel):
    """
    分页信息模型
    """
    current_page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ApiResponse(BaseModel):
    """
    API通用响应模型
    
    success (bool): 请求是否成功
    data (Optional[Any]): 成功时返回的数据
    message (Optional[str]): 成功时返回的消息
    error (Optional[str]): 失败时返回的错误信息
    pagination (Optional[PaginationInfo]): 分页信息
    """
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    pagination: Optional[PaginationInfo] = None
