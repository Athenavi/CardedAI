/**
 * API 基础类型定义
 */
export type {ApiResponse} from '@/lib/api/base-types';

export interface Pagination {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
    per_page: number;
    total: number;
}

export interface PaginatedResponse<T> {
    data: T[];
    pagination: Pagination;
}

// 文章类型
export interface Article {
    id: number;
    title: string;
    slug: string;
    content?: string;
    excerpt?: string;
    summary?: string;
    cover_image?: string;
    author_id?: number;
    author?: {
        id: number;
        username: string;
        avatar?: string;
    };
    category?: {
        id: number;
        name: string;
        slug: string;
    };
    tags?: string[];
    status?: string;
    views?: number;
    likes?: number;
    comments_count?: number;
    created_at?: string;
    updated_at?: string;
    published_at?: string;
}

// 分类类型
export interface Category {
    id?: number;
    name: string;
    slug?: string;
    description?: string;
    cover_image?: string;
    color?: string;
    article_count?: number;
    subscription_count?: number;
    created_at?: string;
    updated_at?: string;
}

// 用户类型
export interface User {
    id: number;
    username: string;
    email?: string;
    avatar?: string;
    bio?: string;
    role?: string;
    created_at?: string;
}
