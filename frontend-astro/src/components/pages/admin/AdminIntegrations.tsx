'use client';

import React, {useCallback, useMemo, useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {
  Eye,
  EyeOff,
  GitBranch,
  Globe,
  Loader,
  MessageCircle,
  Save,
  Shield,
  Star,
  CheckCircle2,
  XCircle,
  ExternalLink,
} from 'lucide-react';

// ─── OAuth Provider Configuration ──────────────────────

interface OAuthProviderConfig {
  key: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  docUrl: string;
  scopes: string;
}

const OAUTH_PROVIDERS: OAuthProviderConfig[] = [
  {
    key: 'github',
    label: 'GitHub',
    icon: GitBranch,
    color: 'from-gray-700 to-gray-900',
    docUrl: 'https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app',
    scopes: 'user:email',
  },
  {
    key: 'google',
    label: 'Google',
    icon: Globe,
    color: 'from-blue-500 to-blue-600',
    docUrl: 'https://console.cloud.google.com/apis/credentials',
    scopes: 'openid email profile',
  },
  {
    key: 'wechat',
    label: '微信',
    icon: MessageCircle,
    color: 'from-green-500 to-green-600',
    docUrl: 'https://open.weixin.qq.com/',
    scopes: 'snsapi_userinfo',
  },
  {
    key: 'qq',
    label: 'QQ',
    icon: Star,
    color: 'from-blue-400 to-blue-500',
    docUrl: 'https://connect.qq.com/',
    scopes: 'get_user_info',
  },
  {
    key: 'weibo',
    label: '微博',
    icon: Shield,
    color: 'from-red-500 to-red-600',
    docUrl: 'https://open.weibo.com/',
    scopes: 'email',
  },
];

// ─── Component ─────────────────────────────────────────

interface Props {
  settings: Record<string, string>;
  onSave: (settings: Record<string, string>) => Promise<void>;
}

export default function AdminIntegrations({settings, onSave}: Props) {
  const [localSettings, setLocalSettings] = useState<Record<string, string>>({});
  const [visibleSecrets, setVisibleSecrets] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Initialize local state from settings
  if (!initialized && Object.keys(settings).length > 0) {
    setLocalSettings({...settings});
    setInitialized(true);
  }

  const getProviderSetting = useCallback((provider: string, field: string): string => {
    const key = `oauth_${provider}_${field}`;
    return localSettings[key] ?? settings[key] ?? '';
  }, [localSettings, settings]);

  const setProviderSetting = useCallback((provider: string, field: string, value: string) => {
    const key = `oauth_${provider}_${field}`;
    setLocalSettings(prev => ({...prev, [key]: value}));
  }, []);

  const isEnabled = useCallback((provider: string): boolean => {
    return getProviderSetting(provider, 'enabled') === 'true';
  }, [getProviderSetting]);

  const hasChanges = useMemo(() => {
    const keys = new Set([...Object.keys(settings), ...Object.keys(localSettings)]);
    for (const key of keys) {
      if ((settings[key] || '') !== (localSettings[key] || '')) return true;
    }
    return false;
  }, [settings, localSettings]);

  const handleSave = async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      const allSettings = {...settings, ...localSettings};
      const r = await apiClient.post('/system/settings/', {settings: allSettings, action: 'update_settings'});
      if (r.success) {
        setSaveMsg('保存成功');
        setTimeout(() => setSaveMsg(null), 2000);
      } else {
        setSaveMsg('保存失败: ' + (r.error || '未知错误'));
      }
    } catch (e: any) {
      setSaveMsg('保存失败: ' + (e.message || '网络错误'));
    } finally {
      setSaving(false);
    }
  };

  return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">第三方登录</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              配置 OAuth 提供商以便用户使用第三方账号登录
            </p>
          </div>
          {hasChanges && (
            <button onClick={handleSave} disabled={saving}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-sm font-medium rounded-xl disabled:opacity-50 transition-all shadow-lg shadow-blue-500/25">
              {saving ? <Loader className="w-4 h-4 animate-spin"/> : <Save className="w-4 h-4"/>}
              保存
            </button>
          )}
        </div>

        {saveMsg && (
          <div className={`px-4 py-3 rounded-xl text-sm ${
            saveMsg.includes('成功') 
              ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800' 
              : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800'
          }`}>
            {saveMsg}
          </div>
        )}

        <div className="grid gap-6">
          {OAUTH_PROVIDERS.map(provider => {
            const Icon = provider.icon;
            const enabled = isEnabled(provider.key);
            const clientId = getProviderSetting(provider.key, 'client_id');
            const clientSecret = getProviderSetting(provider.key, 'client_secret');
            const redirectUri = getProviderSetting(provider.key, 'redirect_uri');
            const secretVisible = visibleSecrets[provider.key];

            return (
              <div key={provider.key}
                   className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden transition-all hover:shadow-md">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${provider.color} flex items-center justify-center shadow-sm`}>
                      <Icon className="w-5 h-5 text-white"/>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{provider.label}</h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400">OAuth 2.0 · {provider.scopes}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <a href={provider.docUrl} target="_blank" rel="noopener noreferrer"
                       className="text-xs text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1">
                      查看文档 <ExternalLink className="w-3 h-3"/>
                    </a>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" checked={enabled}
                             onChange={e => setProviderSetting(provider.key, 'enabled', e.target.checked ? 'true' : 'false')}
                             className="sr-only peer"/>
                      <div
                          className="w-11 h-6 bg-gray-200 dark:bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"/>
                    </label>
                  </div>
                </div>

                {/* Body */}
                <div className={`px-6 py-4 space-y-4 ${enabled ? '' : 'opacity-50 pointer-events-none'}`}>
                  {/* Client ID */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                      Client ID
                    </label>
                    <input value={clientId}
                           onChange={e => setProviderSetting(provider.key, 'client_id', e.target.value)}
                           placeholder={`${provider.label} 应用的 Client ID`}
                           className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-mono"
                    />
                  </div>

                  {/* Client Secret */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                      Client Secret
                    </label>
                    <div className="relative">
                      <input type={secretVisible ? 'text' : 'password'} value={clientSecret}
                             onChange={e => setProviderSetting(provider.key, 'client_secret', e.target.value)}
                             placeholder={`${provider.label} 应用的 Client Secret`}
                             className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-mono pr-10"
                      />
                      <button type="button" onClick={() => setVisibleSecrets(prev => ({...prev, [provider.key]: !secretVisible}))}
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        {secretVisible ? <EyeOff className="w-4 h-4"/> : <Eye className="w-4 h-4"/>}
                      </button>
                    </div>
                  </div>

                  {/* Callback URL */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                      回调地址 (Redirect URI)
                    </label>
                    <div className="relative">
                      <input value={redirectUri}
                             onChange={e => setProviderSetting(provider.key, 'redirect_uri', e.target.value)}
                             placeholder={`https://yourdomain.com/api/v2/auth/oauth/${provider.key}/callback`}
                             className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800/50 text-sm text-gray-600 dark:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-mono"
                      />
                      <button type="button"
                              onClick={() => {
                                const defaultUri = typeof window !== 'undefined'
                                  ? `${window.location.protocol}//${window.location.host}/api/v2/auth/oauth/${provider.key}/callback`
                                  : '';
                                setProviderSetting(provider.key, 'redirect_uri', defaultUri);
                              }}
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-blue-600 dark:text-blue-400 hover:underline">
                        自动填充
                      </button>
                    </div>
                    <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
                      在 {provider.label} 开发者控制台创建 OAuth App 时，将此地址填入回调 URL
                    </p>
                  </div>

                  {/* Status indicator */}
                  {enabled && (
                    <div className={`flex items-center gap-2 text-xs ${
                      clientId && clientSecret ? 'text-green-600 dark:text-green-400' : 'text-amber-600 dark:text-amber-400'
                    }`}>
                      {clientId && clientSecret ? (
                        <><CheckCircle2 className="w-3.5 h-3.5"/> 配置完整</>
                      ) : (
                        <><XCircle className="w-3.5 h-3.5"/> 需要填写 Client ID 和 Client Secret</>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Info box */}
        <div className="px-6 py-4 bg-blue-50 dark:bg-blue-900/10 rounded-2xl border border-blue-100 dark:border-blue-800/50">
          <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-1">关于第三方登录</h4>
          <p className="text-xs text-blue-600 dark:text-blue-400 leading-relaxed">
            配置完成后，用户可以在登录页面使用对应的第三方账号快速登录。首次登录将自动创建一个新的本地账号并关联到该第三方账号。
            每个用户可以为每个 OAuth 提供商绑定一个账号。
          </p>
        </div>
      </div>
  );
}
