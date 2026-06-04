"""
用户服务层 - 提供统一的 SQLAlchemy async 用户相关操作

该模块封装了所有用户相关的数据库操作，避免直接使用 Django ORM,
确保与 FastAPI 的异步架构保持一致。
"""

import re
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User as UserModel
from src.utils.security.password_validator import hash_password, verify_password

# 常量定义
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
ALLOWED_PROFILE_FIELDS = {'profile_picture', 'bio', 'locale', 'profile_private'}


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[UserModel]:
    """
    通过 ID 获取用户
    
    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        
    Returns:
        用户对象，如果不存在则返回 None
    """
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserModel]:
    """
    通过用户名获取用户
    
    Args:
        db: 异步数据库会话
        username: 用户名
        
    Returns:
        用户对象，如果不存在则返回 None
    """
    result = await db.execute(select(UserModel).where(UserModel.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    """
    通过邮箱获取用户
    
    Args:
        db: 异步数据库会话
        email: 邮箱地址
        
    Returns:
        用户对象，如果不存在则返回 None
    """
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username_or_email(db: AsyncSession, identifier: str) -> Optional[UserModel]:
    """
    通过用户名或邮箱获取用户（自动判断）
    
    Args:
        db: 异步数据库会话
        identifier: 用户名或邮箱
        
    Returns:
        用户对象，如果不存在则返回 None
    """
    if EMAIL_PATTERN.match(identifier):
        return await get_user_by_email(db, identifier)
    return await get_user_by_username(db, identifier)


async def update_user_last_login(db: AsyncSession, user_id: int):
    """
    更新用户最后登录时间
    
    Args:
        db: 异步数据库会话
        user_id: 用户 ID
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(last_login_at=now)
    )
    await db.commit()


async def create_user_account(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        is_active: bool = True,
        is_staff: bool = False,
        is_superuser: bool = False,
        **extra_data
) -> UserModel:
    """
    创建用户账户
    
    Args:
        db: 异步数据库会话
        username: 用户名
        email: 邮箱
        password: 明文密码（将自动哈希）
        is_active: 是否激活
        is_staff: 是否为工作人员
        is_superuser: 是否为超级管理员
        **extra_data: 其他额外字段
        
    Returns:
        创建的用户对象
        
    Raises:
        IntegrityError: 如果用户名或邮箱已存在
    """
    # 使用 Argon2 密码哈希
    hashed_password = hash_password(password)

    # 准备数据（PostgreSQL TIMESTAMP WITHOUT TIME ZONE 需要不带时区的 datetime）
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user_data = {
        'username': username,
        'email': email,
        'password': hashed_password,
        'is_active': is_active,
        'is_staff': is_staff,
        'is_superuser': is_superuser,
        'date_joined': now,
        **extra_data
    }

    # 使用 insert 语句
    stmt = insert(UserModel).values(user_data).returning(UserModel)
    result = await db.execute(stmt)
    await db.commit()

    return result.scalar_one()


async def update_user_profile(
        db: AsyncSession,
        user_id: int,
        **kwargs
) -> Optional[UserModel]:
    """
    更新用户资料
    
    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        **kwargs: 要更新的字段
        
    Returns:
        更新后的用户对象，如果用户不存在则返回 None
    """
    # 过滤掉不允许更新的字段
    update_data = {
        k: v for k, v in kwargs.items()
        if k in ALLOWED_PROFILE_FIELDS and v is not None
    }

    if not update_data:
        return await get_user_by_id(db, user_id)

    await db.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(**update_data)
    )
    await db.commit()

    return await get_user_by_id(db, user_id)


async def check_password_async(raw_password: str, hashed_password: str) -> bool:
    """
    验证密码（异步包装）
    
    Args:
        raw_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        验证结果
    """
    return bool(hashed_password) and verify_password(raw_password, hashed_password)


async def set_user_password(
        db: AsyncSession,
        user_id: int,
        new_password: str
) -> bool:
    """
    设置用户新密码
    
    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        new_password: 新密码
        
    Returns:
        是否成功
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    # 使用 Argon2 密码哈希
    hashed_password = hash_password(new_password)

    await db.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(password=hashed_password)
    )
    await db.commit()

    return True


async def deactivate_user(db: AsyncSession, user_id: int) -> bool:
    """
    停用用户账户
    
    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        
    Returns:
        是否成功
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    await db.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(is_active=False)
    )
    await db.commit()

    return True


async def activate_user(db: AsyncSession, user_id: int) -> bool:
    """
    激活用户账户
    
    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        
    Returns:
        是否成功
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    await db.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(is_active=True)
    )
    await db.commit()

    return True


async def count_users(
        db: AsyncSession,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None
) -> int:
    """
    统计用户数量
    
    Args:
        db: 异步数据库会话
        is_active: 筛选活跃状态（可选）
        is_superuser: 筛选超级管理员（可选）
        
    Returns:
        用户总数
    """
    query = select(func.count()).select_from(UserModel)

    if is_active is not None:
        query = query.where(UserModel.is_active == is_active)

    if is_superuser is not None:
        query = query.where(UserModel.is_superuser == is_superuser)

    result = await db.execute(query)
    return result.scalar() or 0


async def search_users(
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        per_page: int = 10,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None
) -> tuple[List[UserModel], int]:
    """
    搜索用户
    
    Args:
        db: 异步数据库会话
        keyword: 搜索关键词（用户名或邮箱）
        page: 页码
        per_page: 每页数量
        is_active: 筛选活跃状态（可选）
        is_superuser: 筛选超级管理员（可选）
        
    Returns:
        (用户列表，总数)
    """
    # 构建查询
    query = select(UserModel).where(
        (UserModel.username.contains(keyword)) |
        (UserModel.email.contains(keyword))
    )

    if is_active is not None:
        query = query.where(UserModel.is_active == is_active)

    if is_superuser is not None:
        query = query.where(UserModel.is_superuser == is_superuser)

    # 统计总数
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * per_page
    query = query.order_by(UserModel.date_joined.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    users = list(result.scalars().all())

    return users, total


# 导出所有公共函数
__all__ = [
    'get_user_by_id',
    'get_user_by_username',
    'get_user_by_email',
    'get_user_by_username_or_email',
    'update_user_last_login',
    'create_user_account',
    'update_user_profile',
    'check_password_async',
    'set_user_password',
    'deactivate_user',
    'activate_user',
    'count_users',
    'search_users',
]
