"""
User 模型的自定义方法定义
这些方法会被自动注入到生成的 SQLAlchemy User 模型中
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
