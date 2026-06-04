'use client';

import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useForm} from 'react-hook-form';
import {z} from 'zod';
import {zodResolver} from '@hookform/resolvers/zod';
import {apiClient, CategoryService} from '@/lib/api';
import type {Category} from '@/lib/api/base-types';
import {
  AlertCircle,
  AlignCenter,
  AlignLeft,
  AlignRight,
  ArrowLeft,
  BarChart3,
  Bold,
  Check,
  ChevronDown,
  Clock,
  Code,
  Copy,
  Crown,
  Eye,
  EyeOff,
  FileText,
  FolderTree,
  Globe,
  Hash,
  Heading1,
  Heading2,
  History,
  Image,
  Italic,
  Keyboard,
  Link,
  List,
  ListOrdered,
  Loader as LoaderIcon,
  Maximize2,
  Minimize2,
  Minus,
  PanelRightClose,
  PanelRightOpen,
  Quote,
  Redo2,
  Save,
  Send,
  Strikethrough,
  Tag,
  Type,
  Underline as UnderlineIcon,
  Undo2,
  Users,
  Wifi,
  WifiOff,
  X
} from 'lucide-react';
import {QueryProvider} from '@/components/QueryProvider';
import {AuthGuard} from '@/components/AuthGuard';
import RevisionsSidebar from '@/components/editor/RevisionsSidebar';
import CoverImageUploader from '@/components/editor/CoverImageUploader';
import {useYjsCollaboration} from '@/hooks/useYjsCollaboration';

const RichEditor = React.lazy(() => import('@/components/editor/RichEditor'));

/* ── Constants ── */
const DRAFT_KEY = 'fastblog_draft';
const slugify = (s: string) => s.toLowerCase().replace(/[^\w\u4e00-\u9fa5]+/g, '-').replace(/^-|-$/g, '').slice(0, 200);
const loadDraft = () => { try { const d = localStorage.getItem(DRAFT_KEY); return d ? JSON.parse(d) : null; } catch { return null; } };
const persistDraft = (data: any) => {
    try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify({...data, _savedAt: Date.now()}));
    } catch {
    }
};
const clearDraft = () => { try { localStorage.removeItem(DRAFT_KEY); } catch {} };

const schema = z.object({
  title: z.string().min(1, '标题不能为空').max(200), slug: z.string().optional(),
  excerpt: z.string().max(500).optional(), cover_image: z.string().optional(),
  category_id: z.coerce.number().optional(), tags: z.string().optional(),
  status: z.union([z.literal(0), z.literal(1)]).default(0),
  hidden: z.boolean().default(false), is_vip_only: z.boolean().default(false),
});
type FormData = z.infer<typeof schema>;
interface Props { mode: 'create' | 'edit'; }

/* ── Writing Stats Hook ── */
function useWritingStats(content: string) {
    return useMemo(() => {
        const text = content.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
        const chars = text.length;
        const words = text ? text.split(/[\s,，。！？；：、]+/).filter(Boolean).length : 0;
        const sentences = text ? text.split(/[。！？.!?\n]+/).filter(Boolean).length : 0;
        const paragraphs = content ? content.split(/<\/p>|<br\s*\/?>/gi).filter(p => p.replace(/<[^>]*>/g, '').trim()).length : 0;
        const readingTime = Math.max(1, Math.ceil(chars / 500)); // ~500 chars/min for Chinese
        return {chars, words, sentences, paragraphs, readingTime};
    }, [content]);
}

