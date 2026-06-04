"""
CDN 优化配置 API - V2 版本
提供多云 CDN 配置、缓存策略管理、性能优化等功能
"""
from typing import Optional

from fastapi import APIRouter, Depends

from shared.models.user import User
from shared.services.performance.cdn_integration import cdn_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(prefix="/cdn", tags=["CDN Optimization"])


@router.get("/config", summary="获取 CDN 配置")
async def get_cdn_config(
        current_user: User = Depends(jwt_required)
):
    """
    获取当前 CDN 配置信息
    
    返回所有已配置的 CDN 提供商及其设置
    """
    try:
        config = cdn_service.get_config()

        return ApiResponse(
            success=True,
            data=config
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取配置失败: {str(e)}"
        )


@router.post("/configure/cloudflare", summary="配置 Cloudflare CDN")
async def configure_cloudflare(
        api_token: str,
        zone_id: str,
        domain: str,
        enable_cache: bool = True,
        enable_minification: bool = True,
        enable_brotli: bool = True,
        cache_ttl: int = 86400,
        current_user: User = Depends(jwt_required)
):
    """
    配置 Cloudflare CDN
    
    参数:
    - api_token: Cloudflare API Token
    - zone_id: Zone ID
    - domain: 域名
    - enable_cache: 启用缓存
    - enable_minification: 启用代码压缩
    - enable_brotli: 启用 Brotli 压缩
    - cache_ttl: 缓存 TTL（秒）
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        return ApiResponse(
            success=False,
            error="需要管理员权限"
        )

    try:
        result = cdn_service.configure_cloudflare(
            api_token=api_token,
            zone_id=zone_id,
            domain=domain,
            enable_cache=enable_cache,
            enable_minification=enable_minification,
            enable_brotli=enable_brotli,
            cache_ttl=cache_ttl
        )

        return ApiResponse(
            success=True,
            data=result,
            message="Cloudflare 配置成功"
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"配置失败: {str(e)}"
        )


@router.post("/configure/aws-cloudfront", summary="配置 AWS CloudFront")
async def configure_aws_cloudfront(
        access_key_id: str,
        secret_access_key: str,
        distribution_id: str,
        domain: str,
        default_ttl: int = 86400,
        max_ttl: int = 31536000,
        current_user: User = Depends(jwt_required)
):
    """
    配置 AWS CloudFront CDN
    
    参数:
    - access_key_id: AWS Access Key ID
    - secret_access_key: AWS Secret Access Key
    - distribution_id: CloudFront Distribution ID
    - domain: 域名
    - default_ttl: 默认缓存时间（秒）
    - max_ttl: 最大缓存时间（秒）
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        return ApiResponse(
            success=False,
            error="需要管理员权限"
        )

    try:
        result = cdn_service.configure_aws_cloudfront(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            distribution_id=distribution_id,
            domain=domain,
            default_ttl=default_ttl,
            max_ttl=max_ttl
        )

        return ApiResponse(
            success=True,
            data=result,
            message="AWS CloudFront 配置成功"
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"配置失败: {str(e)}"
        )


@router.post("/configure/aliyun", summary="配置阿里云 CDN")
async def configure_aliyun_cdn(
        access_key_id: str,
        access_key_secret: str,
        domain: str,
        cache_ttl: int = 86400,
        current_user: User = Depends(jwt_required)
):
    """
    配置阿里云 CDN
    
    参数:
    - access_key_id: 阿里云 Access Key ID
    - access_key_secret: 阿里云 Access Key Secret
    - domain: 加速域名
    - cache_ttl: 缓存时间（秒）
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        return ApiResponse(
            success=False,
            error="需要管理员权限"
        )

    try:
        result = cdn_service.configure_aliyun_cdn(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            domain=domain,
            cache_ttl=cache_ttl
        )

        return ApiResponse(
            success=True,
            data=result,
            message="阿里云 CDN 配置成功"
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"配置失败: {str(e)}"
        )


@router.post("/configure/custom", summary="配置自定义 CDN")
async def configure_custom_cdn(
        name: str,
        base_url: str,
        api_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_ttl: int = 86400,
        current_user: User = Depends(jwt_required)
):
    """
    配置自定义 CDN 提供商
    
    参数:
    - name: 提供商名称
    - base_url: CDN 基础 URL
    - api_endpoint: API 端点（可选）
    - api_key: API 密钥（可选）
    - cache_ttl: 缓存时间（秒）
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        return ApiResponse(
            success=False,
            error="需要管理员权限"
        )

    try:
        result = cdn_service.configure_custom_cdn(
            name=name,
            base_url=base_url,
            api_endpoint=api_endpoint,
            api_key=api_key,
            cache_ttl=cache_ttl
        )

        return ApiResponse(
            success=True,
            data=result,
            message="自定义 CDN 配置成功"
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"配置失败: {str(e)}"
        )


