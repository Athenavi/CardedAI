/**
 * 第三方账号绑定 — Editorial minimal
 * 数据源：GET /api/v2/auth/oauth/bindings（需登录）
 * 绑定：跳转 /api/v2/auth/oauth/{provider}/authorize?mode=bind&next=/settings?tab=security&oauth_bound=<provider>
 * 解绑：DELETE /api/v2/auth/oauth/bindings/{provider}（后端会拦截“唯一登录方式”的场景）
 */

'use client';

import React, {useCallback, useEffect, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';
import {Button} from '@/components/ui/button';
import {Skeleton} from '@/components/ui/skeleton';

interface Binding {
  provider: string;
  label: string;
  provider_user_id: string;
  username?: string | null;
  avatar?: string | null;
  created_at?: string | null;
}

interface Supported {
  key: string;
  label: string;
}

const ERROR_MESSAGES: Record<string, string> = {
  unsupported_provider: '不支持的第三方登录方式',
  provider_disabled: '该第三方登录未启用，请联系管理员',
  provider_not_configured: '该第三方登录尚未配置完成',
  invalid_state: '操作会话已失效，请重新尝试',
  provider_denied: '你取消了第三方授权',
  missing_code: '授权失败：缺少授权码',
  exchange_failed: '与第三方平台通信失败，请稍后重试',
  profile_incomplete: '未能获取第三方账号信息',
  account_link_failed: '账号关联失败，请稍后重试',
  login_required: '请先登录后再绑定第三方账号',
  bind_session_mismatch: '登录状态已变化，请重新登录后再试',
  already_bound_to_other: '该第三方账号已绑定到其它用户',
};

const OAuthBindings: React.FC = () => {
  const [bindings, setBindings] = useState<Binding[]>([]);
  const [supported, setSupported] = useState<Supported[]>([
    {key: 'github', label: 'GitHub'},
    {key: 'google', label: 'Google'},
  ]);
  const [hasPassword, setHasPassword] = useState(true);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await apiClient.get('/auth/oauth/bindings');
      if (res?.success && res.data) {
        setBindings(res.data.bindings || []);
        if (Array.isArray(res.data.supported) && res.data.supported.length) {
          setSupported(res.data.supported);
        }
        setHasPassword(Boolean(res.data.has_password));
      }
    } catch {
      // 未登录或网络异常：保持空态
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // 处理从回调带回的参数
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const bound = params.get('oauth_bound');
    const error = params.get('oauth_error');
    if (bound) setMsg({type: 'ok', text: `已绑定 ${bound} 账号`});
    if (error) setMsg({type: 'err', text: ERROR_MESSAGES[error] || '操作失败，请稍后重试'});
  }, []);

  const bind = (provider: string) => {
    const next = `/settings?tab=security&oauth_bound=${provider}`;
    window.location.href = `/api/v2/auth/oauth/${provider}/authorize?mode=bind&next=${encodeURIComponent(next)}`;
  };

  const unbind = async (provider: string) => {
    setBusy(provider);
    setMsg(null);
    try {
      const res: any = await apiClient.delete(`/auth/oauth/bindings/${provider}`);
      if (res?.success) {
        setMsg({type: 'ok', text: '已解绑'});
        await load();
      } else {
        setMsg({type: 'err', text: res?.error || '解绑失败'});
      }
    } catch (e: any) {
      setMsg({type: 'err', text: e?.message || '解绑失败'});
    } finally {
      setBusy(null);
    }
  };

  return (
    <section className="border border-border bg-card p-5 sm:p-6">
      <header>
        <p className="kicker">OAuth</p>
        <h3 className="editorial-title mt-2 text-lg text-foreground">第三方账号</h3>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          绑定后可使用对应平台的账号一键登录；解绑只影响本平台，不会影响第三方账号本身。
        </p>
      </header>

      {msg && (
        <p className={`mt-4 border px-3 py-2 text-sm ${
          msg.type === 'ok'
            ? 'border-green-200 bg-green-50 text-green-700 dark:border-green-900/50 dark:bg-green-900/20 dark:text-green-400'
            : 'border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-400'
        }`}>
          {msg.text}
        </p>
      )}

      {loading ? (
        <div className="mt-5 space-y-3">
          {Array.from({length: 2}).map((_, index) => (
            <div key={index} className="flex items-center justify-between gap-4 border-b border-border/60 pb-3">
              <Skeleton className="h-4 w-32"/>
              <Skeleton className="h-8 w-16"/>
            </div>
          ))}
        </div>
      ) : (
        <ul className="mt-4 divide-y divide-border/60">
          {supported.map((provider) => {
            const binding = bindings.find((item) => item.provider === provider.key);
            const canUnbind = Boolean(binding) && (hasPassword || bindings.length > 1);
            return (
              <li key={provider.key} className="flex items-center justify-between gap-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">{provider.label}</p>
                  <p className="mt-0.5 truncate font-mono text-xs text-muted-foreground">
                    {binding
                      ? (binding.username ? `@${binding.username}` : binding.provider_user_id)
                      : '未绑定'}
                  </p>
                </div>
                {binding ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!canUnbind || busy === provider.key}
                    onClick={() => unbind(provider.key)}
                    title={canUnbind ? '解除绑定' : '这是你唯一的登录方式，请先设置本地密码'}
                  >
                    {busy === provider.key ? '解绑中…' : '解绑'}
                  </Button>
                ) : (
                  <Button size="sm" onClick={() => bind(provider.key)}>
                    绑定
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {!loading && !hasPassword && (
        <p className="mt-4 text-xs text-amber-600 dark:text-amber-400">
          当前账号没有本地密码，请至少保留一种已绑定的登录方式，否则将无法登录。
        </p>
      )}
    </section>
  );
};

export default OAuthBindings;
