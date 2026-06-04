import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from shared.models.article import Article
from shared.models.user import User


def auth_by_uid(article_id: int, user_id: int, db: Session) -> bool:
    try:
        article_query = select(Article).where(
            Article.id == article_id,
            Article.user == user_id,
            Article.status != -1  # 排除已删除的文章
        )
        article_result = db.execute(article_query)
        article = article_result.scalar_one_or_none()
        return article is not None
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return False


def check_user_conflict(zone: str, value: str, db: Session) -> bool:
    try:
        if zone == 'username':
            user_query = select(User).where(User.username == value)
            user_result = db.execute(user_query)
            user = user_result.scalar_one_or_none()
        elif zone == 'email':
            user_query = select(User).where(User.email == value)
            user_result = db.execute(user_query)
            user = user_result.scalar_one_or_none()
        else:
            return False
        return user is not None
    except SQLAlchemyError as e:
        print(f"Error getting user list: {e}")
        return False


async def check_user_conflict_async(zone: str, value: str, db: AsyncSession) -> bool:
    """异步版本的用户冲突检查"""
    try:
        if zone == 'username':
            user_query = select(User).where(User.username == value)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
        elif zone == 'email':
            user_query = select(User).where(User.email == value)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
        else:
            return False
        return user is not None
    except SQLAlchemyError as e:
        print(f"Error checking user conflict: {e}")
        return False


async def save_uploaded_avatar(file: UploadFile, user_id: int, db):
    try:
        # 生成唯一的文件名
        avatar_uuid = str(uuid.uuid4())

        # 确定保存路径
        avatar_dir = Path('static/avatar')

        # 自动创建目录（如果不存在）
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # 确定文件扩展名
        # 始终使用 .webp 扩展名保存
        avatar_filename = f"{avatar_uuid}.webp"
        avatar_path = avatar_dir / avatar_filename

        # 读取并保存文件
        file_content = file.file.read()

        with open(avatar_path, 'wb') as f:
            f.write(file_content)

        # 更新数据库中的用户头像字段
        if isinstance(db, AsyncSession):
            # 异步会话处理
            result = await db.execute(select(User).filter_by(id=user_id))
            user = result.scalar_one_or_none()
            if user:
                # 存储不含扩展名的文件名，便于后续动态确定扩展名
                user.profile_picture = avatar_uuid
                await db.commit()
        else:
            # 同步会话处理
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                # 存储不含扩展名的文件名，便于后续动态确定扩展名
                user.profile_picture = avatar_uuid
                db.commit()

        return avatar_uuid  # 返回不含扩展名的UUID，扩展名将通过get_avatar函数动态确定
    except SQLAlchemyError as e:
        print(f"Database error saving avatar: {e} by user {user_id}")
        if isinstance(db, AsyncSession):
            await db.rollback()
        else:
            db.rollback()
        raise
    except Exception as e:
        print(f"Error saving avatar file: {e} by user {user_id}")
        raise


async def db_save_bio(user_id: int, bio: str, db):
    try:
        if isinstance(db, AsyncSession):
            # 异步会话处理
            result = await db.execute(select(User).filter_by(id=user_id))
            user = result.scalar_one_or_none()
            if user:
                user.bio = bio
                await db.commit()
        else:
            # 同步会话处理
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                user.bio = bio
                db.commit()
    except SQLAlchemyError as e:
        print(f"Error saving bio: {e} by user {user_id} bio: {bio}")
        if isinstance(db, AsyncSession):
            await db.rollback()
        else:
            db.rollback()


async def change_username(user_id: int, new_username: str, db):
    # 修改用户名将可能导致资料被意外删除,建议先导出您的资料再进行下一步操作
    # 导出资料: 点击右上角头像 -> 点击设置 -> 点击导出资料
    try:
        if isinstance(db, AsyncSession):
            # 异步会话处理
            result = await db.execute(select(User).filter_by(id=user_id))
            user = result.scalar_one_or_none()
            if user:
                user.username = new_username
                await db.commit()
        else:
            # 同步会话处理
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                user.username = new_username
                db.commit()
    except SQLAlchemyError as e:
        print(f"Error changing username: {e} by user {user_id} new username: {new_username}")
        if isinstance(db, AsyncSession):
            await db.rollback()
        else:
            db.rollback()


async def bind_email(user_id: int, param: str, db) -> bool:
    conflict = await check_user_conflict_async('email', param, db)
    if conflict:
        return False
    try:
        if isinstance(db, AsyncSession):
            # 异步会话处理
            result = await db.execute(select(User).filter_by(id=user_id))
            user = result.scalar_one_or_none()
            if user:
                user.email = param
                await db.commit()
                return True
        else:
            # 同步会话处理
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                user.email = param
                db.commit()
                return True
    except SQLAlchemyError as e:
        print(f"Error binding email: {e} by user {user_id} email: {param}")
        if isinstance(db, AsyncSession):
            await db.rollback()
        else:
            db.rollback()
        return False


async def get_avatar(domain: str, user_identifier, identifier_type: str = 'id', db=None):
    avatar_url = None
    if not user_identifier or not db:
        return avatar_url

    try:
        if isinstance(db, AsyncSession):
            # 异步会话处理
            if identifier_type == 'id':
                result = await db.execute(select(User).filter_by(id=user_identifier))
                user = result.scalar_one_or_none()
            elif identifier_type == 'username':
                result = await db.execute(select(User).filter_by(username=user_identifier))
                user = result.scalar_one_or_none()
            else:
                raise ValueError("identifier_type must be 'id' or 'username'")
        else:
            # 同步会话处理
            if identifier_type == 'id':
                user_query = select(User).where(User.id == user_identifier)
                user_result = db.execute(user_query)
                user = user_result.scalar_one_or_none()
            elif identifier_type == 'username':
                user_query = select(User).where(User.username == user_identifier)
                user_result = db.execute(user_query)
                user = user_result.scalar_one_or_none()
            else:
                raise ValueError("identifier_type must be 'id' or 'username'")

        if user and user.profile_picture:
            # 查找实际存在的文件（可能是任何支持的图像格式）
            avatar_dir = Path('static/avatar')
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                avatar_file = avatar_dir / f"{user.profile_picture}{ext}"
                if avatar_file.exists():
                    avatar_url = f"{domain}static/avatar/{user.profile_picture}{ext}"
                    break
            # 如果没有找到对应的文件，使用.webp作为默认扩展名
            if not avatar_url:
                avatar_url = f"{domain}static/avatar/{user.profile_picture}.webp"
    except SQLAlchemyError as e:
        print(f"Error fetching avatar: {e}")

    return avatar_url
