import {apiClient} from './base-client';

/**
 * 打赏记录
 */
export interface TipRecord {
    tip_id: string;
    from_user_id?: number;
    to_user_id?: number;
    article_id?: number;
    amount: number;
    message?: string;
    payment_method?: string;
    created_at: string;
}

/**
 * 打赏统计
 */
export interface TipStats {
    total_amount: number;
    tip_count: number;
    unique_supporters: number;
    average_tip: number;
}

/**
 * 余额信息
 */
export interface BalanceInfo {
    total_earned: number;
    total_withdrawn: number;
    pending_withdrawal: number;
    available_balance: number;
    min_withdrawal_amount: number;
    withdrawal_fee_rate: number;
}

/**
 * 提现记录
 */
export interface WithdrawalRecord {
    withdrawal_id: string;
    amount: number;
    fee: number;
    actual_amount: number;
    payment_method: string;
    status: 'pending' | 'processing' | 'completed' | 'rejected' | 'cancelled';
    created_at: string;
    processed_at?: string;
    admin_note?: string;
}

/**
 * 排行榜项
 */
export interface LeaderboardItem {
    user_id: number;
    total_amount: number;
    rank: number;
}

/**
 * 打赏系统API服务
 */
export const TippingService = {
    /**
     * 打赏文章
     */
    async tipArticle(articleId: number, amount: number, message?: string, paymentMethod: string = 'balance') {
        return apiClient.post('/ext/tipping/tip-article', {
            article_id: articleId,
            amount,
            message: message || '',
            payment_method: paymentMethod,
        });
    },

    /**
     * 获取文章打赏记录
     */
    async getArticleTips(articleId: number, limit: number = 50) {
        return apiClient.get(`/ext/tipping/article/${articleId}`, {params: {limit}});
    },

    /**
     * 获取我收到的打赏
     */
    async getMyReceivedTips(limit: number = 100) {
        return apiClient.get('/ext/tipping/my-received', {params: {limit}});
    },

    /**
     * 获取我的打赏统计
     */
    async getMyTipStats() {
        return apiClient.get('/ext/tipping/my-stats');
    },

    /**
     * 获取打赏排行榜
     */
    async getLeaderboard(period: string = 'all', limit: number = 100) {
        return apiClient.get('/ext/tipping/leaderboard', {params: {period, limit}});
    },

    /**
     * 获取预设打赏金额
     */
    async getPresetAmounts() {
        return apiClient.get('/ext/tipping/preset-amounts');
    },

    /**
     * 获取最近打赏记录
     */
    async getRecentTips(limit: number = 20) {
        return apiClient.get('/ext/tipping/recent', {params: {limit}});
    },

    // ==================== 提现相关 API ====================

    /**
     * 获取可提现余额
     */
    async getBalance() {
        return apiClient.get('/ext/tipping/balance');
    },

    /**
     * 申请提现
     */
    async requestWithdrawal(amount: number, paymentMethod: string = 'bank_transfer', accountInfo: any = {}) {
        return apiClient.post('/ext/tipping/withdraw', {
            amount,
            payment_method: paymentMethod,
            account_info: accountInfo,
        });
    },

    /**
     * 获取我的提现记录
     */
    async getMyWithdrawals(limit: number = 50) {
        return apiClient.get('/ext/tipping/my-withdrawals', {params: {limit}});
    },

    /**
     * 取消提现申请
     */
    async cancelWithdrawal(withdrawalId: string) {
        return apiClient.post(`/ext/tipping/cancel-withdrawal/${withdrawalId}`);
    },

    /**
     * 管理员处理提现申请
     */
    async processWithdrawal(withdrawalId: string, status: 'completed' | 'rejected', adminNote: string = '') {
        return apiClient.post('/ext/tipping/admin/process-withdrawal', {
            withdrawal_id: withdrawalId,
            status,
            admin_note: adminNote,
        });
    },
};
