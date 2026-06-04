"""
Models 包 - 懒加载版本

所有模型类通过 __getattr__ 按需导入，避免启动时一次性加载所有模型文件。
Base 保持立即导入（SQLAlchemy 元数据初始化必需）。
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# ==================== 懒加载映射表 ====================
# 模型名 -> 相对模块路径（不含 shared.models 前缀）
_LAZY_IMPORTS = {
    'AuditLog': '.audit_log',
    'AIWorkflow': '.ai_workflow',
    'PageBuilder': '.page_builder',
    'GlobalStyle': '.global_style',
    'FieldPermission': '.field_permission',
    'User': '.user',
    'Article': '.article',
    'Category': '.category',
    'CategorySubscription': '.category_subscription',
    'Media': '.media',
    'MediaFolder': '.media_folder',
    'MediaOptimization': '.media_optimization',
    'ArticleRevisionNote': '.article_revision_note',
    'SystemSettings': '.system_settings',
    'AdminSettings': '.system_settings',
    'ArticleContent': '.article_content',
    'ArticleLike': '.article_like',
    'FileHash': '.file_hash',
    'Menus': '.menus',
    'MenuItems': '.menu_items',
    'MenuLocation': '.menu_location',
    'MenuLocationAssignment': '.menu_location_assignment',
    'Pages': '.pages',
    'UploadTask': '.upload_task',
    'UploadChunk': '.upload_chunk',
    'DownloadTask': '.download_task',
    'Notification': '.notification',
    'SearchHistory': '.search_history',
    'SearchIndex': '.search_index',
    'CustomField': '.custom_field',
    'ArticleRevision': '.article_revision',
    'Plugin': '.plugin',
    'Theme': '.theme',
    'WidgetInstance': '.widget_instance',
    'BlockPattern': '.block_pattern',
    'CustomPostType': '.custom_post_type',
    'CommentVote': '.comment_vote',
    'CommentSubscription': '.comment_subscription',
    'Comment': '.comment',
    'OAuthAccount': '.o_auth_account',
    'ArticleSEO': '.article_seo',
    'ShareStat': '.share_stat',
    'SensitiveWord': '.sensitive_word',
    'UserSession': '.user_session',
    'LoginAttempt': '.login_attempt',
    'TokenBlacklist': '.token_blacklist',
    'ArticleAnnotation': '.article_annotation',
    'Webhook': '.webhook',
    'WebhookDelivery': '.webhook_delivery',
    'EmailServiceConfig': '.email_service_config',
    'ApprovalRecord': '.approval_record',
    'ApprovalStep': '.approval_step',
    'Role': '.role',
    'Capability': '.capability',
    'RoleCapability': '.role_capability',
    'UserRole': '.user_role',
    'PermissionAuditLog': '.permission_audit_log',
}

# 已加载的模型缓存（避免重复导入）
_loaded_models = {}


def __getattr__(name):
    """模块级 __getattr__：按需懒加载模型类"""
    if name in _loaded_models:
        return _loaded_models[name]

    module_path = _LAZY_IMPORTS.get(name)
    if module_path is not None:
        import importlib
        module = importlib.import_module(module_path, package='shared.models')
        cls = getattr(module, name)
        # 缓存到模块命名空间，后续访问直接命中
        globals()[name] = cls
        _loaded_models[name] = cls
        return cls

    raise AttributeError(f"module 'shared.models' has no attribute {name!r}")


# ==================== 自动生成的导入 - 由 routes.yaml 管理 ====================
# 此部分由脚本自动生成 - 请勿手动修改

__all__ = [
    'Base',
    'AuditLog',
    'AIWorkflow',
    'PageBuilder',
    'GlobalStyle',
    'FieldPermission',
    'User',
    'Article',
    'Category',
    'CategorySubscription',
    'Media',
    'MediaFolder',
    'MediaOptimization',
    'ArticleRevisionNote',
    'SystemSettings',
    'AdminSettings',
    'ArticleContent',
    'ArticleLike',
    'FileHash',
    'Menus',
    'MenuItems',
    'MenuLocation',
    'MenuLocationAssignment',
    'Pages',
    'UploadTask',
    'UploadChunk',
    'DownloadTask',
    'Notification',
    'SearchHistory',
    'SearchIndex',
    'CustomField',
    'ArticleRevision',
    'Plugin',
    'Theme',
    'WidgetInstance',
    'BlockPattern',
    'CustomPostType',
    'CommentVote',
    'CommentSubscription',
    'Comment',
    'OAuthAccount',
    'ArticleSEO',
    'ShareStat',
    'SensitiveWord',
    'UserSession',
    'LoginAttempt',
    'TokenBlacklist',
    'ArticleAnnotation',
    'Webhook',
    'WebhookDelivery',
    'EmailServiceConfig',
    'ApprovalRecord',
    'ApprovalStep',
    'Role',
    'Capability',
    'RoleCapability',
    'UserRole',
    'PermissionAuditLog',
]
# ============================================================================
