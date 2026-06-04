import {apiClient} from './base-client';

/**
 * 广告位信息
 */
export interface AdSlot {
    slot_id: string;
    name: string;
    position: string;
    width: number;
    height: number;
    description: string;
    stats?: any;
}

/**
 * 广告信息
 */
export interface Ad {
    ad_id: string;
    title: string;
    slot_id: string;
    ad_type: 'image' | 'html' | 'adsense' | 'baidu';
    content: string;
    image_url?: string;
    link_url?: string;
    html_code?: string;
    start_date: string;
    end_date: string;
    priority: number;
    budget?: number;
    spent: number;
    status: 'active' | 'paused' | 'expired';
    created_at: string;
    updated_at: string;
}

/**
 * 广告联盟配置
 */
export interface AdNetworkConfig {
    enabled: boolean;
    publisher_id?: string;
    client_id?: string;
    union_id?: string;
}

/**
 * 收益报表
 */
export interface RevenueReport {
    total_impressions: number;
    total_clicks: number;
    total_revenue: number;
    ctr: number;
    ecpm: number;
    period: {
        start?: string;
        end?: string;
    };
}

/**
 * 广告系统API服务
 */
export const AdvertisementService = {
    /**
     * 获取所有广告位
     */
    async getAdSlots() {
        return apiClient.get<{ slots: AdSlot[] }>('/ads/slots');
    },

    /**
     * 创建广告
     */
    async createAd(data: {
        title: string;
        slot_id: string;
        ad_type: string;
        content?: string;
        image_url?: string;
        link_url?: string;
        html_code?: string;
        start_date?: string;
        end_date?: string;
        priority?: number;
        budget?: number;
    }) {
        return apiClient.post('/ads/create', data);
    },

    /**
     * 获取广告列表
     */
    async getAds(slotId?: string, status?: string) {
        const params: any = {};
        if (slotId) params.slot_id = slotId;
        if (status) params.status = status;
        return apiClient.get<{ ads: Ad[] }>('/ads/list', {params});
    },

    /**
     * 暂停广告
     */
    async pauseAd(adId: string) {
        return apiClient.post(`/ads/${adId}/pause`);
    },

    /**
     * 激活广告
     */
    async activateAd(adId: string) {
        return apiClient.post(`/ads/${adId}/activate`);
    },

    /**
     * 删除广告
     */
    async deleteAd(adId: string) {
        return apiClient.delete(`/ads/${adId}`);
    },

    /**
     * 获取广告统计
     */
    async getAdStats(adId: string) {
        return apiClient.get(`/ads/${adId}/stats`);
    },

    // ==================== 广告联盟配置 API ====================

    /**
     * 配置广告联盟
     */
    async configureAdNetwork(network: 'adsense' | 'baidu', config: AdNetworkConfig) {
        return apiClient.post('/ads/network/configure', {network, config});
    },

    /**
     * 获取广告联盟配置
     */
    async getAdNetworkConfig(network: 'adsense' | 'baidu') {
        return apiClient.get(`/ads/network/${network}/config`);
    },

    /**
     * 生成AdSense代码
     */
    async generateAdSenseCode(slotId: string, adFormat: string = 'auto') {
        return apiClient.get('/ads/network/adsense/code', {
            params: {slot_id: slotId, ad_format: adFormat}
        });
    },

    /**
     * 生成百度联盟代码
     */
    async generateBaiduCode(slotId: string) {
        return apiClient.get('/ads/network/baidu/code', {
            params: {slot_id: slotId}
        });
    },

    /**
     * 获取收益报表
     */
    async getRevenueReport(startDate?: string, endDate?: string) {
        const params: any = {};
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;
        return apiClient.get<RevenueReport>('/ads/revenue/report', {params});
    },
};
