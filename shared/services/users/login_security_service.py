"""
登录安全服务
提供异地登录检测、频繁失败锁定、设备指纹识别等功能
"""

import hashlib

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.login_attempt import LoginAttempt

from src.unified_logger import default_logger as logger


class LoginSecurityService:
    """登录安全服务（基于数据库的异步实现）"""

    def __init__(self):
        # 配置参数
        self.max_failures = 5  # 最大失败次数
        self.lock_duration_minutes = 30  # 锁定时长(分钟)
        self.failure_window_minutes = 15  # 失败时间窗口(分钟)

    async def record_login_attempt_async(self, username: str, ip_address: str,
                                         user_agent: str = '', is_success: bool = False,
                                         failure_reason: str = '', db: AsyncSession = None) -> Dict:
        """
        异步记录登录尝试
        
        Args:
            username: 用户名
            ip_address: IP地址
            user_agent: User-Agent
            is_success: 是否成功
            failure_reason: 失败原因
            db: 数据库会话
            
        Returns:
            记录结果
        """
        try:
            now = datetime.now()

            # 创建登录尝试记录
            attempt = LoginAttempt(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                is_success=is_success,
                failure_reason=failure_reason if not is_success else None,
                created_at=now
            )

            if db:
                db.add(attempt)
                await db.commit()
                logger.info(f"Login attempt recorded for user: {username}, success: {is_success}")

            return {'status': 'recorded', 'attempt_id': attempt.id if hasattr(attempt, 'id') else None}
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
            if db:
                await db.rollback()
            return {'status': 'error', 'message': str(e)}

    async def check_account_locked_async(self, username: str, db: AsyncSession = None) -> Tuple[
        bool, Optional[datetime]]:
        """
        异步检查账户是否被锁定（基于用户名）
        
        Args:
            username: 用户名
            db: 数据库会话
            
        Returns:
            (is_locked, unlock_time) 元组
        """
        try:
            if not db:
                return False, None

            now = datetime.now()
            failure_cutoff = now - timedelta(minutes=self.failure_window_minutes)

            # 查询最近失败次数
            result = await db.execute(
                select(func.count(LoginAttempt.id))
                .where(
                    and_(
                        LoginAttempt.username == username,
                        LoginAttempt.is_success == False,
                        LoginAttempt.created_at >= failure_cutoff
                    )
                )
            )
            failure_count = result.scalar() or 0

            if failure_count >= self.max_failures:
                # 获取最后一次失败时间
                last_failure = await db.execute(
                    select(LoginAttempt.created_at)
                    .where(
                        and_(
                            LoginAttempt.username == username,
                            LoginAttempt.is_success == False,
                            LoginAttempt.created_at >= failure_cutoff
                        )
                    )
                    .order_by(LoginAttempt.created_at.desc())
                    .limit(1)
                )
                last_failure_time = last_failure.scalar_one_or_none()

                if last_failure_time:
                    unlock_time = last_failure_time + timedelta(minutes=self.lock_duration_minutes)
                    if now < unlock_time:
                        logger.warning(f"Account locked for user: {username}, failures: {failure_count}")
                        return True, unlock_time

            return False, None
        except Exception as e:
            logger.error(f"Failed to check account lock status: {e}")
            return False, None

    async def get_failed_attempts_count_async(self, username: str, db: AsyncSession = None) -> int:
        """
        异步获取失败尝试次数
        
        Args:
            username: 用户名
            db: 数据库会话
            
        Returns:
            失败尝试次数
        """
        try:
            if not db:
                return 0

            now = datetime.now()
            failure_cutoff = now - timedelta(minutes=self.failure_window_minutes)

            result = await db.execute(
                select(func.count(LoginAttempt.id))
                .where(
                    and_(
                        LoginAttempt.username == username,
                        LoginAttempt.is_success == False,
                        LoginAttempt.created_at >= failure_cutoff
                    )
                )
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to get failed attempts count: {e}")
            return 0

    async def clear_failed_attempts_async(self, username: str, db: AsyncSession = None) -> bool:
        """
        异步清除失败尝试记录
        
        Args:
            username: 用户名
            db: 数据库会话
            
        Returns:
            是否成功清除
        """
        try:
            if not db:
                return False

            now = datetime.now()
            failure_cutoff = now - timedelta(minutes=self.failure_window_minutes)

            # 删除指定时间窗口内的失败记录
            await db.execute(
                LoginAttempt.__table__.delete()
                .where(
                    and_(
                        LoginAttempt.username == username,
                        LoginAttempt.is_success == False,
                        LoginAttempt.created_at >= failure_cutoff
                    )
                )
            )
            await db.commit()

            logger.info(f"Cleared failed attempts for user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear failed attempts: {e}")
            if db:
                await db.rollback()
            return False

    async def get_login_history_async(self, username: str, limit: int = 50, db: AsyncSession = None) -> List[Dict]:
        """
        异步获取用户登录历史
        
        Args:
            username: 用户名
            limit: 返回数量
            db: 数据库会话
            
        Returns:
            登录历史记录
        """
        try:
            if not db:
                return []

            result = await db.execute(
                select(LoginAttempt)
                .where(LoginAttempt.username == username)
                .order_by(LoginAttempt.created_at.desc())
                .limit(limit)
            )
            attempts = result.scalars().all()

            return [
                {
                    'timestamp': attempt.created_at.isoformat() if attempt.created_at else None,
                    'ip_address': attempt.ip_address,
                    'user_agent': attempt.user_agent,
                    'is_success': attempt.is_success,
                    'failure_reason': attempt.failure_reason,
                }
                for attempt in attempts
            ]
        except Exception as e:
            logger.error(f"Failed to get login history: {e}")
            return []

    async def get_security_stats_async(self, username: str, db: AsyncSession = None) -> Dict:
        """
        异步获取用户安全统计
        
        Args:
            username: 用户名
            db: 数据库会话
            
        Returns:
            统计数据
        """
        try:
            if not db:
                return {}

            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            failure_cutoff = now - timedelta(minutes=self.failure_window_minutes)

            # 总登录次数
            total_result = await db.execute(
                select(func.count(LoginAttempt.id))
                .where(LoginAttempt.username == username)
            )
            total_logins = total_result.scalar() or 0

            # 成功登录次数
            success_result = await db.execute(
                select(func.count(LoginAttempt.id))
                .where(
                    and_(
                        LoginAttempt.username == username,
                        LoginAttempt.is_success == True
                    )
                )
            )
            successful_logins = success_result.scalar() or 0

            # 失败次数
            failed_logins = total_logins - successful_logins

            # 唯一IP数量
            ip_result = await db.execute(
                select(func.count(func.distinct(LoginAttempt.ip_address)))
                .where(
                    and_(
                        LoginAttempt.username == username,
                        LoginAttempt.is_success == True
                    )
                )
            )
            unique_ips = ip_result.scalar() or 0

            # 最近7天登录次数
            recent_result = await db.execute(
                select(func.count(LoginAttempt.id))
                .where(
                    and_(
                        LoginAttempt.username == username,
                        LoginAttempt.is_success == True,
                        LoginAttempt.created_at >= seven_days_ago
                    )
                )
            )
            recent_7days_logins = recent_result.scalar() or 0

            # 当前失败次数（在时间窗口内）
            current_failures_result = await db.execute(
                select(func.count(LoginAttempt.id))
                .where(
                    and_(
                        LoginAttempt.username == username,
                        LoginAttempt.is_success == False,
                        LoginAttempt.created_at >= failure_cutoff
                    )
                )
            )
            current_failures = current_failures_result.scalar() or 0

            # 检查是否被锁定
            is_locked = current_failures >= self.max_failures

            return {
                'total_logins': total_logins,
                'successful_logins': successful_logins,
                'failed_logins': failed_logins,
                'unique_ips': unique_ips,
                'recent_7days_logins': recent_7days_logins,
                'current_failures': current_failures,
                'is_locked': is_locked,
            }
        except Exception as e:
            logger.error(f"Failed to get security stats: {e}")
            return {}

    async def get_locked_users_async(self, db: AsyncSession = None) -> List[Dict]:
        """
        异步获取所有被锁定的用户(管理员)
        
        Args:
            db: 数据库会话
            
        Returns:
            锁定用户列表
        """
        try:
            if not db:
                return []

            now = datetime.now()
            failure_cutoff = now - timedelta(minutes=self.failure_window_minutes)

            # 查询失败次数超过阈值的用户名
            result = await db.execute(
                select(
                    LoginAttempt.username,
                    func.count(LoginAttempt.id).label('failure_count'),
                    func.max(LoginAttempt.created_at).label('last_failure')
                )
                .where(
                    and_(
                        LoginAttempt.is_success == False,
                        LoginAttempt.created_at >= failure_cutoff
                    )
                )
                .group_by(LoginAttempt.username)
                .having(func.count(LoginAttempt.id) >= self.max_failures)
            )

            locked_users = []
            for row in result.all():
                username, failure_count, last_failure = row
                unlock_time = last_failure + timedelta(minutes=self.lock_duration_minutes)

                if now < unlock_time:
                    remaining_seconds = (unlock_time - now).total_seconds()
                    locked_users.append({
                        'username': username,
                        'locked_at': last_failure.isoformat(),
                        'lock_until': unlock_time.isoformat(),
                        'remaining_minutes': int(remaining_seconds / 60),
                        'failure_count': failure_count,
                    })

            return locked_users
        except Exception as e:
            logger.error(f"Failed to get locked users: {e}")
            return []

    def _generate_device_fingerprint(self, device_info: Dict,
                                     user_agent: str = '') -> str:
        """
        生成设备指纹（保留用于向后兼容）
        
        Args:
            device_info: 设备信息
            user_agent: User-Agent
            
        Returns:
            设备指纹哈希
        """
        data = f"{device_info}:{user_agent}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

# 全局实例
login_security_service = LoginSecurityService()
