/**
 * 页脚组件 - 全面重构版
 * 特性：
 * - 多列链接布局
 * - 社交媒体图标
 * - Newsletter 订阅
 * - 返回顶部按钮
 * - 版权信息
 */

'use client';

import React, {useEffect, useState} from 'react';
import {motion, AnimatePresence} from 'framer-motion';
import {Rss, GitBranch, Share2, Mail, ArrowUp, Heart, BookOpen, Shield, Globe} from 'lucide-react';
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
        product: {
            title: '产品',
            links: [
                {name: '文章', href: '/articles'},
                {name: '分类', href: '/categories'},
                {name: '搜索', href: '/search'},
                {name: 'VIP 会员', href: '/vip'},
            ]
        },
        resources: {
            title: '资源',
            links: [
                {name: '关于我们', href: '/about'},
                {name: 'RSS 订阅', href: '/api/v2/feed/rss', external: true},
                {name: 'Atom 订阅', href: '/api/v2/feed/atom', external: true},
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
        {name: 'RSS', href: '/api/v2/feed/rss', icon: Rss, external: true},
    ];

    return (
        <footer className="relative bg-gray-50 dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800">
            {/* Newsletter Section */}
            <div className="border-b border-gray-200 dark:border-gray-800">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
                    <div className="grid lg:grid-cols-2 gap-8 items-center">
                        <div>
                            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                                订阅我们的<span className="gradient-text"> Newsletter</span>
                            </h3>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">
                                获取最新文章、技术分享和社区动态，直达你的收件箱。
                            </p>
                        </div>
                        <form onSubmit={handleSubscribe} className="flex gap-3 max-w-md lg:ml-auto">
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="输入你的邮箱地址..."
                                className="input-base flex-1"
                                required
                            />
                            <button type="submit" className="btn-primary whitespace-nowrap">
                                {subscribed ? '✓ 已订阅' : '订阅'}
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            {/* Main Footer Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">
                    {/* Brand Column */}
                    <div className="col-span-2 md:col-span-1">
                        <a href="/" className="flex items-center gap-2.5 mb-4 group">
                            <div className="w-9 h-9 gradient-primary rounded-xl flex items-center justify-center">
                                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24"
                                     stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                                </svg>
                            </div>
                            <span className="text-xl font-bold text-gray-900 dark:text-white">FastBlog</span>
                        </a>
                        <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-6">
                            一个现代化的内容创作与分享平台，致力于为创作者提供最佳的写作体验。
                        </p>
                        {/* Social Links */}
                        <div className="flex items-center gap-3">
                            {socialLinks.map((social) => {
                                const Icon = social.icon;
                                return (
                                    <a
                                        key={social.name}
                                        href={social.href}
                                        target={social.external ? '_blank' : undefined}
                                        rel={social.external ? 'noopener noreferrer' : undefined}
                                        className="w-9 h-9 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 flex items-center justify-center text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-all"
                                        title={social.name}
                                    >
                                        <Icon className="w-4 h-4"/>
                                    </a>
                                );
                            })}
                        </div>
                    </div>

                    {/* Link Columns */}
                    {Object.entries(footerLinks).map(([key, section]) => (
                        <div key={key}>
                            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">{section.title}</h4>
                            <ul className="space-y-2.5">
                                {section.links.map((link) => (
                                    <li key={link.name}>
                                        <a
                                            href={link.href}
                                            target={link.external ? '_blank' : undefined}
                                            rel={link.external ? 'noopener noreferrer' : undefined}
                                            className="text-sm text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
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
            <div className="border-t border-gray-200 dark:border-gray-800">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
                    <div
                        className="flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-gray-500 dark:text-gray-400">
                        <p className="flex items-center gap-1.5">
                            © {year} FastBlog. Made with <Heart
                            className="w-3.5 h-3.5 text-red-500 fill-red-500"/> using FastAPI & Astro
                        </p>
                        <div className="flex items-center gap-4">
                            <LanguageSwitcher/>
                            <a href="/admin"
                               className="hover:text-gray-700 dark:hover:text-gray-300 transition-colors">管理后台</a>
                        </div>
                    </div>
                </div>
            </div>

            {/* Back to Top */}
            <AnimatePresence>
                {showTop && (
                    <motion.button
                        initial={{opacity: 0, y: 20}}
                        animate={{opacity: 1, y: 0}}
                        exit={{opacity: 0, y: 20}}
                        onClick={scrollToTop}
                        className="fixed bottom-20 md:bottom-8 right-6 z-50 w-11 h-11 rounded-full gradient-primary text-white shadow-lg hover:shadow-xl flex items-center justify-center transition-shadow"
                        title="返回顶部"
                    >
                        <ArrowUp className="w-5 h-5"/>
                    </motion.button>
                )}
            </AnimatePresence>
        </footer>
    );
};

export default Footer;