/* ── Keyboard Shortcuts Modal ── */
const ShortcutsModal: React.FC<{ onClose: () => void }> = ({onClose}) => {
    const shortcuts = [
        {
            category: '基础格式', items: [
                {keys: 'Ctrl + B', desc: '粗体'}, {keys: 'Ctrl + I', desc: '斜体'},
                {keys: 'Ctrl + U', desc: '下划线'}, {keys: 'Ctrl + Shift + S', desc: '删除线'},
                {keys: 'Ctrl + Shift + H', desc: '高亮'},
            ]
        },
        {
            category: '标题与段落', items: [
                {keys: 'Ctrl + Alt + 1', desc: '一级标题'}, {keys: 'Ctrl + Alt + 2', desc: '二级标题'},
                {keys: 'Ctrl + Alt + 3', desc: '三级标题'}, {keys: 'Ctrl + Shift + 8', desc: '无序列表'},
                {keys: 'Ctrl + Shift + 7', desc: '有序列表'}, {keys: 'Ctrl + Shift + 9', desc: '引用'},
            ]
        },
        {
            category: '通用操作', items: [
                {keys: 'Ctrl + S', desc: '保存草稿'}, {keys: 'Ctrl + Shift + P', desc: '发布文章'},
                {keys: 'Ctrl + K', desc: '插入链接'}, {keys: 'Ctrl + Shift + I', desc: '插入图片'},
                {keys: 'Ctrl + Z', desc: '撤销'}, {keys: 'Ctrl + Shift + Z', desc: '重做'},
            ]
        },
    ];
    return (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/50 backdrop-blur-sm"
             onClick={onClose}>
            <div
                className="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-lg max-h-[80vh] flex flex-col shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
                onClick={e => e.stopPropagation()}>
                <div
                    className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
                    <div className="flex items-center gap-2">
                        <Keyboard className="w-5 h-5 text-blue-600"/>
                        <h3 className="font-bold text-gray-900 dark:text-white text-lg">键盘快捷键</h3>
                    </div>
                    <button onClick={onClose}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        <X className="w-5 h-5 text-gray-400"/>
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {shortcuts.map(group => (
                        <div key={group.category}>
                          <h4
                            className="text-xs font-bold text-gray-400 dark:text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">{group.category}</h4>
                            <div className="space-y-1.5">
                                {group.items.map(s => (
                                    <div key={s.keys}
                                         className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                        <span className="text-sm text-gray-700 dark:text-gray-300">{s.desc}</span>
                                        <div className="flex gap-1">
                                            {s.keys.split(' + ').map((k, i) => (
                                                <React.Fragment key={i}>
                                                    {i > 0 && <span
                                                        className="text-gray-300 dark:text-gray-600 text-xs self-center">+</span>}
                                                    <kbd
                                                        className="px-2 py-0.5 text-xs font-mono bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-600 dark:text-gray-400 shadow-sm">{k}</kbd>
                                                </React.Fragment>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

/* ── Toolbar Dropdown ── */
const ToolbarDropdown: React.FC<{
    trigger: React.ReactNode;
    children: React.ReactNode;
    align?: 'left' | 'right';
}> = ({trigger, children, align = 'left'}) => {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open) return;
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [open]);

    return (
        <div className="relative" ref={ref}>
            <div onClick={() => setOpen(!open)}>{trigger}</div>
            {open && (
                <div
                    className={`absolute top-full mt-1 ${align === 'right' ? 'right-0' : 'left-0'} z-50 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-1.5 min-w-[180px] animate-in fade-in slide-in-from-top-2 duration-150`}
                    onClick={() => setOpen(false)}>
                    {children}
                </div>
            )}
        </div>
    );
};

/* ── Section Component ── */
const Section: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
    title: string;
    children: React.ReactNode;
    defaultOpen?: boolean;
    badge?: string | number
}> = ({
          icon: Icon, title, children, defaultOpen = true, badge
      }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    return (
        <div
            className="border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden bg-white dark:bg-gray-800/50 mb-3">
            <button type="button" onClick={() => setIsOpen(!isOpen)}
                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/80 transition-colors">
                <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                        <Icon className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"/>
                    </div>
                    <span
                        className="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">{title}</span>
                    {badge !== undefined && (
                        <span
                            className="px-1.5 py-0.5 text-[10px] font-bold bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full">{badge}</span>
                    )}
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}/>
            </button>
            <div
                className={`transition-all duration-200 ${isOpen ? 'max-h-[800px] opacity-100' : 'max-h-0 opacity-0'} overflow-hidden`}>
                <div className="px-4 pb-4">{children}</div>
            </div>
        </div>
    );
};

/* ── Save Status Indicator ── */
const SaveStatus: React.FC<{ saving: boolean; lastSaved: number | null }> = ({saving, lastSaved}) => {
    const [showCheck, setShowCheck] = useState(false);

    useEffect(() => {
        if (lastSaved) {
            setShowCheck(true);
            const t = setTimeout(() => setShowCheck(false), 2000);
            return () => clearTimeout(t);
        }
    }, [lastSaved]);

    if (saving) {
        return (
            <div className="flex items-center gap-1.5 text-xs text-blue-500">
                <LoaderIcon className="w-3.5 h-3.5 animate-spin"/>
                <span>保存中...</span>
            </div>
        );
    }

    if (showCheck) {
        return (
            <div className="flex items-center gap-1.5 text-xs text-emerald-500 animate-in fade-in duration-200">
                <Check className="w-3.5 h-3.5"/>
                <span>已保存</span>
            </div>
        );
    }

    if (lastSaved) {
        const ago = Date.now() - lastSaved;
        const label = ago < 60000 ? '刚刚' : ago < 3600000 ? `${Math.floor(ago / 60000)} 分钟前` : `${Math.floor(ago / 3600000)} 小时前`;
        return <span className="text-xs text-gray-400">{label} 已自动保存</span>;
    }

    return null;
};

/* ── Main Editor Component ── */
const ArticleEditorPageInner: React.FC<Props> = ({mode}) => {
  const qc = useQueryClient();
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<number | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showRevisions, setShowRevisions] = useState(false);
    const [showShortcuts, setShowShortcuts] = useState(false);
    const [focusMode, setFocusMode] = useState(false);
  const [content, setContent] = useState('');
    const [showDraftBanner, setShowDraftBanner] = useState(false);
    const [draftData, setDraftData] = useState<any>(null);
  const editorRef = useRef<any>(null);
  const draftLoaded = useRef(false);
    const remoteContentRef = useRef(false);
    const contentRef = useRef(content);
    contentRef.current = content;

  const articleId = useMemo(() => {
    if (mode === 'edit' && typeof window !== 'undefined') return new URLSearchParams(window.location.search).get('id');
    return null;
  }, [mode]);

    const [collabActive, setCollabActive] = useState(
        mode === 'edit' && typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('collab') === '1'
    );

  // Collaborative editing
  const collabDocId = mode === 'edit' && articleId ? `article-${articleId}` : null;
  const collab = useYjsCollaboration(
    collabActive ? collabDocId : null,
    articleId,
    typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('token') : null,
  );

    // Auto-start collab
  useEffect(() => {
      if (collabActive && articleId) collab.start();
  }, [collabActive, articleId]);

    // Sync remote content → local
  useEffect(() => {
    if (collabActive && collab.content && editorRef.current) {
      remoteContentRef.current = true;
      editorRef.current.commands.setContent(collab.content, false);
    }
  }, [collabActive, collab.content]);

    // Sync local content → remote
  useEffect(() => {
      if (remoteContentRef.current) {
          remoteContentRef.current = false;
          return;
      }
      if (collabActive && content) collab.sendContent(content);
  }, [collabActive, content]);

  const {register, handleSubmit, reset, watch, setValue, getValues, formState: {errors}} = useForm<FormData>({
      resolver: zodResolver(schema) as any, defaultValues: {status: 0, hidden: false, is_vip_only: false, tags: ''},
  });

  const title = watch('title');
    const coverImage = watch('cover_image');
    const isHidden = watch('hidden');
  const __isVipOnly = watch('is_vip_only');

    // Writing stats
    const stats = useWritingStats(content);

  // Auto-slug
    useEffect(() => {
        const cur = getValues('slug');
        if (title && !cur && mode === 'create') setValue('slug', slugify(title));
    }, [title, mode, getValues, setValue]);

  // Auto-save draft
    useEffect(() => {
        if (mode !== 'create') return;
        const t = setInterval(() => {
            const d = getValues();
            if (d.title || contentRef.current) {
                persistDraft({...d, content: contentRef.current});
                setLastSaved(Date.now());
            }
        }, 30000);
        return () => clearInterval(t);
    }, [mode, getValues]);

    // Load draft (show banner instead of confirm)
    useEffect(() => {
        if (mode === 'create' && !draftLoaded.current) {
            draftLoaded.current = true;
            const draft = loadDraft();
            if (draft?.title) {
                setDraftData(draft);
                setShowDraftBanner(true);
            }
        }
    }, [mode]);

    const restoreDraft = () => {
        if (draftData) {
            reset({...draftData, status: 0});
            if (draftData.content) setContent(draftData.content);
            setShowDraftBanner(false);
        }
    };

    const dismissDraft = () => {
        clearDraft();
        setShowDraftBanner(false);
    };

    const {data: categories} = useQuery({
        queryKey: ['categories'], staleTime: 300_000,
        queryFn: async () => {
            const res = await CategoryService.getCategories({per_page: 100});
            return res.success && res.data ? (res.data.categories || []) : [];
        }
    });

  const {isLoading: loadingArticle} = useQuery({
    queryKey: ['article-edit', articleId], enabled: mode === 'edit' && !!articleId,
      staleTime: 0, gcTime: 0,
    queryFn: async () => {
      const res = await apiClient.get(`/articles/edit/${articleId}`);
        if (res.success && res.data) {
            const d = res.data;
            reset({
                title: d.article?.title || d.title || '', slug: d.article?.slug || '',
                excerpt: d.article?.excerpt || d.excerpt || '', category_id: d.article?.category_id || undefined,
                tags: (d.article?.tags || []).join(', '), status: d.article?.status ?? 0,
                hidden: d.article?.hidden || false, is_vip_only: d.article?.is_vip_only || false,
              cover_image: d.article?.cover_image || d.cover_image || '',
            });
            setContent(d.content || d.article?.content || '');
        }
      return res;
    },
  });

  const submitMut = useMutation({
      mutationFn: async (data: FormData) => {
          const fd = new FormData();
          Object.entries(data).forEach(([k, v]) => {
              if (v !== undefined && v !== null && v !== '') fd.append(k, String(v));
          });
          fd.set('content', contentRef.current);
          fd.set('status', String(data.status ?? 0));
        // 使用 apiClient.request 确保 FormData 以 multipart/form-data 发送
        // apiClient.post/put 会强制设置 Content-Type: application/json，导致后端无法解析 form 字段
        return mode === 'create'
          ? apiClient.request('/articles', {method: 'POST', body: fd})
          : apiClient.request(`/articles/${articleId}`, {method: 'PUT', body: fd});
      },
      onSuccess: (res) => {
          if (res.success) {
              qc.invalidateQueries({queryKey: ['my-posts']});
              qc.invalidateQueries({queryKey: ['article-edit']});
              clearDraft();
              setTimeout(() => window.location.href = '/my/posts', 500);
          }
      },
  });

    const submit = async (data: any) => {
        setSaving(true);
        try {
            await submitMut.mutateAsync(data);
        } finally {
            setSaving(false);
        }
    };
    const publish = () => {
        setValue('status', 1 as any);
        handleSubmit(submit as any)();
    };
    const saveDraftAction = () => {
        setValue('status', 0 as any);
        handleSubmit(submit as any)();
    };

    // Toolbar exec
    const exec = useCallback((cmd: string, ...args: any[]) => {
    const e = editorRef.current;
    if (!e) return;
        const chain = e.chain().focus();
        switch (cmd) {
            case 'bold':
                chain.toggleBold().run();
                break;
            case 'italic':
                chain.toggleItalic().run();
                break;
            case 'underline':
                chain.toggleUnderline().run();
                break;
            case 'strike':
                chain.toggleStrike().run();
                break;
            case 'h1':
                chain.toggleHeading({level: 1}).run();
                break;
            case 'h2':
                chain.toggleHeading({level: 2}).run();
                break;
            case 'h3':
                chain.toggleHeading({level: 3}).run();
                break;
            case 'ul':
                chain.toggleBulletList().run();
                break;
            case 'ol':
                chain.toggleOrderedList().run();
                break;
            case 'quote':
                chain.toggleBlockquote().run();
                break;
            case 'code':
                chain.toggleCodeBlock().run();
                break;
            case 'hr':
                chain.setHorizontalRule().run();
                break;
            case 'left':
                chain.setTextAlign('left').run();
                break;
            case 'center':
                chain.setTextAlign('center').run();
                break;
            case 'right':
                chain.setTextAlign('right').run();
                break;
            case 'undo':
                chain.undo().run();
                break;
            case 'redo':
                chain.redo().run();
                break;
            case 'image': {
                const u = prompt('图片 URL:');
                if (u) chain.setImage({src: u}).run();
                break;
            }
            case 'link': {
                const u = prompt('链接 URL:');
                if (u) chain.setLink({href: u}).run();
                break;
            }
        }
    }, []);

    // Keyboard shortcuts
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 's') {
                    e.preventDefault();
                    saveDraftAction();
                }
                if (e.shiftKey && e.key === 'P') {
                    e.preventDefault();
                    publish();
                }
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, []);

    // Loading state
  if (mode === 'edit' && loadingArticle) {
      return (
          <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-950">
              <div className="flex flex-col items-center gap-4">
                  <div className="relative w-12 h-12">
                      <div className="absolute inset-0 rounded-full border-2 border-blue-200 dark:border-blue-800"/>
                      <div
                          className="absolute inset-0 rounded-full border-2 border-blue-600 border-t-transparent animate-spin"/>
                  </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">加载文章中...</p>
              </div>
          </div>
      );
  }

    const TBtn: React.FC<{
        cmd: string; active?: boolean; children: React.ReactNode; title: string; variant?: 'default' | 'danger';
    }> = ({cmd, active, children, title, variant = 'default'}) => (
        <button type="button" onClick={() => exec(cmd)} title={title}
                className={`group relative p-1.5 rounded-lg transition-all duration-150 ${
                    active
                        ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 shadow-sm'
                        : variant === 'danger'
                            ? 'text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600'
                            : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300'
                }`}>
            {children}
        </button>
  );

    const Divider = () => <div className="w-px h-5 bg-gray-200 dark:bg-gray-700 mx-1"/>;

  return (
      <div
          className={`h-screen flex flex-col bg-gray-50 dark:bg-gray-950 overflow-hidden transition-all duration-300 ${focusMode ? 'bg-white dark:bg-black' : ''}`}>
          {/* ===== Top Bar ===== */}
          <header
              className={`flex items-center gap-2 px-3 lg:px-4 h-14 border-b flex-shrink-0 z-30 transition-all duration-300 ${
                  focusMode
                      ? 'border-transparent bg-white/80 dark:bg-black/80 backdrop-blur-xl'
                      : 'border-gray-200/80 dark:border-gray-800/80 bg-white/95 dark:bg-gray-950/95 backdrop-blur-lg'
              }`}>
              {/* Back Button */}
              <a href="/my/posts"
                 className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group">
                  <ArrowLeft
                      className="w-4 h-4 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"/>
                  <span
                      className="text-xs text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 hidden sm:block">返回</span>
              </a>

              <Divider/>

              {/* Undo/Redo */}
              <TBtn cmd="undo" title="撤销 (Ctrl+Z)"><Undo2 className="w-4 h-4"/></TBtn>
              <TBtn cmd="redo" title="重做 (Ctrl+Shift+Z)"><Redo2 className="w-4 h-4"/></TBtn>

              <Divider/>

              {/* Text Formatting */}
              <TBtn cmd="bold" title="粗体 (Ctrl+B)"><Bold className="w-4 h-4"/></TBtn>
              <TBtn cmd="italic" title="斜体 (Ctrl+I)"><Italic className="w-4 h-4"/></TBtn>
              <TBtn cmd="underline" title="下划线 (Ctrl+U)"><UnderlineIcon className="w-4 h-4"/></TBtn>
              <TBtn cmd="strike" title="删除线"><Strikethrough className="w-4 h-4"/></TBtn>

              <Divider/>

              {/* Headings */}
              <ToolbarDropdown
                  trigger={
                      <button
                        className="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                          <Type className="w-4 h-4"/><ChevronDown className="w-3 h-3"/>
                      </button>
                  }>
                  {[
                      {cmd: 'h1', label: '一级标题', icon: Heading1},
                      {cmd: 'h2', label: '二级标题', icon: Heading2},
                      {cmd: 'h3', label: '三级标题', icon: Type},
                  ].map(h => (
                      <button key={h.cmd} onClick={() => exec(h.cmd)}
                              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                          <h.icon className="w-4 h-4 text-gray-400"/>
                          {h.label}
                      </button>
                  ))}
              </ToolbarDropdown>

              <Divider/>

              {/* Lists & Blocks */}
              <TBtn cmd="ul" title="无序列表"><List className="w-4 h-4"/></TBtn>
              <TBtn cmd="ol" title="有序列表"><ListOrdered className="w-4 h-4"/></TBtn>
        <TBtn cmd="quote" title="引用"><Quote className="w-4 h-4"/></TBtn>
              <TBtn cmd="code" title="代码块"><Code className="w-4 h-4"/></TBtn>
              <TBtn cmd="hr" title="分割线"><Minus className="w-4 h-4"/></TBtn>

              <Divider/>

              {/* Media */}
              <TBtn cmd="image" title="插入图片"><Image className="w-4 h-4"/></TBtn>
              <TBtn cmd="link" title="插入链接"><Link className="w-4 h-4"/></TBtn>

              <Divider/>

              {/* Alignment */}
              <div className="hidden lg:flex items-center gap-0.5">
                  <TBtn cmd="left" title="左对齐"><AlignLeft className="w-4 h-4"/></TBtn>
                  <TBtn cmd="center" title="居中"><AlignCenter className="w-4 h-4"/></TBtn>
                  <TBtn cmd="right" title="右对齐"><AlignRight className="w-4 h-4"/></TBtn>
                  <Divider/>
              </div>

              {/* More Actions */}
        {mode === 'edit' && articleId && (
          <>
              <button onClick={() => setShowRevisions(true)}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-all">
              <History className="w-3.5 h-3.5"/><span className="hidden sm:inline">版本</span>
            </button>
            <button onClick={() => { if (!collabActive) { setCollabActive(true); } else { collab.stop(); setCollabActive(false); } }}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg border transition-all ${
                        collabActive
                            ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400'
                          : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}>
              {collabActive ? <Wifi className="w-3.5 h-3.5"/> : <Users className="w-3.5 h-3.5"/>}
              <span className="hidden sm:inline">{collabActive ? '协作中' : '协作'}</span>
              {collabActive && collab.connecting && <LoaderIcon className="w-3 h-3 animate-spin ml-0.5"/>}
            </button>
          </>
        )}

              {/* Spacer */}
              <div className="flex-1"/>

              {/* Right Actions */}
              <div className="flex items-center gap-2">
                  <SaveStatus saving={saving} lastSaved={lastSaved}/>

                  <button onClick={() => setShowShortcuts(true)} title="键盘快捷键"
                          className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors hidden lg:flex">
                      <Keyboard className="w-4 h-4"/>
                  </button>

                  <button onClick={() => setFocusMode(!focusMode)} title={focusMode ? '退出专注模式' : '专注模式'}
                          className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                      {focusMode ? <Minimize2 className="w-4 h-4"/> : <Maximize2 className="w-4 h-4"/>}
                  </button>

                  <button onClick={() => setShowSidebar(!showSidebar)} title={showSidebar ? '收起侧边栏' : '展开侧边栏'}
                          className={`p-2 rounded-lg transition-all ${showSidebar ? 'text-blue-600 bg-blue-50 dark:bg-blue-900/20' : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>
                      {showSidebar ? <PanelRightClose className="w-4 h-4"/> : <PanelRightOpen className="w-4 h-4"/>}
                  </button>

                  <Divider/>

                  <button onClick={saveDraftAction} disabled={saving}
                          className="flex items-center gap-1.5 px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 transition-all hover:border-gray-300 dark:hover:border-gray-600">
                      <Save className="w-4 h-4"/>{saving ? '...' : '草稿'}
                  </button>

                  <button onClick={publish} disabled={saving}
                          className="flex items-center gap-1.5 px-5 py-2 text-sm bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 disabled:opacity-50 transition-all">
                      <Send className="w-4 h-4"/>{mode === 'create' ? '发布' : '更新'}
                  </button>
        </div>
      </header>

          {/* ===== Draft Recovery Banner ===== */}
          {showDraftBanner && (
              <div
                  className="flex items-center justify-between px-4 py-3 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800">
                  <div className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-amber-600"/>
                      <span className="text-sm text-amber-800 dark:text-amber-300">检测到未保存的草稿</span>
                  </div>
                  <div className="flex items-center gap-2">
                      <button onClick={restoreDraft}
                              className="px-3 py-1 text-xs bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors">
                          恢复草稿
                      </button>
                      <button onClick={dismissDraft}
                              className="px-3 py-1 text-xs border border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-400 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors">
                          丢弃
                      </button>
                  </div>
              </div>
          )}

          {/* ===== Editor Body ===== */}
      <div className="flex flex-1 overflow-hidden">
          {/* Main Editor */}
          <main className={`flex-1 overflow-y-auto transition-all duration-300 ${focusMode ? '' : ''}`}>
              <div
                  className={`mx-auto px-6 lg:px-12 py-10 transition-all duration-300 ${showSidebar && !focusMode ? 'max-w-3xl' : 'max-w-4xl'}`}>
                  {/* Title */}
                  <div className="mb-8">
                      <input {...register('title')} placeholder="在此输入文章标题..."
                             className="w-full text-3xl lg:text-4xl font-bold px-0 py-2 bg-transparent border-none outline-none focus:ring-0 dark:text-white placeholder-gray-300 dark:placeholder-gray-600 tracking-tight leading-tight"
                             style={{fontFamily: 'inherit'}}/>
                      {errors.title && (
                          <p className="flex items-center gap-1.5 text-red-500 text-sm mt-2">
                              <AlertCircle className="w-3.5 h-3.5"/>{errors.title.message}
                          </p>
                      )}
                      {/* Slug preview */}
                      {watch('slug') && (
                          <div className="flex items-center gap-2 mt-2">
                              <Globe className="w-3.5 h-3.5 text-gray-400"/>
                              <span className="text-xs text-gray-400 font-mono">/articles/{watch('slug')}</span>
                          </div>
                      )}
                  </div>

                  {/* Rich Editor */}
                  <React.Suspense fallback={
                      <div className="space-y-4">
                          {[...Array(8)].map((_, i) => (
                              <div key={i} className="h-4 bg-gray-100 dark:bg-gray-800 rounded-full animate-pulse"
                                   style={{width: `${80 + Math.random() * 20}%`}}/>
                          ))}
                      </div>
                  }>
                      <RichEditor value={content} onChange={setContent} placeholder="开始你的创作..."
                                  editorRef={editorRef}/>
                  </React.Suspense>
          </div>
        </main>

          {/* ===== Sidebar ===== */}
          {showSidebar && !focusMode && (
              <aside
                  className="w-72 lg:w-80 border-l border-gray-200/80 dark:border-gray-800/80 bg-gray-50/80 dark:bg-gray-900/80 backdrop-blur-sm overflow-y-auto flex-shrink-0">
                  <div className="p-4 space-y-0">
                      {/* Writing Stats Card */}
                      <div
                          className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-4 mb-4 border border-blue-100 dark:border-blue-800/30">
                          <div className="flex items-center gap-2 mb-3">
                              <BarChart3 className="w-4 h-4 text-blue-600 dark:text-blue-400"/>
                              <span
                                  className="text-xs font-semibold text-blue-700 dark:text-blue-300 uppercase tracking-wider">写作统计</span>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                              {[
                                  {label: '字数', value: stats.chars.toLocaleString()},
                                  {label: '词数', value: stats.words.toLocaleString()},
                                  {label: '段落', value: stats.paragraphs.toString()},
                                  {label: '阅读时间', value: `${stats.readingTime} 分钟`},
                              ].map(s => (
                                  <div key={s.label} className="text-center">
                                      <div className="text-lg font-bold text-gray-900 dark:text-white">{s.value}</div>
                                      <div
                                          className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider">{s.label}</div>
                                  </div>
                              ))}
                          </div>
                      </div>

                      {/* Collaborators */}
                      {collabActive && (
                          <Section icon={Users} title="协作者" badge={collab.collaborators.length}>
                              <div className="space-y-2">
                                  {collab.collaborators.map((c, i) => (
                                      <div key={c.client_id || i}
                                           className="flex items-center gap-2.5 p-2 rounded-lg bg-gray-50 dark:bg-gray-800">
                                          <div
                                              className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
                                              style={{backgroundColor: c.color || '#339af0'}}>
                                              {(c.user_name || '?').charAt(0).toUpperCase()}
                                          </div>
                                          <div className="flex-1 min-w-0">
                          <span className="text-sm text-gray-700 dark:text-gray-300 truncate block">
                            {c.user_name || `用户 ${c.client_id?.slice(0, 6)}`}
                          </span>
                                          </div>
                                          {c.client_id === collab.collaborators.find(x => x.user_id?.toString() === '0')?.client_id && (
                                              <span
                                                  className="text-[10px] bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded-full">我</span>
                                          )}
                                      </div>
                                  ))}
                                  {collab.connecting && (
                                      <div className="flex items-center gap-2 text-xs text-gray-400 p-2">
                                          <LoaderIcon className="w-3.5 h-3.5 animate-spin"/>连接中...
                                      </div>
                                  )}
                                  {!collab.connected && !collab.connecting && (
                                      <div className="flex items-center gap-2 text-xs text-red-400 p-2">
                                          <WifiOff className="w-3.5 h-3.5"/>已断开
                                      </div>
                                  )}
                                  <button onClick={() => {
                                      const url = `${window.location.origin}/my/posts/edit?id=${articleId}&collab=1`;
                                      navigator.clipboard.writeText(url);
                                  }}
                                          className="w-full px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 flex items-center justify-center gap-1.5 transition-colors">
                                      <Copy className="w-3.5 h-3.5"/>复制邀请链接
                                  </button>
                              </div>
                          </Section>
                      )}

                      {/* Publish Settings */}
                      <Section icon={Eye} title="发布设置">
                          <div className="space-y-3">
                              <label
                                  className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 cursor-pointer group hover:border-blue-200 dark:hover:border-blue-800 transition-colors">
                                  <div className="flex items-center gap-2.5">
                                      {isHidden ? <EyeOff className="w-4 h-4 text-gray-400"/> :
                                          <Eye className="w-4 h-4 text-gray-400"/>}
                                      <span className="text-sm text-gray-700 dark:text-gray-300">公开可见</span>
                                  </div>
                                  <div className="relative">
                                      <input type="checkbox" {...register('hidden')} className="sr-only peer"/>
                                      <div
                                          className="w-10 h-5 bg-gray-200 dark:bg-gray-700 rounded-full peer-checked:bg-blue-600 transition-colors"/>
                                      <div
                                          className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm peer-checked:translate-x-5 transition-transform"/>
                                  </div>
                              </label>
                              <label
                                  className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 cursor-pointer group hover:border-amber-200 dark:hover:border-amber-800 transition-colors">
                                  <div className="flex items-center gap-2.5">
                                      <Crown className="w-4 h-4 text-amber-500"/>
                                      <span className="text-sm text-gray-700 dark:text-gray-300">仅 VIP 可读</span>
                                  </div>
                                  <div className="relative">
                                      <input type="checkbox" {...register('is_vip_only')} className="sr-only peer"/>
                                      <div
                                          className="w-10 h-5 bg-gray-200 dark:bg-gray-700 rounded-full peer-checked:bg-amber-500 transition-colors"/>
                                      <div
                                          className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm peer-checked:translate-x-5 transition-transform"/>
                                  </div>
                              </label>
                          </div>
                      </Section>

                      {/* Category */}
                      <Section icon={FolderTree} title="分类">
                          <select {...register('category_id')}
                                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white transition-all appearance-none cursor-pointer">
                              <option value="">选择分类</option>
                              {categories?.map((c: Category) => <option key={c.id} value={c.id}>{c.name}</option>)}
                          </select>
                      </Section>

                      {/* Tags */}
                      <Section icon={Hash} title="标签">
                          <div className="relative">
                              <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                              <input {...register('tags')} placeholder="标签，逗号分隔"
                                     className="w-full pl-9 pr-3 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white placeholder-gray-400 transition-all"/>
                          </div>
                      </Section>

                      {/* Cover Image */}
                      <Section icon={Image} title="封面图">
                        <CoverImageUploader
                          value={coverImage}
                          onChange={(url) => setValue('cover_image', url)}
                        />
                      </Section>

                      {/* Excerpt */}
                      <Section icon={FileText} title="摘要">
                <textarea {...register('excerpt')} rows={4} placeholder="简短描述文章内容..."
                          className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white placeholder-gray-400 resize-none transition-all"/>
                          <div className="flex justify-end mt-1">
                              <span className="text-[10px] text-gray-400">{(watch('excerpt') || '').length}/500</span>
                          </div>
                      </Section>

                      {/* Slug */}
                      <Section icon={Hash} title="URL 别名" defaultOpen={false}>
                          <input {...register('slug')} placeholder="自动生成"
                                 className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white placeholder-gray-400 font-mono text-xs transition-all"/>
                      </Section>
                  </div>
          </aside>
        )}
      </div>

          {/* ===== Status Bar ===== */}
          {!focusMode && (
              <footer
                  className="flex items-center justify-between px-4 h-8 border-t border-gray-200/80 dark:border-gray-800/80 bg-white/80 dark:bg-gray-950/80 backdrop-blur-sm flex-shrink-0 text-xs text-gray-400">
                  <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1"><Type className="w-3 h-3"/>{stats.chars} 字</span>
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3"/>约 {stats.readingTime} 分钟阅读</span>
                      {mode === 'edit' &&
                          <span className="flex items-center gap-1"><FileText className="w-3 h-3"/>编辑模式</span>}
                      {collabActive &&
                          <span className="flex items-center gap-1 text-emerald-500"><Wifi className="w-3 h-3"/>实时协作</span>}
                  </div>
                  <div className="flex items-center gap-4">
                      <span>FastBlog Editor</span>
                  </div>
              </footer>
          )}

          {/* ===== Revisions Sidebar ===== */}
      {mode === 'edit' && articleId && (
        <RevisionsSidebar articleId={articleId} open={showRevisions}
          onClose={() => setShowRevisions(false)}
          onCollapse={() => setShowRevisions(false)}
                          onRestore={(c, t, e) => {
                              setContent(c);
                              setValue('title', t);
                              setValue('excerpt', e);
                              setShowRevisions(false);
                          }}/>
      )}

          {/* ===== Keyboard Shortcuts Modal ===== */}
          {showShortcuts && <ShortcutsModal onClose={() => setShowShortcuts(false)}/>}
    </div>
  );
};

const ArticleEditorPage: React.FC<Props> = (props) => (
  <AuthGuard><QueryProvider><ArticleEditorPageInner {...props} /></QueryProvider></AuthGuard>
);
export default ArticleEditorPage;
