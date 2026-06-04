// Category service for Next.js frontend
import {apiClient} from './base-client';
import type {ApiResponse, Article, Category, Pagination} from '@/lib/api/base-types';

// Category Service
export class CategoryService {
    static async getCategories(params?: {
        page?: number;
        per_page?: number;
        search?: string;
        sort_by?: string
    }): Promise<ApiResponse<{
        categories: Category[];
        pagination: Pagination;
        subscribed_ids: number[];
        total_categories: number;
    }>> {
        // 使用 /home/categories 公开API，避免权限问题
        const response = await apiClient.get('/home/categories', params);

        // 确保返回正确的格式
        if (response.success && response.data && typeof response.data === 'object') {
            // 如果响应数据已经是期望格式（包含后端实际返回的字段）
            if ('categories' in response.data) {
                // 转换后端返回的格式为前端期望的格式
                const backendData = response.data as any;

                // 创建标准分页对象
                const pagination: Pagination = {
                    current_page: backendData.page || params?.page || 1,
                    per_page: backendData.per_page || params?.per_page || 10,
                    total: backendData.total_categories || (Array.isArray(backendData.categories) ? backendData.categories.length : 0),
                    total_pages: Math.ceil((backendData.total_categories || 0) / (backendData.per_page || 10)),
                    has_next: (backendData.page || params?.page || 1) < Math.ceil((backendData.total_categories || 0) / (backendData.per_page || 10)),
                    has_prev: (backendData.page || params?.page || 1) > 1
                };

                return {
                    ...response,
                    data: {
                        categories: backendData.categories || [],
                        pagination,
                        subscribed_ids: backendData.subscribed_ids || [],
                        total_categories: backendData.total_categories || 0
                    }
                } as ApiResponse<{
                    categories: Category[];
                    pagination: Pagination;
                    subscribed_ids: number[];
                    total_categories: number;
                }>;
            } else {
                // 如果响应数据是纯数组或其他格式，构造期望的格式
                return {
                    ...response,
                    data: {
                        categories: Array.isArray(response.data) ? response.data : [],
                        pagination: response.pagination || {
                            current_page: params?.page || 1,
                            per_page: params?.per_page || 10,
                            total: Array.isArray(response.data) ? response.data.length : 0,
                            total_pages: 1,
                            has_next: false,
                            has_prev: false
                        },
                        subscribed_ids: [],
                        total_categories: Array.isArray(response.data) ? response.data.length : 0
                    }
                } as ApiResponse<{
                    categories: Category[];
                    pagination: Pagination;
                    subscribed_ids: number[];
                    total_categories: number;
                }>;
            }
        }

        return {
            ...response,
            data: {
                categories: [],
                pagination: {
                    current_page: params?.page || 1,
                    per_page: params?.per_page || 10,
                    total: 0,
                    total_pages: 1,
                    has_next: false,
                    has_prev: false
                },
                subscribed_ids: [],
                total_categories: 0
            }
        } as ApiResponse<{
            categories: Category[];
            pagination: Pagination;
            subscribed_ids: number[];
            total_categories: number;
        }>;
    }

