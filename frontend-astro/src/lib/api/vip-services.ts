import type {ApiResponse} from '@/lib/api/base-types';
import {apiClient} from './base-client';

export interface PremiumArticle {
    id: number;
    title: string;
    slug: string;
    excerpt?: string;
    cover_image?: string;
    views: number;
    likes: number;
    required_vip_level: number;
    created_at?: string;
    updated_at?: string;
    user_id: number;
    category_id: number;
    author: {
        id?: number;
        username: string;
    };
}

export interface PremiumContentResponse {
    active_status: boolean;
    current_vip_level: number;
    articles: PremiumArticle[];
}

// VIP types
export interface VIPPlan {
    id: number;
    name: string;
    description?: string;
    price: number;
    original_price?: number;
    duration_days: number;
    level: number;
    features?: string;
    is_active: boolean;
    daily_cost: number;
    created_at?: string;
    updated_at?: string;
}

export interface VIPFeature {
    id: number;
    code: string;
    name: string;
    description?: string;
    required_level: number;
    is_active: boolean;
    created_at?: string;
}

export interface VIPSubscription {
    id: number;
    user_id: number;
    plan_id: number;
    starts_at: string;
    expires_at: string;
    status: number;
    payment_amount?: number;
    transaction_id?: string;
    created_at?: string;
}

export interface VIPPlansResponse {
    plans: VIPPlan[];
    features: VIPFeature[];
}

export interface VIPFeaturesResponse {
    features_by_level: Record<number, VIPFeature[]>;
    features: VIPFeature[];
}

export interface MyVipSubscriptionResponse {
    active_subscription?: VIPSubscription;
    subscription_history: VIPSubscription[];
}

// VIP service
export class VIPService {
    static async getVipPlans(): Promise<ApiResponse<VIPPlansResponse>> {
        return apiClient.get('/membership/plans');
    }

    static async getVipFeatures(): Promise<ApiResponse<VIPFeaturesResponse>> {
        return apiClient.get('/membership/features');
    }

    static async getMySubscription(): Promise<ApiResponse<MyVipSubscriptionResponse>> {
        return apiClient.get('/membership/my-subscription');
    }

    static async getPremiumContent(): Promise<ApiResponse<PremiumContentResponse>> {
        return apiClient.get('/membership/premium-content');
    }
}


// Payment types
export interface CreatePaymentRequest {
    user_id: number;
    plan_id: number;
    payment_method: 'alipay' | 'wechat';
}

export interface PaymentData {
    pay_url?: string;
    qr_code?: string;
    order_id: string;
    amount: number;
    description: string;
}

export interface CreatePaymentResponse {
    payment_data: PaymentData;
}

// Payment service
export class PaymentService {
    static async createPayment(data: CreatePaymentRequest): Promise<ApiResponse<CreatePaymentResponse>> {
        // 后端没有直接的/payment/create，使用membership/subscribe代替
        return apiClient.post('/membership/subscribe', data);
    }
}
