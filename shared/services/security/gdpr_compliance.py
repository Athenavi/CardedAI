"""
GDPR合规工具服务

提供数据导出、删除、同意管理等功能
符合欧盟通用数据保护条例(GDPR)要求
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.comment import Comment
from shared.models.media import Media
from shared.models.user import User


class GDPRComplianceService:
    """
    GDPR合规工具服务
    
    帮助用户行使数据权利
    """

    def __init__(self):
        """初始化GDPR合规服务"""
        # 用户同意记录 {user_id: consents}
        self.consent_records: Dict[int, Dict[str, Any]] = {}

        # 数据导出请求 {request_id: request_data}
        self.export_requests: Dict[str, Dict[str, Any]] = {}

        # 数据删除请求 {request_id: request_data}
        self.deletion_requests: Dict[str, Dict[str, Any]] = {}

    async def export_user_data(
            self,
            db: AsyncSession,
            user_id: int,
            username: str,
            email: str,
            include_articles: bool = True,
            include_comments: bool = True,
            include_media: bool = True,
            include_settings: bool = True
    ) -> Dict[str, Any]:
        """
        导出用户数据
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            email: 邮箱
            include_articles: 是否包含文章
            include_comments: 是否包含评论
            include_media: 是否包含媒体
            include_settings: 是否包含设置
        
        Returns:
            导出的数据
        """
        timestamp = datetime.now()
        request_id = f"export_{user_id}_{timestamp.strftime('%Y%m%d%H%M%S')}"

        # 构建导出数据
        exported_data = {
            'request_id': request_id,
            'exported_at': timestamp.isoformat(),
            'user_info': {
                'id': user_id,
                'username': username,
                'email': email,
            },
            'data_categories': [],
        }

        # 获取用户文章
        if include_articles:
            articles = await self._get_user_articles(db, user_id)
            exported_data['articles'] = articles
            exported_data['data_categories'].append({
                'category': 'articles',
                'count': len(articles),
                'description': '用户创建的文章',
            })

        # 获取用户评论
        if include_comments:
            comments = await self._get_user_comments(db, user_id)
            exported_data['comments'] = comments
            exported_data['data_categories'].append({
                'category': 'comments',
                'count': len(comments),
                'description': '用户的评论',
            })

        # 获取用户媒体
        if include_media:
            media = await self._get_user_media(db, user_id)
            exported_data['media'] = media
            exported_data['data_categories'].append({
                'category': 'media',
                'count': len(media),
                'description': '用户上传的媒体文件',
            })

        # 获取用户设置
        if include_settings:
            settings = await self._get_user_settings(db, user_id)
            exported_data['settings'] = settings
            exported_data['data_categories'].append({
                'category': 'settings',
                'count': len(settings.keys()) if isinstance(settings, dict) else 0,
                'description': '用户的个人设置',
            })

        # 添加元数据
        exported_data['metadata'] = {
            'total_data_points': sum(cat['count'] for cat in exported_data['data_categories']),
            'format': 'json',
            'compression': 'none',
            'gdpr_article': 'Article 15 - Right of access',
        }

        # 记录导出请求
        self.export_requests[request_id] = {
            'request_id': request_id,
            'user_id': user_id,
            'requested_at': timestamp.isoformat(),
            'status': 'completed',
            'data_size': len(json.dumps(exported_data, default=str)),
        }

        return exported_data

    async def anonymize_user_data(
            self,
            db: AsyncSession,
            user_id: int,
            hard_delete: bool = False
    ) -> Dict[str, Any]:
        """
        匿名化或删除用户数据
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            hard_delete: 是否硬删除（否则匿名化）
        
        Returns:
            操作结果
        """
        timestamp = datetime.now()
        request_id = f"deletion_{user_id}_{timestamp.strftime('%Y%m%d%H%M%S')}"

        result = {
            'request_id': request_id,
            'user_id': user_id,
            'action': 'hard_delete' if hard_delete else 'anonymize',
            'requested_at': timestamp.isoformat(),
            'completed_at': None,
            'status': 'processing',
            'affected_data': {},
        }

        try:
            if hard_delete:
                # 硬删除所有用户数据
                deleted_counts = {
                    'articles': await self._delete_user_articles(db, user_id),
                    'comments': await self._delete_user_comments(db, user_id),
                    'media': await self._delete_user_media(db, user_id),
                    'settings': await self._delete_user_settings(db, user_id),
                    'user_account': 1,
                }

                result['affected_data'] = deleted_counts
                result['status'] = 'completed'
            else:
                # 匿名化处理
                anonymized_counts = {
                    'username': await self._anonymize_username(db, user_id),
                    'email': await self._anonymize_email(db, user_id),
                    'profile': await self._anonymize_profile(db, user_id),
                    'comments': await self._anonymize_comments(db, user_id),
                }

                result['affected_data'] = anonymized_counts
                result['status'] = 'completed'

            result['completed_at'] = datetime.now().isoformat()
            await db.commit()

            # 记录删除请求
            self.deletion_requests[request_id] = result

            return result

        except Exception as e:
            await db.rollback()
            result['status'] = 'failed'
            result['error'] = str(e)
            return result

    def record_consent(
            self,
            user_id: int,
            consent_type: str,
            granted: bool,
            details: Optional[str] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        记录用户同意
        
        Args:
            user_id: 用户ID
            consent_type: 同意类型 (analytics, marketing, cookies, etc.)
            granted: 是否授予
            details: 详细信息
            ip_address: IP地址（可选）
            user_agent: 用户代理（可选）
        
        Returns:
            同意记录
        """
        timestamp = datetime.now()

        if user_id not in self.consent_records:
            self.consent_records[user_id] = {
                'user_id': user_id,
                'consents': {},
                'history': [],
            }

        consent_record = {
            'type': consent_type,
            'granted': granted,
            'details': details,
            'timestamp': timestamp.isoformat(),
            'ip_address': ip_address,
            'user_agent': user_agent,
        }

        # 更新当前同意状态
        self.consent_records[user_id]['consents'][consent_type] = consent_record

        # 添加到历史记录
        self.consent_records[user_id]['history'].append(consent_record)

        return consent_record

    def get_user_consents(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户同意记录
        
        Args:
            user_id: 用户ID
        
        Returns:
            同意记录
        """
        if user_id not in self.consent_records:
            return {
                'user_id': user_id,
                'consents': {},
                'history': [],
            }

        return self.consent_records[user_id]

    def withdraw_consent(
            self,
            user_id: int,
            consent_type: str
    ) -> Dict[str, Any]:
        """
        撤回同意
        
        Args:
            user_id: 用户ID
            consent_type: 同意类型
        
        Returns:
            更新后的同意记录
        """
        return self.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=False,
            details='User withdrew consent'
        )

    def get_privacy_report(self, user_id: int) -> Dict[str, Any]:
        """
        生成隐私报告
        
        Args:
            user_id: 用户ID
        
        Returns:
            隐私报告
        """
        # 获取用户同意记录
        consents = self.get_user_consents(user_id)

        # 统计数据
        data_summary = {
            'articles_count': self._count_user_articles(user_id),
            'comments_count': self._count_user_comments(user_id),
            'media_count': self._count_user_media(user_id),
            'login_count': self._count_user_logins(user_id),
        }

        report = {
            'user_id': user_id,
            'generated_at': datetime.now().isoformat(),
            'data_summary': data_summary,
            'consents': consents,
            'data_retention': {
                'articles': '保留至用户删除账户',
                'comments': '保留至用户删除账户',
                'media': '保留至用户删除账户',
                'logs': '保留90天',
                'analytics': '保留365天',
            },
            'third_party_sharing': [
                {
                    'service': 'Analytics Provider',
                    'purpose': '网站分析',
                    'legal_basis': '用户同意',
                },
                {
                    'service': 'CDN Provider',
                    'purpose': '内容分发',
                    'legal_basis': '合法利益',
                },
            ],
            'user_rights': [
                '访问权 (Article 15)',
                '更正权 (Article 16)',
                '删除权 (Article 17)',
                '限制处理权 (Article 18)',
                '数据可携带权 (Article 20)',
                '反对权 (Article 21)',
            ],
        }

        return report

    async def _get_user_articles(self, db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取用户文章"""
        stmt = select(Article).where(Article.user == user_id)
        result = await db.execute(stmt)
        articles = result.scalars().all()

        return [
            {
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'excerpt': article.excerpt,
                'status': article.status,
                'created_at': article.created_at.isoformat() if article.created_at else None,
                'updated_at': article.updated_at.isoformat() if article.updated_at else None,
            }
            for article in articles
        ]

    async def _get_user_comments(self, db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取用户评论"""
        stmt = select(Comment).where(Comment.user_id == user_id)
        result = await db.execute(stmt)
        comments = result.scalars().all()

        return [
            {
                'id': comment.id,
                'content': comment.content,
                'article_id': comment.article_id,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
            }
            for comment in comments
        ]

    async def _get_user_media(self, db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取用户媒体"""
        stmt = select(Media).where(Media.user == user_id)
        result = await db.execute(stmt)
        media_list = result.scalars().all()

        return [
            {
                'id': media.id,
                'filename': media.filename,
                'file_url': media.file_url,
                'file_type': media.file_type,
                'file_size': media.file_size,
                'created_at': media.created_at.isoformat() if media.created_at else None,
            }
            for media in media_list
        ]

    async def _get_user_settings(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """获取用户设置"""

        stmt = select(AdminSettings).where(AdminSettings.user == user_id)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings and settings.settings_data:
            return settings.settings_data
        return {}

    async def _delete_user_articles(self, db: AsyncSession, user_id: int) -> int:
        """删除用户文章"""
        stmt = delete(Article).where(Article.user == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_user_comments(self, db: AsyncSession, user_id: int) -> int:
        """删除用户评论"""
        stmt = delete(Comment).where(Comment.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_user_media(self, db: AsyncSession, user_id: int) -> int:
        """删除用户媒体"""
        stmt = delete(Media).where(Media.user == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_user_settings(self, db: AsyncSession, user_id: int) -> int:
        """删除用户设置"""

        stmt = delete(AdminSettings).where(AdminSettings.user == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _anonymize_username(self, db: AsyncSession, user_id: int) -> bool:
        """匿名化用户名"""
        anonymized_name = f"user_{uuid.uuid4().hex[:8]}"
        stmt = update(User).where(User.id == user_id).values(username=anonymized_name)
        await db.execute(stmt)
        return True

    async def _anonymize_email(self, db: AsyncSession, user_id: int) -> bool:
        """匿名化邮箱"""
        anonymized_email = f"deleted_{uuid.uuid4().hex[:8]}@anonymous.invalid"
        stmt = update(User).where(User.id == user_id).values(email=anonymized_email)
        await db.execute(stmt)
        return True

    async def _anonymize_profile(self, db: AsyncSession, user_id: int) -> bool:
        """匿名化个人资料"""
        stmt = update(User).where(User.id == user_id).values(
            profile_picture=None,
            bio=None,
            locale='zh_CN',
            profile_private=False
        )
        await db.execute(stmt)
        return True

    async def _anonymize_comments(self, db: AsyncSession, user_id: int) -> int:
        """匿名化评论（保留内容但移除作者信息）"""
        stmt = update(Comment).where(Comment.user_id == user_id).values(
            user_id=None,
            author_name='Anonymous',
            author_email=None,
            author_url=None
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _count_user_articles(self, user_id: int) -> int:
        """统计用户文章数"""
        from src.utils.database.unified_manager import db_manager

        async with db_manager.get_session() as db:
            stmt = select(func.count(Article.id)).where(Article.user == user_id)
            result = await db.execute(stmt)
            return result.scalar() or 0

    async def _count_user_comments(self, user_id: int) -> int:
        """统计用户评论数"""
        from src.utils.database.unified_manager import db_manager

        async with db_manager.get_session() as db:
            stmt = select(func.count(Comment.id)).where(Comment.user_id == user_id)
            result = await db.execute(stmt)
            return result.scalar() or 0

    async def _count_user_media(self, user_id: int) -> int:
        """统计用户媒体数"""
        from src.utils.database.unified_manager import db_manager

        async with db_manager.get_session() as db:
            stmt = select(func.count(Media.id)).where(Media.user == user_id)
            result = await db.execute(stmt)
            return result.scalar() or 0

    async def _count_user_logins(self, user_id: int) -> int:
        """统计用户登录次数"""
        try:
            from shared.models.security import LoginAttempt
            from sqlalchemy import select, func
            from src.utils.database.unified_manager import db_manager

            async with db_manager.get_session() as db:
                # 统计该用户的成功登录次数
                stmt = select(func.count(LoginAttempt.id)).where(
                    (LoginAttempt.user_id == user_id) &
                    (LoginAttempt.is_success == True)
                )
                result = await db.execute(stmt)
                count = result.scalar() or 0

                return count
        except Exception as e:
            logger.warning(f"Failed to count user logins: {e}")
            return 0


# 全局实例
gdpr_service = GDPRComplianceService()

# 导出
__all__ = ['GDPRComplianceService', 'gdpr_service']
