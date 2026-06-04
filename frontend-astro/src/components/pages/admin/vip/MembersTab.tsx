'use client';

import React, {useState} from 'react';
import {Crown, Users, DollarSign, TrendingUp, Search} from 'lucide-react';
import {Member} from './shared';

const MembersTab: React.FC<{ members: Member[]; stats: Record<string, any> }> = ({members, stats}) => {
  const [search, setSearch] = useState('');
  const filtered = members.filter(m => !search || m.username.includes(search));

  return <>
    {/* Stats */}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Crown
          className="w-4 h-4"/>VIP 总数
        </div>
        <p className="text-2xl font-bold">{stats.total_vip_count ?? '—'}</p></div>
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Users
          className="w-4 h-4"/>本月新增
        </div>
        <p className="text-2xl font-bold">{stats.monthly_new ?? '—'}</p></div>
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><DollarSign
          className="w-4 h-4"/>月收入
        </div>
        <p className="text-2xl font-bold">{stats.monthly_revenue ?? '—'}</p></div>
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><TrendingUp
          className="w-4 h-4"/>续费率
        </div>
        <p className="text-2xl font-bold">{stats.renewal_rate ? `${stats.renewal_rate}%` : '—'}</p></div>
    </div>

    {/* Search */}
    <div className="relative mb-4"><Search
      className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/><input type="text" value={search}
                                                                                           onChange={e => setSearch(e.target.value)}
                                                                                           placeholder="搜索会员..."
                                                                                           className="w-full pl-10 pr-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
    </div>

    {/* Table */}
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      {!filtered.length ? (
        <div className="p-12 text-center text-gray-400"><Crown className="w-10 h-10 mx-auto mb-3 opacity-40"/><p>暂无
          VIP 会员</p></div>
      ) : (
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800 border-b">
          <tr>
            <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">用户
            </th>
            <th
              className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden sm:table-cell">套餐
            </th>
            <th
              className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">到期
            </th>
            <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">状态
            </th>
            <th
              className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">金额
            </th>
          </tr>
          </thead>
          <tbody className="divide-y">
          {filtered.map(m => (
            <tr key={m.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
              <td className="px-5 py-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold">{m.username?.charAt(0) || '?'}</div>
                  <span className="font-medium text-sm text-gray-900 dark:text-white">{m.username}</span></div>
              </td>
              <td className="px-5 py-4 text-sm hidden sm:table-cell">
                <span
                  className="px-2 py-0.5 text-xs rounded-full bg-purple-100 dark:bg-purple-900/20 text-purple-700">{m.plan_name}</span>
              </td>
              <td
                className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">{m.expires_at ? new Date(m.expires_at).toLocaleDateString('zh-CN') : '-'}</td>
              <td className="px-5 py-4"><span
                className={`px-2 py-0.5 text-xs rounded-full ${m.is_active ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'}`}>{m.is_active ? '有效' : '过期'}</span>
              </td>
              <td
                className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 text-right hidden lg:table-cell">¥{m.amount.toFixed(2)}</td>
            </tr>
          ))}
          </tbody>
        </table>
      )}
    </div>
  </>;
};

export default MembersTab;
