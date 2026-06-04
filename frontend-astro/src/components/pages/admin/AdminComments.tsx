'use client';

import React, {useState, useEffect, useRef, useMemo} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {
  Check,
  X,
  MessageSquare,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  RefreshCw,
  MoreHorizontal,
  Trash2,
  Search,
  ThumbsUp,
  ThumbsDown,
  TrendingUp,
  Mail,
  Bell,
  BellOff,
  BarChart3,
  ArrowUpRight,
  Globe,
} from 'lucide-react';
import type {Comment, CommentSubscription} from '@/lib/api/comment-service';

/* ── Tab Config ── */
type TabValue = 'pending' | 'approved' | 'rejected' | '' | 'subscriptions' | 'analytics';

interface TabDef {
  value: TabValue;
  label: string;
  icon: React.FC<{ className?: string }>;
  color: string;
}

const STATUS_TABS: TabDef[] = [
  {value: 'pending', label: '待审核', icon: Clock, color: 'amber'},
  {value: 'approved', label: '已通过', icon: CheckCircle2, color: 'green'},
  {value: 'rejected', label: '已拒绝', icon: XCircle, color: 'red'},
  {value: '', label: '全部', icon: MessageSquare, color: 'gray'},
  {value: 'subscriptions', label: '订阅管理', icon: Bell, color: 'blue'},
  {value: 'analytics', label: '数据分析', icon: BarChart3, color: 'purple'},
];

/* ── Comment Avatar ── */
const CommentAvatar: React.FC<{ name: string }> = ({name}) => {
  const colors = ['from-blue-500 to-indigo-500', 'from-purple-500 to-pink-500', 'from-emerald-500 to-teal-500', 'from-amber-500 to-orange-500', 'from-rose-500 to-red-500', 'from-cyan-500 to-blue-500'];
  const colorIndex = (name || '').charCodeAt(0) % colors.length;
  return (
    <div
      className={`w-9 h-9 rounded-full bg-gradient-to-br ${colors[colorIndex]} flex items-center justify-center text-white text-sm font-bold shadow-sm shrink-0`}>
      {(name || '?').charAt(0).toUpperCase()}
    </div>
  );
};

