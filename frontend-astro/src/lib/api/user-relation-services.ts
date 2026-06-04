import {apiClient} from './base-client';
import type {ApiResponse} from './base-types';

// User relation types
export interface UserRelation {
    id: number;
    username: string;
    email: string;
    bio?: string;
    profile_picture?: string;
}

export interface RelationWithDate {
    user: UserRelation;
    created_at: string;
}

export interface FollowToggleResponse {
    message: string;
}

export interface UserListResponse {
    users: UserRelation[];
    following_ids: number[];
}

export interface RelationCounts {
    fans_count: number;
    following_count: number;
}

export interface RelationListResponse {
    fans_list: RelationWithDate[];
    fans_count: number;
    following_list: RelationWithDate[];
    following_count: number;
}

export class RelationService {
    static async getFollowers(): Promise<ApiResponse<RelationListResponse>> {
        return apiClient.get('/users/me/followers');
    }

    static async getFollowing(): Promise<ApiResponse<RelationListResponse>> {
        return apiClient.get('/users/me/following');
    }

    static async getUsers(): Promise<ApiResponse<UserListResponse>> {
        // 后端没有直接的/relations/users，使用/users/代替
        return apiClient.get('/users/');
    }

    static async followUser(targetUserId: number): Promise<ApiResponse<FollowToggleResponse>> {
        return apiClient.post(`/users/${targetUserId}/follow`);
    }

    static async unfollowUser(targetUserId: number): Promise<ApiResponse<FollowToggleResponse>> {
        return apiClient.delete(`/users/${targetUserId}/follow`);
    }
}
