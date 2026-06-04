"""
媒体库增强服务
提供现代化的媒体管理功能
"""


from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from src.unified_logger import default_logger as logger


class MediaLibraryService:
    """
    媒体库增强服务
    
    功能:
    1. 优化的分页查询
    2. 全文搜索支持
    3. 元数据索引和过滤
    4. 批量操作支持
    """
    
    async def get_media_list(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        media_type: Optional[str] = None,
        search_query: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """获取媒体列表（带高级过滤和搜索）"""
        from shared.models.media import Media
        
        try:
            query = select(Media)
            if media_type:
                query = query.where(Media.media_type == media_type)
            if search_query:
                search_filter = (
                        Media.filename.ilike(f"%{search_query}%") | Media.title.ilike(f"%{search_query}%") |
                        Media.description.ilike(f"%{search_query}%") | Media.alt_text.ilike(f"%{search_query}%")
                )
                query = query.where(search_filter)
            if date_from:
                query = query.where(Media.created_at >= datetime.fromisoformat(date_from))
            if date_to:
                query = query.where(Media.created_at <= datetime.fromisoformat(date_to))
            if min_size is not None:
                query = query.where(Media.file_size >= min_size)
            if max_size is not None:
                query = query.where(Media.file_size <= max_size)
            
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar()
            
            sort_column = getattr(Media, sort_by, Media.created_at)
            query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)
            
            result = await db.execute(query)
            media_items = result.scalars().all()
            media_list = [self._media_to_dict(media) for media in media_items]
            
            return {
                "success": True, "data": media_list,
                "pagination": {
                    "page": page, "per_page": per_page, "total": total,
                    "total_pages": (total + per_page - 1) // per_page,
                    "has_next": page * per_page < total, "has_prev": page > 1
                }
            }
        except Exception as e:
            return {"success": False, "error": f"查询失败: {str(e)}"}
    
    async def get_media_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """获取媒体库统计信息"""
        from shared.models.media import Media
        
        try:
            count_query = select(func.count(Media.id))
            count_result = await db.execute(count_query)
            total_count = count_result.scalar()
            
            type_query = select(Media.media_type, func.count(Media.id)).group_by(Media.media_type)
            type_result = await db.execute(type_query)
            type_stats = dict(type_result.all())
            
            size_query = select(func.sum(Media.file_size))
            size_result = await db.execute(size_query)
            total_size = size_result.scalar() or 0
            
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            month_query = select(func.count(Media.id)).where(Media.created_at >= month_start)
            month_result = await db.execute(month_query)
            month_count = month_result.scalar()
            
            return {
                "success": True,
                "statistics": {
                    "total_count": total_count, "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "by_type": type_stats, "uploaded_this_month": month_count
                }
            }
        except Exception as e:
            return {"success": False, "error": f"统计失败: {str(e)}"}
    
    async def batch_delete_media(
        self,
        db: AsyncSession,
        media_ids: List[int]
    ) -> Dict[str, Any]:
        """批量删除媒体文件"""
        from shared.models.media import Media
        
        try:
            deleted_count = 0
            errors = []
            
            for media_id in media_ids:
                try:
                    query = select(Media).where(Media.id == media_id)
                    result = await db.execute(query)
                    media = result.scalar_one_or_none()
                    
                    if media:
                        for file_path_attr in ['file_path', 'thumbnail_path']:
                            file_path = getattr(media, file_path_attr)
                            if file_path:
                                try:
                                    path = Path(file_path)
                                    if path.exists():
                                        path.unlink()
                                        logger.info(f"已删除文件: {file_path}")
                                except Exception as e:
                                    logger.warning(f"删除文件失败 {file_path}: {e}")
                        
                        await db.delete(media)
                        deleted_count += 1
                        logger.info(f"已删除媒体记录 ID={media_id}")
                    else:
                        errors.append(f"媒体不存在: {media_id}")
                except Exception as e:
                    error_msg = f"删除 {media_id} 失败: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)

            await db.commit()
            logger.info(f"批量删除完成: 成功{deleted_count}个, 失败{len(errors)}个")
            
            return {
                "success": True, "deleted_count": deleted_count,
                "failed_count": len(errors), "errors": errors
            }
        except Exception as e:
            await db.rollback()
            error_msg = f"批量删除失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def batch_update_metadata(
        self,
        db: AsyncSession,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量更新媒体元数据"""
        from shared.models.media import Media
        
        try:
            updated_count = 0
            errors = []
            
            for update_data in updates:
                media_id = update_data.pop('id', None)
                if not media_id:
                    errors.append("缺少媒体ID")
                    continue
                
                try:
                    query = select(Media).where(Media.id == media_id)
                    result = await db.execute(query)
                    media = result.scalar_one_or_none()
                    
                    if media:
                        for key, value in update_data.items():
                            if hasattr(media, key):
                                setattr(media, key, value)
                        updated_count += 1
                    else:
                        errors.append(f"媒体不存在: {media_id}")
                except Exception as e:
                    errors.append(f"更新 {media_id} 失败: {str(e)}")
            
            await db.commit()
            return {
                "success": len(errors) == 0, "updated_count": updated_count,
                "failed_count": len(errors), "errors": errors
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": f"批量更新失败: {str(e)}"}
    
    def _media_to_dict(self, media: Any) -> Dict[str, Any]:
        """将媒体对象转换为字典"""
        return {
            "id": media.id, "filename": media.filename, "title": media.title,
            "alt_text": media.alt_text, "description": media.description,
            "file_path": media.file_path, "url": media.url, "thumbnail_url": media.thumbnail_url,
            "media_type": media.media_type, "mime_type": media.mime_type,
            "file_size": media.file_size, "width": media.width, "height": media.height,
            "created_at": media.created_at.isoformat() if hasattr(media.created_at, 'isoformat') else str(media.created_at),
            "updated_at": media.updated_at.isoformat() if hasattr(media.updated_at, 'isoformat') else str(media.updated_at)
        }

# 全局实例
media_library_service = MediaLibraryService()
