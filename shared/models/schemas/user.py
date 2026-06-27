"""User schemas for FastAPI-Users"""
from datetime import datetime
from typing import Optional

from fastapi_users import schemas


# FastAPI-Users 兼容的用户模型
class UserRead(schemas.BaseUser[int]):
    username: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    register_ip: Optional[str] = None
    is_2fa_enabled: Optional[bool] = False
    locale: Optional[str] = "zh_CN"


class UserCreate(schemas.BaseUserCreate):
    username: str
    bio: Optional[str] = None
    locale: Optional[str] = "zh_CN"


class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None
    bio: Optional[str] = None
    locale: Optional[str] = None
