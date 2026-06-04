/**
 * 首页数据获取 Hook
 * 适配 Astro：使用 @tanstack/react-query 替代手写状态管理
 */

'use client';

import {useQuery} from '@tanstack/react-query';
import type {Article, Category} from '@/lib/api';
import {cachedFetch} from '@/lib/api-cache';

interface HomePageData {
    featuredArticles: Article[];
    recentArticles: Article[];
    popularArticles: Article[];
    categories: Category[];
}

const fetchConfig = async () => {
    const config = await import('@/lib/config').then(m => m.getConfig());
    return config;
};

const fetchHomeData = async (): Promise<HomePageData> => {
    const config = await fetchConfig();
    const apiUrl = `${config.API_BASE_URL}${config.API_PREFIX}`;

    const [articlesRes, categoriesRes] = await Promise.all([
        cachedFetch<any>(`${apiUrl}/articles?page=1&page_size=20`, undefined, 5 * 60 * 1000),
        cachedFetch<any>(`${apiUrl}/home/categories`, undefined, 10 * 60 * 1000)
    ]);

    if (articlesRes.success && categoriesRes.success) {
        const articles = articlesRes.data || [];
        const categories = categoriesRes.data || [];

        return {
            featuredArticles: articles.filter((a: Article) => a.is_featured).slice(0, 3),
            recentArticles: articles.slice(0, 9),
            popularArticles: [...articles].sort((a: Article, b: Article) => (b.views || 0) - (a.views || 0)).slice(0, 8),
            categories: categories.slice(0, 6),
        };
    }

    return {
        featuredArticles: [],
        recentArticles: [],
        popularArticles: [],
        categories: [],
    };
};

export function useHomePageData() {
    return useQuery<HomePageData>({
        queryKey: ['homePageData'],
        queryFn: fetchHomeData,
        staleTime: 5 * 60 * 1000,
        retry: 2,
    });
}

export {type HomePageData};
