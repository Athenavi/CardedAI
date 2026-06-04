// Article management service for Next.js frontend
import {apiClient} from './base-client';
import type {ApiResponse, Article, Pagination} from '@/lib/api/base-types';

// Article management types
export interface ArticleStats {
    total_articles: number;
    published_articles: number;
    draft_articles: number;
    total_views: number;
}

// Article management service
export class ArticleManagementService {
    static async getArticleStats(): Promise<ApiResponse<ArticleStats>> {
        return apiClient.get('/dashboard/blog-management/articles/stats');
    }

    static async getArticles(
        params?: { page?: number; per_page?: number; status?: string; search?: string; category_id?: number }
    ): Promise<ApiResponse<{ articles: Article[]; pagination: Pagination }>> {
        const response = await apiClient.get('/dashboard/blog-management/articles', params);

        // 确保返回正确的格式
        if (response.success && response.data && typeof response.data === 'object') {
            // 如果响应数据已经是期望格式
            if ('articles' in response.data && 'pagination' in response.data) {
                return response as ApiResponse<{ articles: Article[]; pagination: Pagination }>;
            } else {
                // 如果响应数据是纯数组或不同格式，构造期望的格式
                return {
                    ...response,
                    data: {
                        articles: Array.isArray(response.data) ? response.data : [],
                        pagination: ('pagination' in (response.data || {}) && (response.data as any)?.pagination) ? (response.data as any).pagination : {
                            current_page: params?.page || 1,
                            per_page: params?.per_page || 10,
                            total: Array.isArray(response.data) ? response.data.length : 0,
                            total_pages: 1,
                            has_next: false,
                            has_prev: false
                        }
                    }
                } as ApiResponse<{ articles: Article[]; pagination: Pagination }>;
            }
        }

        return {
            ...response,
            data: {
                articles: [],
                pagination: {
                    current_page: params?.page || 1,
                    per_page: params?.per_page || 10,
                    total: 0,
                    total_pages: 1,
                    has_next: false,
                    has_prev: false
                }
            }
        } as ApiResponse<{ articles: Article[]; pagination: Pagination }>;
    }

    static async deleteArticle(id: number): Promise<ApiResponse<any>> {
        return apiClient.delete(`/dashboard/blog-management/articles/${id}`);
    }

    // 批量操作文章
    static async batchOperation(
        operation: 'delete' | 'publish' | 'draft' | 'feature' | 'unfeature',
        articleIds: number[]
    ): Promise<ApiResponse<{ message: string; operation: string; updated_count: number }>> {
        // 根据操作类型映射到不同的后端API
        let endpoint = '';
        switch (operation) {
            case 'delete':
                endpoint = '/admin/batch/articles/delete';
                break;
            case 'publish':
            case 'draft':
                endpoint = '/admin/batch/articles/update-status';
                break;
            case 'feature':
            case 'unfeature':
                // 可能需要使用其他端点，这里暂时使用update-status
                endpoint = '/admin/batch/articles/update-status';
                break;
            default:
                endpoint = '/admin/batch/articles/delete';
        }

        return apiClient.post(endpoint, {
            article_ids: articleIds,
            operation
        });
    }

    // 拖拽排序文章
    static async reorderArticles(
        articles: Array<{ id: number; sort_order: number }>
    ): Promise<ApiResponse<{ message: string; updated_count: number }>> {
        return apiClient.post('/admin/batch/articles/update-sort', {
            articles
        });
    }
}