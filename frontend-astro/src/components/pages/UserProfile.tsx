/**
 * 个人资料页 — Editorial minimal
 * 数据源：GET /api/v2/users/me（含 recent_articles 与 stats）
 */

'use client';

import {useEffect, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';
import {getFullMediaUrl} from '@/lib/utils';
import {AuthGuard} from '@/components/AuthGuard';
import {Button} from '@/components/ui/button';
import {Skeleton} from '@/components/ui/skeleton';

interface Article {
  id: number;
  title: string;
  slug: string;
  excerpt?: string;
  cover_image?: string;
  views: number;
  likes: number;
  created_at: string;
  tags?: string[];
}

interface ProfileData {
  user: {
    id: number;
    username: string;
    display_name?: string;
    email: string;
    bio?: string;
    location?: string;
    website?: string;
    avatar?: string;
    avatar_url?: string;
    profile_private: boolean;
    created_at: string;
  };
  recent_articles?: Article[];
  stats?: { articles_count: number; followers_count: number; following_count: number; };
}

const TABS = ['近期文章', '个人信息'] as const;

const avatarFallback = (username: string) =>
  `https://ui-avatars.com/api/?name=${encodeURIComponent(username || 'U')}&background=2b4f86&color=fffdf8`;

function Profile() {
  const [data, setData] = useState<ProfileData | null>(null);
  const [avatar, setAvatar] = useState('');
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/users/me');
        if (res.success && res.data) {
          const payload = res.data as any;
          const user: ProfileData['user'] = payload.user ?? payload;
          setData({user, recent_articles: payload.recent_articles, stats: payload.stats});
          setAvatar(user.avatar ? getFullMediaUrl(user.avatar) : avatarFallback(user.username));
        }
      } catch {
        // 静默失败，由下方空态提示
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div>
        <div className="flex flex-col gap-6 border-b border-border pb-8 sm:flex-row sm:items-center">
          <Skeleton className="h-20 w-20 rounded-md"/>
          <div className="flex-1 space-y-3">
            <Skeleton className="h-5 w-24"/>
            <Skeleton className="h-8 w-56"/>
            <Skeleton className="h-4 w-40"/>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-6 py-6 sm:grid-cols-4">
          {Array.from({length: 4}).map((_, index) => (
            <Skeleton key={index} className="h-12 w-full"/>
          ))}
        </div>
      </div>
    );
  }

  if (!data?.user) {
    return (
      <div className="border border-border bg-card px-6 py-16 text-center">
        <p className="editorial-title text-xl text-foreground">无法加载个人资料</p>
        <p className="mt-2 text-sm text-muted-foreground">可能需要先登录，或稍后重试</p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <a href="/login">
            <Button>去登录</Button>
          </a>
          <a
            href="/articles"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            浏览文章
          </a>
        </div>
      </div>
    );
  }

  const user = data.user;
  const articles = data.recent_articles || [];
  const stats = data.stats || {articles_count: 0, followers_count: 0, following_count: 0};
  const totalViews = articles.reduce((sum, item) => sum + (item.views || 0), 0);

  const statItems = [
    {label: '文章', value: stats.articles_count},
    {label: '粉丝', value: stats.followers_count},
    {label: '关注', value: stats.following_count},
    {label: '浏览', value: totalViews},
  ];

  const infoRows = [
    {label: '邮箱', value: user.email},
    {label: '位置', value: user.location || '未设置'},
    {label: '网站', value: user.website || '未设置', link: Boolean(user.website)},
    {label: '隐私', value: user.profile_private ? '私密' : '公开'},
    {label: '加入', value: user.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '—'},
  ];

  return (
    <div>
      {/* 头部 */}
      <header className="flex flex-col gap-6 border-b border-border pb-8 sm:flex-row sm:items-center">
        <img
          src={avatar}
          alt=""
          className="h-20 w-20 shrink-0 rounded-md border border-border bg-card object-cover"
          onError={(event) => {
            (event.target as HTMLImageElement).src = avatarFallback(user.username);
          }}
        />
        <div className="min-w-0 flex-1">
          <p className="kicker">Profile</p>
          <h1 className="editorial-title mt-2 text-3xl text-foreground">
            {user.display_name || user.username}
          </h1>
          <p className="mt-1 font-mono text-xs text-muted-foreground">@{user.username}</p>
          {user.bio && (
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">{user.bio}</p>
          )}
        </div>
        <a href="/settings" className="shrink-0">
          <Button variant="outline" size="sm">编辑资料</Button>
        </a>
      </header>

      {/* 统计 */}
      <dl className="grid grid-cols-2 gap-6 border-b border-border py-6 sm:grid-cols-4">
        {statItems.map((item) => (
          <div key={item.label}>
            <dt className="kicker">{item.label}</dt>
            <dd className="editorial-title mt-2 text-2xl text-foreground">{item.value}</dd>
          </div>
        ))}
      </dl>

      {/* 标签页 */}
      <div className="mt-8 flex items-center gap-1 border-b border-border" role="tablist" aria-label="资料分区">
        {TABS.map((label, index) => (
          <button
            key={label}
            type="button"
            role="tab"
            aria-selected={tab === index}
            onClick={() => setTab(index)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm transition-colors ${
              tab === index
                ? 'border-foreground text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 近期文章 */}
      {tab === 0 && (
        <div className="mt-6 pb-4">
          {articles.length === 0 ? (
            <div className="border border-border bg-card px-6 py-16 text-center">
              <p className="editorial-title text-xl text-foreground">还没有文章</p>
              <p className="mt-2 text-sm text-muted-foreground">写下第一篇，让它出现在这里</p>
              <a href="/admin/editor" className="mt-6 inline-block">
                <Button size="sm">开始写作</Button>
              </a>
            </div>
          ) : (
            articles.map((article) => (
              <a
                key={article.id}
                href={`/view?slug=${encodeURIComponent(article.slug)}`}
                className="group flex gap-5 border-b border-border/60 py-4"
              >
                {article.cover_image && (
                  <img
                    src={getFullMediaUrl(article.cover_image)}
                    alt=""
                    className="hidden h-16 w-24 shrink-0 rounded-sm border border-border object-cover sm:block"
                  />
                )}
                <div className="min-w-0 flex-1">
                  <h3 className="editorial-title text-lg text-foreground transition-colors group-hover:text-primary">
                    {article.title}
                  </h3>
                  {article.excerpt && (
                    <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">{article.excerpt}</p>
                  )}
                  <div className="mt-2 flex items-center gap-4 font-mono text-[11px] text-muted-foreground">
                    {article.created_at && (
                      <time dateTime={article.created_at}>
                        {new Date(article.created_at).toLocaleDateString('zh-CN')}
                      </time>
                    )}
                    <span>{article.views || 0} 阅读</span>
                    <span>{article.likes || 0} 赞</span>
                  </div>
                </div>
              </a>
            ))
          )}
        </div>
      )}

      {/* 个人信息 */}
      {tab === 1 && (
        <dl className="mt-6 divide-y divide-border/60 border-b border-border">
          {infoRows.map((row) => (
            <div key={row.label} className="flex items-baseline gap-4 py-3 text-sm">
              <dt className="kicker w-16 shrink-0">{row.label}</dt>
              <dd className="min-w-0 truncate text-foreground">
                {row.link && row.value !== '未设置' ? (
                  <a
                    href={row.value}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="link-editorial"
                  >
                    {row.value}
                  </a>
                ) : (
                  row.value
                )}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

export default function UserProfileGuard() {
  return <AuthGuard><Profile/></AuthGuard>;
}
