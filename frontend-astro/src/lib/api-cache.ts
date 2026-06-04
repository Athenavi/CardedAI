/**
 * API 请求缓存工具
 */

interface CacheEntry<T> {
    data: T;
    timestamp: number;
    ttl: number;
}

class ApiCache {
    private cache: Map<string, CacheEntry<any>> = new Map();
    private defaultTTL: number = 5 * 60 * 1000;

    constructor(defaultTTL?: number) {
        if (defaultTTL) {
            this.defaultTTL = defaultTTL;
        }
    }

    get<T>(key: string): T | null {
        const entry = this.cache.get(key);
        if (!entry) return null;

        const now = Date.now();
        if (now - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            return null;
        }
        return entry.data as T;
    }

    set<T>(key: string, data: T, ttl?: number): void {
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            ttl: ttl || this.defaultTTL
        });
    }

    delete(key: string): void {
        this.cache.delete(key);
    }

    clear(): void {
        this.cache.clear();
    }

    has(key: string): boolean {
        const entry = this.cache.get(key);
        if (!entry) return false;

        const now = Date.now();
        if (now - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            return false;
        }
        return true;
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
