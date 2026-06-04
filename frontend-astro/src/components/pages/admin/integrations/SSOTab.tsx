'use client';

import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {SectionTitle, StatusBadge} from '@/components/admin/shared-ui';
import {Check, Key, Server, Shield} from 'lucide-react';
import {apiClient} from '@/lib/api/base-client';
import {ProviderAvatar, InputField} from './shared';


export default function SSOTab({showToast}: { showToast: (msg: string, type?: 'success' | 'error' | 'info') => void }) {
  const [activeSection, setActiveSection] = useState<'oauth2' | 'saml' | 'ldap'>('oauth2');

  const {data: ssoConfig} = useQuery({
    queryKey: ['integ-sso-config'],
    queryFn: async () => {
      const r = await apiClient.get('/integrations/sso/config');
      return r.success && r.data ? r.data : {};
    },
  });

  const ssoProviders = ssoConfig?.oauth || {};
  const samlConfigured = ssoConfig?.saml || false;
  const ldapConfigured = ssoConfig?.ldap || false;

  const sections = [
    {
      key: 'oauth2' as const,
      label: 'OAuth 2.0',
      icon: Key,
      desc: 'Google / GitHub / Microsoft',
      configured: Object.values(ssoProviders).some(Boolean)
    },
    {
      key: 'saml' as const,
      label: 'SAML 2.0',
      icon: Shield,
      desc: 'Okta / Azure AD / OneLogin',
      configured: samlConfigured
    },
    {
      key: 'ldap' as const,
      label: 'LDAP',
      icon: Server,
      desc: 'OpenLDAP / Active Directory',
      configured: ldapConfigured
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {sections.map(s => {
          const Icon = s.icon;
          return (
            <div key={s.key}
                 className={`bg-white dark:bg-gray-900 rounded-2xl border p-5 cursor-pointer transition-all hover:shadow-md ${activeSection === s.key ? 'ring-2 ring-blue-500 border-blue-200' : 'border-gray-200 dark:border-gray-700'}`}
                 onClick={() => setActiveSection(s.key)}>
              <div className="flex items-center justify-between mb-3">
                <div
                  className={`w-10 h-10 rounded-xl ${s.configured ? 'bg-gradient-to-br from-green-500 to-emerald-500' : 'bg-gradient-to-br from-gray-400 to-gray-500'} flex items-center justify-center`}>
                  <Icon className="w-5 h-5 text-white"/>
                </div>
                <StatusBadge active={s.configured} activeText="已配置" inactiveText="未配置"/>
              </div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">{s.label}</p>
              <p className="text-xs text-gray-400 mt-1">{s.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Detail Panels */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
        {activeSection === 'oauth2' && (
          <div className="space-y-6">
            <SectionTitle icon={Key} title="OAuth 2.0 配置" subtitle="通过环境变量配置 OAuth2 提供商凭证"/>
            <div className="grid sm:grid-cols-3 gap-4">
              {['Google', 'GitHub', 'Microsoft'].map(name => {
                const key = name.toLowerCase();
                const configured = ssoProviders[key] || false;
                return (
                  <div key={name}
                       className={`p-4 rounded-xl border ${configured ? 'border-green-200 bg-green-50/50 dark:bg-green-900/10 dark:border-green-800' : 'border-gray-200 dark:border-gray-700'}`}>
                    <div className="flex items-center gap-3 mb-3">
                      <ProviderAvatar name={key} size="sm"/>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{name}</p>
                        <p
                          className={`text-xs ${configured ? 'text-green-600' : 'text-gray-400'}`}>{configured ? '已配置' : '未配置'}</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <InputField label={`Client ID`} value="" onChange={() => {
                      }} placeholder={`OAUTH_${key.toUpperCase()}_CLIENT_ID`} hint="通过环境变量设置"/>
                      <InputField label="Client Secret" value="" onChange={() => {
                      }} type="password" placeholder={`OAUTH_${key.toUpperCase()}_CLIENT_SECRET`}
                                  hint="通过环境变量设置"/>
                    </div>
                  </div>
                );
              })}
            </div>
            <div
              className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-800/30">
              <p className="text-xs text-blue-700 dark:text-blue-300">
                <strong>配置方式：</strong>在 <code
                className="bg-blue-100 dark:bg-blue-800 px-1 rounded">.env</code> 文件中设置对应环境变量后重启服务即可。授权端点：<code
                className="bg-blue-100 dark:bg-blue-800 px-1 rounded">/api/v2/integrations/sso/oauth/{"{provider}"}/authorize</code>
              </p>
            </div>
          </div>
        )}

        {activeSection === 'saml' && (
          <div className="space-y-6">
            <SectionTitle icon={Shield} title="SAML 2.0 配置" subtitle="配置企业身份提供商 (IdP) 进行单点登录"/>
            <div className="grid sm:grid-cols-2 gap-6">
              <div className="space-y-4">
                <InputField label="Entity ID (IdP)" value="" onChange={() => {
                }} placeholder="https://idp.company.com/metadata" hint="身份提供商的实体 ID / Metadata URL"/>
                <InputField label="SSO URL" value="" onChange={() => {
                }} placeholder="https://idp.company.com/sso/saml" hint="IdP 的 SSO 登录 URL"/>
                <InputField label="SLO URL" value="" onChange={() => {
                }} placeholder="https://idp.company.com/slo/saml" hint="单点登出 URL（可选）"/>
                <InputField label="X.509 证书" value="" onChange={() => {
                }} placeholder="-----BEGIN CERTIFICATE-----" hint="IdP 的签名证书"/>
              </div>
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">支持的 IdP</p>
                  <div className="space-y-2">
                    {['Okta', 'Azure AD', 'OneLogin', 'Auth0'].map(idp => (
                      <div key={idp} className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                        <Check className="w-3.5 h-3.5 text-green-500"/>{idp}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">SP 端点</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">ACS:
                    /api/v2/integrations/sso/saml/acs</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 font-mono mt-1">SLO:
                    /api/v2/integrations/sso/saml/slo</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'ldap' && (
          <div className="space-y-6">
            <SectionTitle icon={Server} title="LDAP 配置" subtitle="连接企业目录服务进行身份认证"/>
            <div className="grid sm:grid-cols-2 gap-6">
              <div className="space-y-4">
                <InputField label="LDAP 服务器" value="" onChange={() => {
                }} placeholder="ldap://ldap.company.com:389" hint="LDAP 服务器地址"/>
                <InputField label="Base DN" value="" onChange={() => {
                }} placeholder="dc=company,dc=com" hint="搜索基准 DN"/>
                <InputField label="Bind DN" value="" onChange={() => {
                }} placeholder="cn=admin,dc=company,dc=com" hint="绑定用户 DN"/>
                <InputField label="Bind 密码" value="" onChange={() => {
                }} type="password" placeholder="绑定密码" hint="绑定用户密码"/>
              </div>
              <div className="space-y-4">
                <InputField label="用户搜索过滤器" value="" onChange={() => {
                }} placeholder="(uid={username})" hint="用户搜索条件模板"/>
                <InputField label="用户属性映射" value="" onChange={() => {
                }} placeholder="uid,mail,cn" hint="需要获取的属性列表"/>
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">认证端点</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">POST
                    /api/v2/integrations/sso/ldap/authenticate</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
