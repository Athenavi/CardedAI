"""扩展模块，初始化FastAPI兼容的扩展实例"""
import json
import os
from contextlib import contextmanager
from typing import Generator, AsyncGenerator

import redis
from slowapi import _rate_limit_exceeded_handler, Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.declarative import declarative_base

from src.unified_logger import default_logger as logger

# 初始化 Sentry 错误追踪
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration

    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")),
            environment=os.getenv("ENVIRONMENT", "development"),
        )
        logger.info("Sentry initialized successfully")
    else:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
except ImportError:
    logger.warning("sentry-sdk not installed, skipping Sentry initialization")
except Exception as e:
    logger.error(f"Failed to initialize Sentry: {e}")

# 创建SQLAlchemy基类
Base = declarative_base()

# 缓存
try:
    # 从环境变量读取 Redis 配置（与 token_blacklist.py 保持一致）
    _redis_host = os.environ.get('REDIS_HOST', os.getenv('REDIS_HOST', 'localhost'))
    _redis_port = int(os.environ.get('REDIS_PORT', os.getenv('REDIS_PORT', 6379)))
    _redis_db = int(os.environ.get('REDIS_DB', os.getenv('REDIS_DB', 0)))
    _redis_password = os.environ.get('REDIS_PASSWORD', os.getenv('REDIS_PASSWORD')) or None

    _redis_client = redis.Redis(
        host=_redis_host,
        port=_redis_port,
        db=_redis_db,
        password=_redis_password,
        decode_responses=True,
        socket_connect_timeout=1,  # 连接超时 1 秒，避免启动阻塞
        socket_timeout=1,  # 读写超时 1 秒
        retry_on_timeout=False,  # 启动时不重试，快速失败
    )
    # 移除 ping()：redis.Redis() 本身是惰性的，首次实际操作时才连接
    logger.info(f"Redis 客户端已创建（惰性连接）: {_redis_host}:{_redis_port}/{_redis_db}")


    # 为 Redis 对象添加兼容的装饰器方法
    def _redis_memoize(timeout=300):
        """Redis memoize 装饰器"""
        import functools
        import json

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 创建缓存键
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

                # 尝试从 Redis 获取
                try:
                    result = _redis_client.get(cache_key)
                    if result is not None:
                        # 尝试反序列化 JSON
                        try:
                            return json.loads(result)
                        except (json.JSONDecodeError, TypeError):
                            return result
                except Exception:
                    pass

                # 执行函数
                result = func(*args, **kwargs)

                # 存储到 Redis
                try:
                    if isinstance(result, (dict, list)):
                        _redis_client.setex(cache_key, timeout, json.dumps(result, ensure_ascii=False))
                    else:
                        _redis_client.setex(cache_key, timeout, str(result))
                except Exception:
                    pass

                return result

            return wrapper

        return decorator


    def _redis_cached(timeout=300, key_prefix=''):
        """Redis cached 装饰器"""
        import functools
        import json

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 创建缓存键
                cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

                # 尝试从 Redis 获取
                try:
                    result = _redis_client.get(cache_key)
                    if result is not None:
                        try:
                            return json.loads(result)
                        except (json.JSONDecodeError, TypeError):
                            return result
                except Exception:
                    pass

                # 执行函数
                result = func(*args, **kwargs)

                # 存储到 Redis
                try:
                    if isinstance(result, (dict, list)):
                        _redis_client.setex(cache_key, timeout, json.dumps(result, ensure_ascii=False))
                    else:
                        _redis_client.setex(cache_key, timeout, str(result))
                except Exception:
                    pass

                return result

            return wrapper

        return decorator


    # 创建兼容的缓存对象，包装 Redis 客户端
    class RedisCacheWrapper:
        """Redis 缓存包装器，提供与 SimpleCache 兼容的接口"""

        def __init__(self, redis_client):
            self._client = redis_client
            self.memoize = _redis_memoize
            self.cached = _redis_cached

        def __getattr__(self, name):
            """代理所有其他属性到 Redis 客户端"""
            return getattr(self._client, name)

        def __call__(self, timeout=300):
            """使对象可以作为装饰器使用"""
            return _redis_cached(timeout=timeout)

        # 代理常用的 Redis 方法
        def get(self, key):
            return self._client.get(key)

        def set(self, key, value, ex=None):
            if ex:
                return self._client.setex(key, ex, value)
            return self._client.set(key, value)

        def delete(self, key):
            return self._client.delete(key)

        def get_with_stale_data(self, key, fallback_func, fresh_timeout=600, stale_timeout=1800):
            """带陈旧数据支持的获取方法（简化版）"""
            result = self.get(key)
            if result is not None:
                try:
                    return json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    return result

            # 缓存未命中，执行回调
            result = fallback_func()
            try:
                if isinstance(result, (dict, list)):
                    self.set(key, json.dumps(result, ensure_ascii=False), ex=fresh_timeout)
                else:
                    self.set(key, str(result), ex=fresh_timeout)
            except Exception:
                pass
            return result


    cache = RedisCacheWrapper(_redis_client)

