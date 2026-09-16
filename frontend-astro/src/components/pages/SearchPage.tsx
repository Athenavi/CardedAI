/**
 * 搜索页 — Editorial minimal
 * 功能：URL 关键词同步（?q=）/ 结果高亮 / 分页 / 本地搜索历史 / 骨架屏 / 空态 / 错误重试
 * 数据源：GET /api/v2/home/search?q=&page=&per_page=
 */

'use client';

import React, {useCallback, useEffect, useState} from 'react';
import {SearchService} from '@/lib/api/search-service';
import type {Article} from '@/lib/api/base-types';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import {Skeleton} from '@/components/ui/skeleton';

const PER_PAGE = 10;

interface Pagination {
  current_page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

/** 关键词高亮（纯 React 节点，不做 HTML 注入） */
const highlight = (text: string, keyword: string) => {
  if (!text || !keyword) return text;
  const index = text.toLowerCase().indexOf(keyword.toLowerCase());
  if (index < 0) return text;
  return (
    <>
      {text.slice(0, index)}
      <mark
        className="bg-transparent text-primary underline decoration-primary/40 underline-offset-2">
        {text.slice(index, index + keyword.length)}
      </mark>
      {text.slice(index + keyword.length)}
    </>
  );
};

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [submitted, setSubmitted] = useState('');
  const [results, setResults] = useState<Article[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);

  // 初始：读取 ?q= 与本地历史
  useEffect(() => {
    setHistory(SearchService.loadFromLocalStorage());
    if (typeof window === 'undefined') return;
    const initial = new URL(window.location.href).searchParams.get('q') || '';
    if (initial) {
      setQuery(initial);
      setSubmitted(initial);
    }
  }, []);

  const runSearch = useCallback(async (keyword: string, targetPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await SearchService.search(keyword, targetPage, PER_PAGE);
      if (res.success && res.data) {
        setResults(res.data.articles || []);
        setPagination((res.data.pagination as Pagination) || null);
      } else {
        setResults([]);
        setPagination(null);
        setError(res.error || '搜索失败');
      }
    } catch (e: any) {
      setResults([]);
      setPagination(null);
      setError(e?.message || '网络异常，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (submitted) runSearch(submitted, page);
  }, [submitted, page, runSearch]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const keyword = query.trim();
    if (!keyword) return;
    setSubmitted(keyword);
    setPage(1);
    SearchService.saveToLocalStorage(keyword);
    setHistory(SearchService.loadFromLocalStorage());
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('q', keyword);
      window.history.replaceState({}, '', url.toString());
    }
  };

  const searchHistoryItem = (keyword: string) => {
    setQuery(keyword);
    setSubmitted(keyword);
    setPage(1);
    SearchService.saveToLocalStorage(keyword);
    setHistory(SearchService.loadFromLocalStorage());
  };

  const clearHistory = () => {
    SearchService.clearHistory();
    setHistory([]);
  };

  return (
    <div>
      <header className="border-b border-border pb-8">
        <p className="kicker">Search</p>
        <h1 className="editorial-title mt-3 text-4xl text-foreground sm:text-5xl">搜索</h1>
        <p className="editorial-lede mt-4 max-w-2xl">
          在全部已发布内容中按标题与摘要检索。
        </p>
      </header>

      {/* 搜索表单 */}
      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-3 sm:flex-row" role="search">
        <Input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入关键词，例如 Astro、FastAPI…"
          aria-label="搜索关键词"
          autoFocus
          className="h-12 flex-1 text-base"
        />
        <Button type="submit" className="h-12 px-6">
          搜索
        </Button>
      </form>

      {/* 搜索历史 */}
      {history.length > 0 && !submitted && (
        <div className="mt-6 flex flex-wrap items-center gap-2">
          <span className="kicker">最近</span>
          {history.map((keyword) => (
            <button
              key={keyword}
              type="button"
              onClick={() => searchHistoryItem(keyword)}
              className="rounded-sm border border-border px-2.5 py-1 font-mono text-xs text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground"
            >
              {keyword}
            </button>
          ))}
          <button
            type="button"
            onClick={clearHistory}
            className="ml-1 text-xs text-muted-foreground underline decoration-border underline-offset-4 transition-colors hover:text-foreground"
          >
            清除
          </button>
        </div>
      )}

      {/* 结果区 */}
      <div className="mt-10">
        {!submitted ? (
          <div className="border-t border-border pt-10 text-center">
            <p className="editorial-title text-xl text-foreground">开始检索</p>
            <p className="mt-2 text-sm text-muted-foreground">
              输入关键词后回车，或从历史记录中选择
            </p>
          </div>
        ) : loading ? (
          <div>
            {Array.from({length: 4}).map((_, index) => (
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
              onClick={() => runSearch(submitted, page)}
              className="rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
            >
              重新搜索
            </button>
          </div>
        ) : results.length === 0 ? (
          <div className="border border-border bg-card px-6 py-16 text-center">
            <p className="editorial-title text-xl text-foreground">没有找到相关内容</p>
            <p className="mt-2 text-sm text-muted-foreground">
              关键词「{submitted}」没有匹配的文章，试试更短的关键词
            </p>
            <div className="mt-6 flex items-center justify-center gap-3">
              <a
                href="/articles"
                className="rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
              >
                浏览全部文章
              </a>
              <a href="/tags" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                按标签浏览
              </a>
            </div>
          </div>
        ) : (
          <>
            <p className="kicker">
              {pagination?.total ?? results.length} 个结果 · 「{submitted}」
            </p>

            <div className="mt-4">
              {results.map((article) => (
                <article key={article.id} className="group border-b border-border/60">
                  <a
                    href={`/blog/detail?slug=${encodeURIComponent(article.slug)}`}
                    className="block py-6"
                  >
                    <h2
                      className="editorial-title text-xl text-foreground transition-colors group-hover:text-primary sm:text-2xl">
                      {highlight(article.title, submitted)}
                    </h2>
                    {(article.excerpt || article.summary) && (
                      <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
                        {highlight(article.excerpt || article.summary || '', submitted)}
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
    </div>
  );
};

export default SearchPage;
