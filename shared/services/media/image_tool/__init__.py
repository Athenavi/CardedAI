"""
图片处理工具包

提供 EXIF 数据提取、图片编辑、图片处理、分类标签管理和版本管理等功能
"""

from .exif_service import ExifService
from .image_editor import ImageEditor, image_editor
from .image_processor import ImageProcessor, image_processor
from .image_version_manager import ImageVersionManager, image_version_manager

__all__ = [
    # 服务类
    'ExifService',
    'ImageEditor',
    'ImageProcessor',
    'ImageVersionManager',

    # 全局实例
    'image_editor',
    'image_processor',
    'image_version_manager',
]
