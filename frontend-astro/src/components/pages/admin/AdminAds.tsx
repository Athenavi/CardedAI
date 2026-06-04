'use client';

import React, {useMemo, useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {
  AlertTriangle,
  Eye,
  Layout,
  Loader,
  MousePointerClick,
  Pause,
  Play,
  Plus,
  Search,
  ToggleLeft,
  Trash2,
  X,
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────
interface AdSlot {
  slot_id: string;
  name: string;
  position: string;
  width: number;
  height: number;
  description: string;
  stats?: {active_ads: number; total_impressions: number; total_clicks: number; ctr: number};
}

interface Ad {
  ad_id: string;
  title: string;
  slot_id: string;
  ad_type: string;
  content: string;
  image_url?: string;
  link_url?: string;
  html_code?: string;
  start_date: string;
  end_date: string;
  priority: number;
  budget?: number;
  spent: number;
  status: 'active' | 'paused' | 'expired';
  created_at: string;
  updated_at: string;
}

// ─── Helpers ──────────────────────────────────────────
const fmtNum = (n: number | undefined | null) => {
  if (n == null) return '—';
  return n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n / 1_000).toFixed(1)}K` : String(n);
};

const statusBadge = (status: string) => {
  const map: Record<string, string> = {
    active: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    paused: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    expired: 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
  };
  const labels: Record<string, string> = {active: '投放中', paused: '已暂停', expired: '已过期'};
  return <span
    className={`px-2 py-0.5 text-xs rounded-full font-medium ${map[status] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>{labels[status] || status}</span>;
};

const typeLabel: Record<string, string> = {image: '图片', html: 'HTML', adsense: 'AdSense', baidu: '百度联盟'};
const slotLabels: Record<string, string> = {header_top: '顶部横幅', sidebar_right: '右侧边栏', article_inline: '文中广告', footer_bottom: '底部广告', homepage_banner: '首页轮播'};

// ─── Stat Card ────────────────────────────────────────
const StatCard: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: any;
  sub?: string;
  color?: string
}> = ({icon: Icon, label, value, sub, color}) => (
  <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
    <div className="flex items-center justify-between mb-2"><span
      className="text-sm text-gray-500 dark:text-gray-400">{label}</span><Icon
      className={`w-5 h-5 ${color || 'text-gray-400'}`}/></div>
    <p className="text-2xl font-bold text-gray-900 dark:text-white">{fmtNum(value)}</p>
    {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
  </div>
);

// ─── Create Ad Modal ──────────────────────────────────
const CreateAdModal: React.FC<{open: boolean; onClose: () => void; slots: AdSlot[]; onCreated: () => void}> = ({open, onClose, slots, onCreated}) => {
  const [title, setTitle] = useState('');
  const [slotId, setSlotId] = useState(slots[0]?.slot_id || '');
  const [adType, setAdType] = useState<string>('image');
  const [content, setContent] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [linkUrl, setLinkUrl] = useState('');
  const [htmlCode, setHtmlCode] = useState('');
  const [priority, setPriority] = useState(5);
  const [budget, setBudget] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [error, setError] = useState('');

  const createMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/ads/create', data),
    onSuccess: (res) => {
      if (res.success) { onCreated(); onClose(); reset(); }
      else setError(res.error || '创建失败');
    },
    onError: () => setError('创建失败，请稍后重试'),
  });

  const reset = () => {
    setTitle(''); setSlotId(slots[0]?.slot_id || ''); setAdType('image');
    setContent(''); setImageUrl(''); setLinkUrl(''); setHtmlCode('');
    setPriority(5); setBudget(''); setStartDate(''); setEndDate(''); setError('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) { setError('请输入广告标题'); return; }
    setError('');
    createMut.mutate({title: title.trim(), slot_id: slotId, ad_type: adType, content, image_url: imageUrl || undefined, link_url: linkUrl || undefined, html_code: htmlCode || undefined, priority, budget: budget ? parseFloat(budget) : undefined, start_date: startDate || undefined, end_date: endDate || undefined});
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto m-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="font-semibold text-gray-900 dark:text-white">创建广告</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5"/></button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">广告标题 *</label>
            <input value={title} onChange={e => setTitle(e.target.value)} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" placeholder="输入广告标题" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">广告位</label>
              <select value={slotId} onChange={e => setSlotId(e.target.value)} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
                {slots.map(s => <option key={s.slot_id} value={s.slot_id}>{s.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">广告类型</label>
              <select value={adType} onChange={e => setAdType(e.target.value)} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
                <option value="image">图片</option>
                <option value="html">HTML</option>
                <option value="adsense">AdSense</option>
                <option value="baidu">百度联盟</option>
              </select>
            </div>
          </div>

          {adType === 'image' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">图片 URL</label>
                <input value={imageUrl} onChange={e => setImageUrl(e.target.value)} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" placeholder="https://..." />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">跳转链接</label>
                <input value={linkUrl} onChange={e => setLinkUrl(e.target.value)} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" placeholder="https://..." />
              </div>
            </>
          )}

          {adType === 'html' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">HTML 代码</label>
              <textarea value={htmlCode} onChange={e => setHtmlCode(e.target.value)} rows={4} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white font-mono" placeholder="<div>...</div>" />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">广告内容（文本描述）</label>
            <textarea value={content} onChange={e => setContent(e.target.value)} rows={2} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">优先级 (1-10)</label>
              <input type="number" min={1} max={10} value={priority} onChange={e => setPriority(Math.min(10, Math.max(1, parseInt(e.target.value) || 5)))} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">预算</label>
              <input type="number" min={0} value={budget} onChange={e => setBudget(e.target.value)} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" placeholder="不限" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">开始时间</label>
              <input type="datetime-local" value={startDate} onChange={e => setStartDate(e.target.value)} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">结束时间</label>
              <input type="datetime-local" value={endDate} onChange={e => setEndDate(e.target.value)} className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" />
            </div>
          </div>

          {error && <p className="text-xs text-red-500 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/>{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800">取消</button>
            <button type="submit" disabled={createMut.isPending}
              className="inline-flex items-center gap-1.5 px-5 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition-colors">
              {createMut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : <Plus className="w-4 h-4"/>}
              创建
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────
function AdsInner() {
  const confirm = useConfirm();
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [filterSlot, setFilterSlot] = useState('');
  const [search, setSearch] = useState('');

  // ── queries ──
  const {data: slots, isLoading: slotsLoading} = useQuery({
    queryKey: ['ads-slots'],
    queryFn: async () => {
      const r = await apiClient.get('/ads/slots');
      if (r.success) {
        const raw = r.data?.slots || r.data || [];
        return Array.isArray(raw) ? raw : [];
      }
      return [];
    },
  });

  const {data: adsData, isLoading: adsLoading} = useQuery({
    queryKey: ['ads-list', filterSlot],
    queryFn: async () => {
      const r = await apiClient.get('/ads/list', filterSlot ? {slot_id: filterSlot} : undefined);
      if (r.success) {
        const raw = r.data?.ads || r.data || [];
        return Array.isArray(raw) ? raw : [];
      }
      return [];
    },
  });

  // ── mutations ──
  const toggleMut = useMutation({
    mutationFn: ({id, action}:{id:string;action:'activate'|'pause'}) => apiClient.post(`/ads/${id}/${action}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['ads-list']}),
  });
  const delMut = useMutation({
    mutationFn: (id:string) => apiClient.delete(`/ads/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['ads-list']}),
  });

  // ── derived data ──
  const slotList: AdSlot[] = Array.isArray(slots) ? slots : [];

  const ads: Ad[] = useMemo(() => {
    let list = Array.isArray(adsData) ? adsData : [];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(a => a.title?.toLowerCase().includes(q) || a.slot_id?.includes(q));
    }
    return list;
  }, [adsData, search]);

  const totalStats = useMemo(() => {
    const total = ads.length;
    const active = ads.filter(a => a.status === 'active').length;
    const imp = slotList.reduce((s, sl) => s + (sl.stats?.total_impressions || 0), 0);
    const clicks = slotList.reduce((s, sl) => s + (sl.stats?.total_clicks || 0), 0);
    return {total, active, imp, clicks};
  }, [ads, slotList]);

  const loading = slotsLoading || adsLoading;

  return (
    <AdminShell title="广告管理">
      {/* ═══ Header actions ═══ */}
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索广告..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400"/>
          </div>
          <select value={filterSlot} onChange={e => setFilterSlot(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">所有广告位</option>
            {slotList.map(s => <option key={s.slot_id} value={s.slot_id}>{s.name}</option>)}
          </select>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors">
          <Plus className="w-4 h-4"/>创建广告
        </button>
      </div>

      {/* ═══ Stats ═══ */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <StatCard icon={Layout} label="广告总数" value={totalStats.total} color="text-blue-500"/>
        <StatCard icon={ToggleLeft} label="投放中" value={totalStats.active} color="text-green-500"/>
        <StatCard icon={Eye} label="总展示" value={totalStats.imp} color="text-purple-500"/>
        <StatCard icon={MousePointerClick} label="总点击" value={totalStats.clicks} color="text-orange-500"/>
      </div>

      {/* ═══ Ad slots overview ═══ */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
        {slotList.map(s => (
          <div key={s.slot_id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{s.name}</p>
            <p className="text-xs text-gray-400 mt-0.5">{s.width}×{s.height}</p>
            <div className="flex items-center gap-2 mt-3 text-xs text-gray-500 dark:text-gray-400">
              <span className="px-1.5 py-0.5 rounded bg-green-50 dark:bg-green-900/20 text-green-600 font-medium">{s.stats?.active_ads || 0} 个</span>
              <span>{fmtNum(s.stats?.total_impressions)} 展示</span>
            </div>
          </div>
        ))}
      </div>

      {/* ═══ Ads table ═══ */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center"><div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/></div>
        ) : ads.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            <Layout className="w-10 h-10 mx-auto mb-3 opacity-40"/>
            <p className="text-sm">{search || filterSlot ? '没有匹配的广告' : '暂无广告，点击上方按钮创建'}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th
                    className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left">标题
                  </th>
                  <th
                    className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden md:table-cell">广告位
                  </th>
                  <th
                    className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden lg:table-cell">类型
                  </th>
                  <th
                    className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left">状态
                  </th>
                  <th
                    className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden sm:table-cell">展示/点击
                  </th>
                  <th
                    className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden lg:table-cell">优先级
                  </th>
                  <th
                    className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-right">操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {ads.map((a) => (
                  <tr key={a.ad_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-5 py-4">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[200px]">{a.title}</p>
                      <p className="text-[10px] text-gray-400 mt-0.5">{(a.start_date || '').slice(0, 10)} ~ {(a.end_date || '').slice(0, 10)}</p>
                    </td>
                    <td
                      className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">{slotLabels[a.slot_id] || a.slot_id}</td>
                    <td
                      className="px-5 py-4 text-xs text-gray-500 dark:text-gray-400 hidden lg:table-cell">{typeLabel[a.ad_type] || a.ad_type}</td>
                    <td className="px-5 py-4">{statusBadge(a.status)}</td>
                    <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden sm:table-cell">
                      <span className="flex items-center gap-3">
                        <span className="flex items-center gap-1"><Eye className="w-3 h-3"/>{fmtNum(0)}</span>
                        <span className="flex items-center gap-1"><MousePointerClick className="w-3 h-3"/>{fmtNum(0)}</span>
                      </span>
                    </td>
                    <td className="px-5 py-4 hidden lg:table-cell">
                      <span className={`text-xs font-mono ${a.priority >= 8 ? 'text-green-600' : a.priority >= 5 ? 'text-yellow-600' : 'text-gray-400'}`}>{a.priority}</span>
                    </td>
                    <td className="px-5 py-4 text-right whitespace-nowrap">
                      {a.status === 'active' ? (
                        <button onClick={() => toggleMut.mutate({id: a.ad_id, action: 'pause'})} className="p-1.5 inline-block text-gray-400 hover:text-yellow-600" title="暂停">
                          <Pause className="w-4 h-4"/>
                        </button>
                      ) : a.status === 'paused' ? (
                        <button onClick={() => toggleMut.mutate({id: a.ad_id, action: 'activate'})} className="p-1.5 inline-block text-gray-400 hover:text-green-600" title="激活">
                          <Play className="w-4 h-4"/>
                        </button>
                      ) : null}
                      <button onClick={async () => {
                        if (await confirm({
                          message: '确定删除广告「' + a.title + '」？',
                          variant: 'danger'
                        })) delMut.mutate(a.ad_id);
                      }}
                        className="p-1.5 inline-block text-gray-400 hover:text-red-600" title="删除">
                        <Trash2 className="w-4 h-4"/>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ═══ Create modal ═══ */}
      <CreateAdModal open={showCreate} onClose={() => setShowCreate(false)} slots={slotList} onCreated={() => qc.invalidateQueries({queryKey: ['ads-list']})} />
    </AdminShell>
  );
}

export default function AdminAds() {
  return <AuthGuard><QueryProvider><AdsInner/></QueryProvider></AuthGuard>;
}
