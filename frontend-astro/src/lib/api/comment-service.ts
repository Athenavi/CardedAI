/**
 * 评论服务
 * 提供评论相关的API调用
 */

import {apiClient} from './base-client';

export interface Comment {
    id: number;
    article_id: number;
    user_id: number | null;
    username?: string;
    author_name: string | null;
    author_email: string | null;
    author_url: string | null;
    content: string;
    is_approved: boolean;
  status?: string;
    created_at: string;
    updated_at?: string;
    likes: number;
  dislikes?: number;
    parent_id: number | null;
    avatar_url?: string;
    replies?: Comment[];
  article_title?: string;
  article_slug?: string;
}

export interface CommentListResponse {
    success: boolean;
    data: {
        comments: Comment[];
        total: number;
        page: number;
        per_page: number;
    };
    error?: string;
}

export interface LikeCommentResponse {
    success: boolean;
    data: {
        action: 'liked' | 'unliked';
        likes: number;
    };
    error?: string;
}

/** 评论投票记录 */
export interface CommentVote {
  id: number;
  comment_id: number;
  user: number | null;
  vote_type: number; // 1: 赞, -1: 踩
  ip_address?: string;
  created_at: string;
}

/** 评论订阅记录 */
export interface CommentSubscription {
  id: number;
  article_id: number;
  user_id: number | null;
  email: string | null;
  notify_type: string; // new_comment | reply_to_me | all_replies
  is_active: boolean;
  confirm_token?: string;
  confirmed_at?: string;
  created_at: string;
  updated_at?: string;
  article_title?: string;
}

/** 评论投票统计 */
export interface CommentVoteStats {
  comment_id: number;
  up_votes: number;
  down_votes: number;
  total_votes: number;
}

/** 评论互动分析数据 */
export interface CommentAnalytics {
  total_comments: number;
  pending_comments: number;
  approved_comments: number;
  rejected_comments: number;
  total_votes: number;
  total_subscriptions: number;
  top_commented_articles: Array<{ article_id: number; article_title: string; comment_count: number }>;
  recent_vote_activity: number;
}

class CommentService {
    /**
     * 获取文章评论列表
     * @param articleId - 文章ID
     * @param page - 页码
     * @param perPage - 每页数量
     * @param sortBy - 排序方式 (created_at, likes)
     * @param order - 排序方向 (asc, desc)
     */
    async getComments(
        articleId: number,
        page: number = 1,
        perPage: number = 20,
        sortBy: string = 'created_at',
        order: string = 'desc'
    ): Promise<CommentListResponse> {
        try {
            // 使用 /comments/enhanced/article/{article_id} 端点
            const response = await apiClient.get<{
                comments: Comment[];
                total: number;
                page: number;
                per_page: number
            }>(
                `/comments/enhanced/article/${articleId}`,
                {page, per_page: perPage, sort_by: sortBy, order}
            );

            return response as CommentListResponse;
        } catch (error) {
            console.error('[CommentService] Failed to get comments:', error);
            return {
                success: false,
                data: {comments: [], total: 0, page, per_page: perPage},
                error: error instanceof Error ? error.message : '获取评论失败',
            };
        }
    }

    /**
     * 创建评论
     * @param articleId - 文章ID
     * @param content - 评论内容
     * @param parentId - 父评论ID（回复时使用）
     * @param authorName - 作者名称（访客评论）
     * @param authorEmail - 作者邮箱（访客评论）
     */
    async createComment(
        articleId: number,
        content: string,
        parentId?: number,
        authorName?: string,
        authorEmail?: string
    ): Promise<{ success: boolean; data?: Comment; error?: string }> {
        try {
            // 使用 /comments/ POST 方法创建评论
            const response = await apiClient.post<Comment>('/comments/', {
                article_id: articleId,
                content,
                parent_id: parentId,
                author_name: authorName,
                author_email: authorEmail,
            });

            return response as { success: boolean; data?: Comment; error?: string };
        } catch (error) {
            console.error('[CommentService] Failed to create comment:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : '发表评论失败',
            };
        }
    }

