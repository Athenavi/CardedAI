"""
日志工具模块
提供统一的日志记录功能
"""

from src.unified_logger import default_logger as logger


def get_logger(name=None, **kwargs):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（可选）
        **kwargs: 其他关键字参数
        
    Returns:
        日志记录器实例
    """
    if name:
        print(f"Logger requested for: {name}")
    return logger
