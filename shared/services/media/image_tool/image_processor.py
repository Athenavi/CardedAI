"""
图片处理服务
提供裁剪、旋转、缩放、质量调整等功能
使用 Pillow 库进行图片处理
"""

import io

from typing import Dict, Any, Tuple

from PIL import Image, ImageOps, ExifTags, ImageFilter

from src.unified_logger import default_logger as logger

# MIME 类型映射
MIME_TYPES = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'WEBP': 'image/webp',
    'GIF': 'image/gif',
    'BMP': 'image/bmp'
}

# 滤镜映射
FILTERS = {
    'blur': ImageFilter.BLUR,
    'sharpen': ImageFilter.SHARPEN,
    'smooth': ImageFilter.SMOOTH,
    'emboss': ImageFilter.EMBOSS,
    'contour': ImageFilter.CONTOUR,
    'detail': ImageFilter.DETAIL,
    'edge_enhance': ImageFilter.EDGE_ENHANCE,
    'edge_enhance_more': ImageFilter.EDGE_ENHANCE_MORE,
    'find_edges': ImageFilter.FIND_EDGES,
}

# 支持的图片格式
SUPPORTED_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF', 'BMP'}

# 从 PIL 导入增强和滤镜模块（避免重复导入）
from PIL import ImageEnhance


