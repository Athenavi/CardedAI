/**
 * 全局快捷键组件 - React 岛屿
 * 适配 Astro：使用 window.location 替代 next/navigation
 */

'use client';

import {useEffect} from 'react';

interface GlobalShortcutsProps {
    enabled?: boolean;
}

export function GlobalShortcuts({enabled = true}: GlobalShortcutsProps) {
    useEffect(() => {
        if (!enabled) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            // Ctrl+K: 搜索
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                window.location.href = '/search';
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [enabled]);

    return null;
}
