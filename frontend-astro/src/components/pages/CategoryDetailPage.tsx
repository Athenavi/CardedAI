/**
 * 分类详情页 — Editorial minimal
 * 数据源：/api/v2/home/categories（解析分类）+ /api/v2/articles/?category_id=（该分类文章）
 * 说明：全部走公开端点，避免旧实现的 /categories/{name} 认证问题。
 */

'use client';

import React, {useCallback, useEffect, useState} from 'react';
import {apiClient, CategoryService} from '@/lib/api';
import type {Article, Category} from '@/lib/api/base-types';
import {Skeleton} from '@/components/ui/skeleton';

const PER_PAGE = 20;

interface Props {
  /** 静态输出下服务端读不到查询参数，故由组件在客户端从 URL 解析 ?name= */
  categoryName?: string;
}

const CategoryDetailPage: React.FC<Props> = ({categoryName}) => {
  const [name, setName] = useState(categoryName || '');
  const [category, setCategory] = useState<Category | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 客户端解析 ?name=（prop 为空时）
  useEffect(() => {
    if (categoryName || typeof window === 'undefined') return;
    const fromUrl = new URL(window.location.href).searchParams.get('name');
    if (fromUrl) setName(fromUrl);
  }, [categoryName]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    try {
      if (!name) {
        setNotFound(true);
        return;
      }
      const categoriesRes = await CategoryService.getCategoryIndex(200);
      const list: Category[] = Array.isArray(categoriesRes?.data) ? categoriesRes.data : [];
      const keyword = name.trim().toLowerCase();
      const matched =
        list.find((item) => item.name.toLowerCase() === keyword) ||
        list.find((item) => item.name.toLowerCase().includes(keyword));

      if (!matched) {
        setNotFound(true);
        setCategory(null);
        setArticles([]);
        setTotal(0);
        setTotalPages(1);
        return;
      }

      setCategory(matched);

      const res: any = await apiClient.get('/articles/', {
        category_id: matched.id,
        page,
        per_page: PER_PAGE,
      });

      if (res?.success) {
        setArticles(Array.isArray(res.data) ? res.data : []);
        setTotal(res?.pagination?.total ?? 0);
        setTotalPages(res?.pagination?.total_pages ?? 1);
      } else {
        setArticles([]);
        setError(res?.error || '加载分类文章失败');
      }
    } catch (e: any) {
      setArticles([]);
      setError(e?.message || '网络异常，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [name, page]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <nav className="mb-8 font-mono text-xs text-muted-foreground">
        <a href="/categories" className="transition-colors hover:text-foreground">← 全部分类</a>
      </nav>

      <header className="border-b border-border pb-8">
        <p className="kicker">Category</p>
        <h1 className="editorial-title mt-3 text-4xl text-foreground sm:text-5xl">
          {category?.name || name}
        </h1>
        {category?.description && (
          <p className="editorial-lede mt-4 max-w-2xl">{category.description}</p>
        )}
        {!loading && !error && !notFound && (
          <p className="mt-6 font-mono text-xs text-muted-foreground">
            {total} 篇文章
          </p>
        )}
      </header>

      {loading ? (
        <div className="py-4">
          {Array.from({length: 5}).map((_, index) => (
            <div key={index} className="border-b border-border/60 py-6">
              <Skeleton className="h-6 w-2/3"/>
              <Skeleton className="mt-3 h-4 w-full"/>
              <Skeleton className="mt-2 h-3 w-40"/>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="mt-8 flex flex-col items-center gap-4 border border-border bg-card px-6 py-16 text-center">
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            type="button"
            onClick={load}
            className="rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
          >
            重新加载
          </button>
        </div>
      ) : notFound ? (
        <div className="mt-8 border border-border bg-card px-6 py-16 text-center">
          <p className="editorial-title text-xl text-foreground">没有找到这个分类</p>
          <p className="mt-2 text-sm text-muted-foreground">
            分类「{name}」不存在或已被重命名
          </p>
          <a
            href="/categories"
            className="mt-6 inline-block rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
          >
            浏览全部分类
          </a>
        </div>
      ) : articles.length === 0 ? (
        <div className="mt-8 border border-border bg-card px-6 py-16 text-center">
          <p className="editorial-title text-xl text-foreground">该分类下暂无文章</p>
          <a
            href="/articles"
            className="mt-6 inline-block rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
          >
            浏览全部文章
          </a>
        </div>
      ) : (
        <>
          <div className="mt-2">
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

          {totalPages > 1 && (
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
                                {page} / {totalPages}
                            </span>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
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

export default CategoryDetailPage;
