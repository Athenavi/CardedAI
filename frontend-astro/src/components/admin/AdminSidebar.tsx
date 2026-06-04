'use client';

import React from 'react';
import {
  AlertTriangle,
  ArrowRightLeft,
  Award,
  BarChart3,
  Bell,
  Brain,
  Building2,
  CheckSquare,
  ChevronLeft,
  Coins,
  CreditCard,
  Crown,
  Database,
  Diamond,
  Eye,
  FileEdit,
  FileText,
  FolderTree,
  GitBranch,
  Globe,
  Handshake,
  Image,
  Lock,
  LogOut,
  Medal,
  MessageSquare,
  Newspaper,
  Package,
  PenLine,
  PieChart,
  Puzzle,
  Radio,
  ScrollText,
  Search,
  Server,
  Settings,
  Shield,
  Star,
  TrendingUp,
  Users,
  X,
  Zap
} from 'lucide-react';
import {useTranslation} from '@/lib/i18n';

/** 导航项配置（使用 i18n key） */
interface NavItem {
  labelKey?: string;
  href?: string;
  icon?: React.FC<{ className?: string }>;
  sepKey?: string;
}

export const navConfig: NavItem[] = [
  {labelKey: 'nav.dashboard', href: '/admin', icon: BarChart3},
  {labelKey: 'nav.articles', href: '/admin/articles', icon: FileText},
  {labelKey: 'nav.categories', href: '/admin/categories', icon: FolderTree},
  {labelKey: 'nav.media', href: '/admin/media', icon: Image},
  {labelKey: 'nav.comments', href: '/admin/comments', icon: MessageSquare},
  {labelKey: 'nav.users', href: '/admin/users', icon: Users},
  {labelKey: 'nav.roles', href: '/admin/roles', icon: Shield},
  {labelKey: 'nav.plugins', href: '/admin/plugins', icon: Puzzle},
  {labelKey: 'nav.backup', href: '/admin/backup', icon: Database},
  {labelKey: 'nav.sensitiveWords', href: '/admin/sensitive-words', icon: AlertTriangle},
  {labelKey: 'nav.analytics', href: '/admin/analytics', icon: TrendingUp},
  {labelKey: 'nav.auditLogs', href: '/admin/audit-logs', icon: ScrollText},
  {labelKey: 'nav.system', href: '/admin/system', icon: Server},
  {labelKey: 'nav.vip', href: '/admin/vip', icon: Crown},
  {labelKey: 'nav.ads', href: '/admin/ads', icon: Newspaper},
  {labelKey: 'nav.templates', href: '/admin/templates', icon: GitBranch},
  {labelKey: 'nav.notifications', href: '/admin/notifications', icon: Bell},
  {labelKey: 'nav.collaboration', href: '/admin/collaboration', icon: Handshake},
  {labelKey: 'nav.integrations', href: '/admin/integrations', icon: Globe},
  {labelKey: 'nav.aiTools', href: '/admin/ai', icon: Brain},
  {labelKey: 'nav.cdn', href: '/admin/cdn', icon: Radio},
  {labelKey: 'nav.accessibility', href: '/admin/accessibility', icon: Eye},
  {labelKey: 'nav.gdpr', href: '/admin/gdpr', icon: Shield},
  {sepKey: 'nav.advancedManagement'},
  {labelKey: 'nav.enterprise', href: '/admin/enterprise', icon: Building2},
  {labelKey: 'nav.payment', href: '/admin/payment', icon: CreditCard},
  {labelKey: 'nav.migration', href: '/admin/migration', icon: ArrowRightLeft},
  {labelKey: 'nav.contentExt', href: '/admin/content-ext', icon: FileEdit},
  {labelKey: 'nav.userSecurity', href: '/admin/user-security', icon: Lock},
  {labelKey: 'nav.searchMedia', href: '/admin/search-media', icon: Zap},
  {labelKey: 'nav.ecommerce', href: '/admin/ecommerce', icon: Package},
  {labelKey: 'nav.revenue', href: '/admin/revenue', icon: PieChart},
  {labelKey: 'nav.multisite', href: '/admin/multisite', icon: Globe},
  {labelKey: 'nav.chatGroups', href: '/admin/chat-groups', icon: MessageSquare},
  {labelKey: 'nav.seo', href: '/admin/seo', icon: Search},
  {labelKey: 'nav.approval', href: '/admin/approval', icon: CheckSquare},
  {sepKey: 'nav.extensions'},
  {labelKey: 'nav.badges', href: '/admin/ext/badges', icon: Award},
  {labelKey: 'nav.points', href: '/admin/ext/points', icon: Coins},
  {labelKey: 'nav.tipping', href: '/admin/ext/tipping', icon: Diamond},
  {labelKey: 'nav.aiWriting', href: '/admin/ext/ai-writing', icon: PenLine},
  {labelKey: 'nav.certification', href: '/admin/ext/certification', icon: Medal},
  {labelKey: 'nav.nft', href: '/admin/ext/nft', icon: Diamond},
  {labelKey: 'nav.recommendations', href: '/admin/ext/recommendations', icon: Star},
  {labelKey: 'nav.settings', href: '/admin/settings', icon: Settings},
];

