"""
Models 包 - 懒加载版本

所有模型类通过 __getattr__ 按需导入，避免启动时一次性加载所有模型文件。
Base 保持立即导入（SQLAlchemy 元数据初始化必需）。

由代码生成器自动生成 - 请勿手动修改
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# ==================== 懒加载映射表 ====================
# 模型名 -> 相对模块路径（不含 shared.models 前缀）
_LAZY_IMPORTS = {
    'AIWorkflow': '.ai_workflow',
    'AgentMemory': '.workflow.agent_memory',
    'AgentTool': '.workflow.agent_tool',
    'AlertEvent': '.intel.alert_event',
    'AlertRule': '.intel.alert_rule',
    'ApprovalRecord': '.approval_record',
    'ApprovalStep': '.approval_step',
    'Article': '.article',
    'ArticleAnnotation': '.article_annotation',
    'ArticleContent': '.article_content',
    'ArticleLike': '.article_like',
    'ArticleRevision': '.article_revision',
    'ArticleRevisionNote': '.article_revision_note',
    'ArticleSEO': '.article_seo',
    'AuditLog': '.audit_log',
    'BlockPattern': '.block_pattern',
    'Briefing': '.intel.briefing',
    'Category': '.category',
        'CollectedItem': '.intel.collected_item',
    'Comment': '.comment',
    'CommentSubscription': '.comment_subscription',
    'CommentVote': '.comment_vote',
    'CustomField': '.custom_field',
    'CustomPostType': '.custom_post_type',
    'DataSource': '.intel.data_source',
    'DocumentChunk': '.knowledge.document_chunk',
    'DownloadTask': '.download_task',
    'EmailServiceConfig': '.email_service_config',
    'FileHash': '.file_hash',
    'GeneratedReport': '.knowledge.generated_report',
        'Intelligence': '.intel.intelligence',
    'KnowledgeBase': '.knowledge.knowledge_base',
    'KnowledgeDocument': '.knowledge.knowledge_document',
    'LoginAttempt': '.login_attempt',
    'Media': '.media',
    'MediaFolder': '.media_folder',
    'MediaOptimization': '.media_optimization',
    'MenuItems': '.menu_items',
    'MenuLocation': '.menu_location',
    'MenuLocationAssignment': '.menu_location_assignment',
    'Menus': '.menus',
    'NodeExecution': '.workflow.node_execution',
    'Notification': '.notification',
    'OAuthAccount': '.o_auth_account',
    'PageBuilder': '.page_builder',
    'Pages': '.pages',
    'ReportTemplate': '.knowledge.report_template',
    'SearchHistory': '.search_history',
    'SearchIndex': '.search_index',
    'SensitiveWord': '.sensitive_word',
    'ShareStat': '.share_stat',
    'SystemSettings': '.system_settings',
        'TokenBlacklist': '.token_blacklist',
    'Trigger': '.workflow.trigger',
    'UploadChunk': '.upload_chunk',
    'UploadTask': '.upload_task',
    'User': '.user',
    'UserSession': '.user_session',
    'Webhook': '.webhook',
    'WebhookDelivery': '.webhook_delivery',
    'WidgetInstance': '.widget_instance',
    'WorkflowDefinition': '.workflow.workflow_definition',
    'WorkflowExecution': '.workflow.workflow_execution',
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


# ==================== 自动生成 - __all__ ====================
# 此部分由脚本自动生成 - 请勿手动修改

__all__ = [
    'AIWorkflow',
    'AgentMemory',
    'AgentTool',
    'AlertEvent',
    'AlertRule',
    'ApprovalRecord',
    'ApprovalStep',
    'Article',
    'ArticleAnnotation',
    'ArticleContent',
    'ArticleLike',
    'ArticleRevision',
    'ArticleRevisionNote',
    'ArticleSEO',
    'AuditLog',
    'Base',
    'BlockPattern',
    'Briefing',
    'Category',
    'CollectedItem',
    'Comment',
    'CommentSubscription',
    'CommentVote',
    'CustomField',
    'CustomPostType',
    'DataSource',
    'DocumentChunk',
    'DownloadTask',
    'EmailServiceConfig',
    'FileHash',
    'GeneratedReport',
    'Intelligence',
    'KnowledgeBase',
    'KnowledgeDocument',
    'LoginAttempt',
    'Media',
    'MediaFolder',
    'MediaOptimization',
    'MenuItems',
    'MenuLocation',
    'MenuLocationAssignment',
    'Menus',
    'NodeExecution',
    'Notification',
    'OAuthAccount',
    'PageBuilder',
    'Pages',
    'ReportTemplate',
    'SearchHistory',
    'SearchIndex',
    'SensitiveWord',
    'ShareStat',
    'SystemSettings',
    'TokenBlacklist',
    'Trigger',
    'UploadChunk',
    'UploadTask',
    'User',
    'UserSession',
    'Webhook',
    'WebhookDelivery',
    'WidgetInstance',
    'WorkflowDefinition',
    'WorkflowExecution',
]
# ============================================================================
