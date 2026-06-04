// User management service for Next.js frontend
import {apiClient} from './base-client';
import type {ApiResponse, Pagination, UserRole} from '@/lib/api/base-types';

// User management types
export interface UserWithRoles {
    id: number;
    username: string;
    email: string;
    bio?: string;
    profile_picture?: string;
    created_at: string;
    last_login?: string;
    is_active: boolean;
    is_superuser: boolean;
    media_count?: number;
    comment_count?: number;
    roles: UserRole[];
}

export interface UserManagementData {
    users: UserWithRoles[];
    pagination: Pagination;
}

// User management service
export class UserManagementService {
    static async getUsers(
        params?: { page?: number; per_page?: number; search?: string; role?: string }
    ): Promise<ApiResponse<UserManagementData>> {
        const response = await apiClient.get('/dashboard/user-management/users', params);

        // 确保返回正确的格式
        if (response.success && response.data && typeof response.data === 'object') {
            // 如果响应数据已经是期望格式
            if ('users' in response.data && 'pagination' in response.data) {
                return response as ApiResponse<UserManagementData>;
            } else {
                // 如果响应数据是纯数组或不同格式，构造期望的格式
                return {
                    ...response,
                    data: {
                        users: Array.isArray(response.data) ? response.data : [],
                        pagination: response.pagination || {
                            current_page: params?.page || 1,
                            per_page: params?.per_page || 10,
                            total: Array.isArray(response.data) ? response.data.length : 0,
                            total_pages: 1,
                            has_next: false,
                            has_prev: false
                        }
                    }
                } as unknown as ApiResponse<UserManagementData>;
            }
        }

        return {
            ...response,
            data: {
                users: [],
                pagination: {
                    current_page: params?.page || 1,
                    per_page: params?.per_page || 10,
                    total: 0,
                    total_pages: 1,
                    has_next: false,
                    has_prev: false
                }
            }
        } as ApiResponse<UserManagementData>;
    }

    static async createUser(userData: {
        username: string;
        email: string;
        password: string;
        bio?: string;
        profile_picture?: string;
    }): Promise<ApiResponse<UserWithRoles>> {
        // 后端可能没有直接创建用户的端点，需要使用其他端点
        throw new Error('Create user API not implemented yet');
    }

    static async updateUser(userId: number, userData: Partial<UserWithRoles>): Promise<ApiResponse<UserWithRoles>> {
        // 后端使用 /users/{user_id} 来更新用户资料
        return apiClient.put(`/users/${userId}`, userData);
    }

    static async deleteUser(userId: number): Promise<ApiResponse<{ message: string }>> {
        // 后端可能没有直接删除用户的端点
        throw new Error('Delete user API not implemented yet');
    }

    static async getUserById(userId: number, page: number = 1, perPage: number = 10): Promise<ApiResponse<never>> {
        try {
            return await apiClient.get(`/users/${userId}`, {page, per_page: perPage});
        } catch (error) {
            console.error(`Error fetching user profile for user ID ${userId}:`, error);
            return {
                success: false,
                requires_auth: false,
                error: error instanceof Error ? error.message : '获取用户资料失败'
            };
        }
    }
}

export class UserRoleService {
    static async assignRolesToUser(userId: number, roleIds: number[]): Promise<ApiResponse<{ message: string }>> {
        return apiClient.post(`/security/rbac/users/${userId}/roles`, {role_ids: roleIds});
    }
}