'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {Check, CheckCircle, Eye, X} from 'lucide-react';
import {ApprovalRecord, StatusBadge, PriorityBadge} from './shared';
import {useToast} from '@/components/ui/toast-provider';
import type {ApiResponse} from '@/lib/api/base-types';
const PendingTab: React.FC = () => {
  const qc = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState('');
  const [showDetail, setShowDetail] = useState<ApprovalRecord | null>(null);
  const [actionNotes, setActionNotes] = useState('');

  const {data, isLoading} = useQuery({
    queryKey: ['pending-approvals', page, typeFilter],
    queryFn: () => apiClient.get('/security/content-approval/pending', {
      page, per_page: 15,
      content_type: typeFilter || undefined,
    }),
  });

  const items: ApprovalRecord[] = data?.data?.approvals || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const approveMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/security/content-approval/${id}/approve`, {notes: actionNotes}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['pending-approvals']});
        setShowDetail(null);
        setActionNotes('');
      } else toast.error(r.error || '操作失败');
    },
  });
  const rejectMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/security/content-approval/${id}/reject`, {notes: actionNotes}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['pending-approvals']});
        setShowDetail(null);
        setActionNotes('');
      } else toast.error(r.error || '操作失败');
    },
  });
  const cancelMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/security/content-approval/${id}/cancel`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['pending-approvals']});
        setShowDetail(null);
      } else toast.error(r.error || '操作失败');
    },
  });

  const contentTypeLabels: Record<string, string> = {
    article: '文章', page: '页面', comment: '评论', media: '媒体', product: '商品',
  };

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <select value={typeFilter} onChange={e => {
            setTypeFilter(e.target.value);
            setPage(1);
          }}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
            <option value="">全部类型</option>
            {Object.entries(contentTypeLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-20 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={CheckCircle} title="暂无待审批内容" desc="所有内容已处理完毕"/>
      ) : (
        <div className="space-y-3">
          {items.map(a => (
            <div key={a.id}
                 className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className="px-2 py-0.5 text-[10px] rounded-full font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                      {contentTypeLabels[a.content_type] || a.content_type}
                    </span>
                    <PriorityBadge priority={a.priority}/>
                    <StatusBadge status={a.status}/>
                  </div>
                  <h3
                    className="font-semibold text-gray-900 dark:text-gray-100 mb-1">{a.content_title || `内容#${a.content_id}`}</h3>
                  <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                    <span>申请人: {a.requester_name || `用户#${a.requester_id}`}</span>
                    <span>步骤: {a.current_step}/{a.total_steps}</span>
                    <span>申请时间: {a.created_at?.slice(0, 16)}</span>
                  </div>
                  {a.reason && <p className="text-xs text-gray-400 mt-1 line-clamp-1">理由: {a.reason}</p>}
                </div>
                <div className="flex items-center gap-1 ml-4">
                  <button onClick={() => {
                    setShowDetail(a);
                    setActionNotes('');
                  }}
                          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800" title="查看详情">
                    <Eye className="w-4 h-4 text-gray-500 dark:text-gray-400"/>
                  </button>
                  <button onClick={() => {
                    setShowDetail(a);
                    setActionNotes('');
                  }}
                          className="p-2 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20" title="审批通过">
                    <Check className="w-4 h-4 text-green-500"/>
                  </button>
                  <button onClick={() => {
                    setShowDetail(a);
                    setActionNotes('');
                  }}
                          className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20" title="审批拒绝">
                    <X className="w-4 h-4 text-red-500"/>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {total > 15 &&
        <div className="mt-4"><Pagination page={page} totalPages={Math.ceil(total / 15)} onPageChange={setPage}/></div>}

      {/* Detail & Action Modal */}
      <Modal open={showDetail !== null} onClose={() => setShowDetail(null)} title="审批详情">
        {showDetail && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">内容类型：</span>
                <span
                  className="font-medium">{contentTypeLabels[showDetail.content_type] || showDetail.content_type}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">内容ID：</span>
                <span className="font-mono">#{showDetail.content_id}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">申请人：</span>
                <span>{showDetail.requester_name || `#${showDetail.requester_id}`}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">审批进度：</span>
                <span>{showDetail.current_step}/{showDetail.total_steps} 步</span>
              </div>
              <div className="col-span-2">
                <span className="text-gray-500 dark:text-gray-400">申请理由：</span>
                <span>{showDetail.reason || '无'}</span>
              </div>
            </div>

            <div className="border-t border-gray-100 dark:border-gray-800 pt-4">
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">审批备注</label>
              <textarea rows={3} value={actionNotes} onChange={e => setActionNotes(e.target.value)}
                        placeholder="输入审批意见（可选）"
                        className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white resize-none"/>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-gray-100 dark:border-gray-800">
              <button onClick={() => cancelMut.mutate(showDetail.id)} disabled={cancelMut.isPending}
                      className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                取消申请
              </button>
              <button onClick={() => rejectMut.mutate(showDetail.id)} disabled={rejectMut.isPending}
                      className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50">
                {rejectMut.isPending ? '处理中...' : '拒绝'}
              </button>
              <button onClick={() => approveMut.mutate(showDetail.id)} disabled={approveMut.isPending}
                      className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">
                {approveMut.isPending ? '处理中...' : '通过'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

export default PendingTab;
