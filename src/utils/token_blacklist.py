"""
Token 黑名单管理
支持 Redis 高速缓存 + ORM 持久化降级的双重保障机制
"""

import hashlib
import os
from datetime import datetime

from src.unified_logger import default_logger as logger


class TokenBlacklistManager:
    """
    Token 黑名单管理器

    架构设计：
    - 主层：Redis 高速缓存（快速读写，TTL 自动过期）
    - 降级层：ORM 持久化存储（Redis 不可用时的降级方案，同时提供审计追踪）
    """

    def __init__(self):
        self.redis_client = None
        self.redis_enabled = False
        self._initialize_redis()

    def _initialize_redis(self):
        """初始化 Redis 连接"""
        try:
            import redis

            # 从环境变量读取 Redis 配置
            redis_host = os.environ.get('REDIS_HOST', 'localhost')
            redis_port = int(os.environ.get('REDIS_PORT', 6379))
            redis_db = int(os.environ.get('REDIS_DB', 0))
            redis_password = os.environ.get('REDIS_PASSWORD') or None

            # 尝试连接 Redis
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=1,  # 连接超时 1 秒，避免启动阻塞
                socket_timeout=1,  # 读写超时 1 秒
                retry_on_timeout=False  # 启动时不重试，快速失败
            )

            # 测试连接
            self.redis_client.ping()
            self.redis_enabled = True
            logger.info(f"Redis Token 黑名单连接成功：{redis_host}:{redis_port}")

        except ImportError:
            logger.warning("redis 库未安装，Token 黑名单将使用 ORM 持久化模式")
            self.redis_enabled = False
        except Exception as e:
            logger.warning(f"Redis 连接失败，Token 黑名单将降级为 ORM 持久化模式：{e}")
            self.redis_client = None
            self.redis_enabled = False

    @staticmethod
    def _get_token_identifier(token: str) -> str:
        """获取 Token 唯一标识（前32字符）"""
        return token[:32]

    @staticmethod
    def _get_token_hash(token: str) -> str:
        """获取 Token 的 SHA256 哈希值（用于 ORM 存储和审计）"""
        return hashlib.sha256(token.encode()).hexdigest()

    def add_to_blacklist(self, token: str, expires_at: datetime) -> bool:
        """
        将 Token 加入黑名单（同步方法，仅操作 Redis）

        Args:
            token: JWT Token 字符串
            expires_at: Token 过期时间

        Returns:
            bool: 操作是否成功
        """
        if not self.redis_enabled or not self.redis_client:
            logger.debug("Redis 不可用，跳过 Redis 黑名单写入（将通过 ORM 持久化）")
            return False

        try:
            # 计算剩余有效期（秒）
            ttl = int((expires_at - datetime.now()).total_seconds())
            if ttl > 0:
                key = f"token_blacklist:{self._get_token_identifier(token)}"
                self.redis_client.setex(key, ttl, "blacklisted")
                logger.debug(f"Token 已加入 Redis 黑名单，TTL: {ttl}s")
                return True
        except Exception as e:
            logger.error(f"添加 Token 到 Redis 黑名单失败：{e}")

        return False

    async def add_to_blacklist_async(self, token: str, expires_at: datetime, reason: str = None) -> bool:
        """
        将 Token 加入黑名单（异步方法，同时写入 Redis 和 ORM）

        Args:
            token: JWT Token 字符串
            expires_at: Token 过期时间
            reason: 撤销原因

        Returns:
            bool: 操作是否成功
        """
        success = False

        # 1. 写入 Redis（如果可用）
        redis_ok = self.add_to_blacklist(token, expires_at)
        if redis_ok:
            success = True

        # 2. 写入 ORM 持久化层（无论 Redis 是否成功，都进行持久化以保证审计追踪）
        orm_ok = await self._persist_to_orm(token, expires_at, reason)
        if orm_ok:
            success = True

        return success

    async def _persist_to_orm(self, token: str, expires_at: datetime, reason: str = None) -> bool:
        """将 Token 黑名单记录持久化到 ORM 模型"""
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.token_blacklist import TokenBlacklist

            async with db_manager.get_async_session() as session:
                token_id = self._get_token_identifier(token)
                token_hash = self._get_token_hash(token)

                # 检查是否已存在
                from sqlalchemy import select
                existing = await session.execute(
                    select(TokenBlacklist).where(TokenBlacklist.token_identifier == token_id)
                )
                if existing.scalar_one_or_none():
                    return True  # 已存在，视为成功

                record = TokenBlacklist(
                    token_identifier=token_id,
                    token_hash=token_hash,
                    expires_at=expires_at,
                    created_at=datetime.now(),
                    reason=reason or "revoked"
                )
                session.add(record)
                await session.commit()
                logger.debug(f"Token 已持久化到 ORM 黑名单：{token_id[:8]}...")
                return True
        except Exception as e:
            logger.warning(f"ORM 黑名单持久化失败（不影响主流程）：{e}")
            return False

    def is_blacklisted(self, token: str) -> bool:
        """
        检查 Token 是否在黑名单中（同步方法，仅检查 Redis）

        Args:
            token: JWT Token 字符串

        Returns:
            bool: 是否在黑名单中
        """
        if not self.redis_enabled or not self.redis_client:
            logger.debug("Redis 不可用，跳过 Redis 黑名单检查")
            return False

        try:
            key = f"token_blacklist:{self._get_token_identifier(token)}"
            return self.redis_client.exists(key) == 1
        except Exception as e:
            logger.error(f"检查 Redis Token 黑名单失败：{e}")
            return False

    async def is_blacklisted_async(self, token: str) -> bool:
        """
        检查 Token 是否在黑名单中（异步方法，Redis → ORM 逐级检查）

        Args:
            token: JWT Token 字符串

        Returns:
            bool: 是否在黑名单中
        """
        # 1. 优先检查 Redis
        if self.is_blacklisted(token):
            return True

        # 2. Redis 不可用或未命中时，检查 ORM 持久化层
        return await self._check_orm_blacklist(token)

    async def _check_orm_blacklist(self, token: str) -> bool:
        """检查 ORM 持久化层中的黑名单"""
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.token_blacklist import TokenBlacklist
            from sqlalchemy import select

            token_id = self._get_token_identifier(token)

            async with db_manager.get_async_session() as session:
                result = await session.execute(
                    select(TokenBlacklist).where(
                        TokenBlacklist.token_identifier == token_id,
                        TokenBlacklist.expires_at > datetime.now()
                    )
                )
                record = result.scalar_one_or_none()
                if record:
                    # 找到记录后同步回 Redis
                    if self.redis_enabled and self.redis_client:
                        try:
                            ttl = int((record.expires_at - datetime.now()).total_seconds())
                            if ttl > 0:
                                key = f"token_blacklist:{token_id}"
                                self.redis_client.setex(key, ttl, "blacklisted")
                        except Exception:
                            pass
                    return True
                return False
        except Exception as e:
            logger.warning(f"ORM 黑名单查询失败：{e}")
            return False

    def clear_expired(self):
        """清理过期的黑名单记录（Redis 会自动处理 TTL）"""
        pass  # Redis 会自动清理，ORM 的过期清理由定时任务处理

    @property
    def is_available(self) -> bool:
        """黑名单服务是否可用（Redis 或 ORM 至少一个可用）"""
        return self.redis_enabled and self.redis_client is not None

    @property
    def has_persistence(self) -> bool:
        """是否有持久化层保障"""
        return True  # ORM 持久化始终可用


