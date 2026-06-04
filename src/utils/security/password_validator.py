"""
密码验证模块
使用 argon2-cffi 进行密码哈希和验证
"""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# 创建全局密码哈希器实例
ph = PasswordHasher()


def hash_password(password: str) -> str:
    """
    对密码进行 Argon2 哈希处理
    
    Args:
        password: 明文密码
    
    Returns:
        str: Argon2 哈希后的密码字符串
    """
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配
    
    Args:
        plain_password: 明文密码
        hashed_password: Argon2 哈希后的密码
    
    Returns:
        bool: 验证成功返回 True，否则返回 False
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        # 捕获其他可能的异常（如哈希格式错误）
        return False
