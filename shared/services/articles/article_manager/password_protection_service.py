"""
文章密码保护服务
"""
import hashlib
import hmac
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article_content import ArticleContent


class PasswordProtectionService:
    """文章密码保护服务"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            是否匹配
        """
        hashed_input = PasswordProtectionService.hash_password(plain_password)
        return hmac.compare_digest(hashed_input, hashed_password)
    
    @staticmethod
    async def set_article_password(
        db: AsyncSession,
        article_id: int,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        设置文章密码
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            password: 密码（None表示清除密码）
            
        Returns:
            操作结果
        """
        # 获取文章内容
        content_query = select(ArticleContent).where(ArticleContent.article == article_id)
        content_result = await db.execute(content_query)
        content = content_result.scalar_one_or_none()
        
        if not content:
            # 如果不存在，创建一个新的
            content = ArticleContent(article=article_id)
            db.add(content)
        
        if password:
            # 设置密码
            content.passwd = PasswordProtectionService.hash_password(password)
        else:
            # 清除密码
            content.passwd = None
        
        await db.commit()
        await db.refresh(content)
        
        return {
            "success": True,
            "has_password": content.passwd is not None
        }
    
    @staticmethod
    async def verify_article_password(
        db: AsyncSession,
        article_id: int,
        password: str
    ) -> Dict[str, Any]:
        """
        验证文章密码
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            password: 用户输入的密码
            
        Returns:
            验证结果
        """
        # 获取文章内容
        content_query = select(ArticleContent).where(ArticleContent.article == article_id)
        content_result = await db.execute(content_query)
        content = content_result.scalar_one_or_none()
        
        if not content or not content.passwd:
            return {
                "success": False,
                "error": "Article does not require password"
            }
        
        # 验证密码
        if PasswordProtectionService.verify_password(password, content.passwd):
            return {
                "success": True,
                "message": "Password verified successfully"
            }
        else:
            return {
                "success": False,
                "error": "Incorrect password"
            }
    
    @staticmethod
    async def check_article_access(
        db: AsyncSession,
        article_id: int,
        session_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检查文章访问权限
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            session_token: 会话token（已验证的标记）
            
        Returns:
            访问权限信息
        """
        # 获取文章内容
        content_query = select(ArticleContent).where(ArticleContent.article == article_id)
        content_result = await db.execute(content_query)
        content = content_result.scalar_one_or_none()
        
        if not content or not content.passwd:
            # 不需要密码
            return {
                "requires_password": False,
                "can_access": True
            }
        
        # 需要密码，检查session token
        if session_token:
            # 这里可以扩展为检查session中存储的已验证文章ID列表
            # 简化实现：假设token是文章ID的签名
            expected_token = PasswordProtectionService.hash_password(f"access_{article_id}")
            if session_token == expected_token:
                return {
                    "requires_password": True,
                    "can_access": True
                }
        
        return {
            "requires_password": True,
            "can_access": False
        }
    
    @staticmethod
    def generate_access_token(article_id: int) -> str:
        """
        生成访问token
        
        Args:
            article_id: 文章ID
            
        Returns:
            访问token
        """
        return PasswordProtectionService.hash_password(f"access_{article_id}")


# 全局实例
password_protection_service = PasswordProtectionService()