/* ── Status Badge ── */
const CommentStatusBadge: React.FC<{ status: string }> = ({status}) => {
  const config = useMemo(() => {
    switch (status) {
      case 'approved':
        return {
          label: '已通过',
          bg: 'bg-emerald-50 dark:bg-emerald-900/20',
          text: 'text-emerald-700 dark:text-emerald-400',
          dot: 'bg-emerald-500'
        };
      case 'rejected':
        return {
          label: '已拒绝',
          bg: 'bg-red-50 dark:bg-red-900/20',
          text: 'text-red-700 dark:text-red-400',
          dot: 'bg-red-500'
        };
      default:
        return {
          label: '待审核',
          bg: 'bg-amber-50 dark:bg-amber-900/20',
          text: 'text-amber-700 dark:text-amber-400',
          dot: 'bg-amber-500'
        };
    }
  }, [status]);
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${config.bg} ${config.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`}/>{config.label}
    </span>
  );
};

/* ── Vote Stats Display ── */
const VoteStats: React.FC<{ likes: number; dislikes?: number }> = ({likes, dislikes = 0}) => {
  return (
    <div className="flex items-center gap-3 text-xs text-gray-400 mt-1.5">
      <span className="inline-flex items-center gap-1">
        <ThumbsUp className="w-3 h-3 text-emerald-500"/>
        <span className="text-emerald-600 dark:text-emerald-400 font-medium">{likes}</span>
      </span>
      {dislikes > 0 && (
        <span className="inline-flex items-center gap-1">
          <ThumbsDown className="w-3 h-3 text-red-400"/>
          <span className="text-red-500 dark:text-red-400 font-medium">{dislikes}</span>
        </span>
      )}
      {likes + dislikes > 0 && (
        <span className="text-gray-300 dark:text-gray-600">|</span>
      )}
      {likes + dislikes > 0 && (
        <span className="inline-flex items-center gap-1">
          <TrendingUp className="w-3 h-3"/>
          <span>好评率 {likes + dislikes > 0 ? Math.round(likes / (likes + dislikes) * 100) : 0}%</span>
        </span>
      )}
    </div>
  );
};

/* ── Comment Card ── */
const CommentCard: React.FC<{
  comment: Comment;
  onApprove: () => void;
  onReject: () => void;
  onDelete: () => void;
  isPending?: boolean;
}> = ({comment, onApprove, onReject, onDelete}) => {
  const [showActions, setShowActions] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!showActions) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setShowActions(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showActions]);

  const status = comment.status || 'pending';
  const authorName = comment.author_name || comment.username || '匿名';
  const likes = comment.likes || 0;
  const dislikes = comment.dislikes || 0;

  return (
    <div className={`group p-5 hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors ${
      status === 'pending' ? 'border-l-2 border-l-amber-400' : ''
    }`}>
      <div className="flex items-start gap-3">
        <CommentAvatar name={authorName}/>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className="font-medium text-gray-900 dark:text-white text-sm">
              {authorName}
            </span>
            <CommentStatusBadge status={status}/>
            <span className="text-xs text-gray-400 ml-auto shrink-0">
              {comment.created_at ? new Date(comment.created_at).toLocaleString('zh-CN') : ''}
            </span>
          </div>

          {/* Content */}
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-2">{comment.content}</p>

          {/* Article Reference */}
          {comment.article_title && (
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <FileText className="w-3 h-3"/>
              <span>评论文章：</span>
              <a href={`/view?slug=${comment.article_slug || ''}`} target="_blank"
                 rel="noopener noreferrer"
                 className="text-blue-500 hover:text-blue-600 hover:underline truncate max-w-[200px]">
                {comment.article_title}
              </a>
            </div>
          )}

          {/* Vote Stats */}
          <VoteStats likes={likes} dislikes={dislikes}/>

          {/* Action Buttons for Pending */}
          {status === 'pending' && (
            <div className="flex items-center gap-2 mt-3">
              <button onClick={onApprove}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-medium rounded-lg shadow-sm shadow-emerald-500/20 hover:shadow-emerald-500/30 transition-all">
                <ThumbsUp className="w-3.5 h-3.5"/>通过
              </button>
              <button onClick={onReject}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white text-xs font-medium rounded-lg shadow-sm shadow-red-500/20 hover:shadow-red-500/30 transition-all">
                <ThumbsDown className="w-3.5 h-3.5"/>拒绝
              </button>
            </div>
          )}
        </div>

        {/* More Actions */}
        <div className="relative shrink-0" ref={ref}>
          <button onClick={() => setShowActions(!showActions)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 opacity-0 group-hover:opacity-100 transition-all">
            <MoreHorizontal className="w-4 h-4"/>
          </button>
          {showActions && (
            <div
              className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-1.5 min-w-[140px]">
              {status !== 'approved' && (
                <button onClick={() => {
                  setShowActions(false);
                  onApprove();
                }}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors">
                  <Check className="w-4 h-4"/>通过
                </button>
              )}
              {status !== 'rejected' && (
                <button onClick={() => {
                  setShowActions(false);
                  onReject();
                }}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                  <X className="w-4 h-4"/>拒绝
                </button>
              )}
              <div className="h-px bg-gray-100 dark:bg-gray-700 my-1"/>
              <button onClick={() => {
                setShowActions(false);
                onDelete();
              }}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                <Trash2 className="w-4 h-4"/>删除
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ── Subscription Card ── */
const SubscriptionCard: React.FC<{
  sub: CommentSubscription;
  onToggle: () => void;
  onDelete: () => void;
}> = ({sub, onToggle, onDelete}) => {
  const notifyTypeLabels: Record<string, string> = {
    new_comment: '新评论',
    reply_to_me: '回复我',
    all_replies: '所有回复',
  };

  return (
    <div className="p-4 hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors">
      <div className="flex items-center gap-3">
        <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${
          sub.is_active
            ? 'bg-blue-50 dark:bg-blue-900/20'
            : 'bg-gray-100 dark:bg-gray-800'
        }`}>
          {sub.is_active
            ? <Bell className="w-4 h-4 text-blue-500"/>
            : <BellOff className="w-4 h-4 text-gray-400"/>
          }
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
              <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {sub.email || `用户 #${sub.user_id}`}
              </span>
            <span className={`px-2 py-0.5 text-[10px] font-medium rounded-full ${
              sub.is_active
                ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-500'
            }`}>
                {sub.is_active ? '活跃' : '已暂停'}
              </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            {sub.article_title && (
              <>
                <FileText className="w-3 h-3"/>
                <span className="truncate max-w-[200px]">{sub.article_title}</span>
                <span>·</span>
              </>
            )}
            <span>{notifyTypeLabels[sub.notify_type] || sub.notify_type}</span>
            <span>·</span>
            <span>{sub.created_at ? new Date(sub.created_at).toLocaleDateString('zh-CN') : ''}</span>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button onClick={onToggle}
                  className={`p-1.5 rounded-lg text-xs transition-colors ${
                    sub.is_active
                      ? 'text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20'
                      : 'text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20'
                  }`}
                  title={sub.is_active ? '暂停' : '激活'}>
            {sub.is_active ? <BellOff className="w-4 h-4"/> : <Bell className="w-4 h-4"/>}
          </button>
          <button onClick={onDelete}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  title="删除">
            <Trash2 className="w-4 h-4"/>
          </button>
        </div>
      </div>
    </div>
  );
};

