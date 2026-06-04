// Dashboard service for Next.js frontend
import {apiClient} from './base-client';
import type {ApiResponse} from '@/lib/api/base-types';

// Dashboard data types
export interface DashboardStats {
    visitors: number;
    articles: number;
    comments: number;
    likes: number;
    users: number;
    new_users: number;
}

export interface RecentArticle {
    id: number;
    title: string;
    author: string;
    views: number;
    comments: number;
    created_at: string;
    status: string;
}

export interface Activity {
    id: number;
    user_name: string;
    activity_type: string;
    target_type: string;
    target_id: number;
    details: string;
    created_at: string;
    icon: string;
}

export interface AnalyticsData {
    stats: {
        visitors: number;
        page_views: number;
        bounce_rate: number;
        avg_session_duration: number;
    };
    top_pages: Array<{ title: string, views: number }>;
    top_referrers: Array<{ source: string, visitors: number }>;
    device_data: Array<{ device: string, percentage: number }>;
    country_data: Array<{ country: string, percentage: number }>;
    language_data: Array<{ language: string, percentage: number }>;
}

// Dashboard service
export class DashboardService {
    static async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
        return apiClient.get('/dashboard/stats');
    }

    static async getRecentArticles(): Promise<ApiResponse<RecentArticle[]>> {
        return apiClient.get('/dashboard/recent-articles');
    }

    static async getAnalyticsData(): Promise<ApiResponse<AnalyticsData>> {
        // 后端没有直接的/analytics/data端点，使用overview代替
        return apiClient.get('/dashboard/analytics/overview');
    }
}