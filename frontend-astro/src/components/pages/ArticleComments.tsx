'use client';

import React, {useState, useEffect, useCallback} from 'react';
import {useForm, FormProvider} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {commentService} from '@/lib/api/comment-service';
import type {Comment} from '@/lib/api/comment-service';
import {commentFormSchema, type CommentFormFormData} from '@/lib/schemas';
import {MessageSquare, Heart, Reply, Trash2, Clock, TrendingUp, ChevronDown, Send, X, AlertTriangle, Loader} from 'lucide-react';
import {useConfirm} from '@/components/ui/confirm-provider';

// ─── Types ────────────────────────────────────────────
interface Props {articleId: number;}

// ─── Helpers ──────────────────────────────────────────
const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return '刚刚';
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} 天前`;
  return new Date(iso).toLocaleDateString('zh-CN');
};

const getInitial = (name: string | null) => (name || '匿').charAt(0).toUpperCase();

const AVATAR_COLORS = [
  '#339af0', '#51cf66', '#ff6b6b', '#f59f00', '#cc5de8',
  '#20c997', '#e64980', '#15aabf', '#fab005', '#7950f2',
];
const avatarColor = (id: number) => AVATAR_COLORS[id % AVATAR_COLORS.length];

// ─── Comment Item (recursive) ─────────────────────────
const CommentItem: React.FC<{
  comment: Comment;
  depth: number;
  onLike: (id: number) => void;
  onDelete: (id: number) => void;
  onReply: (id: number, name: string) => void;
}> = ({comment, depth, onLike, onDelete, onReply}) => {
  const confirm = useConfirm();
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(comment.likes || 0);
  const [deleting, setDeleting] = useState(false);

  const handleLike = useCallback(async () => {
    if (!comment.id) return;
    const res = await commentService.likeComment(comment.id);
    if (res.success) {
      setLiked(res.data.action === 'liked');
      setLikeCount(res.data.likes);
    }
  }, [comment.id]);

  const handleDelete = useCallback(async () => {
    if (!comment.id || deleting) return;
    if (!await confirm({message: '确定删除此评论？', variant: 'danger'})) return;
    setDeleting(true);
    const res = await commentService.deleteComment(comment.id);
    if (res.success) onDelete(comment.id);
    setDeleting(false);
  }, [comment.id, deleting, onDelete]);

  const name = comment.author_name || comment.username || `用户${comment.user_id || ''}` || '匿名';
  const isApproved = comment.is_approved !== false;

  return (
    <div className={`group ${depth > 0 ? 'ml-8 lg:ml-12 border-l-2 border-gray-100 dark:border-gray-800 pl-4 lg:pl-6' : ''}`}>
      <div className="py-4">
        {/* Header */}
        <div className="flex items-center gap-2.5 mb-2">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
            style={{backgroundColor: avatarColor(comment.id || comment.article_id)}}
          >
            {getInitial(name)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900 dark:text-white truncate">{name}</span>
              {!isApproved && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] rounded-full bg-yellow-100 text-yellow-700 font-medium">
                  <AlertTriangle className="w-2.5 h-2.5"/>待审核
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400">{timeAgo(comment.created_at)}</p>
          </div>
        </div>

        {/* Content */}
        <div className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-3 whitespace-pre-wrap break-words">
          {comment.content}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <button onClick={handleLike} className={`inline-flex items-center gap-1 hover:text-red-500 transition-colors ${liked ? 'text-red-500' : ''}`}>
            <Heart className={`w-3.5 h-3.5 ${liked ? 'fill-current' : ''}`}/>
            {likeCount > 0 && <span>{likeCount}</span>}
          </button>
          <button onClick={() => onReply(comment.id!, name)} className="inline-flex items-center gap-1 hover:text-blue-500 transition-colors">
            <Reply className="w-3.5 h-3.5"/>回复
          </button>
          {deleting ? (
            <span className="text-gray-300"><Loader className="w-3 h-3 animate-spin"/></span>
          ) : (
            <button onClick={handleDelete} className="inline-flex items-center gap-1 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
              <Trash2 className="w-3.5 h-3.5"/>删除
            </button>
          )}
        </div>

          {/* Replies */}
          {comment.replies && comment.replies.length > 0 && (
          <div className="mt-1">
            {comment.replies.map((child) => (
              <CommentItem key={child.id} comment={child} depth={depth + 1} onLike={onLike} onDelete={onDelete} onReply={onReply}/>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Comment Form ─────────────────────────────────────
const CommentForm: React.FC<{
  articleId: number;
  parentId?: number;
  replyTo?: string;
  onCancel?: () => void;
  onSubmitted: () => void;
}> = ({articleId, parentId, replyTo, onCancel, onSubmitted}) => {
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState('');

  const form = useForm<CommentFormFormData>({
    resolver: zodResolver(commentFormSchema),
    defaultValues: {content: '', author_name: '', author_email: ''},
  });
  const {register, handleSubmit, watch, reset, formState: {errors}} = form;
  const contentValue = watch('content') || '';

  const isReply = !!parentId;

  const onSubmit = useCallback(async (data: CommentFormFormData) => {
    setSubmitting(true);
    setServerError('');

    const res = await commentService.createComment(
      articleId, data.content.trim(), parentId,
      data.author_name?.trim() || undefined, data.author_email?.trim() || undefined,
    );

    setSubmitting(false);
    if (res.success) {
      reset({content: '', author_name: '', author_email: ''});
      onSubmitted();
    } else {
      setServerError(res.error || '提交失败，请稍后重试');
    }
  }, [articleId, parentId, onSubmitted, reset]);

  return (
    <FormProvider {...form}>
    <div className={`${isReply ? 'mt-3 border-t border-gray-100 dark:border-gray-800 pt-3' : ''}`}>
      {replyTo && (
        <p className="text-xs text-blue-500 mb-2 flex items-center gap-1">
          <Reply className="w-3 h-3"/>回复 @{replyTo}
          {onCancel && <button onClick={onCancel} className="ml-auto text-gray-400 hover:text-gray-600"><X className="w-3.5 h-3.5"/></button>}
        </p>
      )}
      <textarea
        {...register('content')}
        placeholder={isReply ? '写下你的回复...' : '写下你的评论...'}
        rows={3}
        maxLength={2000}
        className={`w-full px-4 py-3 border rounded-xl bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400 resize-none transition-shadow ${
          errors.content ? 'border-red-400 dark:border-red-500' : 'border-gray-200 dark:border-gray-700'
        }`}
      />
      {errors.content && <p className="mt-1 text-xs text-red-500">{errors.content.message}</p>}
      <div className="flex items-center justify-between mt-2 gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <input {...register('author_name')} placeholder="昵称（可选）"
            className="flex-1 min-w-[100px] px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400"/>
          <input {...register('author_email')} placeholder="邮箱（可选）"
                 className={`flex-1 min-w-[120px] px-3 py-1.5 border rounded-lg bg-white dark:bg-gray-800 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400 ${
                   errors.author_email ? 'border-red-400 dark:border-red-500' : 'border-gray-200 dark:border-gray-700'
                 }`}/>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] text-gray-400">{contentValue.length}/2000</span>
          <button onClick={handleSubmit(onSubmit)} disabled={submitting}
            className="inline-flex items-center gap-1 px-4 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition-colors">
            {submitting ? <Loader className="w-3 h-3 animate-spin"/> : <Send className="w-3 h-3"/>}
            {isReply ? '回复' : '发表评论'}
          </button>
        </div>
      </div>
      {serverError && <p className="mt-1.5 text-xs text-red-500 flex items-center gap-1"><AlertTriangle
        className="w-3 h-3"/>{serverError}</p>}
    </div>
    </FormProvider>
  );
};

// ─── Main Component ───────────────────────────────────
const ArticleComments: React.FC<Props> = ({articleId}) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<string>('latest');
  const [replyTo, setReplyTo] = useState<{id: number; name: string} | null>(null);
  const [showSortMenu, setShowSortMenu] = useState(false);

  const loadComments = useCallback(async () => {
    setLoading(true);
    const res = await commentService.getComments(articleId, 1, 50, sortBy);
    if (res.success && res.data) {
      setComments(res.data.comments || []);
      setTotal(res.data.total || 0);
    }
    setLoading(false);
  }, [articleId, sortBy]);

  useEffect(() => { loadComments(); }, [loadComments]);

  const handleDelete = useCallback((id: number) => {
    setComments(prev => {
      const remove = (list: Comment[]): Comment[] =>
          list.filter(c => c.id !== id).map(c => ({...c, replies: remove(c.replies || [])}));
      return remove(prev);
    });
    setTotal(prev => Math.max(0, prev - 1));
  }, []);

  const handleSubmitted = useCallback(() => {
    setReplyTo(null);
    loadComments();
  }, [loadComments]);

  return (
    <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <MessageSquare className="w-5 h-5"/>
          评论
          {total > 0 && <span className="text-sm font-normal text-gray-400">({total})</span>}
        </h2>
        <div className="relative">
          <button onClick={() => setShowSortMenu(!showSortMenu)}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800">
            {sortBy === 'latest' ? <Clock className="w-3.5 h-3.5"/> : <TrendingUp className="w-3.5 h-3.5"/>}
            {sortBy === 'latest' ? '最新' : sortBy === 'popular' ? '最热' : '最早'}
            <ChevronDown className="w-3 h-3"/>
          </button>
          {showSortMenu && (
            <div className="absolute right-0 top-full mt-1 z-20 w-28 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-1">
              {[{v:'latest',l:'最新'},{v:'popular',l:'最热'},{v:'oldest',l:'最早'}].map(({v,l}) => (
                <button key={v} onClick={() => { setSortBy(v); setShowSortMenu(false); }}
                  className={`w-full text-left px-3 py-2 text-sm rounded-lg ${sortBy === v ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}>{l}</button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Comment form (top level) */}
      <div className="mb-8 bg-gray-50 dark:bg-gray-900 rounded-2xl p-4 lg:p-6">
        <CommentForm articleId={articleId} onSubmitted={handleSubmitted} />
      </div>

      {/* Comments list */}
      {loading ? (
        <div className="py-12 text-center"><div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/></div>
      ) : comments.length === 0 ? (
        <div className="py-12 text-center text-gray-400">
          <MessageSquare className="w-10 h-10 mx-auto mb-3 opacity-40"/>
          <p className="text-sm">暂无评论，来写第一条吧</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-100 dark:divide-gray-800/50">
          {comments.map(comment => (
            <div key={comment.id}>
              <CommentItem
                comment={comment}
                depth={0}
                onLike={() => {}}
                onDelete={handleDelete}
                onReply={(id, name) => setReplyTo(id === replyTo?.id ? null : {id, name})}
              />
              {/* Inline reply form */}
              {replyTo && replyTo.id === comment.id && (
                <div className="mb-4 ml-8 lg:ml-12 pl-4 lg:pl-6 border-l-2 border-blue-200 dark:border-blue-800">
                  <CommentForm articleId={articleId} parentId={comment.id} replyTo={replyTo.name}
                    onCancel={() => setReplyTo(null)} onSubmitted={handleSubmitted} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ArticleComments;
