"""
代码分割优化服务
提供动态导入、路由懒加载、组件分割等功能
"""

import json
import os
from typing import Dict, List


class CodeSplittingOptimizer:
    """
    代码分割优化器
    
    功能：
    1. 分析bundle大小
    2. 生成代码分割建议
    3. 动态导入映射
    4. 预加载策略
    5. 资源优先级管理
    """

    def __init__(self, build_dir: str = None):
        """
        初始化代码分割优化器
        
        Args:
            build_dir: 构建输出目录
        """
        self.build_dir = build_dir or "frontend-next/.next"
        self.bundle_analysis: Dict = {}
        self.split_recommendations: List[Dict] = []

    def analyze_bundle(self) -> Dict:
        """
        分析bundle大小和结构
        
        Returns:
            bundle分析报告
        """
        if not os.path.exists(self.build_dir):
            return {
                'success': False,
                'error': f'Build directory not found: {self.build_dir}'
            }

        try:
            # 查找统计文件
            stats_file = os.path.join(self.build_dir, 'build-manifest.json')

            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    manifest = json.load(f)

                analysis = self._analyze_manifest(manifest)
                self.bundle_analysis = analysis

                return {
                    'success': True,
                    'analysis': analysis,
                }
            else:
                return {
                    'success': False,
                    'error': 'Build manifest not found',
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def _analyze_manifest(self, manifest: Dict) -> Dict:
        """分析构建清单"""
        chunks = manifest.get('pages', {})

        total_size = 0
        chunk_details = []

        for page, files in chunks.items():
            page_size = 0
            file_details = []

            for file_path in files:
                full_path = os.path.join(self.build_dir, file_path)

                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    page_size += size

                    file_details.append({
                        'file': file_path,
                        'size': size,
                        'size_kb': round(size / 1024, 2),
                    })

            total_size += page_size

            chunk_details.append({
                'page': page,
                'total_size': page_size,
                'total_size_kb': round(page_size / 1024, 2),
                'files': file_details,
                'file_count': len(files),
            })

        # 按大小排序
        chunk_details.sort(key=lambda x: x['total_size'], reverse=True)

        return {
            'total_size': total_size,
            'total_size_kb': round(total_size / 1024, 2),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'chunk_count': len(chunk_details),
            'chunks': chunk_details,
            'largest_chunks': chunk_details[:10],
        }

    def generate_split_recommendations(self, threshold_kb: int = 100) -> List[Dict]:
        """
        生成分割建议
        
        Args:
            threshold_kb: 建议分割的阈值（KB）
            
        Returns:
            分割建议列表
        """
        recommendations = []

        if not self.bundle_analysis:
            self.analyze_bundle()

        for chunk in self.bundle_analysis.get('chunks', []):
            if chunk['total_size_kb'] > threshold_kb:
                recommendation = {
                    'page': chunk['page'],
                    'current_size_kb': chunk['total_size_kb'],
                    'recommendation': '考虑将此页面拆分为更小的chunk',
                    'priority': 'high' if chunk['total_size_kb'] > 500 else 'medium',
                    'suggestions': self._get_split_suggestions(chunk),
                }
                recommendations.append(recommendation)

        self.split_recommendations = recommendations
        return recommendations

    def _get_split_suggestions(self, chunk: Dict) -> List[str]:
        """获取具体的分割建议"""
        suggestions = []

        # 检查是否有大型第三方库
        large_files = [f for f in chunk['files'] if f['size_kb'] > 50]

        if large_files:
            suggestions.append(
                f"发现 {len(large_files)} 个大型文件，考虑使用动态导入"
            )

        # 检查页面类型
        page = chunk['page']

        if '/admin/' in page:
            suggestions.append("管理页面可以考虑按需加载")

        if page.endswith('/index'):
            suggestions.append("首页可以考虑预加载关键资源")

        if chunk['file_count'] > 5:
            suggestions.append(f"此页面有 {chunk['file_count']} 个文件，考虑合并或拆分")

        return suggestions

    def generate_prefetch_hints(self) -> List[Dict]:
        """
        生成预加载提示
        
        Returns:
            预加载资源列表
        """
        prefetch_hints = []

        # 分析常见导航路径
        common_routes = [
            {'from': '/', 'to': '/articles', 'priority': 'high'},
            {'from': '/articles', 'to': '/article/[id]', 'priority': 'medium'},
            {'from': '/', 'to': '/categories', 'priority': 'low'},
        ]

        for route in common_routes:
            prefetch_hints.append({
                'route': route['to'],
                'trigger': route['from'],
                'priority': route['priority'],
                'strategy': 'prefetch' if route['priority'] == 'high' else 'preload',
            })

        return prefetch_hints

    def generate_dynamic_import_map(self) -> Dict:
        """
        生成动态导入映射
        
        Returns:
            动态导入配置
        """
        dynamic_imports = {
            'components': [
                {
                    'name': 'ArticleEditor',
                    'path': '@/components/ArticleEditor',
                    'condition': '用户访问编辑页面时',
                },
                {
                    'name': 'CommentSection',
                    'path': '@/components/CommentSection',
                    'condition': '文章滚动到评论区域时',
                },
                {
                    'name': 'AnalyticsDashboard',
                    'path': '@/components/AnalyticsDashboard',
                    'condition': '管理员访问分析页面时',
                },
            ],
            'pages': [
                {
                    'name': 'AdminPanel',
                    'path': '@/app/admin',
                    'condition': '管理员登录后',
                },
                {
                    'name': 'UserProfile',
                    'path': '@/app/user/[id]',
                    'condition': '访问用户资料页时',
                },
            ],
            'libraries': [
                {
                    'name': 'ChartLibrary',
                    'package': 'recharts',
                    'condition': '渲染图表时',
                },
                {
                    'name': 'RichTextEditor',
                    'package': '@tiptap/react',
                    'condition': '进入编辑模式时',
                },
            ],
        }

        return dynamic_imports

    def get_optimization_report(self) -> Dict:
        """
        获取完整的优化报告
        
        Returns:
            优化报告
        """
        bundle_analysis = self.analyze_bundle()
        split_recommendations = self.generate_split_recommendations()
        prefetch_hints = self.generate_prefetch_hints()
        dynamic_import_map = self.generate_dynamic_import_map()

        return {
            'bundle_analysis': bundle_analysis,
            'split_recommendations': split_recommendations,
            'prefetch_hints': prefetch_hints,
            'dynamic_import_map': dynamic_import_map,
            'summary': {
                'total_chunks': bundle_analysis.get('analysis', {}).get('chunk_count', 0),
                'total_size_kb': bundle_analysis.get('analysis', {}).get('total_size_kb', 0),
                'recommendations_count': len(split_recommendations),
                'estimated_improvement': self._estimate_improvement(split_recommendations),
            },
        }

    def _estimate_improvement(self, recommendations: List[Dict]) -> str:
        """估算优化效果"""
        high_priority = sum(1 for r in recommendations if r.get('priority') == 'high')
        medium_priority = sum(1 for r in recommendations if r.get('priority') == 'medium')

        if high_priority > 3:
            return "预计可减少30-50%初始加载时间"
        elif high_priority > 0 or medium_priority > 3:
            return "预计可减少15-30%初始加载时间"
        else:
            return "预计可减少5-15%初始加载时间"


# 全局实例
code_splitting_optimizer = CodeSplittingOptimizer()
