// 版本信息服务
import {apiClient} from './base-client';

export interface VersionInfo {
    version: string;
    build_time: string;
    framework: string;
    node_version?: string;
    python_version?: string;
}

export interface AuthorInfo {
    maintainer: string;
    repository: string;
}

export interface Versions {
    frontend: VersionInfo;
    backend: VersionInfo;
    database: {
        version: string;
        migration_status: string;
    };
    author: AuthorInfo;
}

export interface FullVersionData {
    versions: Versions;
    timestamp: string;
}

export interface VersionSummary {
    frontend: string;
    backend: string;
    database: string;
    build_time?: string;
}

export class VersionService {
    static async getVersionInfo(): Promise<{ success: boolean; data?: FullVersionData; error?: string }> {
        try {
            const response = await apiClient.get<FullVersionData>('/misc/version');
            return {success: true, data: response.data};
        } catch (error: any) {
            return {
                success: false,
                error: error.response?.data?.detail || '获取版本信息失败'
            };
        }
    }

    static async getVersionSummary(): Promise<{ success: boolean; data?: VersionSummary; error?: string }> {
        try {
            const response = await apiClient.get<VersionSummary>('/misc/version-summary');
            return {success: true, data: response.data};
        } catch (error: any) {
            return {
                success: false,
                error: error.response?.data?.detail || '获取版本摘要失败'
            };
        }
    }

    static async checkForUpdates(): Promise<{
        success: boolean;
        data?: { has_update: boolean; latest_version?: string };
        error?: string
    }> {
        try {
            const response = await apiClient.get<{
                has_update: boolean;
                latest_version?: string
            }>('/misc/check-update');
            return {success: true, data: response.data};
        } catch (error: any) {
            return {
                success: false,
                error: error.response?.data?.detail || '检查更新失败'
            };
        }
    }
}