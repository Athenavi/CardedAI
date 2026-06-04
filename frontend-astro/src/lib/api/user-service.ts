/**
 * 用户搜索服务
 * 用于 @提及功能获取用户列表
 */

import {apiClient} from './base-client';
import type {ApiResponse} from '@/lib/api/base-types';

export interface UserSuggestion {
    id: number;
    username: string;
    avatar_url?: string;
}

export interface UserSearchResponse {
    success: boolean;
    data?: {
        users: UserSuggestion[];
    };
    error?: string;
}

class UserService {
    /**
     * 搜索用户（用于 @提及）
     * @param query - 搜索关键词
     * @param limit - 返回数量限制
     */
    async searchUsers(query: string, limit: number = 10): Promise<ApiResponse<{ users: UserSuggestion[] }>> {
        try {
            // 如果查询为空，返回推荐用户
            if (!query || query.trim() === '') {
                const response = await apiClient.get('/users/recommendations', {
                    params: {limit},
                });
                return response as ApiResponse<{ users: UserSuggestion[] }>;
            }

            // 后端没有直接的 /users/search 端点，使用 /users/ 并传递搜索参数
            const response = await apiClient.get('/users/', {
                params: {q: query, limit, per_page: limit},
            });

            return response as ApiResponse<{ users: UserSuggestion[] }>;
        } catch (error) {
            console.error('[UserService] Failed to search users:', error);
            return {
                success: false,
                data: {users: []},
                error: error instanceof Error ? error.message : '搜索用户失败',
            };
        }
    }

    /**
     * 获取用户详细信息
     * @param userId - 用户ID
     */
    async getUserById(userId: number): Promise<ApiResponse<UserSuggestion>> {
        try {
            const response = await apiClient.get(`/users/${userId}`);
            return response as ApiResponse<UserSuggestion>;
        } catch (error) {
            console.error('[UserService] Failed to get user:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : '获取用户信息失败',
            };
        }
    }

    /**
     * 根据用户名获取用户
     * @param username - 用户名
     */
    async getUserByUsername(username: string): Promise<ApiResponse<UserSuggestion>> {
        try {
            // 后端没有直接的 /users/by-username/{username} 端点
            // 可以使用 /users/ 并传递用户名参数进行搜索
            const response = await apiClient.get('/users/', {
                params: {username: username, per_page: 1}
            });
            return response as ApiResponse<UserSuggestion>;
        } catch (error) {
            console.error('[UserService] Failed to get user by username:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : '获取用户信息失败',
            };
        }
    }
}

// 导出单例实例
export const userService = new UserService();
export default userService;
