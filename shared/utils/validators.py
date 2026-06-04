"""
输入验证和输出转义工具

提供统一的安全验证功能，防止 XSS、SQL 注入等安全威胁
"""

import html
import re
from typing import Optional

from pydantic import BaseModel, field_validator, Field, ConfigDict


class SecurityValidator:
    """
    安全验证器
    
    提供常见的安全验证和清理功能
    """

    # XSS 危险模式
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # script 标签
        r'javascript:',  # javascript 协议
        r'on\w+\s*=',  # 事件处理器 (onclick= 等)
        r'<iframe[^>]*>',  # iframe
        r'<object[^>]*>',  # object
        r'<embed[^>]*>',  # embed
        r'<form[^>]*>',  # form
        r'<input[^>]*>',  # input
        r'<button[^>]*>',  # button
        r'expression\s*\(',  # CSS expression
        r'url\s*\(\s*javascript:',  # CSS url with javascript
    ]

    # SQL 注入危险模式
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",  # SQL 关键字
        r"(--|#|/\*)",  # SQL 注释
        r"(\bOR\b\s+\d+\s*=\s*\d+)",  # OR 1=1
        r"(\bAND\b\s+\d+\s*=\s*\d+)",  # AND 1=1
        r"('\s*(OR|AND)\s*')",  # ' OR '
        r"(;\s*(DROP|DELETE|UPDATE))",  # ; DROP
    ]

    @staticmethod
    def sanitize_html(text: str, allowed_tags: Optional[list] = None) -> str:
        """
        清理 HTML，防止 XSS
        
        Args:
            text: 输入文本
            allowed_tags: 允许的标签列表（None 表示移除所有标签）
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 如果允许特定标签，使用白名单过滤
        if allowed_tags:
            return SecurityValidator._whitelist_html(text, allowed_tags)

        # 否则移除所有 HTML 标签
        # 先转义特殊字符
        text = html.escape(text, quote=True)

        # 移除残留的标签
        text = re.sub(r'<[^>]+>', '', text)

        return text

    @staticmethod
    def _whitelist_html(text: str, allowed_tags: list) -> str:
        """
        白名单方式过滤 HTML
        
        Args:
            text: 输入文本
            allowed_tags: 允许的标签列表
            
        Returns:
            过滤后的文本
        """
        # 构建允许的正则模式
        allowed_pattern = '|'.join(re.escape(tag) for tag in allowed_tags)

        # 移除不允许的标签
        pattern = f'<(?!/?({allowed_pattern})\\b)[^>]+>'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        return text

    @staticmethod
    def detect_xss(text: str) -> bool:
        """
        检测 XSS 攻击
        
        Args:
            text: 待检测文本
            
        Returns:
            是否检测到 XSS
        """
        if not text:
            return False

        text_lower = text.lower()

        for pattern in SecurityValidator.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True

        return False

    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """
        检测 SQL 注入
        
        Args:
            text: 待检测文本
            
        Returns:
            是否检测到 SQL 注入
        """
        if not text:
            return False

        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否有效
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_slug(slug: str) -> bool:
        """
        验证 slug 格式（只允许小写字母、数字和连字符）
        
        Args:
            slug: slug 字符串
            
        Returns:
            是否有效
        """
        pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
        return bool(re.match(pattern, slug))

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """
        验证用户名
        
        Args:
            username: 用户名
            
        Returns:
            (是否有效, 错误消息)
        """
        if not username or len(username) < 3:
            return False, "用户名至少需要3个字符"

        if len(username) > 50:
            return False, "用户名不能超过50个字符"

        # 只允许字母、数字、下划线和连字符
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "用户名只能包含字母、数字、下划线和连字符"

        return True, ""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，防止路径遍历攻击
        
        Args:
            filename: 文件名
            
        Returns:
            安全的文件名
        """
        # 移除路径分隔符
        filename = filename.replace('/', '').replace('\\', '')

        # 移除 .. 
        filename = filename.replace('..', '')

        # 只保留安全的字符
        filename = re.sub(r'[^\w\-\.]', '_', filename)

        # 限制长度
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255 - len(ext) - 1] + ('.' + ext if ext else '')

        return filename

    @staticmethod
    def validate_pagination(page: int, per_page: int, max_per_page: int = 100) -> tuple[int, int]:
        """
        验证分页参数
        
        Args:
            page: 页码
            per_page: 每页数量
            max_per_page: 最大每页数量
            
        Returns:
            (验证后的 page, 验证后的 per_page)
        """
        # 确保 page >= 1
        page = max(1, page)

        # 确保 per_page 在合理范围内
        per_page = max(1, min(per_page, max_per_page))

        return page, per_page

    @staticmethod
    def truncate_text(text: str, max_length: int = 5000, suffix: str = "...") -> str:
        """
        截断文本到指定长度
        
        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 截断后缀
            
        Returns:
            截断后的文本
        """
        if not text or len(text) <= max_length:
            return text

        return text[:max_length - len(suffix)] + suffix


# Pydantic 基础模型，带自动验证
class SecureBaseModel(BaseModel):
    """
    安全的基础 Pydantic 模型
    
    自动进行常见的安全验证
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator('*', mode='before')
    @classmethod
    def strip_strings(cls, v):
        """自动去除字符串前后空格"""
        if isinstance(v, str):
            return v.strip()
        return v


# 常用验证器示例
class ArticleCreateRequest(SecureBaseModel):
    """文章创建请求验证"""
    title: str = Field(..., min_length=1, max_length=200, description="文章标题")
    slug: Optional[str] = Field(None, max_length=200, description="文章slug")
    excerpt: Optional[str] = Field(None, max_length=500, description="文章摘要")
    content: str = Field(..., min_length=1, max_length=100000, description="文章内容")
    category_id: Optional[int] = Field(None, gt=0, description="分类ID")
    tags: Optional[list[str]] = Field(None, description="标签列表")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """验证标题"""
        if SecurityValidator.detect_xss(v):
            raise ValueError("标题包含不安全的内容")
        return v.strip()

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        """验证 slug"""
        if v and not SecurityValidator.validate_slug(v):
            raise ValueError("Slug 格式不正确，只允许小写字母、数字和连字符")
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """验证内容"""
        if SecurityValidator.detect_xss(v):
            raise ValueError("内容包含不安全的内容")
        return v


class UserRegisterRequest(SecureBaseModel):
    """用户注册请求验证"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, max_length=128, description="密码")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """验证用户名"""
        is_valid, message = SecurityValidator.validate_username(v)
        if not is_valid:
            raise ValueError(message)
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """验证邮箱"""
        if not SecurityValidator.validate_email(v):
            raise ValueError("邮箱格式不正确")
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError("密码至少需要8个字符")
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r'[a-z]', v):
            raise ValueError("密码必须包含小写字母")
        if not re.search(r'\d', v):
            raise ValueError("密码必须包含数字")
        return v


# 全局验证器实例
security_validator = SecurityValidator()