@router.get("/cache-strategies", summary="获取缓存策略")
async def get_cache_strategies():
    """
    获取推荐的缓存策略配置
    
    返回不同类型资源的最佳缓存实践
    """
    strategies = {
        'static_assets': {
            'description': '静态资源（CSS、JS、字体）',
            'ttl': 31536000,  # 1年
            'ttl_human': '1 year',
            'files': ['*.css', '*.js', '*.woff', '*.woff2', '*.ttf', '*.eot'],
            'note': '使用版本化URL，文件名包含哈希值'
        },
        'images': {
            'description': '图片资源',
            'ttl': 2592000,  # 30天
            'ttl_human': '30 days',
            'files': ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.svg'],
            'note': '根据更新频率调整，考虑使用响应式图片'
        },
        'html': {
            'description': 'HTML 页面',
            'ttl': 3600,  # 1小时
            'ttl_human': '1 hour',
            'files': ['*.html', '/'],
            'note': '短期缓存，确保内容及时更新'
        },
        'api': {
            'description': 'API 响应',
            'ttl': 300,  # 5分钟
            'ttl_human': '5 minutes',
            'files': ['/api/*'],
            'note': '动态内容，根据业务需求调整'
        },
        'media': {
            'description': '媒体文件（视频、音频）',
            'ttl': 7776000,  # 90天
            'ttl_human': '90 days',
            'files': ['*.mp4', '*.webm', '*.mp3', '*.wav'],
            'note': '大文件长期缓存，使用范围请求支持断点续传'
        }
    }

    return ApiResponse(
        success=True,
        data=strategies
    )


@router.get("/best-practices", summary="获取 CDN 最佳实践")
async def get_best_practices():
    """
    获取 CDN 使用和优化的最佳实践指南
    """
    return ApiResponse(
        success=True,
        data={
            'title': 'CDN 优化最佳实践',
            'sections': [
                {
                    'title': '缓存策略',
                    'practices': [
                        '使用版本化URL管理静态资源缓存失效',
                        '为不同类型资源设置合理的TTL',
                        '利用 Cache-Control 和 ETag 头',
                        '定期清除过时资源的缓存',
                        '使用 stale-while-revalidate 提高可用性'
                    ]
                },
                {
                    'title': '性能优化',
                    'practices': [
                        '启用 Brotli 或 Gzip 压缩',
                        '使用 HTTP/2 或 HTTP/3',
                        '实施图片懒加载',
                        '使用 WebP 等现代图片格式',
                        '最小化 CSS 和 JavaScript',
                        '使用 CDN 的图像优化功能'
                    ]
                },
                {
                    'title': '安全配置',
                    'practices': [
                        '强制使用 HTTPS',
                        '启用 HSTS (HTTP Strict Transport Security)',
                        '配置 CORS 策略',
                        '使用 WAF (Web Application Firewall)',
                        '限制允许的 HTTP 方法',
                        '实施速率限制'
                    ]
                },
                {
                    'title': '监控和分析',
                    'practices': [
                        '监控 CDN 命中率',
                        '跟踪带宽使用情况',
                        '分析用户地理位置分布',
                        '设置异常告警',
                        '定期审查访问日志',
                        'A/B 测试不同的 CDN 配置'
                    ]
                },
                {
                    'title': '成本优化',
                    'practices': [
                        '选择合适的 CDN 套餐',
                        '优化缓存策略减少回源',
                        '使用边缘计算减少传输',
                        '实施流量整形',
                        '定期清理未使用的资源',
                        '考虑多云 CDN 策略'
                    ]
                }
            ],
            'tools': [
                'Google PageSpeed Insights',
                'GTmetrix',
                'WebPageTest',
                'CDNPerf',
                'Pingdom'
            ]
        }
    )


@router.get("/integration-guide", summary="获取集成指南")
async def get_integration_guide():
    """
    获取 CDN 集成详细指南
    
    包括各云服务商的配置步骤和代码示例
    """
    return ApiResponse(
        success=True,
        data={
            'cloudflare': {
                'name': 'Cloudflare',
                'website': 'https://www.cloudflare.com',
                'free_tier': True,
                'steps': [
                    '注册 Cloudflare 账号',
                    '添加域名并更改 Nameservers',
                    '在 Dashboard 中获取 Zone ID',
                    '创建 API Token（Zone -> Cache Purge 权限）',
                    '在 FastBlog 中配置 Cloudflare',
                    '测试 CDN 是否正常工作'
                ],
                'code_example': '''
# Python 示例
import cloudflare

cf = cloudflare.CloudFlare(email='your@email.com', token='YOUR_API_TOKEN')
zones = cf.zones.get()
zone_id = zones[0]['id']

# 清除缓存
cf.zones.purge_cache.delete(zone_id, data={'files': ['https://example.com/image.jpg']})
                '''.strip()
            },
            'aws_cloudfront': {
                'name': 'AWS CloudFront',
                'website': 'https://aws.amazon.com/cloudfront/',
                'free_tier': False,
                'steps': [
                    '创建 AWS 账号',
                    '在 CloudFront 控制台创建 Distribution',
                    '配置 Origin（S3 或自定义源站）',
                    '设置缓存行为',
                    '获取 Distribution ID',
                    '创建 IAM 用户并获取 Access Key',
                    '在 FastBlog 中配置 CloudFront'
                ],
                'code_example': '''
# Python 示例 (boto3)
import boto3

client = boto3.client('cloudfront')

# 创建 invalidation 清除缓存
response = client.create_invalidation(
    DistributionId='E1234567890',
    InvalidationBatch={
        'Paths': {
            'Quantity': 1,
            'Items': ['/image.jpg']
        },
        'CallerReference': 'unique-id-123'
    }
)
                '''.strip()
            },
            'aliyun': {
                'name': '阿里云 CDN',
                'website': 'https://www.aliyun.com/product/cdn',
                'free_tier': False,
                'steps': [
                    '注册阿里云账号并完成实名认证',
                    '在 CDN 控制台添加域名',
                    '配置 CNAME 记录',
                    '设置缓存规则',
                    '获取 AccessKey',
                    '在 FastBlog 中配置阿里云 CDN'
                ],
                'code_example': '''
# Python 示例 (aliyun-python-sdk-cdn)
from aliyunsdkcdn.request.v20180510 import RefreshObjectCachesRequest
from aliyunsdkcore.client import AcsClient

client = AcsClient('<accessKeyId>', '<accessSecret>', 'cn-hangzhou')
request = RefreshObjectCachesRequest.RefreshObjectCachesRequest()
request.set_ObjectPath('https://example.com/image.jpg')
request.set_ObjectType('File')
response = client.do_action_with_exception(request)
                '''.strip()
            }
        }
    )


