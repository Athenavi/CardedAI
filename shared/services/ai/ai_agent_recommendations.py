"""
AI Agent 智能推荐服务
提供自动标签推荐、SEO 优化建议、相关文章推荐等功能
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.unified_logger import default_logger as logger


class AIAgentRecommendations:
    """
    P11-1: AI Agent 自主决策服务
    
    功能：
    1. 基于文章内容的自动标签推荐
    2. SEO 优化建议主动提示
    3. 相关文章智能推荐
    """

    def __init__(self):
        self.recommendation_cache = {}
        self.cache_ttl = 3600  # 1小时缓存

    async def recommend_tags(
            self,
            title: str,
            content: str,
            existing_tags: List[str] = None,
            max_tags: int = 5
    ) -> Dict[str, Any]:
        """
        P11-1: 基于文章内容自动推荐标签
        
        Args:
            title: 文章标题
            content: 文章内容
            existing_tags: 已有标签列表
            max_tags: 最大推荐数量
            
        Returns:
            推荐的标签列表及置信度
        """
        try:
            # 简单关键词提取（实际项目中应使用 NLP 模型或调用 LLM API）
            text = f"{title} {content}".lower()

            # 常见技术标签关键词映射
            tag_keywords = {
                'python': ['python', 'django', 'flask', 'fastapi'],
                'javascript': ['javascript', 'js', 'react', 'vue', 'node.js'],
                'web-development': ['web', 'html', 'css', 'frontend', 'backend'],
                'database': ['sql', 'postgresql', 'mysql', 'mongodb', 'redis'],
                'devops': ['docker', 'kubernetes', 'ci/cd', 'deployment', 'linux'],
                'ai-ml': ['ai', 'machine learning', 'deep learning', 'neural network', 'nlp'],
                'security': ['security', 'authentication', 'encryption', 'oauth', 'jwt'],
                'performance': ['performance', 'optimization', 'caching', 'cdn', 'lazy loading'],
                'mobile': ['mobile', 'ios', 'android', 'react native', 'flutter'],
                'cloud': ['cloud', 'aws', 'azure', 'gcp', 'serverless'],
            }

            recommended_tags = []

            for tag, keywords in tag_keywords.items():
                # 跳过已有标签
                if existing_tags and tag in existing_tags:
                    continue

                # 计算匹配度
                match_count = sum(1 for keyword in keywords if keyword in text)

                if match_count > 0:
                    confidence = min(match_count / len(keywords), 1.0)

                    if confidence >= 0.3:  # 至少 30% 置信度
                        recommended_tags.append({
                            "tag": tag,
                            "confidence": round(confidence, 2),
                            "matched_keywords": [kw for kw in keywords if kw in text]
                        })

            # 按置信度排序
            recommended_tags.sort(key=lambda x: x['confidence'], reverse=True)

            # 限制返回数量
            recommended_tags = recommended_tags[:max_tags]

            return {
                "success": True,
                "recommended_tags": recommended_tags,
                "total_found": len(recommended_tags),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "note": "这些标签是基于文章内容自动生成的建议，您可以根据需要调整。"
            }

        except Exception as e:
            logger.error(f"Tag recommendation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommended_tags": []
            }

    async def suggest_seo_optimizations(
            self,
            title: str,
            content: str,
            excerpt: str = None,
            slug: str = None
    ) -> Dict[str, Any]:
        """
        P11-1: SEO 优化建议主动提示
        
        Args:
            title: 文章标题
            content: 文章内容
            excerpt: 摘要
            slug: URL 路径
            
        Returns:
            SEO 优化建议列表
        """
        suggestions = []

        # 1. 标题长度检查
        if len(title) < 30:
            suggestions.append({
                "type": "warning",
                "field": "title",
                "message": "标题过短（建议 30-60 字符）",
                "recommendation": "添加更多描述性词汇以提高搜索引擎可见性",
                "priority": "high"
            })
        elif len(title) > 60:
            suggestions.append({
                "type": "warning",
                "field": "title",
                "message": f"标题过长（{len(title)} 字符，建议不超过 60）",
                "recommendation": "精简标题，确保在搜索结果中完整显示",
                "priority": "medium"
            })

        # 2. 摘要检查
        if not excerpt or len(excerpt) < 100:
            suggestions.append({
                "type": "info",
                "field": "excerpt",
                "message": "缺少摘要或摘要过短",
                "recommendation": "添加 100-160 字符的摘要，提高点击率",
                "priority": "high"
            })

        # 3. URL Slug 检查
        if slug:
            if len(slug) > 75:
                suggestions.append({
                    "type": "warning",
                    "field": "slug",
                    "message": "URL 路径过长",
                    "recommendation": "使用简短、描述性的 URL（不超过 75 字符）",
                    "priority": "medium"
                })

            if any(char in slug for char in ['_', '.', '%']):
                suggestions.append({
                    "type": "info",
                    "field": "slug",
                    "message": "URL 包含特殊字符",
                    "recommendation": "使用连字符 (-) 分隔单词，避免下划线和特殊字符",
                    "priority": "low"
                })

        # 4. 内容长度检查
        word_count = len(content.split())
        if word_count < 300:
            suggestions.append({
                "type": "warning",
                "field": "content",
                "message": f"内容过短（{word_count} 字）",
                "recommendation": "长内容（800+ 字）通常排名更好，考虑扩展内容",
                "priority": "high"
            })

        # 5. 关键词密度检查（简单实现）
        title_words = set(title.lower().split())
        content_words = content.lower().split()

        keyword_matches = sum(1 for word in content_words if word in title_words)
        keyword_density = keyword_matches / len(content_words) if content_words else 0

        if keyword_density < 0.01:
            suggestions.append({
                "type": "info",
                "field": "keywords",
                "message": "标题关键词在内容中出现频率较低",
                "recommendation": "确保标题中的主要关键词在内容中自然出现 2-3 次",
                "priority": "medium"
            })

        # 6. 内部链接检查
        if '[link]' not in content and 'http' not in content:
            suggestions.append({
                "type": "info",
                "field": "links",
                "message": "未检测到内部或外部链接",
                "recommendation": "添加相关内部链接和权威外部引用以提升 SEO",
                "priority": "low"
            })

        # 7. 图片 Alt 文本检查（简单检测）
        if '![](' in content or '<img' in content.lower():
            if 'alt=' not in content.lower():
                suggestions.append({
                    "type": "warning",
                    "field": "images",
                    "message": "图片缺少 Alt 文本",
                    "recommendation": "为所有图片添加描述性 Alt 文本以提升可访问性和 SEO",
                    "priority": "high"
                })

        return {
            "success": True,
            "suggestions": suggestions,
            "seo_score": self._calculate_seo_score(suggestions),
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_seo_score(self, suggestions: List[Dict]) -> int:
        """计算 SEO 分数（0-100）"""
        score = 100

        for suggestion in suggestions:
            if suggestion['priority'] == 'high':
                score -= 15
            elif suggestion['priority'] == 'medium':
                score -= 8
            elif suggestion['priority'] == 'low':
                score -= 3

        return max(0, min(100, score))

    async def recommend_related_articles(
            self,
            article_id: int,
            db_session: AsyncSession,
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        P11-1: 相关文章智能推荐
        
        Args:
            article_id: 当前文章 ID
            db_session: 数据库会话
            limit: 推荐数量
            
        Returns:
            相关文章列表
        """
        try:
            from shared.models.article import Article

            # 获取当前文章
            result = await db_session.execute(
                select(Article).where(Article.id == article_id)
            )
            current_article = result.scalar_one_or_none()

            if not current_article:
                return []

            # 基于标签相似度推荐（简化实现）
            # 实际项目中应使用向量相似度或协同过滤

            all_articles_result = await db_session.execute(
                select(Article)
                .where(
                    (Article.id != article_id) &
                    (Article.status == 'published')
                )
                .order_by(Article.published_at.desc())
                .limit(limit * 3)  # 获取更多候选文章
            )

            candidates = all_articles_result.scalars().all()

            # 简单评分算法：基于共同标签数量
            scored_articles = []
            current_tags = set(current_article.tags or [])

            for article in candidates:
                article_tags = set(article.tags or [])
                common_tags = current_tags.intersection(article_tags)

                if common_tags:
                    score = len(common_tags) / max(len(current_tags.union(article_tags)), 1)
                    scored_articles.append({
                        "id": article.id,
                        "title": article.title,
                        "slug": article.slug,
                        "excerpt": article.excerpt,
                        "relevance_score": round(score, 2),
                        "common_tags": list(common_tags),
                        "published_at": article.published_at.isoformat() if article.published_at else None
                    })

            # 按相关度排序
            scored_articles.sort(key=lambda x: x['relevance_score'], reverse=True)

            return scored_articles[:limit]

        except Exception as e:
            logger.error(f"Related articles recommendation failed: {e}")
            return []


# 全局实例
ai_agent_service = AIAgentRecommendations()
