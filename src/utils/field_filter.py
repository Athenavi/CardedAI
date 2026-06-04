"""
API 响应字段过滤工具

提供 fields 参数支持，允许客户端指定返回的字段
减少不必要的数据传输，提高API性能
"""

from typing import Dict, List, Optional, Union


def filter_fields(data: Union[Dict, List], fields_param: Optional[str] = None) -> Union[Dict, List]:
    """
    根据 fields 参数过滤数据
    
    Args:
        data: 原始数据（字典或列表）
        fields_param: fields 查询参数值，逗号分隔的字段名
                     支持嵌套字段，如: "id,title,author.username"
    
    Returns:
        过滤后的数据
    
    Examples:
        >>> data = {"id": 1, "title": "Test", "content": "...", "author": {"id": 2, "username": "admin"}}
        >>> filter_fields(data, "id,title")
        {"id": 1, "title": "Test"}
        
        >>> filter_fields(data, "id,author.username")
        {"id": 1, "author": {"username": "admin"}}
    """
    if not fields_param or fields_param.strip() == '':
        return data

    # 解析字段列表
    requested_fields = [f.strip() for f in fields_param.split(',') if f.strip()]

    if isinstance(data, list):
        return [filter_fields(item, fields_param) for item in data]

    if isinstance(data, dict):
        filtered = {}
        for field_path in requested_fields:
            _set_nested_field(filtered, data, field_path)
        return filtered

    return data


def _set_nested_field(target: Dict, source: Dict, field_path: str):
    """
    设置嵌套字段到目标字典
    
    Args:
        target: 目标字典
        source: 源字典
        field_path: 字段路径，如 "author.username"
    """
    parts = field_path.split('.')

    if len(parts) == 1:
        # 简单字段
        field_name = parts[0]
        if field_name in source:
            target[field_name] = source[field_name]
    else:
        # 嵌套字段
        top_level = parts[0]
        remaining_path = '.'.join(parts[1:])

        if top_level in source and isinstance(source[top_level], dict):
            if top_level not in target:
                target[top_level] = {}

            # 递归处理嵌套字段
            _set_nested_field(target[top_level], source[top_level], remaining_path)


def parse_fields_param(fields_param: str) -> List[str]:
    """
    解析 fields 参数为字段列表
    
    Args:
        fields_param: fields 查询参数值
    
    Returns:
        字段名列表
    """
    if not fields_param:
        return []

    return [f.strip() for f in fields_param.split(',') if f.strip()]


def validate_fields(data: Dict, allowed_fields: List[str], fields_param: str) -> List[str]:
    """
    验证请求的字段是否在允许的范围内
    
    Args:
        data: 数据字典
        allowed_fields: 允许的字段列表
        fields_param: 请求的 fields 参数
    
    Returns:
        无效的字段列表
    """
    if not fields_param:
        return []

    requested = parse_fields_param(fields_param)
    invalid_fields = []

    for field in requested:
        # 只检查顶级字段
        top_level = field.split('.')[0]
        if top_level not in allowed_fields:
            invalid_fields.append(field)

    return invalid_fields


# 导出
__all__ = ['filter_fields', 'parse_fields_param', 'validate_fields']
