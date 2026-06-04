"""
媒体文件增强服务
提供批量上传、图片优化、WebP转换等功能
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from PIL import Image

# 默认配置常量
DEFAULT_IMAGE_CONFIG = {
    'max_width': 1920,
    'max_height': 1080,
    'quality': 85,
    'optimize': True,
    'progressive': True,
}

DEFAULT_WEBP_CONFIG = {
    'enabled': True,
    'quality': 80,
    'method': 6,
}

SUPPORTED_FORMATS = {'JPEG', 'JPG', 'PNG', 'GIF', 'BMP', 'TIFF', 'WEBP'}
WEBP_CONVERTIBLE_FORMATS = {'JPEG', 'JPG', 'PNG', 'BMP', 'TIFF'}


class MediaEnhancementService:
    """
    媒体文件增强服务
    
    功能:
    1. 批量上传处理
    2. 图片自动优化(压缩、调整大小)
    3. WebP格式转换
    4. EXIF数据处理
    5. 重复文件检测
    6. 缩略图生成
    """

    def __init__(self, image_config: Dict = None, webp_config: Dict = None):
        self.image_config = image_config or DEFAULT_IMAGE_CONFIG.copy()
        self.webp_config = webp_config or DEFAULT_WEBP_CONFIG.copy()

    async def optimize_image(
            self,
            input_path: str,
            output_path: Optional[str] = None,
            config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """优化图片(压缩、调整大小)"""
        try:
            cfg = {**self.image_config, **(config or {})}
            with Image.open(input_path) as img:
                original_size = os.path.getsize(input_path)
                original_dimensions = img.size

                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                max_width, max_height = cfg.get('max_width', 1920), cfg.get('max_height', 1080)
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                output_path = output_path or input_path
                save_kwargs = {'optimize': cfg.get('optimize', True), 'quality': cfg.get('quality', 85)}
                if img.format == 'JPEG' or output_path.endswith(('.jpg', '.jpeg')):
                    save_kwargs['progressive'] = cfg.get('progressive', True)

                img.save(output_path, **save_kwargs)
                optimized_size = os.path.getsize(output_path)
                compression_ratio = (1 - optimized_size / original_size) * 100 if original_size > 0 else 0

                return {
                    'success': True, 'original_size': original_size, 'optimized_size': optimized_size,
                    'compression_ratio': round(compression_ratio, 2), 'original_dimensions': original_dimensions,
                    'optimized_dimensions': img.size, 'format': img.format, 'path': output_path
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def convert_to_webp(
            self,
            input_path: str,
            output_path: Optional[str] = None,
            config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """将图片转换为WebP格式"""
        try:
            cfg = {**self.webp_config, **(config or {})}
            if not cfg.get('enabled', True):
                return {'success': False, 'error': 'WebP转换已禁用'}

            input_ext = Path(input_path).suffix.lower().lstrip('.')
            if input_ext.upper() not in WEBP_CONVERTIBLE_FORMATS:
                return {'success': False, 'error': f'不支持的格式: {input_ext}'}

            output_path = output_path or str(Path(input_path).with_suffix('.webp'))
            original_size = os.path.getsize(input_path)

            with Image.open(input_path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(output_path, format='WEBP', quality=cfg.get('quality', 80), method=cfg.get('method', 6))

            webp_size = os.path.getsize(output_path)
            compression_ratio = (1 - webp_size / original_size) * 100 if original_size > 0 else 0

            return {
                'success': True, 'original_size': original_size, 'webp_size': webp_size,
                'compression_ratio': round(compression_ratio, 2), 'original_format': input_ext.upper(),
                'webp_path': output_path
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def process_image_with_webp(
            self,
            input_path: str,
            keep_original: bool = True
    ) -> Dict[str, Any]:
        """处理图片:优化 + 生成WebP版本"""
        result = {'success': False, 'original': None, 'webp': None}
        try:
            optimized_result = await self.optimize_image(input_path)
            if not optimized_result['success']:
                return {'success': False, 'error': f'优化失败: {optimized_result.get("error")}'}

            result['original'] = optimized_result
            webp_path = str(Path(input_path).with_suffix('.webp'))
            webp_result = await self.convert_to_webp(input_path, webp_path)
            if webp_result['success']:
                result['webp'] = webp_result
                if not keep_original and webp_result.get('webp_size', 0) < optimized_result.get('optimized_size', 0):
                    os.remove(input_path)
                    result['deleted_original'] = True

            result['success'] = True
            return result
        except Exception as e:
            result['error'] = str(e)
            return result

    async def batch_process_images(
            self,
            image_paths: List[str],
            generate_webp: bool = True,
            keep_original: bool = True,
            progress_callback=None
    ) -> Dict[str, Any]:
        """批量处理图片"""
        results = {'total': len(image_paths), 'success': 0, 'failed': 0, 'details': []}
        for i, image_path in enumerate(image_paths):
            try:
                result = await self.process_image_with_webp(image_path,
                                                            keep_original) if generate_webp else await self.optimize_image(
                    image_path)
                if result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                results['details'].append({'path': image_path, 'result': result})
                if progress_callback:
                    progress_callback(i + 1, len(image_paths))
            except Exception as e:
                results['failed'] += 1
                results['details'].append({'path': image_path, 'error': str(e)})
        return results

    def detect_duplicate(self, file_hash: str, db_session) -> Optional[Dict[str, Any]]:
        """检测重复文件(基于哈希)"""
        try:
            from sqlalchemy import select
            from shared.models.file_hash import FileHash
            query = select(FileHash).where(FileHash.hash == file_hash)
            result = db_session.execute(query)
            existing_file = result.scalar_one_or_none()
            if existing_file:
                return {
                    'is_duplicate': True, 'file_id': existing_file.id,
                    'hash': existing_file.hash, 'size': existing_file.file_size,
                    'mime_type': existing_file.mime_type
                }
            return None
        except Exception as e:
            print(f"Duplicate detection error: {e}")
            return None

    def extract_exif_data(self, image_path: str) -> Dict[str, Any]:
        """提取EXIF数据"""
        try:
            from PIL.ExifTags import TAGS
            with Image.open(image_path) as img:
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    for tag_id, value in img._getexif().items():
                        tag = TAGS.get(tag_id, tag_id)
                        if not isinstance(value, bytes):
                            exif_data[tag] = value
                return {'success': True, 'exif': exif_data}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def remove_exif_data(self, input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """移除EXIF数据(保护隐私)"""
        try:
            output_path = output_path or input_path
            with Image.open(input_path) as img:
                data = list(img.getdata())
                img_without_exif = Image.new(img.mode, img.size)
                img_without_exif.putdata(data)
                img_without_exif.save(output_path, optimize=True)
                return {'success': True, 'path': output_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_image_stats(self, image_path: str) -> Dict[str, Any]:
        """获取图片统计信息"""
        try:
            with Image.open(image_path) as img:
                file_size = os.path.getsize(image_path)
                return {
                    'success': True, 'width': img.width, 'height': img.height,
                    'format': img.format, 'mode': img.mode, 'file_size': file_size,
                    'file_size_human': self._format_file_size(file_size),
                    'aspect_ratio': round(img.width / img.height, 2) if img.height > 0 else 0
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"


# 全局实例
media_enhancement = MediaEnhancementService()
