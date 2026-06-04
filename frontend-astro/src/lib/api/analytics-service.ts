import {apiClient} from './base-client';
import type {ApiResponse} from './base-types';

export interface OverviewStats {
    total_views: number;
    unique_visitors: number;
    avg_duration: number;
    bounce_rate: number;
    page_views_change?: number;
    visitors_change?: number;
}

export interface DailyTrend {
    date: string;
    views: number;
    visitors: number;
}

export interface TrafficSource {
    name: string;
    value: number;
    color?: string;
}

export interface DeviceStat {
    name: string;
    value: number;
    color?: string;
}

export interface PopularArticle {
    id: number;
    title: string;
    views: number;
    engagement?: number;
}

export interface CategoryDistribution {
    name: string;
    value: number;
}

export class AnalyticsService {
    // 获取概览统计数据
    static async getOverviewStats(days: number = 30): Promise<ApiResponse<OverviewStats>> {
        return apiClient.get(`/dashboard/analytics/overview?days=${days}`);
    }

    // 获取文章浏览量趋势
    static async getArticleViewsTrend(days: number = 7): Promise<ApiResponse<DailyTrend[]>> {
        return apiClient.get(`/dashboard/analytics/article-views-trend?days=${days}`);
    }

    // 获取热门文章
    static async getPopularArticles(limit: number = 10, days: number = 7): Promise<ApiResponse<PopularArticle[]>> {
        return apiClient.get(`/dashboard/analytics/popular-articles?limit=${limit}&days=${days}`);
    }

    // 获取分类分布
    static async getCategoryDistribution(): Promise<ApiResponse<CategoryDistribution[]>> {
        return apiClient.get('/dashboard/analytics/category-distribution');
    }

    // 获取流量来源
    static async getTrafficSources(days: number = 30): Promise<ApiResponse<TrafficSource[]>> {
        return apiClient.get(`/dashboard/analytics/traffic-sources?days=${days}`);
    }

    // 获取设备统计
    static async getDeviceStats(days: number = 30): Promise<ApiResponse<DeviceStat[]>> {
        return apiClient.get(`/dashboard/analytics/device-stats?days=${days}`);
    }

    // 获取用户活动
  static async getUserActivity(days: number = 30): Promise<ApiResponse<unknown>> {
        return apiClient.get(`/dashboard/analytics/user-activity?days=${days}`);
    }

    // 获取内容表现
  static async getContentPerformance(days: number = 30): Promise<ApiResponse<unknown>> {
        return apiClient.get(`/dashboard/analytics/content-performance?days=${days}`);
    }
}
