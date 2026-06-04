"""
内容质量检测服务
提供文章内容的质量分析和改进建议
"""

import re
from typing import Dict, List, Any


class ContentQualityService:
    """
    内容质量检测服务
    
    功能:
    1. 语法检查
    2. 可读性分析
    3. 关键词密度分析
    4. 段落结构分析
    5. 语气风格检测
    6. 内容完整性检查
    """

    def __init__(self):
        # 常见语法错误模式
        self.common_errors = {
            'double_spaces': {
                'pattern': r'  +',
                'message': '发现多个连续空格',
                'severity': 'warning'
            },
            'missing_space_after_punctuation': {
                'pattern': r'[.,;!?][a-zA-Z]',
                'message': '标点后缺少空格',
                'severity': 'error'
            },
            'repeated_words': {
                'pattern': r'\b(\w+)\s+\1\b',
                'message': '重复的单词',
                'severity': 'warning'
            }
        }

    def analyze_content_quality(self, content: str, title: str = '', excerpt: str = '') -> Dict[str, Any]:
        """
        分析内容质量
        
        Args:
            content: 文章内容
            title: 文章标题
            excerpt: 文章摘要
            
        Returns:
            质量分析报告
        """
        issues = []
        suggestions = []
        score = 100

        # 1. 语法检查
        grammar_issues = self._check_grammar(content)
        issues.extend(grammar_issues)
        score -= len(grammar_issues) * 2

        # 2. 可读性分析
        readability = self._analyze_readability(content)
        if readability['score'] < 60:
            suggestions.append('简化句子结构，提高可读性')
            score -= 10

        # 3. 关键词密度分析
        keyword_density = self._analyze_keyword_density(content, title)
        if keyword_density['too_high']:
            suggestions.append('关键词密度过高，可能被判定为关键词堆砌')
            score -= 5
        elif keyword_density['too_low']:
            suggestions.append('关键词密度过低，建议增加关键词出现频率')
            score -= 5

        # 4. 段落结构分析
        structure_analysis = self._analyze_structure(content)
        if structure_analysis['paragraphs_too_long']:
            suggestions.append('部分段落过长，建议拆分为更小的段落')
            score -= 5
        if structure_analysis['no_headings'] and len(content) > 500:
            suggestions.append('长文章建议使用标题分隔不同部分')
            score -= 5

        # 5. 语气风格检测
        tone_analysis = self._analyze_tone(content)
        if tone_analysis['issues']:
            suggestions.extend(tone_analysis['suggestions'])
            score -= len(tone_analysis['issues']) * 3

        # 6. 内容完整性检查
        completeness = self._check_completeness(content, title, excerpt)
        if not completeness['has_introduction']:
            suggestions.append('文章缺少引言部分')
            score -= 5
        if not completeness['has_conclusion']:
            suggestions.append('文章缺少结论部分')
            score -= 5

        # 确保分数不低于0
        score = max(0, score)

        # 评级
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'score': score,
            'grade': grade,
            'issues': issues,
            'suggestions': suggestions,
            'readability': readability,
            'keyword_density': keyword_density,
            'structure': structure_analysis,
            'tone': tone_analysis,
            'completeness': completeness
        }

    def _check_grammar(self, content: str) -> List[Dict[str, Any]]:
        """检查语法错误"""
        issues = []

        for error_type, config in self.common_errors.items():
            matches = re.finditer(config['pattern'], content)
            for match in matches:
                issues.append({
                    'type': error_type,
                    'message': config['message'],
                    'position': match.start(),
                    'text': match.group(),
                    'severity': config['severity']
                })

        return issues

    def _analyze_readability(self, content: str) -> Dict[str, Any]:
        """分析可读性"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = content.split()
        total_words = len(words)
        total_sentences = len(sentences)

        if total_sentences == 0:
            return {
                'score': 0,
                'avg_sentence_length': 0,
                'total_words': total_words,
                'total_sentences': total_sentences,
                'level': 'unknown'
            }

        avg_sentence_length = total_words / total_sentences

        # 简化的可读性评分
        if avg_sentence_length < 15:
            score = 90
            level = 'easy'
        elif avg_sentence_length < 25:
            score = 75
            level = 'medium'
        elif avg_sentence_length < 35:
            score = 60
            level = 'hard'
        else:
            score = 40
            level = 'very_hard'

        return {
            'score': score,
            'avg_sentence_length': round(avg_sentence_length, 2),
            'total_words': total_words,
            'total_sentences': total_sentences,
            'level': level
        }

    def _analyze_keyword_density(self, content: str, title: str = '') -> Dict[str, Any]:
        """分析关键词密度"""
        # 提取关键词（从标题中）
        keywords = []
        if title:
            keywords = re.findall(r'\b\w+\b', title.lower())

        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        keywords = [k for k in keywords if k not in stop_words and len(k) > 2]

        content_lower = content.lower()
        total_words = len(content.split())

        density_results = {}
        too_high = False
        too_low = False

        for keyword in keywords:
            count = content_lower.count(keyword)
            density = (count / total_words * 100) if total_words > 0 else 0

            density_results[keyword] = {
                'count': count,
                'density': round(density, 2)
            }

            # 检查密度是否合理（1-3%为理想范围）
            if density > 5:
                too_high = True
            elif density < 0.5 and count == 0:
                too_low = True

        return {
            'keywords': density_results,
            'too_high': too_high,
            'too_low': too_low,
            'total_keywords': len(keywords)
        }

    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """分析文章结构"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # 检查是否有标题
        has_headings = bool(re.search(r'^#{1,6}\s+', content, re.MULTILINE))

        # 检查段落长度
        long_paragraphs = [p for p in paragraphs if len(p.split()) > 100]

        return {
            'total_paragraphs': len(paragraphs),
            'avg_paragraph_length': sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
            'paragraphs_too_long': len(long_paragraphs) > 0,
            'long_paragraph_count': len(long_paragraphs),
            'no_headings': not has_headings,
            'has_headings': has_headings
        }

    def _analyze_tone(self, content: str) -> Dict[str, Any]:
        """分析语气风格"""
        issues = []
        suggestions = []

        # 检测过度使用感叹号
        exclamation_count = content.count('!')
        if exclamation_count > 5:
            issues.append('excessive_exclamation')
            suggestions.append('减少感叹号的使用，保持专业语气')

        # 检测全部大写
        uppercase_words = re.findall(r'\b[A-Z]{3,}\b', content)
        if len(uppercase_words) > 3:
            issues.append('excessive_uppercase')
            suggestions.append('避免过多使用全大写字母')

        # 检测被动语态（简化版）
        passive_patterns = [r'\b(is|are|was|were)\s+\w+ed\b']
        passive_count = 0
        for pattern in passive_patterns:
            passive_count += len(re.findall(pattern, content, re.IGNORECASE))

        if passive_count > 5:
            issues.append('passive_voice')
            suggestions.append('尝试使用主动语态，使文章更有活力')

        return {
            'issues': issues,
            'suggestions': suggestions,
            'exclamation_count': exclamation_count,
            'uppercase_words': len(uppercase_words),
            'passive_voice_count': passive_count
        }

    def _check_completeness(self, content: str, title: str = '', excerpt: str = '') -> Dict[str, bool]:
        """检查内容完整性"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # 简单判断是否有引言和结论
        has_introduction = len(paragraphs) > 0
        has_conclusion = len(paragraphs) > 1

        # 检查是否有标题
        has_title = bool(title and len(title) > 0)

        # 检查是否有摘要
        has_excerpt = bool(excerpt and len(excerpt) > 0)

        return {
            'has_introduction': has_introduction,
            'has_conclusion': has_conclusion,
            'has_title': has_title,
            'has_excerpt': has_excerpt,
            'total_paragraphs': len(paragraphs)
        }


# 全局实例
content_quality_service = ContentQualityService()