/* ── Stat Card ── */
const StatCard: React.FC<{
  icon: React.FC<{ className?: string }>;
  label: string;
  value: number;
  color: string;
  suffix?: string;
}> = ({icon: Icon, label, value, color, suffix}) => {
  const colorMap: Record<string, { bg: string; text: string; iconBg: string }> = {
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900/10',
      text: 'text-blue-700 dark:text-blue-400',
      iconBg: 'bg-blue-100 dark:bg-blue-900/30'
    },
    green: {
      bg: 'bg-emerald-50 dark:bg-emerald-900/10',
      text: 'text-emerald-700 dark:text-emerald-400',
      iconBg: 'bg-emerald-100 dark:bg-emerald-900/30'
    },
    amber: {
      bg: 'bg-amber-50 dark:bg-amber-900/10',
      text: 'text-amber-700 dark:text-amber-400',
      iconBg: 'bg-amber-100 dark:bg-amber-900/30'
    },
    red: {
      bg: 'bg-red-50 dark:bg-red-900/10',
      text: 'text-red-700 dark:text-red-400',
      iconBg: 'bg-red-100 dark:bg-red-900/30'
    },
    purple: {
      bg: 'bg-purple-50 dark:bg-purple-900/10',
      text: 'text-purple-700 dark:text-purple-400',
      iconBg: 'bg-purple-100 dark:bg-purple-900/30'
    },
    gray: {
      bg: 'bg-gray-50 dark:bg-gray-800/50',
      text: 'text-gray-700 dark:text-gray-400',
      iconBg: 'bg-gray-100 dark:bg-gray-800'
    },
  };
  const c = colorMap[color] || colorMap.gray;

  return (
    <div className={`rounded-xl ${c.bg} p-4 border border-transparent`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl ${c.iconBg} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${c.text}`}/>
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
          <p className={`text-xl font-bold ${c.text}`}>
            {value.toLocaleString()}{suffix || ''}
          </p>
        </div>
      </div>
    </div>
  );
};

/* ── Main Component ── */
function CommentsInner() {
  const confirm = useConfirm();
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabValue>('pending');
  const [searchInput, setSearchInput] = useState('');

  /* ── Data Queries ── */
  const {data: comments, isLoading, refetch} = useQuery({
    queryKey: ['admin-comments', activeTab],
    queryFn: async (): Promise<Comment[]> => {
      if (activeTab === 'pending') {
        const res = await apiClient.get<Comment[]>('/comments/admin/comments/pending');
        return res.success && res.data ? (Array.isArray(res.data) ? res.data : []) : [];
      }
      if (activeTab === 'subscriptions' || activeTab === 'analytics') return [];
      const res = await apiClient.get<Comment[] | {
        comments: Comment[]
      }>('/comments/admin/comments', {status: activeTab || undefined});
      if (!res.success || !res.data) return [];
      return Array.isArray(res.data) ? res.data : res.data.comments || [];
    },
    enabled: activeTab !== 'subscriptions' && activeTab !== 'analytics',
  });

  /* Fetch all comments for stats (only when on analytics tab or need totals) */
  const {data: allCommentsData} = useQuery({
    queryKey: ['admin-comments-all'],
    queryFn: async (): Promise<Comment[]> => {
      const res = await apiClient.get<Comment[] | { comments: Comment[] }>('/comments/admin/comments', {});
      if (!res.success || !res.data) return [];
      return Array.isArray(res.data) ? res.data : res.data.comments || [];
    },
  });

  /* Subscriptions query */
  const {data: subscriptionsData, isLoading: subsLoading} = useQuery({
    queryKey: ['admin-comment-subscriptions'],
    queryFn: async () => {
      const res = await apiClient.get<{ subscriptions: CommentSubscription[]; total: number }>(
        '/comments/subscriptions/my-subscriptions'
      );
      return res.success && res.data ? res.data : {subscriptions: [] as CommentSubscription[], total: 0};
    },
    enabled: activeTab === 'subscriptions',
  });

  const subscriptions = subscriptionsData?.subscriptions || [];

  /* ── Mutations ── */
  const approveMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/comments/admin/comments/${id}/approve`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['admin-comments']}),
  });

  const rejectMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/comments/admin/comments/${id}/reject`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['admin-comments']}),
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/comments/admin/comments/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['admin-comments']}),
  });

  const toggleSubMut = useMutation({
    mutationFn: async (sub: CommentSubscription) => {
      if (sub.is_active) {
        return apiClient.post('/comments/subscriptions/unsubscribe', {
          article_id: sub.article_id,
          email: sub.email,
        });
      }
      return apiClient.post('/comments/subscriptions/subscribe', {
        article_id: sub.article_id,
        email: sub.email,
        notify_type: sub.notify_type,
      });
    },
    onSuccess: () => qc.invalidateQueries({queryKey: ['admin-comment-subscriptions']}),
  });

  /* ── Filtered & Stats ── */
  const filteredComments = useMemo(() => {
    if (!comments) return [];
    if (!searchInput) return comments;
    const q = searchInput.toLowerCase();
    return comments.filter((c) =>
      (c.content || '').toLowerCase().includes(q) ||
      (c.author_name || '').toLowerCase().includes(q) ||
      (c.article_title || '').toLowerCase().includes(q)
    );
  }, [comments, searchInput]);

  const allComments = allCommentsData || [];
  const stats = useMemo(() => {
    const total = allComments.length;
    const pending = allComments.filter((c) => c.status === 'pending' || !c.status).length;
    const approved = allComments.filter((c) => c.status === 'approved').length;
    const rejected = allComments.filter((c) => c.status === 'rejected').length;
    const totalLikes = allComments.reduce((sum, c) => sum + (c.likes || 0), 0);
    const totalDislikes = allComments.reduce((sum, c) => sum + (c.dislikes || 0), 0);

    // Top commented articles
    const articleMap = new Map<number, { title: string; count: number }>();
    allComments.forEach((c) => {
      if (!c.article_id) return;
      const existing = articleMap.get(c.article_id);
      if (existing) {
        existing.count++;
      } else {
        articleMap.set(c.article_id, {title: c.article_title || `文章 #${c.article_id}`, count: 1});
      }
    });
    const topArticles = Array.from(articleMap.values())
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // Comment trend: group by date (last 7 days)
    const now = new Date();
    const trend: Array<{ date: string; count: number }> = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().slice(0, 10);
      const count = allComments.filter((c) =>
        c.created_at && c.created_at.startsWith(dateStr)
      ).length;
      trend.push({date: dateStr.slice(5), count});
    }

    return {total, pending, approved, rejected, totalLikes, totalDislikes, topArticles, trend};
  }, [allComments]);

  const maxTrendCount = Math.max(...stats.trend.map(t => t.count), 1);

  /* ── Tab Counts ── */
  const tabCounts: Record<string, number> = useMemo(() => ({
    pending: stats.pending,
    approved: stats.approved,
    rejected: stats.rejected,
    '': stats.total,
    subscriptions: subscriptions.length,
    analytics: 0,
  }), [stats, subscriptions]);

  /* ── Render ── */
  const isCommentTab = activeTab === 'pending' || activeTab === 'approved' || activeTab === 'rejected' || activeTab === '';

  return (
    <AdminShell title="评论管理" actions={
      <button onClick={() => refetch()}
              className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              title="刷新">
        <RefreshCw className="w-4 h-4"/>
      </button>
    }>
      {/* Status Tabs */}
      <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-1">
        {STATUS_TABS.map(tab => {
          const count = tabCounts[tab.value] ?? 0;
          return (
            <button key={tab.value} onClick={() => setActiveTab(tab.value)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                      activeTab === tab.value
                        ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-md shadow-gray-200/50 dark:shadow-gray-900/50 border border-gray-200 dark:border-gray-700'
                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/50'
                    }`}>
              <tab.icon className="w-4 h-4"/>
              {tab.label}
              {tab.value !== 'analytics' && (
                <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded-full ${
                  activeTab === tab.value
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
                }`}>{count}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Comment Tabs Content ── */}
      {isCommentTab && (
        <>
          {/* Search */}
          <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                <input type="text" value={searchInput} onChange={e => setSearchInput(e.target.value)}
                       placeholder="搜索评论内容、作者、文章标题..."
                       className="w-full pl-10 pr-10 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white transition-all"/>
                {searchInput && (
                    <button onClick={() => setSearchInput('')}
                            className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 transition-colors">
                      <X className="w-4 h-4"/>
                    </button>
                )}
          </div>

          {/* Comments List */}
          <div
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden shadow-sm">
            {isLoading ? (
              <div className="divide-y divide-gray-50 dark:divide-gray-800/50">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="p-5 animate-pulse">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-gray-200 dark:bg-gray-700 rounded-full"/>
                      <div className="flex-1 space-y-2">
                                <div className="flex items-center gap-2">
                                  <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded"/>
                                  <div className="h-5 w-16 bg-gray-100 dark:bg-gray-800 rounded-full"/>
                                </div>
                                <div className="h-4 w-full bg-gray-100 dark:bg-gray-800 rounded"/>
                                <div className="h-3 w-2/3 bg-gray-50 dark:bg-gray-800/50 rounded"/>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredComments.length === 0 ? (
              <div className="p-16 text-center">
                <div
                  className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="w-8 h-8 text-gray-300 dark:text-gray-600"/>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                  {searchInput ? '未找到匹配的评论' : activeTab === 'pending' ? '暂无待审评论' : '暂无评论'}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {searchInput ? '尝试使用不同的关键词搜索' : activeTab === 'pending' ? '所有评论都已处理完毕' : '该分类下暂无评论'}
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50 dark:divide-gray-800/50">
                {filteredComments.map((c) => (
                  <CommentCard
                    key={c.id}
                    comment={c}
                    onApprove={() => approveMut.mutate(c.id)}
                    onReject={() => rejectMut.mutate(c.id)}
                    onDelete={async () => {
                      if (await confirm({
                        message: '确认删除此评论？此操作不可恢复。',
                        variant: 'danger'
                      })) deleteMut.mutate(c.id);
                    }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Batch Actions for Pending */}
          {activeTab === 'pending' && filteredComments.length > 0 && (
            <div
              className="flex items-center justify-between mt-4 p-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 rounded-xl">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600"/>
                      <span className="text-sm text-amber-800 dark:text-amber-300">
              有 <strong>{filteredComments.length}</strong> 条待审核评论
            </span>
                    </div>
              <button onClick={async () => {
                if (await confirm({
                  message: `确认批量通过所有 ${filteredComments.length} 条评论？`,
                  variant: 'danger'
                })) {
                  filteredComments.forEach((c) => approveMut.mutate(c.id));
                }
                    }}
                            className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg transition-colors">
                <CheckCircle2 className="w-4 h-4"/>全部通过
                    </button>
            </div>
          )}
        </>
      )}

      {/* ── Subscriptions Tab ── */}
      {activeTab === 'subscriptions' && (
        <div className="space-y-4">
          {/* Header */}
          <div
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden shadow-sm">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-blue-500"/>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">评论订阅管理</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    管理文章评论的邮件订阅通知，共 {subscriptions.length} 个订阅
                  </p>
                </div>
              </div>
            </div>

            {subsLoading ? (
              <div className="p-5 space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center gap-3 animate-pulse">
                    <div className="w-9 h-9 bg-gray-200 dark:bg-gray-700 rounded-full"/>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded"/>
                      <div className="h-3 w-48 bg-gray-100 dark:bg-gray-800 rounded"/>
                    </div>
                  </div>
                ))}
              </div>
            ) : subscriptions.length === 0 ? (
              <div className="p-12 text-center">
                <div
                  className="w-14 h-14 bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-3">
                  <Bell className="w-7 h-7 text-gray-300 dark:text-gray-600"/>
                </div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">暂无订阅</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">还没有用户订阅评论通知</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50 dark:divide-gray-800/50">
                {subscriptions.map((sub) => (
                  <SubscriptionCard
                    key={sub.id}
                    sub={sub}
                    onToggle={() => toggleSubMut.mutate(sub)}
                    onDelete={async () => {
                      if (await confirm({
                        message: `确认删除此订阅？`,
                        variant: 'danger'
                      })) {
                        await apiClient.post('/comments/subscriptions/unsubscribe', {
                          article_id: sub.article_id,
                          email: sub.email,
                        });
                        qc.invalidateQueries({queryKey: ['admin-comment-subscriptions']});
                      }
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Analytics Tab ── */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {/* Overview Stats */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <StatCard icon={MessageSquare} label="评论总数" value={stats.total} color="blue"/>
            <StatCard icon={Clock} label="待审核" value={stats.pending} color="amber"/>
            <StatCard icon={CheckCircle2} label="已通过" value={stats.approved} color="green"/>
            <StatCard icon={ThumbsUp} label="总点赞" value={stats.totalLikes} color="purple"/>
            <StatCard icon={TrendingUp} label="好评率"
                      value={stats.totalLikes + stats.totalDislikes > 0
                        ? Math.round(stats.totalLikes / (stats.totalLikes + stats.totalDislikes) * 100)
                        : 0}
                      color="gray"
                      suffix="%"/>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Comment Trend (last 7 days) */}
            <div
              className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden shadow-sm">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-500"/>
                  <h3 className="font-semibold text-gray-900 dark:text-white text-sm">近7天评论趋势</h3>
                </div>
              </div>
              <div className="p-6">
                <div className="flex items-end gap-2 h-32">
                  {stats.trend.map((t, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <span className="text-[10px] text-gray-400 font-medium">{t.count}</span>
                      <div
                        className="w-full rounded-t-md bg-blue-500/80 dark:bg-blue-400/60 transition-all"
                        style={{height: `${Math.max(t.count / maxTrendCount * 100, 4)}%`}}
                      />
                      <span className="text-[10px] text-gray-400">{t.date}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Top Commented Articles */}
            <div
              className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden shadow-sm">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-2">
                  <ArrowUpRight className="w-4 h-4 text-emerald-500"/>
                  <h3 className="font-semibold text-gray-900 dark:text-white text-sm">热门评论文章</h3>
                </div>
              </div>
              <div className="divide-y divide-gray-50 dark:divide-gray-800/50">
                {stats.topArticles.length === 0 ? (
                  <div className="p-8 text-center">
                    <Globe className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2"/>
                    <p className="text-xs text-gray-500">暂无评论数据</p>
                  </div>
                ) : (
                  stats.topArticles.map((article, i) => (
                    <div key={i} className="flex items-center gap-3 px-6 py-3.5">
                              <span
                                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                                  i === 0 ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                                    : i === 1 ? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                                      : i === 2 ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                                        : 'bg-gray-50 dark:bg-gray-800/50 text-gray-400'
                                }`}>
                                {i + 1}
                              </span>
                      <span className="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate">
                                {article.title}
                              </span>
                      <span
                        className="text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">
                                {article.count} 条评论
                              </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Status Distribution */}
          <div
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden shadow-sm">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-500"/>
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm">评论状态分布</h3>
              </div>
            </div>
            <div className="p-6">
              <div className="flex gap-2 h-6 rounded-full overflow-hidden">
                {stats.total > 0 && (
                  <>
                    <div className="bg-emerald-500 transition-all"
                         style={{width: `${stats.approved / stats.total * 100}%`}}
                         title={`已通过: ${stats.approved}`}/>
                    <div className="bg-amber-500 transition-all"
                         style={{width: `${stats.pending / stats.total * 100}%`}}
                         title={`待审核: ${stats.pending}`}/>
                    <div className="bg-red-500 transition-all" style={{width: `${stats.rejected / stats.total * 100}%`}}
                         title={`已拒绝: ${stats.rejected}`}/>
                  </>
                )}
              </div>
              <div className="flex items-center gap-6 mt-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"/>已通过 {stats.approved}
                    </span>
                <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500"/>待审核 {stats.pending}
                    </span>
                <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-red-500"/>已拒绝 {stats.rejected}
                    </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </AdminShell>
  );
}

export default function AdminComments() {
  return <AuthGuard><QueryProvider><CommentsInner/></QueryProvider></AuthGuard>;
}
