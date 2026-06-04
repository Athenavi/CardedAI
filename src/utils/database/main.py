import importlib

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import AsyncGenerator, List, Dict, Tuple

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy.pool import QueuePool

# 导入统一管理器
from src.utils.database.unified_manager import db_manager as unified_db_manager

from src.unified_logger import default_logger as logger
Base = declarative_base()
_models_imported = False  # 防止重复导入模型


def _import_models_once():
    """一次性导入所有模型模块（避免重复执行）"""
    global _models_imported
    if _models_imported:
        return

    try:
        # 动态导入settings模块，避免循环依赖
        from src.setting import settings

        # 尝试从配置中获取模型路径
        if hasattr(settings, 'MODELS_PATH'):
            models_path = Path(settings.MODELS_PATH)
        else:
            # 默认路径：shared/models
            current_dir = Path(__file__).parent.parent
            models_path = current_dir.parent / "shared" / "models"

        if not models_path.exists():
            logger.warning(f"模型目录不存在: {models_path}")
            _models_imported = True
            return

        # 添加父目录到Python路径
        parent_path = str(models_path.parent)
        if parent_path not in sys.path:
            sys.path.insert(0, parent_path)

        # 导入所有模型文件
        for file_path in models_path.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            module_name = f"shared.models.{file_path.stem}"
            try:
                importlib.import_module(module_name)
                logger.debug(f"导入模型模块: {module_name}")
            except ImportError as e:
                logger.debug(f"导入失败 {module_name}: {e}")

        # 配置映射
        configure_mappers()
        _models_imported = True
        logger.info(f"模型导入完成 (from {models_path})")

    except ImportError as e:
        logger.error(f"无法导入settings模块: {e}")
    except Exception as e:
        logger.error(f"导入模型时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())


class DatabaseManager:
    """简化的数据库管理器"""

    def __init__(self):
        self._sync_engine = None
        self._async_engine = None
        self._sync_session_factory = None
        self._async_session_factory = None

        # 驱动映射
        self._driver_map = {
            'postgresql': {'sync': 'psycopg2', 'async': 'asyncpg'},
            'mysql': {'sync': 'pymysql', 'async': 'aiomysql'},
            'sqlite': {'sync': 'sqlite3', 'async': 'aiosqlite'},
        }

    @property
    def database_url(self) -> str:
        """获取数据库URL"""
        from src.setting import settings
        return settings.database_url

    @property
    def echo_sql(self) -> bool:
        """是否输出SQL日志"""
        from src.setting import settings
        return getattr(settings, 'database_echo', False)

    def _parse_database_url(self, url: str) -> tuple:
        """解析数据库URL"""
        if "://" not in url:
            return "sqlite", url, None

        protocol, rest = url.split("://", 1)
        if "+" in protocol:
            db_type, driver = protocol.split("+", 1)
        else:
            db_type, driver = protocol, None

        return db_type, driver, rest

    def _build_url(self, db_type: str, driver: str, rest: str) -> str:
        """构建数据库URL"""
        if driver:
            return f"{db_type}+{driver}://{rest}"
        return f"{db_type}://{rest}"

    @property
    def sync_engine(self):
        """获取同步引擎（懒加载）"""
        if self._sync_engine is None:
            self._init_sync_engine()
        return self._sync_engine

    @property
    def async_engine(self):
        """获取异步引擎（懒加载）"""
        if self._async_engine is None:
            self._init_async_engine()
        return self._async_engine

    @property
    def sync_session(self):
        """获取同步会话工厂"""
        if self._sync_session_factory is None:
            self._init_sync_engine()
        return self._sync_session_factory

    @property
    def async_session(self):
        """获取异步会话工厂"""
        if self._async_session_factory is None:
            self._init_async_engine()
        return self._async_session_factory

    def _init_sync_engine(self):
        """初始化同步引擎（PostgreSQL）"""
        # 从环境变量读取连接池配置
        from src.setting import settings
        pool_size = getattr(settings, 'database_pool_size', 50)
        max_overflow = getattr(settings, 'database_pool_overflow', 100)
        pool_timeout = getattr(settings, 'database_pool_timeout', 60)
    
        logger.info(f"初始化同步引擎 - 连接池配置：pool_size={pool_size}, max_overflow={max_overflow}, timeout={pool_timeout}")
    
        self._sync_engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            echo=self.echo_sql
        )

        self._sync_session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._sync_engine
        )

    def _init_async_engine(self):
        """初始化异步引擎"""
        db_type, driver, rest = self._parse_database_url(self.database_url)

        # 确保使用异步驱动
        async_driver = self._driver_map.get(db_type, {}).get('async')
        if async_driver:
            # 构建带有异步驱动的 URL
            async_url = f"{db_type}+{async_driver}://{rest}"
        else:
            # 如果没有可用的异步驱动，则使用原始 URL（可能失败）
            async_url = self.database_url

        # Windows 上 asyncpg 的 pool_pre_ping 会导致 Proactor 事件循环问题
        # 参考：https://github.com/encode/databases/issues/206
        import sys
        use_pre_ping = True
        if sys.platform == 'win32' and driver == 'asyncpg':
            # 在 Windows 上使用 asyncpg 时禁用 pre_ping
            use_pre_ping = False
            logger.warning(
                "Detected Windows + asyncpg combination. Disabling pool_pre_ping to avoid Proactor event loop issues."
            )

        # 从环境变量读取连接池配置
        from src.setting import settings
        pool_size = getattr(settings, 'database_pool_size', 50)
        max_overflow = getattr(settings, 'database_pool_overflow', 100)
        pool_timeout = getattr(settings, 'database_pool_timeout', 60)

        logger.info(f"初始化异步引擎 - 连接池配置：pool_size={pool_size}, max_overflow={max_overflow}, timeout={pool_timeout}")

        self._async_engine = create_async_engine(
            async_url,
            pool_pre_ping=use_pre_ping,
            pool_recycle=300,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            echo=self.echo_sql
        )

        self._async_session_factory = async_sessionmaker(
            self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )


