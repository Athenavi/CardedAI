'use client';

import React, {useCallback, useEffect, useRef, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';
import {useDarkMode} from '@/lib/dark-mode-manager';
import {getAccessTokenFromCookie} from '@/lib/auth-utils';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {useConfirm} from '@/components/ui/confirm-provider';
import {
  AlertCircle,
  Camera,
  Check,
  CheckCircle2,
  Copy,
  Eye,
  EyeOff,
  Fingerprint,
  Globe,
  Loader,
  Lock,
  LogOut,
  Monitor,
  Moon,
  Palette,
  RefreshCw,
  Shield,
  Smartphone,
  Sun,
  Trash2,
  User
} from 'lucide-react';

const TABS = [
    {id: 'profile', label: '个人资料', icon: User, desc: '管理你的基本信息'},
    {id: 'security', label: '安全设置', icon: Shield, desc: '密码、双重验证和会话'},
    {id: 'appearance', label: '外观偏好', icon: Palette, desc: '主题和显示设置'},
    {id: 'sessions', label: '登录设备', icon: Monitor, desc: '管理已登录的设备'},
];

function Settings() {
  const confirm = useConfirm();
  const {theme, setTheme} = useDarkMode();
  const [tab, setTab] = useState(0);
  const [p, setP] = useState<any>(null);
  const [av, setAv] = useState('');
  const [busy, setBusy] = useState(false);
  const [un, setUn] = useState('');
  const [bio, setBio] = useState('');
  const [loc, setLoc] = useState('zh_CN');
  const [priv, setPriv] = useState(false);
  const [pw, setPw] = useState({cur:'',new:'',con:''});
    const [showPw, setShowPw] = useState({cur: false, new: false, con: false});
  const [fa, setFa] = useState(false);
  const [qr, setQr] = useState('');
  const [secret, setSecret] = useState('');
  const [vc, setVc] = useState('');
  const [codes, setCodes] = useState<string[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
    const [savedField, setSavedField] = useState<string | null>(null);
    const [pwStrength, setPwStrength] = useState(0);
  const avRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await apiClient.get('/users/me');
        if (r.success && r.data) {
          const u = (r.data as any).user || r.data;
          setP(u); setUn(u.username||''); setBio(u.bio||''); setLoc(u.locale||'zh_CN'); setPriv(u.profile_private||false);
          let url = u.avatar_url || u.avatar || '';
          if (url && !url.startsWith('http')) {
            const c = await import('@/lib/config').then(m => m.getConfig());
            url = url.startsWith('/') ? `${c.API_BASE_URL}${url}` : `${c.API_BASE_URL}/api/v2/static/avatar/${url}.webp`;
          }
          setAv(url||`https://ui-avatars.com/api/?name=${encodeURIComponent(u.username||'U')}&background=random`);
        }
        const f = await apiClient.get('/security/2fa/status');
        if (f.success && f.data) setFa((f.data as any).is_2fa_enabled||false);
      } catch {}
    })();
  }, []);

    // Password strength calculator
    useEffect(() => {
        const p = pw.new;
        let s = 0;
        if (p.length >= 8) s++;
        if (p.length >= 12) s++;
        if (/[A-Z]/.test(p)) s++;
        if (/[0-9]/.test(p)) s++;
        if (/[^A-Za-z0-9]/.test(p)) s++;
        setPwStrength(s);
    }, [pw.new]);

    const flashSaved = useCallback((field: string) => {
        setSavedField(field);
        setTimeout(() => setSavedField(null), 2000);
    }, []);

  const save = async (field: string, value: any) => {
    setBusy(true);
    try {
      const r = await apiClient.put('/users/me', {[field]: value});
        if (r.success) flashSaved(field);
        else alert(r.error || '保存失败');
    } catch { alert('网络错误'); }
    setBusy(false);
  };

  const uploadAv = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]; if(!f) return;
    if(!['image/jpeg','image/png','image/webp'].includes(f.type)){alert('仅支持 JPG/PNG/WEBP');return;}
    if(f.size>5<<20){alert('不超过5MB');return;}
    const fd = new FormData(); fd.append('file', f);
    setBusy(true);
    try {
      const c = await import('@/lib/config').then(m => m.getConfig());
      const t = getAccessTokenFromCookie();
      const h:any = {}; if(t) h['Authorization']=`Bearer ${t}`;
      const r = await fetch(`${c.API_BASE_URL}${c.API_PREFIX}/users/me/avatar`,{method:'POST',body:fd,credentials:'include',headers:h});
      const d = await r.json();
        if (r.ok && d.success) {
            const rd = new FileReader();
            rd.onload = e2 => setAv(e2.target?.result as string);
            rd.readAsDataURL(f);
            flashSaved('avatar');
        }
      else alert(d.error||'上传失败');
    } catch {} finally { setBusy(false); }
  };

  const changePw = async () => {
    if(pw.new!==pw.con){alert('两次密码不一致');return;}
    if(pw.new.length<6){alert('密码至少6位');return;}
    setBusy(true);
    try {
      const c = await import('@/lib/config').then(m => m.getConfig());
      const fd = new FormData(); fd.append('current_password',pw.cur); fd.append('new_password',pw.new); fd.append('confirm_password',pw.con);
      const r = await fetch(`${c.API_BASE_URL}${c.API_PREFIX}/users/me/change-password`,{method:'POST',body:fd,credentials:'include'});
      const d = await r.json();
      if(r.ok&&d.success){alert('密码已更新，请重新登录');window.location.href='/login';} else alert(d.error||'失败');
    } catch{} finally{setBusy(false);}
  };

  const setup2FA = async () => { const r = await apiClient.get('/security/2fa/setup'); if(r.success&&r.data){setQr(r.data.qr_code);setSecret(r.data.secret);} };
  const enable2FA = async () => { if(vc.length!==6){alert('输入6位验证码');return;} const r = await apiClient.post('/security/2fa/enable',{totp_token:vc}); if(r.success){setFa(true);setQr('');setCodes((r.data as any)?.backup_codes||[]);} };
  const disable2FA = async () => {
    if (!await confirm({message: '禁用2FA？', variant: 'warning'})) return;
    const r = await apiClient.post('/security/2fa/disable');
    if (r.success) {
      setFa(false);
      setQr('');
      setSecret('');
      setCodes([]);
    }
  };

  const loadS = async () => {
    const r = await apiClient.get('/security/admin/session/my-sessions');
    if (r.success && r.data) {
      const raw = r.data.sessions || r.data.data?.sessions || [];
      setSessions(Array.isArray(raw) ? raw : []);
    }
  };
  useEffect(()=>{if(tab===3)loadS();},[tab]);

  const revokeSession = async (sessionId: string) => {
    const r = await apiClient.post('/security/admin/session/revoke', {session_id: sessionId});
      if (r.success) setSessions(prev => prev.filter(s => s.session_id !== sessionId && s.id !== sessionId));
      else alert(r.error || '注销失败');
  };

  const revokeAllOther = async () => {
    if (!await confirm({message: '这将注销所有其他设备，确定继续？', variant: 'warning'})) return;
    const r = await apiClient.post('/security/admin/session/revoke-all', {});
      if (r.success) loadS();
      else alert(r.error || '操作失败');
  };

  const handleLogout = async () => {
      try {
          await apiClient.post('/auth/logout');
      } catch {
      }
    document.cookie='access_token=;path=/;expires=Thu,01 Jan 1970 00:00:00 UTC';
    document.cookie='refresh_token=;path=/;expires=Thu,01 Jan 1970 00:00:00 UTC';
    window.location.href='/login';
  };

  const formatDevice = (s: any): string => {
    const info = s.device_info || s;
    if (typeof info === 'string') return info;
    const parts: string[] = [];
    if (info.browser) parts.push(info.browser);
    if (info.platform) parts.push(info.platform);
    if (info.os) parts.push(info.os);
    return parts.length ? parts.join(' · ') : (s.device || s.user_agent?.slice(0, 50) || '未知设备');
  };

  const getDeviceIcon = (s: any) => {
    const info = s.device_info || s;
    const ua = (info.user_agent || info.browser || '').toLowerCase();
    if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) return <Smartphone className="w-4 h-4"/>;
    return <Monitor className="w-4 h-4"/>;
  };

    const pwStrengthColors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500', 'bg-emerald-500'];
    const pwStrengthLabels = ['弱', '一般', '良好', '强', '非常强'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-950 dark:to-gray-900">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">设置</h1>
                <p className="text-gray-500 dark:text-gray-400">管理你的账户设置和偏好</p>
        </div>

            <div className="flex flex-col lg:flex-row gap-6">
                {/* ═══ Sidebar Navigation ═══ */}
                <div className="lg:w-64 shrink-0">
                    <nav
                        className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden p-1.5">
                        {TABS.map((t, i) => {
                            const Icon = t.icon;
                            return (
                                <button
                                    key={t.id}
                                    onClick={() => setTab(i)}
                                    className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl text-left transition-all duration-200 ${
                                        tab === i
                                            ? 'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 text-blue-700 dark:text-blue-300 shadow-sm'
                                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-750'
                                    }`}
                                >
                                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                                        tab === i
                                            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                                          : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                                    }`}>
                                        <Icon className="w-4.5 h-4.5"/>
                                    </div>
                                    <div className="min-w-0">
                                        <span className="block text-sm font-medium">{t.label}</span>
                                        <span className="block text-[11px] opacity-60 truncate">{t.desc}</span>
                                    </div>
                                </button>
                            );
                        })}

                        {/* Logout */}
                        <div className="border-t border-gray-100 dark:border-gray-700 mt-1.5 pt-1.5">
                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-3 px-4 py-3.5 rounded-xl text-left text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors"
                            >
                                <div
                                    className="w-9 h-9 rounded-lg bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                                    <LogOut className="w-4.5 h-4.5"/>
                                </div>
                                <span className="text-sm font-medium">退出登录</span>
                            </button>
                        </div>
                    </nav>
                </div>

                {/* ═══ Main Content ═══ */}
                <div className="flex-1 min-w-0">
                    {/* Profile Tab */}
                    {tab === 0 && (
                        <div className="space-y-6">
                            {/* Avatar Section */}
                            <div
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
                                <div className="h-20 bg-gradient-to-r from-blue-500 to-indigo-500"/>
                                <div className="px-6 pb-6">
                                    <div className="flex flex-col sm:flex-row items-start sm:items-end gap-4 -mt-10">
                                        <div className="relative group">
                                            <img
                                                src={av}
                                                alt=""
                                                className="w-20 h-20 rounded-2xl object-cover border-4 border-white dark:border-gray-800 shadow-lg bg-gray-100"
                                                onError={e => {
                                                    (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(p?.username || 'U')}&background=random`
                                                }}
                                            />
                                            <button
                                                onClick={() => avRef.current?.click()}
                                                className="absolute inset-0 bg-black/40 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                                            >
                                                <Camera className="w-6 h-6 text-white"/>
                                            </button>
                                            {savedField === 'avatar' && (
                                                <div
                                                    className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                                                    <Check className="w-3.5 h-3.5 text-white"/>
                                                </div>
                                            )}
                                            <input ref={avRef} type="file" accept="image/jpeg,image/png,image/webp"
                                                   onChange={uploadAv} className="hidden"/>
                                        </div>
                                        <div className="pb-1">
                                            <h2 className="text-lg font-bold text-gray-900 dark:text-white">{p?.username || '用户'}</h2>
                                            <p className="text-sm text-gray-500 dark:text-gray-400">{p?.email || ''}</p>
                                        </div>
                                        <div className="sm:ml-auto pb-1">
                                            <button
                                                onClick={() => avRef.current?.click()}
                                                className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors flex items-center gap-2"
                                            >
                                                <Camera className="w-4 h-4"/> 更换头像
                                            </button>
                                            <p className="text-xs text-gray-400 mt-1.5">JPG/PNG/WEBP · 最大5MB</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Username */}
                            <div
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                                <label
                                    className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">用户名</label>
                                <div className="flex gap-3">
                                    <input
                                        value={un}
                                        onChange={e => setUn(e.target.value)}
                                        className="flex-1 px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-sm focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:text-white transition-all"
                                    />
                                    <button
                                        onClick={() => save('username', un)}
                                        disabled={busy}
                                        className="px-5 py-3 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center gap-2 shrink-0"
                                    >
                                        {savedField === 'username' ? <><Check className="w-4 h-4"/> 已保存</> : busy ?
                                            <Loader className="w-4 h-4 animate-spin"/> : '保存'}
                                    </button>
                                </div>
                            </div>

                            {/* Bio */}
                            <div
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                                <label
                                    className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">个人简介</label>
                                <textarea
                                    value={bio}
                                    onChange={e => setBio(e.target.value)}
                                    rows={3}
                                    placeholder="介绍一下你自己..."
                                    className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-sm focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:text-white resize-none transition-all placeholder-gray-400"
                                />
                                <div className="flex items-center justify-between mt-3">
                                    <span className="text-xs text-gray-400">{bio.length}/200 字符</span>
                                    <button
                                        onClick={() => save('bio', bio)}
                                        disabled={busy}
                                        className="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center gap-2"
                                    >
                                        {savedField === 'bio' ? <><Check className="w-4 h-4"/> 已保存</> : '保存'}
                                    </button>
                                </div>
                            </div>

                            {/* Language & Privacy */}
                            <div
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                                <div className="grid sm:grid-cols-2 gap-6">
                                    <div>
                                        <label
                                            className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                                            <Globe className="w-4 h-4"/> 界面语言
                                        </label>
                                        <select
                                            value={loc}
                                            onChange={e => {
                                                setLoc(e.target.value);
                                                save('locale', e.target.value);
                                            }}
                                            className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-sm focus:outline-none focus:border-blue-500 dark:text-white transition-all"
                                        >
                                            <option value="zh_CN">🇨🇳 简体中文</option>
                                            <option value="en_US">🇺🇸 English</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label
                                            className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                                            <Eye className="w-4 h-4"/> 隐私设置
                                        </label>
                                        <label
                                            className="flex items-center gap-3 cursor-pointer p-3 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors">
                                            <div className="relative">
                                                <input type="checkbox" checked={priv} onChange={e => {
                                                    setPriv(e.target.checked);
                                                    save('privacy', e.target.checked);
                                                }} className="peer sr-only"/>
                                                <div
                                                    className="w-10 h-6 bg-gray-300 dark:bg-gray-600 peer-checked:bg-blue-500 rounded-full transition-colors"/>
                                                <div
                                                    className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transform peer-checked:translate-x-4 transition-transform"/>
                                            </div>
                                            <span className="text-sm text-gray-700 dark:text-gray-300">私密资料</span>
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Security Tab */}
                    {tab === 1 && (
                        <div className="space-y-6">
                            {/* Password Change */}
                            <div
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                                <div className="flex items-center gap-3 mb-6">
                                    <div
                                        className="w-10 h-10 bg-amber-100 dark:bg-amber-900/30 rounded-xl flex items-center justify-center">
                                        <Lock className="w-5 h-5 text-amber-600 dark:text-amber-400"/>
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900 dark:text-white">修改密码</h3>
                                      <p
                                        className="text-xs text-gray-500 dark:text-gray-400">定期更改密码以保护账户安全</p>
                                    </div>
                                </div>

                                <div className="space-y-4 max-w-md">
                                    <div className="relative">
                                        <input
                                            type={showPw.cur ? 'text' : 'password'}
                                            value={pw.cur}
                                            onChange={e => setPw(p => ({...p, cur: e.target.value}))}
                                            placeholder="当前密码"
                                            className="w-full px-4 py-3.5 pr-12 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-sm focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:text-white transition-all"
                                        />
                                        <button type="button" onClick={() => setShowPw(s => ({...s, cur: !s.cur}))}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                                            {showPw.cur ? <EyeOff className="w-4.5 h-4.5"/> :
                                                <Eye className="w-4.5 h-4.5"/>}
                                        </button>
                                    </div>
                                    <div className="relative">
                                        <input
                                            type={showPw.new ? 'text' : 'password'}
                                            value={pw.new}
                                            onChange={e => setPw(p => ({...p, new: e.target.value}))}
                                            placeholder="新密码"
                                            className="w-full px-4 py-3.5 pr-12 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-sm focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:text-white transition-all"
                                        />
                                        <button type="button" onClick={() => setShowPw(s => ({...s, new: !s.new}))}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                                            {showPw.new ? <EyeOff className="w-4.5 h-4.5"/> :
                                                <Eye className="w-4.5 h-4.5"/>}
                                        </button>
                                        {pw.new && (
                                            <div className="mt-2 space-y-1">
                                                <div className="flex gap-1">
                                                    {[0, 1, 2, 3, 4].map(i => (
                                                        <div key={i}
                                                             className={`h-1 flex-1 rounded-full transition-all ${i < pwStrength ? pwStrengthColors[pwStrength - 1] : 'bg-gray-200 dark:bg-gray-700'}`}/>
                                                    ))}
                                                </div>
                                                <span
                                                  className="text-xs text-gray-500 dark:text-gray-400">强度: {pwStrength > 0 ? pwStrengthLabels[pwStrength - 1] : '—'}</span>
                                            </div>
                                        )}
                                    </div>
                                    <div className="relative">
                                        <input
                                            type="password"
                                            value={pw.con}
                                            onChange={e => setPw(p => ({...p, con: e.target.value}))}
                                            placeholder="确认新密码"
                                            className="w-full px-4 py-3.5 pr-12 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-sm focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:text-white transition-all"
                                        />
                                        {pw.con && (
                                            <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                                {pw.new === pw.con ?
                                                    <CheckCircle2 className="w-5 h-5 text-green-500"/> :
                                                    <AlertCircle className="w-5 h-5 text-red-500"/>}
                                            </div>
                                        )}
                                    </div>
                                    <button
                                        onClick={changePw}
                                        disabled={busy || !pw.cur || !pw.new || pw.new !== pw.con}
                                        className="px-6 py-3 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                                    >
                                        {busy ? <Loader className="w-4 h-4 animate-spin"/> :
                                            <Lock className="w-4 h-4"/>}
                                        更新密码
                                    </button>
                                </div>
                            </div>

                            {/* 2FA */}
                            <div
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                                <div className="flex items-start justify-between mb-6">
                                    <div className="flex items-center gap-3">
                                        <div
                                            className={`w-10 h-10 rounded-xl flex items-center justify-center ${fa ? 'bg-green-100 dark:bg-green-900/30' : 'bg-gray-100 dark:bg-gray-700'}`}>
                                            <Fingerprint
                                              className={`w-5 h-5 ${fa ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}/>
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                                双重验证
                                                {fa && <span
                                                    className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs rounded-full font-medium">已启用</span>}
                                            </h3>
                                          <p
                                            className="text-xs text-gray-500 dark:text-gray-400">使用认证器应用增加额外安全层</p>
                                        </div>
                                    </div>
                                    {fa ? (
                                        <button onClick={disable2FA}
                                                className="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 text-sm font-medium rounded-xl hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors">
                                            禁用
                                        </button>
                                    ) : (
                                        <button onClick={setup2FA} disabled={busy}
                                                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all">
                                            启用
                                        </button>
                                    )}
                                </div>

                                {qr && (
                                    <div className="mt-4 space-y-4 border-t border-gray-100 dark:border-gray-700 pt-6">
                                        <div className="text-center">
                                            <img src={qr} alt="2FA QR"
                                                 className="w-40 h-40 mx-auto rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm"/>
                                            {secret && (
                                                <div className="mt-3 flex items-center justify-center gap-2">
                                                    <code
                                                        className="bg-gray-100 dark:bg-gray-900 px-3 py-1.5 rounded-lg text-xs font-mono text-gray-700 dark:text-gray-300">{secret}</code>
                                                    <button onClick={() => {
                                                        navigator.clipboard.writeText(secret)
                                                    }}
                                                            className="p-1.5 text-gray-400 hover:text-blue-500 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20">
                                                        <Copy className="w-3.5 h-3.5"/>
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex gap-2 max-w-xs mx-auto">
                                            <input
                                                type="text"
                                                value={vc}
                                                onChange={e => setVc(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                                placeholder="000000"
                                                className="flex-1 text-center text-xl tracking-[0.4em] px-3 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:text-white font-mono transition-all"
                                            />
                                            <button onClick={enable2FA}
                                                    className="px-5 py-3 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 shrink-0">验证
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {codes.length > 0 && (
                                    <div
                                        className="mt-4 p-5 bg-amber-50 dark:bg-amber-900/20 rounded-2xl border border-amber-200 dark:border-amber-800/30">
                                        <div className="flex items-center gap-2 mb-3">
                                            <AlertCircle className="w-4 h-4 text-amber-600"/>
                                            <span
                                                className="text-sm font-semibold text-amber-800 dark:text-amber-200">备用恢复码</span>
                                        </div>
                                        <p className="text-xs text-amber-700 dark:text-amber-300 mb-3">请妥善保存这些备用码，每个只能使用一次。</p>
                                        <div className="grid grid-cols-2 gap-2">
                                            {codes.map(c => (
                                                <code key={c}
                                                      className="px-3 py-1.5 bg-white dark:bg-gray-800 rounded-lg text-xs font-mono text-gray-700 dark:text-gray-300 text-center">{c}</code>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Appearance Tab */}
                    {tab === 2 && (
                        <div className="space-y-6">
                            <div
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                                <div className="flex items-center gap-3 mb-6">
                                    <div
                                        className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
                                        <Palette className="w-5 h-5 text-purple-600 dark:text-purple-400"/>
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900 dark:text-white">主题设置</h3>
                                      <p className="text-xs text-gray-500 dark:text-gray-400">选择你喜欢的界面主题</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-3 gap-4">
                                    {[
                                        {
                                            id: 'light',
                                            label: '浅色',
                                            icon: Sun,
                                            gradient: 'from-amber-50 to-orange-50',
                                            activeBorder: 'border-amber-400'
                                        },
                                        {
                                            id: 'dark',
                                            label: '深色',
                                            icon: Moon,
                                            gradient: 'from-gray-800 to-gray-900',
                                            activeBorder: 'border-blue-400'
                                        },
                                        {
                                            id: 'system',
                                            label: '跟随系统',
                                            icon: Monitor,
                                            gradient: 'from-blue-50 to-indigo-50',
                                            activeBorder: 'border-indigo-400'
                                        },
                                    ].map(t => {
                                        const Icon = t.icon;
                                        const isActive = theme === t.id;
                                        return (
                                            <button
                                                key={t.id}
                                                onClick={() => setTheme(t.id as any)}
                                                className={`relative p-5 rounded-2xl border-2 transition-all duration-200 ${
                                                    isActive
                                                        ? `${t.activeBorder} bg-gradient-to-br ${t.gradient} dark:from-gray-700 dark:to-gray-800 shadow-md`
                                                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 bg-white dark:bg-gray-800'
                                                }`}
                                            >
                                                {isActive && (
                                                    <div
                                                        className="absolute top-2 right-2 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                                                        <Check className="w-3 h-3 text-white"/>
                                                    </div>
                                                )}
                                                <Icon
                                                    className={`w-8 h-8 mx-auto mb-3 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'}`}/>
                                                <span
                                                    className={`text-sm font-medium ${isActive ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'}`}>
                            {t.label}
                          </span>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Sessions Tab */}
                    {tab === 3 && (
                        <div className="space-y-6">
                            <div
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                                            <Monitor className="w-5 h-5 text-blue-600 dark:text-blue-400"/>
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-gray-900 dark:text-white">已登录设备</h3>
                                          <p
                                            className="text-xs text-gray-500 dark:text-gray-400">共 {sessions.length} 个活跃会话</p>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={loadS}
                                                className="p-2 text-gray-400 hover:text-blue-500 rounded-xl hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                                                title="刷新">
                                            <RefreshCw className="w-4 h-4"/>
                                        </button>
                                        {sessions.length > 1 && (
                                            <button
                                                onClick={revokeAllOther}
                                                className="px-3 py-2 text-xs font-medium text-red-500 bg-red-50 dark:bg-red-900/20 rounded-xl hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                                            >
                                                注销其他设备
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {sessions.length === 0 ? (
                                    <div className="py-12 text-center">
                                        <Monitor className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600"/>
                                        <p className="text-sm text-gray-400">暂无活跃会话</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {sessions.map((s: any, i: number) => {
                                            const isCurrent = s.is_current || s.current || false;
                                            const sessionId = s.session_id || s.id;
                                            return (
                                                <div
                                                    key={sessionId || i}
                                                    className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                                                        isCurrent
                                                            ? 'border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10'
                                                            : 'border-gray-100 dark:border-gray-700 hover:border-gray-200 dark:hover:border-gray-600'
                                                    }`}
                                                >
                                                    <div
                                                        className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                                                          isCurrent ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                                                        }`}>
                                                        {getDeviceIcon(s)}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
                                                            <span className="truncate">{formatDevice(s)}</span>
                                                            {isCurrent && <span
                                                                className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-[10px] rounded-full font-medium shrink-0">当前设备</span>}
                                                        </p>
                                                        <div
                                                            className="flex flex-wrap gap-x-4 gap-y-0.5 mt-1 text-xs text-gray-400">
                                                            <span className="flex items-center gap-1"><Globe
                                                                className="w-3 h-3"/> {s.ip_address || s.ip || '—'}</span>
                                                            <span>{s.last_active ? new Date(s.last_active).toLocaleString('zh-CN') : s.created_at ? new Date(s.created_at).toLocaleString('zh-CN') : ''}</span>
                                                        </div>
                                                    </div>
                                                    {!isCurrent && (
                                                        <button
                                                            onClick={() => revokeSession(sessionId)}
                                                            className="p-2 text-gray-400 hover:text-red-500 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                                            title="注销"
                                                        >
                                                            <Trash2 className="w-4 h-4"/>
                                                        </button>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
      </div>
    </div>
  );
}

export default function SettingsPageGuard() {
  return <AuthGuard><QueryProvider><Settings/></QueryProvider></AuthGuard>;
}
