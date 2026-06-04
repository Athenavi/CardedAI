'use client';

import {useState} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {EmptyState, SectionTitle, StatCard, StatusBadge} from '@/components/admin/shared-ui';
import {CheckCircle, Globe, Link, Loader, Shield, Unlink} from 'lucide-react';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {OAuthProvider, LinkedAccount, ProviderAvatar, ActionButton} from './shared';


export default function OAuthTab({showToast}: {
  showToast: (msg: string, type?: 'success' | 'error' | 'info') => void
}) {
  const confirm = useConfirm();
  const qc = useQueryClient();
  const [_showConfigModal, _setShowConfigModal] = useState(false);
  const [_configProvider, _setConfigProvider] = useState('');
  const [_configForm, _setConfigForm] = useState({client_id: '', client_secret: '', redirect_uri: ''});

  const {data: providers, isLoading: loadingProviders} = useQuery({
    queryKey: ['integ-oauth-providers'],
    queryFn: async () => {
      const r = await apiClient.get('/integrations/oauth/providers');
      const raw = r.success && r.data ? (r.data.providers || r.data) : [];
      return (Array.isArray(raw) ? raw : []).filter((p) =>
        (p.name || p.provider || '').toLowerCase() !== 'weibo'
      );
    },
  });

  const {data: linkedAccounts} = useQuery({
    queryKey: ['integ-oauth-linked'],
    queryFn: async () => {
      const r = await apiClient.get('/integrations/oauth/linked-accounts');
      const raw = r.success && r.data ? (r.data.linked_accounts || r.data.accounts || r.data) : [];
      return (Array.isArray(raw) ? raw : []) as LinkedAccount[];
    },
  });

  const unlinkMut = useMutation({
    mutationFn: (provider: string) => apiClient.post(`/integrations/oauth/unlink/${provider}`),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-oauth-linked']});
      showToast(r.message || '已解绑', 'success');
    },
    onError: () => showToast('解绑失败', 'error'),
  });

  const linked = Array.isArray(linkedAccounts) ? linkedAccounts : [];
  const providerList = Array.isArray(providers) ? providers : [];

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Globe} label="可用提供商" value={providerList.length} color="from-blue-500 to-indigo-500"/>
        <StatCard icon={CheckCircle} label="已配置" value={providerList.filter((p) => p.configured).length}
                  color="from-green-500 to-emerald-500"/>
        <StatCard icon={Link} label="已关联账号" value={linked.length} color="from-purple-500 to-violet-500"/>
        <StatCard icon={Shield} label="登录方式" value={linked.length + 1} sub="含密码登录"
                  color="from-orange-500 to-amber-500"/>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Providers List */}
        <div
          className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="p-5 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <SectionTitle icon={Globe} title="OAuth 提供商" subtitle="管理第三方登录渠道"/>
          </div>
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {loadingProviders ? (
              <div className="p-8 text-center"><Loader className="w-6 h-6 animate-spin mx-auto text-gray-400"/></div>
            ) : providerList.length > 0 ? providerList.map((p: OAuthProvider, i: number) => {
              const name = p.name || (p as any).provider || '';
              const isConfigured = p.configured || false;
              const isLinked = linked.some((l: LinkedAccount) => (l.provider || '').toLowerCase() === name.toLowerCase());
              return (
                <div key={i}
                     className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <ProviderAvatar name={name} icon={p.icon}/>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{p.display_name || name}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {isConfigured ? '已配置 Client ID' : '未配置'}
                        {isLinked && ' · 已关联'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge active={isConfigured} activeText="已启用" inactiveText="未启用"/>
                  </div>
                </div>
              );
            }) : (
              <EmptyState icon={Globe} title="暂无提供商" desc="系统尚未配置 OAuth 提供商"/>
            )}
          </div>
        </div>

        {/* Linked Accounts */}
        <div
          className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="p-5 border-b border-gray-100 dark:border-gray-800">
            <SectionTitle icon={Link} title="已关联账号" subtitle="管理当前用户的第三方绑定"/>
          </div>
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {linked.length > 0 ? linked.map((a: LinkedAccount, i: number) => (
              <div key={i}
                   className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <ProviderAvatar name={a.provider} size="sm"/>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{a.provider_name || a.provider}</p>
                    <p
                      className="text-xs text-gray-400 truncate">{a.provider_user_id || a.email || a.username || ''}</p>
                    {a.bound_at && <p
                      className="text-[10px] text-gray-300 mt-0.5">绑定于 {new Date(a.bound_at).toLocaleDateString('zh-CN')}</p>}
                  </div>
                </div>
                <ActionButton onClick={async () => {
                  if (await confirm({
                    message: `确定解绑 ${a.provider_name || a.provider}？`,
                    variant: 'danger'
                  })) unlinkMut.mutate(a.provider);
                }} icon={Unlink} label="解绑" variant="danger" size="sm" loading={unlinkMut.isPending}/>
              </div>
            )) : (
              <EmptyState icon={Link} title="暂无关联账号" desc="用户尚未绑定任何第三方账号"/>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