class ImageProcessor:
    """
    图片处理器
    
    功能:
    1. 图片裁剪
    2. 图片旋转
    3. 图片缩放
    4. 质量调整
    5. 格式转换
    6. EXIF 数据处理
    """

    def process_image(
            self,
            image_data: bytes,
            operations: Dict[str, Any]
    ) -> Tuple[bytes, str]:
        """
        处理图片（支持多个操作）
        
        Args:
            image_data: 原始图片数据（字节）
            operations: 操作配置 {
                'crop': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                'rotate': 90,
                'resize': {'width': 800, 'height': 600},
                'quality': 85,
                'format': 'JPEG'
            }
            
        Returns:
            (处理后的图片数据, MIME类型)
        """
        try:
            # 打开图片
            img = Image.open(io.BytesIO(image_data))

            # 自动旋转（根据EXIF方向）
            img = ImageOps.exif_transpose(img)

            # 执行操作
            if 'crop' in operations:
                img = self._crop(img, operations['crop'])

            if 'rotate' in operations:
                img = self._rotate(img, operations['rotate'])

            if 'flip' in operations:
                img = self._flip(img, operations['flip'])

            if 'resize' in operations:
                img = self._resize(img, operations['resize'])

            if 'thumbnail' in operations:
                img = self._create_thumbnail(img, operations['thumbnail'])

            if 'brightness' in operations:
                img = self._adjust_brightness(img, operations['brightness'])

            if 'contrast' in operations:
                img = self._adjust_contrast(img, operations['contrast'])

            if 'filter' in operations:
                img = self._apply_filter(img, operations['filter'])

            # 确定输出格式
            output_format = operations.get('format', img.format or 'JPEG')
            quality = operations.get('quality', 85)

            # 保存为字节流
            output_buffer = io.BytesIO()

            # PNG不支持quality参数
            save_kwargs = {}
            if output_format.upper() == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
                # 转换为RGB（去除透明通道）
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
            elif output_format.upper() == 'WEBP':
                save_kwargs['quality'] = quality

            img.save(output_buffer, format=output_format.upper(), **save_kwargs)
            output_buffer.seek(0)

            # 确定MIME类型
            mime_type = MIME_TYPES.get(output_format.upper(), 'image/jpeg')

            return output_buffer.getvalue(), mime_type

        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            raise ValueError(f"图片处理失败: {str(e)}")

    def _crop(self, img: Image.Image, crop_params: Dict[str, int]) -> Image.Image:
        """
        裁剪图片
        
        Args:
            img: PIL图片对象
            crop_params: {'x': 0, 'y': 0, 'width': 100, 'height': 100}
            
        Returns:
            裁剪后的图片
        """
        x = crop_params.get('x', 0)
        y = crop_params.get('y', 0)
        width = crop_params.get('width')
        height = crop_params.get('height')

        if not width or not height:
            raise ValueError("裁剪需要提供宽度和高度")

        # 确保坐标在图片范围内
        x = max(0, min(x, img.width - 1))
        y = max(0, min(y, img.height - 1))
        right = min(x + width, img.width)
        bottom = min(y + height, img.height)

        return img.crop((x, y, right, bottom))

    def _flip(self, img: Image.Image, flip_params: Dict[str, Any]) -> Image.Image:
        """
        翻转图片
        
        Args:
            img: PIL图片对象
            flip_params: {'horizontal': True, 'vertical': False}
            
        Returns:
            翻转后的图片
        """
        if flip_params.get('horizontal'):
            img = img.transpose(Image.FLIP_LEFT_RIGHT)

        if flip_params.get('vertical'):
            img = img.transpose(Image.FLIP_TOP_BOTTOM)

        return img

    def _adjust_brightness(self, img: Image.Image, factor: float) -> Image.Image:
        """
        调整亮度
        
        Args:
            img: PIL图片对象
            factor: 亮度因子 (0.0-2.0, 1.0为原图)
            
        Returns:
            调整后的图片
        """
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def _adjust_contrast(self, img: Image.Image, factor: float) -> Image.Image:
        """
        调整对比度
        
        Args:
            img: PIL图片对象
            factor: 对比度因子 (0.0-2.0, 1.0为原图)
            
        Returns:
            调整后的图片
        """
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def _apply_filter(self, img: Image.Image, filter_name: str) -> Image.Image:
        """
        应用滤镜
        
        Args:
            img: PIL图片对象
            filter_name: 滤镜名称 (blur, sharpen, smooth, emboss, contour, detail, edge_enhance)
            
        Returns:
            滤镜处理后的图片
        """
        img_filter = FILTERS.get(filter_name)
        if img_filter:
            return img.filter(img_filter)

        logger.warning(f"不支持的滤镜: {filter_name}")
        return img

    def _rotate(self, img: Image.Image, angle: float) -> Image.Image:
        """
        旋转图片
        
        Args:
            img: PIL图片对象
            angle: 旋转角度（度）
            
        Returns:
            旋转后的图片
        """
        # expand=True 确保图片不被裁剪
        return img.rotate(angle, expand=True, resample=Image.BICUBIC)

    def _resize(self, img: Image.Image, resize_params: Dict[str, int]) -> Image.Image:
        """
        调整图片大小
        
        Args:
            img: PIL图片对象
            resize_params: {
                'width': 800, 'height': 600, 
                'maintain_aspect': True,
                'max_width': 1920, 'max_height': 1080  # 新增：最大宽高限制
            }
            
        Returns:
            调整后的图片
        """
        width = resize_params.get('width')
        height = resize_params.get('height')
        max_width = resize_params.get('max_width')
        max_height = resize_params.get('max_height')
        maintain_aspect = resize_params.get('maintain_aspect', True)

        # 如果指定了最大宽高，先进行缩放
        if max_width or max_height:
            if maintain_aspect:
                # 保持宽高比缩放到最大尺寸内
                img.thumbnail((max_width or 99999, max_height or 99999), Image.LANCZOS)
            else:
                # 强制缩放到最大尺寸
                new_width = min(img.width, max_width) if max_width else img.width
                new_height = min(img.height, max_height) if max_height else img.height
                img = img.resize((new_width, new_height), Image.LANCZOS)

        # 如果还指定了具体宽高，继续调整
        if not width and not height:
            return img

        if maintain_aspect:
            # 保持宽高比
            if width and height:
                img.thumbnail((width, height), Image.LANCZOS)
            elif width:
                # 只指定宽度，按比例计算高度
                ratio = width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((width, new_height), Image.LANCZOS)
            elif height:
                # 只指定高度，按比例计算宽度
                ratio = height / img.height
                new_width = int(img.width * ratio)
                img = img.resize((new_width, height), Image.LANCZOS)
        else:
            # 强制拉伸到指定尺寸
            img = img.resize((width, height), Image.LANCZOS)

        return img

    def _create_thumbnail(self, img: Image.Image, size: int) -> Image.Image:
        """
        创建缩略图（正方形，居中裁剪）
        
        Args:
            img: PIL图片对象
            size: 缩略图边长
            
        Returns:
            缩略图
        """
        # 先调整大小，保持比例
        img_copy = img.copy()
        img_copy.thumbnail((size, size), Image.LANCZOS)

        # 居中裁剪为正方形
        width, height = img_copy.size
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size

        return img_copy.crop((left, top, right, bottom))

    def get_image_info(self, image_data: bytes) -> Dict[str, Any]:
        """
        获取图片信息
        
        Args:
            image_data: 图片数据（字节）
            
        Returns:
            图片信息字典
        """
        try:
            img = Image.open(io.BytesIO(image_data))

            info = {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': len(image_data),
                'aspect_ratio': round(img.width / img.height, 2) if img.height > 0 else 0
            }

            # 尝试获取EXIF数据
            exif_data = {}
            if hasattr(img, '_getexif') and img._getexif():
                for tag_id, value in img._getexif().items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    # 跳过二进制数据
                    if isinstance(value, bytes):
                        continue
                    exif_data[tag_name] = value

            if exif_data:
                info['exif'] = exif_data

            return info

        except Exception as e:
            logger.error(f"获取图片信息失败: {e}")
            raise ValueError(f"无法读取图片信息: {str(e)}")

    def validate_image(self, image_data: bytes, max_size_mb: float = 10) -> Dict[str, Any]:
        """
        验证图片
        
        Args:
            image_data: 图片数据（字节）
            max_size_mb: 最大文件大小（MB）
            
        Returns:
            验证结果 {'valid': bool, 'errors': []}
        """
        errors = []

        # 检查文件大小
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > max_size_mb:
            errors.append(f"图片文件过大 ({size_mb:.2f}MB)，最大允许 {max_size_mb}MB")

        # 检查是否为有效图片
        try:
            img = Image.open(io.BytesIO(image_data))
            img.verify()
        except Exception:
            errors.append("无效的图片文件格式")
            return {'valid': False, 'errors': errors}

        # 重新打开（verify后会关闭）
        img = Image.open(io.BytesIO(image_data))

        # 检查格式
        if img.format not in self.SUPPORTED_FORMATS:
            errors.append(f"不支持的图片格式: {img.format}，支持的格式: {', '.join(self.SUPPORTED_FORMATS)}")

        # 检查尺寸
        if img.width < 10 or img.height < 10:
            errors.append(f"图片尺寸过小 ({img.width}x{img.height})")

        if img.width > 10000 or img.height > 10000:
            errors.append(f"图片尺寸过大 ({img.width}x{img.height})")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'info': {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'size_mb': round(size_mb, 2)
            }
        }


# 全局实例
image_processor = ImageProcessor()
