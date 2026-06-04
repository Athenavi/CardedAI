/**
 * 移动端底部导航栏 - React 岛屿
 * 适配 Astro：使用 <a> 替代 next/link, window.location 替代 usePathname
 */

'use client';

import {useEffect, useState} from 'react';
import {Compass, Home, MessageSquare, PlusSquare, User} from 'lucide-react';

const MobileBottomNav = () => {
    const [pathname, setPathname] = useState('/');
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        setPathname(window.location.pathname);
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    if (!isMobile) return null;

    const navItems = [
        {name: '首页', href: '/', icon: Home},
        {name: '探索', href: '/articles', icon: Compass},
        {name: '消息', href: '/messages', icon: MessageSquare},
        {name: '创建', href: '/admin/editor', icon: PlusSquare},
        {name: '我的', href: '/profile', icon: User},
    ];

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 md:hidden">
            <div className="flex items-center justify-around h-16">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;
                    return (
                        <a key={item.href} href={item.href}
                            className={`flex flex-col items-center justify-center px-3 py-2 text-xs transition-colors ${
                                isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                            }`}>
                            <Icon className="w-6 h-6 mb-1"/>
                            <span>{item.name}</span>
                        </a>
                    );
                })}
            </div>
        </nav>
    );
};

export default MobileBottomNav;
