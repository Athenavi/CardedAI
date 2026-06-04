"""
AI 智能标签推荐服务

功能：
1. 基于文章内容自动推荐标签
2. 使用 TF-IDF 算法提取关键词
3. 支持自定义停用词
4. 标签去重和规范化
"""
import re
import math
from typing import List, Dict, Optional
from collections import Counter


class AITagRecommendationService:
    """
    AI 智能标签推荐服务
    
    使用 TF-IDF 算法从文章内容中提取关键词作为标签推荐
    """

    def __init__(self):
        # 中文停用词表（常用虚词、助词等）
        self.stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '他', '她', '它', '们', '那', '些', '什么', '怎么', '如何', '为什么',
            '因为', '所以', '但是', '如果', '虽然', '然后', '接着', '于是', '而且', '或者',
            '可以', '可能', '应该', '必须', '需要', '能够', '将会', '已经', '正在', '曾经',
            '这个', '那个', '这些', '那些', '这里', '那里', '哪里', '何时', '多少',
            '吗', '呢', '吧', '啊', '呀', '哦', '嗯', '哈', '嘿', '哇', '嘛',
            '与', '及', '等', '等等', '其', '此', '该', '各', '每', '某', '任何',
            '关于', '对于', '通过', '根据', '按照', '由于', '为了', '除了', '包括',
            '以及', '然而', '因此', '因而', '从而', '进而', '同时', '此外', '另外',
        ])

        # 英文停用词表
        self.english_stopwords = set([
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for', 'on', 'with',
            'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'out', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
            'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while', 'although',
            'though', 'after', 'before', 'this', 'that', 'these', 'those', 'i', 'me',
            'my', 'myself', 'we', 'our', 'ours', 'you', 'your', 'he', 'him', 'his',
            'she', 'her', 'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who',
        ])

    def recommend_tags(
            self,
            title: str,
            content: str,
            max_tags: int = 5,
            min_word_length: int = 2,
            existing_tags: Optional[List[str]] = None
    ) -> List[str]:
        """
        基于文章内容推荐标签
        
        Args:
            title: 文章标题
            content: 文章内容
            max_tags: 最大推荐标签数
            min_word_length: 最小词长度
            existing_tags: 已有标签（用于去重）
            
        Returns:
            推荐的标签列表
        """
        # 合并标题和内容
        text = f"{title} {content}"

        # 提取关键词
        keywords = self._extract_keywords(text, min_word_length)

        # 计算 TF-IDF 分数
        tagged_keywords = self._calculate_tfidf(keywords, text)

        # 排序并返回 top N
        sorted_keywords = sorted(tagged_keywords.items(), key=lambda x: x[1], reverse=True)

        # 过滤已有标签
        recommended = []
        for keyword, score in sorted_keywords:
            if existing_tags and keyword.lower() in [t.lower() for t in existing_tags]:
                continue
            recommended.append(keyword)
            if len(recommended) >= max_tags:
                break

        return recommended

    def _extract_keywords(self, text: str, min_word_length: int = 2) -> List[str]:
        """
        从文本中提取关键词（分词）
        
        简单实现：使用正则表达式分割中英文单词
        """
        # 提取中文词汇（连续的中文字符）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)

        # 提取英文单词
        english_words = re.findall(r'\b[a-zA-Z]{2,}\b', text)

        # 合并所有词汇
        all_words = chinese_words + english_words

        # 过滤停用词和短词
        filtered_words = []
        for word in all_words:
            word_lower = word.lower()

            # 检查是否是停用词
            if word in self.stopwords or word_lower in self.english_stopwords:
                continue

            # 检查长度
            if len(word) < min_word_length:
                continue

            filtered_words.append(word)

        return filtered_words

    def _calculate_tfidf(self, keywords: List[str], text: str) -> Dict[str, float]:
        """
        计算 TF-IDF 分数
        
        TF (Term Frequency) = 词频 / 总词数
        IDF (Inverse Document Frequency) = log(总文档数 / 包含该词的文档数)
        
        简化版：只计算 TF，因为只有一个文档
        """
        if not keywords:
            return {}

        # 计算词频
        word_counts = Counter(keywords)
        total_words = len(keywords)

        # 计算 TF 分数
        tf_scores = {}
        for word, count in word_counts.items():
            tf_scores[word] = count / total_words

        return tf_scores

    def extract_summary(
            self,
            content: str,
            max_length: int = 200,
            method: str = 'smart'
    ) -> str:
        """
        从内容中提取摘要
        
        Args:
            content: 文章内容
            max_length: 最大长度
            method: 提取方法 ('simple' 或 'smart')
            
        Returns:
            提取的摘要
        """
        if method == 'smart':
            return self._smart_extract_summary(content, max_length)
        else:
            return self._simple_extract_summary(content, max_length)

    def _simple_extract_summary(self, content: str, max_length: int = 200) -> str:
        """
        简单摘要提取：取第一段
        """
        # 按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if not paragraphs:
            return content[:max_length]

        # 取第一段
        summary = paragraphs[0]

        # 如果太长，截断
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(' ', 1)[0] + '...'

        return summary

    def _smart_extract_summary(self, content: str, max_length: int = 200) -> str:
        """
        智能摘要提取：基于句子重要性评分
        
        算法：
        1. 将文章分成句子
        2. 计算每个句子的关键词密度
        3. 选择最重要的前 N 个句子
        4. 按原文顺序组合
        """
        # 分割句子（支持中英文）
        sentences = re.split(r'[。！？.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        if not sentences:
            return content[:max_length]

        # 提取所有关键词
        all_keywords = self._extract_keywords(content, min_word_length=2)
        keyword_set = set(all_keywords)

        # 计算每个句子的重要性分数
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            # 关键词密度
            words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', sentence)
            if not words:
                continue

            keyword_count = sum(1 for word in words if word in keyword_set)
            density = keyword_count / len(words)

            # 位置权重（前面的句子更重要）
            position_weight = 1.0 / (i + 1)

            # 句子长度权重（适中长度的句子更好）
            length = len(sentence)
            if 20 <= length <= 100:
                length_weight = 1.0
            elif length < 20:
                length_weight = 0.5
            else:
                length_weight = 0.7

            # 综合分数
            score = density * 0.5 + position_weight * 0.3 + length_weight * 0.2
            sentence_scores.append((i, sentence, score))

        # 按分数排序，取前 3 个重要句子
        sentence_scores.sort(key=lambda x: x[2], reverse=True)
        top_sentences = sentence_scores[:3]

        # 按原文顺序重新排序
        top_sentences.sort(key=lambda x: x[0])

        # 组合摘要
        summary = '。'.join([s[1] for s in top_sentences]) + '。'

        # 如果太长，截断
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit('。', 1)[0] + '。...'

        return summary

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        简单的情感分析
        
        基于情感词典的简单实现
        """
        # 正面情感词
        positive_words = {
            '好', '棒', '优秀', '精彩', '完美', '喜欢', '爱', '赞', '强', '牛',
            'good', 'great', 'excellent', 'awesome', 'perfect', 'love', 'like', 'best',
        }

        # 负面情感词
        negative_words = {
            '差', '坏', '糟糕', '错误', '失败', '讨厌', '恨', '弱', '烂',
            'bad', 'poor', 'terrible', 'error', 'fail', 'hate', 'worst', 'wrong',
        }

        words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower()))

        positive_count = len(words.intersection(positive_words))
        negative_count = len(words.intersection(negative_words))
        total = positive_count + negative_count

        if total == 0:
            return {'positive': 0.5, 'negative': 0.5, 'neutral': 1.0}

        positive_score = positive_count / total
        negative_score = negative_count / total
        neutral_score = 1.0 - abs(positive_score - negative_score)

        return {
            'positive': round(positive_score, 2),
            'negative': round(negative_score, 2),
            'neutral': round(neutral_score, 2),
        }


# 全局实例
ai_tag_service = AITagRecommendationService()