    static async getCategoriesWithStats(params?: { page?: number; per_page?: number }): Promise<ApiResponse<{
        categories: Array<{ category: Category; article_count: number; subscriber_count: number }>;
        pagination: Pagination;
    }>> {
        const response = await apiClient.get('/categories/', params); // 认证用户使用的API

        // 确保返回正确的格式
        if (response.success && response.data && typeof response.data === 'object') {
            // 如果响应数据已经是期望格式（包含 categories 和 pagination）
            if ('categories' in response.data && 'pagination' in response.data) {
                return response as ApiResponse<{
                    categories: Array<{ category: Category; article_count: number; subscriber_count: number }>;
                    pagination: Pagination;
                }>;
            }
            // 处理实际的 API 返回格式：{ categories: [], subscribed_ids: [], total_categories, page, per_page }
            else if ('categories' in response.data && 'total_categories' in response.data) {
                const apiData = response.data as any;
                const categories = apiData.categories || [];
                const totalCategories = apiData.total_categories || 0;
                const currentPage = apiData.page || params?.page || 1;
                const perPage = apiData.per_page || params?.per_page || 12;

                // 将纯 Category 数组转换为期望的格式（添加默认统计值）
                const formattedCategories = categories.map((cat: Category) => ({
                    category: cat,
                    article_count: 0,  // API 未返回，使用默认值
                    subscriber_count: 0  // API 未返回，使用默认值
                }));

                const totalPages = Math.ceil(totalCategories / perPage);

                return {
                    ...response,
                    data: {
                        categories: formattedCategories,
                        pagination: {
                            current_page: currentPage,
                            per_page: perPage,
                            total: totalCategories,
                            total_pages: totalPages,
                            has_next: currentPage < totalPages,
                            has_prev: currentPage > 1
                        }
                    }
                } as ApiResponse<{
                    categories: Array<{ category: Category; article_count: number; subscriber_count: number }>;
                    pagination: Pagination;
                }>;
            } else {
                // 如果响应数据是纯数组或其他格式，构造期望的格式
                return {
                    ...response,
                    data: {
                        categories: Array.isArray(response.data) ? response.data.map((cat: Category) => ({
                            category: cat,
                            article_count: 0,
                            subscriber_count: 0
                        })) : [],
                        pagination: response.pagination || {
                            current_page: params?.page || 1,
                            per_page: params?.per_page || 10,
                            total: Array.isArray(response.data) ? response.data.length : 0,
                            total_pages: 1,
                            has_next: false,
                            has_prev: false
                        }
                    }
                } as ApiResponse<{
                    categories: Array<{ category: Category; article_count: number; subscriber_count: number }>;
                    pagination: Pagination;
                }>;
            }
        }

        return {
            ...response,
            data: {
                categories: [],
                pagination: {
                    current_page: params?.page || 1,
                    per_page: params?.per_page || 10,
                    total: 0,
                    total_pages: 1,
                    has_next: false,
                    has_prev: false
                }
            }
        } as ApiResponse<{
            categories: Array<{ category: Category; article_count: number; subscriber_count: number }>;
            pagination: Pagination;
        }>;
    }

    static async getCategoryByName(name: string): Promise<ApiResponse<{
        category: Category;
        articles: Article[];
        pagination: {
            current_page: number;
            total_pages: number;
            has_next: boolean;
            has_prev: boolean;
            prev_page?: number;
            next_page?: number;
        };
        total_articles: number;
        description?: string;
        keywords?: string;
        subscribed_ids?: number[];  // 添加订阅ID数组
    }>> {
        return apiClient.get(`/categories/${name}`);
    }

    static async subscribeToCategory(categoryId: number): Promise<ApiResponse<{ message: string }>> {
        // 后端没有直接的subscribe API，可能需要使用其他端点
        // 暂时注释，需要根据实际需求调整
        throw new Error('Subscribe API not implemented yet');
    }

    static async unsubscribeFromCategory(categoryId: number): Promise<ApiResponse<{ message: string }>> {
        // 后端没有直接的unsubscribe API，可能需要使用其他端点
        // 暂时注释，需要根据实际需求调整
        throw new Error('Unsubscribe API not implemented yet');
    }

    static async deleteCategory(deleteCategoryId: number) {
        return apiClient.delete(`/categories/${deleteCategoryId}`)
    }

    static async updateCategory(id: number, param2: { name: string; description: string | undefined }) {
        return apiClient.put(`/categories/${id}`, param2)
    }

    static async createCategory(param: { name: string; description: string | undefined }) {
        return apiClient.post('/categories/', param)
    }

    // 拖拽排序分类
    static async reorderCategories(
        categories: Array<{ id: number; sort_order: number }>
    ): Promise<ApiResponse<{ message: string; updated_count: number }>> {
        return apiClient.put('/categories/reorder', {
            categories
        });
    }
}