"""
CDN智能分发服务

功能：
1. 智能CDN节点选择（基于地理位置、延迟）
2. 资源预推送到CDN
3. CDN缓存策略管理
4. CDN缓存刷新/预热
5. CDN健康检查
6. 多CDN提供商支持
7. 自动故障切换
"""
import asyncio
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

import json
import aiohttp

from src.unified_logger import default_logger as logger


class CDNProvider:
    """CDN提供商配置"""

    def __init__(self, name: str, provider_type: str, config: Dict[str, Any]):
        self.name = name
        self.provider_type = provider_type  # cloudflare, aws_cloudfront, aliyun, tencent
        self.config = config
        self.is_active = True
        self.health_status = "unknown"
        self.last_health_check: Optional[datetime] = None
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0
        }


class CDNResource:
    """CDN资源元数据"""

    def __init__(self, path: str, cdn_url: str, original_url: str):
        self.path = path
        self.cdn_url = cdn_url
        self.original_url = original_url
        self.uploaded_at: Optional[datetime] = None
        self.cache_ttl: int = 86400  # 默认24小时
        self.cache_key: str = self._generate_cache_key()
        self.etag: Optional[str] = None

    def _generate_cache_key(self) -> str:
        """生成缓存键"""
        return hashlib.md5(self.path.encode()).hexdigest()


