"""
FastBlog API v2 路由规范配置

v2 版本采用以下原则：
1. 所有路径使用 kebab-case 命名
2. 避免通用路径冲突（如 /stats、/config）
3. 资源路径清晰分层，不使用根级参数
4. 合并重复模块功能
5. 统一领域前缀

领域映射表：
- users: 用户认证与资料
- articles: 文章核心功能
- categories: 分类管理
- search: 搜索功能
- cms: CMS 内容管理
- shop: 电商功能
- monitoring: 性能监控
- backup: 备份管理
- cache: 缓存管理
- translations: 国际化与翻译
- ads: 广告管理
- integrations: 第三方集成
- seo: SEO 优化
- gdpr: GDPR 合规
- analytics: 统计分析
- notifications: 通知消息
- security: 安全管理
- themes: 主题管理
- ext: 扩展功能
"""

# v2 路由注册表：(模块路径, v2前缀, 标签列表, 是否必需)
ROUTE_REGISTRY_V2 = [
    # ==================== 核心模块（必需）====================
    ("src.api.v1.core.home", "/api/v2/home", ["home"], True),
    # ==================== 仪表板（V2 聚合路由器）====================
    # V2 Dashboard 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.dashboard", "/api/v2/dashboard", ["dashboard-v2"], True),
    ("src.api.v1.core.system", "/api/v2/system", ["system"], True),

    # ==================== 文章核心（V2 聚合路由器）====================
    # V2 Articles 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.articles", "/api/v2/articles", ["articles-v2"], True),

    # ==================== 分类管理 ====================
    ("src.api.v1.content_management.category_management", "/api/v2/categories", ["categories"], True),

    # ==================== 标签管理（新增）====================
    ("src.api.v1.articles.tags", "/api/v2/tags", ["tags"], False),

    # ==================== 搜索（V2 聚合路由器）====================
    # V2 Search 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.search", "/api/v2/search", ["search-v2"], True),

    # ==================== 评论系统（V2 聚合路由器）====================
    # V2 Comments 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.comments", "/api/v2/comments", ["comments-v2"], True),
    # V1 comments 各子模块已废弃，功能已迁移到 V2 聚合路由器
    # [已删除] 聊天与消息模块（PrivateMessage, ChatGroup 等模型已移除）
    # ==================== 通知消息（V2 聚合路由器）====================
    # V2 Notifications 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.notifications", "/api/v2/notifications", ["notifications-v2"], True),
    # [已删除] 协作功能模块（Workspace, Task 等模型已移除）

    # ==================== CMS 内容管理（V2 聚合路由器）====================
    # V2 Content Management 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.content_management", "/api/v2/cms", ["cms-v2"], True),
    # V1 content_management 各子模块已废弃，功能已迁移到 V2 聚合路由器

    # ==================== 块模式库（独立顶级路由）====================
    # 前端直接调用 /api/v2/block-patterns/list
    ("src.api.v1.content_management.block_patterns", "/api/v2/block-patterns", ["block-patterns"], False),

    # [已删除] 电商功能模块（Product, Cart, Order 等模型已移除）

    # ==================== 媒体管理 ====================
    ("src.api.v1.media", "/api/v2/media", ["media"], False),
    ("src.api.v1.media.cover_upload", "/api/v2/media", ["cover-upload"], False),

    # ==================== SEO 优化（V2 聚合路由器）====================
    # V2 SEO 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.seo", "/api/v2/seo", ["seo-v2"], True),

    # ==================== 安全与权限（V2 聚合路由器）====================
    # V2 Security 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.security", "/api/v2/security", ["security-v2"], False),
    # V1 security 各子模块已废弃，功能已迁移到 V2 聚合路由器

    # ==================== 认证模块（新增）====================
    ("src.api.v1.auth", "/api/v2/auth", ["auth"], False),
    ("src.api.v2.qr_login", "/api/v2/auth/qr", ["qr-login"], False),

    # ==================== 用户管理（V2 聚合路由器）====================
    # V2 Users 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.users", "/api/v2", ["users-v2"], True),
    # ==================== 性能监控与优化（V2 聚合路由器）====================
    # V2 Performance 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.performance", "/api/v2/performance", ["performance-v2"], False),
    # V1 performance 各子模块已废弃，功能已迁移到 V2 聚合路由器

    # ==================== 备份管理（V2 完整版）====================
    ("src.api.v2.system.backup_management", "/api/v2/system", ["backup-v2"], False),

    # ==================== 系统管理（V2 聚合路由器）====================
    # V2 System 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.system", "/api/v2/system", ["system-v2"], True),

    # ==================== 安装向导（独立顶级路由）====================
    # 安装功能作为独立顶级资源，便于前端访问
    ("src.api.v1.system.installation", "/api/v2/install", ["installation"], False),

    # ==================== GDPR 合规（V2 完整版）====================
    # V1 gdpr_compliance 已废弃，功能已整合到 V2 compliance_api
    # ("src.api.v1.compliance.gdpr_compliance", "/api/v2/gdpr", ["gdpr-compliance"], False),
    ("src.api.v2.compliance.compliance_api", "/api/v2", ["compliance-management-v2"], False),

    # ==================== 主题管理（移除） ====================

    # ==================== 插件管理（V2 聚合路由器）====================
    # ==================== 翻译（V2 聚合路由器）====================
    # V2 Translation 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.translation", "/api/v2", ["translation-v2"], True),
    # V1 translation 各子模块已废弃，功能已迁移到 V2 聚合路由器

    # ==================== 第三方集成（V2 聚合路由器）====================
    # V2 Integrations 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.integrations", "/api/v2/integrations", ["integrations-v2"], True),
    # V1 integrations 各子模块已废弃，功能已迁移到 V2 聚合路由器

    # [已删除] 广告管理模块（Ad, AdPlacement 等模型已移除）

    # ==================== 静态生成（V2 聚合路由器）====================
    # V2 Static Generation 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.static_generation", "/api/v2/static-site", ["static-generation-v2"], True),
    # V1 static_generation 各子模块已废弃，功能已迁移到 V2 聚合路由器
    # ("src.api.v1.static_generation.static_site_generation", "/api/v2/static-site", ["static-site-generation"], False),

    # [已删除] 支付系统模块（PaymentGateway, PaymentTransaction 等模型已移除）
    # [已删除] 迁移系统模块（MigrationTask, MigrationLog 模型已移除）

    # ==================== 内容管理扩展（修订注释/菜单位置）====================
    ("src.api.v1.content_management.content_management_ext", "/api/v2/cms/management", ["content-management-ext"],
     False),

    # ==================== 用户安全管理（字段权限/会话/邮件订阅）====================
    ("src.api.v1.users.user_security_management", "/api/v2/users/security", ["user-security-management"], False),

    # ==================== 搜索与媒体管理（索引/优化）====================
    ("src.api.v1.search.search_media_management", "/api/v2/search/management", ["search-media-management"], False),

    # ==================== 可访问性（V2 聚合路由器）====================
    # V2 Accessibility 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.accessibility", "/api/v2/accessibility", ["accessibility-v2"], True),
    # V1 accessibility 各子模块已废弃，功能已迁移到 V2 聚合路由器
    # ==================== 社交（V2 聚合路由器）====================
    # V2 Social 模块采用包级别聚合模式，所有子模块通过 __init__.py 统一注册
    ("src.api.v2.social", "/api/v2/social", ["social-v2"], True),
    # V1 social 各子模块已废弃，功能已迁移到 V2 聚合路由器
    # ("src.api.v1.social.share_stats", "/api/v2/social/share-stats", ["share-stats"], False),

    # ==================== 示例和工具端点（集中管理）====================
    ("src.api.v2.examples_tools", "/api/v2/examples", ["examples-tools"], False),

    # ==================== 情报引擎（V2 聚合路由器）====================
    ("src.api.v2.intel", "/api/v2/intel", ["intel-v2"], True),

    # ==================== 知识引擎（V2 聚合路由器）====================
    ("src.api.v2.knowledge", "/api/v2/knowledge", ["knowledge-v2"], True),

    # ==================== 自动化引擎（V2 聚合路由器）====================
    ("src.api.v2.workflow", "/api/v2/workflow", ["workflow-v2"], True),

    # ==================== MCP Server（AI Agent 接口）====================
    ("src.api.v2.mcp", "/api/v2/mcp", ["mcp-v2"], True),

    # ==================== AI 聊天代理（对话式站点管理）====================
    ("src.api.v2.ai", "/api/v2/ai", ["ai-v2"], True),

    # [已删除] 企业管理模块（EnterpriseLicense, SupportTicket 等模型已移除）
]