@router.get("/providers/comparison", summary="CDN 提供商对比")
async def compare_cdn_providers():
    """
    对比主流 CDN 提供商的特性、价格和性能
    """
    return ApiResponse(
        success=True,
        data={
            'providers': [
                {
                    'name': 'Cloudflare',
                    'type': 'global',
                    'free_tier': True,
                    'pricing': '免费 + 付费计划 ($20/月起)',
                    'features': [
                        '全球 275+ 数据中心',
                        '免费 SSL 证书',
                        'DDoS 防护',
                        'WAF',
                        'Workers 边缘计算',
                        'Images 优化',
                        'Stream 视频服务'
                    ],
                    'pros': [
                        '友好的免费套餐',
                        '易于使用',
                        '强大的安全功能',
                        '优秀的文档'
                    ],
                    'cons': [
                        '免费版功能有限',
                        '中国境内速度一般',
                        '技术支持响应慢（免费版）'
                    ],
                    'best_for': '中小型网站、博客、初创企业'
                },
                {
                    'name': 'AWS CloudFront',
                    'type': 'global',
                    'free_tier': False,
                    'pricing': '按使用量付费',
                    'features': [
                        '全球 450+ PoP',
                        '与 AWS 生态深度集成',
                        'Lambda@Edge',
                        '实时日志',
                        '字段级加密',
                        '签名 URL/Cookie'
                    ],
                    'pros': [
                        '与 AWS 服务无缝集成',
                        '高度可定制',
                        '企业级可靠性',
                        '详细的监控和分析'
                    ],
                    'cons': [
                        '配置复杂',
                        '学习曲线陡峭',
                        '成本可能较高'
                    ],
                    'best_for': 'AWS 用户、大型企业、复杂应用'
                },
                {
                    'name': '阿里云 CDN',
                    'type': 'china-focused',
                    'free_tier': False,
                    'pricing': '按流量计费',
                    'features': [
                        '中国大陆 2300+ 节点',
                        '海外 500+ 节点',
                        '智能路由',
                        'HTTPS 加速',
                        '视频直播',
                        '全站加速 DCDN'
                    ],
                    'pros': [
                        '中国大陆速度极快',
                        '性价比高',
                        '完善的备案支持',
                        '本地化服务'
                    ],
                    'cons': [
                        '国际节点较少',
                        '需要实名认证',
                        '英文文档不够完善'
                    ],
                    'best_for': '面向中国用户的网站、电商、视频平台'
                },
                {
                    'name': '腾讯云 CDN',
                    'type': 'china-focused',
                    'free_tier': False,
                    'pricing': '按流量计费',
                    'features': [
                        '中国大陆 2000+ 节点',
                        '海外 800+ 节点',
                        'QUIC 协议支持',
                        '边缘计算 SCF',
                        '音视频处理',
                        '安全防护'
                    ],
                    'pros': [
                        '华南地区优势明显',
                        '与微信生态集成好',
                        '价格竞争力强',
                        '游戏行业优化'
                    ],
                    'cons': [
                        '国际覆盖不如 AWS',
                        '配置界面复杂',
                        '客服响应参差不齐'
                    ],
                    'best_for': '游戏、直播、社交应用、微信小程序'
                }
            ],
            'recommendation': {
                'small_blog': 'Cloudflare（免费且易用）',
                'china_business': '阿里云或腾讯云（国内速度快）',
                'global_enterprise': 'AWS CloudFront 或多云策略',
                'ecommerce': '根据目标市场选择（国内用阿里云，国际用 Cloudflare/AWS）',
                'media_streaming': '专业 CDN（如 Akamai、Fastly）或云服务提供商'
            }
        }
    )
