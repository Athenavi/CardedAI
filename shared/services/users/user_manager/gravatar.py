"""
Gravatar头像服务
根据用户邮箱生成全球通用的头像URL
"""

import hashlib
import re

# 常量定义
GRAVATAR_BASE_URL = "https://www.gravatar.com/avatar/"
CDN_BASE_URL = "https://cravatar.cn/avatar/"
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
DEFAULT_SIZES = [32, 64, 128, 256]
VALID_RATINGS = frozenset(['g', 'pg', 'r', 'x'])


class GravatarService:
    """
    Gravatar头像服务
    
    功能:
    1. 根据邮箱生成Gravatar URL
    2. 支持多种默认头像样式
    3. 支持自定义尺寸
    4. 提供头像评级过滤
    """

    # 默认头像样式
    DEFAULT_STYLES = {
        'mp': '神秘人剪影',
        'identicon': '几何图案',
        'monsterid': '小怪物',
        'wavatar': '卡通脸',
        'retro': '8位像素',
        'robohash': '机器人',
        'blank': '空白透明',
    }

    def __init__(self, use_cdn: bool = True):
        """
        初始化Gravatar服务
        
        Args:
            use_cdn: 是否使用CDN加速(推荐国内使用)
        """
        self.base_url = CDN_BASE_URL if use_cdn else GRAVATAR_BASE_URL

    def get_avatar_url(
            self,
            email: str,
            size: int = 80,
            default: str = 'identicon',
            rating: str = 'g'
    ) -> str:
        """
        获取Gravatar头像URL
        
        Args:
            email: 用户邮箱地址
            size: 头像尺寸(1-2048像素)
            default: 默认头像样式
                - mp: 神秘人剪影
                - identicon: 几何图案
                - monsterid: 小怪物
                - wavatar: 卡通脸
                - retro: 8位像素
                - robohash: 机器人
                - blank: 空白透明
                - 或自定义URL
            rating: 内容评级
                - g: 适合所有场合
                - pg: 可能有争议
                - r: 成人内容
                - x: 强烈成人内容
            
        Returns:
            Gravatar头像URL
        """
        # 验证参数
        if not email:
            return self._get_default_avatar_url(default, size)

        # 限制尺寸范围并验证评级
        size = max(1, min(2048, size))
        rating = rating if rating in VALID_RATINGS else 'g'

        # 生成邮箱哈希(MD5)并构建URL
        email_hash = self._generate_email_hash(email)
        params = f"s={size}&d={default}&r={rating}"
        return f"{self.base_url}{email_hash}?{params}"

    def _generate_email_hash(self, email: str) -> str:
        """
        生成邮箱的MD5哈希
        
        Args:
            email: 邮箱地址
            
        Returns:
            MD5哈希字符串(小写)
        """
        return hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()

    def _get_default_avatar_url(self, default: str, size: int) -> str:
        """
        获取默认头像URL
        
        Args:
            default: 默认样式
            size: 尺寸
            
        Returns:
            默认头像URL
        """
        if default.startswith('http'):
            # 如果是自定义URL,直接返回
            return default

        # 使用占位图服务
        return f"https://ui-avatars.com/api/?name=User&size={size}&background=random"

    def get_avatar_urls(
            self,
            email: str,
            sizes: list = None
    ) -> dict:
        """
        获取多个尺寸的头像URL
        
        Args:
            email: 用户邮箱
            sizes: 尺寸列表,默认 [32, 64, 128, 256]
            
        Returns:
            字典 {size: url}
        """
        sizes = sizes or DEFAULT_SIZES
        return {size: self.get_avatar_url(email, size=size) for size in sizes}

    def validate_email(self, email: str) -> bool:
        """
        简单验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否为有效邮箱格式
        """
        return bool(EMAIL_PATTERN.match(email))

    def has_gravatar(self, email: str) -> bool:
        """
        检查邮箱是否有Gravatar头像
        注意: 这需要实际请求Gravatar API,这里仅做基本判断
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否有Gravatar(简化版始终返回True)
        """
        # 完整实现需要HTTP请求检查
        # 这里简化处理,假设所有邮箱都有Gravatar
        # 如果没有,会显示默认头像
        return True


# 全局实例(使用CDN加速)
gravatar_service = GravatarService(use_cdn=True)