# v1 到 v2 的路径映射表（用于自动重定向）
V1_TO_V2_REDIRECT_MAP = {
    # 通用冲突路径
    "/api/v1/stats": "/api/v2/monitoring/stats",
    "/api/v1/config": "/api/v2/admin/config",
    "/api/v1/delete": "/api/v2/gdpr/data-deletion",
    "/api/v1/export": "/api/v2/gdpr/data-export",
    "/api/v1/rights": "/api/v2/gdpr/user-rights",
    "/api/v1/generate": "/api/v2/seo/hreflang/generate",
    "/api/v1/sync": "/api/v2/sites/sync",
    "/api/v1/process-queue": "/api/v2/downloads/queue/process",

    # 文章相关
    "/api/v1/revisions": "/api/v2/articles/revisions",
    "/api/v1/{article_id}/access": "/api/v2/articles/{article_id}/access-check",

    # 用户相关 - 需要特殊处理动态路径
    "/api/v1/users/profile": "/api/v2/users/me",
    "/api/v1/admin/user/me/profile": "/api/v2/users/me",
    "/api/v1/profiles": "/api/v2/users/settings",

    # SEO 相关
    "/api/v1/admin/seo": "/api/v2/seo/management",
    "/api/v1/breadcrumbs": "/api/v2/seo/breadcrumbs",
    "/api/v1/redirect": "/api/v2/seo/redirects",
    "/api/v1/seo-tracking": "/api/v2/seo/tracking",

    # 缓存相关
    "/api/v1/admin/caches": "/api/v2/cache",
    "/api/v1/clear-all": "/api/v2/cache/clear-all",

    # 备份相关
    "/api/v1/admin/backup": "/api/v2/backup",
    "/api/v1/backup-plus": "/api/v2/backup/incremental",

    # 性能监控相关
    "/api/v1/performance-monitor": "/api/v2/monitoring/performance",
    "/api/v1/performance-tracking": "/api/v2/monitoring/performance",

    # [已删除] 广告相关重定向

    # 翻译相关
    "/api/v1/i18n": "/api/v2/translations",

    # misc 模块迁移重定向
    "/api/v1/misc/tags/suggest": "/api/v2/tags/suggest",
    "/api/v1/misc/search/history": "/api/v2/search/history",
    "/api/v1/misc/upload/cover": "/api/v2/media/cover",
    "/api/v1/misc/check-email": "/api/v2/auth/check-email",
    "/api/v1/misc/check-username": "/api/v2/auth/check-username",
    "/api/v1/misc/email-exists": "/api/v2/auth/check-email",
    "/api/v1/misc/username-exists/{username}": "/api/v2/auth/check-username/{username}",
    "/api/v1/misc/version/info": "/api/v2/system/version/full",
    "/api/v1/misc/version/frontend": "/api/v2/system/version/frontend",
    "/api/v1/misc/version/backend": "/api/v2/system/version/backend",
}
