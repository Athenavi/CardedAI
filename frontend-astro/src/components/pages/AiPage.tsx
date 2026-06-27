'use client';

import React from 'react';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {ChatArea} from '@/components/pages/admin/AdminAI';

/**
 * 公开 AI 聊天页面（无需管理员权限，只需登录）
 */
export default function AiPage() {
  return (
    <AuthGuard>
      <QueryProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
          {/* Simple header */}
          <header className="h-14 flex items-center px-4 lg:px-6 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex-shrink-0">
            <div className="flex items-center gap-3">
              <a href="/" className="text-sm font-bold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                ← 返回首页
              </a>
              <span className="text-gray-300 dark:text-gray-600">|</span>
              <h1 className="text-base font-semibold text-gray-900 dark:text-white">
                AI 助手
              </h1>
            </div>
          </header>
          {/* Chat area */}
          <main className="flex-1 p-4 lg:p-6 overflow-hidden">
            <div className="h-full max-w-4xl mx-auto flex flex-col">
              <ChatArea/>
            </div>
          </main>
        </div>
      </QueryProvider>
    </AuthGuard>
  );
}
