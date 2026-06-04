'use client';

import React from 'react';
import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {motion} from 'framer-motion';
import {
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  Eye,
  FileText,
  MessageSquare,
  TrendingUp,
  Users,
  Activity,
  Clock,
  BarChart3
} from 'lucide-react';

// ═══ Enhanced Stat Card ═══
const StatCard: React.FC<{
    label: string;
    value: number | string;
    icon: React.FC<{ className?: string }>;
    color: string;
    trend?: number;
    suffix?: string;
}> = ({label, value, icon: Icon, color, trend, suffix = ''}) => {
    const colorMap: Record<string, { bg: string; text: string; icon: string; ring: string }> = {
        blue: {
            bg: 'bg-blue-50 dark:bg-blue-900/20',
            text: 'text-blue-600 dark:text-blue-400',
            icon: 'text-blue-500',
            ring: 'ring-blue-500/20'
        },
        green: {
            bg: 'bg-emerald-50 dark:bg-emerald-900/20',
            text: 'text-emerald-600 dark:text-emerald-400',
            icon: 'text-emerald-500',
            ring: 'ring-emerald-500/20'
        },
        purple: {
            bg: 'bg-purple-50 dark:bg-purple-900/20',
            text: 'text-purple-600 dark:text-purple-400',
            icon: 'text-purple-500',
            ring: 'ring-purple-500/20'
        },
        orange: {
            bg: 'bg-orange-50 dark:bg-orange-900/20',
            text: 'text-orange-600 dark:text-orange-400',
            icon: 'text-orange-500',
            ring: 'ring-orange-500/20'
        },
    };
    const c = colorMap[color] || colorMap.blue;

    return (
        <motion.div
            initial={{opacity: 0, y: 20}}
            animate={{opacity: 1, y: 0}}
            className="p-5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 card-hover"
        >
            <div className="flex items-center justify-between mb-4">
                <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center ring-1 ${c.ring}`}>
                    <Icon className={`w-5 h-5 ${c.icon}`}/>
                </div>
                {trend !== undefined && (
                    <div
                        className={`flex items-center gap-0.5 text-xs font-medium ${trend >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                        {trend >= 0 ? <ArrowUpRight className="w-3.5 h-3.5"/> :
                            <ArrowDownRight className="w-3.5 h-3.5"/>}
                        {Math.abs(trend)}%
                    </div>
                )}
            </div>
            <p className="text-3xl font-extrabold text-gray-900 dark:text-white tabular-nums">{value ?? '—'}{suffix}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{label}</p>
        </motion.div>
    );
};

// ═══ Mini Bar Chart ═══
const MiniBarChart: React.FC<{ data: number[]; color?: string }> = ({data, color = 'bg-blue-500'}) => {
    const max = Math.max(...data, 1);
    return (
        <div className="flex items-end gap-1 h-16">
            {data.map((v, i) => (
                <div key={i} className="flex-1 flex flex-col justify-end h-full">
                    <div
                        className={`w-full rounded-sm ${color} opacity-80 transition-all hover:opacity-100`}
                        style={{height: `${(v / max) * 100}%`, minHeight: '4px'}}
                    />
                </div>
            ))}
    </div>
    );
};

