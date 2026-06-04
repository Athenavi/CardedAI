// Article service for Next.js frontend
import {apiClient} from './base-client';
import type {ApiResponse, Article, Category, Pagination} from '@/lib/api/base-types';


// Contribution Service
export interface ContributionData {
    aid: number;
    contribute_type: string;
    contribute_language: string;
    contribute_title: string;
    contribute_slug: string;
    contribute_content: string;
}

export interface ContributionResponse {
    message: string;
    i18n_id?: number;
}

export class ContributionService {
    static async getContributionInfo(articleId: number | string): Promise<ApiResponse<{ aid: number }>> {
        return apiClient.get(`/articles/contribute/${articleId}`);
    }

    static async submitContribution(articleId: number | string, data: Omit<ContributionData, 'aid'>): Promise<ApiResponse<ContributionResponse>> {
        return apiClient.post(`/articles/contribute/${articleId}`, data);
    }
}


export interface ArticleStats {
    total_articles: number;
    published_articles: number;
    draft_articles: number;
    total_views: number;
}

// Specific service classes
export class ArticleService {
    static async getHomeArticles(params?: { page?: number; per_page?: number }): Promise<ApiResponse<{
        data: Article[],
        pagination: Pagination
    }>> {
        const response = await apiClient.get('/home/articles', params);

        // 数据转换函数：将 tags_list 转换为 tags
        const transformArticle = (article: any): Article => {
            return {
                ...article,
                tags: article.tags_list || article.tags || [],
            };
        };

        // 处理后端返回的包装格式
        if (response.success && response.data && typeof response.data === 'object' && 'data' in response.data && 'pagination' in response.data) {
            const dataObj = response.data as any;
            const transformedArticles = (dataObj.data || []).map(transformArticle);
            return {
                ...response,
                data: {
                    data: transformedArticles,
                    pagination: dataObj.pagination
                }
            };
        }

        // 如果响应不符合预期格式，返回默认值
        return {
            ...response,
            data: {
                data: [],
                pagination: {
                    current_page: params?.page || 1,
                    per_page: params?.per_page || 10,
                    total: 0,
                    total_pages: 1,
                    has_next: false,
                    has_prev: false
                }
            }
        } as ApiResponse<{ data: Article[], pagination: Pagination }>;
    }

    static async getArticle(id: number | string): Promise<ApiResponse<Article>> {
        return apiClient.get(`/articles/${id}`);
    }

    static async getArticles(params?: {
        page?: number;
        per_page?: number;
        search?: string;
        category_id?: number
    }): Promise<ApiResponse<{ data: Article[], pagination: Pagination }>> {
        const response = await apiClient.get('/articles', params);

        console.log('🔵 ArticleService.getArticles 原始响应:', response);
        console.log('🔍 response.data 类型:', Array.isArray(response.data) ? 'Array' : typeof response.data);
        console.log('🔍 response.pagination 是否存在:', !!response.pagination);

        // 数据转换函数：将 tags_list 转换为 tags
        const transformArticle = (article: any): Article => {
            return {
                ...article,
                tags: article.tags_list || article.tags || [],
            };
        };

        // 情况 1：后端返回的是 { data: [], pagination: {} } 在 response 层级
        if (response.success && Array.isArray(response.data) && response.pagination) {
            console.log('✅ 使用标准格式：response.data 是数组，response.pagination 存在');
            // 转换数据中的 tags_list 为 tags
            const transformedData = response.data.map(transformArticle);
            return {
                ...response,
                data: {
                    data: transformedData,
                    pagination: response.pagination
                }
            } as ApiResponse<{ data: Article[], pagination: Pagination }>;
        }
        // 情况 2：response.data 是嵌套的对象 { data: { data: [], pagination: {} } }
        else if (response.success && response.data && typeof response.data === 'object' && !Array.isArray(response.data)) {
            console.log('⚠️ 使用嵌套格式：response.data 是对象');
            const dataObj = response.data as any;
            if ('data' in dataObj && 'pagination' in dataObj) {
                const transformedArticles = (dataObj.data || []).map(transformArticle);
                return {
                    ...response,
                    data: {
                        data: transformedArticles,
                        pagination: dataObj.pagination || {
                            current_page: params?.page || 1,
                            per_page: params?.per_page || 10,
                            total: 0,
                            total_pages: 1,
                            has_next: false,
                            has_prev: false
                        }
                    }
                } as ApiResponse<{ data: Article[], pagination: Pagination }>;
            }
        }
        // 情况 3：response.data 是纯数组（没有 pagination）
        else if (response.success && Array.isArray(response.data)) {
            console.log('⚠️ 使用数组格式：只有数组，没有 pagination');
            const transformedData = response.data.map(transformArticle);
            return {
                ...response,
                data: {
                    data: transformedData,
                    pagination: {
                        current_page: params?.page || 1,
                        per_page: params?.per_page || 10,
                        total: transformedData.length,
                        total_pages: 1,
                        has_next: false,
                        has_prev: false
                    }
                }
            } as ApiResponse<{ data: Article[], pagination: Pagination }>;
        }

        // 默认返回空数据
        console.log('❌ 未匹配任何格式，返回空数据');
        return {
            ...response,
            data: {
                data: [],
                pagination: {
                    current_page: params?.page || 1,
                    per_page: params?.per_page || 10,
                    total: 0,
                    total_pages: 1,
                    has_next: false,
                    has_prev: false
                }
            }
        } as ApiResponse<{ data: Article[], pagination: Pagination }>;
    }

