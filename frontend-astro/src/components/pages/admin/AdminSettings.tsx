'use client';

import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {StatCard} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import AdminIntegrations from './AdminIntegrations';
import {getConfig} from '@/lib/config';
import {getFullMediaUrl} from '@/lib/utils';
import {type Locale, locales, useTranslation} from '@/lib/i18n';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Clock,
  Download,
  FileText,
  Film,
  Globe,
  Hash,
  Image,
  Layers,
  Layout,
  Loader,
  Monitor,
  Save,
  Search,
  Settings as SettingsIcon,
  Shield,
  Trash2,
  Type,
  Upload,
  X,
  XCircle
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────
interface Page {id: number; title: string; slug: string; content: string; excerpt: string; template: string; status: number; parent_id: number | null; order_index: number; meta_title?: string; meta_description?: string; meta_keywords?: string; created_at?: string;}

// ─── Tab configuration ────────────────────────────────
const TABS = [
  {
    key: 'basic',
    label: '基本设置',
    icon: SettingsIcon,
    desc: '站点基本信息配置',
    gradient: 'from-blue-500 to-cyan-500'
  },
  {key: 'system', label: '系统选项', icon: Shield, desc: '系统功能开关', gradient: 'from-emerald-500 to-teal-500'},
  {key: 'integrations', label: '第三方登录', icon: Globe, desc: 'OAuth 登录配置', gradient: 'from-indigo-500 to-purple-500'},
];

// ─── Settings field registry ──────────────────────────
interface FieldDef {
  key: string;
  label: string;
  type?: string;
  placeholder?: string;
  category: string;
  options?: { label: string; value: string }[];
  rows?: number;
  icon?: any;
  desc?: string;
}
const SETTINGS_FIELDS: FieldDef[] = [
  // basic
  {
    key: 'site_title',
    label: '站点标题',
    category: 'basic',
    placeholder: 'Carded AI',
    icon: Type,
    desc: '显示在浏览器标签和搜索引擎结果中'
  },
  {
    key: 'site_description',
    label: '站点描述',
    category: 'basic',
    type: 'textarea',
    rows: 2,
    placeholder: '一个快速的博客系统',
    icon: FileText,
    desc: '用于SEO和社交分享'
  },
  {
    key: 'site_domain',
    label: '站点域名',
    category: 'basic',
    placeholder: 'example.com',
    icon: Globe,
    desc: '当前站点的访问域名'
  },
  {
    key: 'site_img',
    label: '站点Logo URL',
    category: 'basic',
    placeholder: 'https://...',
    icon: Image,
    desc: '站点Logo图片地址'
  },
  {
    key: 'site_beian',
    label: '备案号',
    category: 'basic',
    placeholder: '京ICP备...',
    icon: Shield,
    desc: 'ICP备案号（如适用）'
  },
  {
    key: 'site_keywords',
    label: '站点关键词',
    category: 'basic',
    placeholder: '博客, 技术, ...',
    icon: Hash,
    desc: '用于SEO优化，逗号分隔'
  },
  // system
  {
    key: 'user_registration',
    label: '允许用户注册',
    category: 'system',
    type: 'select',
    options: [{label: '开启', value: 'true'}, {label: '关闭', value: 'false'}],
    icon: Shield,
    desc: '控制是否允许新用户注册'
  },
];

// ─── Section Title ────────────────────────────────────
const SectionTitle: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
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
      <div className="flex items-center gap-3">
        <div
            className="w-9 h-9 rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
          <Icon className="w-4.5 h-4.5 text-gray-600 dark:text-gray-300"/>
        </div>
        <div>
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
);

// ─── Skeleton loading ─────────────────────────────────
const SettingsSkeleton = () => (
    <div className="space-y-5 animate-pulse">
      {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-lg w-24"/>
            <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded-xl w-full"/>
          </div>
      ))}
    </div>
);


