'use client';


import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {GitBranch} from 'lucide-react';

function TemplatesInner() {
    const {data, isLoading} = useQuery<any[]>({
    queryKey: ['admin-templates'],
    queryFn: async () => {
      const r = await apiClient.get('/templates/templates/list');
      return r.success && r.data ? (Array.isArray(r.data) ? r.data : r.data.templates||[]) : [];
    },
  });
    const {data: cats} = useQuery<any[]>({
    queryKey: ['admin-template-cats'],
    queryFn: async () => {
      const r = await apiClient.get('/templates/templates/categories');
      return r.success && r.data ? (Array.isArray(r.data) ? r.data : r.data.categories||[]) : [];
    },
  });

  return (
    <AdminShell title="模板管理">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {(cats?.length ?? 0) > 0 && (
          <div className="md:col-span-full flex gap-2 mb-2">
              {cats?.map((c: any, i: number) => <span key={i}
                                                      className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs font-medium">{c.name || c}</span>)}
          </div>
        )}
        {isLoading ? (
          <div className="col-span-full p-12 text-center"><div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/></div>
        ) : !data?.length ? (
          <div className="col-span-full p-12 text-center text-gray-400"><GitBranch className="w-10 h-10 mx-auto mb-3 opacity-40"/><p>暂无模板</p></div>
        ) : data.map((t:any,i:number) => (
          <div key={t.id||i} className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-sm transition-shadow">
            <div className="aspect-video bg-gray-50 dark:bg-gray-800 rounded-xl mb-3 flex items-center justify-center text-gray-300 text-2xl">📄</div>
            <h3 className="font-semibold text-sm text-gray-900 dark:text-white truncate">{t.name||'模板'}</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{t.description || ''}</p>
            <p className="text-xs text-gray-400 mt-2">{t.category||''}</p>
          </div>
        ))}
      </div>
    </AdminShell>
  );
}
export default function AdminTemplates() { return <AuthGuard><QueryProvider><TemplatesInner/></QueryProvider></AuthGuard>; }
