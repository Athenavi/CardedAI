// Backup management types
import type {ApiResponse} from '@/lib/api/base-types';
import {apiClient} from './base-client';

export interface BackupFile {
    name: string;
    type: 'schema' | 'data' | 'all' | 'unknown';
    size: number;
    created_at: string;
}

// Backup management service
export class BackupService {
    static async getBackups(): Promise<ApiResponse<{ data: BackupFile[] }>> {
        return apiClient.get('/backup/list');
    }

    static async createBackup(type: 'schema' | 'data' | 'all' | 'database' | 'files'): Promise<ApiResponse<{
        message: string;
        filename: string
    }>> {
        // 根据类型选择不同的后端API
        let endpoint = '/backup/full';
        if (type === 'database') {
            endpoint = '/backup/database';
        } else if (type === 'files') {
            endpoint = '/backup/files';
        }
        return apiClient.post(endpoint, {backup_type: type});
    }

    static async deleteBackup(filename: string): Promise<ApiResponse<{ message: string }>> {
        return apiClient.delete(`/backup/delete?filename=${filename}`);
    }

    static async downloadBackup(filename: string): Promise<Blob> {
        const config = await import('@/lib/config').then(m => m.getConfig());
        const baseUrl = `${config.API_BASE_URL}${config.API_PREFIX}`;
        const response = await fetch(`${baseUrl}/backup/download/${filename}`, {
            method: 'GET',
            credentials: 'include',
        });

        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }

        return response.blob();
    }
}