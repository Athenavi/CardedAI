"""
区域化部署最佳实践 API - V2 版本
提供全球各地区的部署指南、云服务配置和最佳实践
"""
from fastapi import APIRouter, Depends

from shared.models.user import User
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(prefix="/deployment", tags=["Regional Deployment"])


@router.get("/guide/{region}", summary="获取区域部署指南")
async def get_deployment_guide(
        region: str,
        current_user: User = Depends(jwt_required)
):
    """
    获取特定区域的详细部署指南
    
    参数:
    - region: 区域代码 (aws, azure, gcp, aliyun, tencent, digitalocean)
    
    返回该区域的完整部署步骤、配置示例和最佳实践
    """
    guides = {
        'aws': {
            'name': 'Amazon Web Services',
            'region_coverage': 'Global',
            'difficulty': 'Medium',
            'estimated_cost': '$50-200/month for small-medium sites',
            'steps': [
                {
                    'step': 1,
                    'title': '创建 AWS 账户',
                    'description': '注册 AWS 账户并设置账单提醒',
                    'url': 'https://aws.amazon.com/'
                },
                {
                    'step': 2,
                    'title': '选择区域',
                    'description': '选择离目标用户最近的 AWS 区域（如 us-east-1, eu-west-1, ap-northeast-1）',
                    'recommendation': '考虑延迟、数据主权和成本'
                },
                {
                    'step': 3,
                    'title': '设置 VPC',
                    'description': '创建虚拟私有云，配置子网和安全组',
                    'details': [
                        '创建公有和私有子网',
                        '配置 NAT Gateway',
                        '设置安全组规则（仅开放 80/443 端口）'
                    ]
                },
                {
                    'step': 4,
                    'title': '启动 EC2 实例',
                    'description': '选择合适的实例类型',
                    'recommendation': 't3.medium 或 t3.large 用于中小型博客',
                    'ami': 'Amazon Linux 2 或 Ubuntu Server'
                },
                {
                    'step': 5,
                    'title': '配置 RDS',
                    'description': '设置 PostgreSQL 数据库',
                    'details': [
                        '选择 db.t3.small 或 db.t3.medium',
                        '启用多可用区部署（生产环境）',
                        '配置自动备份',
                        '设置安全组仅允许 EC2 访问'
                    ]
                },
                {
                    'step': 6,
                    'title': '设置 ElastiCache',
                    'description': '配置 Redis 缓存',
                    'recommendation': 'cache.t3.micro 或 cache.t3.small'
                },
                {
                    'step': 7,
                    'title': '配置 S3',
                    'description': '设置对象存储用于媒体文件',
                    'details': [
                        '创建存储桶',
                        '配置 CORS',
                        '设置 CloudFront CDN',
                        '启用版本控制'
                    ]
                },
                {
                    'step': 8,
                    'title': '设置 Route 53',
                    'description': '配置 DNS 和域名',
                    'details': [
                        '注册或转移域名',
                        '创建 A 记录指向 EC2 或 ALB',
                        '配置 SSL 证书（Certificate Manager）'
                    ]
                },
                {
                    'step': 9,
                    'title': '部署应用',
                    'description': '使用 ECS、EKS 或直接部署到 EC2',
                    'options': [
                        'Docker + ECS（推荐）',
                        'Kubernetes + EKS（大规模）',
                        'EC2 + Supervisor（简单部署）'
                    ]
                },
                {
                    'step': 10,
                    'title': '监控和告警',
                    'description': '设置 CloudWatch 监控',
                    'details': [
                        'CPU、内存、磁盘监控',
                        '设置告警阈值',
                        '配置 SNS 通知',
                        '启用日志聚合'
                    ]
                }
            ],
            'terraform_example': '''
# main.tf
provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "fastblog" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  
  vpc_security_group_ids = [aws_security_group.fastblog_sg.id]
  
  tags = {
    Name = "FastBlog"
  }
}

resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "14"
  instance_class       = "db.t3.small"
  db_name              = "fastblog"
  username             = var.db_username
  password             = var.db_password
  
  skip_final_snapshot = true
}
            '''.strip(),
            'best_practices': [
                '使用 Auto Scaling Group 实现弹性扩缩容',
                '启用 CloudFront CDN 加速静态资源',
                '使用 Secrets Manager 管理敏感信息',
                '实施 Infrastructure as Code (Terraform/CloudFormation)',
                '定期备份和测试恢复流程',
                '使用 IAM Role 而非 Access Key',
                '启用 VPC Flow Logs 进行网络监控'
            ],
            'cost_optimization': [
                '使用 Spot Instances 降低计算成本',
                '购买 Reserved Instances（1年或3年）',
                '使用 S3 Intelligent-Tiering',
                '设置预算和成本告警',
                '定期清理未使用的资源'
            ]
        },
        'azure': {
            'name': 'Microsoft Azure',
            'region_coverage': 'Global',
            'difficulty': 'Medium',
            'estimated_cost': '$50-200/month for small-medium sites',
            'steps': [
                {
                    'step': 1,
                    'title': '创建 Azure 账户',
                    'description': '注册 Azure 账户，新用户有 $200 免费额度',
                    'url': 'https://azure.microsoft.com/'
                },
                {
                    'step': 2,
                    'title': '创建资源组',
                    'description': '将所有相关资源组织到一个资源组中',
                    'recommendation': '按环境分离（dev/staging/prod）'
                },
                {
                    'step': 3,
                    'title': '设置 Virtual Network',
                    'description': '配置虚拟网络和子网',
                    'details': [
                        '创建 VNet',
                        '配置子网',
                        '设置网络安全组（NSG）'
                    ]
                },
                {
                    'step': 4,
                    'title': '部署 Azure VM',
                    'description': '创建虚拟机',
                    'recommendation': 'Standard B2s 或 Standard B2ms',
                    'os': 'Ubuntu Server 20.04 LTS 或 CentOS'
                },
                {
                    'step': 5,
                    'title': '配置 Azure Database for PostgreSQL',
                    'description': '设置托管 PostgreSQL 服务',
                    'details': [
                        '选择 Basic 或 General Purpose 层级',
                        '配置防火墙规则',
                        '启用备份',
                        '设置高可用性（可选）'
                    ]
                },
                {
                    'step': 6,
                    'title': '设置 Azure Cache for Redis',
                    'description': '配置 Redis 缓存服务',
                    'recommendation': 'C0 或 C1 层级'
                },
                {
                    'step': 7,
                    'title': '配置 Azure Blob Storage',
                    'description': '设置对象存储',
                    'details': [
                        '创建存储账户',
                        '设置容器',
                        '配置 CDN（Azure CDN）',
                        '设置访问策略'
                    ]
                },
                {
                    'step': 8,
                    'title': '设置 Azure DNS',
                    'description': '配置域名解析',
                    'details': [
                        '创建 DNS 区域',
                        '添加 A 记录',
                        '配置 SSL 证书（App Service 或 Key Vault）'
                    ]
                },
                {
                    'step': 9,
                    'title': '部署应用',
                    'description': '使用 Azure App Service 或 Container Instances',
                    'options': [
                        'Azure App Service（PaaS，推荐）',
                        'Azure Kubernetes Service (AKS)',
                        'VM + Docker Compose'
                    ]
                },
                {
                    'step': 10,
                    'title': '监控和告警',
                    'description': '设置 Azure Monitor',
                    'details': [
                        '启用 Application Insights',
                        '配置指标告警',
                        '设置 Log Analytics',
                        '创建 Dashboard'
                    ]
                }
            ],
            'arm_template_note': '可以使用 ARM 模板或 Bicep 进行基础设施即代码部署',
            'best_practices': [
                '使用 Availability Zones 提高可用性',
                '实施 Azure Policy 进行治理',
                '使用 Managed Identity 代替服务主体',
                '启用 Azure Security Center',
                '定期审查成本管理建议',
                '使用 Azure DevOps 进行 CI/CD'
            ]
        },
        'gcp': {
            'name': 'Google Cloud Platform',
            'region_coverage': 'Global',
            'difficulty': 'Medium',
            'estimated_cost': '$40-180/month for small-medium sites',
            'steps': [
                {
                    'step': 1,
                    'title': '创建 GCP 项目',
                    'description': '在 Google Cloud Console 中创建新项目',
                    'url': 'https://cloud.google.com/'
                },
                {
                    'step': 2,
                    'title': '设置 VPC Network',
                    'description': '配置虚拟私有云网络',
                    'details': [
                        '创建 VPC',
                        '配置子网',
                        '设置防火墙规则'
                    ]
                },
                {
                    'step': 3,
                    'title': '创建 Compute Engine VM',
                    'description': '启动虚拟机实例',
                    'recommendation': 'e2-medium 或 e2-standard-2',
                    'image': 'Ubuntu 20.04 LTS 或 Debian 11'
                },
                {
                    'step': 4,
                    'title': '配置 Cloud SQL',
                    'description': '设置托管 PostgreSQL',
                    'details': [
                        '创建实例',
                        '选择机器类型（db-custom-1-3840）',
                        '配置备份',
                        '设置授权网络'
                    ]
                },
                {
                    'step': 5,
                    'title': '设置 Memorystore',
                    'description': '配置 Redis 缓存',
                    'recommendation': 'basic_tier, 1GB'
                },
                {
                    'step': 6,
                    'title': '配置 Cloud Storage',
                    'description': '设置对象存储',
                    'details': [
                        '创建存储桶',
                        '设置生命周期规则',
                        '配置 Cloud CDN',
                        '设置 IAM 权限'
                    ]
                },
                {
                    'step': 7,
                    'title': '设置 Cloud DNS',
                    'description': '配置域名系统',
                    'details': [
                        '创建托管区域',
                        '添加记录集',
                        '配置 SSL（Load Balancer 或 Certbot）'
                    ]
                },
                {
                    'step': 8,
                    'title': '部署应用',
                    'description': '使用 GKE 或 Cloud Run',
                    'options': [
                        'Google Kubernetes Engine (GKE)',
                        'Cloud Run（无服务器容器）',
                        'Compute Engine（传统 VM）'
                    ]
                },
                {
                    'step': 9,
                    'title': '监控和日志',
                    'description': '设置 Cloud Monitoring 和 Logging',
                    'details': [
                        '创建 Workspace',
                        '配置告警政策',
                        '设置 Dashboard',
                        '启用 Error Reporting'
                    ]
                }
            ],
            'best_practices': [
                '使用 Cloud Build 进行 CI/CD',
                '实施 Organization Policies',
                '使用 Service Accounts 最小权限原则',
                '启用 Security Command Center',
                '利用 Sustained Use Discounts',
                '使用 Terraform Provider for GCP'
            ]
        },
        'aliyun': {
            'name': '阿里云 (Alibaba Cloud)',
            'region_coverage': 'China-focused, Global presence',
            'difficulty': 'Easy-Medium',
            'estimated_cost': '¥300-1500/month for small-medium sites',
            'special_notes': [
                '需要完成 ICP 备案才能在中国大陆提供服务',
                '实名认证是必须的',
                '中国大陆节点速度最优'
            ],
            'steps': [
                {
                    'step': 1,
                    'title': '注册阿里云账号',
                    'description': '完成注册和实名认证',
                    'url': 'https://www.aliyun.com/',
                    'requirements': ['个人身份证或企业营业执照']
                },
                {
                    'step': 2,
                    'title': 'ICP 备案',
                    'description': '如果使用中国大陆节点，必须完成 ICP 备案',
                    'duration': '通常需要 7-20 个工作日',
                    'process': '通过阿里云备案系统提交申请'
                },
                {
                    'step': 3,
                    'title': '创建 VPC',
                    'description': '设置专有网络',
                    'details': [
                        '创建 VPC',
                        '划分交换机（子网）',
                        '配置路由表',
                        '设置安全组'
                    ]
                },
                {
                    'step': 4,
                    'title': '购买 ECS 实例',
                    'description': '创建云服务器',
                    'recommendation': 'ecs.t6.large 或 ecs.c6.large',
                    'os': 'CentOS 7.9、Ubuntu 20.04 或 Alibaba Cloud Linux'
                },
                {
                    'step': 5,
                    'title': '配置 RDS PostgreSQL',
                    'description': '设置云数据库',
                    'details': [
                        '选择实例规格（pg.n2.small.1）',
                        '设置存储空间',
                        '配置白名单',
                        '启用备份'
                    ]
                },
                {
                    'step': 6,
                    'title': '设置 KVStore for Redis',
                    'description': '配置云缓存 Redis',
                    'recommendation': '社区版 1GB'
                },
                {
                    'step': 7,
                    'title': '配置 OSS',
                    'description': '设置对象存储',
                    'details': [
                        '创建 Bucket',
                        '设置读写权限',
                        '配置 CDN 加速',
                        '设置防盗链'
                    ]
                },
                {
                    'step': 8,
                    'title': '配置域名和 SSL',
                    'description': '设置域名解析和 HTTPS',
                    'details': [
                        '在阿里云注册或转入域名',
                        '配置 DNS 解析',
                        '申请免费 SSL 证书',
                        '绑定到负载均衡或 CDN'
                    ]
                },
                {
                    'step': 9,
                    'title': '部署应用',
                    'description': '部署 FastBlog 应用',
                    'options': [
                        'ECS + Docker Compose',
                        '容器服务 ACK（Kubernetes）',
                        '函数计算 FC（无服务器）'
                    ]
                },
                {
                    'step': 10,
                    'title': '监控和告警',
                    'description': '设置云监控',
                    'details': [
                        '安装云监控插件',
                        '设置报警规则',
                        '配置联系人',
                        '查看监控Dashboard'
                    ]
                }
            ],
            'best_practices': [
                '使用 RAM 用户而非主账号',
                '启用操作审计（ActionTrail）',
                '使用资源编排服务 ROS（类似 Terraform）',
                '配置 DDoS 基础防护',
                '使用 WAF 保护 Web 应用',
                '定期快照备份 ECS',
                '利用阿里云优惠活动和预付费套餐'
            ],
            'compliance': [
                '完成 ICP 备案',
                '公安联网备案',
                '遵守《网络安全法》',
                '数据存储在中国境内',
                '内容审核机制'
            ]
        }
    }

    guide = guides.get(region)
    if not guide:
        return ApiResponse(
            success=False,
            error=f"不支持的区域: {region}。支持的区域: {', '.join(guides.keys())}"
        )

    return ApiResponse(
        success=True,
        data=guide
    )


