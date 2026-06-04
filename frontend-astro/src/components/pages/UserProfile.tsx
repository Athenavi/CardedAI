'use client';

import {useEffect, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';
import {getFullMediaUrl} from '@/lib/utils';
import {AuthGuard} from '@/components/AuthGuard';
import {Calendar, Edit3, Eye, FileText, Heart, Link as LinkIcon, Lock, Mail, MapPin, Settings} from 'lucide-react';

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

function Profile() {
  const [data, setData] = useState<ProfileData | null>(null);
  const [av, setAv] = useState('');
  const [tab, setTab] = useState(0);

  useEffect(() => {
    (async () => {
      try {
        const r = await apiClient.get('/users/me');
        if (!r.success || !r.data) return;
        const user = r.data as ProfileData['user'];
        setData({user, recent_articles: r.data.recent_articles, stats: r.data.stats});
        const avatarUrl = user.avatar ? getFullMediaUrl(user.avatar) : '';
        setAv(avatarUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.username || 'U')}&background=random`);
      } catch {
      }
    })();
  }, []);

  if (!data?.user) return (
    <div
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-950 dark:to-gray-900">
      <div className="animate-spin w-8 h-8 border-[3px] border-blue-500 border-t-transparent rounded-full"/>
    </div>
  );

  const u = data.user, arts = data.recent_articles || [],
    st = data.stats || {articles_count: 0, followers_count: 0, following_count: 0};

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-950 dark:to-gray-900">
      {/* Cover — minimal gradient */}
      <div
        className="h-48 lg:h-56 bg-gradient-to-r from-blue-500/20 via-purple-500/10 to-pink-500/20 dark:from-blue-900/20 dark:via-purple-900/10 dark:to-pink-900/20"/>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 -mt-20 relative z-10">
        {/* Avatar + Name — floating card */}
        <div className="flex flex-col sm:flex-row items-center sm:items-end gap-5 mb-8">
          <img src={av} alt=""
               className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl border-4 border-white dark:border-gray-900 shadow-xl object-cover bg-white"
               onError={e => {
                 (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(u.username || 'U')}&background=random`
               }}/>
          <div className="text-center sm:text-left flex-1">
            <h1
              className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">{u.display_name || u.username}</h1>
            <p className="text-gray-500 dark:text-gray-400">@{u.username}</p>
            {u.bio && <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 max-w-lg">{u.bio}</p>}
          </div>
          <a href="/settings"
             className="shrink-0 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 shadow-sm transition-colors"><Settings
            className="w-4 h-4 inline mr-1 -mt-0.5"/>编辑</a>
        </div>

        {/* Stats row */}
        <div className="flex gap-6 sm:gap-10 mb-8 text-center sm:text-left">
          <div><p className="text-xl font-bold text-gray-900 dark:text-white">{st.articles_count}</p><p
            className="text-xs text-gray-500 dark:text-gray-400">文章</p></div>
          <div><p className="text-xl font-bold text-gray-900 dark:text-white">{st.followers_count}</p><p
            className="text-xs text-gray-500 dark:text-gray-400">粉丝</p></div>
          <div><p className="text-xl font-bold text-gray-900 dark:text-white">{st.following_count}</p><p
            className="text-xs text-gray-500 dark:text-gray-400">关注</p></div>
          <div><p
            className="text-xl font-bold text-gray-900 dark:text-white">{arts.reduce((s, a) => s + (a.views || 0), 0)}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">浏览</p></div>
        </div>

        {/* Tabs */}
        <div
          className="flex gap-1 mb-6 bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-xl p-1 border border-gray-200/60 dark:border-gray-700/60 w-fit">
          {['近期文章', '个人信息'].map((l, i) => (
            <button key={l} onClick={() => setTab(i)}
                    className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${tab === i ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}>{l}</button>
          ))}
        </div>

        {/* Articles */}
        {tab === 0 && (
          <div className="space-y-3 pb-12">
            {arts.length === 0 ? (
              <div className="text-center py-16 text-gray-400"><FileText className="w-10 h-10 mx-auto mb-3 opacity-40"/>
                <p className="text-sm">还没有文章</p><a href="/admin/editor"
                                                        className="inline-block mt-3 text-sm text-blue-600 hover:underline"><Edit3
                  className="w-4 h-4 inline mr-1"/>开始写作</a></div>
            ) : arts.map(a => (
              <a key={a.id} href={`/view?slug=${a.slug}`}
                 className="block bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-4 hover:border-gray-200 dark:hover:border-gray-700 transition-all hover:shadow-sm">
                <div className="flex gap-4">
                  {a.cover_image && <img src={getFullMediaUrl(a.cover_image)} alt=""
                                         className="hidden sm:block w-28 h-20 rounded-lg object-cover shrink-0"/>}
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white truncate">{a.title}</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-1">{a.excerpt || ''}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span><Calendar
                        className="w-3 h-3 inline mr-0.5"/>{a.created_at ? new Date(a.created_at).toLocaleDateString('zh-CN') : ''}</span>
                      <span><Eye className="w-3 h-3 inline mr-0.5"/>{a.views || 0}</span>
                      <span><Heart className="w-3 h-3 inline mr-0.5"/>{a.likes || 0}</span>
                    </div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}

        {/* About */}
        {tab === 1 && (
          <div
            className="bg-white/70 dark:bg-gray-900/70 backdrop-blur-sm rounded-xl border border-gray-100 dark:border-gray-800 p-6 pb-12 space-y-4">
            {[
              {icon: Mail, label: '邮箱', value: u.email},
              {icon: MapPin, label: '位置', value: u.location || '未设置'},
              {icon: LinkIcon, label: '网站', value: u.website, link: true},
              {icon: Lock, label: '隐私', value: u.profile_private ? '私密' : '公开'},
            ].map(({icon: Icon, label, value, link}) => (
              <div key={label} className="flex items-center gap-3 text-sm">
                <Icon className="w-4 h-4 text-gray-400 shrink-0"/>
                <span className="text-gray-500 dark:text-gray-400 w-12">{label}</span>
                {link && value !== '未设置' ? <a href={value} target="_blank" rel="noopener"
                                                 className="text-blue-600 hover:underline truncate">{value}</a> :
                  <span className="text-gray-900 dark:text-white">{value}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function UserProfileGuard() {
  return <AuthGuard><Profile/></AuthGuard>;
}
