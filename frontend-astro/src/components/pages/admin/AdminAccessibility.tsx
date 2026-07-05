'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { QueryProvider } from '@/components/QueryProvider';
import { AdminShell } from '@/components/admin/AdminShell';
import { apiClient } from '@/lib/api/base-client';
import { ToastProvider, useToast } from '@/components/ui/toast-provider';
import {
  Activity,
  BookOpen,
  Check,
  ExternalLink,
  Eye,
  Keyboard,
  Monitor,
  Sun,
  Wrench,
} from 'lucide-react';

// ─── WCAG color ───────────────────────────────────────
const WCAG_COLORS: Record<string, string> = {
  A: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
  AA: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  AAA: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
};

// ─── SVG Icons ────────────────────────────────────────
const ArrowRightIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M13 7l5 5m0 0l-5 5m5-5H6"
    />
  </svg>
);

const LoaderIcon = ({ className }: { className?: string }) => (
  <svg
    className={`animate-spin ${className || ''}`}
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
    />
  </svg>
);

const AlertIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

// ─── Loading skeleton ─────────────────────────────────
function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl" />
      ))}
    </div>
  );
}

// ─── AccessContent component ─────────────────────────────────────
function AccessContent() {
  const qc = useQueryClient();
  const { success, error: showError } = useToast();

  // ── User accessibility config ──
  const {
    data: userConfig,
    isLoading: configLoading,
    error: configError,
  } = useQuery({
    queryKey: ['admin-a11y-config'],
    queryFn: async () => {
      const r = await apiClient.get('/system/accessibility/config');
      if (!r.success) throw new Error(r.error || '获取配置失败');
      return r.data || {};
    },
    staleTime: 30_000,
  });

  const configMut = useMutation({
    mutationFn: (data: Record<string, any>) =>
      apiClient.post('/system/accessibility/config', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-a11y-config'] });
      success('配置已保存', '无障碍偏好设置已更新');
    },
    onError: (err: Error) => {
      showError('保存失败', err.message || '无法保存配置');
    },
  });

  // ── Apply accessibility config to DOM ──
  useEffect(() => {
    if (!userConfig) return;
    const root = document.documentElement;
    const cl = root.classList;

    // High contrast
    cl.toggle('a11y-high-contrast', !!userConfig.high_contrast_mode);

    // Reduce motion
    cl.toggle('a11y-reduce-motion', !!userConfig.reduce_motion);

    // Font size
    const sizes = ['small', 'medium', 'large', 'x-large'];
    sizes.forEach(s => cl.remove(`a11y-font-${s}`));
    if (userConfig.font_size && userConfig.font_size !== 'medium') {
      cl.add(`a11y-font-${userConfig.font_size}`);
    }

    // Focus visible
    cl.toggle('a11y-focus-visible', !!userConfig.focus_visible);

    // Skip links
    cl.toggle('a11y-skip-links', !!userConfig.skip_links);

    // Keyboard navigation
    cl.toggle('a11y-keyboard-nav', !!userConfig.keyboard_navigation);

    // Screen reader support
    cl.toggle('a11y-screen-reader', !!userConfig.screen_reader_support);
  }, [userConfig]);

  // ── WCAG Checklist ──
  const {
    data: checklistData,
    isLoading: checklistLoading,
    error: checklistError,
  } = useQuery({
    queryKey: ['admin-a11y-checklist'],
    queryFn: async () => {
      const r = await apiClient.get('/accessibility/audit/checklist');
      if (!r.success) throw new Error(r.error || '获取检查清单失败');
      return r.data || {};
    },
    staleTime: 300_000,
  });

  // ── Guidelines ──
  const { data: guidelinesData, isLoading: guidelinesLoading } = useQuery({
    queryKey: ['admin-a11y-guidelines'],
    queryFn: async () => {
      const r = await apiClient.get('/accessibility/audit/guidelines');
      if (!r.success) throw new Error(r.error || '获取指南失败');
      return r.data || {};
    },
    staleTime: 300_000,
  });

  // ── Tools ──
  const {
    data: toolsData,
    isLoading: toolsLoading,
    error: toolsError,
  } = useQuery({
    queryKey: ['admin-a11y-tools'],
    queryFn: async () => {
      const r = await apiClient.get('/accessibility/audit/tools');
      if (!r.success) throw new Error(r.error || '获取工具失败');
      return r.data || {};
    },
    staleTime: 300_000,
  });

  // ── Config toggles ──
  const toggleConfig = useCallback(
    (key: string, currentVal: boolean) => {
      configMut.mutate({ [key]: !currentVal });
    },
    [configMut]
  );

  const configToggles = useMemo(
    () => [
      {
        key: 'keyboard_navigation',
        label: '键盘导航',
        icon: Keyboard,
        desc: '启用 Tab 键导航所有交互元素',
      },
      {
        key: 'screen_reader_support',
        label: '屏幕阅读器支持',
        icon: Monitor,
        desc: '优化屏幕阅读器兼容性',
      },
      {
        key: 'high_contrast_mode',
        label: '高对比度模式',
        icon: Sun,
        desc: '提高文本和背景的对比度',
      },
      {
        key: 'reduce_motion',
        label: '减少动画',
        icon: Activity,
        desc: '关闭非必要的动画效果',
      },
      {
        key: 'focus_visible',
        label: '焦点轮廓',
        icon: Eye,
        desc: '显示可点击元素的焦点环',
      },
      {
        key: 'skip_links',
        label: '跳过链接',
        icon: ArrowRightIcon,
        desc: '提供跳过导航的快捷链接',
      },
    ],
    []
  );

  // ── Process WCAG checklist ──
  const checklist = useMemo(() => {
    if (!checklistData || typeof checklistData !== 'object' || Array.isArray(checklistData))
      return [];
    return Object.entries(checklistData)
      .filter(([k]) => k !== 'title')
      .map(([key, section]: [string, any]) => ({
        id: key,
        title: section.title || key,
        items: Array.isArray(section.items) ? section.items : [],
      }));
  }, [checklistData]);

  // ── Guidelines processing ──
  const guidelines = useMemo(() => {
    if (!guidelinesData) return [];
    if (Array.isArray(guidelinesData)) return guidelinesData;

    // Backend returns { principles: { perceivable: {name, description, guidelines: [...string]}, ... },
    //                    conformance_levels: { A: {name, description, requirement}, ... } }
    const result: {
      id: string;
      title: string;
      description: string;
      list?: string[];
      level?: string;
      requirement?: string;
    }[] = [];

    // Flatten principles
    const principles = (guidelinesData as any).principles;
    if (principles && typeof principles === 'object') {
      for (const [key, val] of Object.entries(principles) as [string, any][]) {
        if (val?.name) {
          result.push({
            id: key,
            title: val.name,
            description: val.description || '',
            list: Array.isArray(val.guidelines) ? val.guidelines : undefined,
          });
        }
      }
    }

    // Flatten conformance levels
    const levels = (guidelinesData as any).conformance_levels;
    if (levels && typeof levels === 'object') {
      for (const [key, val] of Object.entries(levels) as [string, any][]) {
        if (val?.name) {
          result.push({
            id: key,
            title: val.name,
            description: val.description || '',
            level: key,
            requirement: val.requirement || '',
          });
        }
      }
    }

    return result;
  }, [guidelinesData]);

  // ── Tools sections ──
  const toolSections = useMemo(() => {
    if (!toolsData || typeof toolsData !== 'object') return [];
    return Object.entries(toolsData)
      .filter(([k]) => k !== 'title')
      .map(([key, section]: [string, any]) => ({
        id: key,
        title: section.title || key,
        section,
      }));
  }, [toolsData]);

  return (
    <>
      {/* ═══ 1. User Preferences ═══ */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
          <Monitor className="w-5 h-5" />
          用户无障碍偏好
        </h3>
        <p className="text-xs text-gray-400 mb-4">
          自定义站点的无障碍设置，包括键盘导航、屏幕阅读器支持、高对比度模式和字体大小等
        </p>
        {configLoading ? (
          <LoadingSkeleton rows={3} />
        ) : configError ? (
          <div className="flex items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-600 dark:text-red-400 text-sm">
            <AlertIcon className="w-5 h-5 shrink-0" />
            加载配置失败，请刷新页面重试
          </div>
        ) : (
          <>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {configToggles.map(({ key, label, icon: Icon, desc }) => (
                <div
                  key={key}
                  className="flex items-center justify-between p-4 border border-gray-100 dark:border-gray-800 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                  onClick={() => toggleConfig(key, userConfig?.[key])}
                >
                  <div className="flex items-start gap-3">
                    <Icon
                      className={`w-5 h-5 mt-0.5 ${
                        userConfig?.[key] ? 'text-blue-500' : 'text-gray-300'
                      }`}
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {label}
                      </p>
                      <p className="text-xs text-gray-400">{desc}</p>
                    </div>
                  </div>
                  <div
                    className={`w-10 h-6 rounded-full transition-colors shrink-0 ${
                      userConfig?.[key]
                        ? 'bg-blue-600'
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 bg-white rounded-full shadow-sm mt-1 transition-transform ${
                        userConfig?.[key] ? 'translate-x-5' : 'translate-x-1'
                      }`}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-4">
              <div>
                <label className="text-sm text-gray-500 dark:text-gray-400">
                  字号
                </label>
                <select
                  value={userConfig?.font_size || 'medium'}
                  onChange={(e) => configMut.mutate({ font_size: e.target.value })}
                  disabled={configMut.isPending}
                  className="ml-2 px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 dark:text-white disabled:opacity-50"
                >
                  <option value="small">小</option>
                  <option value="medium">中</option>
                  <option value="large">大</option>
                  <option value="x-large">超大</option>
                </select>
              </div>
              {configMut.isPending && <LoaderIcon className="w-4 h-4 text-blue-500" />}
            </div>
          </>
        )}
      </div>

      {/* ═══ 2. WCAG Compliance Checklist ═══ */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
          <BookOpen className="w-5 h-5" />
          WCAG 合规检查清单
        </h3>
        <p className="text-xs text-gray-400 mb-4">
          按 WCAG 2.1 四个原则分类的可访问性检查项，帮助确保站点符合无障碍标准
        </p>
        {checklistLoading ? (
          <LoadingSkeleton rows={4} />
        ) : checklistError ? (
          <div className="flex items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-600 dark:text-red-400 text-sm">
            <AlertIcon className="w-5 h-5 shrink-0" />
            加载检查清单失败
          </div>
        ) : checklist.length > 0 ? (
          <div className="grid lg:grid-cols-2 gap-4">
            {checklist.map((section) => (
              <div
                key={section.id}
                className="border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden"
              >
                <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {section.title}
                  </p>
                </div>
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {section.items.map((item: any, i: number) => (
                    <div key={i} className="px-4 py-3 flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-700 dark:text-gray-300">
                          {item.task}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          WCAG {item.wcag_criterion || item.wcag || item.guideline || ''}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-3">
                        <span
                          className={`px-1.5 py-0.5 text-[10px] rounded font-medium ${
                            WCAG_COLORS[(item.level || '').toUpperCase()] ||
                            'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
                          }`}
                        >
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

      {/* ═══ 3. WCAG Guidelines ═══ */}
      {guidelinesLoading ? (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            WCAG 2.1 指南
          </h3>
          <LoadingSkeleton rows={3} />
        </div>
      ) : guidelines.length > 0 ? (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            WCAG 2.1 指南
          </h3>
          <div className="space-y-3">
            {guidelines.map((g: any, i: number) => (
              <div
                key={g.id || i}
                className="p-4 border border-gray-100 dark:border-gray-800 rounded-xl"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {g.title || g.name || `指南 ${i + 1}`}
                    </p>
                    {g.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {g.description}
                      </p>
                    )}
                    {g.list && g.list.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {g.list.map((item: string, j: number) => (
                          <li key={j} className="text-xs text-gray-400 flex items-start gap-1.5">
                            <span className="text-blue-400 mt-0.5 shrink-0">•</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    )}
                    {g.requirement && (
                      <p className="text-xs text-gray-400 mt-1 italic">
                        {g.requirement}
                      </p>
                    )}
                  </div>
                  {g.level && (
                    <span
                      className={`px-1.5 py-0.5 text-[10px] rounded font-medium shrink-0 ${
                        WCAG_COLORS[g.level?.toUpperCase()] ||
                        'bg-gray-100 dark:bg-gray-800 text-gray-500'
                      }`}
                    >
                      Level {g.level}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* ═══ 4. Tools ═══ */}
      {toolsLoading ? (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
            <Wrench className="w-5 h-5" />
            辅助工具
          </h3>
          <LoadingSkeleton rows={3} />
        </div>
      ) : toolsError ? (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
            <Wrench className="w-5 h-5" />
            辅助工具
          </h3>
          <p className="text-xs text-gray-400 mb-4">
            推荐的无障碍测试工具和屏幕阅读器，帮助验证站点可访问性
          </p>
          <div className="flex items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-600 dark:text-red-400 text-sm">
            <AlertIcon className="w-5 h-5 shrink-0" />
            加载工具数据失败
          </div>
        </div>
      ) : toolSections.length > 0 ? (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Wrench className="w-5 h-5" />
            辅助工具
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {toolSections.map((section) => (
              <div
                key={section.id}
                className="border border-gray-100 dark:border-gray-800 rounded-xl p-4"
              >
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                  {section.title}
                </p>
                <div className="space-y-2">
                  {section.section.tools?.map((tool: any, i: number) => (
                    <div key={i} className="text-sm">
                      <a
                        href={tool.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline inline-flex items-center gap-1"
                      >
                        {tool.name}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                      <p className="text-xs text-gray-400">{tool.description}</p>
                      {tool.platform && (
                        <span className="text-[10px] text-gray-400">{tool.platform}</span>
                      )}
                      {tool.integration && (
                        <p className="text-[10px] text-gray-500 mt-0.5">{tool.integration}</p>
                      )}
                    </div>
                  ))}
                  {section.section.methods?.map((m: string, i: number) => (
                    <div
                      key={`m${i}`}
                      className="text-xs text-gray-500 dark:text-gray-400 flex items-start gap-1.5"
                    >
                      <Check className="w-3 h-3 text-green-500 mt-0.5 shrink-0" />
                      {m}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}

export default function AdminAccessibility() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AccessInner />
      </QueryProvider>
    </AuthGuard>
  );
}

// ─── Main component ───────────────────────────────────────
function AccessInner() {
  return (
    <AdminShell title="无障碍">
      <AccessContent />
    </AdminShell>
  );
}
