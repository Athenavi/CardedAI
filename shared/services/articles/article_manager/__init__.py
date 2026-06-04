"""
文章管理服务包

提供统一的文章相关操作，包括：
- 文章 CRUD 操作
- 文章查询和过滤
- 修订历史管理
- 密码保护功能
"""

from .password_protection_service import (
    PasswordProtectionService,
    password_protection_service,
)
from .query_service import (
    ArticleQueryService,
    article_query_service,
)
from .revision_service import (
    save_article_revision,
    get_article_revisions,
    get_revision_detail,
    rollback_to_revision,
    compare_revisions,
    delete_revision,
    calculate_revision_hash,
)
from .service import (
    get_article_by_id,
    get_articles_by_user_id,
    get_article_count_by_user,
    get_article_with_content,
    get_user_articles_with_pagination,
    create_article,
    update_article,
    update_article_content,
    delete_article,
    increment_article_views,
    search_articles,
)

__all__ = [
    # Service functions
    'get_article_by_id',
    'get_articles_by_user_id',
    'get_article_count_by_user',
    'get_article_with_content',
    'get_user_articles_with_pagination',
    'create_article',
    'update_article',
    'update_article_content',
    'delete_article',
    'increment_article_views',
    'search_articles',

    # Query service
    'ArticleQueryService',
    'article_query_service',

    # Revision service
    'save_article_revision',
    'get_article_revisions',
    'get_revision_detail',
    'rollback_to_revision',
    'compare_revisions',
    'delete_revision',
    'calculate_revision_hash',

    # Password protection
    'PasswordProtectionService',
    'password_protection_service',
]
