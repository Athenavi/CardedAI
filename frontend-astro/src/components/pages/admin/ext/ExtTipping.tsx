'use client';


import {useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {DollarSign, Eye, TrendingUp} from 'lucide-react';

function TippingInner() {
  const __qc = useQueryClient();

  const {data: recentTips} = useQuery({
    queryKey: ['ext-tipping-recent'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/tipping/recent', {limit: 20});
      const raw = r.success && r.data ? (r.data.tips || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const {data: leaderboard} = useQuery({
    queryKey: ['ext-tipping-leaderboard'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/tipping/leaderboard', {limit: 20, period: 'all'});
      const raw = r.success && r.data ? (r.data.leaderboard || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const {data: presetAmounts} = useQuery({
    queryKey: ['ext-tipping-amounts'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/tipping/preset-amounts');
      return r.success && r.data ? r.data : {};
    },
  });

  const amounts: number[] = Array.isArray(presetAmounts?.amounts) ? presetAmounts.amounts : [];

  return (
    <AdminShell title="打赏系统">
      {/* Preset amounts */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2"><DollarSign className="w-5 h-5"/>预设打赏金额</h3>
        <div className="flex flex-wrap gap-2">
          {amounts.map((a, i) => (
            <span key={i} className="px-4 py-2 bg-green-50 dark:bg-green-900/20 text-green-700 rounded-xl text-sm font-medium">¥{a}</span>
          ))}
          {presetAmounts?.min_amount !== undefined && (
            <span className="text-xs text-gray-400 ml-2 self-center">范围: ¥{presetAmounts.min_amount} ~ ¥{presetAmounts.max_amount}</span>
          )}
          {!amounts.length && <p className="text-sm text-gray-400">暂无预设金额</p>}
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Recent tips */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2"><Eye className="w-5 h-5"/>最近打赏</h3>
          </div>
          {Array.isArray(recentTips) && recentTips.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {recentTips.slice(0, 15).map((tip: any, i: number) => (
                <div key={tip.tip_id || i} className="px-6 py-3.5 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <span className="font-medium">{tip.from_username || tip.from_user_id || '用户'}</span>
                      {' → '}
                      <span className="font-medium">{tip.to_username || tip.to_user_id || '用户'}</span>
                    </p>
                    <p className="text-xs text-gray-400">{tip.message || (tip.article_id ? `文章 #${tip.article_id}` : '')}</p>
                  </div>
                  <span className="text-sm font-bold text-green-600">¥{tip.amount || 0}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-sm text-gray-400">暂无打赏记录</div>
          )}
        </div>

        {/* Leaderboard */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2"><TrendingUp className="w-5 h-5"/>打赏排行榜 TOP 20</h3>
          </div>
          {Array.isArray(leaderboard) && leaderboard.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {leaderboard.map((entry: any, i: number) => (
                <div key={entry.user_id || i} className="px-6 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0
                      ${i === 0 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' : i === 1 ? 'bg-gray-200 text-gray-600' : i === 2 ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400' : 'text-gray-500 dark:text-gray-400'}`}>
                      {i + 1}
                    </span>
                    <span className="text-sm text-gray-700 dark:text-gray-300">{entry.username || entry.user || `用户 #${entry.user_id}`}</span>
                  </div>
                  <span className="text-sm font-semibold text-green-600">¥{entry.total_amount || entry.amount || 0}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-sm text-gray-400">暂无排行榜数据</div>
          )}
        </div>
      </div>
    </AdminShell>
  );
}

export default function ExtTipping() { return <AuthGuard><QueryProvider><TippingInner/></QueryProvider></AuthGuard>; }
