'use client';

import React, {useEffect, useRef, useState} from 'react';
import {Controller, FormProvider, useForm} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {apiClient} from '@/lib/api/base-client';
import {getCookie, setCookie} from '@/lib/auth-utils';
import {type LoginFormData, loginSchema, type TwoFactorFormData, twoFactorSchema} from '@/lib/schemas';
import {useTranslation} from '@/lib/i18n';
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
  Smartphone,
  Sparkles,
  User,
  Zap
} from 'lucide-react';

export default function LoginPage() {
  const {t} = useTranslation();
  const [mode, setMode] = useState<'password'|'qrcode'>('password');
  const [pv, setPv] = useState(false); const [err, setErr] = useState(''); const [busy, setBusy] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const features = [
    {icon: Sparkles, titleKey: 'login.features.aiWriting', descKey: 'login.features.aiWritingDesc'},
    {icon: Zap, titleKey: 'login.features.fastPublish', descKey: 'login.features.fastPublishDesc'},
    {icon: BookOpen, titleKey: 'login.features.immersiveReading', descKey: 'login.features.immersiveReadingDesc'},
    {icon: Shield, titleKey: 'login.features.secure', descKey: 'login.features.secureDesc'},
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
  const [fa, setFa] = useState<{tempToken:string;userId:number}|null>(null);
  const [backup, setBackup] = useState(false);

  // QR code
  const [qrImg, setQrImg] = useState('');
  const [, setQrToken] = useState('');
  const [qrStatus, setQrStatus] = useState<'idle'|'loading'|'ready'|'pending'|'success'|'expired'>('idle');
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

  const next = () => new URLSearchParams(window.location.search).get('next')||'/profile';

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
    setErr(''); setQrStatus('loading'); setQrImg(''); setQrToken(''); cancelRef.current = false;
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
          const dataUrl = await mod.toDataURL(loginUrl, {width:280,margin:2,color:{dark:'#1e40af',light:'#ffffff'}});
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
      if (d.requires_2fa && d.temp_token) { setFa({tempToken:d.temp_token, userId:d.user_id}); setBusy(false); return; }
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
    setBusy(true); setErr('');
    try {
      const r = await apiClient.post('/security/2fa/verify-login', {user_id: fa.userId, token: data.code});
      if (r.success && r.data) {
        const d = r.data as any; if (d.access_token) setCookie('access_token', d.access_token, 3600);
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
      <div
          className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-blue-200 dark:border-blue-800 rounded-full animate-spin"/>
            <div
                className="absolute inset-0 w-12 h-12 border-4 border-transparent border-t-blue-600 rounded-full animate-spin"/>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 animate-pulse">{t('login.verifyingStatus')}</p>
        </div>
      </div>
  );

  return (
      <div
          className="min-h-screen flex bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
        {/* ═══ Left Panel - Branding ═══ */}
        <div className="hidden lg:flex lg:w-1/2 xl:w-[45%] relative overflow-hidden">
          {/* Gradient Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700"/>

          {/* Animated Orbs */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-20 -left-20 w-80 h-80 bg-blue-400/20 rounded-full blur-3xl animate-pulse"
                 style={{animationDuration: '4s'}}/>
            <div className="absolute bottom-20 right-10 w-60 h-60 bg-purple-400/20 rounded-full blur-3xl animate-pulse"
                 style={{animationDuration: '6s'}}/>
            <div className="absolute top-1/3 left-1/3 w-40 h-40 bg-indigo-400/20 rounded-full blur-3xl animate-pulse"
                 style={{animationDuration: '5s'}}/>
          </div>

          {/* Grid Pattern */}
          <div className="absolute inset-0 opacity-10" style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
            backgroundSize: '40px 40px'
          }}/>

          {/* Content */}
          <div className="relative z-10 flex flex-col justify-between p-12 xl:p-16 w-full">
            {/* Logo & Brand */}
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-white"/>
                </div>
                <span className="text-xl font-bold text-white">FastBlog</span>
              </div>
            </div>

            {/* Main Content */}
            <div className="space-y-8">
              <div>
                <h2 className="text-3xl xl:text-4xl font-bold text-white leading-tight mb-4">
                  {t('login.branding.tagline').split('\n').map((line, i) => (
                    <React.Fragment key={i}>{i > 0 && <br/>}{line}</React.Fragment>
                  ))}
                </h2>
                <p className="text-blue-100/80 text-lg leading-relaxed max-w-md">
                  {t('login.branding.description')}
                </p>
              </div>

              {/* Features */}
              <div className="grid grid-cols-2 gap-4">
                {features.map((feat, i) => {
                  const Icon = feat.icon;
                  return (
                      <div key={i}
                           className="group p-4 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/10 hover:bg-white/15 transition-all duration-300">
                        <Icon className="w-6 h-6 text-blue-200 mb-3 group-hover:scale-110 transition-transform"/>
                        <h3 className="text-sm font-semibold text-white mb-1">{t(feat.titleKey)}</h3>
                        <p className="text-xs text-blue-100/70 leading-relaxed">{t(feat.descKey)}</p>
                      </div>
                  );
                })}
              </div>
            </div>

            {/* Bottom Stats */}
            <div className="flex items-center gap-8">
              <div>
                <div className="text-2xl font-bold text-white">50K+</div>
                <div className="text-sm text-blue-100/70">{t('login.branding.activeCreators')}</div>
              </div>
              <div className="w-px h-10 bg-white/20"/>
              <div>
                <div className="text-2xl font-bold text-white">1M+</div>
                <div className="text-sm text-blue-100/70">{t('login.branding.qualityArticles')}</div>
              </div>
              <div className="w-px h-10 bg-white/20"/>
              <div>
                <div className="text-2xl font-bold text-white">100+</div>
                <div className="text-sm text-blue-100/70">{t('login.branding.countries')}</div>
              </div>
          </div>
          </div>
        </div>

        {/* ═══ Right Panel - Login Form ═══ */}
        <div className="flex-1 flex items-center justify-center p-6 sm:p-8 lg:p-12">
          <div className="w-full max-w-md">
            {/* Mobile Logo */}
            <div className="lg:hidden flex items-center gap-3 mb-8">
              <div
                  className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-200/50 dark:shadow-blue-900/30">
                <BookOpen className="w-5 h-5 text-white"/>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">FastBlog</span>
            </div>

            {/* Header */}
            <div className="mb-8">
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                {fa ? `🔐 ${t('login.twoFactorTitle')}` : mode === 'qrcode' ? `📱 ${t('login.qrLogin')}` : `👋 ${t('login.title')}`}
              </h1>
              <p className="text-gray-500 dark:text-gray-400">
                {fa ? t('login.twoFactorSubtitle') : mode === 'qrcode' ? t('login.scanQRCode') : t('login.subtitle')}
              </p>
            </div>

            {/* Error Message */}
            {err && (
                <div
                    className="mb-6 flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200/60 dark:border-red-800/40 rounded-2xl text-sm">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"/>
                  <span className="text-red-600 dark:text-red-400">{err}</span>
                </div>
            )}

            {/* 2FA Form */}
            {fa ? (
              <FormProvider {...twoFAForm}>
                <div className="space-y-6">
                  <div
                      className="text-center p-6 bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-2xl border border-indigo-100 dark:border-indigo-800/30">
                    <div
                        className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg">
                      <Smartphone className="w-8 h-8 text-white"/>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {backup ? t('login.twoFactorBackupHint') : t('login.twoFactorCodeHint')}
                    </p>
                  </div>

                  <form onSubmit={twoFAForm.handleSubmit(on2FASubmit)} className="space-y-4">
                    <Controller
                      name="code"
                      control={twoFAForm.control}
                      render={({field}) => (
                        <div className="relative">
                          <input
                            type="text"
                            inputMode="numeric"
                            autoFocus
                            value={field.value}
                            onChange={e => field.onChange(e.target.value.replace(/\D/g, '').slice(0, backup ? 8 : 6))}
                            placeholder={backup ? t('login.twoFactorPlaceholder') : '000000'}
                            className="w-full text-center text-3xl tracking-[0.5em] px-6 py-5 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-2xl focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 dark:text-white font-mono transition-all"
                          />
                          {twoFAForm.formState.errors.code && (
                            <p className="text-xs text-red-500 dark:text-red-400 text-center mt-2">
                              {twoFAForm.formState.errors.code.message}
                            </p>
                          )}
                        </div>
                      )}
                    />

                    <button
                        type="submit"
                        disabled={busy}
                        className="w-full py-4 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-semibold rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 active:scale-[0.98]"
                    >
                      {busy ? (
                          <span className="flex items-center justify-center gap-2">
                      <Loader className="w-5 h-5 animate-spin"/> {t('login.twoFactorVerifying')}
                    </span>
                      ) : t('login.verifyButton')}
                    </button>

                    <div className="flex items-center justify-between pt-2">
                      <button type="button" onClick={() => {
                        setBackup(!backup);
                        twoFAForm.reset({code: ''});
                      }}
                              className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-medium">
                        {backup ? t('login.twoFactorUseCode') : t('login.twoFactorUseBackup')}
                      </button>
                      <button type="button" onClick={() => {
                        setFa(null);
                        twoFAForm.reset({code: ''});
                        setErr('');
                      }}
                              className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                        <ArrowLeft className="w-4 h-4"/> {t('login.backToLogin')}
                      </button>
                    </div>
                  </form>
                </div>
              </FormProvider>
            ) : (
                <>
                  {/* Mode Switch */}
                  <div className="flex p-1.5 bg-gray-100 dark:bg-gray-800 rounded-2xl mb-6">
                    <button
                        onClick={() => {
                          setMode('password');
                          setErr('');
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                            mode === 'password'
                                ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
                              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                        }`}
                    >
                      <Lock className="w-4 h-4"/> {t('login.passwordLogin')}
                    </button>
                    <button
                        onClick={() => {
                          setMode('qrcode');
                          setErr('');
                          if (!qrImg) generateQR();
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                            mode === 'qrcode'
                                ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
                              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                        }`}
                    >
                      <QrCode className="w-4 h-4"/> {t('login.qrLogin')}
                    </button>
                  </div>

                  {/* Password Form */}
                  {mode === 'password' && (
                    <FormProvider {...loginForm}>
                      <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-5">
                        {/* Username Field */}
                        <div className="space-y-2">
                          <label
                            className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('login.usernameOrEmail')}</label>
                          <div
                              className={`relative group transition-all duration-200 ${focusedField === 'username' ? 'scale-[1.01]' : ''}`}>
                            <div className="absolute left-4 top-1/2 -translate-y-1/2">
                              <User
                                  className={`w-5 h-5 transition-colors ${focusedField === 'username' ? 'text-blue-500' : 'text-gray-400'}`}/>
                            </div>
                            <input
                                type="text"
                                {...loginForm.register('username')}
                                onFocus={() => setFocusedField('username')}
                                onBlur={() => setFocusedField(null)}
                                placeholder={t('login.usernameOrEmailPlaceholder')}
                                autoFocus
                                className={`w-full pl-12 pr-4 py-4 bg-white dark:bg-gray-800 border-2 rounded-2xl text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all ${
                                  loginForm.formState.errors.username
                                    ? 'border-red-400 dark:border-red-500'
                                    : 'border-gray-200 dark:border-gray-700'
                                }`}
                            />
                          </div>
                          {loginForm.formState.errors.username && (
                            <p className="text-xs text-red-500 dark:text-red-400 flex items-center gap-1 pl-1">
                              <AlertCircle className="w-3 h-3 flex-shrink-0"/>
                              {loginForm.formState.errors.username.message}
                            </p>
                          )}
                        </div>

                        {/* Password Field */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label
                              className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('login.password')}</label>
                            <a href="/forgot-password"
                               className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 font-medium">
                              {t('login.forgotPassword')}
                            </a>
                          </div>
                          <div
                              className={`relative group transition-all duration-200 ${focusedField === 'password' ? 'scale-[1.01]' : ''}`}>
                            <div className="absolute left-4 top-1/2 -translate-y-1/2">
                              <Lock
                                  className={`w-5 h-5 transition-colors ${focusedField === 'password' ? 'text-blue-500' : 'text-gray-400'}`}/>
                            </div>
                            <input
                                type={pv ? 'text' : 'password'}
                                {...loginForm.register('password')}
                                onFocus={() => setFocusedField('password')}
                                onBlur={() => setFocusedField(null)}
                                placeholder={t('login.passwordPlaceholder')}
                                className={`w-full pl-12 pr-12 py-4 bg-white dark:bg-gray-800 border-2 rounded-2xl text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all ${
                                  loginForm.formState.errors.password
                                    ? 'border-red-400 dark:border-red-500'
                                    : 'border-gray-200 dark:border-gray-700'
                                }`}
                            />
                            <button
                                type="button"
                                onClick={() => setPv(!pv)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                            >
                              {pv ? <EyeOff className="w-5 h-5"/> : <Eye className="w-5 h-5"/>}
                            </button>
                          </div>
                          {loginForm.formState.errors.password && (
                            <p className="text-xs text-red-500 dark:text-red-400 flex items-center gap-1 pl-1">
                              <AlertCircle className="w-3 h-3 flex-shrink-0"/>
                              {loginForm.formState.errors.password.message}
                            </p>
                          )}
                        </div>

                        {/* Remember Me */}
                        <label className="flex items-center gap-3 cursor-pointer group">
                          <div className="relative">
                            <input
                                type="checkbox"
                                {...loginForm.register('remember')}
                                className="peer sr-only"
                            />
                            <div
                                className="w-5 h-5 border-2 border-gray-300 dark:border-gray-600 rounded-lg peer-checked:border-blue-500 peer-checked:bg-blue-500 transition-all flex items-center justify-center">
                              {loginForm.watch('remember') && (
                                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24"
                                       stroke="currentColor" strokeWidth={3}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                                  </svg>
                              )}
                            </div>
                          </div>
                          <span
                              className="text-sm text-gray-600 dark:text-gray-400 group-hover:text-gray-800 dark:group-hover:text-gray-200 transition-colors">
                      {t('login.rememberMeStatus')}
                    </span>
                        </label>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={busy}
                            className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 active:scale-[0.98] flex items-center justify-center gap-2"
                        >
                          {busy ? (
                              <>
                                <Loader className="w-5 h-5 animate-spin"/>
                                <span>{t('login.loggingIn')}</span>
                              </>
                          ) : (
                              <>
                                <span>{t('login.loginButton')}</span>
                                <ChevronRight className="w-5 h-5"/>
                              </>
                          )}
                        </button>

                        {/* Divider */}
                        <div className="relative flex items-center py-2">
                          <div className="flex-1 border-t border-gray-200 dark:border-gray-700"/>
                          <span
                            className="px-4 text-xs text-gray-400 dark:text-gray-500 font-medium">{t('login.orOtherMethods')}</span>
                          <div className="flex-1 border-t border-gray-200 dark:border-gray-700"/>
                        </div>

                        {/* Social Login */}
                        <div className="grid grid-cols-2 gap-3">
                          <button
                              type="button"
                              className="flex items-center justify-center gap-2 py-3.5 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-2xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-750 hover:border-gray-300 dark:hover:border-gray-600 transition-all active:scale-[0.98]"
                          >
                            <GitBranch className="w-5 h-5"/> GitHub
                          </button>
                          <button
                              type="button"
                              className="flex items-center justify-center gap-2 py-3.5 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-2xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-750 hover:border-gray-300 dark:hover:border-gray-600 transition-all active:scale-[0.98]"
                          >
                            <Globe className="w-5 h-5"/> Google
                          </button>
                        </div>

                        {/* Register Link */}
                        <p className="text-center text-sm text-gray-500 dark:text-gray-400 pt-2">
                          {t('login.noAccount')}{' '}
                          <a href="/register"
                             className="text-blue-600 hover:text-blue-700 dark:text-blue-400 font-semibold hover:underline">
                            {t('login.registerNow')}
                          </a>
                        </p>
                      </form>
                    </FormProvider>
                  )}

                  {/* QR Code Panel */}
                  {mode === 'qrcode' && (
                      <div className="space-y-6">
                        <div
                            className="bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-100 dark:border-gray-700 shadow-sm">
                          <div className="text-center space-y-5">
                            {/* QR Display */}
                            <div className="flex justify-center">
                              {qrStatus === 'loading' ? (
                                  <div
                                      className="w-[220px] h-[220px] bg-gray-50 dark:bg-gray-900 rounded-2xl animate-pulse flex items-center justify-center">
                                    <div className="flex flex-col items-center gap-3">
                                      <Loader className="w-8 h-8 animate-spin text-blue-500"/>
                                      <span className="text-sm text-gray-400">{t('login.qrGenerating')}</span>
                                    </div>
                                  </div>
                              ) : qrImg ? (
                                  <div className="relative p-4 bg-white rounded-2xl border-2 border-gray-100 shadow-lg">
                                    <img src={qrImg} alt="Login QR Code" className="w-[200px] h-[200px]"/>
                                    {qrStatus === 'success' && (
                                        <div
                                            className="absolute inset-0 bg-green-500/90 rounded-2xl flex items-center justify-center">
                                          <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24"
                                               stroke="currentColor" strokeWidth={2.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                                          </svg>
                                        </div>
                                    )}
                                    {qrStatus === 'expired' && (
                                      <div
                                        className="absolute inset-0 bg-orange-500/85 rounded-2xl flex flex-col items-center justify-center gap-2">
                                        <svg className="w-14 h-14 text-white" fill="none" viewBox="0 0 24 24"
                                             stroke="currentColor" strokeWidth={2}>
                                          <circle cx="12" cy="12" r="10"/>
                                          <polyline points="12 6 12 12 16 14"/>
                                        </svg>
                                        <span
                                          className="text-white text-sm font-medium">{t('login.qrExpiredAutoRefresh')}</span>
                                      </div>
                                    )}
                                  </div>
                              ) : (
                                  <div
                                      className="w-[220px] h-[220px] bg-gray-50 dark:bg-gray-900 rounded-2xl border-2 border-dashed border-gray-200 dark:border-gray-700 flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
                                      onClick={generateQR}>
                                    <QrCode className="w-10 h-10 text-gray-300 dark:text-gray-600"/>
                                    <span className="text-sm text-gray-400">{t('login.qrClickToGenerate')}</span>
                                  </div>
                              )}
                            </div>

                            {/* Status Text */}
                            <div className="space-y-2">
                              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                {qrStatus === 'loading' ? t('login.generatingQR') :
                                    qrStatus === 'ready' || qrStatus === 'pending' ? (
                                        <span className="flex flex-col items-center gap-1">
                                          <span className="flex items-center justify-center gap-2">
                                            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"/>
                                            {t('login.qrWaitingScan')}
                                          </span>
                                          {countdown > 0 && (
                                            <span
                                              className={`text-xs ${countdown <= 30 ? 'text-orange-500 font-semibold' : 'text-gray-400 dark:text-gray-500'}`}>
                                              {t('login.qrExpiresIn', {seconds: countdown})}
                                            </span>
                                          )}
                                        </span>
                                      ) :
                                      qrStatus === 'success' ? `✅ ${t('login.qrScanSuccess')}` :
                                        qrStatus === 'expired' ? t('login.qrExpiredAutoRefresh') :
                                          t('login.scanQRCode')}
                              </p>
                            </div>

                            {/* Action Buttons */}
                            {(qrStatus === 'expired' || qrStatus === 'idle') && (
                                <button
                                    onClick={generateQR}
                                    className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-sm font-semibold rounded-xl transition-all shadow-md hover:shadow-lg active:scale-[0.98]"
                                >
                                  {qrStatus === 'expired' ? t('login.qrRegenerate') : t('login.qrGenerate')}
                                </button>
                            )}
                          </div>
                        </div>

                        {/* Instructions */}
                        <div
                            className="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-5 border border-gray-100 dark:border-gray-800">
                          <h3
                            className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">{t('login.scanSteps')}</h3>
                          <ol className="space-y-2.5">
                            {[t('login.scanStep1'), t('login.scanStep2'), t('login.scanStep3'), t('login.scanStep4')].map((step, i) => (
                                <li key={i}
                                    className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                          <span
                              className="w-6 h-6 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                            {i + 1}
                          </span>
                                  {step}
                                </li>
                            ))}
                          </ol>
                        </div>
                      </div>
                  )}
                </>
            )}

            {/* Footer */}
            <div className="mt-8 text-center">
              <p className="text-xs text-gray-400 dark:text-gray-500">
                {t('login.agreeToTerms')}{' '}
                <a href="/terms"
                   className="text-gray-500 dark:text-gray-400 hover:underline">{t('login.termsOfService')}</a>
                {' '}{t('common.and') || '和'}{' '}
                <a href="/privacy"
                   className="text-gray-500 dark:text-gray-400 hover:underline">{t('login.privacyPolicy')}</a>
              </p>
            </div>
          </div>
      </div>
    </div>
  );
}
