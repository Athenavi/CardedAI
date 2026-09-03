/**
 * API 请求缓存工具 - 带 LRU 淘汰策略
 *
 * 优化项：
 * - 缓存大小限制（最大 100 条目）
 * - LRU 淘汰（最近最少使用）
 * - 内存预估（避免过度缓存大对象）
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  size: number; // 估算字节大小
}

const MAX_CACHE_SIZE = 100;     // 最大条目数
const MAX_CACHE_BYTES = 5 * 1024 * 1024; // 5MB 上限

class ApiCache {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private defaultTTL: number = 5 * 60 * 1000;
  private totalBytes = 0;

  constructor(defaultTTL?: number) {
    if (defaultTTL) {
      this.defaultTTL = defaultTTL;
    }
  }

  /** 估算对象字节大小 */
  private estimateSize(obj: any): number {
    try {
      return new Blob([JSON.stringify(obj)]).size;
    } catch {
      return 1024; // fallback
    }
  }

  /** LRU 淘汰：从缓存中移除最旧的条目，直到有空间 */
  private evictIfNeeded(entrySize: number): void {
    while (this.cache.size >= MAX_CACHE_SIZE || this.totalBytes + entrySize > MAX_CACHE_BYTES) {
      if (this.cache.size === 0) break;

      // 找到最近最少使用的条目（时间戳最旧）
      let oldestKey: string | null = null;
      let oldestTime = Infinity;

      for (const [key, entry] of this.cache) {
        if (entry.timestamp < oldestTime) {
          oldestTime = entry.timestamp;
          oldestKey = key;
        }
      }

      if (oldestKey !== null) {
        const evicted = this.cache.get(oldestKey);
        if (evicted) this.totalBytes -= evicted.size;
        this.cache.delete(oldestKey);
      }
    }
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.totalBytes -= entry.size;
      this.cache.delete(key);
      return null;
    }
    return entry.data as T;
  }

  set<T>(key: string, data: T, ttl?: number): void {
    // 如果 key 已存在，先移除
    if (this.cache.has(key)) {
      const existing = this.cache.get(key);
      if (existing) this.totalBytes -= existing.size;
      this.cache.delete(key);
    }

    const size = this.estimateSize(data);
    // 淘汰直到有空间
    this.evictIfNeeded(size);

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
      size,
    });
    this.totalBytes += size;
  }

  delete(key: string): void {
    const entry = this.cache.get(key);
    if (entry) {
      this.totalBytes -= entry.size;
      this.cache.delete(key);
    }
  }

  clear(): void {
    this.cache.clear();
    this.totalBytes = 0;
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.totalBytes -= entry.size;
      this.cache.delete(key);
      return false;
    }
    return true;
  }

  /** 获取缓存统计信息（调试用） */
  stats(): { size: number; bytes: number; maxBytes: number } {
    return {
      size: this.cache.size,
      bytes: this.totalBytes,
      maxBytes: MAX_CACHE_BYTES,
    };
  }

  async getOrFetch<T>(
    key: string,
    fetchFn: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = this.get<T>(key);
    if (cached !== null) return cached;

    const data = await fetchFn();
    this.set(key, data, ttl);
    return data;
  }
}

export const apiCache = new ApiCache();

export async function cachedFetch<T>(
    url: string,
    options?: RequestInit,
    ttl?: number
): Promise<T> {
    const cacheKey = `${url}:${JSON.stringify(options || {})}`;

    return apiCache.getOrFetch(
        cacheKey,
        async () => {
            if (!url || typeof url !== 'string') {
                throw new Error(`Invalid URL: ${url}`);
            }

            const response = await fetch(url, options);

            if (response.status === 304) {
                const cachedData = apiCache.get<T>(cacheKey);
                if (cachedData !== null) return cachedData;
                throw new Error('304 Not Modified but no cached data available');
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const text = await response.text();
            if (!text) throw new Error('Empty response from server');

            try {
                return JSON.parse(text) as T;
            } catch (e) {
                throw new Error(`Failed to parse JSON response: ${e instanceof Error ? e.message : 'Unknown error'}`);
            }
        },
        ttl
    );
}

export function clearCacheByPattern(pattern: string): void {
    const keysToDelete: string[] = [];
    for (const key of apiCache['cache'].keys()) {
        if (key.includes(pattern)) {
            keysToDelete.push(key);
        }
    }
    keysToDelete.forEach(key => apiCache.delete(key));
}

export function getCacheStats() {
    return apiCache.stats();
}
