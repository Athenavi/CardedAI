"""
示例：共享的自定义方法定义
这个文件可以包含多个模型共用的方法
"""
from datetime import datetime


def is_vip(self) -> bool:
    """
    判断是否为 VIP 用户
    
    Returns:
        bool: 是否为 VIP 用户
    """
    if not self.vip_level:
        return False
    
    # 检查 VIP 是否过期
    if self.vip_expires_at:
        try:
            # 如果 vip_expires_at 是字符串，尝试解析
            if isinstance(self.vip_expires_at, str):
                expires = datetime.fromisoformat(self.vip_expires_at.replace('Z', '+00:00'))
                return datetime.now(expires.tzinfo) < expires
            else:
                # 如果是 datetime 对象
                tzinfo = getattr(self.vip_expires_at, 'tzinfo', None)
                return datetime.now(tzinfo) < self.vip_expires_at
        except Exception:
            # 如果解析失败，只检查 vip_level
            return self.vip_level > 0
    
    return self.vip_level > 0


def get_display_name(self) -> str:
    """
    获取显示名称
    
    Returns:
        str: 显示名称（优先返回 username）
    """
    if hasattr(self, 'username'):
        return self.username
    if hasattr(self, 'name'):
        return self.name
    return f"User_{self.id}"
