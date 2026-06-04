'use client';

import React, {useState, useMemo} from 'react';
import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {StatCard} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {
  TrendingUp,
  Eye,
  Users,
  FileText,
  MessageSquare,
  UserPlus,
  Clock,
  Globe,
  Monitor,
  Smartphone,
  Tablet,
  ChevronUp,
  ChevronDown,
  Activity,
  Zap,
  Download,
  RefreshCw,
  Calendar,
  BarChart3,
  PieChart,
  Loader2
} from 'lucide-react';

/* ─── Helpers ─── */
const fmt = (n: number | string | undefined | null) => {
  if (n === null || n === undefined) return '—';
  if (typeof n === 'string') return n;
  return n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n / 1_000).toFixed(1)}K` : String(n);
};

const pct = (n: number | undefined | null) => (n !== null && n !== undefined ? `${n}%` : '—');

const DATE_RANGES = [
  {key: 7, label: '7天'},
  {key: 14, label: '14天'},
  {key: 30, label: '30天'},
  {key: 90, label: '90天'},
];

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

/* ─── Section Title ─── */
const SectionTitle: React.FC<{
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  title: string;
  subtitle?: string;
  action?: React.ReactNode
}> = ({
                                                                                                             icon: Icon,
                                                                                                             title,
                                                                                                             subtitle,
                                                                                                             action
                                                                                                           }) => (
    <div className="flex items-center justify-between mb-5">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
          <Icon className="w-4 h-4 text-gray-500 dark:text-gray-400"/>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>
          {subtitle && <p className="text-[10px] text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
);

/* ─── Skeleton ─── */
const __CardSkeleton = () => (
    <div
        className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-gray-700"/>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"/>
      </div>
      <div className="space-y-3">
        {[1, 2, 3, 4].map(i => (
            <div key={i} className="flex items-center justify-between">
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"/>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16"/>
            </div>
        ))}
      </div>
    </div>
);

const StatsSkeleton = () => (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
      {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i}
               className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 animate-pulse">
            <div className="flex items-start justify-between mb-3">
              <div className="w-12 h-12 rounded-xl bg-gray-200 dark:bg-gray-700"/>
              <div className="w-14 h-6 bg-gray-200 dark:bg-gray-700 rounded-full"/>
            </div>
            <div className="h-7 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-1"/>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-20"/>
          </div>
      ))}
  </div>
);

/* ─── SVG Trend Chart ─── */
const TrendChart: React.FC<{data: {date: string; views: number; visitors: number}[]}> = ({data}) => {
  if (!data?.length) return (
      <div className="py-12 text-center">
        <BarChart3 className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3"/>
        <p className="text-sm text-gray-400">暂无趋势数据</p>
      </div>
  );

  const maxVal = Math.max(...data.map(d => Math.max(d.views, d.visitors)), 1);
  const w = 700;
  const h = 200;
  const padding = {top: 10, right: 20, bottom: 30, left: 50};
  const chartW = w - padding.left - padding.right;
  const chartH = h - padding.top - padding.bottom;
  const barW = Math.max(3, (chartW / data.length) - 2);

  const getX = (i: number) => padding.left + i * (chartW / data.length) + barW / 2;
  const getY = (val: number) => padding.top + chartH * (1 - val / maxVal);

  // Generate grid labels
  const gridLines = [0, 0.25, 0.5, 0.75, 1];
  const xLabels = data.filter((_, i) => i % Math.max(1, Math.floor(data.length / 7)) === 0);

  return (
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto" preserveAspectRatio="xMidYMid meet">
      {/* Grid lines */}
        {gridLines.map((r, i) => (
            <g key={i}>
              <line x1={padding.left} y1={getY(maxVal * r)} x2={w - padding.right} y2={getY(maxVal * r)}
                    stroke="currentColor" strokeWidth={0.5} className="text-gray-200 dark:text-gray-700"/>
              <text x={padding.left - 8} y={getY(maxVal * r) + 4} textAnchor="end"
                    className="text-[9px] fill-gray-400 dark:fill-gray-500">
                {fmt(Math.round(maxVal * r))}
              </text>
            </g>
        ))}

        {/* Bars */}
        {data.map((d, i) => {
          const x = padding.left + i * (chartW / data.length);
          return (
              <g key={i}>
                <rect x={x} y={getY(d.views)} width={barW * 0.45} height={getY(0) - getY(d.views)}
                      fill="#3b82f6" opacity={0.7} rx={1.5}/>
                <rect x={x + barW * 0.5} y={getY(d.visitors)} width={barW * 0.45} height={getY(0) - getY(d.visitors)}
                      fill="#10b981" opacity={0.7} rx={1.5}/>
              </g>
          );
        })}

      {/* X labels */}
        {xLabels.map((d, i) => {
        const idx = data.indexOf(d);
          return (
              <text key={i} x={getX(idx)} y={h - 8} textAnchor="middle"
                    className="text-[8px] fill-gray-400 dark:fill-gray-500">
                {d.date.slice(5)}
              </text>
          );
      })}

        {/* Legend */}
        <g transform={`translate(${w - padding.right - 120}, ${padding.top})`}>
          <rect x={0} y={0} width={10} height={10} rx={2} fill="#3b82f6" opacity={0.7}/>
          <text x={14} y={9} className="text-[9px] fill-gray-500">浏览量</text>
          <rect x={60} y={0} width={10} height={10} rx={2} fill="#10b981" opacity={0.7}/>
          <text x={74} y={9} className="text-[9px] fill-gray-500">访客</text>
        </g>
    </svg>
  );
};

/* ─── Horizontal Bar ─── */
const HBar: React.FC<{
  items: { name: string; value: number; pct: number }[];
  colors?: string[];
}> = ({items, colors = CHART_COLORS}) => (
    <div className="space-y-3">
    {items.slice(0, 8).map((item, i) => (
      <div key={i}>
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-gray-700 dark:text-gray-300 truncate font-medium">{item.name}</span>
          <span className="text-gray-500 dark:text-gray-400 shrink-0 ml-2">
            {fmt(item.value)} <span
            className="text-gray-400 dark:text-gray-500 dark:text-gray-400">({item.pct.toFixed(0)}%)</span>
          </span>
        </div>
        <div className="w-full h-2.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
          <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{width: `${Math.min(item.pct, 100)}%`, backgroundColor: colors[i % colors.length]}}
          />
        </div>
      </div>
    ))}
      {!items.length && (
          <div className="py-8 text-center">
            <PieChart className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2"/>
            <p className="text-sm text-gray-400">暂无数据</p>
          </div>
      )}
    </div>
);

/* ─── Device Card ─── */
const DeviceCard: React.FC<{
  items: {
    name: string;
    value: number;
    pct: number;
    icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>
  }[];
}> = ({items}) => (
    <div className="space-y-4">
      {items.map((d, i) => {
        const Icon = d.icon;
        return (
            <div key={i} className="flex items-center gap-4">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0`}
                   style={{backgroundColor: `${CHART_COLORS[i]}15`}}>
                <Icon className="w-5 h-5" style={{color: CHART_COLORS[i]}}/>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between text-sm mb-1.5">
                  <span className="text-gray-700 dark:text-gray-300 font-medium">{d.name}</span>
                  <span className="text-gray-500 dark:text-gray-400">{fmt(d.value)} <span
                      className="text-gray-400">({d.pct.toFixed(0)}%)</span></span>
                </div>
                <div className="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700 ease-out"
                       style={{width: `${d.pct}%`, backgroundColor: CHART_COLORS[i]}}/>
                </div>
              </div>
            </div>
        );
      })}
      {!items.length && (
          <div className="py-8 text-center">
            <Monitor className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2"/>
            <p className="text-sm text-gray-400">暂无设备数据</p>
          </div>
      )}
  </div>
);

