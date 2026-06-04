/**
 * 前端布局组件 - React 岛屿
 * 适配 Astro：移除了 Next.js 依赖，使用 props 接收 data
 */

'use client';

import React from 'react';
import {useDarkMode} from '@/lib/dark-mode-manager';

interface FrontendLayoutProps {
    children: React.ReactNode;
}

export const FrontendLayout: React.FC<FrontendLayoutProps> = ({children}) => {
    const {theme} = useDarkMode();

    return (
        <div className="min-h-screen flex flex-col"
             style={{
                 backgroundColor: theme === 'dark' ? '#111827' : '#f9fafb'
             }}>
            <main className="flex-grow">
                {children}
            </main>
        </div>
    );
};

export default FrontendLayout;
