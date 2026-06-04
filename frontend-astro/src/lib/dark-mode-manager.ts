'use client';

import { useEffect, useState, useCallback } from 'react';

const STORAGE_KEY = 'fastblog-theme';
const DARK_CLASS = 'dark';

type Theme = 'light' | 'dark';

function getStoredTheme(): Theme | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v === 'light' || v === 'dark') return v;
  } catch {}
  return null;
}

function getSystemTheme(): Theme {
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
}

function resolveTheme(): Theme {
  return getStoredTheme() ?? getSystemTheme();
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.toggle(DARK_CLASS, theme === 'dark');
}

function storeTheme(theme: Theme) {
  try { localStorage.setItem(STORAGE_KEY, theme); } catch {}
}

export function useDarkMode() {
  const [theme, setThemeState] = useState<Theme>('light');

  // Hydrate from storage/system
  useEffect(() => {
    const t = resolveTheme();
    setThemeState(t);
    applyTheme(t);
  }, []);

  // Listen to system preference changes (only when user hasn't set a preference)
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      if (!getStoredTheme()) {
        const t = mq.matches ? 'dark' : 'light';
        setThemeState(t);
        applyTheme(t);
      }
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    applyTheme(t);
    storeTheme(t);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  }, [theme]);

  return { theme, setTheme, toggleTheme };
}