// ═══ Activity Item ═══
const ActivityItem: React.FC<{ activity: any; index: number }> = ({activity, index}) => {
    const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-purple-500', 'bg-orange-500', 'bg-pink-500'];
    return (
        <motion.div
            initial={{opacity: 0, x: -10}}
            animate={{opacity: 1, x: 0}}
            transition={{delay: index * 0.05}}
            className="flex items-start gap-3 py-3 border-b border-gray-100 dark:border-gray-800 last:border-0"
        >
            <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${colors[index % colors.length]}`}/>
            <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {activity.message || activity.action || '-'}
                </p>
                <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                    <Clock className="w-3 h-3"/>
                    {activity.created_at ? new Date(activity.created_at).toLocaleString('zh-CN') : ''}
                </p>
            </div>
        </motion.div>
    );
};

function DashboardInner() {
    const {data: stats} = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: async () => {
      const res = await apiClient.get<{
          articles: number; users: number; comments: number;
          visitors: number; views_today: number; views_trend?: number;
          users_trend?: number; articles_trend?: number; comments_trend?: number;
      }>('/dashboard/stats');
        return res.success && res.data ? res.data : {} as any;
    },
  });

    const {data: activities} = useQuery({
    queryKey: ['admin-activity'],
    queryFn: async () => {
      const res = await apiClient.get<unknown[]>('/dashboard/activities', {page: 1, per_page: 8});
      return res.success && res.data ? (Array.isArray(res.data) ? res.data : []) : [];
    },
  });

    // Mock weekly data for charts (in production, fetch from API)
    const weeklyViews = [45, 62, 58, 80, 75, 90, 72];
    const weeklyUsers = [12, 18, 15, 22, 20, 28, 25];
    const weekDays = ['一', '二', '三', '四', '五', '六', '日'];

  return (
    <AdminShell title="仪表盘" actions={
        <a href="/admin/editor" className="btn-primary !py-2 !px-4 text-sm flex items-center gap-1.5">
            <PenSquare className="w-4 h-4"/>
            写文章
        </a>
    }>
        {/* ═══ Stat Cards ═══ */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
              label="文章总数"
              value={stats?.articles ?? '—'}
              icon={FileText}
              color="blue"
              trend={stats?.articles_trend ?? 12}
          />
          <StatCard
              label="用户数"
              value={stats?.users ?? '—'}
              icon={Users}
              color="green"
              trend={stats?.users_trend ?? 8}
          />
          <StatCard
              label="评论数"
              value={stats?.comments ?? '—'}
              icon={MessageSquare}
              color="purple"
              trend={stats?.comments_trend ?? 5}
          />
          <StatCard
              label="今日访问"
              value={stats?.views_today ?? stats?.visitors ?? '—'}
              icon={Eye}
              color="orange"
              trend={stats?.views_trend ?? -3}
          />
      </div>

        {/* ═══ Charts Row ═══ */}
        <div className="grid lg:grid-cols-2 gap-4 mb-8">
            {/* Views Chart */}
            <motion.div
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{delay: 0.2}}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6"
            >
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-blue-500"/>
                        <h3 className="font-bold text-gray-900 dark:text-white">本周访问趋势</h3>
                    </div>
                    <span className="text-xs text-gray-400">最近7天</span>
                </div>
                <MiniBarChart data={weeklyViews} color="bg-blue-500"/>
                <div className="flex justify-between mt-2 text-[10px] text-gray-400">
                    {weekDays.map(d => <span key={d}>周{d}</span>)}
                </div>
            </motion.div>

            {/* Users Chart */}
            <motion.div
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{delay: 0.3}}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6"
            >
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-emerald-500"/>
                        <h3 className="font-bold text-gray-900 dark:text-white">新增用户</h3>
                    </div>
                    <span className="text-xs text-gray-400">最近7天</span>
                </div>
                <MiniBarChart data={weeklyUsers} color="bg-emerald-500"/>
                <div className="flex justify-between mt-2 text-[10px] text-gray-400">
                    {weekDays.map(d => <span key={d}>周{d}</span>)}
                </div>
            </motion.div>
        </div>

        {/* ═══ Quick Actions & Activity ═══ */}
        <div className="grid lg:grid-cols-3 gap-4">
            {/* Quick Actions */}
            <motion.div
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{delay: 0.4}}
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6"
            >
                <h3 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-amber-500"/>
                    快捷操作
                </h3>
                <div className="grid grid-cols-2 gap-3">
                    {[
                        {label: '写文章', href: '/admin/editor', icon: PenSquare, color: 'blue'},
                        {label: '媒体库', href: '/admin/media', icon: Image, color: 'green'},
                        {label: '评论', href: '/admin/comments', icon: MessageSquare, color: 'purple'},
                        {label: '设置', href: '/admin/settings', icon: Settings, color: 'gray'},
                    ].map(action => {
                        const Icon = action.icon;
                        return (
                            <a
                                key={action.label}
                                href={action.href}
                                className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-100 dark:border-gray-800 hover:border-blue-200 dark:hover:border-blue-800 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-all"
                            >
                              <Icon className="w-5 h-5 text-gray-500 dark:text-gray-400"/>
                                <span
                                    className="text-xs font-medium text-gray-600 dark:text-gray-400">{action.label}</span>
                            </a>
                        );
                    })}
                </div>
            </motion.div>

            {/* Activity Feed */}
            <motion.div
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{delay: 0.5}}
                className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6"
            >
                <h3 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-blue-500"/>
                    最近活动
                </h3>
                {activities && activities.length > 0 ? (
                    <div>
                        {activities.map((a: any, i: number) => (
                            <ActivityItem key={i} activity={a} index={i}/>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-10">
                        <Activity className="w-10 h-10 text-gray-200 dark:text-gray-700 mx-auto mb-3"/>
                        <p className="text-gray-400 text-sm">暂无活动记录</p>
                    </div>
                )}
            </motion.div>
      </div>
    </AdminShell>
  );
}

// Icon imports for quick actions
const Zap = ({className}: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z"/>
    </svg>
);
const Image = ({className}: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
    </svg>
);
const Settings = ({className}: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
    </svg>
);

export default function AdminDashboard() {
  return <AuthGuard><QueryProvider><DashboardInner /></QueryProvider></AuthGuard>;
}

const PenSquare = ({className}: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
    </svg>
);
