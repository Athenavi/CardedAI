'use client';

import React, {createContext, useContext, useState, useCallback, useMemo, useEffect} from 'react';
import zhCN from '../locales/zh-CN.json';
import en from '../locales/en.json';

// ──────────────────────────────────────────────
//  基础常量 & 类型
// ──────────────────────────────────────────────

/** 支持的语言列表 */
export const locales = ['zh-CN', 'en', 'ar', 'he'] as const;
export type Locale = (typeof locales)[number];

/** 默认语言 */
export const defaultLocale: Locale = 'zh-CN';

/** RTL 语言列表 */
export const rtlLocales: Locale[] = ['ar', 'he'];

/** 翻译资源类型（嵌套对象，叶子节点为 string） */
interface TranslationDict {
  [key: string]: string | TranslationDict;
}

/** 翻译资源映射 */
const translationMap: Record<Locale, TranslationDict> = {
  'zh-CN': zhCN as TranslationDict,
  'en': en as TranslationDict,
  'ar': zhCN as TranslationDict,   // fallback to zh-CN until ar translation is ready
  'he': zhCN as TranslationDict,   // fallback to zh-CN until he translation is ready
};

// ──────────────────────────────────────────────
//  RTL 辅助函数（保持向后兼容）
// ──────────────────────────────────────────────

/** 检查语言是否为 RTL */
export function isRTL(locale: Locale): boolean {
  return rtlLocales.includes(locale);
}

/** 获取 HTML 方向属性 */
export function getDirection(locale: Locale): 'rtl' | 'ltr' {
  return isRTL(locale) ? 'rtl' : 'ltr';
}

// ──────────────────────────────────────────────
//  翻译函数核心逻辑
// ──────────────────────────────────────────────

/**
 * 通过点分路径获取嵌套对象中的值
 * 例如: resolveKey({ nav: { dashboard: '仪表盘' } }, 'nav.dashboard') => '仪表盘'
 */
function resolveKey(obj: TranslationDict, key: string): string | undefined {
  const parts = key.split('.');
  let current: string | TranslationDict | undefined = obj;

  for (const part of parts) {
    if (current === undefined || current === null || typeof current === 'string') {
      return undefined;
    }
    current = (current as TranslationDict)[part];
  }

  return typeof current === 'string' ? current : undefined;
}

/**
 * 在字符串中替换 {variable} 占位符
 * 例如: interpolate('至少 {min} 个字符', { min: 6 }) => '至少 6 个字符'
 */
function interpolate(template: string, params?: Record<string, string | number>): string {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, key: string) => {
    return params[key] !== undefined ? String(params[key]) : `{${key}}`;
  });
}

/**
 * 翻译函数
 * @param locale - 当前语言
 * @param key - 点分路径键名，如 'nav.dashboard'
 * @param params - 插值参数，如 { min: 6 }
 * @returns 翻译后的字符串，若找不到则返回 key 本身
 */
export function t(locale: Locale, key: string, params?: Record<string, string | number>): string {
  const dict = translationMap[locale] || translationMap[defaultLocale];
  const value = resolveKey(dict, key);
  if (value === undefined) {
    // 尝试回退到默认语言
    if (locale !== defaultLocale) {
      const fallback = resolveKey(translationMap[defaultLocale], key);
      if (fallback !== undefined) return interpolate(fallback, params);
    }
    return key; // 找不到翻译，返回 key 本身
  }
  return interpolate(value, params);
}

// ──────────────────────────────────────────────
//  React Context & Provider
// ──────────────────────────────────────────────

const STORAGE_KEY = 'fastblog-locale';

interface I18nContextValue {
  /** 当前语言 */
  locale: Locale;
  /** 切换语言 */
  setLocale: (locale: Locale) => void;
  /** 翻译函数 */
  t: (key: string, params?: Record<string, string | number>) => string;
  /** 当前方向 */
  direction: 'rtl' | 'ltr';
}

const I18nContext = createContext<I18nContextValue | null>(null);

/** 从 localStorage 读取语言偏好（仅客户端） */
function getInitialLocale(): Locale {
  if (typeof window === 'undefined') return defaultLocale;
  try {
    const stored = localStorage.getItem(STORAGE_KEY) as Locale | null;
    if (stored && locales.includes(stored)) return stored;
    // 尝试从浏览器语言推断
    const browserLang = navigator.language;
    if (browserLang.startsWith('zh')) return 'zh-CN';
    if (browserLang.startsWith('en')) return 'en';
    if (browserLang.startsWith('ar')) return 'ar';
    if (browserLang.startsWith('he')) return 'he';
  } catch {
    // SSR 或 localStorage 不可用
  }
  return defaultLocale;
}

export function I18nProvider({children}: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    try {
      localStorage.setItem(STORAGE_KEY, newLocale);
    } catch {
      // ignore
    }
    // 更新 html lang 和 dir 属性
    if (typeof document !== 'undefined') {
      document.documentElement.lang = newLocale;
      document.documentElement.dir = getDirection(newLocale);
    }
  }, []);

  // 初始化时同步 html 属性
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale;
      document.documentElement.dir = getDirection(locale);
    }
  }, [locale]);

  const translate = useCallback(
    (key: string, params?: Record<string, string | number>) => t(locale, key, params),
    [locale]
  );

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale,
      t: translate,
      direction: getDirection(locale),
    }),
    [locale, setLocale, translate]
  );

  return React.createElement(I18nContext.Provider, {value}, children);
}

/**
 * i18n hook — 在组件中使用翻译
 *
 * @example
 * ```tsx
 * const { t, locale, setLocale, direction } = useTranslation();
 * return <h1>{t('nav.dashboard')}</h1>;
 * ```
 */
export function useTranslation(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    // 若组件不在 I18nProvider 内，提供一个降级实现
    return {
      locale: defaultLocale,
      setLocale: () => {
      },
      t: (key, params) => t(defaultLocale, key, params),
      direction: getDirection(defaultLocale),
    };
  }
  return ctx;
}
