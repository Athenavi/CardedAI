"""
统一的数据库连接管理器

解决数据库会话冲突问题，确保：
1. 全局唯一的引擎和会话工厂
2. 统一的连接池配置
3. 正确的会话生命周期管理
4. Windows + asyncpg 兼容性处理
"""

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.unified_logger import default_logger as logger


class UnifiedDatabaseManager:
    """
    统一的数据库管理器
    
    确保整个应用中只有一个异步引擎实例和会话工厂，
    避免连接池冲突和会话管理问题。
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if self._initialized:
            return

        self._async_engine = None
        self._async_session_factory = None
        self._initialized = True

        logger.info("UnifiedDatabaseManager initialized")

    @property
    def database_url(self) -> str:
        """获取数据库URL"""
        from src.setting import settings
        return settings.database_url

    def _get_pool_config(self) -> dict:
        """
        获取连接池配置
        
        Windows + asyncpg 特殊处理：
        - 使用适中的连接池大小支持并发
        - 设置合理的超时时间避免长时间阻塞
        - 禁用 pre-ping 避免 Proactor 事件循环问题
        """
        from src.setting import settings

        if sys.platform == 'win32':
            # Windows: 优化配置以平衡性能和稳定性
            # 参考最佳实践：pool_size=5-10, timeout=5-10s
            return {
                'pool_size': 10,  # 增加到 10，支持更高并发
                'max_overflow': 20,  # 允许最多 20 个溢出连接
                'pool_timeout': 10,  # 降低到 10 秒，避免长时间阻塞
                'pool_recycle': 180,  # 3 分钟回收，防止连接过期
                'pool_pre_ping': False,  # Windows 上禁用 pre-ping
                'pool_use_lifo': False,  # 使用 FIFO，避免连接复用问题
            }
        else:
            # Linux/Mac: 生产环境优化配置
            # 参考最佳实践：pool_timeout=10-30s, pool_recycle=1800-3600s
            return {
                'pool_size': getattr(settings, 'database_pool_size', 20),  # 降低到 20，避免资源浪费
                'max_overflow': getattr(settings, 'database_pool_overflow', 40),  # 降低到 40
                'pool_timeout': getattr(settings, 'database_pool_timeout', 30),  # 增加到 30 秒，更宽松
                'pool_recycle': 1800,  # 增加到 30 分钟，防止频繁重建连接
                'pool_pre_ping': True,  # Linux 上启用健康检查
            }

    def _build_async_url(self, original_url: str) -> str:
        """构建异步数据库URL"""
        if "postgresql" in original_url:
            return original_url.replace(
                "postgresql+psycopg2://", "postgresql+asyncpg://"
            ).replace("postgresql://", "postgresql+asyncpg://")
        elif "mysql" in original_url:
            return original_url.replace(
                "mysql+pymysql://", "mysql+aiomysql://"
            ).replace("mysql://", "mysql+aiomysql://")
        elif "sqlite" in original_url:
            return original_url.replace(
                "sqlite:///", "sqlite+aiosqlite:///"
            )
        else:
            return original_url

    def initialize(self):
        """
        初始化异步引擎和会话工厂
        
        这个方法应该在应用启动时调用一次。
        """
        if self._async_engine is not None:
            logger.warning("Database engine already initialized")
            return

        try:
            db_url = self.database_url
            if not db_url:
                logger.warning("Database URL not configured, skipping initialization")
                return

            # 构建异步URL
            async_url = self._build_async_url(db_url)

            # 获取连接池配置
            pool_config = self._get_pool_config()

            # Windows + asyncpg 特殊处理
            use_pre_ping = True
            if sys.platform == 'win32' and 'asyncpg' in async_url:
                use_pre_ping = False
                logger.warning(
                    "Windows + asyncpg detected. Disabling pool_pre_ping to avoid "
                    "Proactor event loop issues."
                )

            logger.info(
                f"Initializing async database engine with config: "
                f"pool_size={pool_config['pool_size']}, "
                f"max_overflow={pool_config['max_overflow']}, "
                f"timeout={pool_config['pool_timeout']}"
            )

            # 创建异步引擎
            engine_kwargs = {
                'pool_pre_ping': use_pre_ping,
                'pool_recycle': pool_config['pool_recycle'],
                'pool_size': pool_config['pool_size'],
                'max_overflow': pool_config['max_overflow'],
                'pool_timeout': pool_config['pool_timeout'],
                'echo': getattr(__import__('src.setting', fromlist=['settings']).settings,
                                'database_echo', False),
            }

            # Windows + asyncpg: 添加额外的连接参数
            if sys.platform == 'win32' and 'asyncpg' in async_url:
                engine_kwargs['connect_args'] = {
                    'statement_cache_size': 0,  # 禁用语句缓存，避免 prepared statement 问题
                    'command_timeout': 60,  # 命令超时
                    'server_settings': {
                        'jit': 'off',  # 禁用 JIT 编译，提高性能
                    },
                }
                logger.info(
                    f"Windows + asyncpg detected. Using optimized settings: "
                    f"pool_size={pool_config['pool_size']}, "
                    f"max_overflow={pool_config['max_overflow']}, "
                    f"statement_cache_size=0, jit=off"
                )

            self._async_engine = create_async_engine(async_url, **engine_kwargs)

            # 创建会话工厂
            self._async_session_factory = async_sessionmaker(
                self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            logger.info("Async database engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}", exc_info=True)
            raise

    @property
    def async_engine(self):
        """获取异步引擎（懒加载）"""
        if self._async_engine is None:
            self.initialize()
        return self._async_engine

    @property
    def async_session_factory(self):
        """获取异步会话工厂（懒加载）"""
        if self._async_session_factory is None:
            self.initialize()
        return self._async_session_factory

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话的上下文管理器
        
        这是推荐的会话获取方式，确保：
        1. 会话正确关闭
        2. 异常时自动回滚
        3. 成功时自动提交
        4. Windows + asyncpg 兼容性处理
        
        使用示例：
            async with db_manager.get_session() as session:
                result = await session.execute(query)
                await session.commit()
        """
        # 检查会话工厂是否已初始化
        if self._async_session_factory is None:
            # 尝试初始化
            self.initialize()

            # 如果仍然为 None，说明数据库URL未配置
            if self._async_session_factory is None:
                error_msg = (
                    "Database manager not initialized. "
                    "This usually means the database URL is not configured. "
                    "Please ensure you have completed the database configuration step "
                    "before attempting to use the database."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        session = self.async_session_factory()
        logger.debug(f"Creating new session: {id(session)}")
        
        try:
            yield session
            # 如果没有异常，尝试提交
            try:
                logger.debug(f"Committing session: {id(session)}")
                await session.commit()
                logger.debug(f"Session committed successfully: {id(session)}")
            except Exception as commit_err:
                error_msg = str(commit_err)
                # 检查是否是并发错误
                if "another operation is in progress" in error_msg:
                    logger.warning(
                        f"⚠️ Concurrent operation detected on session {id(session)}. "
                        f"This is a known Windows + asyncpg compatibility issue. "
                        f"Attempting rollback and retry..."
                    )
                    # 在 Windows 上，如果遇到并发错误，等待一小段时间再重试
                    if sys.platform == 'win32':
                        import asyncio
                        await asyncio.sleep(0.2)  # 等待 200ms
                        try:
                            await session.rollback()
                            logger.debug(f"Session rolled back after retry: {id(session)}")
                            # 重新提交
                            await session.commit()
                            logger.debug(f"Session re-committed successfully: {id(session)}")
                        except Exception:
                            pass
                else:
                    logger.debug(f"Rolling back session due to error: {commit_err}")
                    try:
                        await session.rollback()
                        logger.debug(f"Session rolled back: {id(session)}")
                    except Exception as rollback_err:
                        logger.error(f"Error during rollback: {rollback_err}")
                raise
        except Exception as e:
            # 发生异常时回滚
            error_msg = str(e)
            if "another operation is in progress" in error_msg:
                logger.warning(
                    f"⚠️ Concurrent operation error on session {id(session)}: {error_msg}"
                )
                # 在 Windows 上，如果遇到并发错误，等待一小段时间
                if sys.platform == 'win32':
                    import asyncio
                    await asyncio.sleep(0.2)
            else:
                logger.debug(f"Exception occurred, rolling back session: {id(session)}")

            try:
                await session.rollback()
                logger.debug(f"Session rolled back after exception: {id(session)}")
            except Exception as rollback_err:
                logger.error(f"Error during rollback: {rollback_err}")
            raise
        finally:
            # 确保会话总是被关闭
            try:
                logger.debug(f"Closing session: {id(session)}")
                await session.close()
                logger.debug(f"Session closed successfully: {id(session)}")
            except Exception as e:
                logger.warning(f"Error closing session (may be expected): {e}")

    @asynccontextmanager
    async def get_session_no_auto_commit(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话（不自动提交）- 上下文管理器版本
        
        适用于需要手动控制事务的场景。
        调用者负责 commit/rollback。
        
        使用示例：
            async with db_manager.get_session_no_auto_commit() as session:
                result = await session.execute(query)
                await session.commit()
        """
        # 检查会话工厂是否已初始化
        if self._async_session_factory is None:
            # 尝试初始化
            self.initialize()

            # 如果仍然为 None，说明数据库URL未配置
            if self._async_session_factory is None:
                error_msg = (
                    "Database manager not initialized. "
                    "This usually means the database URL is not configured. "
                    "Please ensure you have completed the database configuration step "
                    "before attempting to use the database."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        session = self.async_session_factory()
        logger.debug(f"Creating new session (no auto-commit): {id(session)}")
        try:
            yield session
        except Exception as e:
            # 发生异常时回滚
            error_msg = str(e)
            if "another operation is in progress" in error_msg:
                logger.warning(
                    f"⚠️ Concurrent operation error on session {id(session)}: {error_msg}"
                )
                # 在 Windows 上，如果遇到并发错误，等待一小段时间
                if sys.platform == 'win32':
                    import asyncio
                    await asyncio.sleep(0.2)
            else:
                logger.debug(f"Exception occurred, rolling back session: {id(session)}")

            try:
                await session.rollback()
                logger.debug(f"Session rolled back after exception: {id(session)}")
            except Exception as rollback_err:
                logger.error(f"Error during rollback: {rollback_err}")
            raise
        finally:
            # 确保会话总是被关闭
            try:
                logger.debug(f"Closing session: {id(session)}")
                await session.close()
                logger.debug(f"Session closed successfully: {id(session)}")
            except Exception as e:
                logger.warning(f"Error closing session (may be expected): {e}")

    async def close(self):
        """关闭数据库引擎（应用 shutdown 时调用）"""
        if self._async_engine:
            try:
                await self._async_engine.dispose()
                logger.info("Database engine disposed")
            except Exception as e:
                logger.error(f"Error disposing database engine: {e}")
            finally:
                self._async_engine = None
                self._async_session_factory = None


# 全局单例实例
db_manager = UnifiedDatabaseManager()


# 便捷函数 - 用于 FastAPI 依赖注入
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入使用的会话生成器
    
    这是推荐的使用方式，在 FastAPI 路由中使用：
    
    @router.get("/example")
    async def example_endpoint(db: AsyncSession = Depends(get_db_session)):
        result = await db.execute(query)
        return result
    """
    async with db_manager.get_session() as session:
        yield session


async def get_db_session_manual() -> AsyncGenerator[AsyncSession, None]:
    """
    手动控制事务的会话生成器
    
    适用于需要手动控制 commit/rollback 的场景。
    """
    async with db_manager.get_session_no_auto_commit() as session:
        yield session


# 兼容旧代码的别名
get_async_session = get_db_session
get_async_db = get_db_session
