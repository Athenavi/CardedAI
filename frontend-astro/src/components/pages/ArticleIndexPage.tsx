/**
 * 文章列表页 — Editorial minimal
 * 数据源：GET /api/v2/articles/（支持 page / per_page / search / category_id）
 * 功能：服务端搜索（防抖）/ 分类筛选 / 分页 / 骨架屏 / 空态 / 错误重试
 */

'use client';

import React, {useCallback, useEffect, useState} from 'react';
import {apiClient, CategoryService} from '@/lib/api';
import type {Article, Category} from '@/lib/api/base-types';
import {Input} from '@/components/ui/input';
import {Skeleton} from '@/components/ui/skeleton';

const PER_PAGE = 12;

interface Pagination {
  current_page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

const ArticleIndexPage: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [categoryId, setCategoryId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 分类下拉数据（一次拉取）
  useEffect(() => {
    CategoryService.getCategoryIndex(100)
      .then((res) => setCategories(Array.isArray(res?.data) ? res.data : []))
      .catch(() => setCategories([]));
  }, []);

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search.trim());
      setPage(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [search]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = {
        page,
        per_page: PER_PAGE,
      };
      if (debouncedSearch) params.search = debouncedSearch;
      if (categoryId) params.category_id = Number(categoryId);

      const res: any = await apiClient.get('/articles/', params);
      if (res?.success) {
        setArticles(Array.isArray(res.data) ? res.data : []);
        setPagination((res.pagination as Pagination) || null);
      } else {
        setArticles([]);
        setPagination(null);
        setError(res?.error || '加载文章失败');
      }
    } catch (e: any) {
      setArticles([]);
      setPagination(null);
      setError(e?.message || '网络异常，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, categoryId]);

  useEffect(() => {
    load();
  }, [load]);

  const hasFilter = Boolean(debouncedSearch || categoryId);

  return (
    <div>
      <header className="border-b border-border pb-8">
        <p className="kicker">Articles</p>
        <h1 className="editorial-title mt-3 text-4xl text-foreground sm:text-5xl">文章</h1>
        <p className="editorial-lede mt-4 max-w-2xl">
          全部已发布内容，按发布时间倒序排列。
        </p>
        {!loading && !error && pagination && (
          <p className="mt-6 font-mono text-xs text-muted-foreground">
            {pagination.total} 篇文章
          </p>
        )}
      </header>

      {/* 工具栏 */}
      <div className="flex flex-col gap-3 py-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:max-w-xs">
          <Input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索标题或摘要…"
            aria-label="搜索文章"
          />
        </div>
        <select
          value={categoryId}
          onChange={(e) => {
            setCategoryId(e.target.value);
            setPage(1);
          }}
          aria-label="按分类筛选"
          className="h-10 rounded-md border border-input bg-card px-3 text-sm text-foreground transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        >
          <option value="">全部分类</option>
          {categories.map((category) => (
            <option key={category.id} value={String(category.id)}>
              {category.name}
            </option>
          ))}
        </select>
      </div>

      {/* 内容 */}
      {loading ? (
        <div>
          {Array.from({length: 5}).map((_, index) => (
            <div key={index} className="border-b border-border/60 py-6">
              <Skeleton className="h-6 w-2/3"/>
              <Skeleton className="mt-3 h-4 w-full"/>
              <Skeleton className="mt-2 h-3 w-40"/>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center gap-4 border border-border bg-card px-6 py-16 text-center">
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            type="button"
            onClick={load}
            className="rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
          >
            重新加载
          </button>
        </div>
      ) : articles.length === 0 ? (
        <div className="border border-border bg-card px-6 py-16 text-center">
          <p className="editorial-title text-xl text-foreground">没有匹配的文章</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {hasFilter ? '换个关键词或分类再试试' : '站点还没有已发布的内容'}
          </p>
          {hasFilter && (
            <button
              type="button"
              onClick={() => {
                setSearch('');
                setCategoryId('');
              }}
              className="mt-5 rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
            >
              清除筛选
            </button>
          )}
        </div>
      ) : (
        <>
          <div>
            {articles.map((article) => (
              <article key={article.id} className="group border-b border-border/60">
                <a
                  href={`/blog/detail?slug=${encodeURIComponent(article.slug)}`}
                  className="block py-6"
                >
                  <h2
                    className="editorial-title text-xl text-foreground transition-colors group-hover:text-primary sm:text-2xl">
                    {article.title}
                  </h2>
                  {(article.excerpt || article.summary) && (
                    <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
                      {article.excerpt || article.summary}
                    </p>
                  )}
                  <div className="mt-3 flex flex-wrap items-center gap-4 font-mono text-xs text-muted-foreground">
                    {article.author?.username && <span>{article.author.username}</span>}
                    {article.category_name && <span>{article.category_name}</span>}
                    {article.created_at && (
                      <time dateTime={article.created_at}>
                        {new Date(article.created_at).toLocaleDateString('zh-CN')}
                      </time>
                    )}
                    {typeof article.views === 'number' && <span>{article.views} 阅读</span>}
                  </div>
                </a>
              </article>
            ))}
          </div>

          {(pagination?.total_pages ?? 1) > 1 && (
            <nav className="mt-10 flex items-center justify-between border-t border-border pt-6" aria-label="分页">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="rounded-sm border border-border px-3 py-1.5 text-sm transition-colors hover:bg-accent disabled:pointer-events-none disabled:opacity-40"
              >
                ← 上一页
              </button>
              <span className="font-mono text-xs text-muted-foreground">
                                {page} / {pagination?.total_pages ?? 1}
                            </span>
              <button
                type="button"
                onClick={() => setPage((p) => p + 1)}
                disabled={!pagination?.has_next}
                className="rounded-sm border border-border px-3 py-1.5 text-sm transition-colors hover:bg-accent disabled:pointer-events-none disabled:opacity-40"
              >
                下一页 →
              </button>
            </nav>
          )}
        </>
      )}
    </div>
  );
};

export default ArticleIndexPage;
