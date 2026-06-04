'use client';

import {useQuery} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {DollarSign, TrendingUp, Banknote, Clock} from 'lucide-react';
import {StatCard} from './shared';

const StatsTab: React.FC = () => {
  const {data, isLoading} = useQuery({
    queryKey: ['revenue-platform-stats'],
    queryFn: () => apiClient.get('/shop/revenue/stats/platform'),
  });

  const stats = data?.data || {};

  if (isLoading) {
    return <div className="space-y-4">{[...Array(4)].map((_, i) => <div key={i}
                                                                        className="h-24 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={DollarSign} label="总交易额" value={`¥${(stats.total_revenue || 0).toLocaleString()}`}
                  color="bg-blue-500"/>
        <StatCard icon={TrendingUp} label="平台收益" value={`¥${(stats.platform_revenue || 0).toLocaleString()}`}
                  color="bg-green-500"/>
        <StatCard icon={Banknote} label="用户收益" value={`¥${(stats.user_revenue || 0).toLocaleString()}`}
                  color="bg-purple-500"/>
        <StatCard icon={Clock} label="待处理提现" value={`${stats.pending_payouts || 0} 笔`} color="bg-yellow-500"/>
      </div>
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">分成比例概览</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-full h-6 overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full flex items-center justify-end pr-2"
                 style={{width: `${stats.platform_ratio || 30}%`}}>
              <span className="text-[10px] text-white font-medium">{stats.platform_ratio || 30}%</span>
            </div>
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">平台 | 用户</span>
          <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-full h-6 overflow-hidden">
            <div className="h-full bg-green-500 rounded-full flex items-center justify-start pl-2"
                 style={{width: `${100 - (stats.platform_ratio || 30)}%`}}>
              <span className="text-[10px] text-white font-medium">{100 - (stats.platform_ratio || 30)}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatsTab;