    /**
     * 点赞评论
     * @param commentId - 评论ID
     */
    async likeComment(commentId: number): Promise<LikeCommentResponse> {
        try {
            // 使用 /comments/enhanced/{comment_id}/like
            const response = await apiClient.post<{ action: 'liked' | 'unliked'; likes: number }>(
                `/comments/enhanced/${commentId}/like`
            );
            return response as LikeCommentResponse;
        } catch (error) {
            console.error('[CommentService] Failed to like comment:', error);
            return {
                success: false,
                data: {action: 'unliked', likes: 0},
                error: error instanceof Error ? error.message : '点赞失败',
            };
        }
    }

    /**
     * 取消点赞评论
     * @param commentId - 评论ID
     */
    async unlikeComment(commentId: number): Promise<LikeCommentResponse> {
        try {
            // 后端使用 toggle 机制，再次调用即可取消点赞
            const response = await apiClient.post<{ action: 'liked' | 'unliked'; likes: number }>(
                `/comments/enhanced/${commentId}/like`
            );
            return response as LikeCommentResponse;
        } catch (error) {
            console.error('[CommentService] Failed to unlike comment:', error);
            return {
                success: false,
                data: {action: 'liked', likes: 0},
                error: error instanceof Error ? error.message : '取消点赞失败',
            };
        }
    }

    /**
     * 获取用户对评论的投票状态
     * @param commentId - 评论ID
     */
    async getUserVote(commentId: number): Promise<{
        success: boolean;
        data?: { vote_type: 'like' | 'dislike' | null };
        error?: string;
    }> {
        try {
            // 使用 /comments/enhanced/{comment_id}/vote
            const response = await apiClient.get<{ vote_type: 'like' | 'dislike' | null }>(
                `/comments/enhanced/${commentId}/vote`
            );
            return response as { success: boolean; data?: { vote_type: 'like' | 'dislike' | null }; error?: string };
        } catch (error) {
            console.error('[CommentService] Failed to get user vote:', error);
            return {
                success: false,
                data: {vote_type: null},
                error: error instanceof Error ? error.message : '获取投票状态失败',
            };
        }
    }

    /**
     * 删除评论（仅管理员或评论作者）
     * @param commentId - 评论ID
     */
    async deleteComment(commentId: number): Promise<{
        success: boolean;
        error?: string;
    }> {
        try {
            const response = await apiClient.delete(`/comments/${commentId}`);
            return response as { success: boolean; error?: string };
        } catch (error) {
            console.error('[CommentService] Failed to delete comment:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : '删除评论失败',
            };
        }
    }

    /**
     * 更新评论（仅评论作者）
     * @param commentId - 评论ID
     * @param content - 新的评论内容
     */
    async updateComment(
        commentId: number,
        content: string
    ): Promise<{ success: boolean; data?: Comment; error?: string }> {
        try {
            const response = await apiClient.put<Comment>(`/comments/${commentId}`, {
                content,
            });
            return response as { success: boolean; data?: Comment; error?: string };
        } catch (error) {
            console.error('[CommentService] Failed to update comment:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : '更新评论失败',
            };
        }
    }

  /* ──────── 管理端 API ──────── */

  /**
   * 获取待审核评论列表（管理员）
   */
  async getPendingComments(): Promise<{ success: boolean; data?: Comment[]; error?: string }> {
    try {
      const res = await apiClient.get<unknown[]>('/comments/admin/comments/pending');
      return {
        success: !!res.success,
        data: Array.isArray(res.data) ? (res.data as Comment[]) : [],
      };
    } catch (error) {
      console.error('[CommentService] Failed to get pending comments:', error);
      return {success: false, data: [], error: error instanceof Error ? error.message : '获取待审评论失败'};
    }
  }

  /**
   * 获取所有评论列表（管理员），支持状态筛选
   * @param status - 筛选状态 (pending, approved, rejected, 空=全部)
   */
  async getAdminComments(status?: string): Promise<{ success: boolean; data?: Comment[]; error?: string }> {
    try {
      const res = await apiClient.get<unknown[]>('/comments/admin/comments', {status: status || undefined});
      const comments = res.success && res.data
        ? (Array.isArray(res.data) ? res.data : (res.data as { comments?: Comment[] }).comments || [])
        : [];
      return {success: !!res.success, data: comments as Comment[]};
    } catch (error) {
      console.error('[CommentService] Failed to get admin comments:', error);
      return {success: false, data: [], error: error instanceof Error ? error.message : '获取评论失败'};
    }
  }

