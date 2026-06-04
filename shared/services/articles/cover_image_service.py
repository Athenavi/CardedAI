"""
封面图片处理服务
负责将媒体库中的图片优化并保存到公开访问的缓存目录
"""
from pathlib import Path
from typing import Optional

from shared.services.media.image_tool.image_processor import ImageProcessor
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class CoverImageService:
    """封面图片处理服务"""

    def __init__(self):
        # 使用绝对路径，避免相对路径问题
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cover_dir = Path(base_dir) / "storage" / "cache" / "cover"
        self.image_processor = ImageProcessor()

        # 确保目录存在
        try:
            self.cover_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"封面缓存目录已就绪: {self.cover_dir}")
        except Exception as e:
            logger.error(f"创建封面缓存目录失败: {e}")
            raise

    def generate_cover_filename(self, media_id: int | str, file_hash: str, extension: str = '.jpg') -> str:
        """
        生成封面文件名
        
        Args:
            media_id: 媒体ID（可以是整数或字符串）
            file_hash: 文件哈希值
            extension: 文件扩展名（默认 .jpg）
        
        Returns:
            格式化的文件名，如: 123_abc123def456.jpg 或 ext_urlhash_abc123def456.jpg
        """
        # 使用 media_id 和 hash 的组合确保唯一性
        return f"{media_id}_{file_hash[:16]}{extension}"

    def optimize_and_save_cover(
            self,
            media_id: int | str,
            image_data: bytes,
            file_hash: str,
            mime_type: str = 'image/jpeg',
            max_width: int = 1920,
            max_height: int = 1080,
            quality: int = 85,
            filename: Optional[str] = None
    ) -> Optional[str]:
        """
        优化图片并保存为封面
        
        Args:
            media_id: 媒体ID（可以是整数或字符串）
            image_data: 原始图片数据
            file_hash: 文件哈希值
            mime_type: MIME类型
            max_width: 最大宽度
            max_height: 最大高度
            quality: JPEG质量 (1-100)
            filename: 可选的自定义文件名，如果提供则直接使用
        
        Returns:
            封面文件的URL路径，失败返回None
        """
        try:
            # 确保目录存在（每次保存前都检查）
            self.cover_dir.mkdir(parents=True, exist_ok=True)

            # 确定文件扩展名
            ext_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/webp': '.webp',
                'image/gif': '.gif',
            }
            extension = ext_map.get(mime_type, '.jpg')

            # 生成或使用提供的文件名
            if filename:
                cover_filename = filename
            else:
                cover_filename = self.generate_cover_filename(media_id, file_hash, extension)

            cover_path = self.cover_dir / cover_filename

            # 如果文件已存在，直接返回URL
            if cover_path.exists():
                logger.info(f"封面已存在: {cover_filename}")
                return f"/api/v1/media/cover/{cover_filename}"

            # 优化图片
            optimized_data, optimized_mime = self._optimize_image(
                image_data,
                max_width=max_width,
                max_height=max_height,
                quality=quality,
                output_format=mime_type.split('/')[1].upper()
            )

            # 再次确保目录存在（防止并发问题）
            self.cover_dir.mkdir(parents=True, exist_ok=True)

            # 保存文件
            with open(cover_path, 'wb') as f:
                f.write(optimized_data)

            logger.info(f"封面图片已保存: {cover_filename}, 大小: {len(optimized_data)} bytes")

            # 返回公开访问的URL
            return f"/api/v1/media/cover/{cover_filename}"

        except Exception as e:
            logger.error(f"优化和保存封面失败: {e}", exc_info=True)
            return None

    def _optimize_image(
            self,
            image_data: bytes,
            max_width: int = 1920,
            max_height: int = 1080,
            quality: int = 85,
            output_format: str = 'JPEG'
    ) -> tuple[bytes, str]:
        """
        优化图片（调整大小、压缩等）
        
        Args:
            image_data: 原始图片数据
            max_width: 最大宽度
            max_height: 最大高度
            quality: 质量参数
            output_format: 输出格式
        
        Returns:
            (优化后的图片数据, MIME类型)
        """
        operations = {
            'resize': {'max_width': max_width, 'max_height': max_height},
            'quality': quality,
            'format': output_format,
        }

        return self.image_processor.process_image(image_data, operations)

    def delete_cover(self, media_id: int, file_hash: str) -> bool:
        """
        删除封面图片
        
        Args:
            media_id: 媒体ID
            file_hash: 文件哈希值
        
        Returns:
            是否成功删除
        """
        try:
            # 尝试各种可能的扩展名
            for ext in ['.jpg', '.png', '.webp', '.gif']:
                filename = self.generate_cover_filename(media_id, file_hash, ext)
                cover_path = self.cover_dir / filename

                if cover_path.exists():
                    cover_path.unlink()
                    logger.info(f"封面图片已删除: {filename}")
                    return True

            logger.warning(f"未找到封面图片: media_id={media_id}, hash={file_hash}")
            return False

        except Exception as e:
            logger.error(f"删除封面图片失败: {e}")
            return False

    def get_cover_url(self, media_id: int, file_hash: str, extension: str = '.jpg') -> str:
        """
        获取封面图片的URL
        
        Args:
            media_id: 媒体ID
            file_hash: 文件哈希值
            extension: 文件扩展名
        
        Returns:
            封面图片的URL
        """
        filename = self.generate_cover_filename(media_id, file_hash, extension)
        return f"/api/v1/media/cover/{filename}"


# 全局实例
cover_image_service = CoverImageService()
