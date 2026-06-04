'use client';

import {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Coins, Loader, Minus, Plus, TrendingUp, Users} from 'lucide-react';

function PointsInner() {
  const toast = useToast();
  const qc = useQueryClient();

  const {data: stats} = useQuery({
    queryKey: ['ext-points-stats'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/points/admin/stats');
      return r.success && r.data ? r.data : {};
    },
  });

  const {data: rules} = useQuery({
    queryKey: ['ext-points-rules'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/points/points-rules');
      const raw = r.success && r.data ? (r.data.rules || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const {data: exchangeRules} = useQuery({
    queryKey: ['ext-points-exchange'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/points/exchange-rules');
      const raw = r.success && r.data ? (r.data.rules || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const {data: leaderboard} = useQuery({
    queryKey: ['ext-points-leaderboard'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/points/leaderboard', {limit: 20, period: 'all'});
      const raw = r.success && r.data ? (r.data.leaderboard || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  // Admin add/deduct
  const [userId, setUserId] = useState('');
  const [pointsAmount, setPointsAmount] = useState('');
  const [reason, setReason] = useState('');

  const addMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/ext/points/admin/add-points', data),
    onSuccess: (r) => {
      if (r.success) {
        toast.success(r.message || '操作成功');
        setUserId('');
        setPointsAmount('');
        setReason('');
        qc.invalidateQueries({queryKey: ['ext-points-stats']});
      }
    },
  });
  const deductMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/ext/points/admin/deduct-points', data),
    onSuccess: (r) => {
      if (r.success) {
        toast.success(r.message || '操作成功');
        setUserId('');
        setPointsAmount('');
        setReason('');
        qc.invalidateQueries({queryKey: ['ext-points-stats']});
      }
    },
  });

  return (
    <AdminShell title="积分系统">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Users
            className="w-4 h-4"/>有积分的用户
          </div>
          <p className="text-2xl font-bold">{stats?.total_users_with_points ?? '—'}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Coins
            className="w-4 h-4"/>总发放积分
          </div>
          <p className="text-2xl font-bold">{stats?.total_points_issued ?? '—'}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><TrendingUp
            className="w-4 h-4"/>积分规则
          </div>
          <p className="text-2xl font-bold">{Array.isArray(rules) ? rules.length : '—'}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Points Rules */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">积分获取规则</h3>
          <div className="space-y-2">
            {Array.isArray(rules) && rules.length > 0 ? rules.map((r: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-2.5 border-b border-gray-100 dark:border-gray-800 last:border-0">
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{r.name || r.action || r.description}</p>
                  <p className="text-xs text-gray-400">{r.description || r.action || ''}</p>
                </div>
                <span className="text-sm font-semibold text-yellow-600">+{r.points || r.value || 0}</span>
              </div>
            )) : <p className="text-sm text-gray-400 text-center py-4">暂无规则</p>}
          </div>
        </div>

        {/* Exchange Rules */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">兑换规则</h3>
          <div className="space-y-2">
            {Array.isArray(exchangeRules) && exchangeRules.length > 0 ? exchangeRules.map((r: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-2.5 border-b border-gray-100 dark:border-gray-800 last:border-0">
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{r.name || r.item || r.description}</p>
                  <p className="text-xs text-gray-400">{r.description || ''}</p>
                </div>
                <span className="text-sm font-semibold text-red-500">{r.cost || r.points || 0} 积分</span>
              </div>
            )) : <p className="text-sm text-gray-400 text-center py-4">暂无兑换规则</p>}
          </div>
        </div>
      </div>

      {/* Admin actions */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">管理员操作</h3>
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">用户 ID</label>
            <input type="number" value={userId} onChange={e => setUserId(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-800 dark:text-white dark:border-gray-700"/>
          </div>
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">积分数量</label>
            <input type="number" value={pointsAmount} onChange={e => setPointsAmount(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-800 dark:text-white dark:border-gray-700"/>
          </div>
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">原因</label>
            <input value={reason} onChange={e => setReason(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-800 dark:text-white dark:border-gray-700"/>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={() => addMut.mutate({user_id: parseInt(userId), points: parseInt(pointsAmount), reason})}
            disabled={addMut.isPending || !userId || !pointsAmount}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg inline-flex items-center gap-1.5 disabled:opacity-50">
            {addMut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : <Plus className="w-4 h-4"/>}添加积分
          </button>
          <button onClick={() => deductMut.mutate({user_id: parseInt(userId), points: parseInt(pointsAmount), reason})}
            disabled={deductMut.isPending || !userId || !pointsAmount}
            className="px-4 py-2 border border-red-200 text-red-600 text-sm rounded-lg inline-flex items-center gap-1.5 hover:bg-red-50 disabled:opacity-50">
            {deductMut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : <Minus className="w-4 h-4"/>}扣除积分
          </button>
        </div>
      </div>

      {/* Leaderboard */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h3 className="font-semibold text-gray-900 dark:text-white">积分排行榜 TOP 20</h3>
        </div>
        {Array.isArray(leaderboard) && leaderboard.length > 0 ? (
          <table className="w-full"><thead className="bg-gray-50 dark:bg-gray-800 border-b"><tr>
            <th
              className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left w-12">排名
            </th>
            <th className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left">用户
            </th>
            <th className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-right">积分
            </th>
          </tr></thead><tbody className="divide-y">
            {leaderboard.map((entry: any, i: number) => (
              <tr key={entry.user_id || i} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-5 py-3">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                    ${i === 0 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' : i === 1 ? 'bg-gray-200 text-gray-600' : i === 2 ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400' : 'text-gray-500 dark:text-gray-400'}`}>
                    {i + 1}
                  </span>
                </td>
                <td className="px-5 py-3 text-sm text-gray-700 dark:text-gray-300">{entry.username || entry.user || `用户 #${entry.user_id}`}</td>
                <td className="px-5 py-3 text-sm font-semibold text-right">{entry.points || entry.score || 0}</td>
              </tr>
            ))}
          </tbody></table>
        ) : (
          <div className="p-8 text-center text-sm text-gray-400">暂无排行榜数据</div>
        )}
      </div>
    </AdminShell>
  );
}

export default function ExtPoints() { return <AuthGuard><QueryProvider><PointsInner/></QueryProvider></AuthGuard>; }
