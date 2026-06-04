"""
文章审批工作流插件
提供多级审批、权限控制和协作功能
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class ApprovalStatus(str, Enum):
    """审批状态"""
    DRAFT = "draft"  # 草稿
    PENDING_REVIEW = "pending_review"  # 待审核
    IN_REVIEW = "in_review"  # 审核中
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    NEEDS_REVISION = "needs_revision"  # 需要修改


class ArticleWorkflowPlugin(BasePlugin):
    """
    文章审批工作流插件
    
    功能:
    1. 多级审批流程
    2. 角色权限管理
    3. 版本对比
    4. 批注和评论
    5. 审批通知
    6. 审批历史记录
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="文章审批工作流",
            slug="article-workflow",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enable_workflow': True,
            'approval_levels': 2,
            'auto_approve_editors': False,
            'notify_on_submission': True,
            'notify_on_approval': True,
        }

        # 审批记录(实际应存储在数据库)
        self.approval_records = {}

    def register_hooks(self):
        """注册钩子"""
        # 拦截文章发布,检查审批状态
        plugin_hooks.add_filter(
            "before_publish_article",
            self.check_before_publish,
            priority=10
        )

        # 文章保存时触发工作流
        plugin_hooks.add_action(
            "article_saved",
            self.on_article_saved,
            priority=10
        )

        # 文章更新时创建新版本
        plugin_hooks.add_action(
            "article_updated",
            self.on_article_updated,
            priority=10
        )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[ArticleWorkflow] Plugin activated")

    async def check_before_publish(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发布前检查审批状态
        
        Args:
            article_data: 文章数据
            
        Returns:
            检查结果 {can_publish: bool, reason: str}
        """
        if not self.settings.get('enable_workflow', True):
            return {'can_publish': True}

        article_id = article_data.get('id')
        approval_status = self._get_approval_status(article_id)

        if approval_status != ApprovalStatus.APPROVED:
            return {
                'can_publish': False,
                'reason': f'Article must be approved before publishing. Current status: {approval_status.value}',
                'current_status': approval_status.value,
            }

        return {'can_publish': True}

    async def on_article_saved(self, article_data: Dict[str, Any]):
        """文章保存时触发工作流"""
        if not self.settings.get('enable_workflow', True):
            return

        article_id = article_data.get('id')
        user_id = article_data.get('user_id')
        user_role = article_data.get('user_role', 'author')

        # 如果是新文章,设置为待审核
        if not self._has_approval_record(article_id):
            self._create_approval_record(article_id, user_id)

            # 编辑角色可能自动通过
            if self.settings.get('auto_approve_editors') and user_role == 'editor':
                await self._auto_approve(article_id, user_id)
            else:
                # 提交审批
                await self.submit_for_approval(article_id, user_id)

    async def on_article_updated(self, article_data: Dict[str, Any]):
        """文章更新时创建新版本"""
        article_id = article_data.get('id')

        # 如果文章已发布,更新后需要重新审批
        if article_data.get('status') == 'published':
            self._update_approval_status(article_id, ApprovalStatus.NEEDS_REVISION)

            # 通知相关审批人
            if self.settings.get('notify_on_submission'):
                await self._notify_approvers(article_id, "文章已更新,需要重新审批")

    async def submit_for_approval(self, article_id: int, user_id: int) -> Dict[str, Any]:
        """
        提交文章审批
        
        Args:
            article_id: 文章ID
            user_id: 提交用户ID
            
        Returns:
            提交结果
        """
        record = self._get_approval_record(article_id)
        if not record:
            return {
                'success': False,
                'error': 'Approval record not found',
            }

        # 更新状态
        self._update_approval_status(article_id, ApprovalStatus.PENDING_REVIEW)

        # 分配审批人
        approvers = self._assign_approvers(article_id)

        # 记录提交历史
        self._add_approval_history(article_id, {
            'action': 'submitted',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'approvers': approvers,
        })

        # 通知审批人
        if self.settings.get('notify_on_submission'):
            await self._notify_approvers(article_id, "有新文章需要审批")

        return {
            'success': True,
            'data': {
                'message': 'Submitted for approval',
                'approvers': approvers,
            }
        }

    async def approve_article(
            self,
            article_id: int,
            approver_id: int,
            level: int,
            comment: str = None,
    ) -> Dict[str, Any]:
        """
        审批文章
        
        Args:
            article_id: 文章ID
            approver_id: 审批人ID
            level: 审批级别
            comment: 审批意见
            
        Returns:
            审批结果
        """
        record = self._get_approval_record(article_id)
        if not record:
            return {
                'success': False,
                'error': 'Approval record not found',
            }

        # 检查是否有权限审批
        if not self._can_approve(approver_id, level):
            return {
                'success': False,
                'error': 'No permission to approve at this level',
            }

        # 记录审批
        self._add_approval_decision(article_id, {
            'approver_id': approver_id,
            'level': level,
            'decision': 'approved',
            'comment': comment,
            'timestamp': datetime.now().isoformat(),
        })

        # 检查是否所有级别都已通过
        total_levels = self.settings.get('approval_levels', 2)
        approved_levels = sum(
            1 for d in record.get('decisions', [])
            if d['decision'] == 'approved'
        )

        if approved_levels >= total_levels:
            # 全部通过
            self._update_approval_status(article_id, ApprovalStatus.APPROVED)

            # 通知作者
            if self.settings.get('notify_on_approval'):
                await self._notify_author(article_id, "您的文章已通过审批")

            return {
                'success': True,
                'data': {
                    'message': 'Article fully approved and ready to publish',
                    'status': ApprovalStatus.APPROVED.value,
                }
            }
        else:
            # 进入下一级审批
            next_level = approved_levels + 1
            self._update_approval_status(article_id, ApprovalStatus.IN_REVIEW)

            # 通知下一级审批人
            await self._notify_next_approver(article_id, next_level)

            return {
                'success': True,
                'data': {
                    'message': f'Approved at level {level}. Waiting for level {next_level} approval.',
                    'current_level': level,
                    'next_level': next_level,
                }
            }

    async def reject_article(
            self,
            article_id: int,
            approver_id: int,
            level: int,
            reason: str,
    ) -> Dict[str, Any]:
        """
        拒绝文章
        
        Args:
            article_id: 文章ID
            approver_id: 审批人ID
            level: 审批级别
            reason: 拒绝原因
            
        Returns:
            拒绝结果
        """
        record = self._get_approval_record(article_id)
        if not record:
            return {
                'success': False,
                'error': 'Approval record not found',
            }

        # 记录拒绝决定
        self._add_approval_decision(article_id, {
            'approver_id': approver_id,
            'level': level,
            'decision': 'rejected',
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
        })

        # 更新状态
        self._update_approval_status(article_id, ApprovalStatus.REJECTED)

        # 通知作者
        await self._notify_author(
            article_id,
            f"您的文章被拒绝。原因: {reason}"
        )

        return {
            'success': True,
            'data': {
                'message': 'Article rejected',
                'status': ApprovalStatus.REJECTED.value,
                'reason': reason,
            }
        }

    def get_approval_status(self, article_id: int) -> Dict[str, Any]:
        """获取文章审批状态"""
        record = self._get_approval_record(article_id)

        if not record:
            return {
                'has_record': False,
            }

        return {
            'has_record': True,
            'status': record.get('status'),
            'current_level': record.get('current_level', 0),
            'total_levels': self.settings.get('approval_levels', 2),
            'decisions': record.get('decisions', []),
            'history': record.get('history', []),
        }

    def get_pending_approvals(self, approver_id: int) -> List[Dict[str, Any]]:
        """获取待审批文章列表"""
        pending = []

        for article_id, record in self.approval_records.items():
            if record.get('status') in [ApprovalStatus.PENDING_REVIEW, ApprovalStatus.IN_REVIEW]:
                # 检查是否是当前审批人的任务
                assigned_approvers = record.get('assigned_approvers', {})
                current_level = record.get('current_level', 1)

                if assigned_approvers.get(str(current_level)) == approver_id:
                    pending.append({
                        'article_id': article_id,
                        'title': record.get('article_title', ''),
                        'author_id': record.get('author_id'),
                        'submitted_at': record.get('submitted_at'),
                        'current_level': current_level,
                    })

        return pending

    def compare_versions(self, article_id: int, version1: int, version2: int) -> Dict[str, Any]:
        """
        比较文章版本
        
        Args:
            article_id: 文章ID
            version1: 版本1
            version2: 版本2
            
        Returns:
            差异对比
        """
        try:
            import difflib
            from shared.models import ArticleRevision
            from src.extensions import get_sync_db

            # 从数据库获取版朓内容
            content_v1 = None
            content_v2 = None

            for db_session in get_sync_db_session():
                # 获取版本1
                revision_v1 = db_session.query(ArticleRevision).filter(
                    ArticleRevision.article_id == article_id,
                    ArticleRevision.revision_number == version1
                ).first()

                if revision_v1:
                    content_v1 = revision_v1.content or ""

                # 获取版本2
                revision_v2 = db_session.query(ArticleRevision).filter(
                    ArticleRevision.article_id == article_id,
                    ArticleRevision.revision_number == version2
                ).first()

                if revision_v2:
                    content_v2 = revision_v2.content or ""

                break

            # 如果找不到版本,返回错误
            if content_v1 is None or content_v2 is None:
                return {
                    'success': False,
                    'error': f'Version not found. v1={content_v1 is not None}, v2={content_v2 is not None}',
                }

            # 使用difflib进行文本对比
            diff = difflib.unified_diff(
                content_v1.splitlines(keepends=True),
                content_v2.splitlines(keepends=True),
                fromfile=f'version_{version1}',
                tofile=f'version_{version2}',
                lineterm=''
            )

            differences = list(diff)

            return {
                'success': True,
                'data': {
                    'article_id': article_id,
                    'version1': version1,
                    'version2': version2,
                    'differences': differences,
                    'diff_count': len(differences),
                    'v1_length': len(content_v1),
                    'v2_length': len(content_v2),
                }
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
            }

    def add_comment(
            self,
            article_id: int,
            user_id: int,
            comment: str,
            line_number: int = None,
    ) -> Dict[str, Any]:
        """
        添加批注
        
        Args:
            article_id: 文章ID
            user_id: 用户ID
            comment: 批注内容
            line_number: 行号(可选)
            
        Returns:
            添加结果
        """
        record = self._get_approval_record(article_id)
        if not record:
            return {
                'success': False,
                'error': 'Approval record not found',
            }

        comment_data = {
            'user_id': user_id,
            'comment': comment,
            'line_number': line_number,
            'timestamp': datetime.now().isoformat(),
        }

        if 'comments' not in record:
            record['comments'] = []

        record['comments'].append(comment_data)

        return {
            'success': True,
            'data': comment_data,
        }

    # ========== 私有方法 ==========

    def _get_approval_record(self, article_id: int) -> Optional[Dict[str, Any]]:
        """获取审批记录"""
        return self.approval_records.get(article_id)

    def _has_approval_record(self, article_id: int) -> bool:
        """检查是否有审批记录"""
        return article_id in self.approval_records

    def _create_approval_record(self, article_id: int, author_id: int):
        """创建审批记录"""
        self.approval_records[article_id] = {
            'article_id': article_id,
            'author_id': author_id,
            'status': ApprovalStatus.DRAFT.value,
            'current_level': 0,
            'decisions': [],
            'history': [],
            'comments': [],
            'created_at': datetime.now().isoformat(),
        }

    def _update_approval_status(self, article_id: int, status: ApprovalStatus):
        """更新审批状态"""
        record = self.approval_records.get(article_id)
        if record:
            record['status'] = status.value
            record['updated_at'] = datetime.now().isoformat()

    def _get_approval_status(self, article_id: int) -> ApprovalStatus:
        """获取审批状态"""
        record = self.approval_records.get(article_id)
        if not record:
            return ApprovalStatus.DRAFT

        return ApprovalStatus(record.get('status', ApprovalStatus.DRAFT.value))

    def _assign_approvers(self, article_id: int) -> List[int]:
        """
        根据角色和配置分配审批人
        
        Args:
            article_id: 文章ID
            
        Returns:
            审批人用户ID列表
        """
        try:
            from apps.user.models import User
            from django.db.models import Q
            
            # 方案1: 从插件设置中读取审批人配置
            approvers_config = self.settings.get('approvers_by_level', {})
            if approvers_config:
                level_1_approvers = approvers_config.get('1', [])
                if level_1_approvers:
                    return level_1_approvers

            # 方案2: 基于角色查询(集成Django用户系统)
            # 获取所有活跃的编辑和管理员
            editors_and_admins = User.objects.filter(
                Q(is_staff=True) | Q(is_superuser=True),
                is_active=True
            ).order_by('id')[:5]  # 最多取5个

            if editors_and_admins.exists():
                return [user.id for user in editors_and_admins]

            # 如果没有找到合适的审批人,返回空列表
            print(f"[ArticleWorkflow] No suitable approvers found for article {article_id}")
            return []

        except Exception as e:
            print(f"[ArticleWorkflow] Failed to assign approvers: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _can_approve(self, user_id: int, level: int) -> bool:
        """
        根据角色和级别检查审批权限
        
        Args:
            user_id: 用户ID
            level: 审批级别
            
        Returns:
            是否有权限审批
        """
        try:
            from apps.user.models import User
            from shared.services.permission_system import permission_manager
            from src.extensions import get_sync_db

            # 获取用户信息
            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                print(f"[ArticleWorkflow] User {user_id} not found or inactive")
                return False

            # 超级管理员拥有所有权限
            if user.is_superuser:
                return True

            # 从配置中读取各级别的允许角色
            role_permissions = self.settings.get('approval_role_permissions', {
                '1': ['editor', 'admin'],  # 第一级:编辑和管理员
                '2': ['admin'],  # 第二级:仅管理员
            })

            allowed_roles = role_permissions.get(str(level), [])

            if not allowed_roles:
                # 如果没有配置,默认允许staff用户
                return user.is_staff

            # 检查用户是否具有所需角色/权限
            # 方案1: 检查用户是否是staff或superuser
            if 'admin' in allowed_roles and (user.is_superuser or user.is_staff):
                return True

            if 'editor' in allowed_roles and user.is_staff:
                return True

            # 方案2: 使用权限管理器检查特定权限(如果配置了)
            # 例如:检查用户是否有'article.approve'权限
            try:
                for db_session in get_sync_db_session():
                    has_perm = permission_manager.check_permission(
                        db=db_session,
                        user_id=user_id,
                        resource='article',
                        action='approve'
                    )
                    if has_perm:
                        return True
                    break
            except Exception as e:
                print(f"[ArticleWorkflow] Permission check error: {e}")

            return False

        except Exception as e:
            print(f"[ArticleWorkflow] Failed to check approval permission: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _add_approval_decision(self, article_id: int, decision: Dict[str, Any]):
        """添加审批决定"""
        record = self.approval_records.get(article_id)
        if record:
            if 'decisions' not in record:
                record['decisions'] = []
            record['decisions'].append(decision)
            record['current_level'] = decision.get('level', 0)

    def _add_approval_history(self, article_id: int, history_entry: Dict[str, Any]):
        """添加审批历史"""
        record = self.approval_records.get(article_id)
        if record:
            if 'history' not in record:
                record['history'] = []
            record['history'].append(history_entry)

    async def _auto_approve(self, article_id: int, user_id: int):
        """自动审批"""
        await self.approve_article(
            article_id=article_id,
            approver_id=user_id,
            level=1,
            comment='Auto-approved for editor role',
        )

    async def _notify_approvers(self, article_id: int, message: str):
        """通知审批人(邮件+站内信)"""
        try:
            from src.notification import create_notification
            
            # 获取审批记录
            record = self._get_approval_record(article_id)
            if not record:
                return

            # 获取当前级别的审批人
            current_level = record.get('current_level', 1)
            approvers = record.get('assigned_approvers', {})
            approver_ids = approvers.get(str(current_level), [])

            if not approver_ids:
                approver_ids = self._assign_approvers(article_id)

            # 为每个审批人创建站内通知
            for approver_id in approver_ids:
                try:
                    notification = await create_notification(
                        recipient_id=approver_id,
                        title=f'文章审批通知 - {record.get("article_title", "")}',
                        content=message,
                        notification_type='warning',
                        related_id=article_id,
                        data={
                            'type': 'article_approval_request',
                            'article_id': article_id,
                            'level': current_level,
                            'article_title': record.get('article_title', ''),
                        }
                    )
                    print(f"[ArticleWorkflow] Created notification for approver {approver_id}")
                except Exception as e:
                    print(f"[ArticleWorkflow] Failed to create notification for approver {approver_id}: {e}")

            # 集成邮件系统
            # 如果启用了邮件通知,发送邮件
            if self.settings.get('email_notifications', False):
                try:
                    # 尝试获取邮件插件
                    from plugins.email_marketing.plugin import EmailMarketingPlugin
                    email_plugin = EmailMarketingPlugin()

                    for approver_id in approver_ids:
                        # 获取用户邮箱
                        from apps.user.models import User
                        try:
                            user = User.objects.get(id=approver_id, is_active=True)
                            if user.email:
                                await email_plugin.send_email(
                                    to_email=user.email,
                                    subject=f'文章审批通知 - {record.get("article_title", "")}',
                                    html_content=f'<p>{message}</p><p>请登录系统查看。</p>'
                                )
                                print(f"[ArticleWorkflow] Sent email to approver {approver_id}")
                        except User.DoesNotExist:
                            pass
                except ImportError:
                    print("[ArticleWorkflow] Email marketing plugin not available")
                except Exception as e:
                    print(f"[ArticleWorkflow] Email notification failed: {e}")

            print(f"[ArticleWorkflow] Notified approvers {approver_ids}: {message}")
        except Exception as e:
            print(f"[ArticleWorkflow] Failed to notify approvers: {e}")
            import traceback
            traceback.print_exc()

    async def _notify_next_approver(self, article_id: int, next_level: int):
        """通知下一级审批人"""
        try:
            from src.notification import create_notification
            
            record = self._get_approval_record(article_id)
            if not record:
                return

            approvers = record.get('assigned_approvers', {})
            next_approver_ids = approvers.get(str(next_level), [])

            # 如果没有指定审批人,自动分配
            if not next_approver_ids:
                next_approver_ids = self._assign_approvers(article_id)

            message = f'文章 "{record.get("article_title", "")}" 已通过第{next_level - 1}级审批,等待您的第{next_level}级审批'

            # 为每个下一级审批人创建通知
            for approver_id in next_approver_ids:
                try:
                    notification = await create_notification(
                        recipient_id=approver_id,
                        title=f'文章待审批 - 第{next_level}级 - {record.get("article_title", "")}',
                        content=message,
                        notification_type='info',
                        related_id=article_id,
                        data={
                            'type': 'article_approval_next_level',
                            'article_id': article_id,
                            'level': next_level,
                            'article_title': record.get('article_title', ''),
                        }
                    )
                    print(f"[ArticleWorkflow] Notified level {next_level} approver (ID: {approver_id})")
                except Exception as e:
                    print(f"[ArticleWorkflow] Failed to notify approver {approver_id}: {e}")
                    
        except Exception as e:
            print(f"[ArticleWorkflow] Failed to notify next approver: {e}")
            import traceback
            traceback.print_exc()

    async def _notify_author(self, article_id: int, message: str):
        """通知作者审批结果"""
        try:
            from src.notification import create_notification
            
            record = self._get_approval_record(article_id)
            if not record:
                return

            author_id = record.get('author_id')
            if not author_id:
                return

            # 创建站内通知
            try:
                notification = await create_notification(
                    recipient_id=author_id,
                    title=f'文章审批结果 - {record.get("article_title", "")}',
                    content=message,
                    notification_type='info',
                    related_id=article_id,
                    data={
                        'type': 'article_approval_result',
                        'article_id': article_id,
                        'article_title': record.get('article_title', ''),
                        'status': record.get('status'),
                    }
                )
                print(f"[ArticleWorkflow] Created notification for author {author_id}")
            except Exception as e:
                print(f"[ArticleWorkflow] Failed to create notification for author: {e}")

            # 集成邮件系统
            # 如果启用了邮件通知,发送邮件
            if self.settings.get('email_notifications', False):
                try:
                    from plugins.email_marketing.plugin import EmailMarketingPlugin
                    email_plugin = EmailMarketingPlugin()

                    # 获取用户邮箱
                    from apps.user.models import User
                    try:
                        user = User.objects.get(id=author_id, is_active=True)
                        if user.email:
                            await email_plugin.send_email(
                                to_email=user.email,
                                subject=f'文章审批结果 - {record.get("article_title", "")}',
                                html_content=f'<p>{message}</p>'
                            )
                            print(f"[ArticleWorkflow] Sent email to author {author_id}")
                    except User.DoesNotExist:
                        pass
                except ImportError:
                    print("[ArticleWorkflow] Email marketing plugin not available")
                except Exception as e:
                    print(f"[ArticleWorkflow] Email notification to author failed: {e}")

            print(f"[ArticleWorkflow] Notified author (ID: {author_id}): {message}")
        except Exception as e:
            print(f"[ArticleWorkflow] Failed to notify author: {e}")
            import traceback
            traceback.print_exc()

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enable_workflow',
                    'type': 'boolean',
                    'label': '启用审批流程',
                    'help': '开启后,文章发布前需要经过审批',
                },
                {
                    'key': 'approval_levels',
                    'type': 'number',
                    'label': '审批层级数',
                    'min': 1,
                    'max': 5,
                    'help': '设置需要几级审批才能发布',
                },
                {
                    'key': 'auto_approve_editors',
                    'type': 'boolean',
                    'label': '编辑自动通过',
                    'help': '编辑角色的提交自动通过审批',
                },
                {
                    'key': 'notify_on_submission',
                    'type': 'boolean',
                    'label': '提交时通知审批人',
                },
                {
                    'key': 'notify_on_approval',
                    'type': 'boolean',
                    'label': '审批通过时通知作者',
                },
            ]
        }


# 插件实例
plugin_instance = ArticleWorkflowPlugin()
