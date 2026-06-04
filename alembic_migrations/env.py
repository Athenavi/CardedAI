"""
Alembic 环境配置
支持从环境变量动态读取数据库URL
"""
import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件 - 支持多个位置
project_root = Path(__file__).parent.parent

# 按优先级尝试加载 .env 文件
env_candidates = [
    project_root / '.env',              # 根目录 .env
    project_root / 'config' / '.env',   # config 目录 .env（安装向导写入位置）
]
env_loaded = False
for env_file in env_candidates:
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"[Alembic] Loaded .env from {env_file}")
        env_loaded = True
        break

if not env_loaded:
    print(f"[Alembic] Warning: .env file not found. Searched:")
    for p in env_candidates:
        print(f"  - {p}")

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Dynamically set database URL from environment variables
def get_database_url():
    """
    从环境变量构建数据库URL（仅支持 PostgreSQL）

    优先级:
    1. DATABASE_URL 环境变量 (完整URL)
    2. 分别的 DB_* 环境变量
    3. alembic.ini 中的默认值
    """
    # 尝试直接使用 DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url

    # 从单独的环境变量构建（PostgreSQL）
    db_name = os.getenv('DB_NAME', 'fast_blog')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    # 处理空字符串的情况，使用默认值
    db_port = os.getenv('DB_PORT') or '5432'

    # 验证必要参数
    if not db_host or not db_user or not db_name:
        raise ValueError(
            f"数据库配置不完整: host={db_host}, user={db_user}, name={db_name}"
        )

    # 构建 PostgreSQL URL
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Set the database URL
db_url = get_database_url()
# 隐藏密码打印
safe_url = db_url
if '@' in db_url:
    parts = db_url.split('@')
    prefix = parts[0]
    suffix = parts[1]
    # 把密码部分替换为 ***
    if ':' in prefix.split('://', 1)[-1]:
        user_part = prefix.split('://', 1)[0] + '://' + prefix.split('://', 1)[-1].split(':')[0]
        safe_url = f"{user_part}:***@{suffix}"
print(f"[Alembic] Database URL: {safe_url}")
config.set_main_option("sqlalchemy.url", db_url)

# add your model's MetaData object here
# for 'autogenerate' support
import sys

# 添加项目根目录到路径
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入 Base
from shared.models import Base
target_metadata = Base.metadata

# ============================================================
# 显式导入所有模型模块，确保它们注册到 Base.metadata
# 懒加载模式下，仅 import Base 不会触发模型类的加载
# ============================================================
import importlib

_model_modules = [
    'shared.models.user',
    'shared.models.article',
    'shared.models.article_content',
    'shared.models.article_like',
    'shared.models.article_seo',
    'shared.models.article_revision',
    'shared.models.article_revision_note',
    'shared.models.article_annotation',
    'shared.models.category',
    'shared.models.category_subscription',
    'shared.models.comment',
    'shared.models.comment_vote',
    'shared.models.comment_subscription',
    'shared.models.media',
    'shared.models.media_folder',
    'shared.models.media_optimization',
    'shared.models.system_settings',
    'shared.models.global_style',
    'shared.models.audit_log',
    'shared.models.ai_workflow',
    'shared.models.page_builder',
    'shared.models.field_permission',
    'shared.models.menus',
    'shared.models.menu_items',
    'shared.models.menu_location',
    'shared.models.menu_location_assignment',
    'shared.models.pages',
    'shared.models.upload_task',
    'shared.models.upload_chunk',
    'shared.models.download_task',
    'shared.models.notification',
    'shared.models.search_history',
    'shared.models.search_index',
    'shared.models.custom_field',
    'shared.models.plugin',
    'shared.models.theme',
    'shared.models.widget_instance',
    'shared.models.block_pattern',
    'shared.models.custom_post_type',
    'shared.models.o_auth_account',
    'shared.models.share_stat',
    'shared.models.sensitive_word',
    'shared.models.user_session',
    'shared.models.login_attempt',
    'shared.models.token_blacklist',
    'shared.models.webhook',
    'shared.models.webhook_delivery',
    'shared.models.file_hash',
    'shared.models.email_service_config',
    'shared.models.approval_record',
    'shared.models.approval_step',
    'shared.models.role',
    'shared.models.capability',
    'shared.models.role_capability',
    'shared.models.user_role',
    'shared.models.permission_audit_log',
    # ---- 情报引擎模型 ----
    'shared.models.intel.data_source',
    'shared.models.intel.collected_item',
    'shared.models.intel.intelligence',
    'shared.models.intel.briefing',
    'shared.models.intel.alert_rule',
    'shared.models.intel.alert_event',
    # ---- 知识引擎模型 ----
    'shared.models.knowledge.knowledge_base',
    'shared.models.knowledge.knowledge_document',
    'shared.models.knowledge.document_chunk',
    'shared.models.knowledge.report_template',
    'shared.models.knowledge.generated_report',
    # ---- 自动化引擎模型 ----
    'shared.models.workflow.workflow_definition',
    'shared.models.workflow.workflow_execution',
    'shared.models.workflow.node_execution',
    'shared.models.workflow.trigger',
    'shared.models.workflow.agent_tool',
    'shared.models.workflow.agent_memory',
]

_loaded_count = 0
for _mod_name in _model_modules:
    try:
        importlib.import_module(_mod_name)
        _loaded_count += 1
    except ImportError as e:
        print(f"[Alembic] Warning: Could not import {_mod_name}: {e}")

print(f"[Alembic] Loaded {_loaded_count}/{len(_model_modules)} model modules")
print(f"[Alembic] Registered {len(target_metadata.tables)} tables in metadata")

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 比较列类型
            render_as_batch=True,  # 支持批量操作（SQLite需要）
            include_schemas=True,  # 包含所有schema
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
