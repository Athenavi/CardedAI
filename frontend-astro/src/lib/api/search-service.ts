// 搜索服务
import {apiClient} from './base-client';
import type {Article, Pagination} from './base-types';

export interface SearchResponse {
    articles: Article[];
    pagination: Pagination;
}

export interface SearchHistory {
    keyword: string;
    created_at: string;
}

export const SearchService = {
    /**
     * 搜索文章
     * @param keyword 搜索关键词
     * @param page 页码
     * @param perPage 每页数量
     */
    search: async (
        keyword: string,
        page: number = 1,
        perPage: number = 10
    ): Promise<{ success: boolean; data?: SearchResponse; error?: string }> => {
        try {
            const response = await apiClient.get<SearchResponse>('/home/search', {
                q: keyword,
                page,
                per_page: perPage
            });

            if (response.success && response.data) {
                return {success: true, data: response.data};
            } else {
                return {success: false, error: response.error || '搜索失败'};
            }
        } catch (error) {
            console.error('搜索服务错误:', error);
            return {success: false, error: error instanceof Error ? error.message : String(error)};
        }
    },

    /**
     * 获取用户的搜索历史
     */
    getHistory: async (): Promise<{ success: boolean; data?: SearchHistory[]; error?: string }> => {
        try {
            const response = await apiClient.get<SearchHistory[]>('/search/history');

            if (response.success && response.data) {
                return {success: true, data: response.data};
            } else {
                return {success: false, error: response.error || '获取搜索历史失败'};
            }
        } catch (error) {
            console.error('获取搜索历史错误:', error);
            return {success: false, error: error instanceof Error ? error.message : String(error)};
        }
    },

    /**
     * 保存搜索历史到本地存储
     */
    saveToLocalStorage: (keyword: string): void => {
        if (typeof window === 'undefined') return;

        try {
            // 确保历史记录中不重复，并限制数量
            let searchHistory: string[] = [];
            const history = localStorage.getItem('searchHistory');
            if (history) {
                searchHistory = JSON.parse(history);
            }

            const index = searchHistory.indexOf(keyword);
            if (index !== -1) {
                searchHistory.splice(index, 1);
            }
            const newHistory = [keyword, ...searchHistory];
            const trimmedHistory = newHistory.slice(0, 10); // 限制最多 10 条历史记录

            localStorage.setItem('searchHistory', JSON.stringify(trimmedHistory));
        } catch (error) {
            console.error('保存搜索历史失败:', error);
        }
    },

    /**
     * 从本地存储加载搜索历史
     */
    loadFromLocalStorage: (): string[] => {
        if (typeof window === 'undefined') return [];

        try {
            const history = localStorage.getItem('searchHistory');
            if (history) {
                return JSON.parse(history);
            }
            return [];
        } catch (error) {
            console.error('加载搜索历史失败:', error);
            return [];
        }
    },

    /**
     * 清除搜索历史
     */
    clearHistory: (): void => {
        if (typeof window === 'undefined') return;

        try {
            localStorage.removeItem('searchHistory');
        } catch (error) {
            console.error('清除搜索历史失败:', error);
        }
    }
};
