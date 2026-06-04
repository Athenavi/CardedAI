'use client';

import {useState} from 'react';
import {useMutation, useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {BookOpen, Check, Clock, Download, ExternalLink, FileText, Globe, Loader, Shield, X,} from 'lucide-react';

// ─── Region tab config ────────────────────────────────
const REGIONS: {key: string; label: string; checkEndpoint: string}[] = [
  {key: 'eu', label: 'GDPR (欧盟)', checkEndpoint: '/compliance/gdpr/check'},
  {key: 'california', label: 'CCPA (加州)', checkEndpoint: '/compliance/ccpa/check'},
  {key: 'china', label: 'PIPL (中国)', checkEndpoint: '/compliance/china/check'},
];

// ─── Main ─────────────────────────────────────────────
function GDPRInner() {
  const [activeRegion, setActiveRegion] = useState('eu');

  // ── Compliance checks by region ──
  const {data: gdprCheck} = useQuery({
    queryKey: ['gdpr-check', 'eu'],
    queryFn: async () => {
      const r = await apiClient.get('/compliance/gdpr/check');
      return r.success && r.data ? r.data : {};
    },
  });
  const {data: ccpaCheck} = useQuery({
    queryKey: ['gdpr-check', 'california'],
    queryFn: async () => {
      const r = await apiClient.get('/compliance/ccpa/check');
      return r.success && r.data ? r.data : {};
    },
  });
  const {data: chinaCheck} = useQuery({
    queryKey: ['gdpr-check', 'china'],
    queryFn: async () => {
      const r = await apiClient.get('/compliance/china/check');
      return r.success && r.data ? r.data : {};
    },
  });
  const regionCheck: Record<string, any> = {eu: gdprCheck, california: ccpaCheck, china: chinaCheck};

  // ── Checklist for selected region ──
  const {data: checklistData} = useQuery({
    queryKey: ['gdpr-checklist', activeRegion],
    queryFn: async () => {
      const r = await apiClient.get(`/compliance/checklist/${activeRegion}`);
      return r.success && r.data ? r.data : {};
    },
  });

  // ── Overview ──
  const {data: overview} = useQuery({
    queryKey: ['gdpr-overview'],
    queryFn: async () => {
      const r = await apiClient.get('/compliance/overview');
      return r.success && r.data ? r.data : {};
    },
  });

  // ── Data retention ──
  const {data: retentionData} = useQuery({
    queryKey: ['gdpr-retention'],
    queryFn: async () => {
      const r = await apiClient.get('/compliance/data-retention');
      return r.success && r.data ? r.data : {};
    },
  });

  // ── Privacy policy generator ──
  const [showPolicy, setShowPolicy] = useState(false);
  const [companyName, setCompanyName] = useState('');
  const [companyEmail, setCompanyEmail] = useState('');
  const [companyAddress, setCompanyAddress] = useState('');
  const [policyHtml, setPolicyHtml] = useState('');
  const policyMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/compliance/privacy-policy/generate', data),
    onSuccess: (r) => {
      if (r.success && r.data?.template) setPolicyHtml(r.data.template);
      else setPolicyHtml('生成失败');
    },
  });

  // ── Checklist processing ──
  const checklist = Array.isArray(checklistData?.items) ? checklistData.items
    : (Array.isArray(checklistData) ? checklistData : []);

  // ── Retention ──
  const retentionCats = Array.isArray(retentionData?.categories) ? retentionData.categories
    : (Array.isArray(retentionData) ? retentionData : []);

  // ── Regulations list ──
  const regulations = Array.isArray(overview?.regulations) ? overview.regulations : [];

  // ── Best practices ──
  const bestPractices = Array.isArray(overview?.best_practices) ? overview.best_practices : [];

  const currentCheck = regionCheck[activeRegion];

  return (
    <AdminShell title="GDPR 合规">
      {/* ═══ 1. Region tabs ═══ */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {REGIONS.map(r => (
          <button key={r.key} onClick={() => setActiveRegion(r.key)}
            className={`px-4 py-2 text-sm rounded-xl font-medium transition-colors
              ${activeRegion === r.key
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'}`}>
            {r.label}
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        {/* ═══ 2. Current check result ═══ */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5"/>{REGIONS.find(r => r.key === activeRegion)?.label} 合规检查
          </h3>
          {currentCheck && Object.keys(currentCheck).length > 0 ? (
            <div className="space-y-3">
              {/* Score / Status */}
              {currentCheck.score !== undefined && (
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl font-black">{currentCheck.score}%</span>
                  <span className={`px-3 py-1 text-sm rounded-full font-medium
                    ${currentCheck.score >= 80 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                    currentCheck.score >= 50 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                      'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'}`}>
                    {currentCheck.score >= 80 ? '良好' : currentCheck.score >= 50 ? '需改进' : '不合规'}
                  </span>
                </div>
              )}
              {/* Items */}
              {Array.isArray(currentCheck.items) && currentCheck.items.map((item: any, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 border border-gray-100 dark:border-gray-800 rounded-xl">
                  {item.passed || item.compliant ? (
                    <Check className="w-5 h-5 text-green-500 shrink-0 mt-0.5"/>
                  ) : (
                    <X className="w-5 h-5 text-red-500 shrink-0 mt-0.5"/>
                  )}
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{item.name || item.requirement || item.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{item.description || item.detail || ''}</p>
                    {!item.passed && item.recommendation && (
                      <p className="text-xs text-yellow-600 mt-1">{item.recommendation}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-8">加载中...</p>
          )}
        </div>

        {/* ═══ 3. Checklist sidebar ═══ */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5"/>实施检查表
          </h3>
          {checklist.length > 0 ? (
            <div className="space-y-2">
              {checklist.map((item: any, i: number) => (
                <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <input type="checkbox" defaultChecked={item.completed || item.done}
                    className="mt-0.5 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"/>
                  <div>
                    <p className="text-xs text-gray-700 dark:text-gray-300">{item.name || item.task || item.action}</p>
                    {item.priority && (
                      <span className={`text-[10px] font-medium
                        ${item.priority === 'high' ? 'text-red-500' :
                          item.priority === 'medium' ? 'text-yellow-500' : 'text-green-500'}`}>
                        {item.priority === 'high' ? '高优先级' : item.priority === 'medium' ? '中优先级' : '低优先级'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-6">暂无检查表</p>
          )}
        </div>
      </div>

      {/* ═══ 4. Regulations Overview ═══ */}
      {regulations.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5"/>数据隐私法规概览
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {regulations.map((reg: any, i: number) => (
              <div key={i} className="border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                <p className="text-sm font-medium text-gray-900 dark:text-white">{reg.name}</p>
                <p className="text-xs text-gray-400 mb-2">{reg.full_name}</p>
                <div className="space-y-1 text-xs text-gray-500 dark:text-gray-400">
                  <p><span className="text-gray-400">区域:</span> {reg.region}</p>
                  <p><span className="text-gray-400">生效:</span> {reg.effective_date}</p>
                  {reg.key_rights && (
                    <div className="mt-2">
                      <p className="text-gray-400 mb-1">主要权利:</p>
                      <div className="flex flex-wrap gap-1">
                        {reg.key_rights.slice(0, 3).map((r: string, j: number) => (
                          <span key={j} className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 rounded text-[10px]">{r}</span>
                        ))}
                        {reg.key_rights.length > 3 && <span className="text-[10px] text-gray-400">+{reg.key_rights.length - 3}</span>}
                      </div>
                    </div>
                  )}
                  <p className="mt-2"><span className="text-gray-400">最高罚款:</span> {reg.max_penalty}</p>
                </div>
                {reg.documentation_url && (
                  <a href={reg.documentation_url} target="_blank" rel="noopener noreferrer"
                    className="mt-2 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline">
                    文档<ExternalLink className="w-3 h-3"/>
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ 5. Best Practices ═══ */}
      {bestPractices.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Check className="w-5 h-5"/>合规最佳实践
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {bestPractices.map((p: string, i: number) => (
              <div key={i} className="flex items-start gap-2 p-3 border border-gray-100 dark:border-gray-800 rounded-xl">
                <Check className="w-4 h-4 text-green-500 shrink-0 mt-0.5"/>
                <span className="text-sm text-gray-700 dark:text-gray-300">{p}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ 6. Data Retention ═══ */}
      {retentionCats.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5"/>数据保留建议
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">数据类型
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">建议保留期
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden sm:table-cell">法律依据
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {retentionCats.map((cat: any, i: number) => (
                  <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3 text-gray-900 dark:text-white">{cat.name || cat.type || cat.category}</td>
                    <td
                      className="px-4 py-3 text-gray-500 dark:text-gray-400">{cat.retention || cat.period || cat.duration || '—'}</td>
                    <td className="px-4 py-3 text-gray-400 hidden sm:table-cell">{cat.basis || cat.legal_basis || cat.reason || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ═══ 7. Privacy Policy Generator ═══ */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5"/>隐私政策生成器
        </h3>
        {!showPolicy ? (
          <button onClick={() => setShowPolicy(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg inline-flex items-center gap-1.5">
            <FileText className="w-4 h-4"/>生成隐私政策
          </button>
        ) : (
          <div className="space-y-4">
            <div className="grid sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">公司名称</label>
                <input value={companyName} onChange={e => setCompanyName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">联系邮箱</label>
                <input value={companyEmail} onChange={e => setCompanyEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">公司地址</label>
                <input value={companyAddress} onChange={e => setCompanyAddress(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white" />
              </div>
            </div>
            <button onClick={() => policyMut.mutate({
              company_name: companyName || undefined,
              company_email: companyEmail || undefined,
              company_address: companyAddress || undefined,
            })}
              disabled={policyMut.isPending}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg inline-flex items-center gap-1.5 disabled:opacity-50">
              {policyMut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : <Download className="w-4 h-4"/>}
              生成
            </button>
            {policyHtml && (
              <div className="mt-4 p-4 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800/50">
                <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">{policyHtml}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </AdminShell>
  );
}

export default function AdminGDPR() {
  return <AuthGuard><QueryProvider><GDPRInner/></QueryProvider></AuthGuard>;
}
