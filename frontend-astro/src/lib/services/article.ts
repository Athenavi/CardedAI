/**
 * 文章服务
 */

import {apiClient} from '../api/base-client';
import type {Article, ApiResponse} from '../api/base-types';

export interface PaginatedResponse<T> {
    data: T[];
    pagination: {
        current_page: number;
        per_page: number;
        total: number;
        total_pages: number;
        has_next: boolean;
        has_prev: boolean;
    };
}

export class ArticleService {
    /**
     * 获取首页文章
     */
    static async getHomeArticles(params?: { page?: number; per_page?: number }) {
        return apiClient.get<ApiResponse<PaginatedResponse<Article>>>('/api/v2/articles/home', params);
    }

    /**
     * 获取文章列表
     */
    static async getArticles(params?: {
        page?: number;
        per_page?: number;
        search?: string;
        category_id?: number;
    }) {
        return apiClient.get<ApiResponse<PaginatedResponse<Article>>>('/api/v2/articles', params);
    }

    /**
     * 获取文章详情
     */
    static async getArticleBySlug(slug: string) {
        return apiClient.get<ApiResponse<Article>>(`/api/v2/articles/slug/${slug}`);
    }

    /**
     * 获取热门文章
     */
    static async getPopularArticles(limit = 10) {
        return apiClient.get<ApiResponse<Article[]>>('/api/v2/articles/popular', {limit});
    }

    /**
     * 获取最新文章
     */
    static async getRecentArticles(limit = 10) {
        return apiClient.get<ApiResponse<Article[]>>('/api/v2/articles/recent', {limit});
    }
}
