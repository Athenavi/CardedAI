"""
SVG 文件处理服务
提供 SVG 上传、清理、验证和优化功能
"""
import os
from typing import Dict, Any

from shared.utils.svg_sanitizer import sanitize_svg, validate_svg, optimize_svg

# SVG 配置常量
ALLOWED_SVG_MIME_TYPES = {'image/svg+xml'}
MAX_SVG_FILE_SIZE = 1 * 1024 * 1024  # 1MB
DEFAULT_PREVIEW_SIZE = 200


class SVGService:
    """SVG 文件处理服务"""
    
    # 允许的 MIME 类型
    ALLOWED_MIME_TYPES = {
        'image/svg+xml',
    }
    
    # 最大文件大小 (1MB)
    MAX_FILE_SIZE = 1 * 1024 * 1024
    
    @classmethod
    def validate_upload(cls, file_obj) -> tuple[bool, str]:
        """验证上传的 SVG 文件"""
        content_type = file_obj.content_type
        if content_type not in ALLOWED_SVG_MIME_TYPES:
            return False, f"不支持的文件类型: {content_type}。只允许 SVG 文件"

        if file_obj.size > MAX_SVG_FILE_SIZE:
            return False, f"文件大小超过限制 ({MAX_SVG_FILE_SIZE / 1024 / 1024:.0f}MB)"
        
        try:
            file_obj.seek(0)
            svg_content = file_obj.read().decode('utf-8')
            file_obj.seek(0)
        except UnicodeDecodeError:
            return False, "文件编码无效，必须是 UTF-8 编码的 SVG"
        
        try:
            validate_svg(svg_content)
        except ValueError as e:
            return False, str(e)
        
        return True, "验证通过"
    
    @classmethod
    def process_svg(cls, file_obj, save_path: str) -> Dict[str, Any]:
        """处理并保存 SVG 文件"""
        file_obj.seek(0)
        svg_content = file_obj.read().decode('utf-8')
        cleaned_svg = sanitize_svg(svg_content)
        optimized_svg = optimize_svg(cleaned_svg)
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(optimized_svg)
        
        metadata = validate_svg(optimized_svg)
        return {
            'success': True, 'file_size': len(optimized_svg.encode('utf-8')),
            'metadata': metadata, 'path': save_path
        }
    
    @classmethod
    def convert_to_png(cls, svg_path: str, output_path: str) -> bool:
        """将 SVG 转换为 PNG（需要 CairoSVG 库）"""
        try:
            import cairosvg
            cairosvg.svg2png(url=svg_path, write_to=output_path)
            return True
        except (ImportError, Exception):
            return False
    
    @classmethod
    def get_svg_preview(cls, svg_path: str, max_size: int = DEFAULT_PREVIEW_SIZE) -> str:
        """获取 SVG 预览（返回内联 SVG）"""
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            if 'width=' not in svg_content and 'height=' not in svg_content:
                svg_content = svg_content.replace('<svg', f'<svg width="{max_size}" height="{max_size}"')
            
            return svg_content
        except Exception:
            return ''
