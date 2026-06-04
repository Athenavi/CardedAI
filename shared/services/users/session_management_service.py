"""
会话管理服务
提供会话追踪、设备管理、远程注销等功能
"""


import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from src.unified_logger import default_logger as logger


class SessionManagementService:
    """会话管理服务"""

    def __init__(self):
        # 用户会话存储 {user_id: [session_info, ...]}
        self._user_sessions = defaultdict(list)

        # 会话索引 {session_id: user_id}
        self._session_index = {}

        # 默认配置
        self.session_timeout_hours = 24 * 30  # 30天
        self.max_sessions_per_user = 10  # 每个用户最多10个活跃会话

    def create_session(self, user_id: int, device_info: Dict,
                       ip_address: str = None, user_agent: str = None) -> str:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            device_info: 设备信息
            ip_address: IP地址
            user_agent: User-Agent字符串
            
        Returns:
            会话ID
        """
        # 生成会话ID
        session_id = self._generate_session_id(user_id, device_info, ip_address)

        # 检查并清理旧会话
        self._cleanup_old_sessions(user_id)

        # 检查会话数量限制
        if len(self._user_sessions[user_id]) >= self.max_sessions_per_user:
            # 移除最旧的会话
            oldest_session = min(
                self._user_sessions[user_id],
                key=lambda s: s['created_at']
            )
            self._remove_session(user_id, oldest_session['session_id'])

        # 创建会话记录
        now = datetime.now()
        session = {
            'session_id': session_id,
            'user_id': user_id,
            'device_info': device_info,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'device_fingerprint': self._generate_device_fingerprint(device_info, user_agent),
            'created_at': now,
            'last_active': now,
            'expires_at': now + timedelta(hours=self.session_timeout_hours),
            'is_active': True,
            'location': self._estimate_location(ip_address),
        }

        # 存储会话
        self._user_sessions[user_id].append(session)
        self._session_index[session_id] = user_id

        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """
        获取用户的所有活跃会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            会话列表
        """
        sessions = []

        for session in self._user_sessions.get(user_id, []):
            if session['is_active'] and session['expires_at'] > datetime.now():
                sessions.append({
                    'session_id': session['session_id'],
                    'device_info': session['device_info'],
                    'ip_address': session['ip_address'],
                    'user_agent': session['user_agent'],
                    'device_fingerprint': session['device_fingerprint'],
                    'created_at': session['created_at'].isoformat(),
                    'last_active': session['last_active'].isoformat(),
                    'expires_at': session['expires_at'].isoformat(),
                    'location': session.get('location', 'Unknown'),
                    'is_current': False,  # 需要调用方判断
                })

        # 按最后活动时间排序
        sessions.sort(key=lambda s: s['last_active'], reverse=True)

        return sessions

    def update_session_activity(self, session_id: str):
        """
        更新会话活动时间
        
        Args:
            session_id: 会话ID
        """
        if session_id not in self._session_index:
            return

        user_id = self._session_index[session_id]

        for session in self._user_sessions.get(user_id, []):
            if session['session_id'] == session_id:
                session['last_active'] = datetime.now()
                break

    def revoke_session(self, user_id: int, session_id: str) -> bool:
        """
        撤销指定会话(远程注销)
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        return self._remove_session(user_id, session_id)

    def revoke_all_sessions(self, user_id: int, exclude_session_id: str = None) -> int:
        """
        撤销用户的所有会话(除当前会话外)
        
        Args:
            user_id: 用户ID
            exclude_session_id: 排除的会话ID(当前会话)
            
        Returns:
            撤销的会话数量
        """
        revoked_count = 0

        sessions_to_remove = []
        for session in self._user_sessions.get(user_id, []):
            if session['is_active'] and session['session_id'] != exclude_session_id:
                sessions_to_remove.append(session['session_id'])

        for session_id in sessions_to_remove:
            if self._remove_session(user_id, session_id):
                revoked_count += 1

        logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
        return revoked_count

    def is_session_valid(self, session_id: str) -> bool:
        """
        检查会话是否有效
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否有效
        """
        if session_id not in self._session_index:
            return False

        user_id = self._session_index[session_id]

        for session in self._user_sessions.get(user_id, []):
            if session['session_id'] == session_id:
                # 检查是否激活且未过期
                if not session['is_active']:
                    return False
                if session['expires_at'] <= datetime.now():
                    return False
                return True

        return False

    def get_session_details(self, session_id: str) -> Optional[Dict]:
        """
        获取会话详细信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话详情
        """
        if session_id not in self._session_index:
            return None

        user_id = self._session_index[session_id]

        for session in self._user_sessions.get(user_id, []):
            if session['session_id'] == session_id:
                return {
                    'session_id': session['session_id'],
                    'user_id': session['user_id'],
                    'device_info': session['device_info'],
                    'ip_address': session['ip_address'],
                    'user_agent': session['user_agent'],
                    'device_fingerprint': session['device_fingerprint'],
                    'created_at': session['created_at'].isoformat(),
                    'last_active': session['last_active'].isoformat(),
                    'expires_at': session['expires_at'].isoformat(),
                    'is_active': session['is_active'],
                    'location': session.get('location', 'Unknown'),
                }

        return None

    def detect_suspicious_activity(self, user_id: int,
                                   current_ip: str,
                                   current_device_fingerprint: str) -> List[Dict]:
        """
        检测可疑活动(异地登录、新设备等)
        
        Args:
            user_id: 用户ID
            current_ip: 当前IP地址
            current_device_fingerprint: 当前设备指纹
            
        Returns:
            可疑活动列表
        """
        alerts = []
        active_sessions = self.get_user_sessions(user_id)

        if not active_sessions:
            return alerts

        # 检查是否有不同IP的活跃会话
        ips = set(s['ip_address'] for s in active_sessions if s['ip_address'])
        if current_ip and current_ip not in ips:
            alerts.append({
                'type': 'new_location',
                'severity': 'warning',
                'message': f'检测到新的登录地点: {current_ip}',
                'ip_address': current_ip,
            })

        # 检查是否有新设备
        fingerprints = set(s['device_fingerprint'] for s in active_sessions)
        if current_device_fingerprint and current_device_fingerprint not in fingerprints:
            alerts.append({
                'type': 'new_device',
                'severity': 'info',
                'message': '检测到新设备登录',
                'device_fingerprint': current_device_fingerprint,
            })

        # 检查并发会话数
        if len(active_sessions) > 5:
            alerts.append({
                'type': 'many_sessions',
                'severity': 'warning',
                'message': f'当前有 {len(active_sessions)} 个活跃会话',
                'session_count': len(active_sessions),
            })

        return alerts

    def _generate_session_id(self, user_id: int, device_info: Dict,
                             ip_address: str = None) -> str:
        """
        生成会话ID
        
        Args:
            user_id: 用户ID
            device_info: 设备信息
            ip_address: IP地址
            
        Returns:
            会话ID
        """
        data = f"{user_id}:{device_info}:{ip_address}:{datetime.now().timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _generate_device_fingerprint(self, device_info: Dict,
                                     user_agent: str = None) -> str:
        """
        生成设备指纹
        
        Args:
            device_info: 设备信息
            user_agent: User-Agent字符串
            
        Returns:
            设备指纹
        """
        data = f"{device_info}:{user_agent}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _estimate_location(self, ip_address: str = None) -> str:
        """
        估算位置(基于IP)
        
        Args:
            ip_address: IP地址
            
        Returns:
            位置描述
        """
        if not ip_address:
            return 'Unknown'

        # 检查是否为本地地址
        if ip_address.startswith('192.168') or ip_address.startswith('10.'):
            return 'Local Network'
        elif ip_address.startswith('127.'):
            return 'localhost'

        # 集成IP地理位置服务
        try:
            location_info = self._get_location_from_ip(ip_address)
            if location_info:
                city = location_info.get('city', '')
                region = location_info.get('region', '')
                country = location_info.get('country', '')

                if city and country:
                    return f"{city}, {region}, {country}" if region else f"{city}, {country}"
                elif country:
                    return country
                else:
                    return f'IP: {ip_address}'
        except Exception as e:
            logger.debug(f"Failed to get location from IP: {e}")

        # 降级方案：返回IP地址
        return f'IP: {ip_address}'

    def _get_location_from_ip(self, ip_address: str) -> Dict[str, str]:
        """
        从IP地址获取地理位置信息
        
        Args:
            ip_address: IP地址
            
        Returns:
            包含城市、地区、国家信息的字典，失败返回None
        """
        # 方法1: 使用 ipapi.co API (免费，无需API key)
        try:
            import urllib.request
            import json

            url = f"https://ipapi.co/{ip_address}/json/"
            response = urllib.request.urlopen(url, timeout=3)
            data = json.loads(response.read().decode('utf-8'))

            if data.get('error'):
                logger.debug(f"ipapi.co error: {data.get('reason')}")
                return None

            location = {
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'country': data.get('country_name', ''),
                'country_code': data.get('country', ''),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
            }

            logger.info(f"Location detected for IP {ip_address}: {location['city']}, {location['country']}")
            return location
        except Exception as e:
            logger.debug(f"ipapi.co failed: {e}")

        # 方法2: 使用 ipgeolocation.io API (需要API key)
        api_key = os.getenv('IPGEOLOCATION_API_KEY', '')
        if api_key:
            try:
                import urllib.request
                import json

                url = f"https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip_address}"
                response = urllib.request.urlopen(url, timeout=3)
                data = json.loads(response.read().decode('utf-8'))

                location = {
                    'city': data.get('city', ''),
                    'region': data.get('state_prov', ''),
                    'country': data.get('country_name', ''),
                    'country_code': data.get('country_code2', ''),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                }

                logger.info(f"Location detected for IP {ip_address}: {location['city']}, {location['country']}")
                return location
            except Exception as e:
                logger.debug(f"ipgeolocation.io failed: {e}")

        # 方法3: 使用 ipinfo.io API (可选API key)
        try:
            import urllib.request
            import json

            token = os.getenv('IPINFO_TOKEN', '')
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            url = f"https://ipinfo.io/{ip_address}/json"

            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=3)
            data = json.loads(response.read().decode('utf-8'))

            if 'bogon' in data:
                return None

            # ipinfo.io 的 city 格式为 "City, Region"
            city_region = data.get('city', '').split(',')

            location = {
                'city': city_region[0] if city_region else '',
                'region': city_region[1].strip() if len(city_region) > 1 else '',
                'country': data.get('country', ''),
                'country_code': data.get('country', ''),
            }

            logger.info(f"Location detected for IP {ip_address}: {location['city']}, {location['country']}")
            return location
        except Exception as e:
            logger.debug(f"ipinfo.io failed: {e}")

        return None

    def _cleanup_old_sessions(self, user_id: int):
        """
        清理过期会话
        
        Args:
            user_id: 用户ID
        """
        now = datetime.now()
        expired_sessions = [
            s for s in self._user_sessions.get(user_id, [])
            if s['expires_at'] <= now or not s['is_active']
        ]

        for session in expired_sessions:
            self._remove_session(user_id, session['session_id'])

    def _remove_session(self, user_id: int, session_id: str) -> bool:
        """
        移除会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        sessions = self._user_sessions.get(user_id, [])

        for i, session in enumerate(sessions):
            if session['session_id'] == session_id:
                session['is_active'] = False
                session['expires_at'] = datetime.now()

                # 从索引中移除
                if session_id in self._session_index:
                    del self._session_index[session_id]

                logger.info(f"Removed session {session_id} for user {user_id}")
                return True

        return False

    def get_session_stats(self) -> Dict:
        """
        获取会话统计信息
        
        Returns:
            统计数据
        """
        total_sessions = sum(len(sessions) for sessions in self._user_sessions.values())
        active_sessions = sum(
            1 for sessions in self._user_sessions.values()
            for s in sessions
            if s['is_active'] and s['expires_at'] > datetime.now()
        )
        
        return {
            'total_users_with_sessions': len(self._user_sessions),
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
        }


# 全局实例
session_management_service = SessionManagementService()
