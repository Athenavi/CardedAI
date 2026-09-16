/**
 * 首页 — Editorial minimal（报头 + 最新 + 热门 + 分类）
 * 数据源：/api/v2/home/articles（最新，真实实现）、/home/popular、/home/categories、/home/stats
 * 说明：旧的 ModernHomePage（视差 + 粒子 + 渐变 hero）已不再被 index.astro 引用，保留以便对照回滚。
 */

'use client';

import React, {useCallback, useEffect, useState} from 'react';
import {ArticleService, CategoryService, apiClient} from '@/lib/api';
import type {Article, Category} from '@/lib/api/base-types';
import {Skeleton} from '@/components/ui/skeleton';

const PER_PAGE = 6;

interface SiteStats {
  total_articles?: number;
  total_users?: number;
  total_views?: number;
}

const formatCount = (value?: number) => {
  if (typeof value !== 'number') return '—';
  if (value >= 10000) return `${(value / 10000).toFixed(1)} 万`;
  return String(value);
};

const HomePage: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [popular, setPopular] = useState<Article[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [stats, setStats] = useState<SiteStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [latestRes, popularRes, categoryRes, statsRes] = await Promise.all([
        ArticleService.getHomeArticles({page: 1, per_page: PER_PAGE}),
        apiClient.get('/home/popular', {limit: 5}),
        CategoryService.getCategoryIndex(6),
        apiClient.get('/home/stats'),
      ]);

      if (latestRes.success && latestRes.data) {
        setArticles(latestRes.data.data || []);
      } else {
        setArticles([]);
      }

      const popularData: any = popularRes;
      setPopular(Array.isArray(popularData?.data) ? popularData.data : []);

      const categoryData: any = categoryRes;
      setCategories(Array.isArray(categoryData?.data) ? categoryData.data : []);

      const statsData: any = statsRes;
      setStats(statsData?.data || null);
    } catch (e: any) {
      setError(e?.message || '加载失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const statItems = [
    {label: '文章', value: formatCount(stats?.total_articles)},
    {label: '作者', value: formatCount(stats?.total_users)},
    {label: '阅读', value: formatCount(stats?.total_views)},
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
      {/* 报头 */}
      <header className="border-b border-border pb-10">
        <div className="flex items-baseline justify-between gap-6">
          <p className="kicker">Carded AI</p>
          <p className="kicker">
            {new Date().toLocaleDateString('zh-CN', {year: 'numeric', month: 'long', day: 'numeric'})}
          </p>
        </div>
        <h1 className="editorial-title mt-6 text-4xl leading-[1.1] text-foreground sm:text-6xl">
          写作、阅读与检索，都收在一处
        </h1>
        <p className="editorial-lede mt-5 max-w-2xl">
          一个以内容为中心的平台：专注的写作体验、清爽的阅读版面、快速的全文检索与分类标签体系。
        </p>

        <dl className="mt-8 grid grid-cols-3 gap-6 border-t border-border pt-6 sm:max-w-md">
          {statItems.map((item) => (
            <div key={item.label}>
              <dt className="kicker">{item.label}</dt>
              <dd className="editorial-title mt-2 text-2xl text-foreground">{item.value}</dd>
            </div>
          ))}
        </dl>
      </header>

      {error && (
        <div className="mt-10 flex flex-col items-center gap-4 border border-border bg-card px-6 py-16 text-center">
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            type="button"
            onClick={load}
            className="rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
          >
            重新加载
          </button>
        </div>
      )}

      {!error && (
        <div className="mt-12 grid gap-12 lg:grid-cols-[minmax(0,1fr)_18rem] lg:gap-16">
          {/* 主栏：最新文章 */}
          <section aria-label="最新文章">
            <div className="flex items-baseline justify-between border-b border-border pb-3">
              <h2 className="kicker">Latest</h2>
              <a
                href="/articles"
                className="text-xs text-muted-foreground transition-colors hover:text-foreground"
              >
                全部文章 →
              </a>
            </div>

            {loading ? (
              <div>
                {Array.from({length: 4}).map((_, index) => (
                  <div key={index} className="border-b border-border/60 py-6">
                    <Skeleton className="h-6 w-3/4"/>
                    <Skeleton className="mt-3 h-4 w-full"/>
                    <Skeleton className="mt-2 h-3 w-40"/>
                  </div>
                ))}
              </div>
            ) : articles.length === 0 ? (
              <div className="border-b border-border/60 py-16 text-center">
                <p className="editorial-title text-xl text-foreground">还没有发布内容</p>
                <p className="mt-2 text-sm text-muted-foreground">
                  发布第一篇文章后，这里会展示最新更新
                </p>
              </div>
            ) : (
              articles.map((article, index) => (
                <article key={article.id} className="group border-b border-border/60">
                  <a
                    href={`/blog/detail?slug=${encodeURIComponent(article.slug)}`}
                    className="flex gap-5 py-6"
                  >
                                        <span className="w-8 shrink-0 pt-1 font-mono text-xs text-muted-foreground">
                                            {String(index + 1).padStart(2, '0')}
                                        </span>
                    <div className="min-w-0">
                      <h3
                        className="editorial-title text-xl text-foreground transition-colors group-hover:text-primary sm:text-2xl">
                        {article.title}
                      </h3>
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
                    </div>
                  </a>
                </article>
              ))
            )}
          </section>

          {/* 侧栏：热门 / 分类 / 入口 */}
          <aside className="space-y-12">
            <section aria-label="热门文章">
              <h2 className="kicker border-b border-border pb-3">Popular</h2>
              {loading ? (
                <div className="space-y-3 pt-4">
                  {Array.from({length: 3}).map((_, index) => (
                    <Skeleton key={index} className="h-4 w-full"/>
                  ))}
                </div>
              ) : popular.length === 0 ? (
                <p className="pt-4 text-xs text-muted-foreground">暂无数据</p>
              ) : (
                <ol className="pt-2">
                  {popular.map((article, index) => (
                    <li key={article.id} className="flex gap-3 border-b border-border/60 py-3">
                                            <span className="font-mono text-xs text-muted-foreground">
                                                {String(index + 1).padStart(2, '0')}
                                            </span>
                      <a
                        href={`/blog/detail?slug=${encodeURIComponent(article.slug)}`}
                        className="min-w-0 text-sm leading-snug text-foreground transition-colors hover:text-primary"
                      >
                        {article.title}
                      </a>
                    </li>
                  ))}
                </ol>
              )}
            </section>

            <section aria-label="分类">
              <h2 className="kicker border-b border-border pb-3">Categories</h2>
              {loading ? (
                <div className="space-y-3 pt-4">
                  {Array.from({length: 3}).map((_, index) => (
                    <Skeleton key={index} className="h-4 w-2/3"/>
                  ))}
                </div>
              ) : categories.length === 0 ? (
                <p className="pt-4 text-xs text-muted-foreground">暂无分类</p>
              ) : (
                <ul className="pt-2">
                  {categories.map((category) => (
                    <li key={category.id} className="border-b border-border/60">
                      <a
                        href={`/category?name=${encodeURIComponent(category.name)}`}
                        className="flex items-baseline justify-between gap-3 py-2.5 text-sm text-foreground transition-colors hover:text-primary"
                      >
                        <span>{category.name}</span>
                        <span className="font-mono text-xs text-muted-foreground">
                                                    {category.article_count ?? 0}
                                                </span>
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section aria-label="入口" className="border border-border bg-card p-5">
              <h2 className="kicker">Explore</h2>
              <div className="mt-4 flex flex-col gap-2 text-sm">
                <a href="/tags" className="text-foreground transition-colors hover:text-primary">
                  标签索引 →
                </a>
                <a href="/categories" className="text-foreground transition-colors hover:text-primary">
                  全部分类 →
                </a>
                <a href="/search" className="text-foreground transition-colors hover:text-primary">
                  全文搜索 →
                </a>
                <a
                  href="/api/v2/cms/feed?format=rss"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  RSS 订阅
                </a>
              </div>
            </section>
          </aside>
        </div>
      )}
    </div>
  );
};

export default HomePage;
