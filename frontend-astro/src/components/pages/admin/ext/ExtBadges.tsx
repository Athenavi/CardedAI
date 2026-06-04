'use client';

import React from 'react';
import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Award, Filter, Users} from 'lucide-react';

const CATEGORY_LABEL: Record<string, string> = {writing:'写作', consistency:'坚持', quality:'质量', community:'社区', social:'社交', special:'特殊'};

function BadgesInner() {
  const {data: stats} = useQuery({
    queryKey: ['ext-badges-stats'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/badges/admin/stats');
      return r.success && r.data ? r.data : {};
    },
  });

  const {data: available} = useQuery({
    queryKey: ['ext-badges-available'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/badges/available');
      const raw = r.success && r.data ? (r.data.badges || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const [categoryFilter, setCategoryFilter] = React.useState<string>('');
  const categories: string[] = Array.isArray(stats?.categories) ? stats.categories : [];

  const filtered = Array.isArray(available)
    ? (categoryFilter ? available.filter((b) => b.category === categoryFilter) : available)
    : [];

  return (
    <AdminShell title="徽章系统">
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Award
            className="w-4 h-4"/>总徽章数
          </div>
          <p className="text-2xl font-bold">{stats?.total_badges ?? '—'}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Users
            className="w-4 h-4"/>总授予次数
          </div>
          <p className="text-2xl font-bold">{stats?.total_awarded ?? '—'}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Filter
            className="w-4 h-4"/>分类
          </div>
          <p className="text-2xl font-bold">{categories.length}</p>
        </div>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        <button onClick={() => setCategoryFilter('')}
          className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors ${!categoryFilter ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-900 border text-gray-600'}`}>全部</button>
        {categories.map(c => (
          <button key={c} onClick={() => setCategoryFilter(c)}
            className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors ${categoryFilter === c ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-900 border text-gray-600'}`}>
            {CATEGORY_LABEL[c] || c}
          </button>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((badge: any, i: number) => (
          <div key={badge.key || i} className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
            <div className="flex items-start justify-between mb-3">
              <span className="text-2xl">{badge.icon || '🏅'}</span>
              <span className="text-[10px] text-gray-400 font-mono">{badge.category}</span>
            </div>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">{badge.name || badge.key}</p>
            <p className="text-xs text-gray-400 mt-1">{badge.description || ''}</p>
            {badge.points_reward > 0 && (
              <p className="text-[10px] text-yellow-600 mt-2">🎁 {badge.points_reward} 积分奖励</p>
            )}
          </div>
        ))}
        {!filtered.length && <div className="col-span-full text-center py-8 text-sm text-gray-400">暂无徽章</div>}
      </div>
    </AdminShell>
  );
}

export default function ExtBadges() { return <AuthGuard><QueryProvider><BadgesInner/></QueryProvider></AuthGuard>; }
