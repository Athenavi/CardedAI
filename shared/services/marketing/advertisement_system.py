"""
广告管理系统服务
提供广告位管理、广告投放、统计等功能
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from src.unified_logger import default_logger as logger


class AdvertisementSystem:
    """广告管理系统"""

    def __init__(self):
        # 广告位定义 {slot_id: slot_info}
        self._ad_slots = {
            'header_top': {
                'name': '顶部横幅',
                'position': 'header',
                'width': 728,
                'height': 90,
                'description': '页面顶部通栏广告',
            },
            'sidebar_right': {
                'name': '右侧边栏',
                'position': 'sidebar',
                'width': 300,
                'height': 250,
                'description': '文章页右侧广告',
            },
            'article_inline': {
                'name': '文中广告',
                'position': 'content',
                'width': 600,
                'height': 120,
                'description': '文章内容中间插入广告',
            },
            'footer_bottom': {
                'name': '底部广告',
                'position': 'footer',
                'width': 728,
                'height': 90,
                'description': '页面底部广告',
            },
            'homepage_banner': {
                'name': '首页轮播',
                'position': 'homepage',
                'width': 1200,
                'height': 400,
                'description': '首页顶部轮播广告',
            },
        }

        # 广告记录 {ad_id: ad_info}
        self._ads = {}

        # 广告位投放 {slot_id: [ad_id, ...]}
        self._slot_ads = defaultdict(list)

        # 广告展示统计 {ad_id: {'impressions': count, 'clicks': count}}
        self._ad_stats = defaultdict(lambda: {'impressions': 0, 'clicks': 0})

        # 广告ID计数器
        self._ad_counter = 0

        # 广告联盟配置
        self._ad_network_configs = {
            'adsense': {
                'enabled': False,
                'publisher_id': '',  # Google AdSense Publisher ID
                'client_id': '',  # Ad Client ID
            },
            'baidu': {
                'enabled': False,
                'union_id': '',  # 百度联盟ID
            },
        }

    def create_ad(self, title: str, slot_id: str, ad_type: str,
                  content: str, image_url: str = None,
                  link_url: str = None, html_code: str = None,
                  start_date: datetime = None, end_date: datetime = None,
                  priority: int = 5, budget: float = None) -> Dict:
        """
        创建广告
        
        Args:
            title: 广告标题
            slot_id: 广告位ID
            ad_type: 广告类型(image/html/adsense/baidu)
            content: 广告内容(文本或描述)
            image_url: 图片URL(ad_type=image时必需)
            link_url: 点击跳转链接
            html_code: HTML代码(ad_type=html时必需)
            start_date: 开始时间
            end_date: 结束时间
            priority: 优先级(1-10, 越高越优先)
            budget: 预算上限
            
        Returns:
            广告信息
        """
        if slot_id not in self._ad_slots:
            raise ValueError(f"Invalid slot_id: {slot_id}")

        # 生成广告ID
        self._ad_counter += 1
        ad_id = f"ad_{self._ad_counter}_{int(datetime.now().timestamp())}"

        # 默认时间
        now = datetime.now()
        if not start_date:
            start_date = now
        if not end_date:
            end_date = now + timedelta(days=30)

        # 创建广告记录
        ad = {
            'ad_id': ad_id,
            'title': title,
            'slot_id': slot_id,
            'ad_type': ad_type,
            'content': content,
            'image_url': image_url,
            'link_url': link_url,
            'html_code': html_code,
            'start_date': start_date,
            'end_date': end_date,
            'priority': priority,
            'budget': budget,
            'spent': 0,
            'status': 'active',  # active/paused/expired
            'created_at': now,
            'updated_at': now,
        }

        # 存储广告
        self._ads[ad_id] = ad
        self._slot_ads[slot_id].append(ad_id)

        logger.info(f"Created ad {ad_id} for slot {slot_id}")
        return ad

    def get_slot_ads(self, slot_id: str, current_time: datetime = None) -> List[Dict]:
        """
        获取广告位的可用广告
        
        Args:
            slot_id: 广告位ID
            current_time: 当前时间
            
        Returns:
            广告列表(按优先级排序)
        """
        if not current_time:
            current_time = datetime.now()

        ads = []
        for ad_id in self._slot_ads.get(slot_id, []):
            ad = self._ads.get(ad_id)
            if not ad:
                continue

            # 检查状态和时间
            if ad['status'] != 'active':
                continue
            if current_time < ad['start_date'] or current_time > ad['end_date']:
                continue

            # 检查预算
            if ad['budget'] and ad['spent'] >= ad['budget']:
                continue

            ads.append(ad)

        # 按优先级排序(高优先级在前)
        ads.sort(key=lambda x: x['priority'], reverse=True)

        return ads

    def record_impression(self, ad_id: str):
        """
        记录广告展示
        
        Args:
            ad_id: 广告ID
        """
        if ad_id in self._ad_stats:
            self._ad_stats[ad_id]['impressions'] += 1

    def record_click(self, ad_id: str, cost_per_click: float = 0):
        """
        记录广告点击
        
        Args:
            ad_id: 广告ID
            cost_per_click: 每次点击费用
        """
        if ad_id in self._ad_stats:
            self._ad_stats[ad_id]['clicks'] += 1

            # 更新花费
            if ad_id in self._ads:
                self._ads[ad_id]['spent'] += cost_per_click

    def get_ad_stats(self, ad_id: str) -> Dict:
        """
        获取广告统计
        
        Args:
            ad_id: 广告ID
            
        Returns:
            统计数据
        """
        stats = self._ad_stats.get(ad_id, {'impressions': 0, 'clicks': 0})

        impressions = stats['impressions']
        clicks = stats['clicks']
        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        return {
            'impressions': impressions,
            'clicks': clicks,
            'ctr': round(ctr, 2),  # 点击率
        }

    def get_slot_stats(self, slot_id: str) -> Dict:
        """
        获取广告位统计
        
        Args:
            slot_id: 广告位ID
            
        Returns:
            统计数据
        """
        total_impressions = 0
        total_clicks = 0
        active_ads = 0

        for ad_id in self._slot_ads.get(slot_id, []):
            ad = self._ads.get(ad_id)
            if ad and ad['status'] == 'active':
                active_ads += 1

                stats = self._ad_stats.get(ad_id, {'impressions': 0, 'clicks': 0})
                total_impressions += stats['impressions']
                total_clicks += stats['clicks']

        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

        return {
            'slot_id': slot_id,
            'slot_name': self._ad_slots[slot_id]['name'],
            'active_ads': active_ads,
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'ctr': round(ctr, 2),
        }

    def pause_ad(self, ad_id: str) -> bool:
        """
        暂停广告
        
        Args:
            ad_id: 广告ID
            
        Returns:
            是否成功
        """
        ad = self._ads.get(ad_id)
        if not ad:
            return False

        ad['status'] = 'paused'
        ad['updated_at'] = datetime.now()

        logger.info(f"Paused ad {ad_id}")
        return True

    def activate_ad(self, ad_id: str) -> bool:
        """
        激活广告
        
        Args:
            ad_id: 广告ID
            
        Returns:
            是否成功
        """
        ad = self._ads.get(ad_id)
        if not ad:
            return False

        ad['status'] = 'active'
        ad['updated_at'] = datetime.now()

        logger.info(f"Activated ad {ad_id}")
        return True

    def delete_ad(self, ad_id: str) -> bool:
        """
        删除广告
        
        Args:
            ad_id: 广告ID
            
        Returns:
            是否成功
        """
        ad = self._ads.get(ad_id)
        if not ad:
            return False

        # 从广告位中移除
        slot_id = ad['slot_id']
        if ad_id in self._slot_ads[slot_id]:
            self._slot_ads[slot_id].remove(ad_id)

        # 删除广告
        del self._ads[ad_id]

        logger.info(f"Deleted ad {ad_id}")
        return True

    def get_all_slots(self) -> List[Dict]:
        """
        获取所有广告位
        
        Returns:
            广告位列表
        """
        slots = []
        for slot_id, slot_info in self._ad_slots.items():
            stats = self.get_slot_stats(slot_id)
            slots.append({
                'slot_id': slot_id,
                **slot_info,
                'stats': stats,
            })

        return slots

    def get_user_ads(self, user_id: int = None) -> List[Dict]:
        """
        获取用户创建的广告
        
        Args:
            user_id: 用户ID(可选)
            
        Returns:
            广告列表
        """
        # Filter ads by user_id if provided
        if user_id:
            return [ad for ad in self._ads.values() if ad.get('user_id') == user_id]
        return list(self._ads.values())

    def check_expired_ads(self):
        """检查并更新过期广告"""
        now = datetime.now()

        for ad in self._ads.values():
            if ad['status'] == 'active' and ad['end_date'] < now:
                ad['status'] = 'expired'
                logger.info(f"Ad {ad['ad_id']} expired")

    def configure_ad_network(self, network: str, config: Dict) -> bool:
        """
        配置广告联盟
        
        Args:
            network: 广告联盟名称(adsense/baidu)
            config: 配置信息
            
        Returns:
            是否成功
        """
        if network not in self._ad_network_configs:
            return False

        self._ad_network_configs[network].update(config)
        logger.info(f"Configured ad network: {network}")
        return True

    def get_ad_network_config(self, network: str) -> Dict:
        """
        获取广告联盟配置
        
        Args:
            network: 广告联盟名称
            
        Returns:
            配置信息
        """
        return self._ad_network_configs.get(network, {})

    def generate_adsense_code(self, slot_id: str, ad_format: str = 'auto') -> str:
        """
        生成 Google AdSense 广告代码
        
        Args:
            slot_id: 广告位ID
            ad_format: 广告格式(auto/display/article/match_content)
            
        Returns:
            AdSense HTML代码
        """
        config = self._ad_network_configs.get('adsense', {})

        if not config.get('enabled') or not config.get('publisher_id'):
            return '<!-- AdSense not configured -->'

        # AdSense 标准代码模板
        adsense_code = f"""
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
<!-- {self._ad_slots.get(slot_id, {}).get('name', 'Ad')} -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{config.get('client_id', '')}"
     data-ad-slot="AD_SLOT_ID"
     data-ad-format="{ad_format}"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>
        """

        return adsense_code.strip()

    def generate_baidu_code(self, slot_id: str) -> str:
        """
        生成百度联盟广告代码
        
        Args:
            slot_id: 广告位ID
            
        Returns:
            百度联盟HTML代码
        """
        config = self._ad_network_configs.get('baidu', {})

        if not config.get('enabled') or not config.get('union_id'):
            return '<!-- Baidu Union not configured -->'

        # 百度联盟标准代码模板
        baidu_code = f"""
