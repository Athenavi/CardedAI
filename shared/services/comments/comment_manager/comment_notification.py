"""
评论通知服务 - 发送评论相关邮件通知
"""
import time
from typing import Dict, Any, Optional

from shared.services.notifications.email_service import email_service
from shared.services.notifications.notification_rate_limiter import notification_rate_limiter
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class CommentNotificationService:
    """评论通知服务"""

    def __init__(self):
        self.email_service = email_service

    @staticmethod
    def _build_email_template(
            title: str,
            greeting: str,
            content_html: str,
            buttons_html: str = "",
            footer_extra: str = ""
    ) -> tuple[str, str]:
        """
        构建通用邮件模板
        
        Returns:
            (html_content, text_content)
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #fff; padding: 20px; border: 1px solid #e9ecef; }}
                .comment-box {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 15px 0; }}
                .footer {{ background: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; font-size: 12px; color: #6c757d; }}
                .button {{ display: inline-block; padding: 10px 20px; background: #007bff; color: #fff; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{title}</h2>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    {content_html}
                    {buttons_html}
                </div>
                <div class="footer">
                    <p>此邮件由 FastBlog 自动发送，请勿回复。</p>
                    {footer_extra}
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"{greeting}\n\n{content_html}\n\n---\n此邮件由 FastBlog 自动发送，请勿回复。"
        return html_content, text_content

    def _check_rate_limit(
            self,
            email: str,
            user_id: Optional[int],
            notification_data: Dict[str, Any]
    ) -> bool:
        """
        检查邮件频率限制
        
        Returns:
            True if can send, False if rate limited
        """
        can_send, reason, pending_count = notification_rate_limiter.can_send_email(email)

        if not can_send:
            logger.warning(f"邮件频率限制: {email} - {reason}")
            notification_rate_limiter.add_pending_notification(email, notification_data)

            if user_id:
                can_add, should_agg, inbox_reason = notification_rate_limiter.can_add_inbox_notification(user_id)
                if can_add:
                    notification_rate_limiter.increment_inbox_count(user_id)
                    logger.info(f"添加站内通知: user_id={user_id}")
                else:
                    logger.info(f"站内信聚合: {inbox_reason}")
            return False
        return True

    def notify_article_author(
            self,
            author_email: str,
            author_name: str,
            article_title: str,
            article_url: str,
            commenter_name: str,
            comment_content: str,
            comment_url: str,
            article_id: int,
            author_user_id: int = None
    ) -> bool:
        """通知文章作者有新评论"""
        notification_data = {
            'type': 'new_comment',
            'article_title': article_title,
            'commenter_name': commenter_name,
            'comment_content': comment_content,
            'comment_url': comment_url,
            'timestamp': time.time()
        }

        if not self._check_rate_limit(author_email, author_user_id, notification_data):
            return False

        subject = f"【FastBlog】您的文章《{article_title}》收到了新评论"

        content_html = f"""
            <p>您好，<strong>{author_name}</strong>！</p>
            <p>您的文章 <a href="{article_url}"><strong>《{article_title}》</strong></a> 收到了一条评论。</p>
            
            <div class="comment-box">
                <p><strong>评论者：</strong>{commenter_name}</p>
                <p><strong>评论内容：</strong></p>
                <p style="white-space: pre-wrap;">{comment_content}</p>
            </div>
        """

        buttons_html = f"""
            <p>
                <a href="{comment_url}" class="button">查看评论</a>
                <a href="{article_url}" class="button" style="background: #6c757d;">查看文章</a>
            </p>
        """

        footer_extra = "<p>如需关闭通知，请登录后台修改设置。</p>"

        html_content, text_content = self._build_email_template(
            "📬 新评论通知",
            "",  # greeting already in content_html
            content_html,
            buttons_html,
            footer_extra
        )

        success = self.email_service.send_email(author_email, subject, html_content, text_content)
        if success:
            notification_rate_limiter.record_email_sent(author_email)
        return success

    def notify_comment_reply(
            self,
            recipient_email: str,
            recipient_name: str,
            article_title: str,
            article_url: str,
            replier_name: str,
            reply_content: str,
            original_comment: str,
            comment_url: str,
            article_id: int,
            recipient_user_id: int = None
    ) -> bool:
        """通知评论者有人回复"""
        notification_data = {
            'type': 'comment_reply',
            'article_title': article_title,
            'replier_name': replier_name,
            'reply_content': reply_content,
            'original_comment': original_comment,
            'comment_url': comment_url,
            'timestamp': time.time()
        }

        if not self._check_rate_limit(recipient_email, recipient_user_id, notification_data):
            return False

        subject = f"【FastBlog】您的评论收到了回复"

        content_html = f"""
            <p>您好，<strong>{recipient_name}</strong>！</p>
            <p>您在文章 <a href="{article_url}"><strong>《{article_title}》</strong></a> 下的评论收到了回复。</p>
            
            <div class="comment-box" style="border-left-color: #ffc107; background: #fff3cd;">
                <p><strong>您的评论：</strong></p>
                <p style="white-space: pre-wrap;">{original_comment}</p>
            </div>
            
            <div class="comment-box" style="border-left-color: #28a745;">
                <p><strong>{replier_name} 回复您：</strong></p>
                <p style="white-space: pre-wrap;">{reply_content}</p>
            </div>
        """

        buttons_html = f'<p><a href="{comment_url}" class="button" style="background: #28a745;">查看回复</a></p>'
        footer_extra = "<p>如需关闭通知，请登录后台修改设置。</p>"

        html_content, text_content = self._build_email_template(
            "💬 评论回复通知",
            "",
            content_html,
            buttons_html,
            footer_extra
        )

        success = self.email_service.send_email(recipient_email, subject, html_content, text_content)
        if success:
            notification_rate_limiter.record_email_sent(recipient_email)
        return success

    def notify_approval_result(
            self,
            recipient_email: str,
            recipient_name: str,
            article_title: str,
            article_url: str,
            is_approved: bool,
            comment_content: str,
            article_id: int,
            recipient_user_id: int = None
    ) -> bool:
        """通知评论审核结果"""
        status_text = "已通过" if is_approved else "未通过"
        status_icon = "✅" if is_approved else "❌"

        notification_data = {
            'type': 'approval_result',
            'article_title': article_title,
            'is_approved': is_approved,
            'comment_content': comment_content,
            'article_url': article_url,
            'timestamp': time.time()
        }

        if not self._check_rate_limit(recipient_email, recipient_user_id, notification_data):
            return False

        subject = f"【FastBlog】您的评论审核{status_text}"

        status_class = "approved" if is_approved else "rejected"
        status_style = "background: #d4edda; color: #155724; border: 1px solid #c3e6cb;" if is_approved else "background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;"

        content_html = f"""
            <p>您好，<strong>{recipient_name}</strong>！</p>
            <p>您在文章 <a href="{article_url}"><strong>《{article_title}》</strong></a> 下的评论已审核。</p>
            
            <div style="padding: 15px; border-radius: 4px; margin: 15px 0; font-weight: bold; text-align: center; {status_style}">
                审核结果：{status_text}
            </div>
            
            <div class="comment-box" style="border-left-color: #6c757d;">
                <p><strong>您的评论内容：</strong></p>
                <p style="white-space: pre-wrap;">{comment_content}</p>
            </div>
        """

        buttons_html = f'<p><a href="{article_url}" class="button">查看文章</a></p>' if is_approved else ''

        html_content, text_content = self._build_email_template(
            f"{status_icon} 评论审核通知",
            "",
            content_html,
            buttons_html,
            ""
        )

        success = self.email_service.send_email(recipient_email, subject, html_content, text_content)
        if success:
            notification_rate_limiter.record_email_sent(recipient_email)
        return success

    def send_aggregated_email(self, user_email: str, user_name: str) -> bool:
        """发送聚合通知邮件"""
        pending = notification_rate_limiter.get_and_clear_pending(user_email)
        if not pending:
            return False

        count = len(pending)
        subject = f"【FastBlog】您有{count}条新消息"

        # 按类型分组并构建HTML
        type_groups = {}
        for item in pending:
            notif_type = item['data']['type']
            if notif_type not in type_groups:
                type_groups[notif_type] = []
            type_groups[notif_type].append(item['data'])

        html_items = ""
        for notif_type, items in type_groups.items():
            if notif_type == 'new_comment':
                html_items += f"<h3 style='color: #007bff;'>💬 {len(items)} 条新评论</h3>"
                for item in items[:3]:
                    html_items += f"""
                    <div class="comment-box">
                        <p><strong>{item['commenter_name']}</strong> 在《{item['article_title']}》下评论：</p>
                        <p style="white-space: pre-wrap;">{item['comment_content'][:100]}...</p>
                        <a href="{item['comment_url']}" style="color: #007bff;">查看 →</a>
                    </div>
                    """
                if len(items) > 3:
                    html_items += f"<p style='text-align: center; color: #6c757d;'>还有 {len(items) - 3} 条评论未显示</p>"

            elif notif_type == 'comment_reply':
                html_items += f"<h3 style='color: #28a745;'>🔁 {len(items)} 条回复</h3>"
                for item in items[:3]:
                    html_items += f"""
                    <div class="comment-box">
                        <p><strong>{item['replier_name']}</strong> 回复了您在《{item['article_title']}》下的评论：</p>
                        <p style="white-space: pre-wrap;">{item['reply_content'][:100]}...</p>
                        <a href="{item['comment_url']}" style="color: #28a745;">查看 →</a>
                    </div>
                    """
                if len(items) > 3:
                    html_items += f"<p style='text-align: center; color: #6c757d;'>还有 {len(items) - 3} 条回复未显示</p>"

        content_html = f"""
            <p>您好，<strong>{user_name}</strong>！</p>
            <p>您在过去一段时间内有 <strong>{count}</strong> 条新消息：</p>
            {html_items}
            <p style="margin-top: 20px; text-align: center;">
                <a href="/notifications" style="display: inline-block; padding: 10px 20px; background: #007bff; color: #fff; text-decoration: none; border-radius: 4px;">查看所有消息</a>
            </p>
        """

        footer_extra = "<p>提示：您可以通过调整设置来控制通知频率。</p>"

        html_content, text_content = self._build_email_template(
            "📬 消息汇总通知",
            "",
            content_html,
            "",
            footer_extra
        )

        success = self.email_service.send_email(user_email, subject, html_content, text_content)
        if success:
            notification_rate_limiter.record_email_sent(user_email)
            logger.info(f"发送聚合邮件: {user_email}, 包含{count}条消息")
        return success


# 全局实例
comment_notification_service = CommentNotificationService()
