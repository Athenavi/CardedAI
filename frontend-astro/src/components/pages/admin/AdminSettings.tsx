'use client';

import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {StatCard} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {getConfig} from '@/lib/config';
import {getFullMediaUrl} from '@/lib/utils';
import {type Locale, locales, useTranslation} from '@/lib/i18n';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Clock,
  Download,
  Edit3,
  ExternalLink,
  Eye,
  FileCode,
  FileText,
  Film,
  Globe,
  Hash,
  Home,
  Image,
  Layers,
  Layout,
  Link2,
  Loader,
  Mail,
  Menu,
  Monitor,
  Plus,
  Save,
  Search,
  Settings as SettingsIcon,
  Shield,
  Trash2,
  Type,
  Upload,
  X,
  XCircle,
  Zap
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────
interface Menu {id: number; name: string; slug: string; description: string; is_active: boolean; created_at?: string; updated_at?: string;}
interface MenuItem {id: number; title: string; url: string; target: string; parent_id: number | null; order_index: number; is_active?: boolean; created_at?: string;}
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
  {key: 'home', label: '首页配置', icon: Home, desc: '首页展示与布局', gradient: 'from-purple-500 to-pink-500'},
  {key: 'system', label: '系统选项', icon: Shield, desc: '系统功能开关', gradient: 'from-emerald-500 to-teal-500'},
  {key: 'menus', label: '菜单管理', icon: Menu, desc: '导航菜单配置', gradient: 'from-amber-500 to-orange-500'},
  {key: 'pages', label: '页面管理', icon: FileText, desc: '独立页面管理', gradient: 'from-rose-500 to-red-500'},
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
    placeholder: 'FastBlog',
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
  // home
  {key: 'home_hero_title', label: 'Hero 标题', category: 'home', placeholder: '欢迎来到我的博客', icon: Type},
  {key: 'home_hero_subtitle', label: 'Hero 副标题', category: 'home', placeholder: '分享知识与见解', icon: FileText},
  {key: 'home_hero_cta_text', label: 'CTA 按钮文本', category: 'home', placeholder: '开始阅读', icon: Zap},
  {key: 'home_hero_cta_link', label: 'CTA 按钮链接', category: 'home', placeholder: '/articles', icon: Link2},
  {
    key: 'home_cta_target',
    label: 'CTA 跳转方式',
    type: 'select',
    category: 'home',
    options: [{label: '当前窗口', value: '_self'}, {label: '新窗口', value: '_blank'}],
    icon: ExternalLink
  },
  {
    key: 'home_hero_background_image',
    label: 'Hero 背景媒体',
    type: 'media',
    category: 'home',
    placeholder: '输入媒体 URL 或上传图片/视频',
    icon: Film
  },
  {key: 'home_featured_title', label: '精选区域标题', category: 'home', placeholder: '精选文章', icon: Layers},
  {key: 'home_main_title', label: '主内容区标题', category: 'home', placeholder: '最新文章', icon: Type},
  {key: 'home_newsletter_title', label: '订阅区标题', category: 'home', placeholder: '订阅更新', icon: Mail},
  {
    key: 'home_newsletter_subtitle',
    label: '订阅区副标题',
    category: 'home',
    placeholder: '获取最新文章推送',
    icon: Mail
  },
  {key: 'home_newsletter_button_text', label: '订阅按钮文本', category: 'home', placeholder: '订阅', icon: Zap},
  {key: 'home_no_summary_msg', label: '无摘要消息', category: 'home', placeholder: '暂无摘要', icon: FileText},
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
  {
    key: 'menu_slug',
    label: '当前使用菜单标识',
    category: 'system',
    placeholder: 'main',
    icon: Menu,
    desc: '指定前台导航使用的菜单'
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

const MenuSkeleton = () => (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map(i => (
          <div key={i} className="p-5 bg-gray-100 dark:bg-gray-800 rounded-xl">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded-lg w-32"/>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-full w-12"/>
            </div>
            <div className="ml-4 space-y-2">
              {[1, 2].map(j => (
                  <div key={j} className="h-8 bg-gray-200 dark:bg-gray-700 rounded-lg w-full"/>
              ))}
            </div>
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
  const [activeTab, setActiveTab] = useState('basic');
  const [localSettings, setLocalSettings] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{type:'ok'|'err'; text:string}|null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // ── Delete confirm state ──
  const [deleteTarget, setDeleteTarget] = useState<{
    type: 'menu' | 'menuItem' | 'page';
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
      return {settings:{}, menus:[], menu_items:{}, pages:[]};
    },
  });

  const settings: Record<string, string> = localSettings;
  const menus: Menu[] = Array.isArray(fullData?.menus) ? fullData.menus : [];
  const menuItems: Record<string, MenuItem[]> = fullData?.menu_items || {};
  const pages: Page[] = Array.isArray(fullData?.pages) ? fullData.pages : [];

  // ── Stats ──
  const stats = useMemo(() => ({
    totalSettings: Object.keys(settings).filter(k => settings[k]).length,
    activeMenus: menus.filter(m => m.is_active).length,
    totalPages: pages.length,
    publishedPages: pages.filter(p => p.status === 1).length,
  }), [settings, menus, pages]);

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
    const data = {settings: localSettings, menus, menuItems, pages, exportedAt: new Date().toISOString()};
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fastblog-settings-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [localSettings, menus, menuItems, pages]);

  // ── Menu mutations ──
  const createMenuMut = useMutation({mutationFn:(d:any)=>apiClient.post('/system/settings/menus', d), onSuccess:()=>qc.invalidateQueries({queryKey:['admin-system-settings']})});
  const updateMenuMut = useMutation({mutationFn:({id,...d}:any)=>apiClient.put(`/system/settings/menus/${id}`, d), onSuccess:()=>qc.invalidateQueries({queryKey:['admin-system-settings']})});
  const delMenuMut = useMutation({mutationFn:(id:number)=>apiClient.delete(`/system/settings/menus/${id}`), onSuccess:()=>qc.invalidateQueries({queryKey:['admin-system-settings']})});
  const createMenuItemMut = useMutation({mutationFn:(d:any)=>apiClient.post('/system/settings/menu-items', d), onSuccess:()=>qc.invalidateQueries({queryKey:['admin-system-settings']})});
  const delMenuItemMut = useMutation({mutationFn:(id:number)=>apiClient.delete(`/system/settings/menu-items/${id}`), onSuccess:()=>qc.invalidateQueries({queryKey:['admin-system-settings']})});

  // ── Page mutations ──
  const createPageMut = useMutation({mutationFn:(d:any)=>apiClient.post('/system/settings/pages', d), onSuccess:()=>qc.invalidateQueries({queryKey:['admin-system-settings']})});
  const delPageMut = useMutation({mutationFn:(id:number)=>apiClient.delete(`/system/settings/pages/${id}`), onSuccess:()=>qc.invalidateQueries({queryKey:['admin-system-settings']})});

  // ── Menus dialog state ──
  const [menuModal, setMenuModal] = useState<{mode:'create'|'edit'; menu?: Menu} | null>(null);
  const [menuForm, setMenuForm] = useState({name:'', slug:'', description:''});
  const [itemModal, setItemModal] = useState<{menuId: number|null} | null>(null);
  const [itemForm, setItemForm] = useState({title: '', url: '', menu_id: 0, target: '_self', parent_id: ''});

  // ── Pages dialog state ──
  const [pageModal, setPageModal] = useState<{mode:'create'|'edit'; page?: Page} | null>(null);
  const [pageForm, setPageForm] = useState({title:'', slug:'', content:'', excerpt:'', template:'default', status:'0'});

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
    switch (deleteTarget.type) {
      case 'menu':
        delMenuMut.mutate(deleteTarget.id);
        break;
      case 'menuItem':
        delMenuItemMut.mutate(deleteTarget.id);
        break;
      case 'page':
        delPageMut.mutate(deleteTarget.id);
        break;
    }
    setDeleteTarget(null);
  }, [deleteTarget, delMenuMut, delMenuItemMut, delPageMut]);

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
      // ── Basic + Home + System (Settings fields) ──
      case 'basic':
      case 'home':
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

      // ── Menus ──
      case 'menus':
        return (
          <div className="space-y-6">
            <div
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <SectionTitle icon={Menu} title="导航菜单" subtitle={`共 ${menus.length} 个菜单`}
                              action={
                                <button onClick={() => {
                                  setMenuForm({name: '', slug: '', description: ''});
                                  setMenuModal({mode: 'create'});
                                }}
                                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-sm font-medium rounded-xl transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40">
                                  <Plus className="w-4 h-4"/>新建菜单
                                </button>
                              }
                />
              </div>

              {isLoading ? (
                  <div className="p-6"><MenuSkeleton/></div>
              ) : menus.length === 0 ? (
                  <EmptyState icon={Menu} title="暂无菜单" desc="创建您的第一个导航菜单"
                              action={
                                <button onClick={() => {
                                  setMenuForm({name: '', slug: '', description: ''});
                                  setMenuModal({mode: 'create'});
                                }}
                                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl transition-colors">
                                  <Plus className="w-4 h-4"/>新建菜单
                                </button>
                              }
                  />
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {menus.map((m, idx) => (
                      <div key={m.id}
                           className="px-6 py-5 hover:bg-gray-50/50 dark:hover:bg-gray-800/20 transition-colors group">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div
                                className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20">
                              <Menu className="w-5 h-5 text-white"/>
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-gray-900 dark:text-white">{m.name}</span>
                                <StatusBadge active={m.is_active}/>
                              </div>
                              <div className="flex items-center gap-2 mt-0.5">
                                <span className="text-[10px] text-gray-400 font-mono">{m.slug}</span>
                                {m.description && <span className="text-[10px] text-gray-400">· {m.description}</span>}
                              </div>
                            </div>
                        </div>
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => { setMenuForm({name:m.name, slug:m.slug, description:m.description}); setMenuModal({mode:'edit', menu:m}); }}
                                  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl transition-colors"
                                  title="编辑">
                            <Edit3 className="w-4 h-4"/>
                          </button>
                            <button onClick={() => setDeleteTarget({type: 'menu', id: m.id, name: m.name})}
                                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors"
                                    title="删除">
                              <Trash2 className="w-4 h-4"/>
                            </button>
                        </div>
                      </div>

                        {/* Menu items */}
                      {menuItems[String(m.id)]?.length > 0 && (
                          <div className="ml-[52px] space-y-1.5">
                            {menuItems[String(m.id)].map((item, itemIdx) => (
                                <div key={item.id}
                                     className="flex items-center justify-between py-2 px-3.5 bg-gray-50 dark:bg-gray-800/50 rounded-xl text-sm group/item hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                  <div className="flex items-center gap-2.5 min-w-0">
                                <span
                                  className="w-5 h-5 rounded bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-[10px] font-mono text-gray-500 dark:text-gray-400 shrink-0">
                                  {itemIdx + 1}
                                </span>
                                    <span
                                        className="text-gray-700 dark:text-gray-300 truncate font-medium">{item.title}</span>
                                    <span className="text-[10px] text-gray-400 truncate font-mono">{item.url}</span>
                                    {item.target === '_blank' && (
                                        <span
                                            className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded text-[10px] font-medium shrink-0">
                                    <ExternalLink className="w-2.5 h-2.5"/>新窗口
                                  </span>
                                    )}
                              </div>
                                  <button
                                      onClick={() => setDeleteTarget({type: 'menuItem', id: item.id, name: item.title})}
                                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors opacity-0 group-hover/item:opacity-100 shrink-0 ml-2">
                                    <Trash2 className="w-3.5 h-3.5"/>
                                  </button>
                            </div>
                          ))}
                        </div>
                      )}
                      <button onClick={() => { setItemForm({title:'', url:'', menu_id:m.id, target:'_self', parent_id:''}); setItemModal({menuId:m.id}); }}
                              className="ml-[52px] mt-2.5 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 inline-flex items-center gap-1 font-medium hover:underline">
                        <Plus className="w-3.5 h-3.5"/>添加菜单项
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Menu modal */}
            <Modal open={!!menuModal} onClose={() => setMenuModal(null)}
                   title={menuModal?.mode === 'create' ? '新建菜单' : '编辑菜单'}
                   subtitle={menuModal?.mode === 'create' ? '创建一个新的导航菜单' : `编辑菜单「${menuModal?.menu?.name}」`}>
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">名称</label>
                  <input value={menuForm.name} onChange={e => setMenuForm(p=>({...p,name:e.target.value}))}
                         className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                         placeholder="主导航菜单"/>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">标识
                    (slug)</label>
                  <input value={menuForm.slug} onChange={e => setMenuForm(p=>({...p,slug:e.target.value}))} disabled={menuModal?.mode==='edit'}
                         className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-mono"
                         placeholder="main-nav"/>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">描述</label>
                  <input value={menuForm.description} onChange={e => setMenuForm(p=>({...p,description:e.target.value}))}
                         className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                         placeholder="菜单用途说明（可选）"/>
                </div>
                <div className="flex justify-end gap-3 pt-3 border-t border-gray-100 dark:border-gray-800">
                  <button onClick={() => setMenuModal(null)}
                          className="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors">
                    取消
                  </button>
                  <button onClick={() => {
                    if (menuModal?.mode === 'create') createMenuMut.mutate(menuForm);
                    else if (menuModal?.menu) updateMenuMut.mutate({id: menuModal.menu.id, ...menuForm, is_active: menuModal.menu.is_active});
                    setMenuModal(null);
                  }}
                          className="px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-xl transition-all shadow-lg shadow-blue-500/25">
                    {menuModal?.mode === 'create' ? '创建菜单' : '保存更改'}
                  </button>
                </div>
              </div>
            </Modal>

            {/* Menu item modal */}
            <Modal open={!!itemModal} onClose={() => setItemModal(null)} title="添加菜单项"
                   subtitle="为菜单添加一个新的导航项">
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">标题</label>
                  <input value={itemForm.title} onChange={e => setItemForm(p=>({...p,title:e.target.value}))}
                         className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                         placeholder="菜单项名称"/>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">链接 URL</label>
                  <input value={itemForm.url} onChange={e => setItemForm(p=>({...p,url:e.target.value}))}
                         className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all font-mono"
                         placeholder="/articles 或 https://..."/>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">打开方式</label>
                    <div className="relative">
                      <select value={itemForm.target} onChange={e => setItemForm(p => ({...p, target: e.target.value}))}
                              className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 appearance-none pr-10 transition-all">
                        <option value="_self">当前窗口</option>
                        <option value="_blank">新窗口</option>
                      </select>
                      <ChevronDown
                          className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"/>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">父级 ID</label>
                    <input value={itemForm.parent_id} onChange={e => setItemForm(p=>({...p,parent_id:e.target.value}))}
                           className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                           placeholder="留空=顶级"/>
                  </div>
                </div>
                <div className="flex justify-end gap-3 pt-3 border-t border-gray-100 dark:border-gray-800">
                  <button onClick={() => setItemModal(null)}
                          className="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors">
                    取消
                  </button>
                  <button onClick={() => {
                    createMenuItemMut.mutate({
                      title: itemForm.title,
                      url: itemForm.url,
                      menu_id: itemForm.menu_id,
                      target: itemForm.target,
                      parent_id: itemForm.parent_id ? parseInt(itemForm.parent_id) : undefined,
                    });
                    setItemModal(null);
                  }}
                          className="px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-xl transition-all shadow-lg shadow-blue-500/25">
                    添加菜单项
                  </button>
                </div>
              </div>
            </Modal>
          </div>
        );

      // ── Pages ──
      case 'pages':
        return (
            <div
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <SectionTitle icon={FileText} title="独立页面" subtitle={`共 ${pages.length} 个页面`}
                              action={
                                <button onClick={() => {
                                  setPageForm({
                                    title: '',
                                    slug: '',
                                    content: '',
                                    excerpt: '',
                                    template: 'default',
                                    status: '0'
                                  });
                                  setPageModal({mode: 'create'});
                                }}
                                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-sm font-medium rounded-xl transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40">
                                  <Plus className="w-4 h-4"/>新建页面
                                </button>
                              }
                />
            </div>

              {isLoading ? (
                  <PageSkeleton/>
              ) : pages.length === 0 ? (
                  <EmptyState icon={FileText} title="暂无页面" desc="创建您的第一个独立页面"
                              action={
                                <button onClick={() => {
                                  setPageForm({
                                    title: '',
                                    slug: '',
                                    content: '',
                                    excerpt: '',
                                    template: 'default',
                                    status: '0'
                                  });
                                  setPageModal({mode: 'create'});
                                }}
                                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl transition-colors">
                                  <Plus className="w-4 h-4"/>新建页面
                                </button>
                              }
                  />
            ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead
                          className="bg-gray-50/80 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                      <tr>
                        <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left">标题</th>
                        <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden sm:table-cell">别名</th>
                        <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden lg:table-cell">模板</th>
                        <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden md:table-cell">状态</th>
                        <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-right">操作</th>
                      </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50 dark:divide-gray-800/50">
                      {pages.map(p => (
                          <tr key={p.id}
                              className="group hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors">
                            <td className="px-5 py-4">
                              <div className="flex items-center gap-3">
                                <div
                                    className="w-8 h-8 rounded-lg bg-gradient-to-br from-rose-500 to-red-500 flex items-center justify-center shadow-sm">
                                  <FileCode className="w-4 h-4 text-white"/>
                                </div>
                                <span className="text-sm font-medium text-gray-900 dark:text-white">{p.title}</span>
                              </div>
                            </td>
                            <td
                              className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 font-mono hidden sm:table-cell">
                              <span
                                  className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs">/{p.slug}</span>
                            </td>
                            <td className="px-5 py-4 hidden lg:table-cell">
                              <TemplateBadge template={p.template}/>
                            </td>
                            <td className="px-5 py-4 hidden md:table-cell">
                              <StatusBadge active={p.status === 1} label={p.status === 1 ? '已发布' : '草稿'}/>
                            </td>
                            <td className="px-5 py-4 text-right">
                              <div
                                  className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <a href={`/p/${p.slug}`} target="_blank" rel="noopener"
                                   className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl transition-colors"
                                   title="预览">
                                  <Eye className="w-4 h-4"/>
                                </a>
                                <button onClick={() => setDeleteTarget({type: 'page', id: p.id, name: p.title})}
                                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors"
                                        title="删除">
                                  <Trash2 className="w-4 h-4"/>
                                </button>
                              </div>
                            </td>
                          </tr>
                      ))}
                      </tbody>
                    </table>
                  </div>
            )}

              {/* Page modal */}
            <Modal open={!!pageModal} onClose={() => setPageModal(null)}
                   title={pageModal?.mode === 'create' ? '新建页面' : '编辑页面'}
                   subtitle={pageModal?.mode === 'create' ? '创建一个新的独立页面' : `编辑页面「${pageModal?.page?.title}」`}
                   maxWidth="max-w-2xl">
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">标题</label>
                    <input value={pageForm.title} onChange={e => setPageForm(p => ({...p, title: e.target.value}))}
                           className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                           placeholder="页面标题"/>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">别名
                      (slug)</label>
                    <input value={pageForm.slug} onChange={e => setPageForm(p => ({...p, slug: e.target.value}))}
                           className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all font-mono"
                           placeholder="about"/>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">摘要</label>
                  <input value={pageForm.excerpt} onChange={e => setPageForm(p=>({...p,excerpt:e.target.value}))}
                         className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                         placeholder="页面摘要（可选）"/>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">模板</label>
                    <div className="relative">
                      <select value={pageForm.template}
                              onChange={e => setPageForm(p => ({...p, template: e.target.value}))}
                              className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 appearance-none pr-10 transition-all">
                        <option value="default">默认</option>
                        <option value="full-width">全宽</option>
                        <option value="sidebar">侧边栏</option>
                      </select>
                      <ChevronDown
                          className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"/>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">状态</label>
                    <div className="relative">
                      <select value={pageForm.status} onChange={e => setPageForm(p => ({...p, status: e.target.value}))}
                              className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 appearance-none pr-10 transition-all">
                        <option value="0">草稿</option>
                        <option value="1">已发布</option>
                      </select>
                      <ChevronDown
                          className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"/>
                    </div>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">内容
                    (Markdown)</label>
                  <textarea value={pageForm.content} onChange={e => setPageForm(p => ({...p, content: e.target.value}))}
                            rows={8}
                            className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 resize-none font-mono transition-all"
                            placeholder="使用 Markdown 格式编写页面内容..."/>
                </div>
                <div className="flex justify-end gap-3 pt-3 border-t border-gray-100 dark:border-gray-800">
                  <button onClick={() => setPageModal(null)}
                          className="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors">
                    取消
                  </button>
                  <button onClick={() => {
                    createPageMut.mutate(pageForm);
                    setPageModal(null);
                  }}
                          className="px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-xl transition-all shadow-lg shadow-blue-500/25">
                    {pageModal?.mode === 'create' ? '创建页面' : '保存更改'}
                  </button>
                </div>
              </div>
            </Modal>
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
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard icon={SettingsIcon} label="已配置项" value={stats.totalSettings}
                    gradient="from-blue-500 to-blue-600"/>
          <StatCard icon={Menu} label="激活菜单" value={stats.activeMenus} gradient="from-amber-500 to-amber-600"/>
          <StatCard icon={FileText} label="总页面数" value={stats.totalPages} gradient="from-purple-500 to-purple-600"/>
          <StatCard icon={CheckCircle2} label="已发布页面" value={stats.publishedPages}
                    gradient="from-emerald-500 to-emerald-600"/>
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
                  title={`删除${deleteTarget.type === 'menu' ? '菜单' : deleteTarget.type === 'menuItem' ? '菜单项' : '页面'}`}
                  desc={`确定要删除「${deleteTarget.name}」吗？此操作不可撤销。`}
                  onConfirm={handleDeleteConfirm}
                  onCancel={() => setDeleteTarget(null)}
                  isPending={delMenuMut.isPending || delMenuItemMut.isPending || delPageMut.isPending}
              />
          )}
        </Modal>
    </AdminShell>
  );
}

export default function AdminSettings() {
  return <AuthGuard><QueryProvider><SettingsInner/></QueryProvider></AuthGuard>;
}
