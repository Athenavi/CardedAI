/**
 * 键盘快捷键 Hook
 * 适配 Astro：使用 window.addEventListener 替代 next/navigation
 */

'use client';

import {useEffect} from 'react';

type HotkeyMap = Record<string, (e: KeyboardEvent) => void>;

export function useHotkeys(hotkeys: HotkeyMap) {
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            const key = [
                e.ctrlKey || e.metaKey ? 'ctrl' : '',
                e.shiftKey ? 'shift' : '',
                e.altKey ? 'alt' : '',
                e.key.toLowerCase(),
            ].filter(Boolean).join('+');

            const handler = hotkeys[key];
            if (handler) {
                e.preventDefault();
                handler(e);
            }
        };

        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [hotkeys]);
}
