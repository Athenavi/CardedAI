'use client';

import React, {useState} from 'react';
import {FormProvider, useForm} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {apiClient} from '@/lib/api/base-client';
import {type RegisterFormData, registerSchema} from '@/lib/schemas';
import {useTranslation} from '@/lib/i18n';
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  Eye,
  EyeOff,
  Globe,
  Loader,
  Lock,
  Mail,
  Sparkles,
  User
} from 'lucide-react';

const passwordStrength = (pw: string): { level: number; labelKey: string; color: string } => {
    let score = 0;
    if (pw.length >= 8) score++;
    if (pw.length >= 12) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (score <= 1) return {level: 1, labelKey: 'register.passwordStrength.weak', color: 'bg-red-500'};
  if (score <= 2) return {level: 2, labelKey: 'register.passwordStrength.fair', color: 'bg-orange-500'};
  if (score <= 3) return {level: 3, labelKey: 'register.passwordStrength.good', color: 'bg-yellow-500'};
  if (score <= 4) return {level: 4, labelKey: 'register.passwordStrength.strong', color: 'bg-green-500'};
  return {level: 5, labelKey: 'register.passwordStrength.veryStrong', color: 'bg-emerald-500'};
};

export default function RegisterPage() {
  const {t} = useTranslation();
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [pv, setPv] = useState(false);
  const [uOk, setUOk] = useState<boolean|null>(null);
  const [eOk, setEOk] = useState<boolean|null>(null);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const benefits = [
    {
      icon: '✍️',
      titleKey: 'register.branding.benefits.aiAssisted',
      descKey: 'register.branding.benefits.aiAssistedDesc'
    },
    {
      icon: '🌍',
      titleKey: 'register.branding.benefits.globalPublish',
      descKey: 'register.branding.benefits.globalPublishDesc'
    },
    {
      icon: '📊',
      titleKey: 'register.branding.benefits.dataAnalytics',
      descKey: 'register.branding.benefits.dataAnalyticsDesc'
    },
    {
      icon: '💰',
      titleKey: 'register.branding.benefits.contentMonetization',
      descKey: 'register.branding.benefits.contentMonetizationDesc'
    },
  ];

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema) as any,
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      locale: 'zh_CN',
      terms: false as unknown as true
    },
    mode: 'onBlur',
  });
  const {register, handleSubmit, watch, setValue, trigger, getValues, formState: {errors}} = form;

  const watchedPassword = watch('password');
  const watchedConfirm = watch('confirmPassword');
  const strength = passwordStrength(watchedPassword || '');

  const stepLabels = [t('register.step1'), t('register.step2'), t('register.step3')];

  const checkU = async () => {
    const username = getValues('username');
    if ((username || '').length < 3) {
      setUOk(false);
      return;
    }
    try {
      const r = await apiClient.get(`/auth/check-username?username=${username}`);
      setUOk(!(r as any).exists);
    }
    catch { setUOk(false); }
  };
  const checkE = async () => {
    const email = getValues('email');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email || '')) {
      setEOk(false);
      return;
    }
    try {
      const r = await apiClient.get(`/auth/check-email?email=${email}`);
      setEOk(!(r as any).exists);
    }
    catch { setEOk(false); }
  };

  const next = async () => {
    if (step === 0) {
      setErr('');
      const valid = await trigger(['username', 'email']);
      if (!valid) return;
      await checkU();
      await checkE();
      const uVal = getValues('username');
      if ((uVal || '').length < 3) {
        setErr(t('register.usernameMinChars'));
        return;
      }
      setStep(1);
      return;
    }
    if (step === 1) {
      const valid = await trigger(['password', 'confirmPassword']);
      if (!valid) {
        setErr(t('register.checkPassword'));
        return;
      }
      setErr('');
      setStep(2);
    }
  };

  const onSubmit = async (data: RegisterFormData) => {
    setBusy(true); setErr('');
    try {
      const r = await apiClient.postForm('/auth/register', {
        username: data.username,
        email: data.email,
        password: data.password
      });
      if (r?.success) {
        const d = r.data as any;
        if (d?.access_token) {
          document.cookie = `access_token=${d.access_token}; path=/; max-age=3600; SameSite=Lax`;
          window.location.href = '/profile';
        } else window.location.href = '/login?registered=true';
      } else setErr(r?.error || r?.message || t('register.registerFailed'));
    } catch {
      setErr(t('register.networkError'));
    } finally {
      setBusy(false);
    }
  };

  const headerTitles = [t('register.step0Title'), t('register.step1Title'), t('register.step2Title')];
  const headerSubtitles = [t('register.step0Subtitle'), t('register.step1Subtitle'), t('register.step2Subtitle')];

  return (
      <div
        className="min-h-screen flex bg-background">
          {/* ═══ Left Panel - Branding ═══ */}
          <div className="hidden lg:flex lg:w-1/2 xl:w-[45%] relative overflow-hidden">
            <div className="absolute inset-0 bg-primary"/>

              <div className="relative z-10 flex flex-col justify-between p-12 xl:p-16 w-full">
                  {/* Logo */}
                  <div>
                      <div className="flex items-center gap-3 mb-2">
                          <div
                            className="flex h-10 w-10 items-center justify-center rounded-md border border-white/25">
                              <BookOpen className="w-5 h-5 text-white"/>
                          </div>
                          <span className="text-xl font-bold text-white">Carded AI</span>
                      </div>
                  </div>

                  {/* Main Content */}
                  <div className="space-y-8">
            <div>
              <h2 className="editorial-title mb-4 text-3xl leading-tight text-white xl:text-4xl"
                  dangerouslySetInnerHTML={{__html: t('register.branding.tagline').replace(/\n/g, '<br/>')}}/>
              <p className="max-w-md text-lg leading-relaxed text-white/75">
                  {t('register.branding.description')}
                </p>
            </div>

                      {/* Benefits */}
                      <div className="grid grid-cols-2 gap-4">
                          {benefits.map((b, i) => (
                              <div key={i}
                                   className="group rounded-md border border-white/15 p-4 transition-colors hover:border-white/30">
                                  <span className="text-2xl block mb-2">{b.icon}</span>
                                <h3 className="text-sm font-semibold text-white mb-1">{t(b.titleKey)}</h3>
                                <p className="text-xs leading-relaxed text-white/70">{t(b.descKey)}</p>
                              </div>
                          ))}
                      </div>
                  </div>

                  {/* Testimonial */}
                <div className="rounded-md border border-white/15 p-5">
                      <p className="text-white/90 text-sm italic mb-3">
                        "{t('register.branding.testimonial.quote')}"
                      </p>
                      <div className="flex items-center gap-3">
                          <div
                            className="flex h-8 w-8 items-center justify-center rounded-sm border border-white/25 text-xs font-semibold text-white">
                            {t('register.branding.testimonial.author').charAt(0)}
                          </div>
                          <div>
                            <p
                              className="text-sm font-medium text-white">{t('register.branding.testimonial.author')}</p>
                            <p className="text-xs text-primary/60">{t('register.branding.testimonial.role')}</p>
                          </div>
                      </div>
                  </div>
              </div>
          </div>

          {/* ═══ Right Panel - Registration Form ═══ */}
          <div className="flex-1 flex items-center justify-center p-6 sm:p-8 lg:p-12">
              <div className="w-full max-w-md">
                  {/* Mobile Logo */}
                  <div className="lg:hidden flex items-center gap-3 mb-8">
                      <div
                        className="w-10 h-10 bg-primary rounded-md flex items-center justify-center shadow-lg">
                          <BookOpen className="w-5 h-5 text-white"/>
            </div>
                      <span className="text-xl font-bold text-gray-900 dark:text-white">Carded AI</span>
                  </div>

                  {/* Header */}
                  <div className="mb-8">
                      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        {headerTitles[step]}
                      </h1>
                      <p className="text-gray-500 dark:text-gray-400">
                        {headerSubtitles[step]}
                      </p>
                  </div>

                  {/* Steps Indicator */}
                  <div className="flex items-center gap-2 mb-8">
                      {stepLabels.map((label, i) => (
                          <React.Fragment key={i}>
                              <div className="flex items-center gap-2">
                                  <div
                                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                                          i < step ? 'bg-green-500 text-white' :
                                            i === step ? 'bg-primary text-white shadow-md' :
                                                  'bg-gray-200 dark:bg-gray-700 text-gray-400'
                                      }`}>
                                      {i < step ? <Check className="w-4 h-4"/> : i + 1}
                                  </div>
                                  <span className={`text-xs font-medium hidden sm:block ${
                                      i <= step ? 'text-gray-700 dark:text-gray-300' : 'text-gray-400'
                                  }`}>{label}</span>
                              </div>
                              {i < stepLabels.length - 1 && (
                                  <div
                                      className={`flex-1 h-0.5 rounded-full transition-all ${i < step ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'}`}/>
                              )}
                          </React.Fragment>
                      ))}
                  </div>

                  {/* Error */}
                  {err && (
                      <div
                        className="mb-6 flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200/60 dark:border-red-800/40 rounded-lg text-sm">
                          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"/>
                          <span className="text-red-600 dark:text-red-400">{err}</span>
                      </div>
                  )}

                  <div
                    className="bg-card rounded-lg p-6 sm:p-8 shadow-sm border border-gray-100 dark:border-gray-700">
                      {/* Step 0: Basic Info */}
                      {step === 0 && (
                        <FormProvider {...form}>
                          <div className="space-y-5">
                              {/* Username */}
                              <div className="space-y-2">
                                <label
                                  className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('register.username')}</label>
                                  <div
                                      className={`relative transition-all duration-200 ${focusedField === 'username' ? 'scale-[1.01]' : ''}`}>
                                      <div className="absolute left-4 top-1/2 -translate-y-1/2">
                                          <User
                                            className={`w-5 h-5 transition-colors ${focusedField === 'username' ? 'text-primary' : 'text-gray-400'}`}/>
                                      </div>
                                      <input
                                          type="text"
                                          {...register('username')}
                                          onChange={(e) => {
                                            register('username').onChange(e);
                                              setUOk(null);
                                              setErr('');
                                          }}
                                          onFocus={() => setFocusedField('username')}
                                          onBlur={(e) => {
                                            register('username').onBlur(e);
                                              setFocusedField(null);
                                              checkU();
                                          }}
                                          placeholder={t('register.usernamePlaceholder')}
                                          autoFocus
                                          className={`w-full pl-12 pr-12 py-4 bg-gray-50 dark:bg-gray-900 border-2 rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all ${errors.username ? 'border-red-400 focus:border-red-500' : 'border-gray-200 dark:border-gray-600 focus:border-primary'}`}
                                      />
                                      <div className="absolute right-4 top-1/2 -translate-y-1/2">
                                          {uOk === true && <CheckCircle2 className="w-5 h-5 text-green-500"/>}
                                          {uOk === false && <AlertCircle className="w-5 h-5 text-red-500"/>}
                                      </div>
                                  </div>
                                {errors.username && <p className="text-xs text-red-500">{errors.username.message}</p>}
                                {uOk !== null && !errors.username && (
                                      <p className={`text-xs flex items-center gap-1 ${uOk ? 'text-green-600 dark:text-green-400' : 'text-red-500'}`}>
                                        {uOk ? t('register.usernameAvailable') : t('register.usernameUnavailable')}
                                      </p>
                                  )}
                              </div>

                              {/* Email */}
                              <div className="space-y-2">
                                  <label
                                    className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('register.email')}</label>
                                  <div
                                      className={`relative transition-all duration-200 ${focusedField === 'email' ? 'scale-[1.01]' : ''}`}>
                                      <div className="absolute left-4 top-1/2 -translate-y-1/2">
                                          <Mail
                                            className={`w-5 h-5 transition-colors ${focusedField === 'email' ? 'text-primary' : 'text-gray-400'}`}/>
                                      </div>
                                      <input
                                          type="email"
                                          {...register('email')}
                                          onChange={(e) => {
                                            register('email').onChange(e);
                                              setEOk(null);
                                              setErr('');
                                          }}
                                          onFocus={() => setFocusedField('email')}
                                          onBlur={(e) => {
                                            register('email').onBlur(e);
                                              setFocusedField(null);
                                              checkE();
                                          }}
                                          placeholder={t('register.emailPlaceholder')}
                                          className={`w-full pl-12 pr-12 py-4 bg-gray-50 dark:bg-gray-900 border-2 rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all ${errors.email ? 'border-red-400 focus:border-red-500' : 'border-gray-200 dark:border-gray-600 focus:border-primary'}`}
                                      />
                                      <div className="absolute right-4 top-1/2 -translate-y-1/2">
                                          {eOk === true && <CheckCircle2 className="w-5 h-5 text-green-500"/>}
                                          {eOk === false && <AlertCircle className="w-5 h-5 text-red-500"/>}
                                      </div>
                                  </div>
                                {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
                                {eOk !== null && !errors.email && (
                                      <p className={`text-xs flex items-center gap-1 ${eOk ? 'text-green-600 dark:text-green-400' : 'text-red-500'}`}>
                                        {eOk ? t('register.emailAvailable') : t('register.emailUnavailable')}
                                      </p>
                                  )}
                              </div>

                              <button
                                  type="button"
                                  onClick={next}
                                  className="w-full py-4 bg-primary text-white font-semibold rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary hover:shadow-sm active:scale-[0.98] flex items-center justify-center gap-2"
                              >
                                {t('register.nextStep')} <ArrowRight className="w-5 h-5"/>
                              </button>
                          </div>
                        </FormProvider>
                      )}

                      {/* Step 1: Password */}
                    {step === 1 && (
                      <FormProvider {...form}>
                        <div className="space-y-5">
                          {/* Password */}
                          <div className="space-y-2">
                            <label
                              className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('register.password')}</label>
                            <div
                              className={`relative transition-all duration-200 ${focusedField === 'password' ? 'scale-[1.01]' : ''}`}>
                              <div className="absolute left-4 top-1/2 -translate-y-1/2">
                                <Lock
                                  className={`w-5 h-5 transition-colors ${focusedField === 'password' ? 'text-primary' : 'text-gray-400'}`}/>
                              </div>
                              <input
                                type={pv ? 'text' : 'password'}
                                {...register('password')}
                                onChange={(e) => {
                                  register('password').onChange(e);
                                  setErr('');
                                }}
                                onFocus={() => setFocusedField('password')}
                                onBlur={(e) => {
                                  register('password').onBlur(e);
                                  setFocusedField(null);
                                }}
                                placeholder={t('register.passwordPlaceholder')}
                                autoFocus
                                className={`w-full pl-12 pr-12 py-4 bg-gray-50 dark:bg-gray-900 border-2 rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all ${errors.password ? 'border-red-400 focus:border-red-500' : 'border-gray-200 dark:border-gray-600 focus:border-primary'}`}
                              />
                              <button type="button" onClick={() => setPv(!pv)}
                                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                                {pv ? <EyeOff className="w-5 h-5"/> : <Eye className="w-5 h-5"/>}
                              </button>
                            </div>
                            {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
                            {/* Password Strength */}
                            {watchedPassword && (
                              <div className="space-y-1.5">
                                <div className="flex gap-1">
                                  {[1, 2, 3, 4, 5].map(i => (
                                    <div key={i}
                                         className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${i <= strength.level ? strength.color : 'bg-gray-200 dark:bg-gray-700'}`}/>
                                  ))}
                                </div>
                                <p
                                  className="text-xs text-gray-500 dark:text-gray-400">{t('register.passwordStrengthLabel')}
                                  <span
                                    className="font-medium">{t(strength.labelKey)}</span></p>
                              </div>
                            )}
                          </div>

                          {/* Confirm Password */}
                          <div className="space-y-2">
                            <label
                              className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('register.confirmPassword')}</label>
                            <div
                              className={`relative transition-all duration-200 ${focusedField === 'confirm' ? 'scale-[1.01]' : ''}`}>
                              <div className="absolute left-4 top-1/2 -translate-y-1/2">
                                <Lock
                                  className={`w-5 h-5 transition-colors ${focusedField === 'confirm' ? 'text-primary' : 'text-gray-400'}`}/>
                              </div>
                              <input
                                type="password"
                                {...register('confirmPassword')}
                                onChange={(e) => {
                                  register('confirmPassword').onChange(e);
                                  setErr('');
                                }}
                                onFocus={() => setFocusedField('confirm')}
                                onBlur={(e) => {
                                  register('confirmPassword').onBlur(e);
                                  setFocusedField(null);
                                }}
                                placeholder={t('register.confirmPasswordPlaceholder')}
                                className={`w-full pl-12 pr-12 py-4 bg-gray-50 dark:bg-gray-900 border-2 rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all ${errors.confirmPassword ? 'border-red-400 focus:border-red-500' : 'border-gray-200 dark:border-gray-600 focus:border-primary'}`}
                              />
                              {watchedConfirm && (
                                <div className="absolute right-4 top-1/2 -translate-y-1/2">
                                  {watchedPassword === watchedConfirm ?
                                    <CheckCircle2 className="w-5 h-5 text-green-500"/> :
                                    <AlertCircle className="w-5 h-5 text-red-500"/>}
                                </div>
                              )}
                            </div>
                            {errors.confirmPassword &&
                              <p className="text-xs text-red-500">{errors.confirmPassword.message}</p>}
                          </div>

                          {/* Password Requirements */}
                          <div
                            className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-700">
                            <p
                              className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">{t('register.passwordRequirements.title')}</p>
                            <div className="grid grid-cols-2 gap-1.5">
                              {[
                                {
                                  met: (watchedPassword || '').length >= 8,
                                  textKey: 'register.passwordRequirements.length'
                                },
                                {
                                  met: /[A-Z]/.test(watchedPassword || ''),
                                  textKey: 'register.passwordRequirements.uppercase'
                                },
                                {
                                  met: /[0-9]/.test(watchedPassword || ''),
                                  textKey: 'register.passwordRequirements.number'
                                },
                                {
                                  met: /[^A-Za-z0-9]/.test(watchedPassword || ''),
                                  textKey: 'register.passwordRequirements.special'
                                },
                              ].map((req, i) => (
                                <div key={i}
                                     className={`flex items-center gap-1.5 text-xs ${req.met ? 'text-green-600 dark:text-green-400' : 'text-gray-400'}`}>
                                  {req.met ? <Check className="w-3.5 h-3.5"/> : <div
                                    className="w-3.5 h-3.5 rounded-full border border-gray-300 dark:border-gray-600"/>}
                                  {t(req.textKey)}
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="flex gap-3">
                            <button type="button" onClick={() => {
                              setStep(0);
                              setErr('');
                            }}
                                    className="flex-1 py-4 border-2 border-gray-200 dark:border-gray-600 rounded-lg text-sm font-semibold hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors flex items-center justify-center gap-2 text-gray-700 dark:text-gray-300">
                              <ArrowLeft className="w-4 h-4"/> {t('register.prevStep')}
                            </button>
                            <button
                              type="button"
                              onClick={next}
                              className="flex-1 py-4 bg-primary text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary active:scale-[0.98] flex items-center justify-center gap-2"
                            >
                              {t('register.nextStep')} <ArrowRight className="w-4 h-4"/>
                            </button>
                          </div>
                        </div>
                      </FormProvider>
                    )}

                      {/* Step 2: Confirm & Terms */}
                    {step === 2 && (
                      <FormProvider {...form}>
                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                          {/* Summary */}
                          <div
                            className="p-5 bg-secondary rounded-lg border border-primary dark:border-primary/30">
                            <h3
                              className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                              <CheckCircle2 className="w-4 h-4 text-green-500"/> {t('register.confirmInfo.title')}
                            </h3>
                            <div className="space-y-2">
                              <div className="flex items-center gap-3 text-sm">
                                <User className="w-4 h-4 text-gray-400"/>
                                <span
                                  className="text-gray-500 dark:text-gray-400">{t('register.confirmInfo.username')}</span>
                                <span
                                  className="font-medium text-gray-900 dark:text-white">{watch('username')}</span>
                              </div>
                              <div className="flex items-center gap-3 text-sm">
                                <Mail className="w-4 h-4 text-gray-400"/>
                                <span
                                  className="text-gray-500 dark:text-gray-400">{t('register.confirmInfo.email')}</span>
                                <span className="font-medium text-gray-900 dark:text-white">{watch('email')}</span>
                              </div>
                              <div className="flex items-center gap-3 text-sm">
                                <Lock className="w-4 h-4 text-gray-400"/>
                                <span
                                  className="text-gray-500 dark:text-gray-400">{t('register.confirmInfo.password')}</span>
                                <span
                                  className="font-medium text-gray-900 dark:text-white">{'•'.repeat((watchedPassword || '').length)}</span>
                              </div>
                            </div>
                          </div>

                          {/* Language */}
                          <div className="space-y-2">
                            <label
                              className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                              <Globe className="w-4 h-4"/> {t('register.locale')}
                            </label>
                            <select
                              {...register('locale')}
                              className="w-full px-4 py-3.5 bg-gray-50 dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all"
                            >
                              <option value="zh_CN">🇨🇳 简体中文</option>
                              <option value="en_US">🇺🇸 English</option>
                            </select>
                          </div>

                          {/* Terms */}
                          <label
                            className="flex items-start gap-3 cursor-pointer group p-4 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-700 hover:border-primary dark:hover:border-primary transition-colors">
                            <div className="relative mt-0.5">
                              <input type="checkbox" {...register('terms')} className="peer sr-only"/>
                              <div
                                className="w-5 h-5 border-2 border-gray-300 dark:border-gray-600 rounded-lg peer-checked:border-primary peer-checked:bg-primary transition-all flex items-center justify-center">
                                {watch('terms') &&
                                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24"
                                       stroke="currentColor" strokeWidth={3}>
                                    <path strokeLinecap="round" strokeLinejoin="round"
                                          d="M5 13l4 4L19 7"/>
                                  </svg>}
                              </div>
                            </div>
                            <span className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                     {t('register.agreeTerms')}{' '}
                              <a href="/terms"
                                 className="text-primary hover:underline dark:text-primary font-medium">{t('register.termsOfService')}</a>
                              {' '}{t('common.and')}{' '}
                              <a href="/privacy"
                                 className="text-primary hover:underline dark:text-primary font-medium">{t('register.privacyPolicy')}</a>
                   </span>
                          </label>
                          {errors.terms && <p className="text-xs text-red-500">{errors.terms.message}</p>}

                          <div className="flex gap-3">
                            <button type="button" onClick={() => {
                              setStep(1);
                              setErr('');
                            }}
                                    className="flex-1 py-4 border-2 border-gray-200 dark:border-gray-600 rounded-lg text-sm font-semibold hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors flex items-center justify-center gap-2 text-gray-700 dark:text-gray-300">
                              <ArrowLeft className="w-4 h-4"/> {t('register.prevStep')}
                            </button>
                            <button
                              type="submit"
                              disabled={busy || !watch('terms')}
                              className="flex-1 py-4 bg-primary text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-500/25 hover:shadow-sm active:scale-[0.98] flex items-center justify-center gap-2"
                            >
                              {busy ? (
                                <><Loader className="w-5 h-5 animate-spin"/> {t('register.creating')}</>
                              ) : (
                                <><Sparkles className="w-5 h-5"/> {t('register.createAccount')}</>
                              )}
                            </button>
                          </div>
                        </form>
                      </FormProvider>
                    )}
                  </div>

                  {/* Login Link */}
                  <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6">
                    {t('register.hasAccount')}{' '}
                      <a href="/login"
                         className="text-primary hover:text-primary dark:text-primary font-semibold hover:underline">
                        {t('register.loginNow')}
                      </a>
                  </p>

                  {/* Footer */}
                  <div className="mt-6 text-center">
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      {t('register.footerAgreement')}
                      </p>
                  </div>
              </div>
      </div>
    </div>
  );
}
