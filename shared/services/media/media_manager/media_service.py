"""
媒体管理服务
整合缩略图生成、分类标签、批量操作、EXIF处理
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from PIL import Image, ExifTags

from shared.models import Media

# 默认缩略图尺寸配置
DEFAULT_THUMBNAIL_SIZES = [
    ('small', (150, 150)),
    ('medium', (300, 300)),
    ('large', (600, 600)),
]

# EXIF 日期格式
EXIF_DATE_FORMAT = '%Y:%m:%d %H:%M:%S'


class MediaService:
    """
    媒体服务
    
    功能:
    1. 自动生成多尺寸缩略图
    2. 媒体分类和标签管理
    3. 批量操作支持
    4. EXIF数据提取和处理
    """

    def __init__(self, media_dir: str = "storage/objects"):
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    # ==================== 缩略图生成 ====================

    def generate_thumbnails(
            self,
            image_path: str,
            sizes: List[Tuple[str, Tuple[int, int]]] = None
    ) -> Dict[str, str]:
        """生成多尺寸缩略图"""
        sizes = sizes or DEFAULT_THUMBNAIL_SIZES
        thumbnails = {}

        try:
            img = Image.open(image_path)
            for size_name, dimensions in sizes:
                thumb = img.copy()
                thumb.thumbnail(dimensions, Image.LANCZOS)
                thumb_path = self._get_thumbnail_path(image_path, size_name)
                thumb.save(thumb_path, optimize=True, quality=85)
                thumbnails[size_name] = str(thumb_path)
        except Exception as e:
            print(f"生成缩略图失败: {e}")

        return thumbnails

    def _get_thumbnail_path(self, original_path: str, size_name: str) -> Path:
        """获取缩略图路径"""
        original = Path(original_path)
        return original.parent / f"{original.stem}_{size_name}{original.suffix}"

    # ==================== 分类和标签 ====================

    def _parse_tags(self, tags_str: str) -> List[str]:
        """解析标签字符串为列表"""
        if not tags_str:
            return []
        return [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    
    def add_tags(self, media_id: int, tags: List[str]) -> bool:
        """为媒体添加标签"""
        try:
            media = Media.objects.get(id=media_id)
            existing_tags = set(self._parse_tags(media.tags))
            existing_tags.update(tag.strip() for tag in tags if tag.strip())
            media.tags = ','.join(existing_tags)
            media.save()
            return True
        except Exception as e:
            print(f"添加标签失败: {e}")
            return False

    def remove_tags(self, media_id: int, tags: List[str]) -> bool:
        """移除标签"""
        try:
            media = Media.objects.get(id=media_id)
            existing_tags = set(self._parse_tags(media.tags))
            tags_to_remove = {tag.strip() for tag in tags}
            existing_tags -= tags_to_remove
            media.tags = ','.join(existing_tags) if existing_tags else None
            media.save()
            return True
        except Exception as e:
            print(f"移除标签失败: {e}")
            return False

    def get_media_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """根据标签获取媒体"""
        try:

            # 查询包含该标签的媒体
            medias = Media.objects.filter(tags__icontains=tag)

            return [media.to_dict() for media in medias]
        except Exception as e:
            print(f"查询标签媒体失败: {e}")
            return []

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        try:
            medias = Media.objects.exclude(tags__isnull=True).exclude(tags='')
            all_tags = set()
            for media in medias:
                all_tags.update(self._parse_tags(media.tags))
            return sorted(all_tags)
        except Exception as e:
            print(f"获取所有标签失败: {e}")
            return []

    def categorize_media(self, media_id: int, category: str) -> bool:
        """分类媒体"""
        try:

            media = Media.objects.get(id=media_id)
            media.category = category
            media.save()

            return True
        except Exception as e:
            print(f"分类媒体失败: {e}")
            return False

    # ==================== 批量操作 ====================

    def batch_delete(self, media_ids: List[int]) -> Dict[str, Any]:
        """批量删除媒体"""
        results = {'success': 0, 'failed': 0, 'errors': []}

        try:
            import os

            for media_id in media_ids:
                try:
                    media = Media.objects.get(id=media_id)
                    # 删除文件
                    for file_path in [media.file_path, media.thumbnail_path]:
                        if file_path and os.path.exists(file_path):
                            os.remove(file_path)
                    media.delete()
                    results['success'] += 1
                except Media.DoesNotExist:
                    results['failed'] += 1
                    results['errors'].append({'media_id': media_id, 'error': '媒体不存在'})
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'media_id': media_id, 'error': str(e)})
        except Exception as e:
            print(f"批量删除失败: {e}")
            
        return results

    def batch_update_tags(self, media_ids: List[int], tags: List[str]) -> Dict[str, Any]:
        """批量更新标签"""
        results = {'success': 0, 'failed': 0}

        for media_id in media_ids:
            if self.add_tags(media_id, tags):
                results['success'] += 1
            else:
                results['failed'] += 1

        return results

    def batch_categorize(self, media_ids: List[int], category: str) -> Dict[str, Any]:
        """批量分类"""
        results = {'success': 0, 'failed': 0}

        for media_id in media_ids:
            if self.categorize_media(media_id, category):
                results['success'] += 1
            else:
                results['failed'] += 1

        return results

    # ==================== EXIF数据处理 ====================

    def extract_exif(self, image_path: str) -> Dict[str, Any]:
        """提取EXIF数据"""
        try:
            img = Image.open(image_path)
            exif_data = {'width': img.width, 'height': img.height, 'format': img.format}

            if hasattr(img, '_getexif') and img._getexif():
                for tag_id, value in img._getexif().items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    if isinstance(value, bytes):
                        continue

                    if tag_name == 'DateTimeOriginal':
                        try:
                            exif_data['date_taken'] = datetime.strptime(value, EXIF_DATE_FORMAT).isoformat()
                        except ValueError:
                            pass
                    elif tag_name == 'GPSInfo':
                        exif_data['gps'] = self._parse_gps_info(value)
                    else:
                        exif_data[tag_name.lower()] = value

            return exif_data
        except Exception as e:
            print(f"提取EXIF失败: {e}")
            return {}

    def _parse_gps_info(self, gps_info: Dict) -> Optional[Dict[str, float]]:
        """解析GPS信息"""
        try:
            return {
                'latitude': float(gps_info.get(2, [0])[0]),
                'longitude': float(gps_info.get(4, [0])[0]),
            }
        except (TypeError, IndexError, ValueError):
            return None

    def remove_exif(self, image_path: str, output_path: str = None) -> bool:
        """移除EXIF数据(保护隐私)"""
        try:
            img = Image.open(image_path)
            data = list(img.getdata())
            img_without_exif = Image.new(img.mode, img.size)
            img_without_exif.putdata(data)
            img_without_exif.save(output_path or image_path, optimize=True, quality=90)
            return True
        except Exception as e:
            print(f"移除EXIF失败: {e}")
            return False


# 全局实例
media_service = MediaService()
