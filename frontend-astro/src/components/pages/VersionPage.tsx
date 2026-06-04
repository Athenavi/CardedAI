'use client';


import {useQuery} from '@tanstack/react-query';
import {QueryProvider} from '@/components/QueryProvider';
import {apiClient} from '@/lib/api/base-client';
import {Calendar, GitBranch, Info, Server} from 'lucide-react';

function VersionInner() {
  const {data, isLoading} = useQuery({
    queryKey: ['version'],
    queryFn: async () => {
      const r = await apiClient.get('/system/version/full');
      return r.success && r.data ? r.data : {};
    },
  });

  const Row = ({icon: Icon, label, value}: {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    value: string
  }) => (
    <div className="flex items-center gap-4 py-3 border-b border-gray-100 dark:border-gray-800 last:border-0"><Icon
      className="w-5 h-5 text-gray-400 shrink-0"/><span
      className="text-sm text-gray-500 dark:text-gray-400 w-24">{label}</span><span
      className="text-sm font-medium text-gray-900 dark:text-white">{value || '—'}</span></div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-950 dark:to-gray-900 pt-20">
      <div className="max-w-lg mx-auto px-4">
        <div className="text-center mb-8"><Info className="w-10 h-10 text-blue-600 mx-auto mb-3"/><h1 className="text-2xl font-bold text-gray-900 dark:text-white">版本信息</h1></div>
        <div className="bg-white/70 dark:bg-gray-900/70 backdrop-blur-sm rounded-2xl border border-gray-100 dark:border-gray-800 p-6">
          {isLoading ? (
            <div className="space-y-4">{[1,2,3,4].map(i=><div key={i} className="h-10 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
          ) : (
            <>
              <Row icon={Server} label="后端版本" value={data?.backend_version||data?.version||'-'} />
              <Row icon={GitBranch} label="构建号" value={data?.build_number||data?.build||'-'} />
              <Row icon={Calendar} label="更新时间" value={data?.updated_at||data?.build_time?new Date(data.build_time).toLocaleString('zh-CN'):'-'} />
              <Row icon={Server} label="前端版本" value={data?.frontend_version||'-'} />
              <Row icon={Info} label="环境" value={data?.environment||data?.env||'production'} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function VersionPage() { return <QueryProvider><VersionInner/></QueryProvider>; }
