'use client';

import React, {useState} from 'react';
import {Controller, FormProvider, useForm} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {apiClient} from '@/lib/api/base-client';
import {type RegisterFormData, registerSchema} from '@/lib/schemas';
import {useTranslation} from '@/lib/i18n';
import {cn} from '@/lib/utils';
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Eye,
  EyeOff,
  Globe,
  Loader,
  Lock,
  Mail,
  Sparkles,
  User,
  Wallet
} from 'lucide-react';
import AuthShell from '@/components/auth/AuthShell';
import AuthField from '@/components/auth/AuthField';
import {Button} from '@/components/ui/button';
import {Checkbox} from '@/components/ui/checkbox';

const passwordStrength = (pw: string): { level: number; labelKey: string; color: string } => {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (score <= 1) return {level: 1, labelKey: 'register.passwordStrength.weak', color: 'bg-destructive'};
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
  const [uOk, setUOk] = useState<boolean | null>(null);
  const [eOk, setEOk] = useState<boolean | null>(null);

  const benefits = [
    {
      icon: Sparkles,
      titleKey: 'register.branding.benefits.aiAssisted',
      descKey: 'register.branding.benefits.aiAssistedDesc'
    },
    {
      icon: Globe,
      titleKey: 'register.branding.benefits.globalPublish',
      descKey: 'register.branding.benefits.globalPublishDesc'
    },
    {
      icon: BarChart3,
      titleKey: 'register.branding.benefits.dataAnalytics',
      descKey: 'register.branding.benefits.dataAnalyticsDesc'
    },
    {
      icon: Wallet,
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
  const {register, handleSubmit, watch, trigger, getValues, formState: {errors}} = form;

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
    } catch {
      setUOk(false);
    }
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
    } catch {
      setEOk(false);
    }
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
    setBusy(true);
    setErr('');
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

  const availabilityText = (ok: boolean, okKey: string, badKey: string) => (
    <p className={cn('text-xs', ok ? 'text-primary' : 'text-destructive')}>
      {t(ok ? okKey : badKey)}
    </p>
  );

  return (
    <AuthShell
      tagline={t('register.branding.tagline')}
      title={headerTitles[step]}
      subtitle={headerSubtitles[step]}
      footnote={
        <div className="space-y-3">
          <p>
            {t('register.hasAccount')}{' '}
            <a href="/login"
               className="font-medium text-foreground underline decoration-border underline-offset-4 transition-colors hover:decoration-foreground">
              {t('register.loginNow')}
            </a>
          </p>
          <p className="text-xs text-muted-foreground/75">{t('register.footerAgreement')}</p>
        </div>
      }
      note={
        <div className="space-y-5">
          <blockquote>
            <p className="text-sm italic leading-relaxed text-muted-foreground">
              “{t('register.branding.testimonial.quote')}”
            </p>
            <footer className="mt-2.5 text-xs text-muted-foreground/80">
              {t('register.branding.testimonial.author')} · {t('register.branding.testimonial.role')}
            </footer>
          </blockquote>
          <p className="text-xs leading-relaxed text-muted-foreground/80">
            {benefits.map(b => t(b.titleKey)).join(' · ')}
          </p>
        </div>
      }
    >
      {/* 步骤指示器 —— 等宽序号 + 发丝线 */}
      <ol className="mb-9 flex items-center gap-4">
        {stepLabels.map((label, i) => (
          <React.Fragment key={i}>
            <li className={cn(
              'flex items-center gap-2 text-[11px] tracking-[0.16em] transition-colors',
              i <= step ? 'text-foreground' : 'text-muted-foreground/60',
            )}>
              <span className={cn('font-mono tabular-nums', i < step && 'text-primary')}>
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="hidden sm:inline">{label}</span>
            </li>
            {i < stepLabels.length - 1 && (
              <li aria-hidden="true"
                  className={cn('h-px flex-1 transition-colors', i < step ? 'bg-primary' : 'bg-border')}/>
            )}
          </React.Fragment>
        ))}
      </ol>

      {/* Error */}
      {err && (
        <div
          className="mb-8 flex items-start gap-3 border-l-2 border-destructive bg-destructive/[0.04] py-3 pl-4 pr-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0"/>
          <span>{err}</span>
        </div>
      )}

      <FormProvider {...form}>
        {/* Step 0: 账号信息 */}
        {step === 0 && (
          <div className="space-y-7">
            <AuthField
              label={t('register.username')}
              icon={User}
              autoFocus
              placeholder={t('register.usernamePlaceholder')}
              error={errors.username?.message}
              action={
                uOk === true ? <CheckCircle2 className="h-4 w-4 text-primary"/>
                  : uOk === false ? <AlertCircle className="h-4 w-4 text-destructive"/>
                    : undefined
              }
              description={uOk !== null && !errors.username
                ? availabilityText(uOk, 'register.usernameAvailable', 'register.usernameUnavailable')
                : undefined}
              {...register('username')}
              onChange={(e) => {
                register('username').onChange(e);
                setUOk(null);
                setErr('');
              }}
              onBlur={(e) => {
                register('username').onBlur(e);
                checkU();
              }}
            />

            <AuthField
              label={t('register.email')}
              icon={Mail}
              type="email"
              placeholder={t('register.emailPlaceholder')}
              error={errors.email?.message}
              action={
                eOk === true ? <CheckCircle2 className="h-4 w-4 text-primary"/>
                  : eOk === false ? <AlertCircle className="h-4 w-4 text-destructive"/>
                    : undefined
              }
              description={eOk !== null && !errors.email
                ? availabilityText(eOk, 'register.emailAvailable', 'register.emailUnavailable')
                : undefined}
              {...register('email')}
              onChange={(e) => {
                register('email').onChange(e);
                setEOk(null);
                setErr('');
              }}
              onBlur={(e) => {
                register('email').onBlur(e);
                checkE();
              }}
            />

            <Button type="button" onClick={next} className="h-12 w-full gap-2 rounded-sm text-[15px]">
              {t('register.nextStep')} <ArrowRight className="h-4 w-4"/>
            </Button>
          </div>
        )}

        {/* Step 1: 设置密码 */}
        {step === 1 && (
          <div className="space-y-7">
            <AuthField
              label={t('register.password')}
              icon={Lock}
              type={pv ? 'text' : 'password'}
              autoFocus
              placeholder={t('register.passwordPlaceholder')}
              error={errors.password?.message}
              action={
                <button
                  type="button"
                  onClick={() => setPv(!pv)}
                  aria-label={t('register.password')}
                  className="flex h-8 w-8 items-center justify-center text-muted-foreground transition-colors hover:text-foreground"
                >
                  {pv ? <EyeOff className="h-4 w-4"/> : <Eye className="h-4 w-4"/>}
                </button>
              }
              {...register('password')}
              onChange={(e) => {
                register('password').onChange(e);
                setErr('');
              }}
            />

            {/* 强度 —— 单条细线，按等级延展 */}
            {watchedPassword && (
              <div className="space-y-2">
                <div className="h-[2px] w-full bg-border">
                  <div
                    className={cn('h-full transition-all duration-300', strength.color)}
                    style={{width: `${strength.level * 20}%`}}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  {t('register.passwordStrengthLabel')}{' '}
                  <span className="text-foreground">{t(strength.labelKey)}</span>
                </p>
              </div>
            )}

            <AuthField
              label={t('register.confirmPassword')}
              icon={Lock}
              type="password"
              placeholder={t('register.confirmPasswordPlaceholder')}
              error={errors.confirmPassword?.message}
              action={watchedConfirm ? (
                watchedPassword === watchedConfirm
                  ? <CheckCircle2 className="h-4 w-4 text-primary"/>
                  : <AlertCircle className="h-4 w-4 text-destructive"/>
              ) : undefined}
              {...register('confirmPassword')}
              onChange={(e) => {
                register('confirmPassword').onChange(e);
                setErr('');
              }}
            />

            {/* 密码要求 —— 无卡片，短横线达成即转墨蓝 */}
            <div>
              <p className="mb-3 text-[11px] tracking-[0.2em] text-muted-foreground">
                {t('register.passwordRequirements.title')}
              </p>
              <ul className="grid grid-cols-2 gap-x-6 gap-y-2.5 border-t border-border pt-3">
                {[
                  {met: (watchedPassword || '').length >= 8, textKey: 'register.passwordRequirements.length'},
                  {met: /[A-Z]/.test(watchedPassword || ''), textKey: 'register.passwordRequirements.uppercase'},
                  {met: /[0-9]/.test(watchedPassword || ''), textKey: 'register.passwordRequirements.number'},
                  {met: /[^A-Za-z0-9]/.test(watchedPassword || ''), textKey: 'register.passwordRequirements.special'},
                ].map((req, i) => (
                  <li key={i} className={cn(
                    'flex items-center gap-2.5 text-xs transition-colors',
                    req.met ? 'text-foreground' : 'text-muted-foreground/70',
                  )}>
                    <span
                      className={cn('h-px w-3.5 shrink-0 transition-colors', req.met ? 'bg-primary' : 'bg-border')}/>
                    {t(req.textKey)}
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setStep(0);
                  setErr('');
                }}
                className="h-12 flex-1 gap-2 rounded-sm border-border font-normal"
              >
                <ArrowLeft className="h-4 w-4"/> {t('register.prevStep')}
              </Button>
              <Button type="button" onClick={next} className="h-12 flex-1 gap-2 rounded-sm text-[15px]">
                {t('register.nextStep')} <ArrowRight className="h-4 w-4"/>
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: 确认信息 */}
        {step === 2 && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-7">
            {/* 汇总 —— 无卡片，发丝线分行 */}
            <div>
              <p className="mb-3 text-[11px] tracking-[0.2em] text-muted-foreground">
                {t('register.confirmInfo.title')}
              </p>
              <dl className="border-t border-border">
                {[
                  {icon: User, label: t('register.confirmInfo.username'), value: watch('username')},
                  {icon: Mail, label: t('register.confirmInfo.email'), value: watch('email')},
                  {
                    icon: Lock,
                    label: t('register.confirmInfo.password'),
                    value: '•'.repeat((watchedPassword || '').length)
                  },
                ].map(({icon: Icon, label, value}) => (
                  <div key={label} className="flex items-center gap-3 border-b border-border py-3 text-sm">
                    <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground"/>
                    <dt className="text-muted-foreground">{label}</dt>
                    <dd className="ml-auto truncate text-foreground">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>

            {/* 界面语言 —— 下划线式切换 */}
            <div>
              <p className="flex items-center gap-2 text-[13px] font-medium text-muted-foreground">
                <Globe className="h-3.5 w-3.5" aria-hidden="true"/>
                {t('register.locale')}
              </p>
              <Controller
                name="locale"
                control={form.control}
                render={({field}) => (
                  <div className="mt-1 flex border-b border-input">
                    {[
                      {value: 'zh_CN', label: '简体中文'},
                      {value: 'en_US', label: 'English'},
                    ].map(({value, label}) => (
                      <button
                        key={value}
                        type="button"
                        aria-pressed={field.value === value}
                        onClick={() => field.onChange(value)}
                        className={cn(
                          '-mb-px mr-6 border-b-2 py-2.5 text-sm transition-colors',
                          field.value === value
                            ? 'border-primary text-foreground'
                            : 'border-transparent text-muted-foreground hover:text-foreground',
                        )}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                )}
              />
            </div>

            {/* 条款 */}
            <div>
              <label className="flex cursor-pointer items-start gap-3 text-sm text-muted-foreground">
                <Controller
                  name="terms"
                  control={form.control}
                  render={({field}) => (
                    <Checkbox
                      className="mt-0.5"
                      checked={Boolean(field.value)}
                      onCheckedChange={(checked) => field.onChange(checked === true)}
                    />
                  )}
                />
                <span className="leading-relaxed">
                  {t('register.agreeTerms')}{' '}
                  <a href="/terms"
                     className="text-foreground underline decoration-border underline-offset-4 hover:decoration-foreground">
                    {t('register.termsOfService')}
                  </a>{' '}
                  {t('common.and')}{' '}
                  <a href="/privacy"
                     className="text-foreground underline decoration-border underline-offset-4 hover:decoration-foreground">
                    {t('register.privacyPolicy')}
                  </a>
                </span>
              </label>
              {errors.terms && <p className="mt-2 text-xs text-destructive">{errors.terms.message}</p>}
            </div>

            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setStep(1);
                  setErr('');
                }}
                className="h-12 flex-1 gap-2 rounded-sm border-border font-normal"
              >
                <ArrowLeft className="h-4 w-4"/> {t('register.prevStep')}
              </Button>
              <Button type="submit" disabled={busy || !watch('terms')}
                      className="h-12 flex-1 gap-2 rounded-sm text-[15px]">
                {busy ? (
                  <>
                    <Loader className="h-4 w-4 animate-spin"/>
                    {t('register.creating')}
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4"/>
                    {t('register.createAccount')}
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </FormProvider>
    </AuthShell>
  );
}
