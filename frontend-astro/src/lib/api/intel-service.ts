// Intel (情报引擎) service for frontend
import {apiClient} from './base-client';
import type {ApiResponse} from '@/lib/api/base-types';

// ===== 情报引擎数据类型 =====

export interface IntelSource {
    id: number;
    name: string;
    source_type: string;
    url?: string;
    config?: Record<string, any>;
    is_active: boolean;
    last_collected_at?: string;
    created_at: string;
    updated_at?: string;
}

export interface CollectedItem {
    id: number;
    source_id: number;
    source_name?: string;
    title: string;
    url?: string;
    content_raw?: string;
    content_cleaned?: string;
    content_hash?: string;
    metadata_json?: string;
    status: string; // raw, cleaned, analyzed, error
    collected_at?: string;
    analyzed_at?: string;
}

export interface Intelligence {
    id: number;
    title: string;
    summary?: string;
    category?: string;
    sentiment?: string; // positive, negative, neutral
    importance_score?: number; // 0-5 (Numeric)
    item_ids?: string; // JSON array of related collected item IDs
    tags?: string; // comma-separated tags
    source_urls?: string; // JSON array of source URLs
    created_at: string;
}

export interface Briefing {
    id: number;
    briefing_type: string; // daily, weekly, monthly, topic
    title: string;
    content: string;
    topic?: string;
    date_range_start?: string;
    date_range_end?: string;
    items_count: number;
    created_at: string;
}

export interface AlertRule {
    id: number;
    name: string;
    rule_type: string; // keyword, sentiment, threshold
    conditions: Record<string, any>;
    actions: Record<string, any>;
    is_active: boolean;
    last_triggered_at?: string;
    created_at: string;
}

export interface AlertEvent {
    id: number;
    rule_id: number;
    rule_name?: string;
    event_type: string;
    message: string;
    data?: Record<string, any>;
    created_at: string;
}

export interface IntelStats {
    sources: { total: number; active: number };
    collected_items: { total: number; by_status: Record<string, number> };
    intelligence: { total: number; by_sentiment: Record<string, number>; by_category: Record<string, number> };
    briefings: { total: number };
    alert_rules: { total: number; active: number };
}

// ===== 情报引擎 API 服务 =====

export class IntelService {
    // --- 数据源管理 ---
    static async getSources(params?: {
        page?: number;
        per_page?: number;
        source_type?: string;
        is_active?: boolean;
    }): Promise<ApiResponse<IntelSource[]>> {
        return apiClient.get('/intel/sources', params);
    }

    static async getSource(sourceId: number): Promise<ApiResponse<IntelSource>> {
        return apiClient.get(`/intel/sources/${sourceId}`);
    }

    static async createSource(data: {
        name: string;
        source_type: string;
        url?: string;
        config?: Record<string, any>;
    }): Promise<ApiResponse<IntelSource>> {
        return apiClient.post('/intel/sources', data);
    }

    static async updateSource(sourceId: number, data: {
        name?: string;
        url?: string;
        config?: Record<string, any>;
        is_active?: boolean;
    }): Promise<ApiResponse<IntelSource>> {
        return apiClient.put(`/intel/sources/${sourceId}`, data);
    }

    static async deleteSource(sourceId: number): Promise<ApiResponse<void>> {
        return apiClient.delete(`/intel/sources/${sourceId}`);
    }

    static async triggerCollect(sourceId: number): Promise<ApiResponse<any>> {
        return apiClient.post(`/intel/sources/${sourceId}/collect`);
    }

    // --- 采集条目 ---
    static async getItems(params?: {
        page?: number;
        per_page?: number;
        source_id?: number;
        status?: string;
    }): Promise<ApiResponse<CollectedItem[]>> {
        return apiClient.get('/intel/items', params);
    }

    // --- 情报数据 ---
    static async getIntelligence(params?: {
        page?: number;
        per_page?: number;
        category?: string;
        sentiment?: string;
        query?: string;
    }): Promise<ApiResponse<Intelligence[]>> {
        return apiClient.get('/intel/intelligence', params);
    }

    static async getIntelligenceDetail(intelId: number): Promise<ApiResponse<Intelligence>> {
        return apiClient.get(`/intel/intelligence/${intelId}`);
    }

    // --- 简报 ---
    static async getBriefings(params?: {
        page?: number;
        per_page?: number;
        briefing_type?: string;
    }): Promise<ApiResponse<Briefing[]>> {
        return apiClient.get('/intel/briefings', params);
    }

    static async getBriefingDetail(briefingId: number): Promise<ApiResponse<Briefing>> {
        return apiClient.get(`/intel/briefings/${briefingId}`);
    }

    static async generateBriefing(params?: {
        briefing_type?: string;
        topic?: string;
        days?: number;
    }): Promise<ApiResponse<Briefing>> {
        const qs = params ? '?' + new URLSearchParams(params as any).toString() : '';
        return apiClient.post(`/intel/briefings/generate${qs}`);
    }

    // --- 预警规则 ---
    static async getAlertRules(params?: {
        page?: number;
        per_page?: number;
        is_active?: boolean;
    }): Promise<ApiResponse<AlertRule[]>> {
        return apiClient.get('/intel/alerts/rules', params);
    }

    static async createAlertRule(data: {
        name: string;
        rule_type: string;
        conditions: Record<string, any>;
        actions: Record<string, any>;
    }): Promise<ApiResponse<AlertRule>> {
        return apiClient.post('/intel/alerts/rules', data);
    }

    static async getAlertEvents(params?: {
        page?: number;
        per_page?: number;
        rule_id?: number;
    }): Promise<ApiResponse<AlertEvent[]>> {
        return apiClient.get('/intel/alerts/events', params);
    }

    // --- 分析触发 ---
    static async triggerAnalysis(sourceId: number): Promise<ApiResponse<any>> {
        return apiClient.post(`/intel/analyze/${sourceId}`);
    }

    static async analyzeAllPending(): Promise<ApiResponse<any>> {
        return apiClient.post('/intel/analyze-pending');
    }

    // --- 统计 ---
    static async getStats(): Promise<ApiResponse<IntelStats>> {
        return apiClient.get('/intel/stats');
    }
}
