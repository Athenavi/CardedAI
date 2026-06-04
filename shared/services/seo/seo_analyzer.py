"""
统一SEO管理服务

提供集中式SEO仪表板、实时评分、关键词分析等功能
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class SEOAnalyzer:
    """
    SEO分析服务
    
    分析和评估内容的SEO质量
    """

    def __init__(self):
        """初始化SEO分析器"""
        # SEO评分权重
        self.weights = {
            'title_length': 0.15,
            'description_quality': 0.15,
            'keyword_density': 0.2,
            'readability': 0.15,
            'content_length': 0.15,
            'headings_structure': 0.1,
            'internal_links': 0.05,
            'image_alt': 0.05,
        }

    def analyze_seo(
            self,
            title: str,
            description: str,
            content: str,
            keywords: Optional[List[str]] = None,
            headings: Optional[Dict[str, List[str]]] = None,
            images: Optional[List[Dict[str, str]]] = None,
            internal_links: int = 0
    ) -> Dict[str, Any]:
        """
        全面分析SEO
        
        Args:
            title: 页面标题
            description: 页面描述
            content: 页面内容
            keywords: 目标关键词列表
            headings: 标题结构 {h1: [], h2: [], h3: []}
            images: 图片列表 [{src, alt}]
            internal_links: 内部链接数量
        
        Returns:
            SEO分析报告
        """
        # 计算各项得分
        title_score = self._analyze_title(title)
        description_score = self._analyze_description(description)
        keyword_score = self._analyze_keywords(content, keywords or [])
        readability_score = self._analyze_readability(content)
        content_length_score = self._analyze_content_length(content)
        headings_score = self._analyze_headings(headings or {})
        links_score = self._analyze_links(internal_links)
        images_score = self._analyze_images(images or [])

        # 计算总分
        total_score = (
                title_score['score'] * self.weights['title_length'] +
                description_score['score'] * self.weights['description_quality'] +
                keyword_score['score'] * self.weights['keyword_density'] +
                readability_score['score'] * self.weights['readability'] +
                content_length_score['score'] * self.weights['content_length'] +
                headings_score['score'] * self.weights['headings_structure'] +
                links_score['score'] * self.weights['internal_links'] +
                images_score['score'] * self.weights['image_alt']
        )

        # 生成建议
        suggestions = []
        suggestions.extend(title_score.get('suggestions', []))
        suggestions.extend(description_score.get('suggestions', []))
        suggestions.extend(keyword_score.get('suggestions', []))
        suggestions.extend(readability_score.get('suggestions', []))
        suggestions.extend(content_length_score.get('suggestions', []))
        suggestions.extend(headings_score.get('suggestions', []))
        suggestions.extend(links_score.get('suggestions', []))
        suggestions.extend(images_score.get('suggestions', []))

        return {
            'overall_score': round(total_score * 100, 2),
            'grade': self._get_grade(total_score),
            'metrics': {
                'title': title_score,
                'description': description_score,
                'keywords': keyword_score,
                'readability': readability_score,
                'content_length': content_length_score,
                'headings': headings_score,
                'links': links_score,
                'images': images_score,
            },
            'suggestions': suggestions,
            'analyzed_at': datetime.now().isoformat(),
        }

    def _analyze_title(self, title: str) -> Dict[str, Any]:
        """分析标题"""
        length = len(title)

        # 最佳长度：50-60字符
        if 50 <= length <= 60:
            score = 1.0
            status = 'good'
        elif 40 <= length < 50 or 60 < length <= 70:
            score = 0.7
            status = 'warning'
        else:
            score = 0.3
            status = 'poor'

        suggestions = []
        if length < 40:
            suggestions.append('标题太短，建议增加到50-60个字符')
        elif length > 70:
            suggestions.append('标题太长，可能被搜索引擎截断，建议缩短到60个字符以内')

        return {
            'score': score,
            'status': status,
            'length': length,
            'optimal_range': '50-60',
            'suggestions': suggestions,
        }

    def _analyze_description(self, description: str) -> Dict[str, Any]:
        """分析描述"""
        length = len(description)

        # 最佳长度：150-160字符
        if 150 <= length <= 160:
            score = 1.0
            status = 'good'
        elif 120 <= length < 150 or 160 < length <= 180:
            score = 0.7
            status = 'warning'
        else:
            score = 0.3
            status = 'poor'

        suggestions = []
        if length < 120:
            suggestions.append('描述太短，建议增加到150-160个字符')
        elif length > 180:
            suggestions.append('描述太长，可能被搜索引擎截断，建议缩短到160个字符以内')

        return {
            'score': score,
            'status': status,
            'length': length,
            'optimal_range': '150-160',
            'suggestions': suggestions,
        }

    def _analyze_keywords(self, content: str, keywords: List[str]) -> Dict[str, Any]:
        """分析关键词密度"""
        if not keywords or not content:
            return {
                'score': 0.5,
                'status': 'warning',
                'density': 0,
                'suggestions': ['请添加目标关键词'],
            }

        content_lower = content.lower()
        word_count = len(content_lower.split())

        keyword_results = []
        total_density = 0

        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = content_lower.count(keyword_lower)
            density = (count / word_count * 100) if word_count > 0 else 0

            # 理想密度：1-3%
            if 1 <= density <= 3:
                score = 1.0
                status = 'good'
            elif 0.5 <= density < 1 or 3 < density <= 4:
                score = 0.7
                status = 'warning'
            else:
                score = 0.3
                status = 'poor'

            keyword_results.append({
                'keyword': keyword,
                'count': count,
                'density': round(density, 2),
                'score': score,
                'status': status,
            })

            total_density += density

        avg_density = total_density / len(keywords) if keywords else 0
        avg_score = sum(k['score'] for k in keyword_results) / len(keyword_results)

        suggestions = []
        if avg_density < 0.5:
            suggestions.append('关键词密度太低，建议在内容中更多地使用目标关键词')
        elif avg_density > 4:
            suggestions.append('关键词密度太高，可能被判定为关键词堆砌，建议降低密度')

        return {
            'score': avg_score,
            'status': 'good' if avg_score >= 0.7 else ('warning' if avg_score >= 0.5 else 'poor'),
            'average_density': round(avg_density, 2),
            'keywords': keyword_results,
            'suggestions': suggestions,
        }

    def _analyze_readability(self, content: str) -> Dict[str, Any]:
        """分析可读性"""
        if not content:
            return {
                'score': 0,
                'status': 'poor',
                'suggestions': ['内容为空'],
            }

        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = content.split()
        word_count = len(words)
        sentence_count = len(sentences)

        if sentence_count == 0:
            return {
                'score': 0,
                'status': 'poor',
                'suggestions': ['无法分析可读性'],
            }

        # 平均句长
        avg_sentence_length = word_count / sentence_count

        # Flesch Reading Ease简化版
        # 分数越高越易读
        if avg_sentence_length < 15:
            score = 1.0
            status = 'good'
            level = '容易阅读'
        elif avg_sentence_length < 20:
            score = 0.7
            status = 'warning'
            level = '中等难度'
        else:
            score = 0.4
            status = 'poor'
            level = '较难阅读'

        suggestions = []
        if avg_sentence_length > 20:
            suggestions.append('句子平均长度过长，建议使用更短的句子提高可读性')

        return {
            'score': score,
            'status': status,
            'avg_sentence_length': round(avg_sentence_length, 2),
            'reading_level': level,
            'sentence_count': sentence_count,
            'word_count': word_count,
            'suggestions': suggestions,
        }

    def _analyze_content_length(self, content: str) -> Dict[str, Any]:
        """分析内容长度"""
        word_count = len(content.split())

        # 最佳长度：1500-2500词
        if 1500 <= word_count <= 2500:
            score = 1.0
            status = 'good'
        elif 1000 <= word_count < 1500 or 2500 < word_count <= 3000:
            score = 0.7
            status = 'warning'
        elif 500 <= word_count < 1000:
            score = 0.5
            status = 'warning'
        else:
            score = 0.3
            status = 'poor'

        suggestions = []
        if word_count < 1000:
            suggestions.append('内容较短，建议增加到1500词以上以获得更好的SEO效果')
        elif word_count > 3000:
            suggestions.append('内容很长，考虑拆分为多个相关主题的文章')

        return {
            'score': score,
            'status': status,
            'word_count': word_count,
            'optimal_range': '1500-2500',
            'suggestions': suggestions,
        }

    def _analyze_headings(self, headings: Dict[str, List[str]]) -> Dict[str, Any]:
        """分析标题结构"""
        h1_count = len(headings.get('h1', []))
        h2_count = len(headings.get('h2', []))
        h3_count = len(headings.get('h3', []))

        score = 1.0
        suggestions = []

        # H1应该有且只有一个
        if h1_count == 0:
            score -= 0.3
            suggestions.append('缺少H1标题，请添加一个主标题')
        elif h1_count > 1:
            score -= 0.2
            suggestions.append('有多个H1标题，建议只保留一个')

        # H2应该至少有2个
        if h2_count < 2:
            score -= 0.2
            suggestions.append('H2标题太少，建议至少添加2个子标题来组织内容')

        # 总体结构
        total_headings = h1_count + h2_count + h3_count
        if total_headings < 3:
            score -= 0.2
            suggestions.append('标题总数太少，建议添加更多标题来改善内容结构')

        score = max(0, score)

        return {
            'score': score,
            'status': 'good' if score >= 0.7 else ('warning' if score >= 0.5 else 'poor'),
            'h1_count': h1_count,
            'h2_count': h2_count,
            'h3_count': h3_count,
            'total': total_headings,
            'suggestions': suggestions,
        }

    def _analyze_links(self, internal_links: int) -> Dict[str, Any]:
        """分析内部链接"""
        # 理想的内部链接数：3-10个
        if 3 <= internal_links <= 10:
            score = 1.0
            status = 'good'
        elif 1 <= internal_links < 3 or 10 < internal_links <= 15:
            score = 0.7
            status = 'warning'
        else:
            score = 0.4
            status = 'poor'

        suggestions = []
        if internal_links < 3:
            suggestions.append('内部链接太少，建议添加3-5个相关链接来提高页面关联性')
        elif internal_links > 15:
            suggestions.append('内部链接太多，可能分散页面权重，建议减少到10个以内')

        return {
            'score': score,
            'status': status,
            'count': internal_links,
            'optimal_range': '3-10',
            'suggestions': suggestions,
        }

    def _analyze_images(self, images: List[Dict[str, str]]) -> Dict[str, Any]:
        """分析图片ALT文本"""
        if not images:
            return {
                'score': 0.5,
                'status': 'warning',
                'total': 0,
                'with_alt': 0,
                'suggestions': ['建议添加相关图片以增强内容'],
            }

        with_alt = sum(1 for img in images if img.get('alt'))
        ratio = with_alt / len(images)

        if ratio >= 0.9:
            score = 1.0
            status = 'good'
        elif ratio >= 0.5:
            score = 0.6
            status = 'warning'
        else:
            score = 0.3
            status = 'poor'

        suggestions = []
        if ratio < 1.0:
            missing = len(images) - with_alt
            suggestions.append(f'{missing}张图片缺少ALT文本，建议为所有图片添加描述性ALT文本')

        return {
            'score': score,
            'status': status,
            'total': len(images),
            'with_alt': with_alt,
            'ratio': round(ratio, 2),
            'suggestions': suggestions,
        }

    def _get_grade(self, score: float) -> str:
        """获取等级"""
        if score >= 0.9:
            return 'A+'
        elif score >= 0.8:
            return 'A'
        elif score >= 0.7:
            return 'B'
        elif score >= 0.6:
            return 'C'
        elif score >= 0.5:
            return 'D'
        else:
            return 'F'


# 全局实例
seo_analyzer = SEOAnalyzer()

# 导出
__all__ = ['SEOAnalyzer', 'seo_analyzer']
