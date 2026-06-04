"""
统一异常处理工具
提供安全的异常处理机制，避免暴露内部敏感信息
"""

import traceback

from src.unified_logger import default_logger as logger


class SafeException(Exception):
    """安全异常类 - 可以暴露给用户的异常"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def handle_api_exception(e: Exception, default_message: str = "操作失败，请稍后重试") -> str:
    """
    安全地处理 API 异常，返回通用错误消息
    
    Args:
        e: 捕获的异常对象
        default_message: 默认返回的错误消息
        
    Returns:
        str: 可以安全返回给用户的错误消息
    """
    # 记录详细的错误日志（仅在后端日志中）
    logger.error(f"API 错误：{str(e)}")
    logger.error(traceback.format_exc())
    
    # 如果是 SafeException，返回具体消息
    if isinstance(e, SafeException):
        return e.message
    
    # 对于已知的业务异常，返回友好的错误消息
    error_str = str(e).lower()
    
    # 数据库相关错误
    if any(keyword in error_str for keyword in ['database', 'sqlalchemy', 'postgresql', 'mysql']):
        logger.warning(f"数据库错误：{str(e)}")
        return "数据库操作失败，请稍后重试"
    
    # 认证相关错误
    if any(keyword in error_str for keyword in ['unauthorized', 'forbidden', 'permission']):
        return "权限不足或认证失败"
    
    # 文件相关错误
    if any(keyword in error_str for keyword in ['file', 'upload', 'download']):
        return "文件操作失败"
    
    # 网络相关错误
    if any(keyword in error_str for keyword in ['network', 'connection', 'timeout']):
        return "网络连接失败，请检查网络后重试"
    
    # 数据验证错误
    if any(keyword in error_str for keyword in ['validation', 'invalid', 'required']):
        return "输入数据格式不正确"
    
    # 资源不存在错误
    if 'not found' in error_str or 'does not exist' in error_str:
        return "请求的资源不存在"
    
    # 其他所有错误都返回通用消息
    return default_message


def create_error_response(success: bool = False, error: str = None, **kwargs):
    """
    创建统一的错误响应
    
    Args:
        success: 固定为 False
        error: 错误消息
        **kwargs: 其他参数
        
    Returns:
        dict: 错误响应字典
    """
    from src.api.v1.core.responses import ApiResponse
    
    return ApiResponse(
        success=success,
        error=error,
        **kwargs
    )
