/**
 * 标签索引页 — Editorial minimal
 * 功能：搜索 / 排序（热度·名称）/ 分页 / 骨架屏 / 空态 / 错误重试
 */

'use client';

import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {TagService} from '@/lib/api';
import type {TagSummary} from '@/lib/api';
import {Input} from '@/components/ui/input';
import {Skeleton} from '@/components/ui/skeleton';

const PER_PAGE = 60;

type SortKey = 'count' | 'name';

const tagHref = (name: string) => `/tags/${encodeURIComponent(name)}`;

const TagsPage: React.FC = () => {
  const [tags, setTags] = useState<TagSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<SortKey>('count');
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 搜索防抖（输入停止 300ms 后请求）
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await TagService.getTags({
        page,
        per_page: PER_PAGE,
        sort,
        q: debouncedQuery || undefined,
      });
      if (res.success && res.data) {
        setTags(res.data.tags || []);
        setTotal(res.data.total_tags || 0);
        setTotalPages(res.data.pagination?.total_pages || 1);
      } else {
        setTags([]);
        setTotal(0);
        setTotalPages(1);
        setError(res.error || '加载标签失败');
      }
    } catch (e: any) {
      setTags([]);
      setTotal(0);
      setTotalPages(1);
      setError(e?.message || '网络异常，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [page, sort, debouncedQuery]);

  useEffect(() => {
    load();
  }, [load]);

  const maxCount = useMemo(() => tags.reduce((max, tag) => Math.max(max, tag.count), 0), [tags]);

  // 编辑风"标签索引"：按热度分档调整字号
  const sizeClass = (count: number) => {
    if (!maxCount) return 'text-base';
    const ratio = count / maxCount;
    if (ratio >= 0.75) return 'text-2xl sm:text-3xl';
    if (ratio >= 0.4) return 'text-xl sm:text-2xl';
    if (ratio >= 0.15) return 'text-lg';
    return 'text-base';
  };

  return (
    <div>
      {/* Header */}
      <header className="border-b border-border pb-8">
        <p className="kicker">Tags</p>
        <h1 className="editorial-title mt-3 text-4xl text-foreground sm:text-5xl">标签</h1>
        <p className="editorial-lede mt-4 max-w-2xl">
          按主题索引全部内容。标签按文章数量排序，字号越大表示内容越多。
        </p>
        {!loading && !error && (
          <p className="mt-6 font-mono text-xs text-muted-foreground">
            {total} 个标签
          </p>
        )}
      </header>

      {/* Toolbar */}
      <div className="flex flex-col gap-4 py-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:max-w-xs">
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索标签…"
            aria-label="搜索标签"
          />
        </div>
        <div className="flex items-center gap-1" role="group" aria-label="排序方式">
          {([['count', '按热度'], ['name', '按名称']] as const).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => {
                setSort(key);
                setPage(1);
              }}
              aria-pressed={sort === key}
              className={`rounded-sm border px-3 py-1.5 text-xs tracking-wide transition-colors ${
                sort === key
                  ? 'border-foreground/30 bg-accent text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({length: 12}).map((_, index) => (
            <div key={index} className="flex items-center justify-between border-b border-border/60 py-3">
              <Skeleton className="h-5 w-28"/>
              <Skeleton className="h-3 w-6"/>
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
      ) : tags.length === 0 ? (
        <div className="border border-border bg-card px-6 py-16 text-center">
          <p className="editorial-title text-xl text-foreground">没有找到标签</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {debouncedQuery ? `没有与「${debouncedQuery}」匹配的标签` : '还没有任何标签，发布第一篇文章后即可在此看到'}
          </p>
          {debouncedQuery && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="mt-5 rounded-sm border border-border px-4 py-2 text-sm transition-colors hover:bg-accent"
            >
              清除搜索
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
            {tags.map((tag) => (
              <a
                key={tag.name}
                href={tagHref(tag.name)}
                className="group flex items-baseline justify-between gap-4 border-b border-border/60 py-3 transition-colors hover:border-foreground/40"
              >
                                <span
                                  className={`editorial-title ${sizeClass(tag.count)} text-foreground transition-colors group-hover:text-primary`}
                                >
                                    <span className="mr-1 font-mono text-sm text-muted-foreground">#</span>
                                  {tag.name}
                                </span>
                <span className="shrink-0 font-mono text-xs text-muted-foreground">{tag.count}</span>
              </a>
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

export default TagsPage;
