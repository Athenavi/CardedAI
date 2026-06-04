"""
Alembic 环境配置
支持从环境变量动态读取数据库URL
"""
import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
project_root = Path(__file__).parent.parent
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"[Alembic] Loaded .env from {env_file}")
else:
    print(f"[Alembic] Warning: .env file not found at {env_file}")

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
print(f"[Alembic] Database URL: {db_url.split('@')[1].split('/')[0] if '@' in db_url else db_url}")  # 隐藏密码
config.set_main_option("sqlalchemy.url", db_url)

# add your model's MetaData object here
# for 'autogenerate' support
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入所有模型的 Base
from shared.models import Base
target_metadata = Base.metadata

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
