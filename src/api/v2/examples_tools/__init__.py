"""
统一示例和工具端点 - V2版本
集中管理所有模块的示例和工具端点，避免分散在各个模块中
"""
from fastapi import APIRouter

from src.api.v1.core.responses import ApiResponse

router = APIRouter(tags=["examples-tools"])


@router.get("/accessibility", summary="无障碍性审计示例", description="获取无障碍性审计使用示例")
async def get_accessibility_examples():
    """获取使用示例"""
    examples = {
        "single_page_audit": {
            'description': '单页审计',
            'example': '''
    POST /api/v1/accessibility/audit
    {
      "html_content": "<html><body>...</body></html>",
      "url": "https://example.com/page",
      "level": "AA"
    }
                '''.strip()
        },
        "batch_audit": {
            'description': '批量审计',
            'example': '''
    POST /api/v1/accessibility/audit/batch
    {
      "pages": [
        {"url": "/", "html": "<html>...</html>"},
        {"url": "/about", "html": "<html>...</html>"},
        {"url": "/contact", "html": "<html>...</html>"}
      ],
      "level": "AA"
    }
                '''.strip()
        },
        "frontend_integration": {
            'description': '前端集成',
            'code_example': '''
    // React组件示例
    function AccessibilityChecker({ html }) {
      const [report, setReport] = useState(null);

      useEffect(() => {
        fetch('/api/v1/accessibility/audit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            html_content: html,
            level: 'AA',
          })
        })
        .then(res => res.json())
        .then(data => setReport(data.data));
      }, [html]);

      if (!report) return null;

      return (
        <div className="a11y-report">
          <h3>无障碍性评分: {report.summary.score}/100</h3>
          <span className="grade">{report.summary.grade}</span>

          <div className="violations">
            <h4>发现的问题 ({report.summary.violations})</h4>
            <ul>
              {report.violations.map((violation, index) => (
                <li key={index}>
                  <strong>{violation.rule_name}</strong>: {violation.message}
                  <p>建议: {violation.recommendation}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      );
    }
                '''.strip()
        },
        "best_practices": {
            'description': '最佳实践',
            'practices': [
                '在开发过程中定期进行无障碍性审计',
                '将无障碍性测试集成到CI/CD流程',
                '使用自动化工具和手动测试相结合',
                '邀请残障用户进行真实测试',
                '遵循渐进增强原则',
                '使用语义化HTML',
                '提供多种导航方式',
                '确保足够的颜色对比度',
                '测试键盘导航',
                '验证屏幕阅读器兼容性',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/performance", summary="性能优化示例", description="获取性能优化相关示例")
async def get_performance_examples():
    """获取性能优化相关的使用示例"""
    examples = {
        "page_cache": {
            "description": "页面缓存配置示例",
            "endpoint": "/api/v2/performance/cache/page",
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "examples": [
                {
                    "action": "启用页面缓存",
                    "method": "POST",
                    "body": {
                        "enabled": True,
                        "ttl": 3600,
                        "exclude_patterns": ["/admin/*", "/api/*"]
                    }
                },
                {
                    "action": "清除特定页面缓存",
                    "method": "DELETE",
                    "body": {
                        "urls": ["/home", "/about"]
                    }
                }
            ]
        },
        "object_cache": {
            "description": "对象缓存示例",
            "endpoint": "/api/v2/performance/cache/object",
            "methods": ["GET", "POST", "DELETE"],
            "examples": [
                {
                    "action": "缓存数据库查询结果",
                    "method": "POST",
                    "body": {
                        "key": "user_profile_123",
                        "value": {"name": "John Doe", "email": "john@example.com"},
                        "ttl": 1800
                    }
                }
            ]
        },
        "image_optimization": {
            "description": "图片优化示例",
            "endpoint": "/api/v2/performance/images/optimize",
            "methods": ["POST"],
            "examples": [
                {
                    "action": "优化上传图片",
                    "method": "POST",
                    "form_data": {
                        "file": "<binary>",
                        "quality": 85,
                        "max_width": 1920,
                        "format": "webp"
                    }
                }
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples,
        message="性能优化示例获取成功"
    )


@router.get("/security", summary="安全功能示例", description="获取安全相关功能示例")
async def get_security_examples():
    """获取安全相关功能的使用示例"""
    examples = {
        "security_scan": {
            "description": "安全扫描示例",
            "endpoint": "/api/v2/security/scan",
            "methods": ["POST"],
            "examples": [
                {
                    "action": "执行全面安全扫描",
                    "method": "POST",
                    "body": {
                        "scan_types": ["sql_injection", "xss", "csrf", "headers"],
                        "target_urls": ["https://example.com"]
                    }
                }
            ]
        },
        "firewall_rules": {
            "description": "防火墙规则管理示例",
            "endpoint": "/api/v2/security/firewall/rules",
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "examples": [
                {
                    "action": "添加IP黑名单",
                    "method": "POST",
                    "body": {
                        "rule_type": "ip_blacklist",
                        "value": "192.168.1.100",
                        "reason": "恶意访问"
                    }
                }
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples,
        message="安全功能示例获取成功"
    )


@router.get("/seo", summary="SEO优化示例", description="获取SEO优化相关示例")
async def get_seo_examples():
    """获取SEO优化相关的使用示例"""
    examples = {
        "meta_tags": {
            "description": "元标签优化示例",
            "endpoint": "/api/v2/seo/meta-tags",
            "methods": ["GET", "POST", "PUT"],
            "examples": [
                {
                    "action": "设置页面元标签",
                    "method": "POST",
                    "body": {
                        "url": "/articles/1",
                        "title": "文章标题 - 网站名称",
                        "description": "文章描述...",
                        "keywords": ["关键词1", "关键词2"]
                    }
                }
            ]
        },
        "sitemap_generation": {
            "description": "站点地图生成示例",
            "endpoint": "/api/v2/seo/sitemap/generate",
            "methods": ["POST"],
            "examples": [
                {
                    "action": "生成站点地图",
                    "method": "POST",
                    "body": {
                        "include_articles": True,
                        "include_categories": True,
                        "include_tags": True,
                        "lastmod_frequency": "daily"
                    }
                }
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples,
        message="SEO优化示例获取成功"
    )


@router.get("/nlp", summary="自然语言处理示例", description="获取NLP功能示例")
async def get_nlp_examples():
    """获取自然语言处理功能的使用示例"""
    examples = {
        "content_analysis": {
            "description": "内容分析示例",
            "endpoint": "/api/v2/nlp/analyze",
            "methods": ["POST"],
            "examples": [
                {
                    "action": "分析文章内容",
                    "method": "POST",
                    "body": {
                        "text": "要分析的文本内容...",
                        "analysis_types": ["sentiment", "keywords", "summary"]
                    }
                }
            ]
        },
        "auto_tagging": {
            "description": "自动标签生成示例",
            "endpoint": "/api/v2/nlp/auto-tag",
            "methods": ["POST"],
            "examples": [
                {
                    "action": "为文章自动生成标签",
                    "method": "POST",
                    "body": {
                        "article_id": 123,
                        "max_tags": 5,
                        "confidence_threshold": 0.7
                    }
                }
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples,
        message="NLP功能示例获取成功"
    )


@router.get("/collaboration", summary="协作功能示例", description="获取协作功能示例")
async def get_collaboration_examples():
    """获取协作功能的使用示例"""
    examples = {
        "team_comments": {
            "description": "团队评论协作示例",
            "endpoint": "/api/v2/collaboration/comments",
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "examples": [
                {
                    "action": "创建团队评论",
                    "method": "POST",
                    "body": {
                        "article_id": 123,
                        "content": "评论内容",
                        "mentions": ["user1", "user2"],
                        "priority": "high"
                    }
                }
            ]
        },
        "document_sharing": {
            "description": "文档共享示例",
            "endpoint": "/api/v2/collaboration/share",
            "methods": ["POST"],
            "examples": [
                {
                    "action": "共享文档给团队成员",
                    "method": "POST",
                    "body": {
                        "document_id": 456,
                        "users": ["user1@example.com", "user2@example.com"],
                        "permissions": ["read", "comment"]
                    }
                }
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples,
        message="协作功能示例获取成功"
    )


@router.get("/http2", summary="http2使用示例", description="获取HTTP/2配置使用示例")
async def get_http2_examples():
    """获取使用示例"""
    examples = {
        "enable_http2": {
            'description': '启用HTTP/2',
            'steps': [
                '1. 确保使用HTTPS（HTTP/2需要TLS）',
                '2. 升级Web服务器到支持HTTP/2的版本',
                '3. 在服务器配置中启用HTTP/2',
                '4. 重启Web服务器',
                '5. 测试HTTP/2连接',
            ],
            'test_command': 'curl -I --http2 https://your-domain.com',
        },
        "enable_http3": {
            'description': '启用HTTP/3 (QUIC)',
            'steps': [
                '1. 确保UDP端口443开放',
                '2. 使用支持HTTP/3的Web服务器（Nginx 1.25+）',
                '3. 配置QUIC证书',
                '4. 添加Alt-Svc头',
                '5. 测试HTTP/3连接',
            ],
            'test_command': 'curl -I --http3 https://your-domain.com',
        },
        "server_push": {
            'description': '配置服务器推送',
            'nginx_example': '''
location / {
    add_header Link "</css/style.css>; rel=preload; as=style";
    add_header Link "</js/app.js>; rel=preload; as=script";
    add_header Link "</fonts/main.woff2>; rel=preload; as=font; crossorigin";
}
            '''.strip(),
            'recommendations': [
                '只推送关键资源',
                '避免推送过多文件',
                '监控推送效果',
            ]
        },
        "monitoring": {
            'description': '监控HTTP/2性能',
            'metrics': [
                'HTTP/2连接数',
                '并发流数量',
                '服务器推送命中率',
                'TLS握手时间',
                '页面加载时间',
            ],
            'tools': [
                'Chrome DevTools Network面板',
                'nghttp工具',
                'h2load压力测试',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/loginLog", summary="使用示例", description="获取异常行为检测使用示例")
async def get_loginlog_examples():
    """获取使用示例"""
    examples = {
        "integration": {
            'description': '与认证系统集成',
            'code_example': '''
from shared.services.anomaly_detector import anomaly_detector

# 在登录接口中记录登录尝试
@app.post("/login")
async def login(request: LoginRequest):
    try:
        user = authenticate(request.username, request.password)

        # 记录成功登录
        anomaly_detector.record_login_attempt(
            ip_address=request.client.host,
            username=request.username,
            success=True
        )

        return {"token": generate_token(user)}
    except AuthenticationError:
        # 记录失败登录
        anomaly_detector.record_login_attempt(
            ip_address=request.client.host,
            username=request.username,
            success=False
        )
        raise
            '''.strip()
        },
        "middleware_integration": {
            'description': '中间件集成 - 记录访问',
            'code_example': '''
from shared.services.anomaly_detector import anomaly_detector

@app.middleware("http")
async def access_monitor_middleware(request: Request, call_next):
    # 记录访问
    anomaly_detector.record_access(
        ip_address=request.client.host
    )

    response = await call_next(request)
    return response
            '''.strip()
        },
        "detection_types": {
            'description': '检测类型说明',
            'types': [
                {
                    'type': 'brute_force',
                    'description': '暴力破解检测',
                    'trigger': '同一IP在1小时内失败登录超过阈值',
                    'severity': 'high',
                },
                {
                    'type': 'unusual_time_login',
                    'description': '非正常时间登录',
                    'trigger': '用户在深夜或凌晨登录',
                    'severity': 'medium',
                },
                {
                    'type': 'large_data_export',
                    'description': '大量数据导出',
                    'trigger': '用户导出数据超过阈值',
                    'severity': 'high',
                },
                {
                    'type': 'rate_abuse',
                    'description': '速率滥用',
                    'trigger': '同一IP在1分钟内请求过多',
                    'severity': 'medium',
                },
            ]
        },
        "response_actions": {
            'description': '检测到异常后的响应措施',
            'actions': [
                '发送告警通知（邮件/短信）',
                '临时封禁IP地址',
                '要求二次验证',
                '冻结可疑账户',
                '记录详细日志供后续分析',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/translate", summary="使用示例", description="获取翻译进度跟踪使用示例")
async def get_translate_examples():
    """获取使用示例"""
    examples = {
        "workflow": {
            'description': '翻译工作流程',
            'steps': [
                '1. 初始化语言文件，注册所有翻译键',
                '2. 翻译者开始翻译，调用 /register 接口',
                '3. 实时查看进度 /progress/{language_code}',
                '4. 查看贡献者统计 /contributors',
                '5. 生成完整报告 /report',
            ]
        },
        "integration": {
            'description': '与翻译系统集成',
            'code_example': '''
from shared.services.translation_progress import translation_tracker

# 注册翻译项
def on_translation_complete(language_code, key, translator_id, translator_name):
    translation_tracker.register_translation(
        language_code=language_code,
        translation_key=key,
        is_translated=True,
        translator_id=translator_id,
        translator_name=translator_name,
    )

# 获取进度
progress = translation_tracker.get_language_progress('zh')
print(f"中文翻译进度: {progress['progress_percentage']}%")
            '''.strip()
        },
        "dashboard": {
            'description': '仪表板展示建议',
            'components': [
                '总体进度环形图',
                '各语言进度条形图',
                'Top 10贡献者列表',
                '未翻译字符串列表',
                '最近活动日志',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/translate/export", summary="使用示例", description="获取翻译导出导入使用示例")
async def get_translate_export_examples():
    """获取使用示例"""
    examples = {
        "export_single": {
            'description': '导出单个语言',
            'example': '''
# 导出为JSON
GET /api/v1/translation/export/zh-CN?format=json

# 导出为YAML
GET /api/v1/translation/export/zh-CN?format=yaml

# 导出为PO
GET /api/v1/translation/export/zh-CN?format=po
            '''.strip()
        },
        "export_batch": {
            'description': '批量导出',
            'example': '''
POST /api/v1/translation/export/all
Content-Type: application/json

{
  "format": "json"
}

# 返回所有语言的导出文件
            '''.strip()
        },
        "import_single": {
            'description': '导入单个文件',
            'example': '''
POST /api/v1/translation/import/zh-CN
Content-Type: multipart/form-data

file: zh-CN.json
            '''.strip()
        },
        "import_batch": {
            'description': '批量导入',
            'example': '''
POST /api/v1/translation/import/batch?format=json
Content-Type: multipart/form-data

files: [zh-CN.json, en-US.json, ja-JP.json]
            '''.strip()
        },
        "file_formats": {
            'description': '文件格式说明',
            'formats': {
                'JSON': {
                    'structure': {
                        'language': '语言代码',
                        'exported_at': '导出时间',
                        'total_strings': '字符串总数',
                        'translations': {
                            'key': {
                                'translation': '翻译内容',
                                'translated': '是否已翻译'
                            }
                        }
                    }
                },
                'YAML': '与JSON结构相同，但使用YAML语法',
                'PO': '标准Gettext PO格式，包含msgid和msgstr',
            }
        },
        "best_practices": {
            'description': '最佳实践',
            'practices': [
                '定期导出备份翻译文件',
                '使用版本控制系统管理翻译文件',
                '导入前先在测试环境验证',
                '保持翻译键的一致性',
                '为翻译人员提供清晰的上下文说明',
                '使用自动化脚本定期检查未翻译的字符串',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/automated_reports", summary="使用示例", description="获取安全报告使用示例")
async def get_automated_reports_examples():
    """获取使用示例"""
    examples = {
        "automated_reports": {
            'description': '自动化报告生成',
            'code_example': '''
from shared.services.security_report import report_generator
from shared.services.anomaly_detector import anomaly_detector
from shared.services.security_alert import security_alert_service
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 定时任务调度器
scheduler = AsyncIOScheduler()

# 每天凌晨生成日报
async def daily_report_job():
    anomalies = anomaly_detector.get_anomalies(hours=24)
    alerts = security_alert_service.get_alert_history(hours=24)

    report = report_generator.generate_daily_report(
        anomalies=anomalies,
        alerts=alerts,
        audit_logs=[]
    )

    # 发送邮件报告
    await send_report_email(report)

# 每周一生成周报
async def weekly_report_job():
    anomalies = anomaly_detector.get_anomalies(hours=168)
    alerts = security_alert_service.get_alert_history(hours=168)

    report = report_generator.generate_weekly_report(
        anomalies=anomalies,
        alerts=alerts,
        audit_logs=[]
    )

    await send_report_email(report)

# 配置调度
scheduler.add_job(daily_report_job, 'cron', hour=0, minute=0)
scheduler.add_job(weekly_report_job, 'cron', day_of_week='mon', hour=0, minute=0)
scheduler.start()
            '''.strip()
        },
        "report_structure": {
            'description': '报告结构说明',
            'daily_report': {
                'sections': [
                    '摘要：今日安全事件总数',
                    '异常事件：按类型和严重程度分类',
                    '告警统计：发送成功率和渠道分布',
                    'Top操作：最常见的管理操作',
                    '建议：针对性的改进建议',
                ]
            },
            'weekly_report': {
                'sections': [
                    '摘要：本周安全概况',
                    '趋势分析：每日事件变化',
                    '异常汇总：类型和严重程度分布',
                    '告警汇总：发送统计',
                    '对比分析：与上周对比',
                    '建议：本周改进建议',
                ]
            },
            'monthly_report': {
                'sections': [
                    '摘要：本月安全总结',
                    '趋势分析：每周事件变化',
                    '安全评分：综合安全评分和等级',
                    '异常汇总：详细统计分析',
                    '告警汇总：渠道效果评估',
                    '建议：长期改进策略',
                ]
            }
        },
        "integration_tips": {
            'description': '集成建议',
            'tips': [
                '将报告发送到管理层邮箱',
                '在仪表板展示安全评分',
                '设置阈值自动触发详细报告',
                '定期审查报告中的建议并执行',
                '保存历史报告用于趋势分析',
                '结合业务指标评估安全措施效果',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/email_alert", summary="使用示例", description="获取安全告警使用示例")
async def get_email_alert_examples():
    """获取使用示例"""
    examples = {
        "setup_email": {
            'description': '配置邮件告警',
            'code_example': '''
from shared.services.security_alert import security_alert_service, EmailAlertChannel

# 添加邮件渠道
channel = EmailAlertChannel(
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    username='your-email@gmail.com',
    password='your-app-password',
    from_email='your-email@gmail.com',
    to_emails=['admin@example.com', 'security@example.com'],
    use_tls=True
)

security_alert_service.add_channel('email_primary', channel)

# 添加告警规则
security_alert_service.add_rule(
    rule_id='brute_force_email',
    alert_type='brute_force',
    severity='high',
    channels=['email_primary'],
    enabled=True
)
            '''.strip()
        },
        "setup_webhook": {
            'description': '配置Webhook告警（如Slack、钉钉）',
            'code_example': '''
from shared.services.security_alert import security_alert_service, WebhookAlertChannel

# Slack Webhook
slack_channel = WebhookAlertChannel(
    webhook_url='https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
    headers={'Content-Type': 'application/json'}
)

security_alert_service.add_channel('slack_security', slack_channel)

# 添加规则
security_alert_service.add_rule(
    rule_id='all_critical_slack',
    alert_type='*',  # 所有类型
    severity='critical',
    channels=['slack_security'],
    enabled=True
)
            '''.strip()
        },
        "integration_with_anomaly": {
            'description': '与异常检测集成',
            'code_example': '''
from shared.services.anomaly_detector import anomaly_detector
from shared.services.security_alert import security_alert_service

# 在检测到异常时自动发送告警
def on_anomaly_detected(anomaly):
    import asyncio

    asyncio.create_task(security_alert_service.send_alert(
        alert_type=anomaly['type'],
        title=anomaly['title'],
        message=anomaly['message'],
        severity=anomaly['severity'],
        details=anomaly.get('details', {})
    ))

# 注册回调
# （实际实现中需要在anomaly_detector中添加回调机制）
            '''.strip()
        },
        "best_practices": {
            'description': '最佳实践',
            'practices': [
                '为不同严重程度配置不同的告警渠道',
                'Critical级别同时发送邮件和短信',
                'High级别发送邮件和Webhook',
                'Medium级别只发送邮件',
                '设置合理的频率限制避免告警风暴',
                '定期审查告警历史，优化规则',
                '测试告警渠道确保正常工作',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/slow_query", summary="使用示例", description="获取慢查询日志使用示例")
async def get_slow_query_examples():
    """获取使用示例"""
    examples = {
        "middleware_integration": {
            "description": "中间件集成 - 自动记录慢查询",
            "code": '''
from shared.services.slow_query_logger import slow_query_logger
import time

@app.middleware("http")
async def query_monitor_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # 如果响应时间超过阈值，记录为慢查询
    if duration > slow_query_logger.threshold:
        slow_query_logger.log_query(
            sql=f"HTTP {request.method} {request.url.path}",
            duration=duration,
            table='http_request',
            query_type='HTTP'
        )

    return response
            '''.strip()
        },
        "database_integration": {
            "description": "数据库集成 - 记录SQL慢查询",
            "code": '''
from shared.services.slow_query_logger import slow_query_logger
from sqlalchemy import event
from sqlalchemy.engine import Engine

# SQLAlchemy事件监听
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)

    # 记录慢查询
    if total > slow_query_logger.threshold:
        slow_query_logger.log_query(
            sql=statement,
            duration=total,
            query_type=statement.split()[0].upper() if statement else None
        )
            '''.strip()
        },
        "analyze_and_optimize": {
            "description": "分析和优化流程",
            "steps": [
                "1. 查看慢查询日志 (/api/v1/slow-query/logs)",
                "2. 获取统计信息 (/api/v1/slow-query/statistics)",
                "3. 查看优化建议 (/api/v1/slow-query/suggestions)",
                "4. 根据建议添加索引或优化查询",
                "5. 监控优化效果",
            ]
        },
        "common_optimizations": {
            "description": "常见优化方法",
            "optimizations": [
                {
                    'problem': '全表扫描',
                    'solution': '添加WHERE条件或使用LIMIT',
                },
                {
                    'problem': '缺少索引',
                    'solution': '为WHERE和JOIN字段添加索引',
                },
                {
                    'problem': 'SELECT *',
                    'solution': '明确指定需要的列',
                },
                {
                    'problem': 'N+1查询',
                    'solution': '使用预加载或批量查询',
                },
                {
                    'problem': '重复查询',
                    'solution': '使用缓存存储查询结果',
                },
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/performance_observer", summary="使用示例", description="获取性能追踪使用示例")
async def get_performance_observer_examples():
    """获取使用示例"""
    examples = {
        "frontend_integration": {
            'description': '前端集成示例',
            'code': '''
// 在页面加载完成后发送性能数据
window.addEventListener('load', () => {
  setTimeout(() => {
    const perfData = window.performance.timing;
    const paintEntries = performance.getEntriesByType('paint');

    // Core Web Vitals
    let fcp = 0, lcp = 0, fid = 0, cls = 0;

    // 获取FCP
    const fcpEntry = paintEntries.find(entry => entry.name === 'first-contentful-paint');
    if (fcpEntry) {
      fcp = fcpEntry.startTime;
    }

    // 获取LCP（需要PerformanceObserver）
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries.length > 0) {
        lcp = entries[entries.length - 1].startTime;
      }
    }).observe({ type: 'largest-contentful-paint', buffered: true });

    // 获取FID
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries.length > 0) {
        fid = entries[0].processingStart - entries[0].startTime;
      }
    }).observe({ type: 'first-input', buffered: true });

    // 获取CLS
    let clsValue = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      }
    }).observe({ type: 'layout-shift', buffered: true });

    // 发送数据
    fetch('/api/v1/performance/record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: window.location.href,
        user_agent: navigator.userAgent,
        load_time: perfData.loadEventEnd - perfData.navigationStart,
        dom_content_loaded: perfData.domContentLoadedEventEnd - perfData.navigationStart,
        first_paint: paintEntries[0]?.startTime || 0,
        fcp: fcp,
        lcp: lcp,
        fid: fid,
        cls: clsValue,
      })
    });
  }, 0);
});
            '''.strip()
        },
        "core_web_vitals": {
            'description': 'Core Web Vitals标准',
            'metrics': {
                'FCP (First Contentful Paint)': {
                    'good': '< 1.8s',
                    'needs_improvement': '1.8s - 3.0s',
                    'poor': '> 3.0s',
                    'description': '首次内容绘制时间',
                },
                'LCP (Largest Contentful Paint)': {
                    'good': '< 2.5s',
                    'needs_improvement': '2.5s - 4.0s',
                    'poor': '> 4.0s',
                    'description': '最大内容绘制时间',
                },
                'FID (First Input Delay)': {
                    'good': '< 100ms',
                    'needs_improvement': '100ms - 300ms',
                    'poor': '> 300ms',
                    'description': '首次输入延迟',
                },
                'CLS (Cumulative Layout Shift)': {
                    'good': '< 0.1',
                    'needs_improvement': '0.1 - 0.25',
                    'poor': '> 0.25',
                    'description': '累积布局偏移',
                },
            }
        },
        "monitoring_dashboard": {
            'description': '监控仪表板',
            'features': [
                '实时显示页面平均加载时间',
                'Core Web Vitals达标率',
                '最慢页面排行榜',
                '性能趋势图表',
                '设备和浏览器分布',
                '性能告警通知',
            ]
        },
        "optimization_tips": {
            'description': '优化建议',
            'tips': [
                '图片优化：使用WebP格式、懒加载、适当尺寸',
                '代码分割：按需加载JavaScript模块',
                '缓存策略：合理设置Cache-Control头',
                'CDN加速：静态资源使用CDN分发',
                '减少重排：避免频繁的DOM操作',
                '压缩资源：启用Gzip/Brotli压缩',
                '预加载关键资源：使用preload和prefetch',
                '优化字体加载：使用font-display: swap',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/obj_opt", summary="使用示例", description="获取资源优化使用示例")
async def get_obj_opt_examples():
    """获取使用示例"""
    examples = {
        "cache_single_object": {
            "description": "缓存单个对象",
            "code": '''
from shared.services.object_cache import object_cache_service

# 缓存文章对象
await object_cache_service.set_object(
    model_name="Article",
    object_id=article_id,
    data=article_data,
    ttl=600,
    tags=["article", f"article:{article_id}"]
)

# 获取缓存
cached = await object_cache_service.get_object("Article", article_id)
            '''.strip()
        },
        "cache_query_result": {
            "description": "缓存查询结果",
            "code": '''
# 缓存文章列表查询
await object_cache_service.set_query_result(
    query_type="article_list",
    params={"category_id": 1, "page": 1},
    data=articles_list,
    ttl=300,
    tags=["article_list", "category:1"]
)

# 获取缓存
cached = await object_cache_service.get_query_result(
    "article_list",
    {"category_id": 1, "page": 1}
)
            '''.strip()
        },
        "invalidate_on_update": {
            "description": "更新时清除缓存",
            "code": '''
async def update_article(article_id: int, data: dict):
    # 更新数据库
    await db.update(...)

    # 清除相关缓存
    await object_cache_service.invalidate_by_tag(f"article:{article_id}")
    await object_cache_service.invalidate_by_tag("article_list")
            '''.strip()
        },
        "use_decorator": {
            "description": "使用装饰器自动缓存",
            "code": '''
from shared.services.object_cache import object_cache_service

@object_cache_service.cache_object(
    model_name="Article",
    ttl=600,
    tags=["article"]
)
async def get_article_detail(article_id: int):
    # 这个函数的结果会被自动缓存
    article = await db.get(Article, article_id)
    return serialize_article(article)
            '''.strip()
        },
        "common_tags": {
            "description": "常用缓存标签",
            "tags": [
                "article - 所有文章相关缓存",
                "article:{id} - 特定文章缓存",
                "article_list - 文章列表缓存",
                "category:{id} - 分类相关缓存",
                "user:{id} - 用户相关缓存",
                "settings - 系统设置缓存",
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )


@router.get("/all", summary="所有示例汇总", description="获取所有功能的示例汇总")
async def get_all_examples():
    """获取所有功能的示例汇总"""
    all_examples = {
        "accessibility": await get_accessibility_examples(),
        "performance": await get_performance_examples(),
        "security": await get_security_examples(),
        "seo": await get_seo_examples(),
        "nlp": await get_nlp_examples(),
        "collaboration": await get_collaboration_examples()
    }

    return ApiResponse(
        success=True,
        data=all_examples,
        message="所有示例获取成功"
    )
