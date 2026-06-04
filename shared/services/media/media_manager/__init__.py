"""
媒体管理服务包

提供完整的媒体文件管理功能，包括：
- 媒体上传和处理
- 文件夹管理
- 图片优化和转换
- PDF 和 SVG 特殊处理
- 批量操作支持
"""

from shared.services.media.media_manager.batch_upload_service import BatchUploadService, batch_upload_service
from shared.services.media.media_manager.media_enhancement import MediaEnhancementService, media_enhancement
from shared.services.media.media_manager.media_folder_service import MediaFolderService, media_folder_service
from shared.services.media.media_manager.media_library_enhanced import MediaLibraryService, media_library_service
from shared.services.media.media_manager.media_service import MediaService, media_service
from shared.services.media.media_manager.pdf_service import PDFService
from shared.services.media.media_manager.svg_service import SVGService

__all__ = [
    # 服务类
    'MediaService',
    'BatchUploadService',
    'MediaEnhancementService',
    'MediaFolderService',
    'MediaLibraryService',
    'PDFService',
    'SVGService',

    # 全局实例
    'media_service',
    'batch_upload_service',
    'media_enhancement',
    'media_folder_service',
    'media_library_service',
]

__version__ = '1.0.0'
