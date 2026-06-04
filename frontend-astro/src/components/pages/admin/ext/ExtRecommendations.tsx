'use client';


import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Eye, Star, ThumbsUp, TrendingUp, Zap} from 'lucide-react';

function RecsInner() {
  const {data: trending} = useQuery({
    queryKey: ['ext-recs-trending'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/recommendations/trending', {window: '7d', limit: 10});
      const raw = r.success && r.data ? (r.data.trending || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const {data: risingStars} = useQuery({
    queryKey: ['ext-recs-rising'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/recommendations/rising-stars', {limit: 10});
      const raw = r.success && r.data ? (r.data.rising_stars || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const {data: personalized} = useQuery({
    queryKey: ['ext-recs-personalized'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/recommendations/personalized', {limit: 10});
      const raw = r.success && r.data ? (r.data.recommendations || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  return (
    <AdminShell title="推荐系统">
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Trending */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-orange-50 to-transparent dark:from-orange-900/10">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500"/>Trending <span className="text-xs text-gray-400 font-normal">近7天</span>
            </h3>
          </div>
          {Array.isArray(trending) && trending.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {trending.map((article: any, i: number) => (
                <div key={article.id || i} className="px-6 py-3.5">
                  <div className="flex items-start gap-3">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5
                      ${i === 0 ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400' : i === 1 ? 'bg-gray-200 text-gray-600' : i === 2 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                      {i + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{article.title || `文章 #${article.id}`}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                        {article.views !== undefined && <span className="flex items-center gap-1"><Eye className="w-3 h-3"/>{article.views}</span>}
                        {article.likes !== undefined && <span className="flex items-center gap-1"><ThumbsUp className="w-3 h-3"/>{article.likes}</span>}
                        {(article.score || article.trending_score) && <span className="text-orange-500 font-medium">{(article.score || article.trending_score).toFixed(1)}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-sm text-gray-400">暂无 Trending 数据</div>
          )}
        </div>

        {/* Rising Stars */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-purple-50 to-transparent dark:from-purple-900/10">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-purple-500"/>Rising Stars
            </h3>
          </div>
          {Array.isArray(risingStars) && risingStars.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {risingStars.map((star: any, i: number) => (
                <div key={star.user_id || i} className="px-6 py-3.5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0
                      ${i === 0 ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                      {i + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{star.username || `用户 #${star.user_id}`}</p>
                      {star.articles_count !== undefined && <p className="text-xs text-gray-400">{star.articles_count} 篇文章</p>}
                    </div>
                  </div>
                  {star.growth_rate !== undefined && (
                    <span className="text-xs font-medium text-green-600">+{star.growth_rate}%</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-sm text-gray-400">暂无 Rising Stars 数据</div>
          )}
        </div>

        {/* Personalized */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-transparent dark:from-blue-900/10">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Star className="w-5 h-5 text-blue-500"/>推荐文章 <span className="text-xs text-gray-400 font-normal">基于热度</span>
            </h3>
          </div>
          {Array.isArray(personalized) && personalized.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {personalized.map((rec: any, i: number) => (
                <div key={rec.id || i} className="px-6 py-3.5">
                  <div className="flex items-start gap-3">
                    <span className="text-xs text-gray-400 mt-1 w-4 shrink-0">{i + 1}</span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{rec.title || `文章 #${rec.id}`}</p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                        {rec.views !== undefined && <span>{rec.views} 浏览</span>}
                        {rec.likes !== undefined && <span>· {rec.likes} 赞</span>}
                        {rec.author && <span>· {rec.author}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-sm text-gray-400">暂无推荐数据</div>
          )}
        </div>
      </div>
    </AdminShell>
  );
}

export default function ExtRecommendations() { return <AuthGuard><QueryProvider><RecsInner/></QueryProvider></AuthGuard>; }
