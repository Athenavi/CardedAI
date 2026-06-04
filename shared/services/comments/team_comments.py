"""
团队评论和反馈服务

提供内部评论、@提及、评论线程等功能
支持团队协作和内容反馈
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class TeamCommentService:
    """
    团队评论和反馈服务
    
    管理团队内部的评论和反馈
    """

    def __init__(self):
        """初始化团队评论服务"""
        # 存储评论 {comment_id: comment_data}
        self.comments: Dict[int, Dict[str, Any]] = {}

        # 评论ID计数器
        self.comment_counter = 0

        # @提及记录 {user_id: [comment_ids]}
        self.mentions: Dict[int, List[int]] = {}

    def create_comment(
            self,
            content_id: int,
            content_type: str,
            author_id: int,
            author_name: str,
            text: str,
            parent_id: Optional[int] = None,
            mentions: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        创建评论
        
        Args:
            content_id: 内容ID
            content_type: 内容类型
            author_id: 作者ID
            author_name: 作者名称
            text: 评论内容
            parent_id: 父评论ID（用于回复）
            mentions: @提及的用户ID列表
        
        Returns:
            创建的评论
        """
        self.comment_counter += 1
        comment_id = self.comment_counter

        comment = {
            'id': comment_id,
            'content_id': content_id,
            'content_type': content_type,
            'author_id': author_id,
            'author_name': author_name,
            'text': text,
            'parent_id': parent_id,
            'mentions': mentions or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': None,
            'is_resolved': False,
            'resolved_by': None,
            'resolved_at': None,
            'replies': [],
        }

        self.comments[comment_id] = comment

        # 添加到父评论的回复列表
        if parent_id and parent_id in self.comments:
            self.comments[parent_id]['replies'].append(comment_id)

        # 记录@提及
        if mentions:
            for user_id in mentions:
                if user_id not in self.mentions:
                    self.mentions[user_id] = []
                self.mentions[user_id].append(comment_id)

        return comment

    def update_comment(
            self,
            comment_id: int,
            author_id: int,
            text: str
    ) -> Dict[str, Any]:
        """
        更新评论
        
        Args:
            comment_id: 评论ID
            author_id: 作者ID
            text: 新的评论内容
        
        Returns:
            更新后的评论
        """
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")

        comment = self.comments[comment_id]

        if comment['author_id'] != author_id:
            raise ValueError("Only the author can update the comment")

        comment['text'] = text
        comment['updated_at'] = datetime.now().isoformat()

        return comment

    def delete_comment(self, comment_id: int, user_id: int, is_admin: bool = False) -> bool:
        """
        删除评论
        
        Args:
            comment_id: 评论ID
            user_id: 用户ID
            is_admin: 是否是管理员
        
        Returns:
            是否删除成功
        """
        if comment_id not in self.comments:
            return False

        comment = self.comments[comment_id]

        # 只有作者或管理员可以删除
        if comment['author_id'] != user_id and not is_admin:
            raise ValueError("Only the author or admin can delete the comment")

        # 删除评论及其回复
        self._delete_comment_recursive(comment_id)

        return True

    def resolve_comment(
            self,
            comment_id: int,
            resolver_id: int,
            resolver_name: str
    ) -> Dict[str, Any]:
        """
        标记评论为已解决
        
        Args:
            comment_id: 评论ID
            resolver_id: 解决者ID
            resolver_name: 解决者名称
        
        Returns:
            更新后的评论
        """
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")

        comment = self.comments[comment_id]
        comment['is_resolved'] = True
        comment['resolved_by'] = resolver_id
        comment['resolved_at'] = datetime.now().isoformat()

        return comment

    def get_comments_for_content(
            self,
            content_id: int,
            content_type: str,
            include_resolved: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取内容的评论
        
        Args:
            content_id: 内容ID
            content_type: 内容类型
            include_resolved: 是否包含已解决的评论
        
        Returns:
            评论列表
        """
        comments = [
            comment for comment in self.comments.values()
            if comment['content_id'] == content_id and
               comment['content_type'] == content_type and
               comment['parent_id'] is None  # 只返回顶级评论
        ]

        if not include_resolved:
            comments = [c for c in comments if not c['is_resolved']]

        # 按时间排序
        comments.sort(key=lambda x: x['created_at'])

        # 加载回复
        for comment in comments:
            comment['replies_data'] = self._get_replies(comment['id'])

        return comments

    def get_user_mentions(
            self,
            user_id: int,
            unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取用户的@提及
        
        Args:
            user_id: 用户ID
            unread_only: 是否只返回未读的
        
        Returns:
            提及列表
        """
        if user_id not in self.mentions:
            return []

        mentioned_comments = [
            self.comments[comment_id]
            for comment_id in self.mentions[user_id]
            if comment_id in self.comments
        ]

        # 按时间排序
        mentioned_comments.sort(key=lambda x: x['created_at'], reverse=True)

        return mentioned_comments

    def get_statistics(
            self,
            content_id: Optional[int] = None,
            content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取评论统计
        
        Args:
            content_id: 内容ID过滤
            content_type: 内容类型过滤
        
        Returns:
            统计信息
        """
        filtered_comments = list(self.comments.values())

        if content_id:
            filtered_comments = [c for c in filtered_comments if c['content_id'] == content_id]

        if content_type:
            filtered_comments = [c for c in filtered_comments if c['content_type'] == content_type]

        total = len(filtered_comments)
        resolved = sum(1 for c in filtered_comments if c['is_resolved'])
        unresolved = total - resolved

        # 统计每个作者的评论数
        by_author = {}
        for comment in filtered_comments:
            author = comment['author_name']
            if author not in by_author:
                by_author[author] = 0
            by_author[author] += 1

        return {
            'total_comments': total,
            'resolved_comments': resolved,
            'unresolved_comments': unresolved,
            'by_author': by_author,
        }

    def _delete_comment_recursive(self, comment_id: int):
        """
        递归删除评论及其回复
        
        Args:
            comment_id: 评论ID
        """
        if comment_id not in self.comments:
            return

        comment = self.comments[comment_id]

        # 先删除所有回复
        for reply_id in comment['replies']:
            self._delete_comment_recursive(reply_id)

        # 删除评论
        del self.comments[comment_id]

    def _get_replies(self, parent_id: int) -> List[Dict[str, Any]]:
        """
        获取评论的回复
        
        Args:
            parent_id: 父评论ID
        
        Returns:
            回复列表
        """
        replies = [
            comment for comment in self.comments.values()
            if comment['parent_id'] == parent_id
        ]

        # 按时间排序
        replies.sort(key=lambda x: x['created_at'])

        return replies


# 全局实例
team_comment_service = TeamCommentService()

# 导出
__all__ = ['TeamCommentService', 'team_comment_service']
