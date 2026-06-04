'use client';

import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {CheckCircle, Clock, FileText, XCircle} from 'lucide-react';
import {ApprovalStep, ApprovalStats, StatCard} from './shared';

const HistoryTab: React.FC = () => {
  const [page, _setPage] = useState(1);
  const [selectedRecord, _setSelectedRecord] = useState<number | null>(null);

  const {data, isLoading} = useQuery({
    queryKey: ['approval-history', page],
    queryFn: () => apiClient.get('/security/content-approval/stats'),
  });

  const stats: ApprovalStats = data?.data || {};

  const {data: historyData} = useQuery({
    queryKey: ['approval-record-history', selectedRecord],
    queryFn: () => selectedRecord ? apiClient.get(`/security/content-approval/${selectedRecord}/history`) : null,
    enabled: !!selectedRecord,
  });

  const _historySteps: ApprovalStep[] = historyData?.data?.steps || [];

  return (
    <div className="space-y-6">
      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i}
                                            className="h-20 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={FileText} label="总申请数" value={stats.total_requests || 0} color="bg-blue-500"/>
          <StatCard icon={Clock} label="待审批" value={stats.pending_count || 0} color="bg-yellow-500"/>
          <StatCard icon={CheckCircle} label="已通过" value={stats.approved_count || 0} color="bg-green-500"/>
          <StatCard icon={XCircle} label="已拒绝" value={stats.rejected_count || 0} color="bg-red-500"/>
        </div>
      )}

      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">按内容类型统计</h3>
        <div className="space-y-3">
          {(stats.by_content_type || []).map(ct => (
            <div key={ct.type} className="flex items-center gap-3">
              <span className="text-xs text-gray-500 dark:text-gray-400 w-16">{ct.type}</span>
              <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-full h-4 overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full"
                     style={{width: `${Math.min((ct.count / (stats.total_requests || 1)) * 100, 100)}%`}}/>
              </div>
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300 w-8 text-right">{ct.count}</span>
            </div>
          ))}
          {(!stats.by_content_type || stats.by_content_type.length === 0) && (
            <p className="text-xs text-gray-400 text-center py-2">暂无数据</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistoryTab;
