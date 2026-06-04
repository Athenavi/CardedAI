"""
内容审核服务

功能：
1. 敏感词检测
2. 垃圾内容识别
3. 广告检测
4. 链接密度分析
5. 重复内容检测
"""
import re
from typing import List, Dict, Optional, Tuple


class ContentModerationService:
    """
    内容审核服务
    
    提供敏感词检测、垃圾内容识别等功能
    """

    def __init__(self):
        # 敏感词库（示例，实际应该从数据库或配置文件加载）
        self.sensitive_words = {
            # 政治敏感
            '暴力', '恐怖', '分裂', '反动',
            # 色情低俗
            '色情', '淫秽', '裸露', '性爱',
            # 违法内容
            '赌博', '毒品', '诈骗', '洗钱',
            # 辱骂攻击
            '傻逼', '操你', '他妈', '滚蛋',
            # 广告营销
            '加微信', '加QQ', '联系电话', '微信号',
        }

        # 垃圾内容特征
        self.spam_indicators = {
            'exclamation_marks': 5,  # 感叹号超过5个
            'question_marks': 5,  # 问号超过5个
            'caps_ratio': 0.5,  # 大写字母比例超过50%
            'link_density': 0.3,  # 链接密度超过30%
            'repetition_ratio': 0.4,  # 重复内容比例超过40%
        }

    def moderate_content(
            self,
            content: str,
            title: Optional[str] = None,
            check_type: str = 'all'
    ) -> Dict:
        """
        综合内容审核
        
        Args:
            content: 文章内容
            title: 文章标题（可选）
            check_type: 检查类型 ('sensitive', 'spam', 'ads', 'all')
            
        Returns:
            审核结果
        """
        result = {
            'is_safe': True,
            'issues': [],
            'score': 100,  # 安全分数，100为完全安全
        }

        if check_type in ['sensitive', 'all']:
            sensitive_result = self.check_sensitive_words(content)
            if not sensitive_result['is_clean']:
                result['is_safe'] = False
                result['issues'].extend(sensitive_result['issues'])
                result['score'] -= sensitive_result['penalty']

        if check_type in ['spam', 'all']:
            spam_result = self.detect_spam(content)
            if spam_result['is_spam']:
                result['is_safe'] = False
                result['issues'].extend(spam_result['issues'])
                result['score'] -= spam_result['penalty']

        if check_type in ['ads', 'all']:
            ads_result = self.detect_ads(content)
            if ads_result['has_ads']:
                result['issues'].extend(ads_result['issues'])
                result['score'] -= ads_result['penalty']

        # 确保分数不低于0
        result['score'] = max(0, result['score'])

        return result

    def check_sensitive_words(self, text: str) -> Dict:
        """
        检测敏感词
        
        Args:
            text: 要检查的文本
            
        Returns:
            检测结果
        """
        issues = []
        found_words = []

        for word in self.sensitive_words:
            if word in text:
                found_words.append(word)

        if found_words:
            issues.append({
                'type': 'sensitive_word',
                'message': f'检测到敏感词: {", ".join(found_words)}',
                'words': found_words,
            })

        # 计算惩罚分数（每个敏感词扣10分）
        penalty = len(found_words) * 10

        return {
            'is_clean': len(found_words) == 0,
            'issues': issues,
            'found_words': found_words,
            'penalty': min(penalty, 50),  # 最多扣50分
        }

    def detect_spam(self, text: str) -> Dict:
        """
        检测垃圾内容
        
        Args:
            text: 要检查的文本
            
        Returns:
            检测结果
        """
        issues = []
        spam_score = 0

        # 1. 检查过多标点符号
        exclamation_count = text.count('!') + text.count('！')
        if exclamation_count > self.spam_indicators['exclamation_marks']:
            issues.append({
                'type': 'excessive_punctuation',
                'message': f'过多的感叹号 ({exclamation_count}个)',
            })
            spam_score += 15

        question_count = text.count('?') + text.count('？')
        if question_count > self.spam_indicators['question_marks']:
            issues.append({
                'type': 'excessive_punctuation',
                'message': f'过多的问号 ({question_count}个)',
            })
            spam_score += 15

        # 2. 检查大写字母比例（英文）
        if re.search(r'[a-zA-Z]', text):
            upper_count = sum(1 for c in text if c.isupper())
            alpha_count = sum(1 for c in text if c.isalpha())
            if alpha_count > 0:
                caps_ratio = upper_count / alpha_count
                if caps_ratio > self.spam_indicators['caps_ratio']:
                    issues.append({
                        'type': 'excessive_caps',
                        'message': f'大写字母比例过高 ({caps_ratio:.0%})',
                    })
                    spam_score += 20

        # 3. 检查重复内容
        repetition_ratio = self._calculate_repetition(text)
        if repetition_ratio > self.spam_indicators['repetition_ratio']:
            issues.append({
                'type': 'repetitive_content',
                'message': f'重复内容比例过高 ({repetition_ratio:.0%})',
            })
            spam_score += 25

        # 4. 检查过短内容
        if len(text.strip()) < 10:
            issues.append({
                'type': 'too_short',
                'message': '内容过短',
            })
            spam_score += 30

        is_spam = spam_score >= 50

        return {
            'is_spam': is_spam,
            'issues': issues,
            'spam_score': spam_score,
            'penalty': min(spam_score, 50),
        }

    def detect_ads(self, text: str) -> Dict:
        """
        检测广告内容
        
        Args:
            text: 要检查的文本
            
        Returns:
            检测结果
        """
        issues = []
        ad_score = 0

        # 1. 检测联系方式
        contact_patterns = [
            r'微信[号\s]*[:：]?\s*\w+',
            r'QQ[号\s]*[:：]?\s*\d+',
            r'电话[号码\s]*[:：]?\s*[\d\-]+',
            r'手机[号码\s]*[:：]?\s*[\d\-]+',
            r'邮箱[地址\s]*[:：]?\s*[\w\.-]+@[\w\.-]+',
        ]

        for pattern in contact_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                issues.append({
                    'type': 'contact_info',
                    'message': f'检测到联系方式: {matches[0][:20]}...',
                })
                ad_score += 30
                break

        # 2. 检测链接密度
        link_density = self._calculate_link_density(text)
        if link_density > self.spam_indicators['link_density']:
            issues.append({
                'type': 'high_link_density',
                'message': f'链接密度过高 ({link_density:.0%})',
            })
            ad_score += 25

        # 3. 检测营销词汇
        marketing_words = [
            '优惠', '打折', '促销', '限时', '特价', '免费',
            '赚钱', '投资', '收益', '回报', '暴利',
            'discount', 'sale', 'offer', 'free', 'deal',
        ]

        found_marketing = [word for word in marketing_words if word in text.lower()]
        if len(found_marketing) >= 3:
            issues.append({
                'type': 'marketing_language',
                'message': f'检测到营销词汇: {", ".join(found_marketing[:3])}',
            })
            ad_score += 20

        has_ads = ad_score >= 40

        return {
            'has_ads': has_ads,
            'issues': issues,
            'ad_score': ad_score,
            'penalty': min(ad_score, 40),
        }

    def _calculate_repetition(self, text: str) -> float:
        """
        计算重复内容比例
        """
        # 将文本分成句子
        sentences = re.split(r'[。！？.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        if len(sentences) < 2:
            return 0.0

        # 计算重复的句子
        unique_sentences = set(sentences)
        repetition_ratio = 1.0 - (len(unique_sentences) / len(sentences))

        return repetition_ratio

    def _calculate_link_density(self, text: str) -> float:
        """
        计算链接密度
        """
        # 检测 URL
        urls = re.findall(r'https?://\S+|www\.\S+', text)

        if not urls:
            return 0.0

        # 计算链接字符占总字符的比例
        total_link_length = sum(len(url) for url in urls)
        total_length = len(text)

        if total_length == 0:
            return 0.0

        return total_link_length / total_length

    def batch_moderate(
            self,
            items: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        批量审核内容
        
        Args:
            items: 内容列表，每项包含 'title' 和 'content'
            
        Returns:
            审核结果列表
        """
        results = []

        for item in items:
            result = self.moderate_content(
                content=item.get('content', ''),
                title=item.get('title', '')
            )
            result['title'] = item.get('title', '')
            results.append(result)

        return results


# 全局实例
content_moderation_service = ContentModerationService()
