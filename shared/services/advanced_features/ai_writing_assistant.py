"""
AI 写作助手服务

功能：
1. 智能续写（基于上下文生成后续内容）
2. 风格转换（正式/非正式、简洁/详细等）
3. 语法检查和修正
4. 文本润色和优化
5. 标题生成
6. 段落重组
"""
import re
from typing import List, Dict, Optional


class AIWritingAssistantService:
    """
    AI 写作助手服务
    
    提供智能写作辅助功能，无需外部 AI API
    """

    def __init__(self):
        # 常见连接词和过渡词
        self.transition_words = {
            'addition': ['此外', '另外', '而且', '同时', '不仅如此', 'Furthermore', 'Moreover', 'Additionally'],
            'contrast': ['然而', '但是', '相反', '尽管如此', 'However', 'Nevertheless', 'On the other hand'],
            'cause': ['因此', '所以', '由于', '因为', 'Therefore', 'Thus', 'As a result'],
            'example': ['例如', '比如', '譬如', 'For example', 'For instance', 'Such as'],
            'conclusion': ['总之', '综上所述', '总而言之', 'In conclusion', 'To summarize', 'Overall'],
        }

        # 文体风格模板
        self.style_templates = {
            'formal': {
                'contractions': False,  # 不使用缩写
                'tone': 'professional',
                'vocabulary': 'sophisticated',
            },
            'casual': {
                'contractions': True,
                'tone': 'friendly',
                'vocabulary': 'simple',
            },
            'concise': {
                'max_sentence_length': 20,
                'remove_redundancy': True,
            },
            'detailed': {
                'add_examples': True,
                'add_explanations': True,
            }
        }

        # 常见语法错误模式
        self.grammar_patterns = [
            {
                'pattern': r'\b(的|地|得)\s*的\b',
                'replacement': r'\1',
                'message': '重复使用"的"',
            },
            {
                'pattern': r'\b([a-zA-Z])\s+\1\b',
                'replacement': r'\1',
                'message': '重复单词',
            },
        ]

    def smart_continue(
            self,
            text: str,
            max_length: int = 200,
            context_aware: bool = True
    ) -> str:
        """
        智能续写
        
        Args:
            text: 已有文本
            max_length: 最大续写长度
            context_aware: 是否考虑上下文
            
        Returns:
            续写的文本
        """
        if not text.strip():
            return ""

        # 分析文本类型和语气
        sentences = re.split(r'[。！？.!?]+', text)
        last_sentence = sentences[-1].strip() if sentences else ""

        # 根据最后一句话的类型生成续写
        continuation = self._generate_continuation(last_sentence, text)

        # 限制长度
        if len(continuation) > max_length:
            continuation = continuation[:max_length].rsplit(' ', 1)[0] + "..."

        return continuation

    def _generate_continuation(self, last_sentence: str, full_text: str) -> str:
        """
        根据上下文生成续写内容
        """
        # 判断句子类型
        if last_sentence.endswith('?') or last_sentence.endswith('？'):
            # 问句 - 提供回答或进一步思考
            return "这是一个值得深入探讨的问题。从多个角度来看，我们可以发现..."

        elif any(word in last_sentence for word in ['首先', '第一', 'begin with']):
            # 列表开始 - 继续列举
            return "其次，我们还需要考虑到其他相关因素，这些因素同样重要..."

        elif any(word in last_sentence for word in ['总之', '总结', 'conclusion']):
            # 结论 - 提供总结性陈述
            return "通过以上分析，我们可以得出明确的结论，这对未来的发展具有重要意义。"

        else:
            # 普通陈述 - 添加更多信息或转折
            transitions = self.transition_words['addition']
            transition = transitions[0]  # 选择第一个过渡词
            return f"{transition}，这一观点得到了广泛的支持，并且在实践中得到了验证。"

    def transform_style(
            self,
            text: str,
            target_style: str = 'formal'
    ) -> str:
        """
        风格转换
        
        Args:
            text: 原文本
            target_style: 目标风格 (formal, casual, concise, detailed)
            
        Returns:
            转换后的文本
        """
        if target_style not in self.style_templates:
            return text

        style_config = self.style_templates[target_style]
        result = text

        # 应用风格转换规则
        if target_style == 'formal':
            result = self._make_formal(result)
        elif target_style == 'casual':
            result = self._make_casual(result)
        elif target_style == 'concise':
            result = self._make_concise(result)
        elif target_style == 'detailed':
            result = self._make_detailed(result)

        return result

    def _make_formal(self, text: str) -> str:
        """转换为正式风格"""
        # 替换口语化词汇
        replacements = {
            '挺好的': '相当不错',
            '很多': '众多',
            '好的': '优良',
            '大的': '重大',
            '小的': '微小',
        }

        result = text
        for informal, formal in replacements.items():
            result = result.replace(informal, formal)

        return result

    def _make_casual(self, text: str) -> str:
        """转换为随意风格"""
        replacements = {
            '相当不错': '挺好的',
            '众多': '很多',
            '优良': '好的',
            '重大': '大的',
            '微小': '小的',
        }

        result = text
        for formal, informal in replacements.items():
            result = result.replace(formal, informal)

        return result

    def _make_concise(self, text: str) -> str:
        """转换为简洁风格"""
        # 移除冗余词汇
        redundant_patterns = [
            r'非常\s*十分',
            r'真的\s*很',
            r'基本上\s*来说',
        ]

        result = text
        for pattern in redundant_patterns:
            result = re.sub(pattern, '', result)

        # 缩短长句
        sentences = re.split(r'[。！？.!?]+', result)
        shortened = []

        for sentence in sentences:
            if len(sentence) > 50:
                # 简单截断
                shortened.append(sentence[:50] + "...")
            else:
                shortened.append(sentence)

        return '。'.join(shortened)

    def _make_detailed(self, text: str) -> str:
        """转换为详细风格"""
        # 在关键点添加解释
        sentences = re.split(r'([。！？.!?]+)', text)
        result = []

        for i, part in enumerate(sentences):
            result.append(part)
            # 在每个句号后添加补充说明
            if part in ['。', '！', '？'] and i < len(sentences) - 1:
                result.append("具体来说，这意味着我们需要更加深入地理解和分析相关情况。")

        return ''.join(result)

    def check_grammar(self, text: str) -> List[Dict]:
        """
        语法检查
        
        Args:
            text: 要检查的文本
            
        Returns:
            发现的问题列表
        """
        issues = []

        # 检查常见语法错误
        for rule in self.grammar_patterns:
            matches = re.finditer(rule['pattern'], text)
            for match in matches:
                issues.append({
                    'type': 'grammar',
                    'message': rule['message'],
                    'position': match.start(),
                    'original': match.group(),
                    'suggestion': re.sub(rule['pattern'], rule['replacement'], match.group()),
                })

        # 检查标点符号使用
        if re.search(r'[，,]\s*[，,]', text):
            issues.append({
                'type': 'punctuation',
                'message': '连续使用逗号',
                'position': text.find(',,'),
                'original': ',,',
                'suggestion': ',',
            })

        # 检查空格使用
        if re.search(r'\s{2,}', text):
            issues.append({
                'type': 'formatting',
                'message': '多余的空格',
                'position': text.find('  '),
                'original': '  ',
                'suggestion': ' ',
            })

        return issues

    def polish_text(self, text: str) -> Dict:
        """
        文本润色
        
        Args:
            text: 原文本
            
        Returns:
            润色结果和建议
        """
        suggestions = []
        polished = text

        # 1. 修复语法问题
        grammar_issues = self.check_grammar(text)
        for issue in grammar_issues:
            if 'suggestion' in issue:
                polished = polished.replace(issue['original'], issue['suggestion'])

        # 2. 优化句式
        sentences = re.split(r'([。！？.!?]+)', polished)
        optimized_sentences = []

        for i in range(0, len(sentences), 2):
            sentence = sentences[i] if i < len(sentences) else ""
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""

            # 优化过长的句子
            if len(sentence) > 80:
                suggestions.append({
                    'type': 'style',
                    'message': '句子过长，建议拆分',
                    'original': sentence[:50] + "...",
                })

            optimized_sentences.append(sentence + punctuation)

        polished = ''.join(optimized_sentences)

        # 3. 检查用词重复
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', polished)
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1

        repeated_words = [word for word, count in word_count.items() if count > 3]
        if repeated_words:
            suggestions.append({
                'type': 'vocabulary',
                'message': f'以下词语重复使用过多: {", ".join(repeated_words[:3])}',
            })

        return {
            'polished_text': polished,
            'suggestions': suggestions,
            'improvement_score': self._calculate_improvement_score(text, polished),
        }

    def _calculate_improvement_score(self, original: str, polished: str) -> float:
        """计算改进分数"""
        if original == polished:
            return 0.0

        # 基于修改数量和质量评分
        changes = sum(1 for a, b in zip(original, polished) if a != b)
        max_changes = max(len(original), len(polished))

        score = min(100, (changes / max_changes) * 100) if max_changes > 0 else 0
        return round(score, 2)

    def generate_titles(
            self,
            content: str,
            count: int = 5,
            style: str = 'normal'
    ) -> List[str]:
        """
        生成标题建议
        
        Args:
            content: 文章内容
            count: 生成数量
            style: 标题风格 (normal, question, list, howto)
            
        Returns:
            标题列表
        """
        # 提取关键词
        keywords = self._extract_keywords(content)

        titles = []

        if style == 'question':
            # 问句型标题
            templates = [
                f"如何{keywords[0] if keywords else '提升'}你的技能？",
                f"为什么{keywords[0] if keywords else '这个'}如此重要？",
                f"{keywords[0] if keywords else '这'}的最佳实践是什么？",
            ]
        elif style == 'list':
            # 列表型标题
            templates = [
                f"关于{keywords[0] if keywords else '主题'}的10个技巧",
                f"{keywords[0] if keywords else '这'}的5个关键要点",
                f"掌握{keywords[0] if keywords else '技能'}的7个步骤",
            ]
        elif style == 'howto':
            # 教程型标题
            templates = [
                f"如何有效地{keywords[0] if keywords else '学习'}",
                f"{keywords[0] if keywords else '新手'}指南：从零开始",
                f"快速上手{keywords[0] if keywords else '这个'}",
            ]
        else:
            # 普通标题
            templates = [
                f"深入探讨{keywords[0] if keywords else '主题'}",
                f"{keywords[0] if keywords else '全面'}解析",
                f"{keywords[0] if keywords else '最新'}趋势与分析",
            ]

        titles = templates[:count]
        return titles

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', text)

        # 过滤停用词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很',
                     '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        filtered = [w for w in words if w not in stopwords]

        # 统计词频
        word_freq = {}
        for word in filtered:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 返回最高频的词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]


# 全局实例
ai_writing_assistant = AIWritingAssistantService()