const PageSkeleton = () => (
    <div className="space-y-0 animate-pulse">
      {[1, 2, 3, 4].map(i => (
          <div key={i} className="flex items-center gap-4 px-5 py-4 border-b border-gray-100 dark:border-gray-800">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-lg w-32"/>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-lg w-24 hidden sm:block"/>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-lg w-16 hidden lg:block ml-auto"/>
          </div>
      ))}
    </div>
);

// ─── Image Upload Field ───────────────────────────────
const MediaField: React.FC<{ value: string; onChange: (v: string) => void; placeholder?: string }> = ({
                                                                                                        value,
                                                                                                        onChange,
                                                                                                        placeholder
                                                                                                      }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const isVideo = (url: string) => /\.(mp4|webm|ogg|mov|avi|mkv)(\?|$)/i.test(url);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const isImage = file.type.startsWith('image/');
    const isVideoFile = file.type.startsWith('video/');
    if (!isImage && !isVideoFile) {
      alert('请选择图片或视频文件');
      return;
    }
    const maxSize = isVideoFile ? 50 * 1024 * 1024 : 8 * 1024 * 1024;
    if (file.size > maxSize) {
      alert(isVideoFile ? '视频文件大小不能超过 50MB' : '图片文件大小不能超过 8MB');
      return;
    }
    setUploading(true);
    setUploadProgress(0);
    try {
      const formData = new FormData();
      formData.append('file', file);

      // 从 cookie 读取 JWT token（与 base-client 和 CoverImageUploader 一致）
      const accessToken = (() => {
        for (const c of document.cookie.split(';')) {
          const [n, v] = c.trim().split('=');
          if (n === 'access_token' && v) return decodeURIComponent(v);
        }
        return null;
      })();

      const xhr = new XMLHttpRequest();
      const result = await new Promise<{
        success?: boolean;
        data?: { url?: string; files?: { url: string }[] }
      }>((resolve, reject) => {
        const {API_BASE_URL} = getConfig();
        xhr.open('POST', `${API_BASE_URL}/api/v2/media/settings/upload`);
        xhr.withCredentials = true;
        if (accessToken) {
          xhr.setRequestHeader('Authorization', `Bearer ${accessToken}`);
        }
        xhr.upload.onprogress = (ev) => {
          if (ev.lengthComputable) setUploadProgress(Math.round((ev.loaded / ev.total) * 100));
        };
        xhr.onload = () => {
          if (xhr.status === 302 || xhr.status === 401 || xhr.status === 403) {
            reject(new Error('未登录或登录已过期，请重新登录'));
            return;
          }
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            const snippet = xhr.responseText?.slice(0, 120) || '(empty)';
            reject(new Error(`服务器返回非 JSON 响应 (HTTP ${xhr.status}): ${snippet}`));
          }
        };
        xhr.onerror = () => reject(new Error('网络错误，请检查网络连接'));
        xhr.send(formData);
      });
      const url = result?.data?.url || result?.data?.files?.[0]?.url;
      if (url) {
        onChange(url);
      } else {
        alert('上传成功但未获取到文件 URL');
      }
    } catch (err: any) {
      alert(err?.message || '上传失败');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const resolvedUrl = value ? getFullMediaUrl(value) : '';
  const isVideoMedia = value ? isVideo(value) : false;

  return (
    <div className="space-y-3">
      {/* Preview */}
      {value && (
        <div
          className="relative group rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 aspect-video max-h-48">
          {isVideoMedia ? (
            <video src={resolvedUrl} className="w-full h-full object-cover" controls muted onError={(e) => {
              (e.target as HTMLVideoElement).style.display = 'none';
            }}/>
          ) : (
            <img src={resolvedUrl} alt="预览" className="w-full h-full object-cover" onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}/>
          )}
          <div
            className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center">
            <button onClick={() => onChange('')}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                    title="移除媒体">
              <Trash2 className="w-4 h-4"/>
            </button>
          </div>
        </div>
      )}
      {/* Upload button + URL input */}
      <div className="flex gap-2">
        <input ref={fileInputRef} type="file" accept="image/*,video/*" onChange={handleFileSelect} className="hidden"/>
        <button type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading}
                className="flex-shrink-0 inline-flex items-center gap-1.5 px-3.5 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800/80 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all disabled:opacity-50">
          {uploading ? <Loader className="w-4 h-4 animate-spin"/> : <Upload className="w-4 h-4"/>}
          {uploading ? `${uploadProgress}%` : '上传媒体'}
        </button>
        <div className="relative flex-1">
          <Film className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"/>
          <input type="text" value={value} onChange={e => onChange(e.target.value)}
                 className="w-full px-4 py-2.5 pl-10 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800/80 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                 placeholder={placeholder || '输入媒体 URL'}/>
        </div>
      </div>
    </div>
  );
};