except (redis.ConnectionError, redis.TimeoutError, redis.RedisError, OSError, ImportError):
    # 如果 Redis 不可用（连接拒绝、超时、其他错误），使用简单内存缓存
    class SimpleCache:
        def __init__(self):
            self._cache = {}
            self._expiry = {}  # 存储过期时间
            self._stats = {  # 缓存统计信息
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0
            }
            self._fallback_mode = False  # 降级模式标志

        def get(self, key):
            """获取缓存值，如果已过期则返回 None"""
            import time

            # 检查是否过期
            if key in self._expiry:
                if time.time() > self._expiry[key]:
                    # 已过期，删除
                    self.delete(key)
                    self._stats['misses'] += 1
                    return None

            value = self._cache.get(key)
            if value is not None:
                self._stats['hits'] += 1
            else:
                self._stats['misses'] += 1
            return value

        def set(self, key, value, ex=None):
            """设置缓存值，ex 参数指定过期时间（秒）"""
            import time

            # 在降级模式下不写入新缓存
            if self._fallback_mode:
                return

            self._cache[key] = value
            self._stats['sets'] += 1

            # 如果指定了过期时间，记录过期时间戳
            if ex is not None and ex > 0:
                self._expiry[key] = time.time() + ex
            elif key in self._expiry:
                # 如果没有指定过期时间但之前有，删除过期时间记录
                del self._expiry[key]

        def mget(self, keys):
            """批量获取缓存值"""
            return {key: self.get(key) for key in keys}

        def mset(self, mapping, ex=None):
            """批量设置缓存值

            Args:
                mapping: 字典，{key: value}
                ex: 过期时间（秒），对所有键相同
            """
            for key, value in mapping.items():
                self.set(key, value, ex)

        def delete_many(self, *keys):
            """批量删除缓存键"""
            for key in keys:
                self.delete(key)

        def clear(self):
            """清空所有缓存"""
            self._cache.clear()
            self._expiry.clear()

        def get_stats(self):
            """获取缓存统计信息"""
            return {
                **self._stats,
                'size': len(self._cache),
                'hit_rate': self._stats['hits'] / (self._stats['hits'] + self._stats['misses'])
                if (self._stats['hits'] + self._stats['misses']) > 0 else 0
            }

        def reset_stats(self):
            """重置统计信息"""
            self._stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0
            }

        def warm_up(self, data_dict, ex=None):
            """缓存预热：批量加载数据到缓存

            Args:
                data_dict: 预热的数据字典 {cache_key: data}
                ex: 过期时间（秒）
            """
            self.mset(data_dict, ex)

        def fallback_get(self, key, fallback_func, ex=300):
            """带降级策略的获取：如果缓存未命中，执行回调函数并缓存结果

            Args:
                key: 缓存键
                fallback_func: 回调函数，当缓存未命中时执行
                ex: 过期时间（秒）

            Returns:
                缓存值或回调函数返回值
            """
            import asyncio

            # 尝试从缓存获取
            value = self.get(key)
            if value is not None:
                return value

            # 缓存未命中，执行回调
            if asyncio.iscoroutinefunction(fallback_func):
                # 如果是异步函数，需要抛出异常让调用者处理
                raise RuntimeError(
                    "Async fallback function not supported in sync context. Use fallback_get_async instead.")
            else:
                # 同步函数
                value = fallback_func()
                self.set(key, value, ex)
                return value

        async def fallback_get_async(self, key, fallback_func, ex=300):
            """异步版本的降级获取

            Args:
                key: 缓存键
                fallback_func: 异步回调函数
                ex: 过期时间（秒）

            Returns:
                缓存值或回调函数返回值
            """
            # 尝试从缓存获取
            value = self.get(key)
            if value is not None:
                return value

            # 缓存未命中，执行异步回调
            value = await fallback_func()
            self.set(key, value, ex)
            return value

        def enable_fallback_mode(self):
            """启用降级模式：停止写入新缓存，只读取现有缓存"""
            self._fallback_mode = True

        def disable_fallback_mode(self):
            """禁用降级模式：恢复正常缓存操作"""
            self._fallback_mode = False

        def is_fallback_mode(self):
            """检查是否在降级模式"""
            return self._fallback_mode

        def delete(self, key):
            """删除缓存键"""
            self._cache.pop(key, None)
            # 同时删除过期时间记录
            self._expiry.pop(key, None)
            self._stats['deletes'] += 1

        def incr(self, key, amount=1):
            """增加缓存值（原子操作）"""
            current_value = self.get(key)
            if current_value is None:
                new_value = amount
            else:
                try:
                    new_value = int(current_value) + amount
                except (ValueError, TypeError):
                    new_value = amount

            self.set(key, str(new_value))
            return new_value

        def memoize(self, timeout=300):
            """
            简单的 memoize 装饰器实现
            :param timeout: 超时时间（秒）
            """

            def decorator(func):
                import asyncio
                import functools

                if asyncio.iscoroutinefunction(func):
                    # 异步函数的处理
                    @functools.wraps(func)
                    async def async_wrapper(*args, **kwargs):
                        # 创建缓存键，将参数转换为字符串
                        cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

                        # 尝试从缓存中获取结果
                        result = self.get(cache_key)
                        if result is not None:
                            return result

                        # 如果缓存中没有，则执行函数并将结果存储在缓存中
                        result = await func(*args, **kwargs)
                        # 在降级模式下不写入新缓存
                        if not self._fallback_mode:
                            self.set(cache_key, result, ex=timeout)
                        return result

                    return async_wrapper
                else:
                    # 同步函数的处理
                    @functools.wraps(func)
                    def sync_wrapper(*args, **kwargs):
                        # 创建缓存键，将参数转换为字符串
                        cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

                        # 尝试从缓存中获取结果
                        result = self.get(cache_key)
                        if result is not None:
                            return result

                        # 如果缓存中没有，则执行函数并将结果存储在缓存中
                        result = func(*args, **kwargs)
                        # 在降级模式下不写入新缓存
                        if not self._fallback_mode:
                            self.set(cache_key, result, ex=timeout)
                        return result

                    return sync_wrapper

            return decorator

        def cached(self, timeout=300, key_prefix=''):
            """
            简单的 cached 装饰器实现
            :param timeout: 超时时间（秒）
            :param key_prefix: 缓存键前缀
            """

            def decorator(func):
                import asyncio
                import functools

                if asyncio.iscoroutinefunction(func):
                    # 异步函数的处理
                    @functools.wraps(func)
                    async def async_wrapper(*args, **kwargs):
                        # 创建缓存键
                        cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

                        # 尝试从缓存中获取结果
                        result = self.get(cache_key)
                        if result is not None:
                            return result

                        # 如果缓存中没有，则执行函数并将结果存储在缓存中
                        result = await func(*args, **kwargs)
                        # 在降级模式下不写入新缓存
                        if not self._fallback_mode:
                            self.set(cache_key, result, ex=timeout)
                        return result

                    return async_wrapper
                else:
                    # 同步函数的处理
                    @functools.wraps(func)
                    def sync_wrapper(*args, **kwargs):
                        # 创建缓存键
                        cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

                        # 尝试从缓存中获取结果
                        result = self.get(cache_key)
                        if result is not None:
                            return result

                        # 如果缓存中没有，则执行函数并将结果存储在缓存中
                        result = func(*args, **kwargs)
                        # 在降级模式下不写入新缓存
                        if not self._fallback_mode:
                            self.set(cache_key, result, ex=timeout)
                        return result

                    return sync_wrapper

            return decorator

        def __call__(self, *args, **kwargs):
            """
            使SimpleCache对象本身可调用，模拟Flask-Cache的用法
            这是为了处理直接调用cache()的情况
            """
            # 如果没有参数，返回自身
            if len(args) == 0 and len(kwargs) == 0:
                return self

            # 如果第一个参数是函数，将其包装为缓存装饰器
            if args and callable(args[0]):
                func = args[0]
                # 默认使用cached装饰器行为
                return self.cached(**kwargs)(func)

            # 否则，根据参数决定行为
            timeout = kwargs.get('timeout', 300)
            key_prefix = kwargs.get('key_prefix', '')
            return self.cached(timeout=timeout, key_prefix=key_prefix)


    cache = SimpleCache()


