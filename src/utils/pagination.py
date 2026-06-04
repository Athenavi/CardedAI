"""
统一分页和排序工具

提供标准化的分页参数解析和排序功能
支持游标分页和偏移量分页
"""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import Query


class PaginationParams:
    """分页参数"""

    def __init__(
            self,
            page: int = Query(1, ge=1, description="页码（从1开始）"),
            per_page: int = Query(20, ge=1, le=100, description="每页数量（1-100）"),
            sort_by: Optional[str] = Query(None, description="排序字段，如: created_at,updated_at"),
            sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="排序方向: asc或desc"),
    ):
        self.page = page
        self.per_page = per_page
        self.sort_by = sort_by
        self.sort_order = sort_order

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """获取限制数量"""
        return self.per_page

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "page": self.page,
            "per_page": self.per_page,
            "offset": self.offset,
            "limit": self.limit,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
        }


def create_pagination_response(
        data: List[Any],
        total: int,
        page: int,
        per_page: int,
        additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建标准化的分页响应
    
    Args:
        data: 数据列表
        total: 总记录数
        page: 当前页码
        per_page: 每页数量
        additional_data: 额外的数据
    
    Returns:
        包含数据和分页信息的字典
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    response = {
        "data": data,
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    }

    if additional_data:
        response.update(additional_data)

    return response


def parse_sort_params(
        sort_by: Optional[str],
        sort_order: str = "desc",
        allowed_fields: Optional[List[str]] = None
) -> Tuple[Optional[str], str]:
    """
    解析排序参数
    
    Args:
        sort_by: 排序字段
        sort_order: 排序方向
        allowed_fields: 允许的排序字段列表
    
    Returns:
        (排序字段, 排序方向) 元组
    
    Raises:
        ValueError: 如果排序字段不在允许列表中
    """
    if not sort_by:
        return None, sort_order

    # 验证排序字段
    if allowed_fields and sort_by not in allowed_fields:
        raise ValueError(f"Invalid sort field: {sort_by}. Allowed fields: {allowed_fields}")

    # 验证排序方向
    if sort_order.lower() not in ['asc', 'desc']:
        sort_order = 'desc'

    return sort_by, sort_order.lower()


class CursorPagination:
    """
    游标分页实现
    
    适用于大数据集，性能优于偏移量分页
    """

    def __init__(
            self,
            cursor: Optional[str] = Query(None, description="游标（上一页最后一条记录的ID或时间戳）"),
            limit: int = Query(20, ge=1, le=100, description="每页数量"),
            sort_by: str = Query("id", description="排序字段"),
            sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    ):
        self.cursor = cursor
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order

    def get_where_clause(self, current_cursor_value: Any) -> str:
        """
        生成WHERE子句
        
        Args:
            current_cursor_value: 当前游标值
        
        Returns:
            SQL WHERE子句
        """
        if self.sort_order == 'desc':
            return f"{self.sort_by} < :cursor_value"
        else:
            return f"{self.sort_by} > :cursor_value"

    def create_response(
            self,
            data: List[Any],
            has_more: bool,
            next_cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建游标分页响应
        
        Args:
            data: 数据列表
            has_more: 是否还有更多数据
            next_cursor: 下一页游标
        
        Returns:
            包含数据和分页信息的字典
        """
        return {
            "data": data,
            "pagination": {
                "limit": self.limit,
                "has_more": has_more,
                "next_cursor": next_cursor,
                "sort_by": self.sort_by,
                "sort_order": self.sort_order,
            }
        }


# 导出
__all__ = [
    'PaginationParams',
    'create_pagination_response',
    'parse_sort_params',
    'CursorPagination',
]
