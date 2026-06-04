'use client';


import {useQuery} from '@tanstack/react-query';
import {QueryProvider} from '@/components/QueryProvider';
import {apiClient} from '@/lib/api/base-client';
import {Check, Crown, Star, Zap} from 'lucide-react';

function VipInner() {
  const {data: features} = useQuery({
    queryKey: ['vip-features'],
    queryFn: async () => {
      const r = await apiClient.get<any[]>('/membership/features');
      return r.success && r.data ? (Array.isArray(r.data) ? r.data : []) : [];
    },
  });
  const {data: status} = useQuery({
    queryKey: ['vip-status'],
    queryFn: async () => {
      const r = await apiClient.get('/membership/status');
      return r.success && r.data ? r.data : {};
    },
  });

  const tiers = features?.length ? features : [
    {name:'免费', price:'¥0', period:'永久', features:['基础功能','社区支持'], color:'gray', icon:Star},
    {name:'VIP', price:'¥19', period:'/月', features:['所有免费功能','高级统计','优先支持','无广告'], color:'blue', icon:Zap, popular:true},
    {name:'VIP Pro', price:'¥99', period:'/月', features:['所有VIP功能','API访问','自定义域名','专属客服'], color:'purple', icon:Crown},
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="max-w-5xl mx-auto px-4 py-16 sm:py-24 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-full text-sm font-medium text-purple-700 dark:text-purple-300 mb-6"><Crown className="w-4 h-4"/>VIP 会员</div>
        <h1 className="text-4xl sm:text-5xl font-black text-gray-900 dark:text-white mb-4">解锁全部功能</h1>
        <p className="text-lg text-gray-500 dark:text-gray-400 mb-12 max-w-xl mx-auto">升级到
          VIP，享受更强大的写作和分析工具</p>

        {status?.is_vip && <div className="inline-flex items-center gap-2 px-5 py-2.5 bg-green-100 dark:bg-green-900/20 rounded-xl text-green-700 dark:text-green-300 mb-12"><Crown className="w-5 h-5"/>您是 VIP 会员，有效期至 {new Date(status.expires_at).toLocaleDateString('zh-CN')}</div>}

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {tiers.map(t => {
            const Icon = t.icon;
            return (
              <div key={t.name} className={`relative bg-white dark:bg-gray-900 rounded-2xl p-6 border-2 transition-all hover:shadow-lg ${t.popular ? 'border-blue-500 shadow-blue-200/30 dark:shadow-blue-900/20 scale-105' : 'border-gray-100 dark:border-gray-800'}`}>
                {t.popular && <div className="absolute -top-3 inset-x-0 flex justify-center"><span className="px-3 py-0.5 bg-blue-600 text-white text-xs font-medium rounded-full">推荐</span></div>}
                <Icon className={`w-8 h-8 mx-auto mb-3 ${t.name==='VIP'?'text-blue-600':t.name==='VIP Pro'?'text-purple-600':'text-gray-400'}`}/>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">{t.name}</h2>
                <div className="my-4"><span className="text-3xl font-black text-gray-900 dark:text-white">{t.price}</span><span className="text-sm text-gray-400">{t.period}</span></div>
                <ul className="space-y-2.5 mb-6 text-left">
                  {t.features.map((f,i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400"><Check className="w-4 h-4 text-green-500 shrink-0"/>{f}</li>
                  ))}
                </ul>
                <button className={`w-full py-2.5 rounded-xl text-sm font-medium transition-colors ${t.popular ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-200/30' : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-900 dark:text-white'}`}>
                  {t.price === '¥0' ? '当前计划' : '立即升级'}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default function VipPage() { return <QueryProvider><VipInner/></QueryProvider>; }
