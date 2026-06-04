'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {
  Activity,
  AlertTriangle,
  BookOpen,
  Check,
  Cloud,
  Globe,
  Loader,
  RefreshCw,
  Server,
  Shield,
  X,
  Zap,
} from 'lucide-react';

// ─── Provider configure modal ─────────────────────────
const ProviderModal: React.FC<{
  open: boolean; onClose: () => void; provider: string; label: string;
  fields: {key: string; label: string; type?: string; required?: boolean}[];
  onConfigured: () => void;
}> = ({open, onClose, provider, label, fields, onConfigured}) => {
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const qc = useQueryClient();

  const mut = useMutation({
    mutationFn: (data: any) => apiClient.post(`/performance/cdn/configure/${provider}`, data),
    onSuccess: (r) => {
      if (r.success) { onConfigured(); onClose(); qc.invalidateQueries({queryKey:['admin-cdn-config']}); }
      else setError(r.error || '配置失败');
    },
    onError: () => setError('配置失败'),
  });

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md m-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="font-semibold text-gray-900 dark:text-white">配置 {label}</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5"/></button>
        </div>
        <form onSubmit={e => { e.preventDefault(); if (!values.domain?.trim()) { setError('请填写域名'); return; } setError(''); mut.mutate(values); }}
          className="p-6 space-y-4">
          {fields.map(f => (
            <div key={f.key}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{f.label}{f.required ? ' *' : ''}</label>
              {f.type === 'textarea' ? (
                <textarea value={values[f.key]||''} onChange={e => setValues(v=>({...v,[f.key]:e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" rows={3}/>
              ) : (
                <input type={f.type||'text'} value={values[f.key]||''} onChange={e => setValues(v=>({...v,[f.key]:e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
              )}
            </div>
          ))}
          {error && <p className="text-xs text-red-500 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/>{error}</p>}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm border rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800">取消</button>
            <button type="submit" disabled={mut.isPending}
              className="inline-flex items-center gap-1.5 px-5 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50">
              {mut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : <Check className="w-4 h-4"/>}
              配置
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Main ─────────────────────────────────────────────
function CDNInner() {
  const [provider, setProvider] = useState<{provider:string;label:string;fields:{key:string;label:string;type?:string;required?:boolean}[]}|null>(null);

  const {data: config} = useQuery({
    queryKey: ['admin-cdn-config'],
    queryFn: async () => {
      const r = await apiClient.get('/performance/cdn/config');
      return r.success && r.data ? r.data : {};
    },
  });
  const {data: cacheStrategies} = useQuery({
    queryKey: ['admin-cdn-strategies'],
    queryFn: async () => {
      const r = await apiClient.get('/performance/cdn/cache-strategies');
      return r.success && r.data ? r.data : {};
    },
  });
  const {data: bestPractices} = useQuery({
    queryKey: ['admin-cdn-practices'],
    queryFn: async () => {
      const r = await apiClient.get('/performance/cdn/best-practices');
      return r.success && r.data ? r.data : {};
    },
  });
  const __purgeMut = useMutation({
    mutationFn: () => apiClient.post('/performance/cdn/purge-cache'),
  });

  // Extract provider info from config
  const providers: string[] = config?.providers || (config?.provider ? [config.provider] : []);

  const providerFields: Record<string, {label:string;fields:{key:string;label:string;type?:string;required?:boolean}[]}> = {
    cloudflare: {
      label: 'Cloudflare',
      fields: [
        {key:'api_token', label:'API Token', required:true},
        {key:'zone_id', label:'Zone ID', required:true},
        {key:'domain', label:'域名', required:true},
        {key:'cache_ttl', label:'缓存 TTL（秒）', type:'number'},
      ],
    },
    'aws-cloudfront': {
      label: 'AWS CloudFront',
      fields: [
        {key:'access_key_id', label:'Access Key ID', required:true},
        {key:'secret_access_key', label:'Secret Access Key', required:true, type:'textarea'},
        {key:'distribution_id', label:'Distribution ID', required:true},
        {key:'domain', label:'域名'},
      ],
    },
    aliyun: {
      label: '阿里云 CDN',
      fields: [
        {key:'access_key_id', label:'AccessKey ID', required:true},
        {key:'access_key_secret', label:'AccessKey Secret', required:true, type:'textarea'},
        {key:'domain', label:'加速域名', required:true},
      ],
    },
    custom: {
      label: '自定义 CDN',
      fields: [
        {key:'name', label:'提供商名称', required:true},
        {key:'base_url', label:'CDN 基础 URL', required:true},
        {key:'api_endpoint', label:'API 端点'},
        {key:'api_key', label:'API 密钥'},
        {key:'cache_ttl', label:'缓存 TTL（秒）', type:'number'},
      ],
    },
  };

  return (
    <AdminShell title="CDN 管理">
      {/* ═══ Overview Cards ═══ */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Server
            className="w-4 h-4"/>提供商
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{providers.length > 0 ? providers.join(', ') : '未配置'}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Globe
            className="w-4 h-4"/>域名
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{config?.domain || '—'}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Shield
            className="w-4 h-4"/>HTTPS
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{config?.enable_ssl ? <Check className="w-6 h-6 text-green-500 inline"/> : '—'}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Zap
            className="w-4 h-4"/>压缩
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{config?.enable_brotli ? 'Brotli' : config?.enable_minification ? 'Gzip' : '—'}</p>
        </div>
      </div>

      {/* ═══ Provider config ═══ */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2"><Cloud className="w-5 h-5"/>CDN 提供商配置</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Object.entries(providerFields).map(([key, v]) => (
            <button key={key} onClick={() => setProvider({provider:key, label:v.label, fields:v.fields})}
              className={`p-4 rounded-xl border text-left transition-all hover:border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/10
                ${providers.some(p => p.toLowerCase().includes(key.replace('-',''))) ? 'border-green-300 bg-green-50 dark:bg-green-900/10' : 'border-gray-200 dark:border-gray-700'}`}>
              <p className="font-medium text-sm text-gray-900 dark:text-white">{v.label}</p>
              <p className="text-xs text-gray-400 mt-1">{providers.some(p => p.toLowerCase().includes(key.replace('-',''))) ? '已配置' : '未配置'}</p>
            </button>
          ))}
        </div>
      </div>

      {/* ═══ Cache Strategies ═══ */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2"><RefreshCw className="w-5 h-5"/>缓存策略</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {cacheStrategies && Object.entries(cacheStrategies).map(([key, v]: [string, any]) => (
            <div key={key} className="p-4 border border-gray-100 dark:border-gray-800 rounded-xl bg-gray-50 dark:bg-gray-800/50">
              <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">{v.description}</p>
              <p className="text-xs text-gray-400 mb-2">TTL: {v.ttl_human}</p>
              <div className="flex flex-wrap gap-1">
                {(v.files||[]).slice(0, 4).map((f: string, i: number) => (
                  <span key={i} className="px-1.5 py-0.5 text-[10px] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded font-mono">{f}</span>
                ))}
                {(v.files||[]).length > 4 && <span className="px-1.5 py-0.5 text-[10px] text-gray-400">+{v.files.length-4}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ═══ Best Practices ═══ */}
      {bestPractices?.sections && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2"><BookOpen className="w-5 h-5"/>{bestPractices.title}</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {bestPractices.sections.map((s: any, i: number) => (
              <div key={i} className="p-4 border border-gray-100 dark:border-gray-800 rounded-xl">
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-1.5">
                  {[Zap, Shield, Activity, Globe][i] ? React.createElement([Zap, Shield, Activity, Globe][i], {className:'w-4 h-4 text-blue-500'}) : null}
                  {s.title}
                </p>
                <ul className="space-y-1">
                  {s.practices.map((p: string, j: number) => (
                    <li key={j} className="text-xs text-gray-500 dark:text-gray-400 flex items-start gap-1.5">
                      <Check className="w-3 h-3 text-green-500 mt-0.5 shrink-0"/>{p}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ Provider modal ═══ */}
      <ProviderModal open={!!provider} onClose={() => setProvider(null)}
        provider={provider?.provider||''} label={provider?.label||''} fields={provider?.fields||[]}
        onConfigured={() => {}}/>
    </AdminShell>
  );
}

export default function AdminCDN() { return <AuthGuard><QueryProvider><CDNInner/></QueryProvider></AuthGuard>; }
