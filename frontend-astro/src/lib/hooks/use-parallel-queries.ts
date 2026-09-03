/**
 * 并行请求 Hook - 解决接口瀑布问题
 *
 * 使用方式：
 * ```tsx
 * // 并行加载多个独立请求
 * const {data, isLoading} = useParallelQueries({
 *   stats: () => apiClient.get('/stats'),
 *   articles: () => apiClient.get('/articles'),
 *   categories: () => apiClient.get('/categories'),
 * });
 *
 * // 使用结果
 * if (isLoading) return <Loading />;
 * return <div>{data.stats.total}</div>;
 * ```
 */

import {useEffect, useState, useRef, useMemo, useCallback} from 'react';

interface ParallelQuery<T> {
  queryFn: () => Promise<T>;
  enabled?: boolean;
}

type ParallelQueriesOptions<T extends Record<string, any>> = {
  [K in keyof T]: ParallelQuery<T[K]>;
};

type ParallelQueriesData<T extends Record<string, any>> = {
  [K in keyof T]?: T[K];
};

type ParallelQueriesErrors<T extends Record<string, any>> = {
  [K in keyof T]?: any;
};

interface ParallelQueriesResult<T extends Record<string, any>> {
  data: ParallelQueriesData<T>;
  isLoading: boolean;
  error: ParallelQueriesErrors<T> | null;
  refetch: (key?: keyof T) => Promise<void>;
}

/**
 * 并行执行多个独立查询
 * 所有请求同时发出（避免瀑布加载）
 */
export function useParallelQueries<T extends Record<string, any>>(
  queries: ParallelQueriesOptions<T>
): ParallelQueriesResult<T> {
  const keys = useMemo(() => Object.keys(queries) as Array<keyof T>, [queries]);
  const [data, setData] = useState<ParallelQueriesData<T>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ParallelQueriesErrors<T> | null>(null);
  const mountedRef = useRef(true);

  const fetchAll = useCallback(async (specificKey?: keyof T) => {
    if (!mountedRef.current) return;

    if (specificKey) {
      const query = queries[specificKey];
      if (query.enabled !== false) {
        try {
          const result = await query.queryFn();
          if (mountedRef.current) {
            setData(prev => ({...prev, [specificKey]: result}));
          }
        } catch (e) {
          if (mountedRef.current) {
            setError(prev => {
              const newErrors = prev || {} as ParallelQueriesErrors<T>;
              (newErrors as Record<string, any>)[String(specificKey)] = e;
              return newErrors;
            });
          }
        }
      }
    } else {
      setIsLoading(true);
      setError(null);

      const results: ParallelQueriesData<T> = {};
      const errors: ParallelQueriesErrors<T> = {};

      const promises = keys.map(async (key) => {
        const query = queries[key];
        if (query.enabled === false) return;
        try {
          const result = await query.queryFn();
          if (mountedRef.current) {
            results[key] = result;
          }
        } catch (e) {
          errors[key] = e;
        }
      });

      await Promise.allSettled(promises);

      if (mountedRef.current) {
        setData(results);
        setError(Object.keys(errors).length > 0 ? errors : null);
        setIsLoading(false);
      }
    }
  }, [queries, keys]);

  useEffect(() => {
    mountedRef.current = true;
    fetchAll();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchAll]);

  const refetch = useCallback(async (key?: keyof T) => {
    await fetchAll(key);
  }, [fetchAll]);

  return {data, isLoading, error, refetch};
}

/**
 * 串行请求 Hook（有依赖时使用）
 */
export function useSequentialQueries<T extends Record<string, any>>(
  queries: {
    [K in keyof T]: ParallelQuery<T[K]> & { dependsOn?: (keyof T)[] };
  }
) {
  const [data, setData] = useState<ParallelQueriesData<T>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<any>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    (async () => {
      setIsLoading(true);
      const results: ParallelQueriesData<T> = {};
      const keys = Object.keys(queries) as Array<keyof T>;
      const executed = new Set<keyof T>();

      while (executed.size < keys.length) {
        let progress = false;
        for (const key of keys) {
          if (executed.has(key)) continue;
          const query = queries[key];
          const deps = query.dependsOn || [];

          if (deps.every(d => executed.has(d))) {
            if (query.enabled === false) {
              executed.add(key);
              progress = true;
              continue;
            }
            try {
              const result = await query.queryFn();
              if (mountedRef.current) {
                results[key] = result;
                setData({...results});
              }
              executed.add(key);
              progress = true;
            } catch (e) {
              if (mountedRef.current) setError(e);
              executed.add(key);
              progress = true;
            }
          }
        }
        if (!progress) break;
      }

      if (mountedRef.current) {
        setData(results);
        setIsLoading(false);
      }
    })();

    return () => { mountedRef.current = false; };
  }, [queries]);

  return {data, isLoading, error};
}

/**
 * 优先级请求队列
 * 高优先级请求先执行，低优先级在空闲时执行
 */
export function usePriorityFetch<T = any>(
  url: string,
  priority: 'high' | 'low' = 'high',
  enabled = true
): { data: T | null; isLoading: boolean; error: any } {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<any>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    if (!enabled) return;
    mountedRef.current = true;

    const doFetch = async () => {
      setIsLoading(true);
      try {
        const res = await globalThis.fetch(url, {credentials: 'include'});
        const json = await res.json();
        if (mountedRef.current) {
          setData(json);
        }
      } catch (e) {
        if (mountedRef.current) setError(e);
      } finally {
        if (mountedRef.current) setIsLoading(false);
      }
    };

    if (priority === 'high') {
      doFetch();
    } else {
      if (typeof (window as any).requestIdleCallback === 'function') {
        const handle = (window as any).requestIdleCallback(doFetch);
        return () => {
          mountedRef.current = false;
          (window as any).cancelIdleCallback(handle);
        };
      }
      const timer = setTimeout(doFetch, 100);
      return () => {
        mountedRef.current = false;
        clearTimeout(timer);
      };
    }
  }, [url, priority, enabled]);

  return {data, isLoading, error};
}