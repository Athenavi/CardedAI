// 现代化首页API服务
import {apiClient} from './base-client';
import type {ApiResponse, Article, Category} from './base-types';

export interface HomePageConfig {
    hero: {
        title: string;
        subtitle: string;
        backgroundImage: string;
        ctaText: string;
        ctaLink: string;
    };
    sections: {
        featuredTitle: string;
        recentTitle: string;
        popularTitle: string;
        categoriesTitle: string;
    };
}

export interface HomePageData {
    featuredArticles: Article[];
    recentArticles: Article[];
    popularArticles: Article[];
    categories: Category[];
    stats: {
        totalArticles: number;
        totalUsers: number;
        totalViews: number;
    };
}

export const DEFAULT_HOME_CONFIG: HomePageConfig = {
    hero: {
        title: '欢迎来到 FastBlog',
        subtitle: '发现精彩内容，连接智慧世界。这里有丰富的技术文章和生活分享，与您一同探索无限可能。',
        backgroundImage: 'https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1920',
        ctaText: '开始探索',
        ctaLink: '/articles'
    },
    sections: {
        featuredTitle: '精选文章',
        recentTitle: '最新内容',
        popularTitle: '热门文章',
        categoriesTitle: '内容分类'
    }
};

export const DEFAULT_HOME_DATA: HomePageData = {
    featuredArticles: [],
    recentArticles: [],
    popularArticles: [],
    categories: [],
    stats: {
        totalArticles: 0,
        totalUsers: 0,
        totalViews: 0
    }
};

export class HomeService {
    /**
     * 获取完整的首页数据
     */
    static async getHomePageData(): Promise<ApiResponse<HomePageData>> {
        return apiClient.get<HomePageData>('/home/data');
    }

    /**
     * 获取首页配置
     */
    static async getHomePageConfig(): Promise<ApiResponse<HomePageConfig>> {
        return apiClient.get<HomePageConfig>('/home/config');
    }

    /**
     * 获取特色文章
     */
    static async getFeaturedArticles(limit: number = 4): Promise<ApiResponse<Article[]>> {
        return apiClient.get<Article[]>('/home/featured', {limit});
    }

    /**
     * 获取最新文章
     */
    static async getRecentArticles(params?: {
        page?: number;
        per_page?: number;
        category_id?: number;
    }): Promise<ApiResponse<{ articles: Article[]; pagination: any }>> {
        return apiClient.get<{ articles: Article[]; pagination: any }>('/home/recent', params);
    }

    /**
     * 获取热门文章
     */
    static async getPopularArticles(limit: number = 5): Promise<ApiResponse<Article[]>> {
        return apiClient.get<Article[]>('/home/popular', {limit});
    }

    /**
     * 获取所有分类
     */
    static async getCategories(): Promise<ApiResponse<Category[]>> {
        return apiClient.get<Category[]>('/home/categories');
    }

    /**
     * 获取网站统计数据
     */
    static async getSiteStats(): Promise<ApiResponse<{
        totalArticles: number;
        totalUsers: number;
        totalViews: number;
        todayViews: number;
    }>> {
        return apiClient.get('/home/stats');
    }

    /**
     * 订阅邮件通知
     * 注意：后端没有直接的/home/subscribe API，需要使用其他端点或实现新的API
     */
    static async subscribeEmail(email: string): Promise<ApiResponse<{ message: string }>> {
        // 暂时使用notifications/email/send作为替代，或者需要后端添加此API
        throw new Error('Home subscribe API not implemented yet. Please use /api/v2/notifications/email/send instead.');
    }

    /**
     * 搜索文章
     */
    static async searchArticles(query: string, params?: {
        page?: number;
        per_page?: number;
    }): Promise<ApiResponse<{ articles: Article[]; pagination: any }>> {
        return apiClient.get('/home/search', {q: query, ...params});
    }

    static async getHomeData(): Promise<{ success: boolean; data?: HomePageData; error?: string }> {
        try {
            const response = await apiClient.get<HomePageData>('/home/data');
            return {success: true, data: response.data};
        } catch (error: any) {
            return {
                success: false,
                error: error.response?.data?.detail || '获取首页数据失败'
            };
        }
    }

    static async getHomeConfig(): Promise<{ success: boolean; data?: HomePageConfig; error?: string }> {
        try {
            const response = await apiClient.get<HomePageConfig>('/home/config');
            return {success: true, data: response.data};
        } catch (error: any) {
            return {
                success: false,
                error: error.response?.data?.detail || '获取首页配置失败'
            };
        }
    }

    static async updateHomeConfig(config: Partial<HomePageConfig>): Promise<{
        success: boolean;
        data?: HomePageConfig;
        error?: string
    }> {
        try {
            const response = await apiClient.put<HomePageConfig>('/home/config', config);
            return {success: true, data: response.data};
        } catch (error: any) {
            return {
                success: false,
                error: error.response?.data?.detail || '更新首页配置失败'
            };
        }
    }
}

