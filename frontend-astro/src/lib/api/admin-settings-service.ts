// Admin Settings Service for Next.js frontend
import {apiClient} from './base-client';
import type {ApiResponse} from '@/lib/api/base-types';

export interface Setting {
    key: string;
    value: string;
}

export interface Menu {
    id: number;
    name: string;
    slug: string;
    description?: string;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface MenuItem {
    id: number;
    title: string;
    url: string;
    target: string;
    parent_id?: number;
    order_index: number;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
    menu_id: number;
}

export interface Page {
    id: number;
    title: string;
    slug: string;
    content?: string;
    excerpt?: string;
    template: string;
    status: number;
    parent_id?: number;
    order_index: number;
    is_sticky?: boolean;
    meta_title?: string;
    meta_description?: string;
    meta_keywords?: string;
    author: {
        username: string;
    };
    created_at: string;
    updated_at?: string;
}

export interface AdminSettingsData {
    settings: Record<string, string>;
    menus: Menu[];
    menu_items: Record<string, MenuItem[]>;  // 按菜单ID分组的菜单项
    pages: Page[];
}

export class AdminSettingsService {
    static async getSettings(): Promise<ApiResponse<AdminSettingsData>> {
        return apiClient.get('/admin/settings/');
    }

    static async updateSettings(settings: Record<string, string>): Promise<ApiResponse<{ message: string }>> {
        return apiClient.post('/admin/settings/', {settings});
    }

    static async createMenu(menuData: Omit<Menu, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Menu>> {
        return apiClient.post('/admin/settings/menus', menuData);
    }

    static async updateMenu(menuId: number, menuData: Partial<Menu>): Promise<ApiResponse<Menu>> {
        return apiClient.put(`/admin/settings/menus/${menuId}`, menuData);
    }

    static async deleteMenu(menuId: number): Promise<ApiResponse<{ message: string }>> {
        return apiClient.delete(`/admin/settings/menus/${menuId}`);
    }

    static async createPage(pageData: Omit<Page, 'id' | 'author' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Page>> {
        return apiClient.post('/admin/settings/pages', pageData);
    }

    static async updatePage(pageId: number, pageData: Partial<Page>): Promise<ApiResponse<Page>> {
        return apiClient.put(`/admin/settings/pages/${pageId}`, pageData);
    }

    static async deletePage(pageId: number): Promise<ApiResponse<{ message: string }>> {
        return apiClient.delete(`/admin/settings/pages/${pageId}`);
    }

    static async createMenuItem(menuItemData: Omit<MenuItem, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<MenuItem>> {
        return apiClient.post('/admin/settings/menu-items', menuItemData);
    }

    static async updateMenuItem(menuItemId: number, menuItemData: Partial<MenuItem>): Promise<ApiResponse<MenuItem>> {
        return apiClient.put(`/admin/settings/menu-items/${menuItemId}`, menuItemData);
    }

    static async deleteMenuItem(menuItemId: number): Promise<ApiResponse<{ message: string }>> {
        return apiClient.delete(`/admin/settings/menu-items/${menuItemId}`);
    }
}