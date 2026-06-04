"""
内部链接建议服务
分析文章内容,推荐相关内部链接
类似WordPress Link Whisper插件
"""
import re
from collections import Counter
from typing import Dict, Any, List, Optional


class InternalLinkService:
    """内部链接建议服务"""
    
    def __init__(self):
        self.min_keyword_length = 2  # 最小关键词长度
        self.max_suggestions = 10  # 最大建议数
    
    def extract_keywords(self, content: str, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        从文章内容提取关键词
        
        Args:
            content: 文章内容
            top_n: 返回前N个关键词
            
        Returns:
            关键词列表(包含词频)
        """
        if not content:
            return []
        
        # 清理HTML标签
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # 分词(简化版:按非字母数字字符分割)
        # 实际应使用jieba等中文分词工具
        words = re.findall(r'[\w\u4e00-\u9fff]{2,}', clean_content)
        
        # 过滤停用词(简化版)
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        filtered_words = [w for w in words if w not in stop_words and len(w) >= self.min_keyword_length]
        
        # 统计词频
        word_counts = Counter(filtered_words)
        
        # 返回Top N关键词
        keywords = [
            {'keyword': word, 'count': count}
            for word, count in word_counts.most_common(top_n)
        ]
        
        return keywords
    
    def find_related_articles(self, keywords: List[str], all_articles: List[Dict[str, Any]], 
                             exclude_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        根据关键词查找相关文章
        
        Args:
            keywords: 关键词列表
            all_articles: 所有文章列表
            exclude_id: 排除的文章ID
            
        Returns:
            相关文章列表(按相关度排序)
        """
        if not keywords or not all_articles:
            return []
        
        scored_articles = []
        
        for article in all_articles:
            if exclude_id and article.get('id') == exclude_id:
                continue
            
            score = 0
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()
            
            # 计算匹配得分
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # 标题中匹配权重更高
                title_matches = title.count(keyword_lower)
                content_matches = content.count(keyword_lower)
                
                score += title_matches * 3 + content_matches
            
            if score > 0:
                scored_articles.append({
                    'article': article,
                    'score': score,
                    'matched_keywords': [
                        kw for kw in keywords 
                        if kw.lower() in title or kw.lower() in content
                    ],
                })
        
        # 按得分降序排序
        scored_articles.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回前N个
        return scored_articles[:self.max_suggestions]
    
    def suggest_internal_links(self, current_article: Dict[str, Any], 
                              all_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        为当前文章推荐内部链接
        
        Args:
            current_article: 当前文章
            all_articles: 所有文章列表
            
        Returns:
            建议结果
        """
        # 提取关键词
        content = current_article.get('content', '')
        keywords = self.extract_keywords(content)
        
        if not keywords:
            return {
                'success': True,
                'keywords': [],
                'suggestions': [],
                'link_density': 0,
            }
        
        # 查找相关文章
        keyword_texts = [kw['keyword'] for kw in keywords[:10]]  # 使用前10个关键词
        related = self.find_related_articles(
            keyword_texts, 
            all_articles, 
            exclude_id=current_article.get('id')
        )
        
        # 计算链接密度
        link_count = content.count('<a ')
        word_count = len(re.findall(r'[\w\u4e00-\u9fff]+', content))
        link_density = (link_count / word_count * 100) if word_count > 0 else 0
        
        return {
            'success': True,
            'keywords': keywords[:10],
            'suggestions': [
                {
                    'id': item['article'].get('id'),
                    'title': item['article'].get('title'),
                    'slug': item['article'].get('slug'),
                    'score': item['score'],
                    'matched_keywords': item['matched_keywords'][:3],
                }
                for item in related
            ],
            'link_density': round(link_density, 2),
            'total_articles': len(all_articles),
        }
    
    def detect_orphan_articles(self, all_articles: List[Dict[str, Any]], 
                              all_links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检测孤立文章(没有被其他文章链接的文章)
        
        Args:
            all_articles: 所有文章列表
            all_links: 所有内部链接记录
            
        Returns:
            孤立文章列表
        """
        # 获取被链接的文章ID集合
        linked_ids = set()
        for link in all_links:
            target_id = link.get('target_article_id')
            if target_id:
                linked_ids.add(target_id)
        
        # 找出未被链接的文章
        orphan_articles = [
            article for article in all_articles
            if article.get('id') not in linked_ids
        ]
        
        return orphan_articles
    
    def analyze_link_distribution(self, all_articles: List[Dict[str, Any]], 
                                 all_links: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析内链分布
        
        Args:
            all_articles: 所有文章列表
            all_links: 所有内部链接记录
            
        Returns:
            分布统计
        """
        # 每篇文章的出站链接数
        outbound_counts = Counter()
        for link in all_links:
            source_id = link.get('source_article_id')
            if source_id:
                outbound_counts[source_id] += 1
        
        # 每篇文章的入站链接数
        inbound_counts = Counter()
        for link in all_links:
            target_id = link.get('target_article_id')
            if target_id:
                inbound_counts[target_id] += 1
        
        # 统计
        articles_with_outbound = sum(1 for count in outbound_counts.values() if count > 0)
        articles_with_inbound = sum(1 for count in inbound_counts.values() if count > 0)
        
        return {
            'total_articles': len(all_articles),
            'articles_with_outbound_links': articles_with_outbound,
            'articles_with_inbound_links': articles_with_inbound,
            'orphan_articles': len(all_articles) - articles_with_inbound,
            'avg_outbound_per_article': round(sum(outbound_counts.values()) / len(all_articles), 2) if all_articles else 0,
            'avg_inbound_per_article': round(sum(inbound_counts.values()) / len(all_articles), 2) if all_articles else 0,
        }


# 单例实例
internal_link_service = InternalLinkService()
