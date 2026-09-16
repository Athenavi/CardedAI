'use client';

import React, {useEffect, useState} from 'react';
import {BookOpen, Home, Moon, Sun} from 'lucide-react';
import {cn} from '@/lib/utils';

const THEME_KEY = 'fastblog-theme';
const LOCALE_KEY = 'fastblog-locale';

const LOCALES = [
  {code: 'zh-CN' as const, label: '中', title: '简体中文'},
  {code: 'en' as const, label: 'EN', title: 'English'},
];

/**
 * 认证页顶栏 —— 只有品牌标识、返回站点、语言与主题四个元素。
 *
 * 与全站 Layout 的区别：没有导航菜单、搜索、页脚与 Cookie 提示，
 * 认证页因此保持完整沉浸感。
 */
export default function AuthTopBar() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [locale, setLocale] = useState<'zh-CN' | 'en'>('zh-CN');

  useEffect(() => {
    try {
      setTheme(document.documentElement.classList.contains('dark') ? 'dark' : 'light');
      const storedLocale = localStorage.getItem(LOCALE_KEY);
      if (storedLocale === 'en' || storedLocale === 'zh-CN') {
        setLocale(storedLocale);
      } else if (navigator.language.toLowerCase().startsWith('en')) {
        setLocale('en');
      }
    } catch {
      /* ignore */
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.classList.toggle('dark', nextTheme === 'dark');
    try {
      localStorage.setItem(THEME_KEY, nextTheme);
    } catch {
      /* ignore */
    }
  };

  const switchLocale = (next: 'zh-CN' | 'en') => {
    if (next === locale) return;
    try {
      localStorage.setItem(LOCALE_KEY, next);
    } catch {
      /* ignore */
    }
    document.cookie = `locale=${next}; path=/; SameSite=Lax`;
    document.documentElement.lang = next;
    document.documentElement.dir = 'ltr';
    window.location.reload();
  };

  return (
    <header className="border-b border-border/70 bg-background">
      <div className="mx-auto flex h-14 w-full max-w-[80rem] items-center justify-between px-5 sm:px-8">
        <a href="/" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-primary">
            <BookOpen className="h-4 w-4 text-white"/>
          </span>
          <span className="text-[15px] font-semibold tracking-tight text-foreground">Carded AI</span>
        </a>

        <div className="flex items-center gap-1">
          <div className="flex items-center" role="group" aria-label="语言 / Language">
            {LOCALES.map(({code, label, title}) => (
              <button
                key={code}
                type="button"
                title={title}
                aria-pressed={locale === code}
                onClick={() => switchLocale(code)}
                className={cn(
                  'h-8 min-w-[2rem] rounded-sm px-1.5 text-xs tracking-wide transition-colors',
                  locale === code
                    ? 'font-medium text-foreground'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {label}
              </button>
            ))}
          </div>

          <span className="mx-1.5 h-4 w-px bg-border" aria-hidden="true"/>

          <button
            type="button"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'}
            className="flex h-8 w-8 items-center justify-center rounded-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4"/> : <Moon className="h-4 w-4"/>}
          </button>

          <a
            href="/"
            aria-label="返回站点"
            title="返回站点"
            className="ml-1 flex h-8 w-8 items-center justify-center rounded-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <Home className="h-4 w-4"/>
          </a>
        </div>
      </div>
    </header>
  );
}
