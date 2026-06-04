"""
在线图片编辑服务
提供基本的图片处理功能
"""

import io
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from PIL import Image, ImageFilter, ImageEnhance, ImageOps

# 滤镜映射（类级别常量）
FILTERS = {
    'blur': ImageFilter.BLUR,
    'sharpen': ImageFilter.SHARPEN,
    'edge_enhance': ImageFilter.EDGE_ENHANCE,
    'emboss': ImageFilter.EMBOSS,
    'smooth': ImageFilter.SMOOTH,
    'contour': ImageFilter.CONTOUR,
    'detail': ImageFilter.DETAIL,
}

# 操作映射
OPERATION_MAP = {
    'resize': '_resize',
    'crop': '_crop',
    'rotate': '_rotate',
    'flip': '_flip',
    'brightness': '_adjust_brightness',
    'contrast': '_adjust_contrast',
    'filter': '_apply_filter',
    'grayscale': '_to_grayscale',
}


class ImageEditor:
    """
    图片编辑器
    
    功能:
    1. 裁剪
    2. 旋转
    3. 调整大小
    4. 滤镜效果
    5. 亮度/对比度调整
    """

    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'WEBP', 'GIF']

    def process_image(
            self,
            image_path: str,
            operations: list
    ) -> Tuple[bool, str, Optional[bytes]]:
        """
        处理图片(应用多个操作)
        
        Args:
            image_path: 图片路径
            operations: 操作列表
            
        Returns:
            (成功标志, 消息, 处理后图片数据)
        """
        try:
            # 打开图片
            img = Image.open(image_path)

            # 转换为RGB(如果需要)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # 依次应用操作
            for operation in operations:
                op_type = operation.get('type')
                method_name = OPERATION_MAP.get(op_type)
                if method_name:
                    method = getattr(self, method_name)
                    img = method(img, operation)

            # 保存为字节流
            output = io.BytesIO()
            format_name = img.format or 'JPEG'
            img.save(output, format=format_name, quality=90)
            output.seek(0)

            return True, "处理成功", output.getvalue()

        except Exception as e:
            return False, f"处理失败: {str(e)}", None

    def _resize(self, img: Image.Image, operation: Dict[str, Any]) -> Image.Image:
        """调整大小"""
        width = operation.get('width')
        height = operation.get('height')
        maintain_aspect = operation.get('maintain_aspect', True)

        if maintain_aspect:
            # 保持宽高比
            img.thumbnail((width, height), Image.LANCZOS)
        else:
            img = img.resize((width, height), Image.LANCZOS)

        return img

    def _crop(self, img: Image.Image, operation: Dict[str, Any]) -> Image.Image:
        """裁剪"""
        left = operation.get('left', 0)
        top = operation.get('top', 0)
        right = operation.get('right', img.width)
        bottom = operation.get('bottom', img.height)

        return img.crop((left, top, right, bottom))

    def _rotate(self, img: Image.Image, operation: Dict[str, Any]) -> Image.Image:
        """旋转"""
        angle = operation.get('angle', 0)
        expand = operation.get('expand', True)

        return img.rotate(angle, expand=expand, resample=Image.BICUBIC)

    def _flip(self, img: Image.Image, operation: Dict[str, Any]) -> Image.Image:
        """翻转"""
        direction = operation.get('direction', 'horizontal')

        if direction == 'horizontal':
            return img.transpose(Image.FLIP_LEFT_RIGHT)
        else:
            return img.transpose(Image.FLIP_TOP_BOTTOM)

    def _adjust_brightness(self, img: Image.Image, operation: Dict[str, Any]) -> Image.Image:
        """调整亮度"""
        factor = operation.get('factor', 1.0)  # 0.0-2.0

        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def _adjust_contrast(self, img: Image.Image, operation: Dict[str, Any]) -> Image.Image:
        """调整对比度"""
        factor = operation.get('factor', 1.0)  # 0.0-2.0

        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def _apply_filter(self, img: Image.Image, operation: Dict[str, Any]) -> Image.Image:
        """应用滤镜"""
        filter_name = operation.get('filter', 'none')
        img_filter = FILTERS.get(filter_name)
        return img.filter(img_filter) if img_filter else img

    def _to_grayscale(self, img: Image.Image) -> Image.Image:
        """转为灰度"""
        return ImageOps.grayscale(img).convert('RGB')

    def get_image_info(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        获取图片信息
        
        Args:
            image_path: 图片路径
            
        Returns:
            图片信息字典
        """
        try:
            img = Image.open(image_path)

            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size': Path(image_path).stat().st_size,
            }
        except Exception as e:
            print(f"获取图片信息失败: {e}")
            return None


# 全局实例
image_editor = ImageEditor()
