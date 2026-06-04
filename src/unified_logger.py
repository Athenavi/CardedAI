"""
统一日志配置模块

使用 secure-python-utils 的 LoggerConfig 提供全局日志管理
支持根据不同模块的重要程度创建单独的日志实例
"""
import logging
import os


def _load_logger_config():
    """加载 LoggerConfig，安全处理 secure_python_utils 包的 __init__.py 导入错误"""
    try:
        # 使用 importlib 绕过 secure_python_utils 的 __init__.py 中
        # 导致 ImportError 的 PasswordService 导入
        import importlib
        _mod = importlib.import_module('secure_python_utils.logger.simple')
        return _mod.LoggerConfig
    except (ImportError, AttributeError, Exception) as e:
        # 如果 secure_python_utils 不可用，提供基于标准 logging 的降级方案
        logging.warning(f"secure_python_utils 加载失败 ({e})，使用内置日志系统")

        class _FallbackLogger:
            """标准 logging 的简单封装，兼容 LoggerConfig 接口"""

            @staticmethod
            def get_logger(log_file: str = None, level=logging.INFO):
                logger = logging.getLogger(f"fastblog.{log_file or 'app'}")
                logger.setLevel(level)
                if not logger.handlers:
                    # 控制台 handler
                    console = logging.StreamHandler()
                    console.setLevel(level)
                    fmt = logging.Formatter(
                        '%(asctime)s [%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    )
                    console.setFormatter(fmt)
                    logger.addHandler(console)
                    # 文件 handler（如果指定了日志文件且目录存在）
                    if log_file:
                        log_dir = os.path.dirname(log_file)
                        if log_dir:
                            os.makedirs(log_dir, exist_ok=True)
                        fh = logging.FileHandler(log_file, encoding='utf-8')
                        fh.setLevel(level)
                        fh.setFormatter(fmt)
                        logger.addHandler(fh)
                return logger

        return _FallbackLogger


LoggerConfig = _load_logger_config()

# 获取 logger 函数
get_logger = LoggerConfig.get_logger

# 全局默认日志实例（用于大多数模块）
default_logger = get_logger("logs/app.log")


def get_module_logger(module_name: str, log_file: str = None):
    """
    为特定模块获取日志实例

    Args:
        module_name: 模块名称（如 'auth', 'articles', 'security' 等）
        log_file: 可选的单独日志文件路径，如果为 None 则使用默认日志文件

    Returns:
        logger 实例
    """
    if log_file:
        # 为重要模块创建单独的日志文件
        return get_logger(log_file)
    else:
        # 使用默认日志文件，但带有模块标识
        return default_logger


# 为关键模块预定义日志实例
auth_logger = get_module_logger("auth", "logs/auth.log")
security_logger = get_module_logger("security", "logs/security.log")
database_logger = get_module_logger("database", "logs/database.log")
api_logger = get_module_logger("api", "logs/api.log")
performance_logger = get_module_logger("performance", "logs/performance.log")

# 导出所有日志实例
__all__ = [
    'default_logger',
    'get_module_logger',
    'auth_logger',
    'security_logger',
    'database_logger',
    'api_logger',
    'performance_logger',
]