# 全局数据库管理器实例（已废弃，使用统一管理器）
# 为了向后兼容，保留这个变量但指向统一管理器
db = unified_db_manager


# 会话管理 - 完全委托给统一管理器
@contextmanager
def get_session():
    """
    同步会话上下文管理器（已废弃）
    
    ⚠️ 警告：这个方法已被弃用，请使用异步会话
    推荐使用：from src.utils.database.unified_manager import db_manager
    """
    logger.warning(
        "get_session() is deprecated. Please use async sessions via "
        "unified_manager.get_db_session() instead."
    )
    # 由于项目已全面转向异步，这里抛出异常引导用户使用正确的方法
    raise RuntimeError(
        "Sync sessions are no longer supported. "
        "Please use async sessions: from src.utils.database.unified_manager import get_db_session"
    )


from contextlib import asynccontextmanager

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    异步会话生成器（用于 FastAPI 依赖注入）
    
    这是一个异步生成器，专门用于 FastAPI 的 Depends() 依赖注入。
    如果需要在代码中直接使用 async with，请使用 get_async_session_context()。
    
    推荐使用：from src.utils.database.unified_manager import get_db_session
    """
    # 使用 async with 调用统一管理器的异步上下文管理器
    async with unified_db_manager.get_session_no_auto_commit() as session:
        yield session


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    异步会话上下文管理器（用于直接调用）
    
    这是一个异步上下文管理器，用于在代码中直接使用 async with 语法。
    不应用于 FastAPI 的 Depends() 依赖注入。
    
    使用示例：
        async with get_async_session_context() as session:
            result = await session.execute(query)
    """
    # 委托给统一管理器
    async with unified_db_manager.get_session_no_auto_commit() as session:
        yield session


# FastAPI依赖注入
def get_db():
    """同步数据库依赖"""
    with get_session() as session:
        yield session


async def get_async_db():
    """
    异步数据库依赖（已迁移到统一管理器）
    
    推荐使用：from src.utils.database.unified_manager import get_db_session
    """
    # 委托给统一管理器 - 使用 async with 而不是 async for
    async with unified_db_manager.get_session() as session:
        yield session


# 模型相关函数
def get_model_classes() -> List:
    """获取所有模型类"""
    _import_models_once()

    model_classes = []
    for mapper in Base.registry.mappers:
        model_class = mapper.class_
        if hasattr(model_class, '__tablename__'):
            model_classes.append(model_class)

    return model_classes


# 连接测试
async def test_connection_async() -> bool:
    """异步连接测试"""
    try:
        from src.utils.database.unified_manager import db_manager
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"连接测试失败: {e}")
        return False


def test_connection() -> bool:
    """快速连接测试（同步包装器）"""
    import asyncio
    try:
        # 尝试获取当前事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果已经有运行的事件循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(test_connection_async()))
                return future.result(timeout=10)
        except RuntimeError:
            # 没有运行的事件循环，直接使用 asyncio.run
            return asyncio.run(test_connection_async())
    except Exception as e:
        logger.error(f"连接测试失败: {e}")
        return False


def get_table_count() -> int:
    """获取表数量（已废弃，使用 Alembic 管理迁移）"""
    logger.warning("get_table_count() is deprecated. Please use Alembic for migration management.")
    return 0


def check_consistency() -> Tuple[List[Dict], List[str]]:
    """快速一致性检查（已废弃，使用 Alembic 管理迁移）"""
    logger.warning("check_consistency() is deprecated. Please use Alembic for migration management.")
    return [], []


def create_tables():
    """创建所有表（已废弃，使用 Alembic 管理迁移）"""
    logger.warning("create_tables() is deprecated. Please use Alembic for migration management.")
    return False


def drop_tables():
    """删除所有表（已废弃，使用 Alembic 管理迁移）"""
    logger.warning("drop_tables() is deprecated. Please use Alembic for migration management.")
    return False


# 初始化函数
async def init_database_async(create_if_missing=True, check_consistency=True):
    """异步初始化数据库"""
    from src.utils.database.unified_manager import db_manager

    # 确保数据库管理器已初始化
    if db_manager._async_engine is None:
        db_manager.initialize()

    if not await test_connection_async():
        logger.error("数据库连接失败")
        return False

    logger.info("数据库连接成功")

    # 注意：表创建和一致性检查需要使用 Alembic 迁移，这里不再直接操作
    logger.info("数据库初始化完成（请使用 Alembic 进行迁移）")

    return True


def init_database(create_if_missing=True, check_consistency=True):
    """初始化数据库（同步包装器）"""
    import asyncio
    try:
        # 尝试获取当前事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果已经有运行的事件循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(init_database_async(create_if_missing, check_consistency)))
                return future.result(timeout=30)
        except RuntimeError:
            # 没有运行的事件循环，直接使用 asyncio.run
            return asyncio.run(init_database_async(create_if_missing, check_consistency))
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


# 简化版本，按需初始化
async def ensure_database_async():
    """确保数据库已初始化（异步）"""
    return await init_database_async()


def ensure_database():
    """确保数据库已初始化"""
    return init_database()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_database()
