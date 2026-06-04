'use client';

import {useState} from 'react';
import {useMutation, useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {FileText, Loader, Sparkles} from 'lucide-react';

function ExtAIWritingInner() {
  const [text, setText] = useState(''); const [result, setResult] = useState(''); const [mode, setMode] = useState('polish');

  const tools = [
    {id:'polish',label:'润色'},{id:'grammar',label:'语法检查'},{id:'continue',label:'续写'},{id:'titles',label:'标题生成'},{id:'summary',label:'摘要'},{id:'style',label:'变换风格'},
  ];

  const epMap: Record<string,string> = {
    polish:'/ext/ai-recommendations/writing/polish',
    grammar:'/ext/ai-recommendations/writing/check-grammar',
    continue:'/ext/ai-recommendations/writing/continue',
    titles:'/ext/ai-recommendations/writing/generate-titles',
    summary:'/ext/ai-recommendations/extract-summary',
    style:'/ext/ai-recommendations/writing/transform-style',
  };

  const runMut = useMutation({
    mutationFn: async () => {
      const ep = epMap[mode]||epMap.polish;
      const body = mode==='titles'?{content:text}:mode==='summary'?{content:text}:{text};
      const r = await apiClient.post(ep, body);
      return r;
    },
    onSuccess: (r) => setResult(r.success&&r.data?(r.data as any).result||(r.data as any).text||(r.data as any).titles?.join('\n')||JSON.stringify(r.data):'无结果'),
  });

    const {data: trending} = useQuery({
        queryKey: ['ext-writer-trending'], queryFn: async () => {
        const r = await apiClient.get('/ext/recommendations/trending');
            return r.success && r.data ? (Array.isArray(r.data) ? r.data : r.data.articles || []) : []
        }
    });

  return (
    <AdminShell title="AI 写作助手">
      <div className="grid lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 space-y-4">
          <div className="flex flex-wrap gap-1 bg-white dark:bg-gray-900 rounded-2xl border p-1">
            {tools.map(t=><button key={t.id} onClick={()=>setMode(t.id)} className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${mode===t.id?'bg-blue-600 text-white shadow-md':'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'}`}>{t.label}</button>)}
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 space-y-3">
            <textarea value={text} onChange={e=>setText(e.target.value)} rows={6} placeholder="输入内容..." className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white resize-none"/>
            <button onClick={()=>runMut.mutate()} disabled={!text.trim()||runMut.isPending} className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm rounded-xl font-medium hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2">
              {runMut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : <Sparkles className="w-4 h-4"/>}{runMut.isPending ? '处理中...' : '开始'}</button>
          </div>
          {result && <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5"><h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">结果</h4><div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{result}</div></div>}
        </div>
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2"><FileText className="w-5 h-5"/>热门推荐</h3>
            {trending?.length>0?<div className="space-y-2">{trending.slice(0,5).map((a:any,i:number)=><div key={i} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl"><p className="text-sm font-medium text-gray-900 dark:text-white truncate">{a.title}</p><p className="text-xs text-gray-400 mt-0.5">{a.views||0} 阅读</p></div>)}</div>:<p className="text-sm text-gray-400 text-center py-8">暂无数据</p>}
          </div>
        </div>
      </div>
    </AdminShell>
  );
}
export default function ExtAIWriting(){return <AuthGuard><QueryProvider><ExtAIWritingInner/></QueryProvider></AuthGuard>;}