@router.get("/comparison", summary="云平台对比")
async def compare_cloud_providers():
    """
    对比主流云服务提供商的特性、价格和适用场景
    """
    return ApiResponse(
        success=True,
        data={
            'title': '主流云平台对比',
            'providers': [
                {
                    'name': 'AWS',
                    'strengths': [
                        '最全面的云服务',
                        '全球覆盖最广',
                        '成熟的生态系统',
                        '丰富的文档和社区'
                    ],
                    'weaknesses': [
                        '学习曲线陡峭',
                        '定价复杂',
                        '控制台界面复杂'
                    ],
                    'best_for': '大型企业、全球化应用、复杂架构',
                    'pricing_model': '按使用量付费，预留实例折扣'
                },
                {
                    'name': 'Azure',
                    'strengths': [
                        '与 Microsoft 生态集成好',
                        '混合云解决方案强',
                        '企业级支持',
                        'Active Directory 集成'
                    ],
                    'weaknesses': [
                        '某些服务不如 AWS 成熟',
                        '文档质量参差不齐',
                        '价格相对较高'
                    ],
                    'best_for': 'Microsoft 技术栈、企业客户、混合云',
                    'pricing_model': '按使用量付费，预留实例折扣'
                },
                {
                    'name': 'GCP',
                    'strengths': [
                        'Kubernetes 原生支持',
                        '数据分析和 AI/ML 能力强',
                        '网络性能优秀',
                        '定价透明简单'
                    ],
                    'weaknesses': [
                        '服务数量相对较少',
                        '企业支持不如 AWS/Azure',
                        '部分地区覆盖有限'
                    ],
                    'best_for': '数据驱动应用、AI/ML 工作负载、初创公司',
                    'pricing_model': '持续使用折扣，承诺使用折扣'
                },
                {
                    'name': '阿里云',
                    'strengths': [
                        '中国大陆速度最快',
                        '本地化服务好',
                        '性价比高',
                        '完整的备案支持'
                    ],
                    'weaknesses': [
                        '国际节点较少',
                        '英文文档不够完善',
                        '需要实名认证'
                    ],
                    'best_for': '面向中国用户的业务、电商、直播',
                    'pricing_model': '按量付费、包年包月、抢占式实例'
                }
            ],
            'selection_criteria': [
                '目标用户地理位置',
                '预算和成本预期',
                '技术栈兼容性',
                '合规性要求',
                '团队熟悉度',
                '支持和服务质量'
            ]
        }
    )


