# 导入时不直接使用可能引发错误的模块
import bcrypt
from sqlalchemy.orm import Session

from shared.models.notification import Notification
from shared.models.user import User


def _get_crypt_context():
    """获取密码加密上下文，使用纯 bcrypt 实现以避免 passlib 兼容性问题"""

    # 直接使用 bcrypt 实现，避免 passlib 的兼容性问题
    class BcryptContext:
        def hash(self, secret):
            # 确保密码不超过 72 字节限制
            if len(secret.encode('utf-8')) > 72:
                secret = secret.encode('utf-8')[:72].decode('utf-8', errors='ignore')
            return bcrypt.hashpw(secret.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        def verify(self, secret, hash):
            try:
                return bcrypt.checkpw(secret.encode('utf-8'), hash.encode('utf-8'))
            except Exception:
                # 处理各种可能的错误情况
                try:
                    return bcrypt.checkpw(secret.encode('utf-8'), hash)
                except Exception:
                    return False

    return BcryptContext()


# 延迟初始化密码上下文
# 导入统一的密码验证函数
from src.utils.security.password_validator import verify_password as _verify_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
    
    Returns:
        bool: 验证成功返回True，否则返回False
    """
    return _verify_password(plain_password, hashed_password)


async def update_password(user_id: int, new_password: str, confirm_password: str, ip: str, db):
    """
    更新用户密码
    
    Args:
        user_id: 用户ID
        new_password: 新密码
        confirm_password: 确认密码
        ip: IP地址
        db: 数据库会话
    
    Returns:
        bool: 更新成功返回True，否则返回False
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select

    if isinstance(db, AsyncSession):
        # 异步会话处理
        result = await db.execute(select(User).filter_by(id=user_id))
        user = result.scalar_one_or_none()
    else:
        # 同步会话处理
        from sqlalchemy import select
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

    if user:
        # 验证新密码和确认密码是否一致，并且长度是否符合要求
        if new_password == confirm_password and len(new_password) >= 6:
            try:
                # 使用统一的密码哈希函数
                from src.utils.security.password_validator import hash_password
                from datetime import datetime

                user.password = hash_password(new_password)
                
                # 创建通知（使用不带时区的时间，匹配数据库 TIMESTAMP WITHOUT TIME ZONE）
                now = datetime.now()
                notice = Notification(
                    recipient=user_id,
                    type='safe',
                    title='密码已更改',
                    message=f"{ip} changed password",
                    created_at=now,
                    updated_at=now
                )
                if isinstance(db, AsyncSession):
                    db.add(notice)
                    await db.commit()
                else:
                    db.add(notice)
                    db.commit()
                return True
            except Exception as e:
                print(e)
                if isinstance(db, AsyncSession):
                    await db.rollback()
                else:
                    db.rollback()
                return False
        else:
            return False

    return False


# 导入统一的密码哈希函数
from src.utils.security.password_validator import hash_password as _hash_password


def hash_password(password: str) -> str:
    """
    对密码进行哈希处理
    
    Args:
        password: 明文密码
    
    Returns:
        str: 哈希后的密码
    """
    return _hash_password(password)


async def validate_password_async(user_id: int, password: str, db) -> bool:
    """
    异步验证用户密码
    
    Args:
        user_id: 用户ID
        password: 要验证的密码
        db: 数据库会话
    
    Returns:
        bool: 验证成功返回True，否则返回False
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from shared.models.user import User

    if isinstance(db, AsyncSession):
        # 异步会话处理
        result = await db.execute(select(User).filter_by(id=user_id))
        user = result.scalar_one_or_none()
    else:
        # 同步会话处理
        from sqlalchemy import select
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

    if user and user.password:
        # 使用统一的密码验证函数
        from src.utils.security.password_validator import verify_password
        return verify_password(password, user.password)
    return False


def validate_password(user_id: int, password: str, db: Session) -> bool:
    """
    验证用户密码（同步版本）
    
    Args:
        user_id: 用户ID
        password: 要验证的密码
        db: 数据库会话
    
    Returns:
        bool: 验证成功返回True，否则返回False
    """
    from shared.models.user import User

    user = db.query(User).filter_by(id=user_id).first()
    if user and user.password:
        # 使用统一的密码验证函数
        from src.utils.security.password_validator import verify_password
        return verify_password(password, user.password)
    return False
