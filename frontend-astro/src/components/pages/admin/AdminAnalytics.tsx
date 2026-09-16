'use client';

/**
 * 数据分析（真实数据版）
 *
 * 数据来源：/api/v2/dashboard/analytics/*（后端已全部改为真实聚合）
 *  - overview / article-views-trend / popular-articles / category-distribution
 *  - tag-distribution / user-activity / content-performance
 *  - traffic-sources / device-stats / search-keywords / audit-activity / media-stats
 *
 * 说明：PV / UV / 停留时长 / 跳出率 需要访问明细数据（Phase 2 的 page_views 采集），
 * 在没有明细时后端返回 0 并给出 has_traffic_detail=false，界面显示"待开启访问统计"，
 * 不再展示任何编造数字。
 */

import React, {useMemo, useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {StatCard} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {
  Activity,
  BarChart3,
  Download,
  Eye,
  FileText,
  Globe,
  HardDrive,
  Hash,
  Loader2,
  Monitor,
  PieChart,
  Search,
  Tag,
  TrendingUp,
  UserPlus,
  Users,
  Zap,
} from 'lucide-react';

/* ─── Helpers ─── */
const fmt = (n: number | string | undefined | null) => {
  if (n === null || n === undefined) return '—';
  if (typeof n === 'string') return n;
  return n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n / 1_000).toFixed(1)}K` : String(n);
};

const fmtBytes = (bytes: number | undefined | null) => {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = Number(bytes);
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
};

const DATE_RANGES = [
  {key: 7, label: '7天'},
  {key: 14, label: '14天'},
  {key: 30, label: '30天'},
  {key: 90, label: '90天'},
];

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

/* ─── 区块标题（编辑风） ─── */
const SectionTitle: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}> = ({icon: Icon, title, subtitle, action}) => (
  <div className="mb-4 flex items-start justify-between gap-3 border-b border-border pb-3">
    <div className="flex items-center gap-2.5">
      <Icon className="h-4 w-4 text-muted-foreground"/>
      <div>
        <h3 className="text-sm font-medium text-foreground">{title}</h3>
        {subtitle && <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">{subtitle}</p>}
      </div>
    </div>
    {action}
  </div>
);

const EmptyHint: React.FC<{ icon: React.ComponentType<{ className?: string }>; text: string; hint?: string }> =
  ({icon: Icon, text, hint}) => (
    <div className="py-10 text-center">
      <Icon className="mx-auto mb-2 h-8 w-8 text-muted-foreground/40"/>
      <p className="text-sm text-muted-foreground">{text}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground/70">{hint}</p>}
    </div>
  );

/* ─── 趋势图：发布 / 注册（真实），PV·UV（有明细时） ─── */
interface TrendPoint {
  date: string;
  articles: number;
  users: number;
  views: number;
  visitors: number;
}

const TrendChart: React.FC<{ data: TrendPoint[]; hasTrafficDetail: boolean }> = ({data, hasTrafficDetail}) => {
  if (!data?.length) {
    return <EmptyHint icon={BarChart3} text="暂无趋势数据"/>;
  }

  const showTraffic = hasTrafficDetail;
  const maxVal = Math.max(
    ...data.map((d) => Math.max(d.articles, d.users, showTraffic ? Math.max(d.views, d.visitors) : 0)),
    1,
  );

  const w = 700;
  const h = 200;
  const padding = {top: 10, right: 20, bottom: 30, left: 50};
  const chartW = w - padding.left - padding.right;
  const chartH = h - padding.top - padding.bottom;
  const barW = Math.max(3, chartW / data.length - 2);
  const getY = (val: number) => padding.top + chartH * (1 - val / maxVal);
  const xLabels = data.filter((_, i) => i % Math.max(1, Math.floor(data.length / 7)) === 0);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-auto w-full" preserveAspectRatio="xMidYMid meet">
      {[0, 0.25, 0.5, 0.75, 1].map((r, i) => (
        <g key={i}>
          <line x1={padding.left} y1={getY(maxVal * r)} x2={w - padding.right} y2={getY(maxVal * r)}
                stroke="currentColor" strokeWidth={0.5} className="text-border"/>
          <text x={padding.left - 8} y={getY(maxVal * r) + 4} textAnchor="end"
                className="fill-muted-foreground text-[9px]">
            {fmt(Math.round(maxVal * r))}
          </text>
        </g>
      ))}

      {data.map((d, i) => {
        const x = padding.left + i * (chartW / data.length);
        return (
          <g key={d.date}>
            <rect x={x} y={getY(d.articles)} width={barW * 0.45} height={getY(0) - getY(d.articles)}
                  fill={COLORS[0]} opacity={0.75} rx={1.5}/>
            <rect x={x + barW * 0.5} y={getY(d.users)} width={barW * 0.45} height={getY(0) - getY(d.users)}
                  fill={COLORS[1]} opacity={0.75} rx={1.5}/>
          </g>
        );
      })}

      {xLabels.map((d) => (
        <text key={d.date} x={padding.left + data.indexOf(d) * (chartW / data.length) + barW / 2} y={h - 8}
              textAnchor="middle" className="fill-muted-foreground text-[8px]">
          {d.date.slice(5)}
        </text>
      ))}

      <g transform={`translate(${w - padding.right - 150}, ${padding.top})`}>
        <rect x={0} y={0} width={10} height={10} rx={2} fill={COLORS[0]} opacity={0.75}/>
        <text x={14} y={9} className="fill-muted-foreground text-[9px]">发布文章</text>
        <rect x={74} y={0} width={10} height={10} rx={2} fill={COLORS[1]} opacity={0.75}/>
        <text x={88} y={9} className="fill-muted-foreground text-[9px]">注册用户</text>
      </g>
    </svg>
  );
};

/* ─── 横向占比条 ─── */
const HBar: React.FC<{
  items: { name: string; value: number; pct: number }[]; emptyText?: string;
  emptyHint?: string; icon?: React.ComponentType<{ className?: string }>
}> = ({
        items, emptyText = '暂无数据', emptyHint, icon = PieChart,
      }) => {
  if (!items.length) {
    return <EmptyHint icon={icon} text={emptyText} hint={emptyHint}/>;
  }
  return (
    <div className="space-y-3">
      {items.slice(0, 8).map((item, i) => (
        <div key={`${item.name}-${i}`}>
          <div className="mb-1.5 flex justify-between text-xs">
            <span className="truncate font-medium text-foreground">{item.name}</span>
            <span className="ml-2 shrink-0 text-muted-foreground">
              {fmt(item.value)} <span className="text-muted-foreground/70">({item.pct.toFixed(0)}%)</span>
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-sm bg-muted">
            <div className="h-full rounded-sm transition-all duration-700 ease-out"
                 style={{width: `${Math.min(item.pct, 100)}%`, backgroundColor: COLORS[i % COLORS.length]}}/>
          </div>
        </div>
      ))}
    </div>
  );
};

/* ─── 排行列表（热门文章 / 搜索热词 / 后台动作） ─── */
const RankList: React.FC<{
  items: { label: string; meta?: React.ReactNode; href?: string }[];
  empty: React.ReactNode;
}> = ({items, empty}) => {
  if (!items.length) return <>{empty}</>;
  return (
    <ol className="space-y-0.5">
      {items.map((item, i) => (
        <li key={`${item.label}-${i}`}
            className="-mx-2 flex items-center gap-3 rounded-sm border-b border-border/50 px-2 py-2.5 last:border-0 hover:bg-accent/40">
          <span
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-muted font-mono text-[11px] text-muted-foreground">
            {i + 1}
          </span>
          <div className="min-w-0 flex-1">
            {item.href ? (
              <a href={item.href} target="_blank" rel="noreferrer"
                 className="block truncate text-sm text-foreground transition-colors hover:text-primary">
                {item.label}
              </a>
            ) : (
              <p className="truncate text-sm text-foreground">{item.label}</p>
            )}
            {item.meta && <div
              className="mt-0.5 flex items-center gap-3 font-mono text-[11px] text-muted-foreground">{item.meta}</div>}
          </div>
        </li>
      ))}
    </ol>
  );
};

/* ─── 主组件 ─── */
function AnalyticsInner() {
  const [days, setDays] = useState(30);

  /** 统一取数：失败时回落到默认值（不让单个端点异常拖垮整页） */
  const fetchData = async (path: string, params: Record<string, unknown>, fallback: any) => {
    try {
      const res: any = await apiClient.get(path, params);
      if (res?.success) {
        return res.data !== undefined ? res.data : fallback;
      }
      return fallback;
    } catch {
      return fallback;
    }
  };

  // 全部 useQuery 均在组件顶层调用（满足 Hooks 规则）
  const {data: overview, isLoading: overviewLoading} = useQuery<any>({
    queryKey: ['analytics-overview', days],
    queryFn: () => fetchData('/dashboard/analytics/overview', {days}, {}),
  });
  const {data: trend, isLoading: trendLoading} = useQuery<TrendPoint[]>({
    queryKey: ['analytics-trend', days],
    queryFn: () => fetchData('/dashboard/analytics/article-views-trend', {days}, []),
  });
  const {data: popular} = useQuery<any[]>({
    queryKey: ['analytics-popular', days],
    queryFn: () => fetchData('/dashboard/analytics/popular-articles', {limit: 10, days}, []),
  });
  const {data: categories} = useQuery<any[]>({
    queryKey: ['analytics-categories'],
    queryFn: () => fetchData('/dashboard/analytics/category-distribution', {}, []),
  });
  const {data: tags} = useQuery<any[]>({
    queryKey: ['analytics-tags'],
    queryFn: () => fetchData('/dashboard/analytics/tag-distribution', {limit: 15}, []),
  });
  const {data: activity} = useQuery<any>({
    queryKey: ['analytics-activity', days],
    queryFn: () => fetchData('/dashboard/analytics/user-activity', {days}, {}),
  });
  const {data: performance} = useQuery<any>({
    queryKey: ['analytics-performance', days],
    queryFn: () => fetchData('/dashboard/analytics/content-performance', {days}, {}),
  });
  const {data: traffic} = useQuery<any[]>({
    queryKey: ['analytics-traffic', days],
    queryFn: () => fetchData('/dashboard/analytics/traffic-sources', {days}, []),
  });
  const {data: devices} = useQuery<any[]>({
    queryKey: ['analytics-devices', days],
    queryFn: () => fetchData('/dashboard/analytics/device-stats', {days}, []),
  });
  const {data: keywords} = useQuery<any[]>({
    queryKey: ['analytics-keywords', days],
    queryFn: () => fetchData('/dashboard/analytics/search-keywords', {limit: 10, days}, []),
  });
  const {data: audit} = useQuery<any>({
    queryKey: ['analytics-audit', days],
    queryFn: () => fetchData('/dashboard/analytics/audit-activity', {days}, {top_actions: [], total: 0}),
  });
  const {data: media} = useQuery<any>({
    queryKey: ['analytics-media'],
    queryFn: () => fetchData('/dashboard/analytics/media-stats', {}, {count: 0, bytes: 0, by_type: []}),
  });

  const toItems = (rows: any[] | undefined, nameKeys: string[], valueKeys: string[]) => {
    if (!Array.isArray(rows)) return [];
    const total = rows.reduce((sum, row) => sum + (row[valueKeys[1]] ?? row[valueKeys[0]] ?? 0), 0) || 1;
    return rows.map((row) => {
      const name = nameKeys.map((k) => row[k]).find((v) => v !== undefined && v !== null) ?? '未知';
      const value = row[valueKeys[1]] ?? row[valueKeys[0]] ?? 0;
      return {name: String(name), value, pct: (value / total) * 100};
    });
  };

  const catItems = useMemo(() => toItems(categories as any[], ['name'], ['value', 'count']), [categories]);
  const tagItems = useMemo(() => toItems(tags as any[], ['name'], ['value', 'count']), [tags]);
  const trafficItems = useMemo(() => toItems(traffic as any[], ['name', 'source'], ['value', 'count']), [traffic]);
  const deviceItems = useMemo(() => toItems(devices as any[], ['name', 'device'], ['value', 'count']), [devices]);
  const mediaItems = useMemo(() => toItems(media?.by_type as any[], ['name'], ['value', 'count']), [media]);

  const trendData: TrendPoint[] = Array.isArray(trend) ? trend : [];
  const hasTrafficDetail = Boolean(overview?.has_traffic_detail);

  const exportData = () => {
    if (!trendData.length) return;
    const csv = [
      ['日期', '发布文章', '注册用户'].join(','),
      ...trendData.map((d) => [d.date, d.articles, d.users].join(',')),
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
        <div className="flex items-center rounded-md border border-border bg-card p-0.5">
          {DATE_RANGES.map((range) => (
            <button key={range.key} onClick={() => setDays(range.key)}
                    className={`rounded-sm px-3 py-1.5 text-xs transition-colors ${
                      days === range.key ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground'
                    }`}>
              {range.label}
            </button>
          ))}
        </div>
        <button onClick={exportData} disabled={!trendData.length}
                title="导出趋势数据（CSV）"
                className="rounded-md border border-border p-2 text-muted-foreground transition-colors hover:text-foreground disabled:opacity-40">
          <Download className="h-4 w-4"/>
        </button>
      </div>
    }>
      {/* ═══ 真实指标卡片（无编造值） ═══ */}
      {isLoading ? (
        <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
          {Array.from({length: 6}).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-lg border border-border bg-card"/>
          ))}
        </div>
      ) : (
        <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
          <StatCard icon={Eye} label="总浏览量" value={fmt(overview?.total_views)}
                    gradient="from-blue-500 to-blue-600"/>
          <StatCard icon={FileText} label="文章总数" value={fmt(overview?.total_articles)}
                    gradient="from-purple-500 to-violet-600"/>
          <StatCard icon={TrendingUp} label="已发布" value={fmt(overview?.published_articles)}
                    gradient="from-emerald-500 to-teal-600"/>
          <StatCard icon={Users} label="用户总数" value={fmt(overview?.total_users)}
                    gradient="from-teal-500 to-cyan-600"/>
          <StatCard icon={UserPlus} label={`新增用户 · ${days}天`} value={fmt(overview?.new_users)}
                    gradient="from-amber-500 to-orange-600"/>
          <StatCard icon={HardDrive} label="媒体占用" value={fmtBytes(overview?.media_bytes)}
                    gradient="from-gray-500 to-gray-700"/>
        </div>
      )}

      {/* ═══ 趋势 + 用户活跃 ═══ */}
      <div className="mb-6 grid gap-6 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 lg:col-span-2">
          <SectionTitle icon={TrendingUp} title={`${days} 天趋势`} subtitle="发布文章 / 注册用户（真实数据）"/>
          {trendLoading ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground"/>
            </div>
          ) : (
            <TrendChart data={trendData} hasTrafficDetail={hasTrafficDetail}/>
          )}
          {!hasTrafficDetail && (
            <p className="mt-3 border-t border-border pt-3 text-xs text-muted-foreground">
              浏览量 / 独立访客趋势需要访问明细采集（尚未开启），开启后将自动显示在图中。
            </p>
          )}
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={Activity} title="用户活跃度" subtitle={`近 ${days} 天`}/>
          <div className="divide-y divide-border/60">
            {[
              {label: '活跃作者', value: activity?.active_authors, icon: Users},
              {label: '活跃用户（登录）', value: activity?.active_users, icon: Activity},
              {label: '回访用户', value: activity?.returning_users, icon: UserPlus},
              {label: '新增文章', value: overview?.new_articles, icon: FileText},
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3 py-3">
                <item.icon className="h-4 w-4 shrink-0 text-muted-foreground"/>
                <span className="flex-1 text-xs text-muted-foreground">{item.label}</span>
                <span className="editorial-title text-lg text-foreground">{fmt(item.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ═══ 内容表现 + 媒体统计 ═══ */}
      <div className="mb-6 grid gap-6 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 lg:col-span-2">
          <SectionTitle icon={BarChart3} title="内容表现" subtitle="来自文章表与正文表的真实统计"/>
          <dl className="grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-3">
            {[
              {label: '平均浏览 / 篇', value: performance?.avg_views_per_article},
              {label: '最高浏览', value: performance?.max_views},
              {label: '零浏览文章', value: performance?.zero_view_articles},
              {label: '平均正文字数', value: performance?.avg_content_length},
              {label: '最长正文', value: performance?.max_content_length},
              {label: '窗口内新发布', value: performance?.published_in_period},
            ].map((item) => (
              <div key={item.label} className="border-b border-border/60 pb-2">
                <dt className="kicker">{item.label}</dt>
                <dd className="editorial-title mt-1.5 text-xl text-foreground">{fmt(item.value)}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={HardDrive} title="媒体统计"
                        subtitle={`${fmt(media?.count)} 个文件 · ${fmtBytes(media?.bytes)}`}/>
          <HBar items={mediaItems} icon={HardDrive} emptyText="暂无媒体文件"/>
        </div>
      </div>

      {/* ═══ 热门文章 + 分类分布 ═══ */}
      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={Zap} title="热门文章" subtitle="按累计浏览量（真实值）Top 10"/>
          <RankList
            items={(Array.isArray(popular) ? popular : []).map((a: any) => ({
              label: a.title || '无标题',
              href: a.slug ? `/blog/detail?slug=${encodeURIComponent(a.slug)}` : undefined,
              meta: (
                <>
                  <span className="flex items-center gap-1"><Eye className="h-3 w-3"/>{fmt(a.views)}</span>
                  {a.category_name && <span>{a.category_name}</span>}
                  {a.created_within_period && <span>近 {days} 天新增</span>}
                </>
              ),
            }))}
            empty={<EmptyHint icon={Zap} text="暂无浏览记录" hint="文章被访问后（浏览量 > 0）会出现在这里"/>}
          />
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={PieChart} title="分类分布" subtitle="文章数量占比"/>
          <HBar items={catItems} emptyText="暂无分类数据"/>
        </div>
      </div>

      {/* ═══ 标签分布 + 搜索热词 ═══ */}
      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={Tag} title="标签分布" subtitle="已发布文章的标签 Top 15"/>
          <HBar items={tagItems} icon={Hash} emptyText="暂无标签数据"
                emptyHint="文章的标签会在这里汇总统计"/>
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={Search} title="搜索热词" subtitle={`近 ${days} 天站内搜索`}/>
          <RankList
            items={(Array.isArray(keywords) ? keywords : []).map((k: any) => ({
              label: k.name,
              href: `/search?q=${encodeURIComponent(k.name)}`,
              meta: <span>{fmt(k.value)} 次</span>,
            }))}
            empty={<EmptyHint icon={Search} text="暂无搜索记录" hint="用户使用站内搜索后会产生统计"/>}
          />
        </div>
      </div>

      {/* ═══ 登录地区 + 设备分布 ═══ */}
      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={Globe} title="登录地区" subtitle={`近 ${days} 天登录会话（按会话地区）`}/>
          <HBar items={trafficItems} icon={Globe} emptyText="暂无会话数据"
                emptyHint="用户登录后其会话地区会在这里汇总；referrer 来源统计将在访问明细采集上线后提供"/>
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={Monitor} title="设备分布" subtitle={`近 ${days} 天登录会话（按 UA 归类）`}/>
          <HBar items={deviceItems} icon={Monitor} emptyText="暂无设备数据"
                emptyHint="移动端 / 桌面端 / 平板 由会话的 device_info 解析而来"/>
        </div>
      </div>

      {/* ═══ 后台操作活跃度 ═══ */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={Activity} title="后台操作" subtitle={`近 ${days} 天 · 共 ${fmt(audit?.total)} 次记录`}/>
          <RankList
            items={(audit?.top_actions || []).map((a: any) => ({
              label: a.name,
              meta: <span>{fmt(a.value)} 次</span>,
            }))}
            empty={<EmptyHint icon={Activity} text="暂无审计日志" hint="后台的管理操作会记录在 audit_logs"/>}
          />
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <SectionTitle icon={Users} title="账号概况" subtitle="来自用户表"/>
          <dl className="grid grid-cols-2 gap-x-8 gap-y-4">
            {[
              {label: '用户总数', value: overview?.total_users},
              {label: '管理 / 员工', value: overview?.staff_users},
              {label: `近 ${days} 天活跃`, value: overview?.active_users},
              {label: '草稿数', value: overview?.draft_articles},
              {label: '隐藏文章', value: overview?.hidden_articles},
              {label: `近 ${days} 天搜索`, value: overview?.searches},
            ].map((item) => (
              <div key={item.label} className="border-b border-border/60 pb-2">
                <dt className="kicker">{item.label}</dt>
                <dd className="editorial-title mt-1.5 text-xl text-foreground">{fmt(item.value)}</dd>
              </div>
            ))}
          </dl>
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
