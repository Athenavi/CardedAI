/**
 * 语言切换器 - React 岛屿
 */

'use client';


import {getDirection} from '@/lib/i18n';
import type {Locale} from '@/lib/i18n';

const LanguageSwitcher = () => {
    const languages: { code: Locale; label: string; flag: string }[] = [
        {code: 'zh-CN', label: '简体中文', flag: '🇨🇳'},
        {code: 'en', label: 'English', flag: '🇺🇸'},
        {code: 'ar', label: 'العربية', flag: '🇸🇦'},
        {code: 'he', label: 'עברית', flag: '🇮🇱'},
    ];

    const switchLanguage = (locale: Locale) => {
        const direction = getDirection(locale);
        document.documentElement.lang = locale;
        document.documentElement.dir = direction;
        document.cookie = `locale=${locale}; path=/; SameSite=Lax`;
        window.location.reload();
    };

    return (
        <div className="flex items-center gap-3">
            {languages.map((lang) => (
                <button key={lang.code} onClick={() => switchLanguage(lang.code)}
                    className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors">
                    <span>{lang.flag}</span>
                    <span>{lang.label}</span>
                </button>
            ))}
        </div>
    );
};

export default LanguageSwitcher;
