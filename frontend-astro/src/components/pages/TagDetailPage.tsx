/**
 * 标签详情页 — Editorial minimal
 * 展示某标签下的全部文章（客户端实时拉取）
 */

'use client';

import React, {useCallback, useEffect, useState} from 'react';
import {TagService} from '@/lib/api';
import {Skeleton} from '@/components/ui/skeleton';

interface TagDetailArticle {
  id: number;
  title: string;
  slug: string;
  excerpt?: string;
  cover_image?: string;
  views?: number;
  created_at?: string;
  author?: { id: number; username: string };
  category_name?: string | null;
}

interface Props {
  tagName: string;
}

const TagDetailPage: React.FC<Props> = ({tagName}) => {
  const [articles, setArticles] = useState<TagDetailArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await TagService.getArticlesByTag(tagName);
      if (res.success && res.data) {
        setArticles((res.data.articles || []) as TagDetailArticle[]);
      } else {
        setArticles([]);
        setError(res.error || '加载文章失败');
      }
    } catch (e: any) {
      setArticles([]);
      setError(e?.message || '网络异常，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [tagName]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <nav className="mb-8 font-mono text-xs text-muted-foreground">
        <a href="/tags" className="transition-colors hover:text-foreground">← 全部标签</a>
      </nav>

      <header className="border-b border-border pb-8">
        <p className="kicker">Tag</p>
        <h1 className="editorial-title mt-3 text-4xl text-foreground sm:text-5xl">
          <span className="mr-1 font-mono text-2xl text-muted-foreground sm:text-3xl">#</span>
          {tagName}
        </h1>
        {!loading && !error && (
          <p className="mt-6 font-mono text-xs text-muted-foreground">{articles.length} 篇文章</p>
        )}
      </header>

      {loading ? (
        <div className="py-6">
          {Array.from({length: 4}).map((_, index) => (
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
      ) : articles.length === 0 ? (
        <div className="mt-8 border border-border bg-card px-6 py-16 text-center">
          <p className="editorial-title text-xl text-foreground">该标签下暂无文章</p>
          <p className="mt-2 text-sm text-muted-foreground">换一个标签，或浏览全部文章</p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <a
              href="/articles"
              className="rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
            >
              浏览全部文章
            </a>
            <a href="/tags" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              返回标签索引
            </a>
          </div>
        </div>
      ) : (
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
                {article.excerpt && (
                  <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
                    {article.excerpt}
                  </p>
                )}
                <div className="mt-3 flex flex-wrap items-center gap-4 font-mono text-xs text-muted-foreground">
                  {article.author?.username && <span>{article.author.username}</span>}
                  {article.created_at && (
                    <time dateTime={article.created_at}>
                      {new Date(article.created_at).toLocaleDateString('zh-CN')}
                    </time>
                  )}
                  {article.category_name && <span>{article.category_name}</span>}
                  {typeof article.views === 'number' && <span>{article.views} 阅读</span>}
                </div>
              </a>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

export default TagDetailPage;
