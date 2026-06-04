'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Eye, Search, ShoppingCart} from 'lucide-react';
import {MoneyDisplay} from './shared';
import type {Order} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const OrdersTab: React.FC = () => {
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  const {data, isLoading} = useQuery({
    queryKey: ['orders', page, search, statusFilter],
    queryFn: () => apiClient.get('/shop/orders', {
      page, per_page: 15,
      search: search || undefined,
      status: statusFilter || undefined,
    }),
  });

  const items: Order[] = data?.data?.orders || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const statusMut = useMutation({
    mutationFn: ({id, status}: { id: number; status: string }) => apiClient.put(`/shop/orders/${id}`, {status}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['orders']});
      else toast.error(r.error || '操作失败');
    },
  });

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    confirmed: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    shipped: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400',
    delivered: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    cancelled: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
    refunded: 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400',
  };

  const statusLabels: Record<string, string> = {
    pending: '待处理', confirmed: '已确认', shipped: '已发货',
    delivered: '已送达', completed: '已完成', cancelled: '已取消', refunded: '已退款',
  };

  const paymentStatusColors: Record<string, string> = {
    pending: 'text-yellow-600',
    paid: 'text-green-600',
    failed: 'text-red-600',
    refunded: 'text-gray-500 dark:text-gray-400',
  };

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input value={search} onChange={e => {
              setSearch(e.target.value);
              setPage(1);
            }}
                   placeholder="搜索订单..."
                   className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white w-64"/>
          </div>
          <select value={statusFilter} onChange={e => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
            <option value="">全部状态</option>
            {Object.entries(statusLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={ShoppingCart} title="暂无订单" desc="订单将在用户购买商品后自动生成"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">订单号</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">用户</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">金额</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">订单状态</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">支付状态</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">时间</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">操作</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(o => (
              <tr key={o.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td className="px-4 py-3 font-mono text-xs text-gray-900 dark:text-gray-100">{o.order_number}</td>
                <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{o.username || `用户#${o.user_id}`}</td>
                <td className="px-4 py-3 text-right font-medium"><MoneyDisplay amount={o.total_amount}
                                                                               currency={o.currency}/></td>
                <td className="px-4 py-3 text-center">
                    <span
                      className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${statusColors[o.status] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                      {statusLabels[o.status] || o.status}
                    </span>
                </td>
                <td className="px-4 py-3 text-center">
                    <span
                      className={`text-xs font-medium ${paymentStatusColors[o.payment_status] || 'text-gray-500 dark:text-gray-400'}`}>
                      {o.payment_status === 'paid' ? '已支付' : o.payment_status === 'pending' ? '待支付' : o.payment_status === 'failed' ? '失败' : o.payment_status}
                    </span>
                </td>
                <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">{o.created_at?.slice(0, 16)}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => {
                    setSelectedOrder(o);
                    setShowDetail(true);
                  }}
                          className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800" title="查看详情">
                    <Eye className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"/>
                  </button>
                </td>
              </tr>
            ))}
            </tbody>
          </table>
          {total > 15 && (
            <div className="p-3 border-t border-gray-100 dark:border-gray-800">
              <Pagination page={page} totalPages={Math.ceil(total / 15)} onPageChange={setPage}/>
            </div>
          )}
        </div>
      )}

      {/* Order Detail Modal */}
      <Modal open={showDetail} onClose={() => setShowDetail(false)} title={`订单详情 #${selectedOrder?.order_number}`}>
        {selectedOrder && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">用户：</span>
                <span className="font-medium">{selectedOrder.username || `#${selectedOrder.user_id}`}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">金额：</span>
                <MoneyDisplay amount={selectedOrder.total_amount} currency={selectedOrder.currency}/>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">支付方式：</span>
                <span>{selectedOrder.payment_method || '未指定'}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">下单时间：</span>
                <span>{selectedOrder.created_at?.slice(0, 16)}</span>
              </div>
              {selectedOrder.shipping_address && (
                <div className="col-span-2">
                  <span className="text-gray-500 dark:text-gray-400">收货地址：</span>
                  <span>{selectedOrder.shipping_address}</span>
                </div>
              )}
              {selectedOrder.tracking_number && (
                <div className="col-span-2">
                  <span className="text-gray-500 dark:text-gray-400">物流单号：</span>
                  <span className="font-mono">{selectedOrder.tracking_number}</span>
                </div>
              )}
            </div>
            <div className="border-t border-gray-100 dark:border-gray-800 pt-4">
              <h4 className="text-sm font-semibold mb-2">更新订单状态</h4>
              <div className="flex gap-2 flex-wrap">
                {['confirmed', 'shipped', 'delivered', 'completed', 'cancelled'].map(s => (
                  <button key={s} onClick={() => statusMut.mutate({id: selectedOrder.id, status: s})}
                          disabled={selectedOrder.status === s || statusMut.isPending}
                          className={`px-3 py-1.5 text-xs rounded-lg border ${selectedOrder.status === s ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50 dark:hover:bg-gray-800'} border-gray-200 dark:border-gray-700`}>
                    {statusLabels[s]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

export default OrdersTab;
