"""
维护模式服务 - 管理系统维护状态
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


class MaintenanceModeService:
    """维护模式服务"""
    
    def __init__(self):
        self.config_file = Path("storage/maintenance_mode.json")
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """加载维护模式配置"""
        if not self.config_file.exists():
            return {
                "enabled": False,
                "message": "系统正在维护中，请稍后访问",
                "whitelist_ips": [],
                "scheduled_start": None,
                "scheduled_end": None,
                "retry_after": 3600,
                "updated_at": None
            }
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return self.get_default_config()
    
    def save_config(self, config: Dict[str, Any]):
        """保存维护模式配置"""
        config['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "enabled": False,
            "message": "系统正在维护中，请稍后访问",
            "whitelist_ips": [],
            "scheduled_start": None,
            "scheduled_end": None,
            "retry_after": 3600,
            "updated_at": None
        }
    
    def is_maintenance_mode(self, client_ip: Optional[str] = None) -> bool:
        """
        检查是否处于维护模式
        
        Args:
            client_ip: 客户端IP地址
            
        Returns:
            是否处于维护模式
        """
        config = self.load_config()
        
        # 如果未启用维护模式，直接返回False
        if not config.get('enabled', False):
            return False
        
        # 检查定时维护时间
        scheduled_start = config.get('scheduled_start')
        scheduled_end = config.get('scheduled_end')
        
        if scheduled_start and scheduled_end:
            now = datetime.now(timezone.utc)
            start_time = datetime.fromisoformat(scheduled_start.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(scheduled_end.replace('Z', '+00:00'))
            
            # 如果当前时间在维护时间段内，自动启用
            if start_time <= now <= end_time:
                config['enabled'] = True
                self.save_config(config)
            elif now > end_time:
                # 已过维护时间，自动关闭
                config['enabled'] = False
                config['scheduled_start'] = None
                config['scheduled_end'] = None
                self.save_config(config)
                return False
        
        # 检查IP白名单
        if client_ip and client_ip in config.get('whitelist_ips', []):
            return False
        
        return True
    
    def enable_maintenance(self, message: Optional[str] = None, 
                          whitelist_ips: Optional[List[str]] = None,
                          retry_after: int = 3600) -> Dict[str, Any]:
        """
        启用维护模式
        
        Args:
            message: 维护提示信息
            whitelist_ips: IP白名单列表
            retry_after: Retry-After头部的秒数
            
        Returns:
            更新后的配置
        """
        config = self.load_config()
        config['enabled'] = True
        
        if message:
            config['message'] = message
        
        if whitelist_ips is not None:
            config['whitelist_ips'] = whitelist_ips
        
        config['retry_after'] = retry_after
        config['scheduled_start'] = None
        config['scheduled_end'] = None
        
        self.save_config(config)
        return config
    
    def disable_maintenance(self) -> Dict[str, Any]:
        """
        禁用维护模式
        
        Returns:
            更新后的配置
        """
        config = self.load_config()
        config['enabled'] = False
        config['scheduled_start'] = None
        config['scheduled_end'] = None
        
        self.save_config(config)
        return config
    
    def schedule_maintenance(self, start_time: str, end_time: str,
                            message: Optional[str] = None,
                            whitelist_ips: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        计划维护时间
        
        Args:
            start_time: 开始时间(ISO格式)
            end_time: 结束时间(ISO格式)
            message: 维护提示信息
            whitelist_ips: IP白名单列表
            
        Returns:
            更新后的配置
        """
        config = self.load_config()
        config['scheduled_start'] = start_time
        config['scheduled_end'] = end_time
        
        if message:
            config['message'] = message
        
        if whitelist_ips is not None:
            config['whitelist_ips'] = whitelist_ips
        
        self.save_config(config)
        return config
    
    def add_whitelist_ip(self, ip: str) -> Dict[str, Any]:
        """
        添加IP到白名单
        
        Args:
            ip: IP地址
            
        Returns:
            更新后的配置
        """
        config = self.load_config()
        
        if ip not in config.get('whitelist_ips', []):
            config.setdefault('whitelist_ips', []).append(ip)
            self.save_config(config)
        
        return config
    
    def remove_whitelist_ip(self, ip: str) -> Dict[str, Any]:
        """
        从白名单移除IP
        
        Args:
            ip: IP地址
            
        Returns:
            更新后的配置
        """
        config = self.load_config()
        
        if 'whitelist_ips' in config and ip in config['whitelist_ips']:
            config['whitelist_ips'].remove(ip)
            self.save_config(config)
        
        return config
    
    def update_message(self, message: str) -> Dict[str, Any]:
        """
        更新维护提示信息
        
        Args:
            message: 新的提示信息
            
        Returns:
            更新后的配置
        """
        config = self.load_config()
        config['message'] = message
        self.save_config(config)
        return config
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取维护模式状态
        
        Returns:
            状态信息
        """
        config = self.load_config()
        
        status = {
            "enabled": config['enabled'],
            "message": config.get('message', ''),
            "whitelist_ips": config.get('whitelist_ips', []),
            "retry_after": config.get('retry_after', 3600),
            "scheduled_start": config.get('scheduled_start'),
            "scheduled_end": config.get('scheduled_end'),
            "updated_at": config.get('updated_at')
        }
        
        # 计算距离计划维护的时间
        if config.get('scheduled_start'):
            now = datetime.now(timezone.utc)
            start_time = datetime.fromisoformat(config['scheduled_start'].replace('Z', '+00:00'))
            
            if start_time > now:
                status['time_until_maintenance'] = (start_time - now).total_seconds()
            else:
                status['time_until_maintenance'] = 0
        
        return status


# 全局实例
maintenance_service = MaintenanceModeService()
