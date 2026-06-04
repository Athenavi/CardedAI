// API client for frontend

import {getConfig} from '@/lib/config';
import type {ApiResponse} from '@/lib/api/base-types';

// ─── Cookie helpers ──────────────────────────────
function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  for (const c of document.cookie.split(';')) {
    const [n, v] = c.trim().split('=');
    if (n === name && v) return decodeURIComponent(v);
  }
  return null;
}
function setCookie(name: string, value: string, maxAgeSec: number) {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=${value}; path=/; max-age=${maxAgeSec}; SameSite=Lax`;
}
function clearCookie(name: string) {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Lax`;
}

/** 构建完整 URL：补全 API 前缀 + 查询参数 */
function buildUrl(path: string, params?: Record<string, any>): string {
  const base = getConfig().API_BASE_URL || '';
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  const apiPath = path.startsWith('/api/') ? path : `/api/v2${!path.startsWith('/') ? '/' : ''}${path}`;
  let url = `${base}${apiPath}`;
  if (!params) return url;
  const qs = Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
      .join('&');
  return qs ? `${url}?${qs}` : url;
}

// ─── Token refresh state ──────────────────────────
let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function doRefreshToken(): Promise<boolean> {
  const refreshToken = getCookie('refresh_token');
  if (!refreshToken) return false;
  try {
    const base = getConfig().API_BASE_URL || '';
    const url = `${base}/api/v2/auth/token/refresh`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    if (!res.ok) return false;
    const json = await res.json();
    if (!json.success || !json.data) return false;
    const { access_token, refresh_token } = json.data;
    if (access_token) setCookie('access_token', access_token, 3600);
    if (refresh_token) setCookie('refresh_token', refresh_token, 604800);
    return true;
  } catch {
    return false;
  }
}

async function ensureTokenFresh(): Promise<boolean> {
  if (isRefreshing && refreshPromise) return refreshPromise;
  isRefreshing = true;
  refreshPromise = doRefreshToken();
  const result = await refreshPromise;
  isRefreshing = false;
  refreshPromise = null;
  return result;
}

async function request<T = any>(
    method: string,
    path: string,
    contentType?: string,
    body?: any,
    params?: Record<string, any>
): Promise<ApiResponse<T>> {
  try {
    const url = buildUrl(path, method === 'GET' ? params : undefined);
    const opts: RequestInit = {
      method,
      credentials: 'include',
    };

    if (body && method !== 'GET') {
      if (body instanceof FormData) {
        opts.body = body;
      } else if (contentType === 'application/x-www-form-urlencoded') {
        opts.headers = {'Content-Type': 'application/x-www-form-urlencoded'};
        opts.body = Object.entries(body)
            .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
            .join('&');
      } else {
        opts.headers = {'Content-Type': 'application/json'};
        opts.body = JSON.stringify(body);
      }
    }
    if (params && method !== 'GET') {
      // (uncommon case: query + body)
    }

    const accessToken = getCookie('access_token');
    if (accessToken) {
      opts.headers = { ...(opts.headers as Record<string, string> || {}), 'Authorization': `Bearer ${accessToken}` };
    }

    let res = await fetch(url, opts);

    // ── Auto-refresh on 401 ──
    if (res.status === 401 && !path.includes('/auth/token/refresh') && !path.includes('/auth/login')) {
      const refreshed = await ensureTokenFresh();
      if (refreshed) {
        const newToken = getCookie('access_token');
        if (newToken) {
          opts.headers = { ...(opts.headers as Record<string, string> || {}), 'Authorization': `Bearer ${newToken}` };
        }
        res = await fetch(url, opts);
      } else {
        // Refresh failed — clear cookies and redirect to login
        clearCookie('access_token');
        clearCookie('refresh_token');
        const currentPath = encodeURIComponent(window.location.pathname + window.location.search);
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
          window.location.href = `/login?next=${currentPath}`;
        }
        return { success: false, error: '登录已过期，请重新登录' };
      }
    }

    const text = await res.text();
    try { return JSON.parse(text); } catch { return {success: false, error: text}; }
  } catch (e: any) {
    return {success: false, error: e.message || '网络异常'};
  }
}

export const apiClient = {
  get: <T = any>(path: string, params?: Record<string, any>) => request<T>('GET', path, undefined, undefined, params),
  post: <T = any>(path: string, body?: any) => request<T>('POST', path, 'application/json', body),
  postForm: <T = any>(path: string, body?: Record<string, any>) => request<T>('POST', path, 'application/x-www-form-urlencoded', body),
  put: <T = any>(path: string, body?: any) => request<T>('PUT', path, 'application/json', body),
  patch: <T = any>(path: string, body?: any) => request<T>('PATCH', path, 'application/json', body),
  delete: <T = any>(path: string) => request<T>('DELETE', path),
    /** 通用请求方法，支持任意 method + FormData 等 */
    request: <T = any>(path: string, opts: { method?: string; body?: any; credentials?: string } = {}) => {
        const method = (opts.method || 'GET').toUpperCase();
        const contentType = opts.body instanceof FormData ? undefined : 'application/json';
        return request<T>(method, path, contentType, opts.body);
    },
};