# JWT 密码哈希上下文
def _get_pwd_context():
    """获取密码上下文，使用纯 bcrypt 实现以避免 passlib 兼容性问题"""
    # 直接使用 bcrypt 实现，避免 passlib 的兼容性问题
    import bcrypt
    class BcryptContext:
        def hash(self, secret):
            # 确保密码不超过 72 字节限制
            if len(secret.encode('utf-8')) > 72:
                secret = secret.encode('utf-8')[:72].decode('utf-8', errors='ignore')
            return bcrypt.hashpw(secret.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        def verify(self, secret, hash):
            try:
                return bcrypt.checkpw(secret.encode('utf-8'), hash.encode('utf-8'))
            except Exception:
                # 处理各种可能的错误情况
                try:
                    return bcrypt.checkpw(secret.encode('utf-8'), hash)
                except Exception:
                    return False

    return BcryptContext()


pwd_context = _get_pwd_context()

# 数据库引擎和会话 - 使用统一管理器
from src.utils.database.unified_manager import (
    db_manager,
)

# 为了向后兼容，保留旧的变量名（但指向统一管理器的实例）
engine = None  # 同步引擎已废弃，仅保留变量
SessionLocal = None  # 同步会话工厂已废弃
_async_engine_instance = None  # 指向统一管理器的引擎
_AsyncSessionLocal_instance = None  # 指向统一管理器的会话工厂


def _get_async_engine():
    """
    延迟获取异步引擎实例（向后兼容）

    注意：这个方法已被弃用，请使用 unified_manager.db_manager
    """
    global _async_engine_instance, _AsyncSessionLocal_instance

    # 确保统一管理器已初始化
    if not db_manager._initialized:
        db_manager.initialize()

    # 返回统一管理器的实例（保持向后兼容）
    _async_engine_instance = db_manager.async_engine
    _AsyncSessionLocal_instance = db_manager.async_session_factory

    return _async_engine_instance, _AsyncSessionLocal_instance


def init_extensions(app):
    """初始化所有FastAPI扩展"""
    global engine, SessionLocal

    # 从设置中获取数据库URL
    try:
        from src.setting import settings
        database_url = settings.database_url
    except ImportError:
        # 如果settings不可用，使用默认配置
        database_url = None

    # 如果数据库URL为 None（安装向导模式），跳过数据库初始化
    if not database_url:
        print("Database URL is not configured. Skipping database initialization.")
        print("This is normal during installation wizard.")
        return

    # 【重要】不再创建独立的引擎和会话工厂
    # 统一管理器已在 app.py 的 lifespan 事件中初始化
    # 这里只保留变量以保持向后兼容性
    engine = db_manager.async_engine.sync_engine if hasattr(db_manager.async_engine, 'sync_engine') else None
    SessionLocal = None  # 同步会话工厂已完全废弃

    print("Using unified database manager (created in lifespan event)")

    # 限流中间件
    try:
        app.state.limiter = Limiter(key_func=get_remote_address)
        app.add_exception_handler(429, _rate_limit_exceeded_handler)
    except Exception as e:
        print(f"Failed to initialize rate limiter: {e}")

    # 【移除】不再在这里创建表，由 Alembic 迁移管理
    # Base.metadata.create_all(bind=engine)  # 已删除


# 便捷函数：获取数据库会话
@contextmanager
def get_db() -> Generator:
    """获取数据库会话的便捷函数"""
    if SessionLocal is None:
        raise RuntimeError("Extensions not initialized. Call init_extensions first.")

    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


# 异步便捷函数：获取异步数据库会话（使用统一管理器）
from contextlib import asynccontextmanager


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator:
    """
    获取异步数据库会话的上下文管理器（用于直接调用）

    这是一个异步上下文管理器，用于在代码中直接使用 async with 语法。
    不应用于 FastAPI 的 Depends() 依赖注入。

    使用示例（直接调用）：
        async with get_async_session_context() as session:
            result = await session.execute(query)
    """
    # 直接使用统一管理器的 get_session 异步上下文管理器
    async with db_manager.get_session() as session:
        yield session


# FastAPI依赖注入函数 - 同步版本
def get_sync_db():
    """FastAPI依赖注入：获取同步数据库会话"""
    with get_db() as session:
        yield session


async def get_async_db_session():
    """
    FastAPI依赖注入：获取异步数据库会话（用于 FastAPI Depends）

    这是一个异步生成器，专门用于 FastAPI 的 Depends() 依赖注入。
    如果需要在代码中直接使用，请使用 get_async_session_context()。
    """
    # 直接使用统一管理器的 get_session 异步上下文管理器
    async with db_manager.get_session() as session:
        yield session