  /**
   * 审核通过评论（管理员）
   * @param commentId - 评论ID
   */
  async approveComment(commentId: number): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await apiClient.post(`/comments/admin/comments/${commentId}/approve`);
      return {success: !!res.success};
    } catch (error) {
      console.error('[CommentService] Failed to approve comment:', error);
      return {success: false, error: error instanceof Error ? error.message : '审核通过失败'};
    }
  }

  /**
   * 拒绝评论（管理员）
   * @param commentId - 评论ID
   */
  async rejectComment(commentId: number): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await apiClient.post(`/comments/admin/comments/${commentId}/reject`);
      return {success: !!res.success};
    } catch (error) {
      console.error('[CommentService] Failed to reject comment:', error);
      return {success: false, error: error instanceof Error ? error.message : '拒绝评论失败'};
    }
  }

  /**
   * 删除评论（管理员）
   * @param commentId - 评论ID
   */
  async adminDeleteComment(commentId: number): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await apiClient.delete(`/comments/admin/comments/${commentId}`);
      return {success: !!res.success};
    } catch (error) {
      console.error('[CommentService] Failed to delete comment (admin):', error);
      return {success: false, error: error instanceof Error ? error.message : '删除评论失败'};
    }
  }

  /* ──────── 投票 API ──────── */

  /**
   * 对评论投票（赞/踩）
   * @param commentId - 评论ID
   * @param voteType - 投票类型 (1=赞, -1=踩)
   */
  async voteComment(commentId: number, voteType: 1 | -1): Promise<{
    success: boolean;
    data?: { action: string; likes: number; vote_type: number | null };
    error?: string;
  }> {
    try {
      const endpoint = voteType === 1
        ? `/comments/enhanced/${commentId}/vote/like`
        : `/comments/enhanced/${commentId}/vote/dislike`;
      const res = await apiClient.post<{ action: string; likes: number; vote_type: number | null }>(endpoint);
      return res as {
        success: boolean;
        data?: { action: string; likes: number; vote_type: number | null };
        error?: string
      };
    } catch (error) {
      console.error('[CommentService] Failed to vote comment:', error);
      return {success: false, error: error instanceof Error ? error.message : '投票失败'};
    }
  }

  /* ──────── 订阅 API ──────── */

  /**
   * 获取当前用户的评论订阅列表
   */
  async getMySubscriptions(): Promise<{
    success: boolean;
    data?: { subscriptions: CommentSubscription[]; total: number };
    error?: string;
  }> {
    try {
      const res = await apiClient.get<{ subscriptions: CommentSubscription[]; total: number }>(
        '/comments/subscriptions/my-subscriptions'
      );
      return res as {
        success: boolean;
        data?: { subscriptions: CommentSubscription[]; total: number };
        error?: string
      };
    } catch (error) {
      console.error('[CommentService] Failed to get subscriptions:', error);
      return {
        success: false,
        data: {subscriptions: [], total: 0},
        error: error instanceof Error ? error.message : '获取订阅列表失败'
      };
    }
  }

  /**
   * 订阅文章评论通知
   * @param articleId - 文章ID
   * @param email - 订阅邮箱
   * @param notifyType - 通知类型
   */
  async subscribeArticle(articleId: number, email: string, notifyType: string = 'new_comment'): Promise<{
    success: boolean;
    data?: unknown;
    error?: string;
  }> {
    try {
      const res = await apiClient.post('/comments/subscriptions/subscribe', {
        article_id: articleId,
        email,
        notify_type: notifyType,
      });
      return res as { success: boolean; data?: unknown; error?: string };
    } catch (error) {
      console.error('[CommentService] Failed to subscribe:', error);
      return {success: false, error: error instanceof Error ? error.message : '订阅失败'};
    }
  }

  /**
   * 取消订阅文章评论通知
   * @param articleId - 文章ID
   * @param email - 订阅邮箱
   */
  async unsubscribeArticle(articleId: number, email: string): Promise<{
    success: boolean;
    data?: unknown;
    error?: string;
  }> {
    try {
      const res = await apiClient.post('/comments/subscriptions/unsubscribe', {
        article_id: articleId,
        email,
      });
      return res as { success: boolean; data?: unknown; error?: string };
    } catch (error) {
      console.error('[CommentService] Failed to unsubscribe:', error);
      return {success: false, error: error instanceof Error ? error.message : '取消订阅失败'};
    }
  }
}

// 导出单例实例
export const commentService = new CommentService();
export default commentService;
