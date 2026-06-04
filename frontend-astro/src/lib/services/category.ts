/**
 * 分类服务
 */

import {apiClient} from '../api/base-client';
import type {Category, ApiResponse} from '../api/base-types';

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

export class CategoryService {
    /**
     * 获取分类列表
     */
    static async getCategories(params?: { page?: number; per_page?: number }) {
        return apiClient.get<ApiResponse<PaginatedResponse<Category>>>('/api/v2/categories', params);
    }

    /**
     * 获取分类详情
     */
    static async getCategoryByName(name: string) {
        return apiClient.get<ApiResponse<Category>>(`/api/v2/categories/name/${encodeURIComponent(name)}`);
    }

    /**
     * 获取热门分类
     */
    static async getPopularCategories(limit = 10) {
        return apiClient.get<ApiResponse<Category[]>>('/api/v2/categories/popular', {limit});
    }
}
