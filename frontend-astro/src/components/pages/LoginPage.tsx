'use client';

import React, {useEffect, useRef, useState} from 'react';
import {Controller, FormProvider, useForm} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {apiClient} from '@/lib/api/base-client';
import {getCookie, setCookie} from '@/lib/auth-utils';
import {type LoginFormData, loginSchema, type TwoFactorFormData, twoFactorSchema} from '@/lib/schemas';
import {useTranslation} from '@/lib/i18n';
import {cn} from '@/lib/utils';
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  ChevronRight,
  Eye,
  EyeOff,
  GitBranch,
  Globe,
  Loader,
  Lock,
  QrCode,
  Shield,
  Sparkles,
  User,
  Zap
} from 'lucide-react';
import AuthShell from '@/components/auth/AuthShell';
import AuthField from '@/components/auth/AuthField';
import {Button} from '@/components/ui/button';
import {Checkbox} from '@/components/ui/checkbox';

export default function LoginPage() {
  const {t} = useTranslation();
  const [mode, setMode] = useState<'password' | 'qrcode'>('password');
  const [pv, setPv] = useState(false);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  // 第三方登录（GitHub / Google）：启用状态由后台配置决定
  const [oauthProviders, setOauthProviders] = useState<Array<{
    key: string;
    label: string;
    enabled: boolean;
    configured: boolean
  }>>([]);

  useEffect(() => {
    fetch('/api/v2/auth/oauth/providers')
      .then(r => r.json())
      .then(d => {
        if (d?.success && Array.isArray(d.data)) setOauthProviders(d.data);
      })
      .catch(() => {
      });

    const oauthError = new URLSearchParams(window.location.search).get('oauth_error');
    if (oauthError) {
      const messages: Record<string, string> = {
        unsupported_provider: '不支持的第三方登录方式',
        provider_disabled: '该第三方登录未启用，请联系管理员',
        provider_not_configured: '该第三方登录尚未配置完成',
        invalid_state: '登录会话已失效，请重新尝试',
        provider_denied: '你取消了第三方授权',
        missing_code: '授权失败：缺少授权码',
        exchange_failed: '与第三方平台通信失败，请稍后重试',
        profile_incomplete: '未能获取第三方账号信息',
        account_link_failed: '账号关联失败，请稍后重试',
      };
      setErr(messages[oauthError] || '第三方登录失败，请稍后重试');
    }
  }, []);

  const oauthReady = (key: string) => {
    const provider = oauthProviders.find(item => item.key === key);
    return provider ? provider.configured : true;
  };

  const startOauthLogin = (key: string) => {
    const target = new URLSearchParams(window.location.search).get('next') || '/';
    window.location.href = `/api/v2/auth/oauth/${key}/authorize?next=${encodeURIComponent(target)}`;
  };

  const features = [
    {icon: Sparkles, titleKey: 'login.features.aiWriting', descKey: 'login.features.aiWritingDesc'},
    {icon: Zap, titleKey: 'login.features.fastPublish', descKey: 'login.features.fastPublishDesc'},
    {icon: Shield, titleKey: 'login.features.secure', descKey: 'login.features.secureDesc'},
    {icon: BookOpen, titleKey: 'login.features.immersiveReading', descKey: 'login.features.immersiveReadingDesc'},
  ];

  // react-hook-form — 登录表单
  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema) as any,
    defaultValues: {username: '', password: '', remember: false},
  });

  // react-hook-form — 2FA 表单
  const twoFAForm = useForm<TwoFactorFormData>({
    resolver: zodResolver(twoFactorSchema),
    defaultValues: {code: ''},
  });

  // 2FA
  const [fa, setFa] = useState<{ tempToken: string; userId: number } | null>(null);
  const [backup, setBackup] = useState(false);

  // QR code
  const [qrImg, setQrImg] = useState('');
  const [, setQrToken] = useState('');
  const [qrStatus, setQrStatus] = useState<'idle' | 'loading' | 'ready' | 'pending' | 'success' | 'expired'>('idle');
  const pollRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const cancelRef = useRef(false);
  const [countdown, setCountdown] = useState(0);
  const countdownTimerRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const generateQRRef = useRef<(() => Promise<void>) | null>(null);

  // Auto-redirect if logged in (also try refresh token if access token expired)
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    (async () => {
      try {
        const accessToken = getCookie('access_token');
        if (accessToken) {
          // 有 access_token，验证是否有效
          const r = await apiClient.get('/users/me');
          if (r.success && r.data) {
            window.location.href = new URLSearchParams(window.location.search).get('next') || '/profile';
            return;
          }
        }
        // access_token 不存在或已失效，尝试用 refresh_token 刷新
        const refreshToken = getCookie('refresh_token');
        if (refreshToken) {
          const refreshResult = await apiClient.post('/auth/token/refresh', {refresh: refreshToken});
          if (refreshResult.success && refreshResult.data) {
            const d = refreshResult.data as any;
            if (d.access_token) setCookie('access_token', d.access_token, 3600);
            if (d.refresh_token) setCookie('refresh_token', d.refresh_token, 604800);
            // 刷新成功，重新验证用户
            const r2 = await apiClient.get('/users/me');
            if (r2.success && r2.data) {
              window.location.href = new URLSearchParams(window.location.search).get('next') || '/profile';
              return;
            }
          }
          // refresh 失效，清除无效的 refresh_token
          setCookie('refresh_token', '', 0);
        }
      } catch {
        // 忽略错误，显示登录页
      }
      setChecking(false);
    })();
  }, []);

  const next = () => new URLSearchParams(window.location.search).get('next') || '/profile';

  // Cleanup polling + countdown
  useEffect(() => {
    return () => {
      cancelRef.current = true;
      if (pollRef.current) clearTimeout(pollRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    };
  }, []);

  // Keep generateQR ref current
  useEffect(() => {
    generateQRRef.current = generateQR;
  });

  // Countdown timer for QR code expiry
  useEffect(() => {
    if (countdown <= 0 || qrStatus === 'success' || qrStatus === 'expired' || qrStatus === 'idle' || qrStatus === 'loading') return;
    countdownTimerRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownTimerRef.current!);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => {
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    };
  }, [countdown > 0, qrStatus]);

  // Auto-refresh when QR code expires via countdown
  useEffect(() => {
    if (countdown !== 0) return;
    if (qrStatus !== 'ready' && qrStatus !== 'pending') return;
    // QR expired — stop polling, show expired state, then auto-refresh
    cancelRef.current = true;
    if (pollRef.current) clearTimeout(pollRef.current);
    setQrStatus('expired');
    const timer = setTimeout(() => {
      cancelRef.current = false;
      generateQRRef.current?.();
    }, 2000);
    return () => clearTimeout(timer);
  }, [countdown]);

  // ═══ QR Login Generator (uses V2 backend) ═══
  const generateQR = async () => {
    setErr('');
    setQrStatus('loading');
    setQrImg('');
    setQrToken('');
    cancelRef.current = false;
    try {
      const r = await apiClient.get('/auth/qr/generate');
      if (!r.success || !r.data) {
        setErr(r.error || t('login.qrGenerateFailed'));
        setQrStatus('idle');
        return;
      }
      const token = r.data.token || r.data.qr_token;
      const qrCodeDataUrl = r.data.qr_code || r.data.qr_data;
      setQrToken(token);
      if (qrCodeDataUrl && qrCodeDataUrl.startsWith('data:')) {
        setQrImg(qrCodeDataUrl);
      } else {
        try {
          const mod = await import('qrcode');
          const loginUrl = `${window.location.origin}/api/v2/mobile-login?login_token=${token}`;
          const dataUrl = await mod.toDataURL(loginUrl, {
            width: 280,
            margin: 2,
            color: {dark: '#1e40af', light: '#ffffff'}
          });
          setQrImg(dataUrl);
        } catch {
          setErr(t('login.qrGenerateFailed'));
          setQrStatus('idle');
          return;
        }
      }
      // Calculate countdown from expires_at
      const expiresAt = r.data.expires_at ? parseInt(r.data.expires_at) * 1000 : Date.now() + 180000;
      setCountdown(Math.max(0, Math.floor((expiresAt - Date.now()) / 1000)));
      setQrStatus('ready');
      pollQR(token);
    } catch {
      setErr(t('login.qrGenerateFailed'));
      setQrStatus('idle');
    }
  };

  const pollQR = (token: string) => {
    if (cancelRef.current) return;
    pollRef.current = setTimeout(async () => {
      if (cancelRef.current) return;
      try {
        const r = await apiClient.get(`/auth/qr/status`, {token, 'no-cache': '1'});
        const data = r.success && r.data ? r.data : {status: 'pending'};
        const st = data.status;
        if (st === 'confirmed' || st === 'success') {
          setCountdown(0);
          setQrStatus('success');
          const refreshToken = data.refresh_token;
          if (refreshToken) setCookie('refresh_token', refreshToken, 604800);
          const accessR = await apiClient.post('/auth/token/refresh', {refresh: refreshToken});
          if (accessR.success && accessR.data) {
            setCookie('access_token', (accessR.data as any).access_token || (accessR.data as any).access || '', 3600);
            window.location.href = next();
            return;
          }
          setErr(t('login.qrScanSuccessButTokenFailed'));
          setQrStatus('idle');
          return;
        } else if (st === 'expired') {
          setCountdown(0);
          setQrStatus('expired');
          setErr(t('login.qrExpired'));
          return;
        } else {
          setQrStatus('pending');
          pollQR(token);
        }
      } catch {
        if (!cancelRef.current) pollQR(token);
      }
    }, 2000);
  };

  // ═══ Password Login ═══
  const onLoginSubmit = async (data: LoginFormData) => {
    setBusy(true);
    setErr('');
    try {
      const r = await apiClient.postForm('/auth/login', {
        username: data.username,
        password: data.password,
        remember_me: data.remember
      });
      if (!r.success) {
        setErr(r.error || r.message || t('login.loginFailed'));
        setBusy(false);
        return;
      }
      const d = r.data as any;
      if (d.requires_2fa && d.temp_token) {
        setFa({tempToken: d.temp_token, userId: d.user_id});
        setBusy(false);
        return;
      }
      if (d.access_token) setCookie('access_token', d.access_token, 3600);
      if (d.refresh_token) setCookie('refresh_token', d.refresh_token, 604800);
      window.location.href = next();
    } catch {
      setErr(t('login.networkError'));
      setBusy(false);
    }
  };

  // ═══ 2FA ═══
  const on2FASubmit = async (data: TwoFactorFormData) => {
    if (!fa) return;
    setBusy(true);
    setErr('');
    try {
      const r = await apiClient.post('/security/2fa/verify-login', {user_id: fa.userId, token: data.code});
      if (r.success && r.data) {
        const d = r.data as any;
        if (d.access_token) setCookie('access_token', d.access_token, 3600);
        if (d.refresh_token) setCookie('refresh_token', d.refresh_token, 604800);
        window.location.href = next();
      } else setErr(r.error || t('login.verificationFailed'));
    } catch {
      setErr(t('login.verificationFailed'));
    } finally {
      setBusy(false);
    }
  };

  if (checking) return (
    <div className="flex min-h-[calc(100dvh-3.5rem)] items-center justify-center">
      <div className="flex items-center gap-3 text-xs tracking-[0.18em] text-muted-foreground">
        <Loader className="h-4 w-4 animate-spin"/>
        {t('login.verifyingStatus')}
      </div>
    </div>
  );

  const heading = fa
    ? t('login.twoFactorTitle')
    : mode === 'qrcode'
      ? t('login.qrLogin')
      : t('login.title');

  const subheading = fa
    ? t('login.twoFactorSubtitle')
    : mode === 'qrcode'
      ? t('login.scanQRCode')
      : t('login.subtitle');

  const modeTabs = [
    {value: 'password' as const, icon: Lock, label: t('login.passwordLogin')},
    {value: 'qrcode' as const, icon: QrCode, label: t('login.qrLogin')},
  ];

  const scanSteps = [t('login.scanStep1'), t('login.scanStep2'), t('login.scanStep3'), t('login.scanStep4')];

  return (
    <AuthShell
      tagline={t('login.branding.tagline')}
      title={heading}
      subtitle={subheading}
      footnote={
        <div className="space-y-3">
          <p>
            {t('login.noAccount')}{' '}
            <a href="/register"
               className="font-medium text-foreground underline decoration-border underline-offset-4 transition-colors hover:decoration-foreground">
              {t('login.registerNow')}
            </a>
          </p>
          <p className="text-xs text-muted-foreground/75">
            {t('login.agreeToTerms')}{' '}
            <a href="/terms" className="underline decoration-border underline-offset-4 hover:decoration-foreground">
              {t('login.termsOfService')}
            </a>{' '}
            {t('common.and') || '和'}{' '}
            <a href="/privacy" className="underline decoration-border underline-offset-4 hover:decoration-foreground">
              {t('login.privacyPolicy')}
            </a>
          </p>
        </div>
      }
      note={
        <div className="space-y-5">
          <dl className="flex flex-wrap gap-x-10 gap-y-4">
            {[
              {value: '50K+', label: t('login.branding.activeCreators')},
              {value: '1M+', label: t('login.branding.qualityArticles')},
              {value: '100+', label: t('login.branding.countries')},
            ].map(({value, label}) => (
              <div key={label}>
                <dd className="font-mono text-lg tabular-nums text-foreground">{value}</dd>
                <dt className="mt-0.5 text-[10px] tracking-[0.14em] text-muted-foreground">{label}</dt>
              </div>
            ))}
          </dl>
          <p className="text-xs leading-relaxed text-muted-foreground/80">
            {features.map(f => t(f.titleKey)).join(' · ')}
          </p>
        </div>
      }
    >
      {/* Error */}
      {err && (
        <div
          className="mb-8 flex items-start gap-3 border-l-2 border-destructive bg-destructive/[0.04] py-3 pl-4 pr-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0"/>
          <span>{err}</span>
        </div>
      )}

      {/* ═══ 2FA ═══ */}
      {fa ? (
        <FormProvider {...twoFAForm}>
          <div className="space-y-8">
            <p
              className="border-l-2 border-primary/50 bg-muted/40 py-3 pl-4 pr-3 text-sm leading-relaxed text-muted-foreground">
              {backup ? t('login.twoFactorBackupHint') : t('login.twoFactorCodeHint')}
            </p>

            <form onSubmit={twoFAForm.handleSubmit(on2FASubmit)} className="space-y-8">
              <Controller
                name="code"
                control={twoFAForm.control}
                render={({field}) => (
                  <div>
                    <input
                      type="text"
                      inputMode="numeric"
                      autoFocus
                      aria-label={backup ? t('login.twoFactorPlaceholder') : t('login.twoFactorTitle')}
                      value={field.value}
                      onChange={e => field.onChange(e.target.value.replace(/\D/g, '').slice(0, backup ? 8 : 6))}
                      placeholder={backup ? t('login.twoFactorPlaceholder') : '000000'}
                      className={cn(
                        'h-16 w-full border-0 border-b bg-transparent pb-2 text-center font-mono text-3xl tabular-nums tracking-[0.35em] text-foreground transition-colors',
                        'placeholder:text-muted-foreground/40 focus:outline-none',
                        twoFAForm.formState.errors.code ? 'border-destructive' : 'border-input focus:border-primary',
                      )}
                    />
                    {twoFAForm.formState.errors.code && (
                      <p className="mt-2 text-xs text-destructive">{twoFAForm.formState.errors.code.message}</p>
                    )}
                  </div>
                )}
              />

              <Button type="submit" disabled={busy} className="h-12 w-full rounded-sm text-[15px]">
                {busy ? (
                  <span className="flex items-center gap-2">
                    <Loader className="h-4 w-4 animate-spin"/> {t('login.twoFactorVerifying')}
                  </span>
                ) : t('login.verifyButton')}
              </Button>

              <div className="flex items-center justify-between text-sm">
                <button
                  type="button"
                  onClick={() => {
                    setBackup(!backup);
                    twoFAForm.reset({code: ''});
                  }}
                  className="text-muted-foreground underline decoration-border underline-offset-4 transition-colors hover:text-foreground hover:decoration-foreground"
                >
                  {backup ? t('login.twoFactorUseCode') : t('login.twoFactorUseBackup')}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setFa(null);
                    twoFAForm.reset({code: ''});
                    setErr('');
                  }}
                  className="flex items-center gap-1.5 text-muted-foreground transition-colors hover:text-foreground"
                >
                  <ArrowLeft className="h-3.5 w-3.5"/> {t('login.backToLogin')}
                </button>
              </div>
            </form>
          </div>
        </FormProvider>
      ) : (
        <>
          {/* Mode switch */}
          <div className="mb-9 flex border-b border-border">
            {modeTabs.map(({value, icon: Icon, label}) => (
              <button
                key={value}
                type="button"
                aria-pressed={mode === value}
                onClick={() => {
                  setMode(value);
                  setErr('');
                  if (value === 'qrcode' && !qrImg) generateQR();
                }}
                className={cn(
                  '-mb-px mr-8 flex items-center gap-2 border-b-2 py-3 text-sm transition-colors',
                  mode === value
                    ? 'border-primary font-medium text-foreground'
                    : 'border-transparent text-muted-foreground hover:text-foreground',
                )}
              >
                <Icon className="h-4 w-4"/> {label}
              </button>
            ))}
          </div>

          {/* ═══ 密码登录 ═══ */}
          {mode === 'password' && (
            <FormProvider {...loginForm}>
              <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-7">
                <AuthField
                  label={t('login.usernameOrEmail')}
                  icon={User}
                  autoFocus
                  placeholder={t('login.usernameOrEmailPlaceholder')}
                  error={loginForm.formState.errors.username?.message}
                  {...loginForm.register('username')}
                />

                <AuthField
                  label={t('login.password')}
                  icon={Lock}
                  type={pv ? 'text' : 'password'}
                  placeholder={t('login.passwordPlaceholder')}
                  error={loginForm.formState.errors.password?.message}
                  hint={
                    <a href="/forgot-password"
                       className="text-xs text-muted-foreground underline decoration-border underline-offset-4 transition-colors hover:text-foreground hover:decoration-foreground">
                      {t('login.forgotPassword')}
                    </a>
                  }
                  action={
                    <button
                      type="button"
                      onClick={() => setPv(!pv)}
                      aria-label={t('login.password')}
                      className="flex h-8 w-8 items-center justify-center text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {pv ? <EyeOff className="h-4 w-4"/> : <Eye className="h-4 w-4"/>}
                    </button>
                  }
                  {...loginForm.register('password')}
                />

                {/* Remember me */}
                <Controller
                  name="remember"
                  control={loginForm.control}
                  render={({field}) => (
                    <label
                      className="flex w-fit cursor-pointer items-center gap-2.5 text-sm text-muted-foreground select-none">
                      <Checkbox
                        checked={Boolean(field.value)}
                        onCheckedChange={(checked) => field.onChange(checked === true)}
                      />
                      <span>{t('login.rememberMeStatus')}</span>
                    </label>
                  )}
                />

                <Button type="submit" disabled={busy} className="h-12 w-full gap-2 rounded-sm text-[15px]">
                  {busy ? (
                    <>
                      <Loader className="h-4 w-4 animate-spin"/>
                      <span>{t('login.loggingIn')}</span>
                    </>
                  ) : (
                    <>
                      <span>{t('login.loginButton')}</span>
                      <ChevronRight className="h-4 w-4"/>
                    </>
                  )}
                </Button>

                {/* Divider */}
                <div className="relative">
                  <div className="h-px w-full bg-border"/>
                  <span
                    className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-4 text-xs text-muted-foreground">
                    {t('login.orOtherMethods')}
                  </span>
                </div>

                {/* Social login */}
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => startOauthLogin('github')}
                    disabled={busy || !oauthReady('github')}
                    title={oauthReady('github') ? '使用 GitHub 账号登录' : '管理员尚未启用 GitHub 登录'}
                    className="h-12 gap-2 rounded-sm border-border font-normal"
                  >
                    <GitBranch className="h-4 w-4"/> GitHub
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => startOauthLogin('google')}
                    disabled={busy || !oauthReady('google')}
                    title={oauthReady('google') ? '使用 Google 账号登录' : '管理员尚未启用 Google 登录'}
                    className="h-12 gap-2 rounded-sm border-border font-normal"
                  >
                    <Globe className="h-4 w-4"/> Google
                  </Button>
                </div>
              </form>
            </FormProvider>
          )}

          {/* ═══ 扫码登录 ═══ */}
          {mode === 'qrcode' && (
            <div className="space-y-10">
              <div className="flex flex-col items-center gap-7">
                {/* QR —— 无外框，二维码直接落在纸底上 */}
                {qrStatus === 'loading' ? (
                  <div className="flex h-[190px] w-[190px] items-center justify-center">
                    <Loader className="h-5 w-5 animate-spin text-muted-foreground"/>
                  </div>
                ) : qrImg ? (
                  <div className="relative">
                    <img src={qrImg} alt={t('login.qrLogin')} className="h-[190px] w-[190px]"/>
                    {qrStatus === 'success' && (
                      <div className="absolute inset-0 flex items-center justify-center bg-primary/95">
                        <svg className="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                             strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                        </svg>
                      </div>
                    )}
                    {qrStatus === 'expired' && (
                      <div
                        className="absolute inset-0 flex items-center justify-center bg-background/95 px-4 text-center">
                        <p className="text-xs text-muted-foreground">{t('login.qrExpiredAutoRefresh')}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={generateQR}
                    aria-label={t('login.qrClickToGenerate')}
                    className="flex h-[190px] w-[190px] items-center justify-center text-muted-foreground transition-colors hover:text-foreground"
                  >
                    <QrCode className="h-7 w-7"/>
                  </button>
                )}

                {/* Status */}
                <div className="w-full max-w-[19rem] text-center">
                  <p className="text-sm text-foreground">
                    {qrStatus === 'loading' ? t('login.generatingQR')
                      : qrStatus === 'ready' || qrStatus === 'pending' ? t('login.qrWaitingScan')
                        : qrStatus === 'success' ? t('login.qrScanSuccess')
                          : qrStatus === 'expired' ? t('login.qrExpired')
                            : t('login.qrClickToGenerate')}
                  </p>
                  {countdown > 0 && (qrStatus === 'ready' || qrStatus === 'pending') && (
                    <p className={cn(
                      'mt-1.5 font-mono text-xs tabular-nums',
                      countdown <= 30 ? 'text-destructive' : 'text-muted-foreground',
                    )}>
                      {t('login.qrExpiresIn', {seconds: countdown})}
                    </p>
                  )}
                  {(qrStatus === 'expired' || qrStatus === 'idle') && (
                    <button
                      type="button"
                      onClick={generateQR}
                      className="mt-3 text-sm text-muted-foreground underline decoration-border underline-offset-4 transition-colors hover:text-foreground hover:decoration-foreground"
                    >
                      {qrStatus === 'expired' ? t('login.qrRegenerate') : t('login.qrGenerate')}
                    </button>
                  )}
                </div>
              </div>

              {/* Steps —— 等宽序号 + 发丝线，无卡片 */}
              <div>
                <p className="mb-3 text-[11px] tracking-[0.2em] text-muted-foreground">{t('login.scanSteps')}</p>
                <ol className="border-t border-border">
                  {scanSteps.map((step, i) => (
                    <li key={i}
                        className="flex items-baseline gap-4 border-b border-border py-2.5 text-sm text-muted-foreground">
                      <span className="font-mono text-[11px] tabular-nums text-muted-foreground/60">
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}
        </>
      )}
    </AuthShell>
  );
}
