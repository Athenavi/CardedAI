'use client';

import {useState} from 'react';
import {useMutation, useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Brain, Loader, Sparkles} from 'lucide-react';

function AIInner() {
  const [text, setText] = useState('');
  const [result, setResult] = useState('');
  const [mode, setMode] = useState<'keywords'|'description'|'outline'>('keywords');

    const {data: skills} = useQuery<any[]>({
    queryKey: ['admin-ai-skills'],
    queryFn: async () => {
      const r = await apiClient.get('/ai/skills/ai-skills/list');
      return r.success && r.data ? (Array.isArray(r.data) ? r.data : r.data.skills||[]) : [];
    },
  });

  const analyzeMut = useMutation({
    mutationFn: async () => {
      let ep = '';
      if (mode==='keywords') ep = '/ai/content/ai-content/extract-keywords';
      else if (mode==='description') ep = '/ai/content/ai-content/generate-meta-description';
      else ep = '/ai/content/ai-content/generate-outline';
      const r = await apiClient.post(ep, {content: text});
      return r;
    },
    onSuccess: (r) => { if (r.success && r.data) setResult((r.data as any).result||(r.data as any).keywords?.join(', ')||JSON.stringify(r.data)); },
  });

  return (
    <AdminShell title="AI 工具">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
          <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2"><Sparkles className="w-5 h-5"/>AI 内容助手</h3>
          <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
            {[
              {id:'keywords', label:'关键词'},
              {id:'description', label:'描述'},
              {id:'outline', label:'大纲'},
            ].map(m => (
              <button key={m.id} onClick={() => setMode(m.id as any)}
                      className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${mode === m.id ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}>{m.label}</button>
            ))}
          </div>
          <textarea value={text} onChange={e=>setText(e.target.value)} rows={5} placeholder="输入内容..." className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white resize-none"/>
          <button onClick={()=>analyzeMut.mutate()} disabled={!text.trim()||analyzeMut.isPending} className="w-full py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm rounded-xl font-medium hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2">{analyzeMut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : <Brain className="w-4 h-4"/>}{analyzeMut.isPending?'分析中...':'开始分析'}</button>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
          <h3 className="font-semibold text-gray-900 dark:text-white">AI 技能</h3>

            {(skills?.length ?? 0) > 0 ? (
            <div className="space-y-2">
                {skills?.map((s: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                  <div><p
                    className="text-sm font-medium text-gray-900 dark:text-white">{s.name || s.skill_name || '技能'}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{s.description || ''}</p></div>
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full ${s.is_active !== false ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>{s.is_active !== false ? '已激活' : '未激活'}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400"><Brain className="w-10 h-10 mx-auto mb-3 opacity-40"/><p className="text-sm">暂无 AI 技能</p></div>
          )}
          {result && <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{result}</div>}
        </div>
      </div>
    </AdminShell>
  );
}
export default function AdminAI() { return <AuthGuard><QueryProvider><AIInner/></QueryProvider></AuthGuard>; }
