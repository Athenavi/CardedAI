"""
负载均衡服务
提供多实例部署、健康检查、会话共享和故障转移功能
"""
import json

import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from aioitertools import asyncio

try:
    import redis.asyncio as redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from src.unified_logger import default_logger as logger


class LoadBalancerService:
    """
    负载均衡服务
    
    功能:
    1. 多实例注册和发现
    2. 健康检查
    3. 会话共享（Redis）
    4. 故障转移
    5. 负载均衡策略（轮询、最少连接、加权）
    """

    def __init__(self, redis_url: str = None):
        """
        初始化负载均衡服务
        
        Args:
            redis_url: Redis连接URL（用于会话共享和实例注册）
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL')
        self.redis_client = None
        self.instance_id = self._generate_instance_id()

        # 本地实例信息
        self.local_instance = {
            'id': self.instance_id,
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': int(os.getenv('PORT', '9421')),
            'status': 'starting',
            'started_at': datetime.now().isoformat(),
            'last_heartbeat': None,
            'requests_count': 0,
            'active_connections': 0,
            'weight': 1,  # 权重（用于加权负载均衡）
        }

        # 负载均衡配置
        self.config = {
            'strategy': 'round_robin',  # round_robin, least_connections, weighted
            'health_check_interval': 30,  # 健康检查间隔（秒）
            'health_check_timeout': 5,  # 健康检查超时（秒）
            'max_failures': 3,  # 最大失败次数
            'session_ttl': 3600,  # 会话TTL（秒）
        }

    async def initialize(self):
        """初始化Redis连接和服务"""
        if self.redis_url and HAS_REDIS:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Redis connection established for load balancing")

                # 注册当前实例
                await self.register_instance()

                # 启动心跳
                import asyncio
                asyncio.create_task(self._heartbeat_loop())

            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        else:
            logger.warning("Redis not configured, running in single-instance mode")

    def _generate_instance_id(self) -> str:
        """生成实例ID"""
        import uuid
        hostname = os.getenv('HOSTNAME', 'localhost')
        port = os.getenv('PORT', '9421')
        return f"{hostname}:{port}-{uuid.uuid4().hex[:8]}"

    async def register_instance(self):
        """注册当前实例到服务发现"""
        if not self.redis_client:
            return

        try:
            instance_key = f"lb:instances:{self.instance_id}"

            # 保存实例信息
            await self.redis_client.hset(instance_key, mapping={
                'id': self.local_instance['id'],
                'host': self.local_instance['host'],
                'port': str(self.local_instance['port']),
                'status': 'healthy',
                'started_at': self.local_instance['started_at'],
                'last_heartbeat': datetime.now().isoformat(),
                'weight': str(self.local_instance['weight']),
            })

            # 设置过期时间（如果心跳停止，自动移除）
            await self.redis_client.expire(instance_key, self.config['health_check_interval'] * 3)

            # 添加到实例列表
            await self.redis_client.sadd("lb:instances:active", self.instance_id)

            self.local_instance['status'] = 'healthy'
            self.local_instance['last_heartbeat'] = datetime.now().isoformat()

            logger.info(f"Instance registered: {self.instance_id}")

        except Exception as e:
            logger.error(f"Failed to register instance: {e}")

    async def deregister_instance(self):
        """注销当前实例"""
        if not self.redis_client:
            return

        try:
            instance_key = f"lb:instances:{self.instance_id}"

            # 更新状态为offline
            await self.redis_client.hset(instance_key, 'status', 'offline')

            # 从活动实例列表中移除
            await self.redis_client.srem("lb:instances:active", self.instance_id)

            logger.info(f"Instance deregistered: {self.instance_id}")

        except Exception as e:
            logger.error(f"Failed to deregister instance: {e}")

    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config['health_check_interval'])
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.config['health_check_interval'])

    async def _send_heartbeat(self):
        """发送心跳"""
        if not self.redis_client:
            return

        try:
            instance_key = f"lb:instances:{self.instance_id}"

            # 更新心跳时间和统计信息
            await self.redis_client.hset(instance_key, mapping={
                'last_heartbeat': datetime.now().isoformat(),
                'requests_count': str(self.local_instance['requests_count']),
                'active_connections': str(self.local_instance['active_connections']),
                'status': 'healthy',
            })

            # 刷新过期时间
            await self.redis_client.expire(instance_key, self.config['health_check_interval'] * 3)

            self.local_instance['last_heartbeat'] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            self.local_instance['status'] = 'unhealthy'

    async def get_active_instances(self) -> List[Dict[str, Any]]:
        """
        获取所有活动实例
        
        Returns:
            活动实例列表
        """
        if not self.redis_client:
            return [self.local_instance]

        try:
            instance_ids = await self.redis_client.smembers("lb:instances:active")

            instances = []
            for instance_id in instance_ids:
                instance_key = f"lb:instances:{instance_id}"
                instance_data = await self.redis_client.hgetall(instance_key)

                if instance_data:
                    instance = {
                        'id': instance_data.get('id'),
                        'host': instance_data.get('host'),
                        'port': int(instance_data.get('port', 0)),
                        'status': instance_data.get('status'),
                        'started_at': instance_data.get('started_at'),
                        'last_heartbeat': instance_data.get('last_heartbeat'),
                        'requests_count': int(instance_data.get('requests_count', 0)),
                        'active_connections': int(instance_data.get('active_connections', 0)),
                        'weight': int(instance_data.get('weight', 1)),
                    }

                    # 检查是否超时
                    if instance_data.get('last_heartbeat'):
                        last_hb = datetime.fromisoformat(instance_data['last_heartbeat'])
                        if (datetime.now() - last_hb).total_seconds() > self.config['health_check_interval'] * 3:
                            instance['status'] = 'unhealthy'

                    instances.append(instance)

            return instances

        except Exception as e:
            logger.error(f"Failed to get active instances: {e}")
            return [self.local_instance]

    async def get_next_instance(self, strategy: str = None) -> Optional[Dict[str, Any]]:
        """
        根据负载均衡策略获取下一个实例
        
        Args:
            strategy: 负载均衡策略
            
        Returns:
            选中的实例
        """
        instances = await self.get_active_instances()

        # 过滤健康的实例
        healthy_instances = [i for i in instances if i['status'] == 'healthy']

        if not healthy_instances:
            return None

        strategy = strategy or self.config['strategy']

        if strategy == 'round_robin':
            return self._round_robin_select(healthy_instances)
        elif strategy == 'least_connections':
            return self._least_connections_select(healthy_instances)
        elif strategy == 'weighted':
            return self._weighted_select(healthy_instances)
        else:
            return healthy_instances[0]

    def _round_robin_select(self, instances: List[Dict]) -> Dict:
        """轮询选择"""
        # 简单实现：随机选择一个（实际应该维护一个计数器）
        import random
        return random.choice(instances)

    def _least_connections_select(self, instances: List[Dict]) -> Dict:
        """最少连接选择"""
        return min(instances, key=lambda x: x['active_connections'])

    def _weighted_select(self, instances: List[Dict]) -> Dict:
        """加权选择"""
        total_weight = sum(i['weight'] for i in instances)
        import random
        rand = random.randint(1, total_weight)

        cumulative = 0
        for instance in instances:
            cumulative += instance['weight']
            if rand <= cumulative:
                return instance

        return instances[-1]

    async def record_request(self):
        """记录请求"""
        self.local_instance['requests_count'] += 1

    async def increment_connections(self):
        """增加活跃连接数"""
        self.local_instance['active_connections'] += 1

    async def decrement_connections(self):
        """减少活跃连接数"""
        if self.local_instance['active_connections'] > 0:
            self.local_instance['active_connections'] -= 1

    # ==================== 会话管理 ====================

    async def save_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = None):
        """
        保存会话数据
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
            ttl: TTL（秒）
        """
        if not self.redis_client:
            logger.warning("Redis not available, session not saved")
            return

        try:
            session_key = f"session:{session_id}"
            ttl = ttl or self.config['session_ttl']

            await self.redis_client.setex(
                session_key,
                ttl,
                json.dumps(session_data)
            )

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据
        """
        if not self.redis_client:
            return None

        try:
            session_key = f"session:{session_id}"
            session_data = await self.redis_client.get(session_key)

            if session_data:
                return json.loads(session_data)
            return None

        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    async def delete_session(self, session_id: str):
        """
        删除会话
        
        Args:
            session_id: 会话ID
        """
        if not self.redis_client:
            return

        try:
            session_key = f"session:{session_id}"
            await self.redis_client.delete(session_key)

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")

    # ==================== 健康检查 ====================

    async def check_instance_health(self, instance_id: str) -> Dict[str, Any]:
        """
        检查实例健康状态
        
        Args:
            instance_id: 实例ID
            
        Returns:
            健康检查结果
        """
        if not self.redis_client:
            return {'status': 'unknown'}

        try:
            instance_key = f"lb:instances:{instance_id}"
            instance_data = await self.redis_client.hgetall(instance_key)

            if not instance_data:
                return {'status': 'not_found'}

            # 检查最后心跳时间
            last_heartbeat = instance_data.get('last_heartbeat')
            if last_heartbeat:
                last_hb_time = datetime.fromisoformat(last_heartbeat)
                seconds_since_hb = (datetime.now() - last_hb_time).total_seconds()

                if seconds_since_hb > self.config['health_check_interval'] * 3:
                    health_status = 'unhealthy'
                else:
                    health_status = 'healthy'
            else:
                health_status = 'unknown'

            return {
                'instance_id': instance_id,
                'status': health_status,
                'last_heartbeat': last_heartbeat,
                'requests_count': int(instance_data.get('requests_count', 0)),
                'active_connections': int(instance_data.get('active_connections', 0)),
            }

        except Exception as e:
            logger.error(f"Health check failed for {instance_id}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def get_cluster_stats(self) -> Dict[str, Any]:
        """
        获取集群统计信息
        
        Returns:
            集群统计数据
        """
        instances = await self.get_active_instances()

        total_requests = sum(i['requests_count'] for i in instances)
        total_connections = sum(i['active_connections'] for i in instances)
        healthy_count = len([i for i in instances if i['status'] == 'healthy'])

        return {
            'total_instances': len(instances),
            'healthy_instances': healthy_count,
            'unhealthy_instances': len(instances) - healthy_count,
            'total_requests': total_requests,
            'total_active_connections': total_connections,
            'average_requests_per_instance': total_requests / len(instances) if instances else 0,
            'load_balancing_strategy': self.config['strategy'],
            'instances': instances,
        }

    async def update_config(self, config_updates: Dict[str, Any]):
        """
        更新负载均衡配置
        
        Args:
            config_updates: 配置更新
        """
        self.config.update(config_updates)
        logger.info(f"Load balancer config updated: {config_updates}")


# 全局实例
load_balancer_service = LoadBalancerService()