<script type="text/javascript">
    var cpro_id = "{config.get('union_id', '')}";
</script>
<script type="text/javascript" src="https://cpro.baidustatic.com/cpro/ui/cm.js"></script>
        """

        return baidu_code.strip()

    def get_revenue_report(self, start_date: datetime = None,
                           end_date: datetime = None) -> Dict:
        """
        获取收益报表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            收益统计数据
        """
        total_impressions = 0
        total_clicks = 0
        total_revenue = 0

        for ad_id, stats in self._ad_stats.items():
            ad = self._ads.get(ad_id)
            if ad:
                # Filter by date range if provided
                if start_date and ad.get('created_at'):
                    if ad['created_at'] < start_date:
                        continue
                if end_date and ad.get('end_date'):
                    if ad['end_date'] > end_date:
                        continue
                        
                total_impressions += stats['impressions']
                total_clicks += stats['clicks']
                total_revenue += ad.get('spent', 0)

        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        ecpm = (total_revenue / total_impressions * 1000) if total_impressions > 0 else 0

        return {
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'total_revenue': total_revenue,
            'ctr': round(ctr, 2),
            'ecpm': round(ecpm, 2),  # 每千次展示收益
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None,
            }
        }


# 全局实例
advertisement_system = AdvertisementSystem()
