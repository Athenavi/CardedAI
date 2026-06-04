"""
用户管理器（纯 SQLAlchemy 异步实现，不再依赖 FastAPI Users）
"""
from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User as UserModel
from src.utils.database.main import get_async_session
from src.utils.security.password_validator import verify_password


class UserDatabase:
    """用户数据库操作层（封装 SQLAlchemy 会话）"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: int) -> Optional[UserModel]:
        return await self.session.get(UserModel, user_id)

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        from sqlalchemy import select
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, user: UserModel) -> UserModel:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: UserModel) -> UserModel:
        await self.session.commit()
        await self.session.refresh(user)
        return user


class UserManager:
    """用户业务逻辑管理"""
    def __init__(self, user_db: UserDatabase):
        self.user_db = user_db

    async def get(self, user_id: int) -> Optional[UserModel]:
        return await self.user_db.get(user_id)

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        return await self.user_db.get_by_email(email)

    async def create(self, user_data: dict) -> UserModel:
        """
        从字典创建用户，自动处理密码哈希，
        跳过 created_at/updated_at 等自动字段。
        """
        password = user_data.pop("password", "")
        # 移除不应手动设置的数据库生成字段
        for field in ("created_at", "updated_at", "id"):
            user_data.pop(field, None)

        user = UserModel(**user_data)
        user.set_password(password)  # 模型方法，内部实现哈希
        return await self.user_db.create(user)

    async def update(self, user: UserModel, update_dict: dict) -> UserModel:
        for field, value in update_dict.items():
            setattr(user, field, value)
        return await self.user_db.update(user)

    async def authenticate(self, email: str, password: str) -> Optional[UserModel]:
        user = await self.get_by_email(email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


# ---------- 依赖注入 ----------
async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> UserDatabase:
    """提供 UserDatabase 实例"""
    return UserDatabase(session)


async def get_user_manager(
    user_db: UserDatabase = Depends(get_user_db),
) -> UserManager:
    """提供 UserManager 实例"""
    return UserManager(user_db)