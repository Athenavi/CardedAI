'use client';

import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {AnimatePresence, motion} from 'framer-motion';
import {ArticleService} from '@/lib/api';
import {getFullMediaUrl} from '@/lib/utils';
import type {Article} from '@/lib/api/base-types';
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Clock,
  Eye,
  Filter,
  Grid,
  Hash,
  Heart,
  List,
  Search,
  SlidersHorizontal,
  X
} from 'lucide-react';

type ViewMode = 'grid' | 'list';
type SortBy = 'newest' | 'oldest' | 'popular' | 'views';

const ArticleList: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [viewMode, setViewMode] = useState<ViewMode>('grid');
    const [sortBy, setSortBy] = useState<SortBy>('newest');
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [selectedTag, setSelectedTag] = useState<string | null>(null);
    const [showFilters, setShowFilters] = useState(false);
    const perPage = 12;

    // Fetch articles
    const fetchArticles = useCallback(async () => {
        setLoading(true);
        try {
            const res = await ArticleService.getArticles({
                page: currentPage,
                per_page: perPage,
                search: searchQuery || undefined,
            } as any);
            if (res.success && res.data) {
                const d = res.data as any;
                setArticles(d.data || d.articles || []);
                setTotalPages(d.pagination?.total_pages || d.total_pages || Math.ceil((d.pagination?.total || d.total || 0) / perPage));
                setTotalCount(d.pagination?.total || d.total || 0);
            }
        } catch {
        } finally {
            setLoading(false);
        }
    }, [currentPage, searchQuery, sortBy, selectedTag]);

    useEffect(() => {
        fetchArticles();
    }, [fetchArticles]);

    // Debounced search
    const [searchInput, setSearchInput] = useState('');
  useEffect(() => {
      const timer = setTimeout(() => {
          setSearchQuery(searchInput);
          setCurrentPage(1);
      }, 400);
      return () => clearTimeout(timer);
  }, [searchInput]);

    // All unique tags from articles
    const allTags = useMemo(() => {
        const tags = new Set<string>();
        articles.forEach(a => (a.tags || []).forEach(t => tags.add(t)));
        return Array.from(tags).slice(0, 10);
    }, [articles]);

    // Sort options
    const sortOptions: { value: SortBy; label: string }[] = [
        {value: 'newest', label: '最新发布'},
        {value: 'oldest', label: '最早发布'},
        {value: 'popular', label: '最受欢迎'},
        {value: 'views', label: '浏览最多'},
    ];

    // ═══ Skeleton ═══
    const ArticleSkeleton = ({mode}: { mode: ViewMode }) => {
        if (mode === 'list') {
            return (
                <div className="flex gap-4 p-5 rounded-2xl border border-gray-100 dark:border-gray-800">
                    <div className="w-32 h-24 skeleton rounded-xl flex-shrink-0"/>
                    <div className="flex-1 space-y-2">
                        <div className="h-3 w-16 skeleton rounded"/>
                        <div className="h-5 w-3/4 skeleton rounded"/>
                        <div className="h-3 w-full skeleton rounded"/>
                    </div>
                </div>
            );
        }
        return (
            <div className="rounded-2xl overflow-hidden border border-gray-100 dark:border-gray-800">
                <div className="aspect-[16/10] skeleton"/>
                <div className="p-5 space-y-3">
                    <div className="h-3 w-16 skeleton rounded"/>
                    <div className="h-5 skeleton rounded"/>
                    <div className="h-3 w-3/4 skeleton rounded"/>
                </div>
            </div>
        );
    };

  return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 lg:py-12">
          {/* ═══ Header ═══ */}
          <div className="mb-8">
              <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-2">文章</h1>
              <p className="text-gray-500 dark:text-gray-400">浏览所有发布的文章内容</p>
          </div>

          {/* ═══ Toolbar ═══ */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-8">
              {/* Search */}
              <div className="relative flex-1 w-full sm:max-w-md">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                  <input
                      type="text"
                      value={searchInput}
                      onChange={e => setSearchInput(e.target.value)}
                      placeholder="搜索文章..."
                      className="input-base !pl-10 !pr-10"
                  />
                  {searchInput && (
                      <button
                          onClick={() => setSearchInput('')}
                          className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
                      >
                          <X className="w-4 h-4 text-gray-400"/>
                      </button>
                  )}
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                  {/* Sort */}
                  <select
                      value={sortBy}
                      onChange={e => {
                          setSortBy(e.target.value as SortBy);
                          setCurrentPage(1);
                      }}
                      className="input-base !w-auto !py-2 text-sm cursor-pointer"
                  >
                      {sortOptions.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                  </select>

                  {/* Filter toggle */}
                  <button
                      onClick={() => setShowFilters(!showFilters)}
                      className={`p-2.5 rounded-xl border transition-colors ${showFilters ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-600' : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'}`}
                  >
                      <SlidersHorizontal className="w-4 h-4"/>
                  </button>

                  {/* View mode */}
                  <div
                      className="flex items-center border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
                      <button
                          onClick={() => setViewMode('grid')}
                          className={`p-2.5 transition-colors ${viewMode === 'grid' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
                      >
                          <Grid className="w-4 h-4"/>
                      </button>
                      <button
                          onClick={() => setViewMode('list')}
                          className={`p-2.5 transition-colors ${viewMode === 'list' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
                      >
                          <List className="w-4 h-4"/>
                      </button>
                  </div>
              </div>
          </div>

          {/* ═══ Tag Filters ═══ */}
          <AnimatePresence>
              {showFilters && (
                  <motion.div
                      initial={{height: 0, opacity: 0}}
                      animate={{height: 'auto', opacity: 1}}
                      exit={{height: 0, opacity: 0}}
                      transition={{duration: 0.2}}
                      className="overflow-hidden mb-6"
                  >
                      <div
                          className="p-4 rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50">
                          <div className="flex items-center gap-2 mb-3">
                              <Filter className="w-4 h-4 text-gray-400"/>
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">标签筛选</span>
                              {selectedTag && (
                                  <button
                                      onClick={() => {
                                          setSelectedTag(null);
                                          setCurrentPage(1);
                                      }}
                                      className="text-xs text-blue-600 hover:text-blue-700 ml-auto"
                                  >
                                      清除筛选
                                  </button>
                              )}
                          </div>
                          <div className="flex flex-wrap gap-2">
                              {allTags.map(tag => (
                                  <button
                                      key={tag}
                                      onClick={() => {
                                          setSelectedTag(selectedTag === tag ? null : tag);
                                          setCurrentPage(1);
                                      }}
                                      className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors ${
                                          selectedTag === tag
                                              ? 'bg-blue-600 text-white'
                                              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
                                      }`}
                                  >
                                      <Hash className="w-3 h-3 inline mr-0.5"/>
                                      {tag}
                                  </button>
                              ))}
                          </div>
                      </div>
                  </motion.div>
              )}
          </AnimatePresence>

          {/* ═══ Results Count ═══ */}
          {!loading && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                  {totalCount > 0
                      ? `共 ${totalCount} 篇文章${searchQuery ? ` · 搜索 "${searchQuery}"` : ''}${selectedTag ? ` · 标签 "${selectedTag}"` : ''}`
                      : '未找到相关文章'
                  }
              </p>
          )}

          {/* ═══ Articles Grid / List ═══ */}
          {loading ? (
              <div className={viewMode === 'grid'
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
                  : 'space-y-4'
              }>
                  {[...Array(6)].map((_, i) => <ArticleSkeleton key={i} mode={viewMode}/>)}
              </div>
          ) : articles.length === 0 ? (
              <div className="text-center py-20">
                  <BookOpen className="w-16 h-16 text-gray-200 dark:text-gray-700 mx-auto mb-4"/>
                <h3 className="text-lg font-semibold text-gray-500 dark:text-gray-400 mb-2">暂无文章</h3>
                  <p className="text-sm text-gray-400">
                      {searchQuery ? '尝试换个关键词搜索' : '还没有发布任何文章'}
                  </p>
              </div>
          ) : viewMode === 'grid' ? (
              /* ── Grid View ── */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {articles.map((article, i) => (
                      <motion.a
                          key={article.id}
                          initial={{opacity: 0, y: 20}}
                          animate={{opacity: 1, y: 0}}
                          transition={{delay: i * 0.05, duration: 0.4}}
                          href={`/view?slug=${article.slug}`}
                          className="group bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden card-hover"
                      >
                          {/* Cover */}
                          <div className="aspect-[16/10] bg-gray-50 dark:bg-gray-800 overflow-hidden relative">
                              {article.cover_image ? (
                                  <img
                                    src={getFullMediaUrl(article.cover_image)}
                                      alt={article.title}
                                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                      loading="lazy"
                                  />
                              ) : (
                                  <div className="w-full h-full flex items-center justify-center">
                                      <BookOpen className="w-8 h-8 text-gray-200 dark:text-gray-700"/>
                                  </div>
                              )}
                              {article.category && (
                                  <div className="absolute top-3 left-3">
                    <span
                        className="badge bg-white/90 dark:bg-gray-900/90 text-gray-700 dark:text-gray-300 backdrop-blur-sm text-[10px]">
                      {article.category?.name || ''}
                    </span>
                                  </div>
                              )}
                          </div>
                          {/* Content */}
                          <div className="p-5">
                              <div className="flex items-center gap-2 text-xs text-gray-400 mb-2.5">
                                  {article.tags?.[0] && (
                                      <span
                                          className="text-blue-600 dark:text-blue-400 font-medium flex items-center gap-0.5">
                      <Hash className="w-3 h-3"/>{article.tags[0]}
                    </span>
                                  )}
                                  <span>·</span>
                                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3"/>
                                      {article.created_at ? new Date(article.created_at).toLocaleDateString('zh-CN') : ''}
                  </span>
                              </div>
                              <h3 className="font-semibold text-gray-900 dark:text-white text-sm line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors leading-relaxed mb-2">
                                  {article.title}
                              </h3>
                              <p className="text-xs text-gray-400 line-clamp-2 mb-3">{article.excerpt || article.summary || ''}</p>
                              <div className="flex items-center justify-between text-xs text-gray-400">
                                  <div className="flex items-center gap-3">
                                      <span className="flex items-center gap-1"><Eye
                                          className="w-3 h-3"/>{article.views || 0}</span>
                                      <span className="flex items-center gap-1"><Heart
                                          className="w-3 h-3"/>{article.likes || 0}</span>
                                  </div>
                              </div>
                          </div>
                      </motion.a>
                  ))}
              </div>
          ) : (
              /* ── List View ── */
              <div className="space-y-4">
                  {articles.map((article, i) => (
                      <motion.a
                          key={article.id}
                          initial={{opacity: 0, x: -20}}
                          animate={{opacity: 1, x: 0}}
                          transition={{delay: i * 0.03, duration: 0.4}}
                          href={`/view?slug=${article.slug}`}
                          className="group flex gap-5 p-5 bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 card-hover"
                      >
                          {/* Cover */}
                          <div
                              className="w-40 h-28 rounded-xl overflow-hidden bg-gray-50 dark:bg-gray-800 flex-shrink-0 hidden sm:block">
                              {article.cover_image ? (
                                  <img
                                    src={getFullMediaUrl(article.cover_image)}
                                      alt=""
                                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                      loading="lazy"
                                  />
                              ) : (
                                  <div className="w-full h-full flex items-center justify-center">
                                      <BookOpen className="w-6 h-6 text-gray-200 dark:text-gray-700"/>
                                  </div>
                              )}
                          </div>
                          {/* Content */}
                          <div className="flex-1 min-w-0 flex flex-col justify-center">
                              <div className="flex items-center gap-2 text-xs text-gray-400 mb-1.5">
                                  {article.tags?.[0] && (
                                      <span
                                          className="text-blue-600 dark:text-blue-400 font-medium">{article.tags[0]}</span>
                                  )}
                                  <span>·</span>
                                  <span>{article.created_at ? new Date(article.created_at).toLocaleDateString('zh-CN') : ''}</span>
                              </div>
                              <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors mb-1">
                                  {article.title}
                              </h3>
                            <p
                              className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{article.excerpt || article.summary || ''}</p>
                              <div className="flex items-center gap-4 text-xs text-gray-400 mt-2">
                                  <span className="flex items-center gap-1"><Eye
                                      className="w-3 h-3"/>{article.views || 0}</span>
                                  <span className="flex items-center gap-1"><Heart
                                      className="w-3 h-3"/>{article.likes || 0}</span>
                              </div>
                          </div>
                      </motion.a>
                  ))}
              </div>
          )}

          {/* ═══ Pagination ═══ */}
          {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-10">
                  <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage <= 1}
                      className="p-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                      <ChevronLeft className="w-4 h-4"/>
                  </button>
                  {/* Page numbers */}
                  {Array.from({length: Math.min(totalPages, 7)}, (_, i) => {
                      let page: number;
                      if (totalPages <= 7) {
                          page = i + 1;
                      } else if (currentPage <= 4) {
                          page = i + 1;
                      } else if (currentPage >= totalPages - 3) {
                          page = totalPages - 6 + i;
                      } else {
                          page = currentPage - 3 + i;
                      }
                      return (
                          <button
                              key={page}
                              onClick={() => setCurrentPage(page)}
                              className={`w-10 h-10 rounded-xl text-sm font-medium transition-colors ${
                                  currentPage === page
                                      ? 'bg-blue-600 text-white shadow-sm'
                                      : 'border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                              }`}
                          >
                              {page}
                          </button>
                      );
                  })}
                  <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage >= totalPages}
                      className="p-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                      <ChevronRight className="w-4 h-4"/>
                  </button>
              </div>
          )}
    </div>
  );
};

export default ArticleList;