/* ─── Main Component ─── */
function AnalyticsInner() {
  const [days, setDays] = useState(30);

  /* ─── Queries ─── */
  const {data: overview, isLoading: overviewLoading} = useQuery({
    queryKey: ['analytics-overview', days],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/analytics/overview', {days});
      return res.success && res.data ? res.data : {};
    },
  });

  const {data: trend, isLoading: trendLoading} = useQuery({
    queryKey: ['analytics-trend', days],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/analytics/article-views-trend', {days});
      return res.success && res.data ? res.data : [];
    },
  });

  const {data: popular, isLoading: popularLoading} = useQuery({
    queryKey: ['analytics-popular', days],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/analytics/popular-articles', {limit: 10, days});
      return res.success && res.data ? res.data : [];
    },
  });

  const {data: categories} = useQuery({
    queryKey: ['analytics-categories'],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/analytics/category-distribution');
      return res.success && res.data ? res.data : [];
    },
  });

  const {data: activity} = useQuery({
    queryKey: ['analytics-activity', days],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/analytics/user-activity', {days});
      return res.success && res.data ? res.data : {};
    },
  });

  const {data: trafficSources} = useQuery({
    queryKey: ['analytics-traffic', days],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/analytics/traffic-sources', {days});
      return res.success && res.data ? res.data : [];
    },
  });

  const {data: deviceStats} = useQuery({
    queryKey: ['analytics-devices', days],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/analytics/device-stats', {days});
      return res.success && res.data ? res.data : [];
    },
  });

  /* ─── Computed data ─── */
  const catItems = useMemo(() => {
    if (!Array.isArray(categories)) return [];
    const total = categories.reduce((s, c) => s + (c.value || c.count || 0), 0) || 1;
    return categories.map((c) => ({
      name: c.name || c.category_name || '未知',
      value: c.value || c.count || 0,
      pct: ((c.value || c.count || 0) / total) * 100,
    }));
  }, [categories]);

  const trafficItems = useMemo(() => {
    if (!Array.isArray(trafficSources)) return [];
    const total = trafficSources.reduce((s, t) => s + (t.count || t.visits || 0), 0) || 1;
    return trafficSources.map((t) => ({
      name: t.source || t.name || '未知',
      value: t.count || t.visits || 0,
      pct: ((t.count || t.visits || 0) / total) * 100,
    }));
  }, [trafficSources]);

  const deviceItems = useMemo(() => {
    if (!Array.isArray(deviceStats)) return [];
    const total = deviceStats.reduce((s, d) => s + (d.count || d.visits || 0), 0) || 1;
    return deviceStats.map((d) => ({
      name: d.device || d.device_type || '未知',
      value: d.count || d.visits || 0,
      pct: ((d.count || d.visits || 0) / total) * 100,
      icon: (d.device || '').toLowerCase().includes('mobile') || (d.device || '').toLowerCase().includes('phone') ? Smartphone
        : (d.device || '').toLowerCase().includes('tablet') ? Tablet : Monitor,
    }));
  }, [deviceStats]);

  const trendData = Array.isArray(trend) ? trend : [];

  /* ─── Export CSV ─── */
  const exportData = () => {
    if (!trendData?.length) return;
    const csv = [
      ['日期', '浏览量', '访客'].join(','),
      ...trendData.map((d) => [d.date, d.views, d.visitors].join(','))
    ].join('\n');
    const blob = new Blob(['\uFEFF' + csv], {type: 'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-${days}days-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const isLoading = overviewLoading || trendLoading;

  return (
      <AdminShell title="数据分析" actions={
        <div className="flex items-center gap-2">
          {/* Date range selector */}
          <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
            {DATE_RANGES.map(r => (
                <button
                    key={r.key}
                    onClick={() => setDays(r.key)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                        days === r.key
                            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                >
                  {r.label}
                </button>
            ))}
          </div>
          <button
              onClick={exportData}
              disabled={!trendData?.length}
              className="p-2.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors disabled:opacity-50"
              title="导出数据"
          >
            <Download className="w-4 h-4"/>
          </button>
        </div>
      }>

        {/* ═══ Stat Cards ═══ */}
        {isLoading ? <StatsSkeleton/> : (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
              <StatCard icon={Eye} label="总浏览量" value={fmt(overview?.total_views)}
                        gradient="from-blue-500 to-blue-600" change={overview?.views_change}/>
              <StatCard icon={Users} label="独立访客" value={fmt(overview?.unique_visitors)}
                        gradient="from-green-500 to-emerald-600" change={overview?.visitors_change}/>
              <StatCard icon={FileText} label="文章总数" value={fmt(overview?.total_articles)}
                        gradient="from-purple-500 to-violet-600" change={overview?.page_views_change}/>
              <StatCard icon={MessageSquare} label="评论总数" value={fmt(overview?.total_comments)}
                        gradient="from-orange-500 to-amber-600"/>
              <StatCard icon={UserPlus} label="新增用户" value={fmt(overview?.new_users || overview?.total_users)}
                        gradient="from-teal-500 to-cyan-600"/>
              <StatCard icon={Clock} label="跳出率" value={pct(overview?.bounce_rate)}
                        gradient="from-red-500 to-rose-600"/>
            </div>
        )}

        {/* ═══ Trend + Activity ═══ */}
      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        {/* Trend Chart */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <SectionTitle
              icon={TrendingUp}
              title={`${days}天浏览趋势`}
              subtitle="浏览量与访客数对比"
          />
          {trendLoading ? (
              <div className="h-48 flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-gray-300 animate-spin"/>
              </div>
          ) : (
              <TrendChart data={trendData}/>
          )}
        </div>

        {/* User Activity */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <SectionTitle icon={Activity} title="用户活跃度" subtitle={`近${days}天`}/>
          <div className="space-y-0">
            {[
              {label: '活跃作者', value: activity?.active_authors, icon: Users, color: 'from-blue-500 to-blue-600'},
              {
                label: '活跃评论者',
                value: activity?.active_commenters,
                icon: MessageSquare,
                color: 'from-green-500 to-emerald-600'
              },
              {
                label: '新增文章',
                value: overview?.new_articles,
                icon: FileText,
                color: 'from-purple-500 to-violet-600'
              },
              {
                label: '新注册用户',
                value: activity?.new_users || overview?.new_users,
                icon: UserPlus,
                color: 'from-orange-500 to-amber-600'
              },
            ].map((item, i) => (
                <div key={i}
                     className="flex items-center gap-3 py-3.5 border-b border-gray-100 dark:border-gray-800 last:border-0">
                  <div
                      className={`w-9 h-9 rounded-lg bg-gradient-to-br ${item.color} flex items-center justify-center flex-shrink-0`}>
                    <item.icon className="w-4 h-4 text-white"/>
                  </div>
                  <div className="flex-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400">{item.label}</span>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">{fmt(item.value)}</p>
                  </div>
                </div>
            ))}
          </div>
        </div>
      </div>

        {/* ═══ Popular Articles + Category Distribution ═══ */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Popular Articles */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <SectionTitle icon={Zap} title="热门文章" subtitle={`近${days}天 Top 10`}/>
          {popularLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map(i => (
                    <div key={i} className="flex items-center gap-3 py-2.5 animate-pulse">
                      <div className="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700"/>
                      <div className="flex-1 space-y-1.5">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"/>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"/>
                      </div>
                    </div>
                ))}
              </div>
          ) : Array.isArray(popular) && popular.length > 0 ? (
              <div className="space-y-0.5">
              {popular.map((a: any, i: number) => (
                  <div key={a.id || i}
                       className="flex items-center gap-3 py-2.5 border-b border-gray-50 dark:border-gray-800/50 last:border-0 group hover:bg-gray-50 dark:hover:bg-gray-800/30 -mx-2 px-2 rounded-lg transition-colors">
                  <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                      i === 0 ? 'bg-gradient-to-br from-yellow-400 to-amber-500 text-white' :
                          i === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-400 text-white dark:from-gray-600 dark:to-gray-700' :
                              i === 2 ? 'bg-gradient-to-br from-orange-400 to-orange-500 text-white' :
                                'bg-gray-100 text-gray-500 dark:text-gray-400 dark:bg-gray-800 dark:text-gray-400'
                  }`}>
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {a.title || '无标题'}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 dark:text-gray-400 flex items-center gap-2">
                      <span className="flex items-center gap-0.5"><Eye className="w-3 h-3"/>{fmt(a.views)}</span>
                      <span className="flex items-center gap-0.5"><MessageSquare className="w-3 h-3"/>{a.comments || 0}</span>
                    </p>
                  </div>
                  </div>
              ))}
              </div>
          ) : (
              <div className="py-12 text-center">
                <Zap className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2"/>
                <p className="text-sm text-gray-400">暂无热门文章数据</p>
            </div>
          )}
        </div>

        {/* Category Distribution */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <SectionTitle icon={PieChart} title="分类分布" subtitle="文章数量占比"/>
          <HBar items={catItems}/>
        </div>
      </div>

        {/* ═══ Traffic Sources + Device Distribution ═══ */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Traffic Sources */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <SectionTitle icon={Globe} title="流量来源" subtitle="访客来源渠道"/>
          <HBar items={trafficItems}
                colors={['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']}/>
        </div>

        {/* Device Distribution */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <SectionTitle icon={Monitor} title="设备分布" subtitle="终端设备统计"/>
          <DeviceCard items={deviceItems}/>
        </div>
      </div>
    </AdminShell>
  );
}

export default function AdminAnalytics() {
  return (
      <AuthGuard>
        <QueryProvider>
          <AnalyticsInner/>
        </QueryProvider>
      </AuthGuard>
  );
}
