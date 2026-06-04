// Utility functions for API
import type {ApiResponse} from '@/lib/api/base-types';

// Helper function to normalize API responses
export function normalizeApiResponse<T>(response: ApiResponse<T>, defaultData: T): ApiResponse<T> {
    if (response.success && response.data) {
        return response;
    } else {
        return {
            ...response,
            data: defaultData,
            success: response.success || false
        };
    }
}