"""
资源优化服务

提供CSS/JS压缩、图片优化、资源合并等功能
支持CDN集成和版本化管理
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ResourceOptimizer:
    """
    资源优化服务

    提供静态资源的压缩、优化和版本化管理
    """

    def __init__(self, source_dir: str = "static", output_dir: str = "static/optimized"):
        """
        初始化资源优化器

        Args:
            source_dir: 源文件目录
            output_dir: 优化后输出目录
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 版本映射表
        self.version_map = {}
        self.version_map_file = self.output_dir / "versions.json"

        # 加载现有版本映射
        self._load_version_map()

    def _load_version_map(self):
        """加载版本映射表"""
        import json

        if self.version_map_file.exists():
            try:
                with open(self.version_map_file, 'r', encoding='utf-8') as f:
                    self.version_map = json.load(f)
            except Exception as e:
                print(f"[ResourceOptimizer] Failed to load version map: {e}")
                self.version_map = {}

    def _save_version_map(self):
        """保存版本映射表"""
        import json

        try:
            with open(self.version_map_file, 'w', encoding='utf-8') as f:
                json.dump(self.version_map, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ResourceOptimizer] Failed to save version map: {e}")

    def generate_version_hash(self, file_path: Path) -> str:
        """
        生成文件版本哈希

        Args:
            file_path: 文件路径

        Returns:
            版本哈希字符串
        """
        # 基于文件内容和修改时间生成哈希
        content_hash = hashlib.md5()

        if file_path.exists():
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    content_hash.update(chunk)

            # 添加修改时间
            mtime = file_path.stat().st_mtime
            content_hash.update(str(mtime).encode())

        return content_hash.hexdigest()[:8]

    def get_versioned_url(self, original_url: str) -> str:
        """
        获取带版本号的URL

        Args:
            original_url: 原始URL

        Returns:
            带版本号的URL
        """
        # 提取文件路径
        if '?' in original_url:
            path = original_url.split('?')[0]
        else:
            path = original_url

        # 查找版本
        version = self.version_map.get(path)

        if version:
            separator = '&' if '?' in original_url else '?'
            return f"{original_url}{separator}v={version}"

        return original_url

    def optimize_css(self, css_content: str, minify: bool = True) -> str:
        """
        优化CSS内容

        Args:
            css_content: CSS内容
            minify: 是否压缩

        Returns:
            优化后的CSS
        """
        if not minify:
            return css_content

        # 简单的CSS压缩
        optimized = css_content

        # 移除注释
        import re
        optimized = re.sub(r'/\*.*?\*/', '', optimized, flags=re.DOTALL)

        # 移除多余空白
        optimized = re.sub(r'\s+', ' ', optimized)

        # 移除空格（在特定字符前后）
        optimized = re.sub(r'\s*([{}:;,])\s*', r'\1', optimized)

        # 移除最后的分号
        optimized = re.sub(r';}', '}', optimized)

        return optimized.strip()

    def optimize_js(self, js_content: str, minify: bool = True) -> str:
        """
        优化JavaScript内容

        Args:
            js_content: JavaScript内容
            minify: 是否压缩

        Returns:
            优化后的JavaScript
        """
        if not minify:
            return js_content

        # 简单的JS压缩
        optimized = js_content

        # 移除单行注释（但保留URL中的//）
        import re
        optimized = re.sub(r'(?<!:)//[^\n]*', '', optimized)

        # 移除多行注释
        optimized = re.sub(r'/\*.*?\*/', '', optimized, flags=re.DOTALL)

        # 移除多余空白（简化版）
        lines = [line.strip() for line in optimized.split('\n') if line.strip()]
        optimized = ' '.join(lines)

        return optimized.strip()

    def optimize_image(self, image_path: Path, quality: int = 85,
                       max_width: Optional[int] = None) -> Path:
        """
        优化图片

        Args:
            image_path: 图片路径
            quality: 压缩质量 (1-100)
            max_width: 最大宽度（可选）

        Returns:
            优化后的图片路径
        """
        try:
            from PIL import Image

            # 打开图片
            img = Image.open(image_path)

            # 转换格式（如果需要）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # 调整大小
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            # 生成输出路径
            relative_path = image_path.relative_to(self.source_dir)
            output_path = self.output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存优化后的图片
            img.save(output_path, optimize=True, quality=quality)

            print(f"[ResourceOptimizer] Optimized image: {image_path} -> {output_path}")
            return output_path

        except ImportError:
            print("[ResourceOptimizer] PIL not installed, skipping image optimization")
            return image_path
        except Exception as e:
            print(f"[ResourceOptimizer] Failed to optimize image {image_path}: {e}")
            return image_path

    def process_css_file(self, css_file: Path, minify: bool = True) -> Path:
        """
        处理CSS文件

        Args:
            css_file: CSS文件路径
            minify: 是否压缩

        Returns:
            优化后的文件路径
        """
        # 读取CSS内容
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # 优化CSS
        optimized_css = self.optimize_css(css_content, minify)

        # 生成输出路径
        relative_path = css_file.relative_to(self.source_dir)
        output_path = self.output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入优化后的内容
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(optimized_css)

        # 更新版本映射
        version = self.generate_version_hash(output_path)
        self.version_map[str(relative_path)] = version
        self._save_version_map()

        print(f"[ResourceOptimizer] Processed CSS: {css_file} -> {output_path}")
        return output_path

    def process_js_file(self, js_file: Path, minify: bool = True) -> Path:
        """
        处理JavaScript文件

        Args:
            js_file: JS文件路径
            minify: 是否压缩

        Returns:
            优化后的文件路径
        """
        # 读取JS内容
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()

        # 优化JS
        optimized_js = self.optimize_js(js_content, minify)

        # 生成输出路径
        relative_path = js_file.relative_to(self.source_dir)
        output_path = self.output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入优化后的内容
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(optimized_js)

        # 更新版本映射
        version = self.generate_version_hash(output_path)
        self.version_map[str(relative_path)] = version
        self._save_version_map()

        print(f"[ResourceOptimizer] Processed JS: {js_file} -> {output_path}")
        return output_path

    def batch_optimize(self, file_types: List[str] = ['css', 'js', 'png', 'jpg', 'jpeg', 'gif'],
                       minify: bool = True, image_quality: int = 85) -> Dict[str, int]:
        """
        批量优化资源

        Args:
            file_types: 要优化的文件类型列表
            minify: 是否压缩文本文件
            image_quality: 图片压缩质量

        Returns:
            优化统计信息
        """
        stats = {
            'css': 0,
            'js': 0,
            'images': 0,
            'total': 0,
        }

        # 遍历源目录
        for file_type in file_types:
            pattern = f"**/*.{file_type}"
            files = list(self.source_dir.glob(pattern))

            for file_path in files:
                try:
                    if file_type in ['css']:
                        self.process_css_file(file_path, minify)
                        stats['css'] += 1
                    elif file_type in ['js']:
                        self.process_js_file(file_path, minify)
                        stats['js'] += 1
                    elif file_type in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                        self.optimize_image(file_path, quality=image_quality)
                        stats['images'] += 1

                    stats['total'] += 1

                except Exception as e:
                    print(f"[ResourceOptimizer] Failed to process {file_path}: {e}")

        print(f"[ResourceOptimizer] Batch optimization complete: {stats}")
        return stats

    def generate_resource_manifest(self) -> Dict:
        """
        生成资源清单

        Returns:
            资源清单字典
        """
        manifest = {
            'generated_at': datetime.now().isoformat(),
            'version_map': self.version_map,
            'resources': {},
        }

        # 扫描输出目录
        for file_path in self.output_dir.rglob('*'):
            if file_path.is_file() and file_path.name != 'versions.json':
                relative_path = str(file_path.relative_to(self.output_dir))
                file_size = file_path.stat().st_size

                manifest['resources'][relative_path] = {
                    'size': file_size,
                    'version': self.version_map.get(relative_path),
                    'url': f"/api/v2/static/optimized/{relative_path}",
                }

        # 保存清单
        manifest_path = self.output_dir / "manifest.json"
        import json
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest

    def clear_cache(self):
        """清空优化缓存"""
        import shutil

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.version_map = {}
        print("[ResourceOptimizer] Cache cleared")


# 全局实例
resource_optimizer = ResourceOptimizer()

# 导出
__all__ = ['ResourceOptimizer', 'resource_optimizer']
