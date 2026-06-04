'use client';

import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {apiClient} from '@/lib/api/base-client';
import {UserPlus, Users} from 'lucide-react';

function FansInner() {
  const [tab, setTab] = useState(0);
    const {data: fans, isLoading} = useQuery<any[]>({
    queryKey: ['fans'],
    queryFn: async () => {
      const r = await apiClient.get('/users/me/followers');
      return r.success && r.data ? (Array.isArray(r.data) ? r.data : r.data.followers||r.data.users||[]) : [];
    },
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-950 dark:to-gray-900 pt-20">
      <div className="max-w-2xl mx-auto px-4">
        <div className="flex items-center gap-3 mb-6"><Users className="w-6 h-6 text-gray-600"/><h1 className="text-2xl font-bold text-gray-900 dark:text-white">粉丝</h1></div>
        <div className="flex gap-1 mb-6 bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-xl p-1 border w-fit">
          {['粉丝','关注中'].map((l,i) => (
            <button key={l} onClick={() => setTab(i)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === i ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}>{l}</button>
          ))}
        </div>
        {isLoading ? (
          <div className="space-y-3">{[1,2,3,4].map(i=><div key={i} className="h-16 bg-white/50 dark:bg-gray-800/50 rounded-xl animate-pulse"/>)}</div>
        ) : !fans?.length ? (
          <div className="text-center py-16 text-gray-400"><Users className="w-10 h-10 mx-auto mb-3 opacity-40"/><p className="text-sm">暂无{tab===0?'粉丝':'关注'}</p></div>
        ) : (
          <div className="space-y-2">
            {fans.map((f:any,i:number) => (
              <div key={f.id||i} className="bg-white/70 dark:bg-gray-900/70 backdrop-blur-sm rounded-xl border border-gray-100 dark:border-gray-800 p-4 flex items-center justify-between hover:border-gray-200 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm">{f.username?.charAt(0)||'?'}</div>
                  <div><p className="font-medium text-sm text-gray-900 dark:text-white">{f.username}</p><p className="text-xs text-gray-400">{f.bio||f.followed_at?new Date(f.followed_at).toLocaleDateString('zh-CN'):''}</p></div>
                </div>
                <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors"><UserPlus className="w-3.5 h-3.5 inline mr-1"/>关注</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function FansPage() { return <AuthGuard><QueryProvider><FansInner /></QueryProvider></AuthGuard>; }