// ─── Enhanced Field Input ─────────────────────────────
const FieldInput: React.FC<{field: FieldDef; value: string; onChange: (v: string) => void}> = ({field, value, onChange}) => {
  const baseClass = "w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800/80 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 dark:focus:border-blue-500 transition-all duration-200";

  if (field.type === 'select' && field.options) {
    return (
        <div className="relative">
          <select value={value} onChange={e => onChange(e.target.value)}
                  className={`${baseClass} appearance-none pr-10 cursor-pointer`}>
            {field.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"/>
        </div>
    );
  }
  if (field.type === 'textarea') {
    return (
      <textarea value={value} onChange={e => onChange(e.target.value)} rows={field.rows||3}
                className={`${baseClass} resize-none`} placeholder={field.placeholder}/>
    );
  }
  if (field.type === 'image' || field.type === 'media') {
    return (
      <MediaField value={value} onChange={onChange} placeholder={field.placeholder}/>
    );
  }
  return (
      <div className="relative">
        {field.icon && (
            <field.icon
                className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"/>
        )}
        <input type={field.type || 'text'} value={value} onChange={e => onChange(e.target.value)}
               className={`${baseClass} ${field.icon ? 'pl-10' : ''}`} placeholder={field.placeholder}/>
      </div>
  );
};

// ─── Enhanced Modal ───────────────────────────────────
const Modal: React.FC<{
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  maxWidth?: string
}> = ({open, onClose, title, subtitle, children, maxWidth = 'max-w-lg'}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (open) {
      setIsVisible(true);
      requestAnimationFrame(() => setIsAnimating(true));
    } else {
      setIsAnimating(false);
      const timer = setTimeout(() => setIsVisible(false), 200);
      return () => clearTimeout(timer);
    }
  }, [open]);

  if (!isVisible) return null;
  return (
      <div
          className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-200 ${isAnimating ? 'bg-black/50 backdrop-blur-sm' : 'bg-black/0'}`}
          onClick={onClose}>
        <div
            className={`bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full ${maxWidth} max-h-[85vh] overflow-hidden transform transition-all duration-200 ${isAnimating ? 'scale-100 opacity-100 translate-y-0' : 'scale-95 opacity-0 translate-y-4'}`}
            onClick={e => e.stopPropagation()}>
          <div
              className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white text-base">{title}</h2>
              {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
            </div>
            <button onClick={onClose}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors">
              <X className="w-4.5 h-4.5"/>
            </button>
          </div>
          <div className="p-6 overflow-y-auto max-h-[calc(85vh-80px)]">{children}</div>
        </div>
      </div>
  );
};

// ─── Status Badge ─────────────────────────────────────
const StatusBadge: React.FC<{ active: boolean; label?: string }> = ({active, label}) => (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
        active
            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
          : 'bg-gray-100 text-gray-500 dark:text-gray-400 dark:bg-gray-800 dark:text-gray-400'
    }`}>
    <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`}/>
      {label || (active ? '激活' : '禁用')}
  </span>
);

// ─── Template Badge ───────────────────────────────────
const TemplateBadge: React.FC<{ template: string }> = ({template}) => {
  const config: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string }> = {
    'default': {icon: Layout, color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'},
    'full-width': {icon: Monitor, color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'},
    'sidebar': {icon: Layers, color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'},
  };
  const c = config[template] || config['default'];
  const Icon = c.icon;
  return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${c.color}`}>
      <Icon className="w-3 h-3"/>{template}
    </span>
  );
};

