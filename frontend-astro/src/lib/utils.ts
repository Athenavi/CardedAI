import {type ClassValue, clsx} from "clsx";
import {twMerge} from "tailwind-merge";
import {getConfig} from "./config";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/**
 * 将相对媒体路径转为完整 URL（自动拼接 API_BASE_URL）
 */
export function getFullMediaUrl(url: string | null | undefined): string {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    const config = getConfig();
    return `${config.API_BASE_URL}${url}`;
}

/**
 * 格式化日期字符串为中文本地时间
 */
export function formatDateTime(dateStr: string): string {
    return new Date(dateStr).toLocaleString('zh-CN');
}

export function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export function timeAgo(dateStr: string): string {
    const now = Date.now();
    const diff = now - new Date(dateStr).getTime();
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return '刚刚';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} 分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} 小时前`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days} 天前`;
    const months = Math.floor(days / 30);
    if (months < 12) return `${months} 个月前`;
    return `${Math.floor(months / 12)} 年前`;
}

export function truncate(str: string, len: number): string {
    return str.length > len ? str.slice(0, len) + '…' : str;
}

export function slugify(text: string): string {
    return text.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-').replace(/^-|-$/g, '');
}