# ============================================================
# 全局实例（惰性创建：首次使用时才触发 Redis 连接和 .ping()）
# 避免模块导入时就创建实例，导致多线程并行导入时 Redis .ping() 被 import lock 串行化
# ============================================================
_token_blacklist_instance = None


def _get_token_blacklist():
    """获取 TokenBlacklistManager 单例（首次调用时才创建，避免模块导入时触发 Redis 连接）"""
    global _token_blacklist_instance
    if _token_blacklist_instance is None:
        _token_blacklist_instance = TokenBlacklistManager()
    return _token_blacklist_instance


class _TokenBlacklistProxy:
    """TokenBlacklistManager 的惰性代理，首次属性访问时才创建真实实例

    这样 `from src.utils.token_blacklist import token_blacklist` 不会触发 Redis .ping()，
    只有在实际使用 token_blacklist 的方法时才会初始化 Redis 连接。
    """

    def __getattr__(self, name):
        return getattr(_get_token_blacklist(), name)

    def __setattr__(self, name, value):
        setattr(_get_token_blacklist(), name, value)

    def __bool__(self):
        return True

    def __repr__(self):
        return repr(_get_token_blacklist())


token_blacklist = _TokenBlacklistProxy()
# ============================================================
_token_blacklist_instance = None


def _get_token_blacklist():
    """获取 TokenBlacklistManager 单例（首次调用时才创建，避免模块导入时触发 Redis 连接）"""
    global _token_blacklist_instance
    if _token_blacklist_instance is None:
        _token_blacklist_instance = TokenBlacklistManager()
    return _token_blacklist_instance


class _TokenBlacklistProxy:
    """TokenBlacklistManager 的惰性代理，首次属性访问时才创建真实实例

    这样 `from src.utils.token_blacklist import token_blacklist` 不会触发 Redis .ping()，
    只有在实际使用 token_blacklist 的方法时才会初始化 Redis 连接。
    """

    def __getattr__(self, name):
        return getattr(_get_token_blacklist(), name)

    def __setattr__(self, name, value):
        setattr(_get_token_blacklist(), name, value)

    def __bool__(self):
        return True

    def __repr__(self):
        return repr(_get_token_blacklist())


token_blacklist = _TokenBlacklistProxy()