// ─── Empty State ──────────────────────────────────────
const EmptyState: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  action?: React.ReactNode
}> = ({
                                                                                                      icon: Icon,
                                                                                                      title,
                                                                                                      desc,
                                                                                                      action
                                                                                                    }) => (
    <div className="flex flex-col items-center justify-center py-16 px-6">
      <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-300 dark:text-gray-600"/>
      </div>
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <p className="text-xs text-gray-400 dark:text-gray-500 dark:text-gray-400 mt-1">{desc}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
);

// ─── Delete Confirm ───────────────────────────────────
const DeleteConfirm: React.FC<{
  title: string;
  desc: string;
  onConfirm: () => void;
  onCancel: () => void;
  isPending?: boolean
}> = ({title, desc, onConfirm, onCancel, isPending}) => (
    <div className="text-center py-2">
      <div
          className="w-14 h-14 rounded-2xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
        <AlertTriangle className="w-7 h-7 text-red-500"/>
      </div>
      <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-1">{title}</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">{desc}</p>
      <div className="flex items-center justify-center gap-3">
        <button onClick={onCancel}
                className="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors">
          取消
        </button>
        <button onClick={onConfirm} disabled={isPending}
                className="px-5 py-2.5 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors disabled:opacity-50 inline-flex items-center gap-2">
          {isPending && <Loader className="w-4 h-4 animate-spin"/>}
          确认删除
        </button>
      </div>
    </div>
);

