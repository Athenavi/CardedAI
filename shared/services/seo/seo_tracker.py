"""
SEO 效果追踪服务
追踪搜索引擎流量、关键词排名、自然搜索表现等
"""


from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from src.unified_logger import default_logger as logger


class SEOTracker:
    """SEO 效果追踪器"""

    def __init__(self):
        # 搜索引擎标识符映射
        self.search_engines = {
            'google.com': 'Google',
            'www.google.com': 'Google',
            'baidu.com': 'Baidu',
            'www.baidu.com': 'Baidu',
            'bing.com': 'Bing',
            'www.bing.com': 'Bing',
            'sogou.com': 'Sogou',
            'www.sogou.com': 'Sogou',
            'so.com': '360 Search',
            'www.so.com': '360 Search',
        }

        # 搜索引擎查询参数
        self.search_params = {
            'Google': 'q',
            'Baidu': 'wd',
            'Bing': 'q',
            'Sogou': 'query',
            '360 Search': 'q',
        }

        # 访问记录 {article_id: [visit_info]}
        self._visits = defaultdict(list)

        # 搜索引擎流量统计 {search_engine: count}
        self._search_traffic = Counter()

        # 关键词统计 {keyword: count}
        self._keywords = Counter()

        # 文章 SEO 表现 {article_id: stats}
        self._article_seo = defaultdict(lambda: {
            'organic_views': 0,
            'search_visits': 0,
            'keywords': [],
            'avg_position': 0,
        })

    def track_visit(self, article_id: int, referrer: str = '',
                    user_agent: str = '', timestamp: datetime = None):
        """
        追踪页面访问
        
        Args:
            article_id: 文章ID
            referrer: 来源URL
            user_agent: 用户代理
            timestamp: 访问时间
        """
        if not timestamp:
            timestamp = datetime.now()

        visit_info = {
            'referrer': referrer,
            'user_agent': user_agent,
            'timestamp': timestamp,
            'is_search': False,
            'search_engine': None,
            'keyword': None,
        }

        # 分析是否为搜索引擎流量
        if referrer:
            search_info = self._analyze_referrer(referrer)
            if search_info:
                visit_info['is_search'] = True
                visit_info['search_engine'] = search_info['engine']
                visit_info['keyword'] = search_info['keyword']

                # 更新统计
                self._search_traffic[search_info['engine']] += 1
                if search_info['keyword']:
                    self._keywords[search_info['keyword']] += 1

                # 更新文章 SEO 统计
                self._article_seo[article_id]['organic_views'] += 1
                self._article_seo[article_id]['search_visits'] += 1
                if search_info['keyword']:
                    self._article_seo[article_id]['keywords'].append(search_info['keyword'])

        self._visits[article_id].append(visit_info)

    def _analyze_referrer(self, referrer: str) -> Optional[Dict]:
        """
        分析来源URL，判断是否为搜索引擎流量
        
        Args:
            referrer: 来源URL
            
        Returns:
            {'engine': str, 'keyword': str} 或 None
        """
        try:
            parsed = urlparse(referrer)
            domain = parsed.netloc.lower()

            # 检查是否为搜索引擎
            search_engine = None
            for eng_domain, eng_name in self.search_engines.items():
                if eng_domain in domain:
                    search_engine = eng_name
                    break

            if not search_engine:
                return None

            # 提取搜索关键词
            query_params = parse_qs(parsed.query)
            param_name = self.search_params.get(search_engine, 'q')

            keywords = query_params.get(param_name, [])
            keyword = keywords[0] if keywords else None

            return {
                'engine': search_engine,
                'keyword': keyword,
            }
        except Exception as e:
            logger.error(f"Error analyzing referrer: {e}")
            return None

    def get_search_traffic_summary(self, days: int = 30) -> Dict:
        """
        获取搜索引擎流量汇总
        
        Args:
            days: 统计天数
            
        Returns:
            流量汇总数据
        """
        now = datetime.now()
        cutoff = now - timedelta(days=days)

        # 统计各搜索引擎流量
        engine_stats = {}
        total_organic = 0

        for article_id, visits in self._visits.items():
            for visit in visits:
                if visit['timestamp'] >= cutoff and visit['is_search']:
                    engine = visit['search_engine']
                    if engine:
                        engine_stats[engine] = engine_stats.get(engine, 0) + 1
                        total_organic += 1

        return {
            'total_organic_views': total_organic,
            'by_engine': engine_stats,
            'period_days': days,
            'generated_at': now.isoformat(),
        }

    def get_top_keywords(self, limit: int = 20, days: int = 30) -> List[Dict]:
        """
        获取热门关键词
        
        Args:
            limit: 返回数量
            days: 统计天数
            
        Returns:
            关键词列表 [{keyword, count, articles}]
        """
        now = datetime.now()
        cutoff = now - timedelta(days=days)

        # 统计近期关键词
        keyword_stats = Counter()
        keyword_articles = defaultdict(set)

        for article_id, visits in self._visits.items():
            for visit in visits:
                if (visit['timestamp'] >= cutoff and
                        visit['is_search'] and
                        visit['keyword']):
                    keyword = visit['keyword']
                    keyword_stats[keyword] += 1
                    keyword_articles[keyword].add(article_id)

        # 返回 Top N
        result = []
        for keyword, count in keyword_stats.most_common(limit):
            result.append({
                'keyword': keyword,
                'count': count,
                'articles_count': len(keyword_articles[keyword]),
            })

        return result

    def get_article_seo_performance(self, article_id: int, days: int = 30) -> Dict:
        """
        获取文章 SEO 表现
        
        Args:
            article_id: 文章ID
            days: 统计天数
            
        Returns:
            SEO 表现数据
        """
        now = datetime.now()
        cutoff = now - timedelta(days=days)

        visits = self._visits.get(article_id, [])

        # 统计有机流量
        organic_views = 0
        search_visits = 0
        keywords = []

        for visit in visits:
            if visit['timestamp'] >= cutoff:
                if visit['is_search']:
                    search_visits += 1
                    organic_views += 1
                    if visit['keyword']:
                        keywords.append(visit['keyword'])

        # 关键词统计
        keyword_counts = Counter(keywords)
        top_keywords = [
            {'keyword': k, 'count': c}
            for k, c in keyword_counts.most_common(10)
        ]

        return {
            'article_id': article_id,
            'organic_views': organic_views,
            'search_visits': search_visits,
            'unique_keywords': len(keyword_counts),
            'top_keywords': top_keywords,
            'period_days': days,
        }

    def get_traffic_sources(self, article_id: int = None, days: int = 30) -> Dict:
        """
        获取流量来源分析
        
        Args:
            article_id: 文章ID（可选，不传则统计全站）
            days: 统计天数
            
        Returns:
            流量来源数据
        """
        now = datetime.now()
        cutoff = now - timedelta(days=days)

        sources = {
            'organic_search': 0,  # 自然搜索
            'direct': 0,  # 直接访问
            'referral': 0,  # 引荐流量
            'social': 0,  # 社交媒体
            'other': 0,  # 其他
        }

        # 社交媒体域名
        social_domains = [
            'facebook.com', 'twitter.com', 'weibo.com',
            'linkedin.com', 'reddit.com', 'zhihu.com'
        ]

        article_ids = [article_id] if article_id else self._visits.keys()

        for aid in article_ids:
            visits = self._visits.get(aid, [])
            for visit in visits:
                if visit['timestamp'] < cutoff:
                    continue

                referrer = visit.get('referrer', '')

                if not referrer:
                    sources['direct'] += 1
                elif visit.get('is_search'):
                    sources['organic_search'] += 1
                else:
                    # 检查是否为社交媒体
                    is_social = any(domain in referrer.lower() for domain in social_domains)
                    if is_social:
                        sources['social'] += 1
                    else:
                        sources['referral'] += 1

        total = sum(sources.values())

        # 计算百分比
        sources_with_pct = {}
        for source, count in sources.items():
            pct = (count / total * 100) if total > 0 else 0
            sources_with_pct[source] = {
                'count': count,
                'percentage': round(pct, 2),
            }

        return {
            'sources': sources_with_pct,
            'total_visits': total,
            'period_days': days,
        }


# 全局实例
seo_tracker = SEOTracker()
