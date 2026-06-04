'use client';

import {useEffect, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';
import {CheckCircle, Loader, Smartphone, XCircle} from 'lucide-react';

export default function MobileLoginPage() {
  const [status, setStatus] = useState<'checking'|'confirming'|'success'|'error'>('checking');
  const [msg, setMsg] = useState('');

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('login_token') || new URLSearchParams(window.location.search).get('token');
    if (!token) { setStatus('error'); setMsg('缺少登录令牌'); return; }
    setStatus('confirming');
    (async () => {
      try {
        const r = await apiClient.post('/auth/qr/confirm', {login_token: token});
        if (r.success) { setStatus('success'); setMsg('登录确认成功，请返回电脑端继续'); }
        else setStatus('error'), setMsg(r.error||'确认失败');
      } catch { setStatus('error'); setMsg('网络错误'); }
    })();
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-950 dark:to-gray-900 p-4">
      <div className="text-center max-w-sm">
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-white dark:bg-gray-900 shadow-lg border flex items-center justify-center">
          <Smartphone className="w-8 h-8 text-blue-600"/>
        </div>
        {status === 'checking' && <><Loader className="w-6 h-6 animate-spin mx-auto text-blue-600"/><p className="mt-4 text-gray-600 dark:text-gray-400">检查登录状态...</p></>}
        {status === 'confirming' && <><Loader className="w-6 h-6 animate-spin mx-auto text-blue-600"/><p className="mt-4 text-gray-600 dark:text-gray-400">确认登录中...</p></>}
        {status === 'success' && <><CheckCircle className="w-12 h-12 mx-auto text-green-500"/><p className="mt-4 font-medium text-gray-900 dark:text-white">{msg}</p></>}
        {status === 'error' && <><XCircle className="w-12 h-12 mx-auto text-red-500"/><p className="mt-4 font-medium text-gray-900 dark:text-white">{msg}</p></>}
      </div>
    </div>
  );
}
