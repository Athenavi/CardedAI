'use client';

import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {AnimatePresence, motion} from 'framer-motion';
import {apiClient} from '@/lib/api/base-client';
import {getFullMediaUrl} from '@/lib/utils';
import type {Article} from '@/lib/api/base-types';
import ArticleComments from './ArticleComments';
import {
  ArrowUp,
  Bookmark,
  Calendar,
  Check,
  Clock,
  Copy,
  ExternalLink,
  Eye,
  Hash,
  Heart,
  List,
  Lock,
  MessageSquare,
  Share2,
  Tag,
  X
} from 'lucide-react';

interface Props {
    slug?: string;
}

interface TocItem {
    id: string;
    text: string;
    level: number;
}

const ArticleDetail: React.FC<Props> = ({slug: propSlug}) => {
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
    const [readingProgress, setReadingProgress] = useState(0);
    const [toc, setToc] = useState<TocItem[]>([]);
  const [processedContent, setProcessedContent] = useState('');
    const [activeTocId, setActiveTocId] = useState('');
    const [liked, setLiked] = useState(false);
    const [bookmarked, setBookmarked] = useState(false);
    const [likeCount, setLikeCount] = useState(0);
    const [copied, setCopied] = useState(false);
    const [showToc, setShowToc] = useState(false);
    const [relatedArticles, setRelatedArticles] = useState<any[]>([]);
    const contentRef = useRef<HTMLDivElement>(null);

  // Password protection state
  const [requiresPassword, setRequiresPassword] = useState(false);
  const [passwordData, setPasswordData] = useState<{
    article_id: number;
    article_title: string;
    excerpt: string
  } | null>(null);
  const [passwordInput, setPasswordInput] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);

    // Load article
  useEffect(() => {
    const slug = propSlug || (typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('slug') : '') || '';
      if (!slug) {
      setError('缺少文章参数');
      setLoading(false);
          return;
    }

    const fetchArticle = async (accessToken?: string) => {
      try {
        const path = accessToken
          ? `/articles/p/${slug}?access_token=${encodeURIComponent(accessToken)}`
          : `/articles/p/${slug}`;
        const res = await apiClient.get(path);

        // Check if password required
        if (!res.success && res.data?.requires_password) {
          setRequiresPassword(true);
          setPasswordData(res.data);
          setLoading(false);
          return;
        }

        if (res.success && res.data) {
            const data = res.data.article || res.data as any;
            setArticle(data);
            setLikeCount(data.likes || 0);

            // Extract TOC from content
            if (data.content) {
              processContentWithToc(data.content);
            }

            // Fetch related articles
            if (data.category_id || data.id) {
                try {
                  const relRes = await apiClient.get('/articles', {
                        per_page: 4,
                        exclude: data.id,
                        category_id: data.category_id
                    });
                    if (relRes.success && relRes.data) {
                        const articles = relRes.data.data || relRes.data || [];
                      setRelatedArticles(articles.filter((a) => a.id !== data.id).slice(0, 3));
                    }
                } catch {
                }
            }
        } else {
          setError(res.error || '文章不存在');
        }
      } catch (err) {
        setError('加载失败，请稍后重试');
      } finally {
        setLoading(false);
      }
    };

    // 尝试从 localStorage 或 URL query 获取 access_token
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('access_token');
    let storedToken: string | null = null;
    try {
      // 尝试匹配当前 slug 对应的文章密码 token
      const allKeys = Object.keys(localStorage).filter(k => k.startsWith('article_access_'));
      for (const key of allKeys) {
        const val = localStorage.getItem(key);
        if (val) {
          storedToken = val;
          break;
        }
      }
    } catch {
    }
    const tokenToUse = urlToken || storedToken || undefined;
    fetchArticle(tokenToUse);
  }, [propSlug]);

  // Handle password verification
  const handlePasswordSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordData || !passwordInput.trim()) {
      setPasswordError('请输入密码');
      return;
    }
    if (passwordInput.length < 4) {
      setPasswordError('密码至少 4 位');
      return;
    }

    setPasswordLoading(true);
    setPasswordError('');

    try {
      const res = await apiClient.post(`/articles/${passwordData.article_id}/verify`, {password: passwordInput});
      if (res.success && res.data?.access_token) {
        // Store access token in localStorage (cross-origin compatible)
        try {
          localStorage.setItem(`article_access_${passwordData.article_id}`, res.data.access_token);
        } catch {
        }
        // Reset password state and refetch
        setRequiresPassword(false);
        setPasswordData(null);
        setPasswordInput('');
        setLoading(true);
        const slug = propSlug || (typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('slug') : '');
        const artRes = await apiClient.get(`/articles/p/${slug}?access_token=${encodeURIComponent(res.data.access_token)}`);
        if (artRes.success && artRes.data) {
          const data = artRes.data.article || artRes.data as any;
          setArticle(data);
          setLikeCount(data.likes || 0);
          if (data.content) processContentWithToc(data.content);
          if (data.category_id || data.id) {
            try {
              const relRes = await apiClient.get('/articles', {
                per_page: 4,
                exclude: data.id,
                category_id: data.category_id
              });
              if (relRes.success && relRes.data) {
                const articles = relRes.data.data || relRes.data || [];
                setRelatedArticles(articles.filter((a: any) => a.id !== data.id).slice(0, 3));
              }
            } catch {
            }
          }
        } else {
          setError(artRes.error || '加载失败');
        }
      } else {
        setPasswordError(res.error || '密码错误，请重试');
      }
    } catch {
      setPasswordError('验证失败，请稍后重试');
    } finally {
      setLoading(false);
      setPasswordLoading(false);
    }
  }, [passwordData, passwordInput, propSlug]);

  // Process content: inject heading IDs directly into HTML string for reliable TOC scrolling
  const processContentWithToc = useCallback((html: string) => {
        const items: TocItem[] = [];
    let index = 0;
    const processed = html.replace(/<h([1-4])([^>]*)>([\s\S]*?)<\/h\1>/gi, (match, level, attrs, content) => {
      const id = `heading-${index}`;
      // Extract text content from inner HTML (strip tags)
      const text = content.replace(/<[^>]*>/g, '').trim();
      items.push({id, text, level: parseInt(level)});
      // Avoid duplicate id attribute
      const cleanAttrs = attrs.replace(/\s*id\s*=\s*["'][^"']*["']/gi, '');
      const result = `<h${level}${cleanAttrs} id="${id}">${content}</h${level}>`;
      index++;
      return result;
        });
        setToc(items);
    setProcessedContent(processed);
    }, []);

    // Reading progress & active TOC tracking
    useEffect(() => {
        const handleScroll = () => {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            setReadingProgress(docHeight > 0 ? Math.min(scrollTop / docHeight * 100, 100) : 0);

            // Track active TOC item
            if (toc.length > 0) {
                const headings = document.querySelectorAll('[id^="heading-"]');
                let current = '';
                headings.forEach(h => {
                    const rect = h.getBoundingClientRect();
                    if (rect.top <= 120) current = h.id;
                });
                setActiveTocId(current);
            }
        };

        window.addEventListener('scroll', handleScroll, {passive: true});
        return () => window.removeEventListener('scroll', handleScroll);
    }, [toc]);

    // Calculate reading time
    const readingTime = useMemo(() => {
        if (!article?.content) return 1;
        const text = article.content.replace(/<[^>]*>/g, '');
        const words = text.length;
        return Math.max(1, Math.ceil(words / 400)); // ~400 chars per minute for Chinese
    }, [article?.content]);

    // Format date
    const formatDate = (dateStr: string) => {
        const d = new Date(dateStr);
        return d.toLocaleDateString('zh-CN', {year: 'numeric', month: 'long', day: 'numeric'});
    };

  // TOC click handler - reliable scroll in SPA
  const handleTocClick = useCallback((e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({behavior: 'smooth', block: 'start'});
      // Update URL hash without triggering navigation
      history.replaceState(null, '', `#${id}`);
    }
  }, []);

    // Share handlers
    const handleCopyLink = () => {
        navigator.clipboard.writeText(window.location.href);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleShareTwitter = () => {
        const text = `${article?.title} ${window.location.href}`;
        window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, '_blank');
    };

    // ═══ Loading State ═══
    if (loading) return (
        <div className="min-h-screen">
            {/* Reading progress skeleton */}
            <div className="fixed top-0 left-0 h-1 bg-gray-100 dark:bg-gray-800 w-full z-[99998]"/>
            <div className="max-w-4xl mx-auto px-4 py-12">
                <div className="space-y-4 mb-8">
                    <div className="h-4 w-24 skeleton rounded"/>
                    <div className="h-12 w-full skeleton rounded-xl"/>
                    <div className="h-6 w-2/3 skeleton rounded-lg"/>
                    <div className="flex gap-4">
                        <div className="h-4 w-32 skeleton rounded"/>
                        <div className="h-4 w-20 skeleton rounded"/>
                    </div>
                </div>
                <div className="aspect-[16/9] skeleton rounded-2xl mb-10"/>
                <div className="space-y-4">
                    {[...Array(8)].map((_, i) => <div key={i} className="h-4 skeleton rounded"
                                                      style={{width: `${70 + Math.random() * 30}%`}}/>)}
                </div>
            </div>
        </div>
    );

  // ═══ Password Required State ═══
  if (requiresPassword && passwordData) return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <motion.div
        initial={{opacity: 0, y: 20}}
        animate={{opacity: 1, y: 0}}
        transition={{duration: 0.4}}
        className="w-full max-w-md"
      >
        <div
          className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          {/* Header */}
          <div className="p-8 pb-6 text-center border-b border-gray-100 dark:border-gray-800">
            <div
              className="w-16 h-16 rounded-2xl bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-amber-500 dark:text-amber-400"/>
            </div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-1">需要密码访问</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">此文章已加密保护，请输入访问密码</p>
            {passwordData.article_title && (
              <p
                className="mt-3 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800/50 rounded-lg px-3 py-2">
                {passwordData.article_title}
              </p>
            )}
            {passwordData.excerpt && (
              <p className="mt-2 text-xs text-gray-400 dark:text-gray-500 line-clamp-2">
                {passwordData.excerpt}
              </p>
            )}
          </div>

          {/* Form */}
          <form onSubmit={handlePasswordSubmit} className="p-8 pt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">访问密码</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => {
                    setPasswordInput(e.target.value);
                    setPasswordError('');
                  }}
                  placeholder="请输入文章访问密码"
                  autoFocus
                  className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 transition-all ${
                    passwordError
                      ? 'border-red-300 dark:border-red-600 focus:ring-red-500/20 focus:border-red-500'
                      : 'border-gray-200 dark:border-gray-700 focus:ring-blue-500/20 focus:border-blue-500'
                  }`}
                />
              </div>
              {passwordError && (
                <p className="mt-1.5 text-xs text-red-500 dark:text-red-400">{passwordError}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={passwordLoading || !passwordInput.trim()}
              className="w-full py-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium rounded-xl hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {passwordLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"/>
                  验证中...
                </>
              ) : '验证密码'}
            </button>

            <a href="/articles"
               className="block text-center text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors">
              返回文章列表
            </a>
          </form>
        </div>
      </motion.div>
    </div>
  );

    // ═══ Error State ═══
  if (error || !article) return (
      <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
          <div
              className="w-20 h-20 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-6">
              <MessageSquare className="w-10 h-10 text-gray-300 dark:text-gray-600"/>
          </div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">{error || '文章不存在'}</h1>
        <p className="text-gray-500 dark:text-gray-400 mb-6">请检查链接是否正确，或浏览其他文章</p>
          <a href="/articles" className="btn-primary">返回文章列表</a>
      </div>
    </div>
  );

    // ═══ Extract tags ═══
    const tags: string[] = article.tags || [];

  return (
      <>
          {/* ═══ Reading Progress Bar ═══ */}
          <div
              className="reading-progress"
              style={{width: `${readingProgress}%`}}
          />

          {/* ═══ Main Layout ═══ */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 lg:py-12">
              <div className="flex gap-8 lg:gap-12">
                  {/* ── Left Sidebar: TOC (Desktop) ── */}
                  {toc.length > 2 && (
                      <aside className="hidden xl:block w-56 flex-shrink-0">
                          <div className="sticky top-24">
                              <div
                                  className="flex items-center gap-2 mb-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                  <List className="w-4 h-4"/>
                                  目录
                              </div>
                              <nav className="space-y-0.5 max-h-[60vh] overflow-y-auto">
                                  {toc.map(item => (
                                      <a
                                          key={item.id}
                                          href={`#${item.id}`}
                                          onClick={(e) => handleTocClick(e, item.id)}
                                          className={`toc-link ${activeTocId === item.id ? 'active' : ''}`}
                                          style={{paddingLeft: `${(item.level - 1) * 12 + 12}px`}}
                                      >
                                          {item.text}
                                      </a>
                                  ))}
                              </nav>
                          </div>
                      </aside>
                  )}

                  {/* ── Article Content ── */}
                  <article className="flex-1 min-w-0 max-w-3xl">
                      {/* Breadcrumb */}
                      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
                          <a href="/" className="hover:text-blue-600 transition-colors">首页</a>
                          <span>/</span>
                          <a href="/articles" className="hover:text-blue-600 transition-colors">文章</a>
                          {article.category && (
                              <>
                                  <span>/</span>
                                <span className="text-gray-500 dark:text-gray-400">{article.category?.name}</span>
                              </>
                          )}
                      </div>

                      {/* Title & Meta */}
                      <header className="mb-8">
                          {tags.length > 0 && (
                              <div className="flex flex-wrap gap-2 mb-4">
                                  {tags.slice(0, 3).map(tag => (
                                      <a
                                          key={tag}
                                          href={`/search?q=${encodeURIComponent(tag)}`}
                                          className="badge badge-blue"
                                      >
                                          <Hash className="w-3 h-3 mr-0.5"/>
                                          {tag}
                                      </a>
                                  ))}
                              </div>
                          )}

                          <h1 className="text-3xl sm:text-4xl lg:text-[2.75rem] font-extrabold text-gray-900 dark:text-white leading-tight tracking-tight mb-5">
                              {article.title}
                          </h1>

                          {article.excerpt && (
                              <p className="text-lg text-gray-500 dark:text-gray-400 leading-relaxed mb-6">
                                  {article.excerpt}
                              </p>
                          )}

                          {/* Author & Meta Bar */}
                          <div
                              className="flex flex-wrap items-center gap-4 py-4 border-y border-gray-100 dark:border-gray-800">
                              {/* Author */}
                              {article.author && (
                                  <div className="flex items-center gap-2.5">
                                      {article.author.avatar ? (
                                          <img src={article.author.avatar} alt=""
                                               className="w-9 h-9 rounded-full ring-2 ring-gray-100 dark:ring-gray-800"/>
                                      ) : (
                                          <div
                                              className="w-9 h-9 rounded-full gradient-primary flex items-center justify-center text-white text-sm font-bold">
                                              {(article.author.username || 'U')[0].toUpperCase()}
                                          </div>
                                      )}
                                      <div>
                                          <p className="text-sm font-semibold text-gray-900 dark:text-white">{article.author.username}</p>
                                      </div>
                                  </div>
                              )}

                            <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 ml-auto">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-4 h-4"/>
                      {formatDate(article.created_at)}
                  </span>
                                  <span className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4"/>
                                      {readingTime} 分钟阅读
                  </span>
                                  <span className="flex items-center gap-1.5">
                    <Eye className="w-4 h-4"/>
                                      {article.views || 0}
                  </span>
                              </div>
                          </div>
                      </header>

                      {/* Cover Image */}
                      {article.cover_image && (
                          <div className="mb-10 rounded-2xl overflow-hidden">
                              <img
                                src={getFullMediaUrl(article.cover_image)}
                                  alt={article.title}
                                  className="w-full h-auto object-cover"
                                  loading="eager"
                                  fetchPriority="high"
                              />
                          </div>
                      )}

                    {/* Content (IDs pre-injected by processContentWithToc) */}
                      <div ref={contentRef} className="prose-custom mb-12">
                        <div
                          dangerouslySetInnerHTML={{__html: processedContent || article.content || '<p>暂无内容</p>'}}/>
                      </div>

                      {/* ── Article Footer ── */}
                      <div className="border-t border-gray-100 dark:border-gray-800 pt-8 mb-12">
                          {/* Tags */}
                          {tags.length > 0 && (
                              <div className="flex items-center gap-2 mb-6">
                                  <Tag className="w-4 h-4 text-gray-400"/>
                                  <div className="flex flex-wrap gap-2">
                                      {tags.map(tag => (
                                          <a
                                              key={tag}
                                              href={`/search?q=${encodeURIComponent(tag)}`}
                                              className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                                          >
                                              {tag}
                                          </a>
                                      ))}
                                  </div>
                              </div>
                          )}

                          {/* Action Buttons */}
                          <div className="flex items-center gap-3 flex-wrap">
                              {/* Like */}
                              <button
                                  onClick={() => {
                                      setLiked(!liked);
                                      setLikeCount(prev => liked ? prev - 1 : prev + 1);
                                  }}
                                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl border transition-all text-sm font-medium ${
                                      liked
                                          ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400'
                                          : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-red-200 hover:text-red-500'
                                  }`}
                              >
                                  <Heart className={`w-4 h-4 ${liked ? 'fill-current' : ''}`}/>
                                  <span>{likeCount || '点赞'}</span>
                              </button>

                              {/* Bookmark */}
                              <button
                                  onClick={() => setBookmarked(!bookmarked)}
                                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl border transition-all text-sm font-medium ${
                                      bookmarked
                                          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400'
                                          : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-blue-200 hover:text-blue-500'
                                  }`}
                              >
                                  <Bookmark className={`w-4 h-4 ${bookmarked ? 'fill-current' : ''}`}/>
                                  <span>{bookmarked ? '已收藏' : '收藏'}</span>
                              </button>

                              {/* Share */}
                              <div className="relative group">
                                  <button
                                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-green-200 hover:text-green-500 transition-all text-sm font-medium">
                                      <Share2 className="w-4 h-4"/>
                                      <span>分享</span>
                                  </button>
                                  <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block">
                                      <div
                                          className="bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-2 flex gap-1 whitespace-nowrap">
                                          <button
                                              onClick={handleCopyLink}
                                              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                                          >
                                              {copied ? <Check className="w-4 h-4 text-green-500"/> :
                                                  <Copy className="w-4 h-4"/>}
                                              {copied ? '已复制' : '复制链接'}
                                          </button>
                                          <button
                                              onClick={handleShareTwitter}
                                              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                                          >
                                              <ExternalLink className="w-4 h-4"/>
                                              Twitter
                                          </button>
                                      </div>
                                  </div>
                              </div>
                          </div>
                      </div>

                      {/* ── Related Articles ── */}
                      {relatedArticles.length > 0 && (
                          <div className="mb-12">
                              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
                                  <span className="w-1 h-5 gradient-primary rounded-full"/>
                                  相关推荐
                              </h2>
                              <div className="grid sm:grid-cols-3 gap-4">
                                {relatedArticles.map((a) => (
                                      <a
                                          key={a.id}
                                          href={`/view?slug=${a.slug}`}
                                          className="group p-4 rounded-xl border border-gray-100 dark:border-gray-800 hover:border-blue-200 dark:hover:border-blue-800 transition-all card-hover"
                                      >
                                          {a.cover_image && (
                                              <div
                                                  className="aspect-[16/10] rounded-lg overflow-hidden mb-3 bg-gray-50 dark:bg-gray-800">
                                                <img src={getFullMediaUrl(a.cover_image)} alt=""
                                                       className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                                       loading="lazy"/>
                                              </div>
                                          )}
                                          <h3 className="font-semibold text-sm text-gray-900 dark:text-white line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                              {a.title}
                                          </h3>
                                          <div className="flex items-center gap-2 text-xs text-gray-400 mt-2">
                                              <span className="flex items-center gap-1"><Eye
                                                  className="w-3 h-3"/>{a.views || 0}</span>
                                              <span>{a.created_at ? new Date(a.created_at).toLocaleDateString('zh-CN') : ''}</span>
                                          </div>
                                      </a>
                                  ))}
                              </div>
                          </div>
                      )}

                      {/* ── Comments ── */}
                      {article.id && <ArticleComments articleId={article.id}/>}
                  </article>

                  {/* ── Right Sidebar ── */}
                  <aside className="hidden lg:block w-64 flex-shrink-0">
                      <div className="sticky top-24 space-y-6">
                          {/* TOC for medium screens */}
                          {toc.length > 2 && (
                              <div className="xl:hidden">
                                  <div
                                      className="flex items-center gap-2 mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                      <List className="w-4 h-4"/>
                                      目录
                                  </div>
                                  <nav className="space-y-0.5 max-h-[40vh] overflow-y-auto">
                                      {toc.map(item => (
                                          <a
                                              key={item.id}
                                              href={`#${item.id}`}
                                              onClick={(e) => handleTocClick(e, item.id)}
                                              className={`toc-link ${activeTocId === item.id ? 'active' : ''}`}
                                              style={{paddingLeft: `${(item.level - 1) * 12 + 12}px`}}
                                          >
                                              {item.text}
                                          </a>
                                      ))}
                                  </nav>
                              </div>
                          )}

                          {/* Author Card */}
                          {article.author && (
                              <div
                                  className="p-5 rounded-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900">
                                  <div className="flex items-center gap-3 mb-3">
                                      {article.author.avatar ? (
                                          <img src={article.author.avatar} alt="" className="w-10 h-10 rounded-full"/>
                                      ) : (
                                          <div
                                              className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center text-white font-bold">
                                              {(article.author.username || 'U')[0].toUpperCase()}
                                          </div>
                                      )}
                                      <div>
                                          <p className="font-semibold text-gray-900 dark:text-white text-sm">{article.author.username}</p>
                                          <p className="text-xs text-gray-400">作者</p>
                                      </div>
                                  </div>
                                  <a href={`/profile?user=${article.author.username}`}
                                     className="btn-secondary text-xs w-full !py-2 text-center block">
                                      查看主页
                                  </a>
                              </div>
                          )}

                          {/* Quick Actions */}
                          <div
                              className="p-5 rounded-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900">
                              <button
                                  onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})}
                                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors"
                              >
                                  <ArrowUp className="w-4 h-4"/>
                                  回到顶部
                              </button>
                              <button
                                  onClick={handleCopyLink}
                                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors"
                              >
                                  {copied ? <Check className="w-4 h-4 text-green-500"/> : <Copy className="w-4 h-4"/>}
                                  {copied ? '已复制链接' : '复制文章链接'}
                              </button>
                          </div>
                      </div>
                  </aside>
              </div>
          </div>

          {/* Mobile TOC Toggle */}
          {toc.length > 2 && (
              <button
                  onClick={() => setShowToc(!showToc)}
                  className="fixed bottom-24 right-6 z-50 xl:hidden w-11 h-11 rounded-full bg-white dark:bg-gray-900 shadow-lg border border-gray-200 dark:border-gray-700 flex items-center justify-center text-gray-600 dark:text-gray-400"
                  title="目录"
              >
                  <List className="w-5 h-5"/>
              </button>
          )}

          {/* Mobile TOC Panel */}
          <AnimatePresence>
              {showToc && toc.length > 2 && (
                  <>
                      {/* Backdrop */}
                      <motion.div
                          initial={{opacity: 0}}
                          animate={{opacity: 1}}
                          exit={{opacity: 0}}
                          className="fixed inset-0 bg-black/40 z-[99998] xl:hidden"
                          onClick={() => setShowToc(false)}
                      />
                      <motion.div
                          initial={{opacity: 0, x: 300}}
                          animate={{opacity: 1, x: 0}}
                          exit={{opacity: 0, x: 300}}
                          transition={{type: 'spring', damping: 25, stiffness: 300}}
                          className="fixed right-0 top-0 bottom-0 w-72 z-[99999] bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-700 p-6 overflow-y-auto xl:hidden safe-top"
                          style={{paddingBottom: 'env(safe-area-inset-bottom, 0px)'}}
                      >
                          <div className="flex items-center justify-between mb-4">
                              <h3 className="font-semibold text-gray-900 dark:text-white">目录</h3>
                              <button onClick={() => setShowToc(false)}
                                      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 min-w-[44px] min-h-[44px] flex items-center justify-center">
                                  <X className="w-5 h-5 text-gray-400"/>
                              </button>
                          </div>
                          <nav className="space-y-0.5">
                              {toc.map(item => (
                                  <a
                                      key={item.id}
                                      href={`#${item.id}`}
                                      onClick={(e) => {
                                        handleTocClick(e, item.id);
                                        setShowToc(false);
                                      }}
                                      className={`toc-link ${activeTocId === item.id ? 'active' : ''}`}
                                      style={{paddingLeft: `${(item.level - 1) * 12 + 12}px`}}
                                  >
                                      {item.text}
                                  </a>
                              ))}
                          </nav>
                      </motion.div>
                  </>
              )}
          </AnimatePresence>
      </>
  );
};

export default ArticleDetail;