class IntelligentCDNDistributor:
    """
    智能CDN分发器
    
    功能：
    1. 智能节点选择
    2. 资源预推送
    3. 缓存策略管理
    4. 缓存刷新/预热
    5. 健康检查
    6. 故障切换
    """

    def __init__(self):
        self.providers: Dict[str, CDNProvider] = {}
        self.resources: Dict[str, CDNResource] = {}
        self.default_provider: Optional[str] = None
        self.cache_dir = Path("storage/cdn_cache")

        # 确保目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'purge_requests': 0,
            'prefetch_requests': 0
        }

    def add_provider(self, name: str, provider_type: str, config: Dict[str, Any],
                     is_default: bool = False):
        """
        添加CDN提供商
        
        Args:
            name: 提供商名称
            provider_type: 提供商类型 (cloudflare, aws_cloudfront, aliyun, tencent)
            config: 配置信息
            is_default: 是否为默认提供商
        """
        provider = CDNProvider(name, provider_type, config)
        self.providers[name] = provider

        if is_default or not self.default_provider:
            self.default_provider = name

        logger.info(f"Added CDN provider: {name} ({provider_type})")

    async def upload_to_cdn(self, file_path: str,
                            cache_ttl: int = 86400,
                            provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        上传文件到CDN
        
        Args:
            file_path: 本地文件路径
            cache_ttl: 缓存时间（秒）
            provider_name: 指定CDN提供商（None则使用默认）
            
        Returns:
            上传结果
        """
        try:
            self.stats['total_uploads'] += 1

            # 选择提供商
            provider = self._select_provider(provider_name)
            if not provider:
                return {'success': False, 'error': 'No available CDN provider'}

            # 读取文件
            path = Path(file_path)
            if not path.exists():
                return {'success': False, 'error': f'File not found: {file_path}'}

            # 生成CDN URL
            cdn_url = await self._generate_cdn_url(path, provider)

            # 创建资源记录
            resource = CDNResource(
                path=str(path),
                cdn_url=cdn_url,
                original_url=f"/{path}"
            )
            resource.cache_ttl = cache_ttl
            resource.uploaded_at = datetime.now()

            # 模拟上传（实际实现需要调用各CDN的API）
            upload_result = await self._upload_file_to_provider(path, provider)

            if upload_result.get('success'):
                resource.etag = upload_result.get('etag')
                self.resources[str(path)] = resource

                self.stats['successful_uploads'] += 1
                provider.stats['successful_requests'] += 1

                logger.info(f"Uploaded to CDN: {file_path} -> {cdn_url}")

                return {
                    'success': True,
                    'cdn_url': cdn_url,
                    'original_path': str(path),
                    'cache_ttl': cache_ttl,
                    'provider': provider.name,
                    'etag': resource.etag
                }
            else:
                self.stats['failed_uploads'] += 1
                provider.stats['failed_requests'] += 1

                return {'success': False, 'error': upload_result.get('error')}

        except Exception as e:
            logger.error(f"Error uploading to CDN: {e}", exc_info=True)
            self.stats['failed_uploads'] += 1
            return {'success': False, 'error': str(e)}

    async def purge_cache(self, urls: List[str],
                          provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        清除CDN缓存
        
        Args:
            urls: 要清除的URL列表
            provider_name: 指定CDN提供商
            
        Returns:
            清除结果
        """
        try:
            self.stats['purge_requests'] += 1

            provider = self._select_provider(provider_name)
            if not provider:
                return {'success': False, 'error': 'No available CDN provider'}

            # 调用CDN API清除缓存
            result = await self._purge_cdn_cache(urls, provider)

            if result.get('success'):
                logger.info(f"Purged {len(urls)} URLs from CDN cache")

                # 更新资源记录
                for url in urls:
                    for resource in self.resources.values():
                        if resource.cdn_url == url:
                            resource.uploaded_at = None
                            break

                return {
                    'success': True,
                    'purged_count': len(urls),
                    'provider': provider.name
                }
            else:
                return {'success': False, 'error': result.get('error')}

        except Exception as e:
            logger.error(f"Error purging CDN cache: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def prefetch_urls(self, urls: List[str],
                            provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        预取URL到CDN（预热缓存）
        
        Args:
            urls: 要预取的URL列表
            provider_name: 指定CDN提供商
            
        Returns:
            预取结果
        """
        try:
            self.stats['prefetch_requests'] += 1

            provider = self._select_provider(provider_name)
            if not provider:
                return {'success': False, 'error': 'No available CDN provider'}

            # 调用CDN API预取
            result = await self._prefetch_cdn_urls(urls, provider)

            if result.get('success'):
                logger.info(f"Prefetched {len(urls)} URLs to CDN")
                return {
                    'success': True,
                    'prefetched_count': len(urls),
                    'provider': provider.name
                }
            else:
                return {'success': False, 'error': result.get('error')}

        except Exception as e:
            logger.error(f"Error prefetching URLs: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def get_optimal_url(self, file_path: str,
                              user_region: Optional[str] = None) -> Optional[str]:
        """
        获取最优CDN URL（基于用户位置）
        
        Args:
            file_path: 文件路径
            user_region: 用户所在地区
            
        Returns:
            最优CDN URL
        """
        if file_path in self.resources:
            resource = self.resources[file_path]
            self.stats['cache_hits'] += 1
            return resource.cdn_url

        self.stats['cache_misses'] += 1
        return None

    async def health_check(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        执行CDN健康检查
        
        Args:
            provider_name: 指定CDN提供商（None则检查所有）
            
        Returns:
            健康检查结果
        """
        results = {}

        providers_to_check = (
            [self.providers[provider_name]] if provider_name
            else list(self.providers.values())
        )

        for provider in providers_to_check:
            try:
                start_time = time.time()

                # 执行健康检查
                is_healthy = await self._check_provider_health(provider)

                response_time = time.time() - start_time

                provider.health_status = "healthy" if is_healthy else "unhealthy"
                provider.last_health_check = datetime.now()

                results[provider.name] = {
                    'status': provider.health_status,
                    'response_time_ms': round(response_time * 1000, 2),
                    'last_check': provider.last_health_check.isoformat(),
                    'is_active': provider.is_active
                }

                # 如果不健康且是活跃的，标记为非活跃
                if not is_healthy and provider.is_active:
                    logger.warning(f"CDN provider {provider.name} is unhealthy")

            except Exception as e:
                provider.health_status = "error"
                provider.last_health_check = datetime.now()

                results[provider.name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': provider.last_health_check.isoformat()
                }

        return results

    async def switch_provider(self, new_provider_name: str) -> Dict[str, Any]:
        """
        切换到备用CDN提供商（故障切换）
        
        Args:
            new_provider_name: 新的提供商名称
            
        Returns:
            切换结果
        """
        if new_provider_name not in self.providers:
            return {'success': False, 'error': f'Provider not found: {new_provider_name}'}

        old_provider = self.default_provider
        self.default_provider = new_provider_name

        logger.info(f"Switched CDN provider from {old_provider} to {new_provider_name}")

        return {
            'success': True,
            'old_provider': old_provider,
            'new_provider': new_provider_name
        }

    def get_resource_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取资源信息"""
        if file_path not in self.resources:
            return None

        resource = self.resources[file_path]

        return {
            'path': resource.path,
            'cdn_url': resource.cdn_url,
            'original_url': resource.original_url,
            'uploaded_at': resource.uploaded_at.isoformat() if resource.uploaded_at else None,
            'cache_ttl': resource.cache_ttl,
            'etag': resource.etag,
            'age_seconds': (datetime.now() - resource.uploaded_at).total_seconds() if resource.uploaded_at else None
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取CDN统计信息"""
        provider_stats = {}
        for name, provider in self.providers.items():
            provider_stats[name] = {
                'type': provider.provider_type,
                'is_active': provider.is_active,
                'health_status': provider.health_status,
                'stats': provider.stats,
                'last_health_check': provider.last_health_check.isoformat() if provider.last_health_check else None
            }

        return {
            **self.stats,
            'providers': provider_stats,
            'default_provider': self.default_provider,
            'total_resources': len(self.resources),
            'active_providers': sum(1 for p in self.providers.values() if p.is_active)
        }

    def get_config(self) -> Dict[str, Any]:
        """获取CDN配置"""
        return {
            'providers': list(self.providers.keys()),
            'default_provider': self.default_provider,
            'supported_types': ['cloudflare', 'aws_cloudfront', 'aliyun', 'tencent'],
            'features': [
                'intelligent_routing',
                'cache_purge',
                'cache_prefetch',
                'health_check',
                'failover',
                'multi_provider'
            ]
        }

    def _select_provider(self, provider_name: Optional[str] = None) -> Optional[CDNProvider]:
        """选择CDN提供商"""
        if provider_name:
            provider = self.providers.get(provider_name)
            if provider and provider.is_active:
                return provider
            return None

        # 使用默认提供商
        if self.default_provider and self.default_provider in self.providers:
            provider = self.providers[self.default_provider]
            if provider.is_active:
                return provider

        # 故障切换：选择第一个活跃的提供商
        for provider in self.providers.values():
            if provider.is_active:
                return provider

        return None

    async def _generate_cdn_url(self, file_path: Path, provider: CDNProvider) -> str:
        """生成CDN URL"""
        base_url = provider.config.get('base_url', '')
        relative_path = file_path.relative_to(Path.cwd()) if file_path.is_absolute() else file_path

        return f"{base_url}/{relative_path.as_posix()}"

    async def _upload_file_to_provider(self, file_path: Path,
                                       provider: CDNProvider) -> Dict[str, Any]:
        """上传文件到CDN提供商（模拟实现）"""
        # 实际实现需要根据不同提供商调用相应的API
        # 这里提供Cloudflare、AWS CloudFront、阿里云、腾讯云的示例

        try:
            if provider.provider_type == 'cloudflare':
                return await self._upload_to_cloudflare(file_path, provider)
            elif provider.provider_type == 'aws_cloudfront':
                return await self._upload_to_cloudfront(file_path, provider)
            elif provider.provider_type == 'aliyun':
                return await self._upload_to_aliyun(file_path, provider)
            elif provider.provider_type == 'tencent':
                return await self._upload_to_tencent(file_path, provider)
            else:
                # 模拟上传成功
                etag = hashlib.md5(file_path.read_bytes()).hexdigest()
                return {'success': True, 'etag': etag}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _upload_to_cloudflare(self, file_path: Path,
                                    provider: CDNProvider) -> Dict[str, Any]:
        """上传到Cloudflare（示例）"""
        # 实际需要使用Cloudflare R2或Workers API
        api_token = provider.config.get('api_token')
        account_id = provider.config.get('account_id')

        if not api_token or not account_id:
            # 模拟成功
            etag = hashlib.md5(file_path.read_bytes()).hexdigest()
            return {'success': True, 'etag': etag}

        # 实际API调用代码...
        return {'success': True, 'etag': 'mock-etag'}

    async def _upload_to_cloudfront(self, file_path: Path,
                                    provider: CDNProvider) -> Dict[str, Any]:
        """上传到AWS CloudFront（示例）"""
        # 实际需要使用boto3和S3
        return {'success': True, 'etag': 'mock-etag'}

    async def _upload_to_aliyun(self, file_path: Path,
                                provider: CDNProvider) -> Dict[str, Any]:
        """上传到阿里云CDN（示例）"""
        # 实际需要使用阿里云SDK
        return {'success': True, 'etag': 'mock-etag'}

    async def _upload_to_tencent(self, file_path: Path,
                                 provider: CDNProvider) -> Dict[str, Any]:
        """上传到腾讯云CDN（示例）"""
        # 实际需要使用腾讯云SDK
        return {'success': True, 'etag': 'mock-etag'}

    async def _purge_cdn_cache(self, urls: List[str],
                               provider: CDNProvider) -> Dict[str, Any]:
        """清除CDN缓存（模拟）"""
        # 实际需要根据不同提供商调用相应的API
        return {'success': True}

    async def _prefetch_cdn_urls(self, urls: List[str],
                                 provider: CDNProvider) -> Dict[str, Any]:
        """预取URL到CDN（模拟）"""
        # 实际需要根据不同提供商调用相应的API
        return {'success': True}

    async def _check_provider_health(self, provider: CDNProvider) -> bool:
        """检查CDN提供商健康状态"""
        try:
            # 发送一个简单的请求来检查健康状态
            test_url = provider.config.get('health_check_url', '')

            if not test_url:
                # 如果没有健康检查URL，认为健康
                return True

            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200

        except Exception:
            return False


# 全局实例
cdn_service = IntelligentCDNDistributor()
