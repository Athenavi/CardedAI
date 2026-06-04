"""
图片版本管理服务
负责生成多种尺寸的图片版本并管理原图备份
"""


import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

# 原: from updater.updater import base_dir
# updater/ 被 .dockerignore 排除，改为本地计算项目根目录
base_dir = Path(__file__).resolve().parents[4]  # shared/services/media/image_tool/ → 项目根

from src.unified_logger import default_logger as logger

# 预定义的尺寸配置
SIZE_PRESETS = {
    'thumbnail': {'width': 150, 'height': 150, 'crop': True},
    'small': {'width': 400, 'height': None, 'crop': False},
    'medium': {'width': 800, 'height': None, 'crop': False},
    'large': {'width': 1200, 'height': None, 'crop': False},
    'original': None  # 原图，不处理
}


class ImageVersionManager:
    """
    图片版本管理器

    功能:
    1. 生成多个尺寸的图片版本 (thumbnail, small, medium, large)
    2. 保留原图备份
    3. 管理版本文件生命周期
    """

    def __init__(self):
        self.media_root = base_dir / 'media'

    def generate_versions(
            self,
            image_path: str,
            sizes: Optional[List[str]] = None,
            quality: int = 85,
            backup_original: bool = True
    ) -> Dict[str, str]:
        """
        为图片生成多个尺寸版本

        Args:
            image_path: 原图路径（相对于MEDIA_ROOT）
            sizes: 需要生成的尺寸列表，默认为 ['thumbnail', 'small', 'medium', 'large']
            quality: JPEG/WEBP 质量 (1-100)
            backup_original: 是否备份原图

        Returns:
            生成的版本字典 {size_name: file_path}
        """
        if sizes is None:
            sizes = ['thumbnail', 'small', 'medium', 'large']

        # 完整路径
        full_path = os.path.join(self.media_root, image_path.lstrip('/'))

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"图片文件不存在: {full_path}")

        # 备份原图
        if backup_original:
            self._backup_original(full_path)

        # 打开图片
        img = Image.open(full_path)

        # 获取文件信息
        file_stem = Path(image_path).stem
        file_ext = Path(image_path).suffix.lower()
        file_dir = os.path.dirname(full_path)

        generated_versions = {}

        # 生成各个尺寸版本
        for size_name in sizes:
            preset = SIZE_PRESETS.get(size_name)
            if preset is None:
                logger.warning(f"不支持的尺寸预设: {size_name}")
                continue

            if preset is None:  # original
                continue

            try:
                # 生成版本
                version_path = self._generate_version(
                    img, file_dir, file_stem, file_ext,
                    size_name, preset, quality
                )

                # 转换为相对路径
                relative_path = os.path.relpath(version_path, self.media_root)
                generated_versions[size_name] = relative_path
                logger.info(f"已生成 {size_name} 版本: {relative_path}")

            except Exception as e:
                logger.error(f"生成 {size_name} 版本失败: {e}")
                continue

        return generated_versions

    def _backup_original(self, image_path: str) -> str:
        """
        备份原图

        Args:
            image_path: 原图完整路径

        Returns:
            备份文件路径
        """
        backup_dir = os.path.join(os.path.dirname(image_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # 生成带时间戳的备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_name = Path(image_path).stem
        original_ext = Path(image_path).suffix
        backup_filename = f"{original_name}_backup_{timestamp}{original_ext}"
        backup_path = os.path.join(backup_dir, backup_filename)

        # 复制文件
        shutil.copy2(image_path, backup_path)
        logger.info(f"原图已备份到: {backup_path}")

        return backup_path

    def _generate_version(
            self,
            img: Image.Image,
            output_dir: str,
            file_stem: str,
            file_ext: str,
            size_name: str,
            preset: Dict,
            quality: int
    ) -> str:
        """
        生成单个尺寸版本

        Args:
            img: PIL图片对象
            output_dir: 输出目录
            file_stem: 文件名（不含扩展名）
            file_ext: 文件扩展名
            size_name: 尺寸名称
            preset: 尺寸预设配置
            quality: 输出质量

        Returns:
            生成的版本文件路径
        """
        width = preset['width']
        height = preset.get('height')
        crop = preset.get('crop', False)

        # 创建副本以避免修改原图
        img_copy = img.copy()

        if crop and height:
            # 居中裁剪为固定尺寸
            img_copy = self._center_crop(img_copy, width, height)
        else:
            # 保持宽高比调整大小
            if height:
                img_copy.thumbnail((width, height), Image.LANCZOS)
            else:
                # 只指定宽度
                ratio = width / img_copy.width
                new_height = int(img_copy.height * ratio)
                img_copy = img_copy.resize((width, new_height), Image.LANCZOS)

        # 生成输出文件名
        output_filename = f"{file_stem}_{size_name}{file_ext}"
        output_path = os.path.join(output_dir, output_filename)

        # 保存图片
        save_kwargs = {}
        output_format = file_ext.lstrip('.').upper()

        if output_format in ['JPEG', 'WEBP']:
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True

            # JPEG 不支持透明通道
            if output_format == 'JPEG' and img_copy.mode in ('RGBA', 'P'):
                img_copy = img_copy.convert('RGB')

        img_copy.save(output_path, format=output_format, **save_kwargs)

        return output_path

    def _center_crop(self, img: Image.Image, width: int, height: int) -> Image.Image:
        """
        居中裁剪图片

        Args:
            img: PIL图片对象
            width: 目标宽度
            height: 目标高度

        Returns:
            裁剪后的图片
        """
        # 先调整大小，保持比例
        img_copy = img.copy()
        img_copy.thumbnail((max(width, height), max(width, height)), Image.LANCZOS)

        # 计算裁剪区域
        img_width, img_height = img_copy.size
        left = (img_width - width) // 2
        top = (img_height - height) // 2
        right = left + width
        bottom = top + height

        # 确保坐标在范围内
        left = max(0, min(left, img_width - width))
        top = max(0, min(top, img_height - height))
        right = min(right, img_width)
        bottom = min(bottom, img_height)

        return img_copy.crop((left, top, right, bottom))

    def cleanup_versions(
            self,
            image_path: str,
            sizes: Optional[List[str]] = None
    ) -> List[str]:
        """
        清理指定图片的所有版本

        Args:
            image_path: 原图路径
            sizes: 要清理的尺寸列表，默认为所有

        Returns:
            已删除的文件列表
        """
        if sizes is None:
            sizes = list(SIZE_PRESETS.keys())

        deleted_files = []
        full_path = os.path.join(self.media_root, image_path.lstrip('/'))
        file_dir = os.path.dirname(full_path)
        file_stem = Path(image_path).stem
        file_ext = Path(image_path).suffix

        for size_name in sizes:
            version_filename = f"{file_stem}_{size_name}{file_ext}"
            version_path = os.path.join(file_dir, version_filename)

            if os.path.exists(version_path):
                try:
                    os.remove(version_path)
                    deleted_files.append(version_path)
                    logger.info(f"已删除版本: {version_path}")
                except Exception as e:
                    logger.error(f"删除版本失败 {version_path}: {e}")

        return deleted_files

    def get_version_path(
            self,
            image_path: str,
            size_name: str
    ) -> Optional[str]:
        """
        获取指定版本的文件路径

        Args:
            image_path: 原图路径
            size_name: 尺寸名称

        Returns:
            版本文件路径，如果不存在则返回 None
        """
        full_path = os.path.join(self.media_root, image_path.lstrip('/'))
        file_dir = os.path.dirname(full_path)
        file_stem = Path(image_path).stem
        file_ext = Path(image_path).suffix

        version_filename = f"{file_stem}_{size_name}{file_ext}"
        version_path = os.path.join(file_dir, version_filename)

        if os.path.exists(version_path):
            return os.path.relpath(version_path, self.media_root)

        return None


# 全局实例
image_version_manager = ImageVersionManager()
