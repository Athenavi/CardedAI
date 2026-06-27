'use client';

import React from 'react';
import {usePermissions} from './PermissionContext';
import {Lock, ShieldAlert} from 'lucide-react';

/**
 * AdminGuard — 管理员权限守卫遮罩
 *
 * 包裹需要管理员权限才能访问的页面区域。
 * - 非 staff/superuser 用户看到友好的权限提示遮罩
 * - staff/superuser 用户正常看到子内容
 */
export function AdminGuard({children}: {children: React.ReactNode}) {
  const {permissions, loading} = usePermissions();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-purple-600 border-t-transparent mb-3"/>
          <p className="text-sm text-gray-500">验证权限...</p>
        </div>
      </div>
    );
  }

  const isAdmin = permissions?.is_superuser || permissions?.is_staff;

  if (!permissions || !isAdmin) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center px-4">
        <div className="max-w-md text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
            <ShieldAlert className="w-8 h-8 text-amber-600 dark:text-amber-400"/>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            需要管理员权限
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 leading-relaxed">
            你当前的账户没有访问此页面的权限。
            {permissions?.username && (
              <>当前登录用户: <span className="font-medium text-gray-700 dark:text-gray-300">{permissions.username}</span></>
            )}
          </p>
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-4 text-left text-sm text-gray-500 dark:text-gray-400 space-y-2">
            <p className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-gray-400 shrink-0"/>
              此页面需要 <code className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-xs">is_staff=true</code> 或 <code className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-xs">is_superuser=true</code> 权限
            </p>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
