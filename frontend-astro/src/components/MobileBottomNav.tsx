/**
 * 移动端底部导航栏 - React 岛屿（Editorial minimal）
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
      {name: '标签', href: '/tags', icon: MessageSquare},
        {name: '创建', href: '/admin/editor', icon: PlusSquare},
        {name: '我的', href: '/profile', icon: User},
    ];

    return (
      <nav
        className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/95 md:hidden"
        style={{paddingBottom: 'env(safe-area-inset-bottom, 0px)'}}
      >
        <div className="flex h-16 items-center justify-around">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;
                    return (
                      <a
                        key={item.href}
                        href={item.href}
                        className={`flex flex-1 flex-col items-center justify-center gap-1 py-2 text-[11px] tracking-wide transition-colors ${
                          isActive
                            ? 'text-primary'
                            : 'text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        <Icon className="h-5 w-5"/>
                            <span>{item.name}</span>
                        </a>
                    );
                })}
            </div>
        </nav>
    );
};

export default MobileBottomNav;
