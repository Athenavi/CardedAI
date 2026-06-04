/**
 * 搜索建议服务
 * 提供搜索自动补全和热门搜索功能
 */

import {apiClient} from './base-client';
import type {ApiResponse} from '@/lib/api/base-types';

export interface SearchSuggestion {
    id: number;
    text: string;
    type: 'article' | 'tag' | 'category' | 'user';
    count?: number; // 相关文章数量
}

export interface SearchSuggestionsResponse {
    success: boolean;
    data?: {
        suggestions: SearchSuggestion[];
    };
    error?: string;
}

export interface HotSearch {
    keyword: string;
    count: number;
    trend: 'up' | 'down' | 'stable';
}

export interface HotSearchResponse {
    success: boolean;
    data?: {
        hot_searches: HotSearch[];
    };
    error?: string;
}

class SearchSuggestionService {
    /**
     * 获取搜索建议
     * @param query - 搜索关键词
     * @param limit - 返回数量限制
     */
    async getSuggestions(query: string, limit: number = 10): Promise<ApiResponse<{ suggestions: SearchSuggestion[] }>> {
        try {
            if (!query || query.trim() === '') {
                return {
                    success: true,
                    data: {suggestions: []},
                };
            }

            const response = await apiClient.get('/search/suggestions', {
                params: {q: query, limit},
            });

            return response as ApiResponse<{ suggestions: SearchSuggestion[] }>;
        } catch (error) {
            console.error('[SearchSuggestionService] Failed to get suggestions:', error);
            return {
                success: false,
                data: {suggestions: []},
                error: error instanceof Error ? error.message : '获取搜索建议失败',
            };
        }
    }

    /**
     * 获取热门搜索
     * @param limit - 返回数量限制
     */
    async getHotSearches(limit: number = 10): Promise<ApiResponse<{ hot_searches: HotSearch[] }>> {
        try {
            // 后端没有直接的 /search/hot 端点，使用 /search/stats 获取搜索统计信息
            const response = await apiClient.get('/search/stats', {
                params: {limit},
            });

            // 如果后端返回的数据格式不同，需要进行转换
            return response as ApiResponse<{ hot_searches: HotSearch[] }>;
        } catch (error) {
            console.error('[SearchSuggestionService] Failed to get hot searches:', error);
            return {
                success: false,
                data: {hot_searches: []},
                error: error instanceof Error ? error.message : '获取热门搜索失败',
            };
        }
    }

    /**
     * 记录搜索历史（本地存储）
     * @param query - 搜索关键词
     */
    saveSearchHistory(query: string): void {
        try {
            const history = this.getSearchHistory();

            // 移除重复项
            const filtered = history.filter(item => item !== query);

            // 添加到开头
            filtered.unshift(query);

            // 只保留最近20条
            const limited = filtered.slice(0, 20);

            localStorage.setItem('search_history', JSON.stringify(limited));
        } catch (error) {
            console.error('[SearchSuggestionService] Failed to save search history:', error);
        }
    }

    /**
     * 获取搜索历史（本地存储）
     */
    getSearchHistory(): string[] {
        try {
            const history = localStorage.getItem('search_history');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('[SearchSuggestionService] Failed to get search history:', error);
            return [];
        }
    }

    /**
     * 清除搜索历史
     */
    clearSearchHistory(): void {
        try {
            localStorage.removeItem('search_history');
        } catch (error) {
            console.error('[SearchSuggestionService] Failed to clear search history:', error);
        }
    }

    /**
     * 删除单条搜索历史
     * @param query - 搜索关键词
     */
    removeSearchHistoryItem(query: string): void {
        try {
            const history = this.getSearchHistory();
            const filtered = history.filter(item => item !== query);
            localStorage.setItem('search_history', JSON.stringify(filtered));
        } catch (error) {
            console.error('[SearchSuggestionService] Failed to remove search history item:', error);
        }
    }
}

// 导出单例实例
export const searchSuggestionService = new SearchSuggestionService();
export default searchSuggestionService;