/** @deprecated 使用 navConfig 替代，保留用于向后兼容 */
export const nav = navConfig.map(item => ({
  ...item,
  label: item.labelKey ?? item.sepKey ?? '',
  sep: item.sepKey,
}));

const isActive = (href: string) => typeof window !== 'undefined' && window.location.pathname === href;

/** 侧边栏骨架屏 */
export function SidebarSkeleton({collapsed}: { collapsed: boolean }) {
  return (
    <div
      className={`hidden lg:flex flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 transition-all ${collapsed ? 'w-16' : 'w-56'} flex-shrink-0`}>
      <div className="flex items-center justify-between h-14 px-4 border-b border-gray-200 dark:border-gray-800">
        {!collapsed && <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"/>}
        <div className="w-7 h-7 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"/>
      </div>
      <div className="flex-1 p-3 space-y-2">
        {Array.from({length: 12}).map((_, i) => (
          <div key={i} className="flex items-center gap-3 px-3 py-2">
            <div className="w-5 h-5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"/>
            {!collapsed && <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
                                style={{width: `${50 + Math.random() * 40}%`}}/>}
          </div>
        ))}
      </div>
    </div>
  );
}

/** 桌面端侧边栏 */
export function DesktopSidebar({collapsed, onToggle}: { collapsed: boolean; onToggle: () => void }) {
  const {t} = useTranslation();

  return (
    <aside
      className={`hidden lg:flex flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 transition-all ${collapsed ? 'w-16' : 'w-56'} flex-shrink-0`}>
      <div className="flex items-center justify-between h-14 px-4 border-b border-gray-200 dark:border-gray-800">
        {!collapsed && <span className="font-bold text-gray-900 dark:text-white">FastBlog</span>}
        <button onClick={onToggle} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400">
          <ChevronLeft className={`w-4 h-4 transition-transform ${collapsed ? 'rotate-180' : ''}`}/></button>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navConfig.map((item, i) => {
          if (item.sepKey) return <div key={`sep-${i}`}
                                       className={`pt-3 pb-1 text-xs font-semibold text-gray-400 uppercase tracking-wider ${collapsed ? 'text-center text-[10px]' : 'px-3'}`}>{collapsed ? '··' : t(item.sepKey)}</div>;
          const Icon = item.icon!;
          const active = isActive(item.href!);
          return (
            <a key={item.href} href={item.href}
               className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${active ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
               title={collapsed ? t(item.labelKey!) : undefined}>
              <Icon className="w-5 h-5 flex-shrink-0"/>{!collapsed && <span>{t(item.labelKey!)}</span>}
            </a>
          );
        })}
      </nav>
      <div className="p-3 border-t border-gray-200 dark:border-gray-800">
        <a href="/"
           className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800">
          <LogOut className="w-5 h-5"/>{!collapsed && <span>{t('nav.backToFront')}</span>}
        </a>
      </div>
    </aside>
  );
}

/** 移动端侧边栏 */
export function MobileSidebar({open, onClose}: { open: boolean; onClose: () => void }) {
  const {t} = useTranslation();

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden" onClick={onClose}/>}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transform transition-transform lg:hidden safe-top ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between h-14 px-4 border-b border-gray-200 dark:border-gray-800">
          <span className="font-bold text-gray-900 dark:text-white">FastBlog</span>
          <button onClick={onClose}
                  className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400"/></button>
        </div>
        <nav className="p-3 space-y-1 overflow-y-auto"
             style={{maxHeight: 'calc(100vh - 3.5rem - env(safe-area-inset-bottom, 0px))'}}>
          {navConfig.map((item, i) => {
            if (item.sepKey) return <div key={`sep-${i}`}
                                         className="pt-3 pb-1 px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">{t(item.sepKey)}</div>;
            const Icon = item.icon!;
            return (
              <a key={item.href} href={item.href} onClick={onClose}
                 className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium min-h-[44px] ${isActive(item.href!) ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>
                <Icon className="w-5 h-5"/><span>{t(item.labelKey!)}</span>
              </a>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