// ─── Main Component ───────────────────────────────────
function SettingsInner() {
  const qc = useQueryClient();
  const {locale, setLocale, t} = useTranslation();
  const [activeTab, setActiveTab] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get('tab');
      if (tab && TABS.some(t => t.key === tab)) return tab;
    }
    return 'basic';
  });
  const [localSettings, setLocalSettings] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{type:'ok'|'err'; text:string}|null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // ── Delete confirm state ──
  const [deleteTarget, setDeleteTarget] = useState<{
    type: 'page';
    id: number;
    name: string
  } | null>(null);

  // ── Load settings ──
  const {data: fullData, isLoading} = useQuery({
    queryKey: ['admin-system-settings'],
    queryFn: async () => {
      const r = await apiClient.get('/system/settings/');
      if (r.success && r.data) {
        const raw = r.data.settings || {};
        const norm: Record<string, string> = {};
        for (const [k, v] of Object.entries(raw)) {
          norm[k] = String(v ?? '');
        }
        setLocalSettings(prev => Object.keys(norm).length > 0 ? norm : prev);
        return r.data;
      }
    },
  });

  const settings: Record<string, string> = localSettings;

  // ── Stats ──
  const stats = useMemo(() => ({
    totalSettings: Object.keys(settings).filter(k => settings[k]).length,
  }), [settings]);

  // ── Save settings ──
  const saveSettings = async () => {
    setSaving(true); setSaveMsg(null);
    try {
      const r = await apiClient.post('/system/settings/', {settings: localSettings, action: 'update_settings'});
      setSaveMsg({type: r.success ? 'ok' : 'err', text: r.success ? '✓ 保存成功' : (r.error || '保存失败')});
      if (r.success) {
        qc.invalidateQueries({queryKey: ['admin-system-settings']});
        setHasChanges(false);
      }
    } catch { setSaveMsg({type:'err', text:'网络异常'}); } finally {
      setSaving(false);
      setTimeout(() => setSaveMsg(null), 4000);
    }
  };

  const setVal = (key: string, val: string) => {
    setLocalSettings(prev => ({...prev, [key]: val}));
    setHasChanges(true);
  };

  // ── Export settings ──
  const exportSettings = useCallback(() => {
    const data = {settings: localSettings, exportedAt: new Date().toISOString()};
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Carded AI-settings-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [localSettings]);


  // ── Page mutations ── 已移除（使用 PageBuilder 管理页面）


  // ── Pages dialog state ── 已移除（使用 PageBuilder 管理页面）

  // ── Filtered settings fields ──
  const filteredFields = useMemo(() => {
    const fields = SETTINGS_FIELDS.filter(f => f.category === activeTab);
    if (!searchQuery) return fields;
    const q = searchQuery.toLowerCase();
    return fields.filter(f => f.label.toLowerCase().includes(q) || f.key.toLowerCase().includes(q) || f.desc?.toLowerCase().includes(q));
  }, [activeTab, searchQuery]);

  // ── Handle delete confirm ──
  const handleDeleteConfirm = useCallback(() => {
    if (!deleteTarget) return;
    setDeleteTarget(null);
  }, [deleteTarget]);

  // ── Render tab content ──
  const renderTabContent = () => {
    if (isLoading) {
      return (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 p-6">
            <SettingsSkeleton/>
          </div>
      );
    }

    switch (activeTab) {
      // ── Basic + System (Settings fields) ──
      case 'basic':
      case 'system': {
        const tabConfig = TABS.find(tb => tb.key === activeTab)!;
        const localeNames: Record<Locale, string> = {
          'zh-CN': t('settings.languageSwitcher.languages.zh-CN'),
          'en': t('settings.languageSwitcher.languages.en'),
          'ar': t('settings.languageSwitcher.languages.ar'),
          'he': t('settings.languageSwitcher.languages.he'),
        };
        return (
          <>
            <div
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <SectionTitle icon={tabConfig.icon} title={tabConfig.label} subtitle={tabConfig.desc}
                              action={
                                <div className="flex items-center gap-2">
                                  <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                                    <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                                           placeholder={t('settings.systemOptionsDesc')}
                                           className="pl-9 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 w-48 transition-all"/>
                                  </div>
                                  <button onClick={saveSettings} disabled={saving || !hasChanges}
                                          className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-sm font-medium rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40">
                                    {saving ? <Loader className="w-4 h-4 animate-spin"/> : <Save className="w-4 h-4"/>}
                                    {t('settings.saveSettings')}
                                  </button>
                                </div>
                              }
                />
              </div>

              {/* Save message */}
            {saveMsg && (
                <div className={`mx-6 mt-4 p-3.5 rounded-xl text-sm flex items-center gap-2.5 border ${
                    saveMsg.type === 'ok'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800'
                        : 'bg-red-50 text-red-600 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800'
                }`}>
                  {saveMsg.type === 'ok' ? <CheckCircle2 className="w-4.5 h-4.5"/> : <XCircle className="w-4.5 h-4.5"/>}
                {saveMsg.text}
              </div>
            )}

              {/* Unsaved changes indicator */}
              {hasChanges && !saveMsg && (
                  <div
                      className="mx-6 mt-4 p-3 rounded-xl text-sm flex items-center gap-2 bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800">
                    <Clock className="w-4 h-4"/>{t('common.loading')}
                  </div>
              )}

              <div className="p-6 space-y-5">
                {filteredFields.length === 0 ? (
                    <div className="text-center py-8 text-sm text-gray-400">
                      {searchQuery ? t('common.noData') : t('common.noData')}
                    </div>
                ) : (
                    filteredFields.map((f, i) => (
                        <div key={f.key} className="group">
                          <div className="flex items-start gap-3">
                            {f.icon && (
                                <div
                                    className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center mt-1 group-focus-within:bg-blue-50 dark:group-focus-within:bg-blue-900/20 transition-colors">
                                  <f.icon
                                      className="w-4 h-4 text-gray-400 group-focus-within:text-blue-500 transition-colors"/>
                                </div>
                            )}
                            <div className="flex-1 min-w-0">
                              <label
                                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{f.label}</label>
                              <FieldInput field={f} value={settings[f.key] ?? ''} onChange={v => setVal(f.key, v)}/>
                              <div className="flex items-center justify-between mt-1.5">
                                <p className="text-[10px] text-gray-400 font-mono">{f.key}</p>
                                {f.desc && <p className="text-[10px] text-gray-400">{f.desc}</p>}
                              </div>
                            </div>
                          </div>
                        </div>
                    ))
                )}
            </div>
          </div>

            {/* ── Language Switcher Card ── */}
            <div
              className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <SectionTitle icon={Globe} title={t('settings.languageSwitcher.title')}
                              subtitle={t('settings.languageSwitcher.subtitle')}/>
              </div>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                      <Globe className="w-5 h-5 text-white"/>
                    </div>
                    <div>
                      <p
                        className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('settings.languageSwitcher.current')}</p>
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">{localeNames[locale]}</p>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {locales.map((loc) => (
                    <button
                      key={loc}
                      onClick={() => setLocale(loc)}
                      className={`relative flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200 ${
                        locale === loc
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md shadow-blue-500/20'
                          : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-750'
                      }`}
                    >
                      {locale === loc && (
                        <div className="absolute top-2 right-2">
                          <CheckCircle2 className="w-4 h-4 text-blue-500"/>
                        </div>
                      )}
                      <span className={`text-sm font-medium ${
                        locale === loc
                          ? 'text-blue-700 dark:text-blue-300'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        {localeNames[loc]}
                      </span>
                      <span className={`text-xs ${
                        locale === loc
                          ? 'text-blue-500 dark:text-blue-400'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}>
                        {loc}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </>
        );
      }

      // ── Pages ── 已移除（使用 PageBuilder 管理页面）

      // ── Integrations ──
      case 'integrations':
        return (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 p-6">
            <AdminIntegrations settings={settings} onSave={async (s) => {
              setLocalSettings(prev => ({...prev, ...s}));
            }}/>
          </div>
        );


    }
  };

  return (
      <AdminShell title="系统设置" actions={
        <div className="flex items-center gap-2">
          <button onClick={exportSettings}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <Download className="w-4 h-4"/>导出配置
          </button>
          {hasChanges && (
              <button onClick={saveSettings} disabled={saving}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-sm font-medium rounded-xl disabled:opacity-50 transition-all shadow-lg shadow-blue-500/25">
                {saving ? <Loader className="w-4 h-4 animate-spin"/> : <Save className="w-4 h-4"/>}
                保存
              </button>
          )}
        </div>
      }>
        {/* ═══ Stats Cards ═══ */}
        <div className="grid grid-cols-2 lg:grid-cols-2 gap-4 mb-6">
          <StatCard icon={SettingsIcon} label="已配置项" value={stats.totalSettings}
                    gradient="from-blue-500 to-blue-600"/>

        </div>

      {/* ═══ Tabs ═══ */}
        <div className="flex gap-1.5 mb-6 overflow-x-auto pb-1 scrollbar-hide">
        {TABS.map(t => {
          const Icon = t.icon;
          const isActive = activeTab === t.key;
          return (
              <button key={t.key} onClick={() => {
                setActiveTab(t.key);
                setSearchQuery('');
              }}
                      className={`relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-xl whitespace-nowrap transition-all duration-200 ${
                          isActive
                              ? 'bg-gradient-to-r ' + t.gradient + ' text-white shadow-lg shadow-gray-200/50 dark:shadow-gray-900/50'
                              : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}>
              <Icon className="w-4 h-4"/>{t.label}
            </button>
          );
        })}
      </div>

        {/* ═══ Content ═══ */}
      {renderTabContent()}

        {/* ═══ Delete Confirm Modal ═══ */}
        <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="确认删除">
          {deleteTarget && (
              <DeleteConfirm
                title="删除内容"
                  desc={`确定要删除「${deleteTarget.name}」吗？此操作不可撤销。`}
                  onConfirm={handleDeleteConfirm}
                  onCancel={() => setDeleteTarget(null)}
                isPending={false}
              />
          )}
        </Modal>
    </AdminShell>
  );
}

export default function AdminSettings() {
  return <AuthGuard><QueryProvider><SettingsInner/></QueryProvider></AuthGuard>;
}