    static async getEditArticleData(id: number | string): Promise<ApiResponse<{
        categories: Category[];
        article?: {
            id: number;
            title: string;
            slug: string;
            excerpt?: string;
            cover_image?: string;
            category_id: number;
            user_id: number;
            views: number;
            likes: number;
            tags?: string[];
            status: number;
            created_at: string;
            updated_at: string;
            hidden: boolean;
            is_vip_only: boolean;
            required_vip_level: number;
            article_ad: string;
            is_featured: boolean;
        };
        content: string;
        vip_plans?: Array<{
            id: number;
            name: string;
            level: number;
            price: number;
        }>;
        domain?: string;
    }>> {
        return apiClient.get(`/articles/edit/${id}`);
    }

    static async updateArticle(id: number | string, formData: FormData): Promise<ApiResponse<{
        message: string;
        article_id: number;
    }>> {
        // 使用 FastAPI 的 PUT 端点
        return apiClient.request(`/articles/${id}`, {
            method: 'PUT',
            body: formData,
        });
    }

    static async getNewArticleData(): Promise<ApiResponse<{
        categories: Category[];
    }>> {
        return apiClient.get('/articles/new');
    }

    static async createArticle(formData: FormData): Promise<ApiResponse<{
        message: string;
        article_id: number;
    }>> {
        return apiClient.request('/articles', {
            method: 'POST',
            body: formData,
        });
    }

    static async getArticleWithI18n(id: number | string): Promise<ApiResponse<ArticleDetailResponse>> {
        const response = await apiClient.get(`/articles/${id}`);

        if (response.success && response.data) {
            // 适配返回的数据为 ArticleDetailResponse 格式
            const articleData = response.data as any;

            // 数据转换：将 tags_list 转换为 tags
            const transformArticle = (article: any): Article => {
                if (!article) return article;
                return {
                    ...article,
                    tags: article.tags_list || article.tags || [],
                };
            };

            // 构造 ArticleDetailResponse 格式的数据
            const adaptedResponse: ApiResponse<ArticleDetailResponse> = {
                ...response,
                data: {
                    article: transformArticle(articleData),
                    author: articleData.author || {
                        id: articleData.user_id,
                        username: "Unknown",
                        email: ""
                    },
                    aid: articleData.id,
                    i18n_versions: articleData.i18n_versions || []
                }
            };

            return adaptedResponse;
        }

        return response as ApiResponse<ArticleDetailResponse>;
    }

    static async getArticleBySlug(slug: string): Promise<ApiResponse<ArticleDetailResponse>> {
        const response = await apiClient.get(`/articles/p/${slug}`);

        console.log('🔍 getArticleBySlug - API响应:', response);
        console.log('🔍 response.success:', response.success);
        console.log('🔍 response.data:', response.data);

        if (response.success && response.data) {
            // 适配返回的数据为 ArticleDetailResponse 格式
            const articleData = response.data as any;

            console.log('🔍 articleData:', articleData);
            console.log('🔍 articleData.article:', articleData.article);
            console.log('🔍 articleData.author:', articleData.author);

            // 数据转换：将 tags_list 转换为 tags
            const transformArticle = (article: any): Article => {
                if (!article) return article;
                return {
                    ...article,
                    tags: article.tags_list || article.tags || [],
                };
            };

            // 构造 ArticleDetailResponse 格式的数据
            const adaptedResponse: ApiResponse<ArticleDetailResponse> = {
                ...response,
                data: {
                    article: transformArticle(articleData.article),
                    author: articleData.author,
                    aid: articleData.article?.id || 0,
                    i18n_versions: []
                }
            };

            console.log('✅ 转换后的数据:', adaptedResponse.data);
            return adaptedResponse;
        }

        console.log('❌ API返回失败或无数据');
        return response as ApiResponse<ArticleDetailResponse>;
    }
}


export interface ArticleDetailResponse {
    article: Article;
    author?: {
        id: number;
        username: string;
        email: string;
    };
    aid: number;
    article_id?: number; // 兼容字段
    article_title?: string; // 用于密码验证时显示标题
    excerpt?: string; // 用于密码验证时显示摘要
    requires_password?: boolean; // 是否需要密码
    i18n_versions?: I18nArticleVersion[];
}

export interface I18nArticleVersion {
    language_code: string;
    title: string;
    slug: string;
    excerpt?: string;
    content?: string;
}

export class ArticleManagementService {
    static async getArticleStats(): Promise<ApiResponse<ArticleStats>> {
        return apiClient.get('/dashboard/blog-management/articles/stats');
    }

    static async getArticles(
        params?: { page?: number; per_page?: number; status?: string; search?: string }
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
                        pagination: response.pagination || {
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
}