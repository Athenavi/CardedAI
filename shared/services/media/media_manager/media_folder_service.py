"""
媒体文件夹服务
提供文件夹的 CRUD 操作和树形结构管理
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.media import Media
from shared.models.media_folder import MediaFolder

from src.unified_logger import default_logger as logger

# 文件夹名称验证配置
MAX_FOLDER_NAME_LENGTH = 255
DANGEROUS_CHARS = ['<', '>', ':', '"', '|', '?', '*', '\x00']
FOLDER_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\u4e00-\u9fa5_\-\.\s]+$')


def validate_folder_name(name: str) -> tuple[bool, str]:
    """验证文件夹名称是否合法"""
    if not name or not name.strip():
        return False, "文件夹名称不能为空"
    
    name = name.strip()
    if len(name) > MAX_FOLDER_NAME_LENGTH:
        return False, f"文件夹名称不能超过{MAX_FOLDER_NAME_LENGTH}个字符"
    
    if '..' in name:
        return False, "文件夹名称不能包含 '..'"
    
    if '/' in name or '\\' in name:
        return False, "文件夹名称不能包含路径分隔符 (/ 或 \\)"

    for char in DANGEROUS_CHARS:
        if char in name:
            return False, f"文件夹名称不能包含特殊字符: {char}"

    if not FOLDER_NAME_PATTERN.match(name):
        return False, "文件夹名称只能包含字母、数字、中文、下划线、连字符、空格和点"
    
    if name.startswith('.'):
        return False, "文件夹名称不能以点开头"
    
    return True, ""


class MediaFolderService:
    """媒体文件夹服务类"""

    async def create_folder(
        self,
        db: AsyncSession,
        user_id: int,
        name: str,
        parent_id: Optional[int] = None,
        description: str = "",
        is_public: bool = True
    ) -> Dict[str, Any]:
        """创建文件夹"""
        try:
            is_valid, error_msg = validate_folder_name(name)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            name = name.strip()
            if parent_id:
                parent_query = select(MediaFolder).where(MediaFolder.id == parent_id, MediaFolder.user == user_id)
                parent_result = await db.execute(parent_query)
                if not parent_result.scalar_one_or_none():
                    return {"success": False, "error": "父文件夹不存在或无权访问"}
            
            existing_query = select(MediaFolder).where(
                MediaFolder.name == name, MediaFolder.user == user_id, MediaFolder.parent_id == parent_id
            )
            existing_result = await db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                return {"success": False, "error": "该位置已存在同名文件夹"}
            
            folder = MediaFolder(
                name=name, parent_id=parent_id, user=user_id, description=description,
                is_public=is_public, sort_order=0, media_count=0,
                created_at=datetime.now(), updated_at=datetime.now()
            )
            db.add(folder)
            await db.commit()
            await db.refresh(folder)
            return {"success": True, "folder": folder.to_dict()}
        except Exception as e:
            await db.rollback()
            logger.error(f"创建文件夹失败: {e}")
            return {"success": False, "error": f"创建文件夹失败: {str(e)}"}

    async def get_folder_tree(
        self,
        db: AsyncSession,
        user_id: int,
        include_media_count: bool = True
    ) -> List[Dict[str, Any]]:
        """获取文件夹树形结构"""
        try:
            query = select(MediaFolder).where(MediaFolder.user == user_id).order_by(MediaFolder.sort_order,
                                                                                    MediaFolder.name)
            result = await db.execute(query)
            folders = result.scalars().all()
            
            if include_media_count:
                for folder in folders:
                    count_query = select(func.count(Media.id)).where(Media.folder_id == folder.id)
                    count_result = await db.execute(count_query)
                    folder.media_count = count_result.scalar() or 0
            
            folder_dict = {}
            for folder in folders:
                folder_data = folder.to_dict()
                folder_data['children'] = []
                folder_dict[folder.id] = folder_data
            
            tree = []
            for folder in folders:
                folder_data = folder_dict[folder.id]
                if folder.parent_id and folder.parent_id in folder_dict:
                    folder_dict[folder.parent_id]['children'].append(folder_data)
                else:
                    tree.append(folder_data)
            
            return tree
        except Exception as e:
            logger.error(f"获取文件夹树失败: {e}", exc_info=True)
            return []

    async def get_folder_list(
        self,
        db: AsyncSession,
        user_id: int,
        parent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取文件夹列表（扁平结构）"""
        try:
            query = select(MediaFolder).where(
                MediaFolder.user == user_id, MediaFolder.parent_id == parent_id
            ).order_by(MediaFolder.sort_order, MediaFolder.name)
            result = await db.execute(query)
            return [folder.to_dict() for folder in result.scalars().all()]
        except Exception as e:
            logger.error(f"获取文件夹列表失败: {e}")
            return []

    async def get_folder_detail(
        self,
        db: AsyncSession,
        folder_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取文件夹详情"""
        try:
            query = select(MediaFolder).where(MediaFolder.id == folder_id, MediaFolder.user == user_id)
            result = await db.execute(query)
            folder = result.scalar_one_or_none()
            if not folder:
                return None

            count_query = select(func.count(Media.id)).where(Media.folder_id == folder_id)
            count_result = await db.execute(count_query)
            folder_data = folder.to_dict()
            folder_data['media_count'] = count_result.scalar() or 0
            return folder_data
        except Exception as e:
            logger.error(f"获取文件夹详情失败: {e}")
            return None

    async def update_folder(
        self,
        db: AsyncSession,
        folder_id: int,
        user_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """更新文件夹"""
        try:
            query = select(MediaFolder).where(MediaFolder.id == folder_id, MediaFolder.user == user_id)
            result = await db.execute(query)
            folder = result.scalar_one_or_none()
            if not folder:
                return {"success": False, "error": "文件夹不存在或无权访问"}
            
            if 'name' in kwargs:
                is_valid, error_msg = validate_folder_name(kwargs['name'])
                if not is_valid:
                    return {"success": False, "error": error_msg}
                kwargs['name'] = kwargs['name'].strip()
                existing_query = select(MediaFolder).where(
                    MediaFolder.name == kwargs['name'], MediaFolder.user == user_id,
                    MediaFolder.parent_id == folder.parent_id, MediaFolder.id != folder_id
                )
                existing_result = await db.execute(existing_query)
                if existing_result.scalar_one_or_none():
                    return {"success": False, "error": "该位置已存在同名文件夹"}
            
            allowed_fields = ['name', 'description', 'is_public', 'sort_order']
            for field in allowed_fields:
                if field in kwargs:
                    setattr(folder, field, kwargs[field])

            folder.updated_at = datetime.now()
            await db.commit()
            await db.refresh(folder)
            return {"success": True, "folder": folder.to_dict()}
        except Exception as e:
            await db.rollback()
            logger.error(f"更新文件夹失败: {e}")
            return {"success": False, "error": f"更新文件夹失败: {str(e)}"}

    async def delete_folder(
        self,
        db: AsyncSession,
        folder_id: int,
        user_id: int,
        delete_media: bool = False
    ) -> Dict[str, Any]:
        """删除文件夹"""
        try:
            query = select(MediaFolder).where(MediaFolder.id == folder_id, MediaFolder.user == user_id)
            result = await db.execute(query)
            folder = result.scalar_one_or_none()
            if not folder:
                return {"success": False, "error": "文件夹不存在或无权访问"}

            children_query = select(func.count(MediaFolder.id)).where(MediaFolder.parent_id == folder_id)
            children_result = await db.execute(children_query)
            if children_result.scalar() or 0 > 0:
                return {"success": False, "error": "文件夹包含子文件夹，请先删除子文件夹"}
            
            media_query = select(Media).where(Media.folder_id == folder_id)
            media_result = await db.execute(media_query)
            media_files = media_result.scalars().all()
            
            if media_files:
                if delete_media:
                    for media in media_files:
                        await db.delete(media)
                else:
                    stmt = update(Media).where(Media.folder_id == folder_id).values(folder_id=None)
                    await db.execute(stmt)
            
            await db.delete(folder)
            await db.commit()
            return {"success": True, "message": "文件夹删除成功"}
        except Exception as e:
            await db.rollback()
            logger.error(f"删除文件夹失败: {e}")
            return {"success": False, "error": f"删除文件夹失败: {str(e)}"}

    async def move_media_to_folder(
        self,
        db: AsyncSession,
        media_ids: List[int],
        folder_id: Optional[int],
        user_id: int
    ) -> Dict[str, Any]:
        """移动媒体文件到文件夹"""
        try:
            if folder_id:
                folder_query = select(MediaFolder).where(MediaFolder.id == folder_id, MediaFolder.user == user_id)
                folder_result = await db.execute(folder_query)
                if not folder_result.scalar_one_or_none():
                    return {"success": False, "error": "目标文件夹不存在或无权访问"}

            stmt = update(Media).where(Media.id.in_(media_ids), Media.user == user_id).values(folder_id=folder_id)
            result = await db.execute(stmt)
            await db.commit()
            moved_count = result.rowcount
            return {"success": True, "moved_count": moved_count, "message": f"成功移动 {moved_count} 个文件"}
        except Exception as e:
            await db.rollback()
            logger.error(f"移动媒体文件失败: {e}")
            return {"success": False, "error": f"移动媒体文件失败: {str(e)}"}

    async def copy_media_to_folder(
        self,
        db: AsyncSession,
        media_ids: List[int],
        folder_id: Optional[int],
        user_id: int
    ) -> Dict[str, Any]:
        """
        复制媒体文件到文件夹
        注意：这里只是逻辑复制（改变folder_id），如需物理复制需要额外实现
        """
        return await self.move_media_to_folder(db, media_ids, folder_id, user_id)


# 全局实例
media_folder_service = MediaFolderService()
