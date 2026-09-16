/**
 * 页脚组件 — Editorial minimal
 * 结构：邮件通讯（hairline 分隔）→ 多列链接 → 底栏（版权 / 语言 / 后台）
 */

'use client';

import React, {useEffect, useState} from 'react';
import {motion, AnimatePresence} from 'framer-motion';
import {Rss, GitBranch, Share2, Heart, ArrowUp} from 'lucide-react';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import LanguageSwitcher from './LanguageSwitcher';

const Footer: React.FC = () => {
    const [showTop, setShowTop] = useState(false);
    const [email, setEmail] = useState('');
    const [subscribed, setSubscribed] = useState(false);
    const [year] = useState(() => new Date().getFullYear());

    useEffect(() => {
        const handleScroll = () => setShowTop(window.scrollY > 500);
        window.addEventListener('scroll', handleScroll, {passive: true});
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const handleSubscribe = (e: React.FormEvent) => {
        e.preventDefault();
        if (email.trim()) {
            setSubscribed(true);
            setEmail('');
            setTimeout(() => setSubscribed(false), 3000);
        }
    };

    const scrollToTop = () => {
        window.scrollTo({top: 0, behavior: 'smooth'});
    };

    const footerLinks = {
      content: {
        title: '内容',
            links: [
                {name: '文章', href: '/articles'},
                {name: '分类', href: '/categories'},
              {name: '标签', href: '/tags'},
                {name: '搜索', href: '/search'},
            ]
        },
        resources: {
            title: '资源',
            links: [
                {name: '关于我们', href: '/about'},
                {name: 'RSS 订阅', href: '/api/v2/cms/feed?format=rss', external: true},
                {name: 'Atom 订阅', href: '/api/v2/cms/feed?format=atom', external: true},
                {name: '版本日志', href: '/version'},
            ]
        },
        support: {
            title: '支持',
            links: [
                {name: '帮助中心', href: '/about'},
                {name: '反馈建议', href: '/about'},
                {name: '隐私政策', href: '/about'},
                {name: '服务条款', href: '/about'},
            ]
        },
    };

    const socialLinks = [
        {name: 'GitHub', href: '#', icon: GitBranch},
        {name: 'Twitter', href: '#', icon: Share2},
        {name: 'RSS', href: '/api/v2/cms/feed?format=rss', icon: Rss, external: true},
    ];

    return (
      <footer className="relative border-t border-border bg-card text-card-foreground">
        {/* Newsletter */}
        <div className="border-b border-border">
          <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
            <div className="grid items-center gap-8 lg:grid-cols-2">
                        <div>
                          <p className="kicker">Newsletter</p>
                          <h3 className="mt-3 text-2xl text-foreground sm:text-3xl">订阅邮件通讯</h3>
                          <p className="mt-3 max-w-lg text-sm leading-relaxed text-muted-foreground">
                            获取最新文章、技术分享与社区动态，直达你的收件箱。
                            </p>
                        </div>
              <form onSubmit={handleSubscribe} className="flex w-full max-w-md gap-2 lg:ml-auto">
                <Input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="输入你的邮箱地址…"
                                aria-label="邮箱地址"
                                className="flex-1"
                                required
                            />
                <Button type="submit" className="whitespace-nowrap">
                  {subscribed ? '已订阅' : '订阅'}
                </Button>
                        </form>
                    </div>
                </div>
            </div>

            {/* Main Footer Content */}
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:gap-12">
                    {/* Brand Column */}
                    <div className="col-span-2 md:col-span-1">
                      <a href="/" className="group mb-5 flex items-center gap-2.5">
                            <span
                              className="flex h-8 w-8 items-center justify-center rounded-md bg-gray-900 text-gray-50 dark:bg-gray-100 dark:text-gray-900">
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                                </svg>
                            </span>
                        <span className="editorial-title text-lg text-foreground">Carded AI</span>
                        </a>
                      <p className="mb-6 text-sm leading-relaxed text-muted-foreground">
                            一个现代化的内容创作与分享平台，致力于为创作者提供最佳的写作体验。
                        </p>
                      <div className="flex items-center gap-2">
                            {socialLinks.map((social) => {
                                const Icon = social.icon;
                                return (
                                    <a
                                        key={social.name}
                                        href={social.href}
                                        target={social.external ? '_blank' : undefined}
                                        rel={social.external ? 'noopener noreferrer' : undefined}
                                        className="flex h-9 w-9 items-center justify-center rounded-sm border border-border text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground"
                                        title={social.name}
                                    >
                                      <Icon className="h-4 w-4"/>
                                    </a>
                                );
                            })}
                        </div>
                    </div>

                    {/* Link Columns */}
                    {Object.entries(footerLinks).map(([key, section]) => (
                        <div key={key}>
                          <h4 className="kicker mb-4">{section.title}</h4>
                            <ul className="space-y-2.5">
                                {section.links.map((link) => (
                                    <li key={link.name}>
                                        <a
                                            href={link.href}
                                            target={link.external ? '_blank' : undefined}
                                            rel={link.external ? 'noopener noreferrer' : undefined}
                                            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                                        >
                                            {link.name}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </div>

            {/* Bottom Bar */}
        <div className="border-t border-border">
          <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
                    <div
                      className="flex flex-col items-center justify-between gap-3 text-xs text-muted-foreground sm:flex-row sm:text-sm">
                        <p className="flex items-center gap-1.5">
                          © {year} Carded AI · Built with <Heart
                          className="h-3.5 w-3.5 fill-current text-red-600 dark:text-red-400"/> using FastAPI & Astro
                        </p>
                        <div className="flex items-center gap-4">
                            <LanguageSwitcher/>
                          <a href="/admin" className="transition-colors hover:text-foreground">管理后台</a>
                        </div>
                    </div>
                </div>
            </div>

            {/* Back to Top */}
            <AnimatePresence>
                {showTop && (
                    <motion.button
                      initial={{opacity: 0, y: 12}}
                        animate={{opacity: 1, y: 0}}
                      exit={{opacity: 0, y: 12}}
                        onClick={scrollToTop}
                      className="fixed bottom-20 right-5 z-50 flex h-10 w-10 items-center justify-center rounded-sm border border-border bg-card text-foreground shadow-sm transition-colors hover:bg-accent md:bottom-8"
                        title="返回顶部"
                      aria-label="返回顶部"
                    >
                      <ArrowUp className="h-4 w-4"/>
                    </motion.button>
                )}
            </AnimatePresence>
        </footer>
    );
};

export default Footer;
