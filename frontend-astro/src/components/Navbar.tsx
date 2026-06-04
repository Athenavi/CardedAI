/**
 * 导航栏组件 - 全面重构版
 * 特性：
 * - 多导航项（首页、文章、分类、关于）
 * - 搜索模态框（Cmd/Ctrl+K）
 * - 通知面板
 * - 用户头像菜单
 * - 滚动时毛玻璃效果
 * - 移动端响应式
 */

'use client';

import React, {useEffect, useRef, useState} from 'react';
import {AnimatePresence, motion} from 'framer-motion';
import {
  Bell,
  BookOpen,
  ChevronDown,
  Command,
  FolderTree,
  Home,
  Image as ImageIcon,
  LogOut,
  Moon,
  PenSquare,
  Search,
  Settings,
  Sun,
  User,
  X
} from 'lucide-react';
import {useDarkMode} from '@/lib/dark-mode-manager';
import {getAccessTokenFromCookie} from '@/lib/auth-utils';
import {MenuService, type MenuTreeItem} from '@/lib/api/menu-service';

interface NavbarProps {
  title?: string;
  subtitle?: string;
  showBackButton?: boolean;
  rightActions?: React.ReactNode;
}

const Navbar: React.FC<NavbarProps> = ({title, subtitle, showBackButton = false, rightActions}) => {
  const {theme, toggleTheme} = useDarkMode();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<unknown[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userAvatar, setUserAvatar] = useState<string | null>(null);
  const [username, setUsername] = useState('');
  const [pathname, setPathname] = useState('/');
  const [scrolled, setScrolled] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [navItems, setNavItems] = useState<Array<{ name: string; href: string; icon: React.ComponentType<any> }>>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // 根据菜单项标题/URL匹配图标
  const getIconForMenuItem = (title: string, url: string): React.ComponentType<any> => {
    const t = (title || '').toLowerCase();
    const u = (url || '').toLowerCase();
    if (t.includes('首页') || t.includes('home') || u === '/') return Home;
    if (t.includes('文章') || t.includes('blog') || t.includes('article') || u.includes('/article')) return BookOpen;
    if (t.includes('分类') || t.includes('categor') || u.includes('/categor')) return FolderTree;
    if (t.includes('关于') || t.includes('about') || u.includes('/about')) return User;
    if (t.includes('标签') || t.includes('tag') || u.includes('/tag')) return Search;
    if (t.includes('设置') || t.includes('setting') || u.includes('/setting')) return Settings;
    return BookOpen; // 默认图标
  };

  // 默认导航项（作为后备）
  const defaultNavItems = [
    {name: '首页', href: '/', icon: Home},
    {name: '文章', href: '/articles', icon: BookOpen},
    {name: '分类', href: '/categories', icon: FolderTree},
    {name: '关于', href: '/about', icon: User},
  ];

  useEffect(() => {
    setPathname(window.location.pathname);
    const token = getAccessTokenFromCookie();
    setIsLoggedIn(!!token);

    // Fetch user info if logged in
    if (token) {
      import('@/lib/config').then(({getConfig}) => {
        const {API_BASE_URL} = getConfig();
        return fetch(`${API_BASE_URL}/api/v2/users/me`, {
          headers: {Authorization: `Bearer ${token}`}
        })
          .then(r => r.json())
          .then(data => {
            if (data?.data) {
              setUserAvatar(data.data.avatar ? `${API_BASE_URL}${data.data.avatar}` : null);
              setUsername(data.data.username || '');
            }
          })
          .catch(() => {
          });
      });
    }
  }, []);

  // 从 API 动态获取导航菜单
  useEffect(() => {
    MenuService.getMainMenu().then(response => {
      if (response.success && response.data && response.data.length > 0) {
        const dynamicItems = response.data
          .filter((item: MenuTreeItem) => item.is_active !== false)
          .sort((a: MenuTreeItem, b: MenuTreeItem) => (a.order_index || 0) - (b.order_index || 0))
          .map((item: MenuTreeItem) => ({
            name: item.title || '',
            href: item.url || '#',
            icon: getIconForMenuItem(item.title || '', item.url || ''),
          }));
        if (dynamicItems.length > 0) {
          setNavItems(dynamicItems);
          return;
        }
      }
      // 如果获取失败或无数据，使用默认导航项
      setNavItems(defaultNavItems);
    }).catch(() => {
      setNavItems(defaultNavItems);
    });
  }, []);

  // Scroll detection for glass effect
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll, {passive: true});
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Keyboard shortcut: Cmd/Ctrl + K for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen(true);
      }
      if (e.key === 'Escape') {
        setIsSearchOpen(false);
        setIsUserMenuOpen(false);
        setNotifOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Focus search input when modal opens
  useEffect(() => {
    if (isSearchOpen) {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [isSearchOpen]);

  // Click outside to close dropdowns
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.user-menu-container')) setIsUserMenuOpen(false);
      if (!target.closest('.notif-container')) setNotifOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Search handler with debounce
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (!value.trim()) {
      setSearchResults([]);
      return;
    }
    setSearchLoading(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v2/search?q=${encodeURIComponent(value)}&per_page=5`);
        const data = await res.json();
        setSearchResults(data?.data?.articles || data?.data || []);
      } catch {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/search?q=${encodeURIComponent(searchQuery)}`;
    }
  };

  const userMenuItems = isLoggedIn ? [
    {name: '写文章', href: '/my/posts/create', icon: PenSquare},
    {name: '我的文章', href: '/my/posts', icon: BookOpen},
    {name: '媒体库', href: '/media', icon: ImageIcon},
    {name: '设置', href: '/settings', icon: Settings},
    {name: '个人资料', href: '/profile', icon: User},
  ] : [];

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-[9999] w-full transition-all duration-300 safe-top ${
          scrolled
            ? 'glass-strong shadow-md border-b border-gray-200/60 dark:border-gray-700/60'
            : 'bg-white/95 dark:bg-gray-950/95 border-b border-gray-100 dark:border-gray-900'
        }`}
        suppressHydrationWarning
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Nav */}
            <div className="flex items-center gap-6">
              {/* Logo */}
              <a href="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity group">
                <div
                  className="w-9 h-9 gradient-primary rounded-xl flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24"
                       stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                  </svg>
                </div>
                <span
                  className="text-xl font-bold text-gray-900 dark:text-white hidden sm:block tracking-tight">FastBlog</span>
              </a>

              {/* Page title (for admin pages) */}
              {title && (
                <div
                  className="ml-2 pl-4 border-l border-gray-200 dark:border-gray-800 max-w-[140px] sm:max-w-none truncate">
                  <h1 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white truncate">{title}</h1>
                  {subtitle &&
                    <p className="text-xs text-gray-500 dark:text-gray-400 hidden sm:block">{subtitle}</p>}
                </div>
              )}

              {/* Navigation Links */}
              <nav className="hidden md:flex items-center gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                  return (
                    <a
                      key={item.href}
                      href={item.href}
                      className={`relative px-3.5 py-2 rounded-lg transition-all duration-200 flex items-center gap-2 text-sm font-medium ${
                        isActive
                          ? 'text-blue-600 dark:text-blue-400 bg-blue-50/80 dark:bg-blue-900/20'
                          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100/80 dark:hover:bg-gray-800/50'
                      }`}
                    >
                      <Icon className="w-4 h-4"/>
                      <span>{item.name}</span>
                      {isActive && (
                        <motion.div
                          layoutId="activeNav"
                          className="absolute bottom-0 left-2 right-2 h-0.5 bg-blue-600 dark:bg-blue-400 rounded-full"
                        />
                      )}
                    </a>
                  );
                })}
              </nav>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-1.5">
              {rightActions}

              {/* Search Button */}
              <button
                onClick={() => setIsSearchOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm border border-gray-200 dark:border-gray-700"
                title="搜索 (⌘K)"
              >
                <Search className="w-4 h-4"/>
                <span className="hidden sm:inline text-gray-400">搜索...</span>
                <kbd
                  className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-[10px] font-mono text-gray-400">
                  <Command className="w-3 h-3"/>K
                </kbd>
              </button>

              {/* Notification Bell */}
              {isLoggedIn && (
                <div className="relative notif-container">
                  <button
                    onClick={() => {
                      setNotifOpen(!notifOpen);
                      setIsUserMenuOpen(false);
                    }}
                    className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors relative"
                    title="通知"
                  >
                    <Bell className="w-5 h-5"/>
                    <span
                      className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white dark:ring-gray-950"/>
                  </button>
                  <AnimatePresence>
                    {notifOpen && (
                      <motion.div
                        initial={{opacity: 0, y: -8, scale: 0.96}}
                        animate={{opacity: 1, y: 0, scale: 1}}
                        exit={{opacity: 0, y: -8, scale: 0.96}}
                        transition={{duration: 0.15}}
                        className="absolute right-0 mt-2 w-80 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden"
                      >
                        <div
                          className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                          <h3 className="font-semibold text-gray-900 dark:text-white text-sm">通知</h3>
                          <button
                            className="text-xs text-blue-600 hover:text-blue-700">全部标为已读
                          </button>
                        </div>
                        <div className="max-h-80 overflow-y-auto">
                          <div className="py-12 text-center text-gray-400 text-sm">
                            <Bell className="w-8 h-8 mx-auto mb-2 opacity-30"/>
                            暂无新通知
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                title={theme === 'dark' ? '切换为亮色' : '切换为暗色'}
                suppressHydrationWarning
              >
                <AnimatePresence mode="wait" initial={false}>
                  {theme === 'dark' ? (
                    <motion.span key="sun" initial={{rotate: -90, opacity: 0}}
                                 animate={{rotate: 0, opacity: 1}} exit={{rotate: 90, opacity: 0}}
                                 transition={{duration: 0.2}}>
                      <Sun className="w-5 h-5"/>
                    </motion.span>
                  ) : (
                    <motion.span key="moon" initial={{rotate: 90, opacity: 0}}
                                 animate={{rotate: 0, opacity: 1}} exit={{rotate: -90, opacity: 0}}
                                 transition={{duration: 0.2}}>
                      <Moon className="w-5 h-5"/>
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>

              {/* User Menu */}
              <div className="relative user-menu-container">
                {isLoggedIn ? (
                  <button
                    onClick={() => {
                      setIsUserMenuOpen(!isUserMenuOpen);
                      setNotifOpen(false);
                    }}
                    className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    {userAvatar ? (
                      <img src={userAvatar} alt=""
                           className="w-7 h-7 rounded-full object-cover ring-2 ring-gray-200 dark:ring-gray-700"/>
                    ) : (
                      <div
                        className="w-7 h-7 rounded-full gradient-primary flex items-center justify-center text-white text-xs font-bold">
                        {username ? username[0].toUpperCase() : 'U'}
                      </div>
                    )}
                    <ChevronDown className="w-3.5 h-3.5 text-gray-400 hidden sm:block"/>
                  </button>
                ) : (
                  <a href="/login" className="btn-primary text-sm !px-4 !py-2 !rounded-lg">
                    登录
                  </a>
                )}

                <AnimatePresence>
                  {isUserMenuOpen && (
                    <motion.div
                      initial={{opacity: 0, y: -8, scale: 0.96}}
                      animate={{opacity: 1, y: 0, scale: 1}}
                      exit={{opacity: 0, y: -8, scale: 0.96}}
                      transition={{duration: 0.15}}
                      className="absolute right-0 mt-2 w-56 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-1.5 bg-white dark:bg-gray-900 overflow-hidden"
                    >
                      {/* User info header */}
                      <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                        <p
                          className="text-sm font-semibold text-gray-900 dark:text-white truncate">{username || '用户'}</p>
                        <p className="text-xs text-gray-500 mt-0.5">欢迎回来</p>
                      </div>

                      {userMenuItems.map((item) => {
                        const Icon = item.icon;
                        return (
                          <a
                            key={item.href}
                            href={item.href}
                            onClick={() => setIsUserMenuOpen(false)}
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                          >
                            <Icon className="w-4 h-4 text-gray-400"/>
                            <span>{item.name}</span>
                          </a>
                        );
                      })}

                      {/* Admin link */}
                      <a
                        href="/admin"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <Settings className="w-4 h-4 text-gray-400"/>
                        <span>管理后台</span>
                      </a>

                      <div className="border-t border-gray-100 dark:border-gray-800 my-1"/>

                      <button
                        onClick={() => {
                          document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
                          document.cookie = 'refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
                          window.location.href = '/';
                        }}
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors w-full"
                      >
                        <LogOut className="w-4 h-4"/>
                        <span>退出登录</span>
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Bottom Nav */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-[9998] md:hidden glass-strong border-t border-gray-200/60 dark:border-gray-700/60"
        style={{paddingBottom: 'env(safe-area-inset-bottom, 0px)'}}>
        <div className="flex items-center justify-around h-14">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <a
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-colors min-w-[56px] ${
                  isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                <Icon className="w-5 h-5"/>
                <span className="text-[10px] font-medium">{item.name}</span>
                {isActive && (
                  <motion.div
                    layoutId="mobileActiveNav"
                    className="w-4 h-0.5 bg-blue-600 dark:bg-blue-400 rounded-full mt-0.5"
                  />
                )}
              </a>
            );
          })}
          {isLoggedIn ? (
            <a
              href="/settings"
              className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-colors min-w-[56px] ${
                pathname.startsWith('/settings') || pathname.startsWith('/profile') || pathname.startsWith('/my') ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              {userAvatar ? (
                <img src={userAvatar} alt="" className="w-5 h-5 rounded-full object-cover"/>
              ) : (
                <User className="w-5 h-5"/>
              )}
              <span className="text-[10px] font-medium">我的</span>
            </a>
          ) : (
            <a href="/login"
               className="flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg text-gray-500 dark:text-gray-400 min-w-[56px]">
              <User className="w-5 h-5"/>
              <span className="text-[10px] font-medium">登录</span>
            </a>
          )}
        </div>
      </nav>

      {/* Search Modal */}
      <AnimatePresence>
        {isSearchOpen && (
          <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            exit={{opacity: 0}}
            className="fixed inset-0 z-[99999] flex items-start justify-center pt-[8vh] sm:pt-[15vh]"
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsSearchOpen(false);
            }}
          >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm"/>

            {/* Modal */}
            <motion.div
              initial={{opacity: 0, y: -20, scale: 0.96}}
              animate={{opacity: 1, y: 0, scale: 1}}
              exit={{opacity: 0, y: -20, scale: 0.96}}
              transition={{duration: 0.2}}
              className="relative w-full max-w-2xl mx-3 sm:mx-4 bg-white dark:bg-gray-900 rounded-xl sm:rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden max-h-[80vh] sm:max-h-none flex flex-col"
            >
              {/* Search Input */}
              <form onSubmit={handleSearchSubmit}
                    className="flex items-center gap-3 px-5 py-4 border-b border-gray-100 dark:border-gray-800">
                <Search className="w-5 h-5 text-gray-400 flex-shrink-0"/>
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="搜索文章、分类、标签..."
                  className="flex-1 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 outline-none text-base min-h-[44px]"
                />
                <kbd
                  className="hidden sm:inline px-2 py-0.5 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-400">ESC</kbd>
                <button type="button" onClick={() => setIsSearchOpen(false)}
                        className="sm:hidden p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                  <X className="w-5 h-5"/>
                </button>
              </form>

              {/* Results */}
              <div className="max-h-[50vh] sm:max-h-[400px] overflow-y-auto flex-1">
                {searchLoading ? (
                  <div className="py-12 text-center">
                    <div
                      className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/>
                    <p className="text-sm text-gray-400 mt-3">搜索中...</p>
                  </div>
                ) : searchResults.length > 0 ? (
                  <div className="py-2">
                    {searchResults.map((item: any, i: number) => (
                      <a
                        key={i}
                        href={`/view?slug=${item.slug || item.id}`}
                        onClick={() => setIsSearchOpen(false)}
                        className="flex items-start gap-3 px-5 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div
                          className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <BookOpen className="w-4 h-4 text-blue-600 dark:text-blue-400"/>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{item.title}</p>
                          <p
                            className="text-xs text-gray-500 mt-0.5 line-clamp-1">{item.excerpt || item.summary || ''}</p>
                        </div>
                      </a>
                    ))}
                    <a
                      href={`/search?q=${encodeURIComponent(searchQuery)}`}
                      onClick={() => setIsSearchOpen(false)}
                      className="flex items-center justify-center py-3 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors border-t border-gray-100 dark:border-gray-800"
                    >
                      查看所有搜索结果 →
                    </a>
                  </div>
                ) : searchQuery ? (
                  <div className="py-12 text-center text-gray-400 text-sm">
                    <Search className="w-8 h-8 mx-auto mb-2 opacity-30"/>
                    未找到相关内容
                  </div>
                ) : (
                  <div className="py-8 px-5">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">快捷搜索</p>
                    <div className="flex flex-wrap gap-2">
                      {['技术', '前端', '后端', 'AI', '设计'].map(tag => (
                        <button
                          key={tag}
                          onClick={() => handleSearch(tag)}
                          className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Spacer for fixed navbar */}
      <div className="h-16"/>
    </>
  );
};

export default Navbar;
