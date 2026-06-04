'use client';

import React, {useEffect, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';
import {getAccessTokenFromCookie, getRefreshTokenFromCookie, setCookie} from '@/lib/auth-utils';

/**
 * AuthGuard - 认证守卫组件
 * 包裹需要登录才能访问的页面，未登录自动跳转 /login
 */
export function AuthGuard({children}: {children: React.ReactNode}) {
  const [status, setStatus] = useState<'loading' | 'authenticated' | 'unauthenticated'>('loading');

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        // 1) 检查本地是否有 access_token
        let token = getAccessTokenFromCookie();
        if (!token) {
          // access_token 不存在，尝试用 refresh_token 刷新
          const refreshToken = getRefreshTokenFromCookie();
          if (refreshToken) {
            const refreshResult = await apiClient.post('/auth/token/refresh', {refresh: refreshToken});
            if (refreshResult.success && refreshResult.data) {
              const d = refreshResult.data as any;
              if (d.access_token) setCookie('access_token', d.access_token, 3600);
              if (d.refresh_token) setCookie('refresh_token', d.refresh_token, 604800);
              token = d.access_token;
            }
          }
        }
        if (!token) {
          if (!cancelled) setStatus('unauthenticated');
          return;
        }
        // 2) 验证 token 有效性
        const res = await apiClient.get('/users/me');
        if (res.success && res.data) {
          if (!cancelled) setStatus('authenticated');
        } else {
          if (!cancelled) setStatus('unauthenticated');
        }
      } catch {
        if (!cancelled) setStatus('unauthenticated');
      }
    };
    check();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (status === 'unauthenticated') {
      const next = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.replace(`/login?next=${next}`);
    }
  }, [status]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mb-3" />
          <p className="text-sm text-gray-500">验证登录状态...</p>
        </div>
      </div>
    );
  }

  if (status === 'unauthenticated') return null;

  return <>{children}</>;
}

