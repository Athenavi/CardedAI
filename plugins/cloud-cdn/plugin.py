"""
FastBlog Cloud CDN 管理插件
集成主流CDN提供商,提供智能缓存策略、URL优化和性能监控
"""

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class CDNProvider(ABC):
    """CDN 提供商抽象基类"""

    @abstractmethod
    async def purge_cache(self, urls: List[str]) -> Dict[str, Any]:
        """清除缓存"""
        pass

    @abstractmethod
    async def prefetch_urls(self, urls: List[str]) -> Dict[str, Any]:
        """预热缓存"""
        pass

    @abstractmethod
    async def get_analytics(self, period: str = '24h') -> Dict[str, Any]:
        """获取分析数据"""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        pass


class CloudflareCDN(CDNProvider):
    """Cloudflare CDN 实现"""

    def __init__(self, config: Dict[str, str]):
        self.api_token = config.get('api_token', '')
        self.zone_id = config.get('zone_id', '')
        self.base_url = "https://api.cloudflare.com/client/v4"

    async def purge_cache(self, urls: List[str]) -> Dict[str, Any]:
        """清除 Cloudflare 缓存"""
        try:
            import aiohttp

            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }

            # Cloudflare API 每次最多清除30个URL
            batches = [urls[i:i + 30] for i in range(0, len(urls), 30)]

            results = []
            for batch in batches:
                payload = {
                    'files': batch
                }

                url = f"{self.base_url}/zones/{self.zone_id}/purge_cache"

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        result = await response.json()
                        results.append(result)

            success = all(r.get('success', False) for r in results)

            return {
                'success': success,
                'provider': 'cloudflare',
                'purged_count': len(urls),
                'results': results
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def prefetch_urls(self, urls: List[str]) -> Dict[str, Any]:
        """预热 Cloudflare 缓存"""
        try:
            import aiohttp

            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'files': urls[:10]  # Cloudflare 限制每次最多10个
            }

            url = f"{self.base_url}/zones/{self.zone_id}/prefetch"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    result = await response.json()

            return {
                'success': result.get('success', False),
                'provider': 'cloudflare',
                'prefetched_count': len(urls[:10]),
                'result': result
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def get_analytics(self, period: str = '24h') -> Dict[str, Any]:
        """获取 Cloudflare 分析数据"""
        try:
            import aiohttp

            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }

            # 计算时间范围
            now = datetime.utcnow()
            if period == '24h':
                since = now - timedelta(hours=24)
            elif period == '7d':
                since = now - timedelta(days=7)
            elif period == '30d':
                since = now - timedelta(days=30)
            else:
                since = now - timedelta(hours=24)

            url = f"{self.base_url}/zones/{self.zone_id}/analytics/dashboard"
            params = {
                'since': since.isoformat() + 'Z',
                'until': now.isoformat() + 'Z'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    result = await response.json()

            if result.get('success'):
                data = result.get('result', {})
                return {
                    'success': True,
                    'provider': 'cloudflare',
                    'period': period,
                    'bandwidth': data.get('totals', {}).get('bytes', 0),
                    'requests': data.get('totals', {}).get('requests', 0),
                    'cached_requests': data.get('totals', {}).get('cachedRequests', 0),
                    'uncached_requests': data.get('totals', {}).get('uncachedRequests', 0),
                    'cache_hit_ratio': data.get('totals', {}).get('cacheRatio', 0),
                    'threats_detected': data.get('totals', {}).get('threats', 0),
                }
            else:
                return {
                    'success': False,
                    'error': result.get('errors', [])
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_connection(self) -> Dict[str, Any]:
        """测试 Cloudflare 连接"""
        try:
            import aiohttp

            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }

            url = f"{self.base_url}/zones/{self.zone_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    result = await response.json()

            return {
                'success': result.get('success', False),
                'provider': 'cloudflare',
                'zone_name': result.get('result', {}).get('name', '') if result.get('success') else ''
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class AliyunCDN(CDNProvider):
    """阿里云 CDN 实现"""

    def __init__(self, config: Dict[str, str]):
        self.access_key_id = config.get('access_key_id', '')
        self.access_key_secret = config.get('access_key_secret', '')
        self.domain = config.get('domain', '')

    async def purge_cache(self, urls: List[str]) -> Dict[str, Any]:
        """清除阿里云 CDN 缓存"""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcdn.request.v20180510.RefreshObjectCachesRequest import RefreshObjectCachesRequest

            client = AcsClient(self.access_key_id, self.access_key_secret, 'cn-hangzhou')

            request = RefreshObjectCachesRequest()
            request.set_ObjectPath('\n'.join(urls))
            request.set_ObjectType('File')

            response = client.do_action_with_exception(request)
            result = json.loads(response)

            return {
                'success': True,
                'provider': 'aliyun',
                'refresh_task_id': result.get('RefreshTaskId', ''),
                'purged_count': len(urls)
            }

        except ImportError:
            return {
                'success': False,
                'error': 'aliyun-python-sdk-cdn not installed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def prefetch_urls(self, urls: List[str]) -> Dict[str, Any]:
        """预热阿里云 CDN 缓存"""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcdn.request.v20180510.PushObjectCacheRequest import PushObjectCacheRequest

            client = AcsClient(self.access_key_id, self.access_key_secret, 'cn-hangzhou')

            request = PushObjectCacheRequest()
            request.set_ObjectPath('\n'.join(urls))

            response = client.do_action_with_exception(request)
            result = json.loads(response)

            return {
                'success': True,
                'provider': 'aliyun',
                'push_task_id': result.get('PushTaskId', ''),
                'prefetched_count': len(urls)
            }

        except ImportError:
            return {
                'success': False,
                'error': 'aliyun-python-sdk-cdn not installed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def get_analytics(self, period: str = '24h') -> Dict[str, Any]:
        """获取阿里云 CDN 分析数据"""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcdn.request.v20180510.DescribeDomainBpsDataRequest import DescribeDomainBpsDataRequest
            from aliyunsdkcdn.request.v20180510.DescribeDomainTrafficDataRequest import DescribeDomainTrafficDataRequest

            client = AcsClient(self.access_key_id, self.access_key_secret, 'cn-hangzhou')

            now = datetime.utcnow()
            if period == '24h':
                start_time = (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%MZ')
            elif period == '7d':
                start_time = (now - timedelta(days=7)).strftime('%Y-%m-%dT%H:%MZ')
            elif period == '30d':
                start_time = (now - timedelta(days=30)).strftime('%Y-%m-%dT%H:%MZ')
            else:
                start_time = (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%MZ')

            end_time = now.strftime('%Y-%m-%dT%H:%MZ')

            # 获取带宽数据
            bps_request = DescribeDomainBpsDataRequest()
            bps_request.set_StartTime(start_time)
            bps_request.set_EndTime(end_time)
            if self.domain:
                bps_request.set_DomainName(self.domain)

            bps_response = client.do_action_with_exception(bps_request)
            bps_data = json.loads(bps_response)

            # 获取流量数据
            traffic_request = DescribeDomainTrafficDataRequest()
            traffic_request.set_StartTime(start_time)
            traffic_request.set_EndTime(end_time)
            if self.domain:
                traffic_request.set_DomainName(self.domain)

            traffic_response = client.do_action_with_exception(traffic_request)
            traffic_data = json.loads(traffic_response)

            # 提取峰值带宽（bps -> Mbps）
            bps_list = bps_data.get('BpsDataPerInterval', {}).get('DataModule', [])
            peak_bps = max((item.get('PeakValue', 0) for item in bps_list), default=0)
            avg_bps = sum(item.get('AvgValue', 0) for item in bps_list) / max(len(bps_list), 1)

            # 提取总流量（bytes）
            traffic_list = traffic_data.get('TrafficDataPerInterval', {}).get('DataModule', [])
            total_traffic = sum(item.get('Value', 0) for item in traffic_list)

            return {
                'success': True,
                'provider': 'aliyun',
                'period': period,
                'peak_bandwidth_bps': peak_bps,
                'avg_bandwidth_bps': round(avg_bps, 2),
                'peak_bandwidth_mbps': round(peak_bps / 1_000_000, 2),
                'total_traffic_bytes': total_traffic,
                'total_traffic_gb': round(total_traffic / (1024 ** 3), 2),
                'data_points': len(bps_list),
            }

        except ImportError:
            return {
                'success': False,
                'error': 'aliyun-python-sdk-cdn not installed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_connection(self) -> Dict[str, Any]:
        """测试阿里云 CDN 连接"""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcdn.request.v20180510.DescribeCdnServiceRequest import DescribeCdnServiceRequest

            client = AcsClient(self.access_key_id, self.access_key_secret, 'cn-hangzhou')

            request = DescribeCdnServiceRequest()
            response = client.do_action_with_exception(request)

            return {
                'success': True,
                'provider': 'aliyun',
                'message': 'Connection successful'
            }

        except ImportError:
            return {
                'success': False,
                'error': 'aliyun-python-sdk-cdn not installed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class TencentCDN(CDNProvider):
    """腾讯云 CDN 实现"""

    def __init__(self, config: Dict[str, str]):
        self.secret_id = config.get('secret_id', '')
        self.secret_key = config.get('secret_key', '')
        self.domain = config.get('domain', '')

    async def purge_cache(self, urls: List[str]) -> Dict[str, Any]:
        """清除腾讯云 CDN 缓存"""
        try:
            from tencentcloud.common import credential
            from tencentcloud.cdn.v20180606 import cdn_client, models

            cred = credential.Credential(self.secret_id, self.secret_key)
            client = cdn_client.CdnClient(cred, 'ap-guangzhou')

            req = models.PurgePathCacheRequest()
            params = {
                "Paths": urls,
                "FlushType": "delete"
            }
            req.from_json_string(json.dumps(params))

            resp = client.PurgePathCache(req)
            result = json.loads(resp.to_json_string())

            return {
                'success': True,
                'provider': 'tencent',
                'task_id': result.get('TaskId', ''),
                'purged_count': len(urls)
            }

        except ImportError:
            return {
                'success': False,
                'error': 'tencentcloud-sdk-python not installed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def prefetch_urls(self, urls: List[str]) -> Dict[str, Any]:
        """预热腾讯云 CDN 缓存"""
        try:
            from tencentcloud.common import credential
            from tencentcloud.cdn.v20180606 import cdn_client, models

            cred = credential.Credential(self.secret_id, self.secret_key)
            client = cdn_client.CdnClient(cred, 'ap-guangzhou')

            req = models.PushUrlsCacheRequest()
            params = {
                "Urls": urls
            }
            req.from_json_string(json.dumps(params))

            resp = client.PushUrlsCache(req)
            result = json.loads(resp.to_json_string())

            return {
                'success': True,
                'provider': 'tencent',
                'task_id': result.get('TaskId', ''),
                'prefetched_count': len(urls)
            }

        except ImportError:
            return {
                'success': False,
                'error': 'tencentcloud-sdk-python not installed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def get_analytics(self, period: str = '24h') -> Dict[str, Any]:
        """获取腾讯云 CDN 分析数据"""
        try:
            from tencentcloud.common import credential
            from tencentcloud.cdn.v20180606 import cdn_client, models

            cred = credential.Credential(self.secret_id, self.secret_key)
            client = cdn_client.CdnClient(cred, 'ap-guangzhou')

            now = datetime.utcnow()
            if period == '24h':
                start_time = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
                interval = '5min'
            elif period == '7d':
                start_time = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                interval = 'hour'
            elif period == '30d':
                start_time = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                interval = 'day'
            else:
                start_time = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
                interval = '5min'

            end_time = now.strftime('%Y-%m-%d %H:%M:%S')

            # 获取流量数据
            traffic_req = models.DescribeCdnDataRequest()
            params = {
                "StartTime": start_time,
                "EndTime": end_time,
                "Interval": interval,
                "Metric": "flux",
            }
            if self.domain:
                params["Domains"] = [self.domain]
            traffic_req.from_json_string(json.dumps(params))

            traffic_resp = client.DescribeCdnData(traffic_req)
            traffic_data = json.loads(traffic_resp.to_json_string())

            # 获取带宽数据
            bps_req = models.DescribeCdnDataRequest()
            params["Metric"] = "bandwidth"
            bps_req.from_json_string(json.dumps(params))

            bps_resp = client.DescribeCdnData(bps_req)
            bps_data = json.loads(bps_resp.to_json_string())

            # 提取数据
            flux_list = traffic_data.get('Data', [{}])[0].get('CdnData', []) if traffic_data.get('Data') else []
            total_flux = sum(flux_list) if flux_list else 0

            bps_list = bps_data.get('Data', [{}])[0].get('CdnData', []) if bps_data.get('Data') else []
            peak_bps = max(bps_list) if bps_list else 0
            avg_bps = sum(bps_list) / max(len(bps_list), 1) if bps_list else 0

            return {
                'success': True,
                'provider': 'tencent',
                'period': period,
                'peak_bandwidth_bps': peak_bps,
                'avg_bandwidth_bps': round(avg_bps, 2),
                'peak_bandwidth_mbps': round(peak_bps / 1_000_000, 2),
                'total_flux_bytes': total_flux,
                'total_flux_gb': round(total_flux / (1024 ** 3), 2),
                'data_points': len(bps_list),
            }

        except ImportError:
            return {
                'success': False,
                'error': 'tencentcloud-sdk-python not installed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_connection(self) -> Dict[str, Any]:
        """测试腾讯云 CDN 连接"""
        try:
            from tencentcloud.common import credential
            from tencentcloud.cdn.v20180606 import cdn_client, models

            cred = credential.Credential(self.secret_id, self.secret_key)
            client = cdn_client.CdnClient(cred, 'ap-guangzhou')

            req = models.DescribeCdnDomainLogsRequest()
            req.from_json_string(json.dumps({}))

            client.DescribeCdnDomainLogs(req)

            return {
                'success': True,
                'provider': 'tencent',
                'message': 'Connection successful'
            }

        except ImportError:
            return {
                'success': False,
                'error': 'tencentcloud-sdk-python not installed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class CloudCDNPlugin(BasePlugin):
    """
    FastBlog Cloud CDN 管理插件

    功能:
    1. 多云CDN提供商支持 (Cloudflare/阿里云/腾讯云)
    2. 智能缓存策略管理
    3. 缓存清除和预热
    4. CDN 性能分析和监控
    5. 自动资源优化 (图片压缩/WebP转换)
    6. URL 自动转换为 CDN URL
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="FastBlog Cloud CDN",
            slug="cloud-cdn",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enabled': False,
            'primary_provider': 'cloudflare',
            'providers': {
                'cloudflare': {
                    'enabled': False,
                    'api_token': '',
                    'zone_id': '',
                },
                'aliyun': {
                    'enabled': False,
                    'access_key_id': '',
                    'access_key_secret': '',
                    'domain': '',
                },
                'tencent': {
                    'enabled': False,
                    'secret_id': '',
                    'secret_key': '',
                    'domain': '',
                }
            },

            # 缓存策略
            'cache_strategies': {
                'static': {
                    'pattern': r'\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$',
                    'ttl': 86400 * 365,  # 1年
                    'cache_control': 'public, max-age=31536000, immutable'
                },
                'images': {
                    'pattern': r'\.(png|jpg|jpeg|gif|webp|svg)$',
                    'ttl': 86400 * 30,  # 30天
                    'cache_control': 'public, max-age=2592000'
                },
                'html': {
                    'pattern': r'\.html?$',
                    'ttl': 3600,  # 1小时
                    'cache_control': 'public, max-age=3600'
                },
                'api': {
                    'pattern': r'^/api/',
                    'ttl': 300,  # 5分钟
                    'cache_control': 'private, max-age=300'
                }
            },

            # 自动优化
            'auto_optimize': {
                'convert_to_webp': True,
                'compress_images': True,
                'compression_quality': 80,
                'generate_srcset': True,
                'srcset_sizes': [400, 800, 1200, 1600]
            },

            # URL 转换
            'url_conversion': {
                'enabled': True,
                'cdn_base_url': '',  # 例如: https://cdn.example.com
                'auto_convert_html': True,
                'excluded_paths': ['/admin', '/api']
            },

            # 监控
            'monitoring': {
                'enabled': True,
                'analytics_period': '24h',
                'auto_purge_on_update': True,
                'log_purge_actions': True
            }
        }

        # CDN 提供商实例缓存
        self._provider_instances: Dict[str, CDNProvider] = {}

        # 缓存统计
        self.cache_stats = {
            'total_purges': 0,
            'total_prefetches': 0,
            'total_urls_converted': 0,
            'last_purge_time': None,
            'last_prefetch_time': None
        }

        # 加载统计
        self._load_stats()

        print("[CloudCDN] Plugin initialized")

    def register_hooks(self):
        """注册钩子"""
        # 内容更新时自动清除相关缓存
        if self.settings['monitoring']['auto_purge_on_update']:
            plugin_hooks.add_action(
                "article_published",
                self.on_content_update,
                priority=10
            )

            plugin_hooks.add_action(
                "article_updated",
                self.on_content_update,
                priority=10
            )

        # HTML 响应时自动转换 URL
        if self.settings['url_conversion']['enabled'] and self.settings['url_conversion']['auto_convert_html']:
            plugin_hooks.add_filter(
                "before_response",
                self.convert_html_urls,
                priority=5
            )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[CloudCDN] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[CloudCDN] Plugin deactivated")

    def _load_stats(self):
        """加载统计数据"""
        stats_file = Path("plugins_data") / "cloud-cdn" / "stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.cache_stats = json.load(f)
            except:
                pass

    def _save_stats(self):
        """保存统计数据"""
        stats_file = Path("plugins_data") / "cloud-cdn" / "stats.json"
        stats_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(stats_file, 'w') as f:
                json.dump(self.cache_stats, f, indent=2)
        except Exception as e:
            print(f"[CloudCDN] Failed to save stats: {e}")

    def _get_provider(self, provider_name: str = None) -> Optional[CDNProvider]:
        """获取 CDN 提供商实例"""
        if provider_name is None:
            provider_name = self.settings['primary_provider']

        # 检查缓存
        if provider_name in self._provider_instances:
            return self._provider_instances[provider_name]

        # 创建新实例
        provider_config = self.settings['providers'].get(provider_name, {})

        if not provider_config.get('enabled', False):
            print(f"[CloudCDN] Provider {provider_name} is not enabled")
            return None

        try:
            if provider_name == 'cloudflare':
                instance = CloudflareCDN(provider_config)
            elif provider_name == 'aliyun':
                instance = AliyunCDN(provider_config)
            elif provider_name == 'tencent':
                instance = TencentCDN(provider_config)
            else:
                print(f"[CloudCDN] Unknown provider: {provider_name}")
                return None

            # 缓存实例
            self._provider_instances[provider_name] = instance
            return instance

        except Exception as e:
            print(f"[CloudCDN] Failed to create provider instance: {e}")
            return None

    async def purge_cache(
            self,
            urls: List[str],
            provider: str = None
    ) -> Dict[str, Any]:
        """
        清除 CDN 缓存

        Args:
            urls: 要清除的 URL 列表
            provider: CDN 提供商名称

        Returns:
            清除结果
        """
        if not self.settings['enabled']:
            return {
                'success': False,
                'error': 'CDN plugin is not enabled'
            }

        cdn_provider = self._get_provider(provider)
        if not cdn_provider:
            return {
                'success': False,
                'error': f'CDN provider not available: {provider or self.settings["primary_provider"]}'
            }

        result = await cdn_provider.purge_cache(urls)

        if result['success']:
            self.cache_stats['total_purges'] += 1
            self.cache_stats['last_purge_time'] = datetime.now().isoformat()
            self._save_stats()

            if self.settings['monitoring']['log_purge_actions']:
                print(f"[CloudCDN] Purged {len(urls)} URLs from {result.get('provider', 'unknown')}")

        return result

    async def prefetch_urls(
            self,
            urls: List[str],
            provider: str = None,
            priority: str = 'normal'
    ) -> Dict[str, Any]:
        """
        预热 CDN 缓存

        Args:
            urls: 要预热的 URL 列表
            provider: CDN 提供商名称
            priority: 优先级 (high/normal/low)

        Returns:
            预热结果
        """
        if not self.settings['enabled']:
            return {
                'success': False,
                'error': 'CDN plugin is not enabled'
            }

        cdn_provider = self._get_provider(provider)
        if not cdn_provider:
            return {
                'success': False,
                'error': f'CDN provider not available: {provider or self.settings["primary_provider"]}'
            }

        result = await cdn_provider.prefetch_urls(urls)

        if result['success']:
            self.cache_stats['total_prefetches'] += 1
            self.cache_stats['last_prefetch_time'] = datetime.now().isoformat()
            self._save_stats()

            print(f"[CloudCDN] Prefetched {len(urls)} URLs to {result.get('provider', 'unknown')}")

        return result

    async def get_analytics(
            self,
            period: str = '24h',
            provider: str = None
    ) -> Dict[str, Any]:
        """
        获取 CDN 分析数据

        Args:
            period: 时间周期 (24h/7d/30d)
            provider: CDN 提供商名称

        Returns:
            分析数据
        """
        if not self.settings['enabled']:
            return {
                'success': False,
                'error': 'CDN plugin is not enabled'
            }

        cdn_provider = self._get_provider(provider)
        if not cdn_provider:
            return {
                'success': False,
                'error': f'CDN provider not available'
            }

        return await cdn_provider.get_analytics(period)

    async def test_connection(self, provider: str = None) -> Dict[str, Any]:
        """
        测试 CDN 连接

        Args:
            provider: CDN 提供商名称

        Returns:
            测试结果
        """
        cdn_provider = self._get_provider(provider)
        if not cdn_provider:
            return {
                'success': False,
                'error': f'CDN provider not available'
            }

        return await cdn_provider.test_connection()

    def convert_to_cdn_url(self, original_url: str) -> str:
        """
        将原始 URL 转换为 CDN URL

        Args:
            original_url: 原始 URL

        Returns:
            CDN URL
        """
        if not self.settings['url_conversion']['enabled']:
            return original_url

        cdn_base_url = self.settings['url_conversion']['cdn_base_url']
        if not cdn_base_url:
            return original_url

        # 排除特定路径
        for excluded in self.settings['url_conversion']['excluded_paths']:
            if original_url.startswith(excluded):
                return original_url

        # 如果已经是 CDN URL,直接返回
        if original_url.startswith(cdn_base_url):
            return original_url

        # 转换 URL
        if original_url.startswith('/'):
            cdn_url = f"{cdn_base_url}{original_url}"
        else:
            cdn_url = f"{cdn_base_url}/{original_url}"

        self.cache_stats['total_urls_converted'] += 1
        self._save_stats()

        return cdn_url

    def convert_html_urls(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换 HTML 中的 URL 为 CDN URL

        Args:
            response_data: 响应数据

        Returns:
            修改后的响应数据
        """
        if not self.settings['url_conversion']['enabled']:
            return {'converted': False}

        body = response_data.get('body', '')
        if not body or not isinstance(body, str):
            return {'converted': False}

        # 匹配 img src, link href, script src 等
        patterns = [
            (r'<img[^>]+src=["\']([^"\']+)["\']', 'img_src'),
            (r'<link[^>]+href=["\']([^"\']+)["\']', 'link_href'),
            (r'<script[^>]+src=["\']([^"\']+)["\']', 'script_src'),
        ]

        converted_count = 0

        for pattern, attr_type in patterns:
            def replace_url(match):
                nonlocal converted_count
                original_url = match.group(1)

                # 跳过外部 URL 和数据 URI
                if original_url.startswith(('http://', 'https://', 'data:', '//')):
                    return match.group(0)

                cdn_url = self.convert_to_cdn_url(original_url)
                if cdn_url != original_url:
                    converted_count += 1
                    return match.group(0).replace(original_url, cdn_url)
                return match.group(0)

            body = re.sub(pattern, replace_url, body)

        if converted_count > 0:
            response_data['body'] = body
            print(f"[CloudCDN] Converted {converted_count} URLs in HTML")

        return {
            'converted': converted_count > 0,
            'count': converted_count
        }

    def on_content_update(self, article_data: Dict[str, Any]):
        """内容更新时的回调"""
        if not self.settings['monitoring']['auto_purge_on_update']:
            return

        # 清除相关文章页面的缓存
        article_id = article_data.get('id')
        if article_id:
            urls_to_purge = [
                f'/article/{article_id}',
                f'/api/v1/articles/{article_id}',
            ]

            # 异步清除缓存
            import asyncio
            asyncio.create_task(self.purge_cache(urls_to_purge))

    def get_cache_strategy(self, url: str) -> Optional[Dict[str, Any]]:
        """
        根据 URL 获取缓存策略

        Args:
            url: URL 路径

        Returns:
            缓存策略配置
        """
        for strategy_name, strategy in self.settings['cache_strategies'].items():
            pattern = strategy['pattern']
            if re.search(pattern, url):
                return {
                    'name': strategy_name,
                    'ttl': strategy['ttl'],
                    'cache_control': strategy['cache_control']
                }

        return None

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enabled',
                    'type': 'boolean',
                    'label': '启用 CDN',
                },
                {
                    'key': 'primary_provider',
                    'type': 'select',
                    'label': '主要 CDN 提供商',
                    'options': [
                        {'value': 'cloudflare', 'label': 'Cloudflare'},
                        {'value': 'aliyun', 'label': '阿里云 CDN'},
                        {'value': 'tencent', 'label': '腾讯云 CDN'},
                    ],
                },
                {
                    'key': 'url_conversion.enabled',
                    'type': 'boolean',
                    'label': '启用 URL 自动转换',
                },
                {
                    'key': 'url_conversion.cdn_base_url',
                    'type': 'text',
                    'label': 'CDN 基础 URL',
                    'placeholder': 'https://cdn.example.com',
                },
                {
                    'key': 'auto_optimize.convert_to_webp',
                    'type': 'boolean',
                    'label': '自动转换为 WebP',
                },
                {
                    'key': 'monitoring.auto_purge_on_update',
                    'type': 'boolean',
                    'label': '内容更新时自动清除缓存',
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '测试 CDN 连接',
                    'action': 'test_connection',
                    'variant': 'outline',
                },
                {
                    'type': 'button',
                    'label': '查看分析数据',
                    'action': 'view_analytics',
                    'variant': 'default',
                },
            ]
        }


# 全局实例
plugin = CloudCDNPlugin()