@router.get("/checklist", summary="部署检查清单")
async def get_deployment_checklist():
    """
    获取完整的部署前检查清单
    
    确保所有必要的配置和安全措施都已到位
    """
    return ApiResponse(
        success=True,
        data={
            'title': '部署前检查清单',
            'categories': [
                {
                    'category': '基础设施',
                    'items': [
                        '✓ 选择合适的云平台和区域',
                        '✓ 配置 VPC/虚拟网络',
                        '✓ 设置安全组和防火墙规则',
                        '✓ 配置负载均衡器（如需要）',
                        '✓ 设置域名和 DNS',
                        '✓ 申请和配置 SSL 证书'
                    ]
                },
                {
                    'category': '数据库',
                    'items': [
                        '✓ 选择数据库引擎和版本',
                        '✓ 配置数据库实例规格',
                        '✓ 设置备份策略',
                        '✓ 配置连接池',
                        '✓ 设置访问控制和白名单',
                        '✓ 启用慢查询日志'
                    ]
                },
                {
                    'category': '应用配置',
                    'items': [
                        '✓ 设置环境变量',
                        '✓ 配置 SECRET_KEY',
                        '✓ 设置数据库连接字符串',
                        '✓ 配置 Redis 连接',
                        '✓ 设置邮件服务',
                        '✓ 配置文件存储（S3/OSS等）'
                    ]
                },
                {
                    'category': '安全',
                    'items': [
                        '✓ 更新系统和依赖包',
                        '✓ 禁用 root SSH 登录',
                        '✓ 配置 SSH 密钥认证',
                        '✓ 设置 fail2ban',
                        '✓ 启用防火墙',
                        '✓ 配置速率限制',
                        '✓ 设置 CORS 策略',
                        '✓ 启用 HTTPS 强制跳转'
                    ]
                },
                {
                    'category': '监控',
                    'items': [
                        '✓ 安装监控代理',
                        '✓ 配置 CPU/内存/磁盘告警',
                        '✓ 设置应用性能监控',
                        '✓ 配置日志聚合',
                        '✓ 设置错误追踪',
                        '✓ 配置 uptime 监控'
                    ]
                },
                {
                    'category': '备份',
                    'items': [
                        '✓ 配置数据库自动备份',
                        '✓ 设置文件备份策略',
                        '✓ 测试恢复流程',
                        '✓ 配置备份保留策略',
                        '✓ 设置异地备份'
                    ]
                },
                {
                    'category': '性能优化',
                    'items': [
                        '✓ 启用 Gzip/Brotli 压缩',
                        '✓ 配置浏览器缓存',
                        '✓ 设置 CDN',
                        '✓ 优化图片',
                        '✓ 启用 HTTP/2',
                        '✓ 配置数据库索引'
                    ]
                },
                {
                    'category': '合规性',
                    'items': [
                        '✓ 隐私政策页面',
                        '✓ Cookie 同意横幅',
                        '✓ GDPR/CCPA 合规检查',
                        '✓ ICP 备案（如在中国）',
                        '✓ 数据保留策略',
                        '✓ 用户数据导出功能'
                    ]
                }
            ]
        }
    )
