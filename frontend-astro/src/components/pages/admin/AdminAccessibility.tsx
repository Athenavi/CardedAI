'use client';


import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Activity, BookOpen, Check, ExternalLink, Eye, Keyboard, Monitor, Sun, Wrench,} from 'lucide-react';

// ─── WCAG color ───────────────────────────────────────
const WCAG_COLORS: Record<string, string> = {
  A: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
  AA: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  AAA: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
};

// ─── Main ─────────────────────────────────────────────
function AccessInner() {
  const qc = useQueryClient();

  // ── User accessibility config ──
  const {data: userConfig} = useQuery({
    queryKey: ['admin-a11y-config'],
    queryFn: async () => {
      const r = await apiClient.get('/system/accessibility/config');
      return r.success && r.data ? r.data : {};
    },
  });
  const configMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/system/accessibility/config', data),
    onSuccess: () => qc.invalidateQueries({queryKey: ['admin-a11y-config']}),
  });

  // ── WCAG Checklist ──
  const {data: checklistData} = useQuery({
    queryKey: ['admin-a11y-checklist'],
    queryFn: async () => {
      const r = await apiClient.get('/accessibility/audit/checklist');
      return r.success && r.data ? r.data : {};
    },
  });

  // ── Guidelines ──
  const {data: guidelinesData} = useQuery({
    queryKey: ['admin-a11y-guidelines'],
    queryFn: async () => {
      const r = await apiClient.get('/accessibility/audit/guidelines');
      return r.success && r.data ? r.data : {};
    },
  });

  // ── Tools ──
  const {data: toolsData} = useQuery({
    queryKey: ['admin-a11y-tools'],
    queryFn: async () => {
      const r = await apiClient.get('/accessibility/audit/tools');
      return r.success && r.data ? r.data : {};
    },
  });

  // ── Config toggles ──
  const toggleConfig = (key: string, currentVal: boolean) => {
    configMut.mutate({[key]: !currentVal});
  };

  const configToggles = [
    {key:'keyboard_navigation', label:'键盘导航', icon: Keyboard, desc:'启用 Tab 键导航所有交互元素'},
    {key:'screen_reader_support', label:'屏幕阅读器支持', icon: Monitor, desc:'优化屏幕阅读器兼容性'},
    {key:'high_contrast_mode', label:'高对比度模式', icon: Sun, desc:'提高文本和背景的对比度'},
    {key:'reduce_motion', label:'减少动画', icon: Activity, desc:'关闭非必要的动画效果'},
    {key:'focus_visible', label:'焦点轮廓', icon: Eye, desc:'显示可点击元素的焦点环'},
    {key:'skip_links', label:'跳过链接', icon: ArrowRightIcon, desc:'提供跳过导航的快捷链接'},
  ];

  // ── Process WCAG checklist ──
  const checklist = checklistData && typeof checklistData === 'object' && !Array.isArray(checklistData)
    ? Object.entries(checklistData).filter(([k]) => k !== 'title').map(([key, section]: [string, any]) => ({
      id: key,
      title: section.title || key,
      items: Array.isArray(section.items) ? section.items : [],
    }))
    : [];

  // ── Guidelines ──
  const __guidelines = Array.isArray(guidelinesData) ? guidelinesData
    : (guidelinesData?.guidelines || []);

  // ── Tools sections ──
  const toolSections = toolsData && typeof toolsData === 'object'
    ? Object.entries(toolsData).filter(([k]) => k !== 'title').map(([key, section]: [string, any]) => ({
      id: key, title: section.title || key, section,
    }))
    : [];

  return (
    <AdminShell title="无障碍">
      {/* ═══ 1. User Preferences ═══ */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Monitor className="w-5 h-5"/>用户无障碍偏好
        </h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {configToggles.map(({key, label, icon: Icon, desc}) => (
            <div key={key}
              className="flex items-center justify-between p-4 border border-gray-100 dark:border-gray-800 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer"
              onClick={() => toggleConfig(key, userConfig?.[key])}>
              <div className="flex items-start gap-3">
                <Icon className={`w-5 h-5 mt-0.5 ${userConfig?.[key] ? 'text-blue-500' : 'text-gray-300'}`}/>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
                  <p className="text-xs text-gray-400">{desc}</p>
                </div>
              </div>
              <div className={`w-10 h-6 rounded-full transition-colors shrink-0 ${userConfig?.[key] ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'}`}>
                <div className={`w-4 h-4 bg-white rounded-full shadow-sm mt-1 transition-transform ${userConfig?.[key] ? 'translate-x-5' : 'translate-x-1'}`}/>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center gap-4">
          <div>
            <label className="text-sm text-gray-500 dark:text-gray-400">字号</label>
            <select value={userConfig?.font_size || 'medium'}
              onChange={e => configMut.mutate({font_size: e.target.value})}
              className="ml-2 px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 dark:text-white">
              <option value="small">小</option>
              <option value="medium">中</option>
              <option value="large">大</option>
              <option value="x-large">超大</option>
            </select>
          </div>
        </div>
      </div>

      {/* ═══ 2. WCAG Compliance Checklist ═══ */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5"/>WCAG 合规检查清单
        </h3>
        {checklist.length > 0 ? (
          <div className="grid lg:grid-cols-2 gap-4">
            {checklist.map(section => (
              <div key={section.id} className="border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden">
                <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{section.title}</p>
                </div>
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {section.items.map((item: any, i: number) => (
                    <div key={i} className="px-4 py-3 flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-700 dark:text-gray-300">{item.task}</p>
                        <p className="text-xs text-gray-400">WCAG {item.wcag_criterion || item.wcag || item.guideline || ''}</p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-3">
                        <span
                          className={`px-1.5 py-0.5 text-[10px] rounded font-medium ${WCAG_COLORS[item.level?.toUpperCase()] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                          {item.level || item.wcag_criterion || ''}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400 text-center py-6">暂无检查清单数据</p>
        )}
      </div>

      {/* ═══ 3. Tools ═══ */}
      {toolSections.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Wrench className="w-5 h-5"/>辅助工具
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {toolSections.map(section => (
              <div key={section.id} className="border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">{section.title}</p>
                <div className="space-y-2">
                  {section.section.tools?.map((tool: any, i: number) => (
                    <div key={i} className="text-sm">
                      <a href={tool.url} target="_blank" rel="noopener noreferrer"
                        className="text-blue-600 hover:underline inline-flex items-center gap-1">
                        {tool.name}<ExternalLink className="w-3 h-3"/>
                      </a>
                      <p className="text-xs text-gray-400">{tool.description}</p>
                      {tool.platform && <span className="text-[10px] text-gray-400">{tool.platform}</span>}
                    </div>
                  ))}
                  {section.section.methods?.map((m: string, i: number) => (
                    <div key={`m${i}`} className="text-xs text-gray-500 dark:text-gray-400 flex items-start gap-1.5">
                      <Check className="w-3 h-3 text-green-500 mt-0.5 shrink-0"/>{m}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </AdminShell>
  );
}

const ArrowRightIcon = ({className}:{className?:string}) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6"/>
  </svg>
);

export default function AdminAccessibility() {
  return <AuthGuard><QueryProvider><AccessInner/></QueryProvider></AuthGuard>;
}
