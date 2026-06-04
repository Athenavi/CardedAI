/**
 * 认证工具函数
 */

/**
 * 通用 cookie 读取
 */
export function getCookie(name: string): string | null {
    if (typeof document === 'undefined') return null;
    for (const c of document.cookie.split(';')) {
        const [n, v] = c.trim().split('=');
        if (n === name && v) return decodeURIComponent(v);
    }
    return null;
}

/**
 * 通用 cookie 写入
 */
export function setCookie(name: string, value: string, maxAgeSec: number): void {
    if (typeof document === 'undefined') return;
    document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeSec}; SameSite=Lax`;
}

/**
 * 从 cookie 获取 access_token
 */
export function getAccessTokenFromCookie(): string | null {
    if (typeof document === 'undefined') return null;

    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'access_token' && value) {
            return decodeURIComponent(value);
        }
    }
    return null;
}

/**
 * 从 cookie 获取 refresh_token
 */
export function getRefreshTokenFromCookie(): string | null {
    if (typeof document === 'undefined') return null;

    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'refresh_token' && value) {
            return decodeURIComponent(value);
        }
    }
    return null;
}

/**
 * 清除认证 cookie
 */
export function clearAuthCookies(): void {
    if (typeof document === 'undefined') return;
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/';
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/';
}

/**
 * 检查用户是否已登录
 */
export function isLoggedIn(): boolean {
    return getAccessTokenFromCookie() !== null;
}

/**
 * 保存 token 到 cookie
 */
export function saveTokens(accessToken: string, refreshToken?: string): void {
    if (typeof window === 'undefined') return;

    const expirationDate = new Date();
    expirationDate.setTime(expirationDate.getTime() + (60 * 60 * 1000));
    document.cookie = `access_token=${accessToken}; expires=${expirationDate.toUTCString()}; path=/; SameSite=Lax;`;

    if (refreshToken) {
        const refreshExpirationDate = new Date();
        refreshExpirationDate.setTime(refreshExpirationDate.getTime() + (7 * 24 * 60 * 60 * 1000));
        document.cookie = `refresh_token=${refreshToken}; expires=${refreshExpirationDate.toUTCString()}; path=/; SameSite=Lax;`;
    }
}
