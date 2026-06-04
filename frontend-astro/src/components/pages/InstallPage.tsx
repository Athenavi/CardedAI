'use client';

import {useEffect, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';
import {ArrowLeft, ArrowRight, Check, Database, Globe, Loader, Server, Shield} from 'lucide-react';

const steps = [
    {id: 'prereq', label: '检查', icon: Server},
    {id: 'database', label: '配置', icon: Database},
    {id: 'migration', label: '迁移', icon: Loader},
    {id: 'site', label: '设置', icon: Globe},
    {id: 'admin', label: '安全', icon: Shield},
];

export default function InstallPage() {
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [prereqs, setPrereqs] = useState<any[]>([]);
    const [db, setDb] = useState({host: 'localhost', port: '5432', name: '', user: 'postgres', pass: ''});
  const [site, setSite] = useState({name:'FastBlog', desc:'', url:''});
  const [admin, setAdmin] = useState({username:'', email:'', password:''});
    const [migrationStatus, setMigrationStatus] = useState<{
        success?: boolean;
        message?: string;
        logs?: string[]
    }>({});

    useEffect(() => {
        if (step === 0) {
            apiClient.get('/install/prerequisites').then(r => {
                if (r.success && r.data) {
                    // 将对象转换为数组格式
                    const prereqArray = Object.entries(r.data)
                        .filter(([key]) => key !== 'all_passed')
                        .map(([key, value]: [string, any]) => ({
                            name: {
                                python_version: 'Python版本',
                                database_connection: '数据库连接',
                                writable_directories: '目录权限',
                                required_packages: '依赖包'
                            }[key] || key,
                            passed: value.passed,
                            message: value.message,
                            ...value
                        }));
                    setPrereqs(prereqArray);
                }
            });
        }
    }, [step]);

  const checkDb = async () => {
    setBusy(true); setErr('');
    const r = await apiClient.post('/install/check-database', db);
    if (!r.success) setErr(r.error||'连接失败');
    setBusy(false);
    return r.success;
  };

    const runMigration = async () => {
        setBusy(true);
        setErr('');
        try {
            // 先配置数据库
            const dbResult = await apiClient.post('/install/configure-database', {
                db_type: 'postgresql',
                host: db.host,
                port: db.port,
                database: db.name,
                username: db.user,
                password: db.pass
            });

            if (!dbResult.success) {
                setErr(dbResult.error || '数据库配置失败');
                setMigrationStatus({success: false, message: dbResult.error || '数据库配置失败'});
                return false;
            }

            // 再执行数据库迁移
            const r = await apiClient.post('/install/confirm-database-and-migrate');
            if (r.success) {
                setMigrationStatus({success: true, message: r.data?.message || '迁移成功'});
                return true;
            } else {
                setErr(r.error || '迁移失败');
                setMigrationStatus({success: false, message: r.error || '迁移失败'});
                return false;
            }
        } catch (e: any) {
            setErr('迁移过程出错: ' + (e.message || '未知错误'));
            setMigrationStatus({success: false, message: '迁移过程出错'});
            return false;
        } finally {
            setBusy(false);
        }
    };

  const complete = async () => {
    setBusy(true); setErr('');
    try {
        // 注意：数据库配置和迁移已经在 Step 2 完成
        // 这里只需要配置站点、创建管理员和完成安装

        // 配置站点
        await apiClient.post('/install/configure-site', {
            site_name: site.name,
            site_description: site.desc,
            site_url: site.url,
            admin_email: admin.email
        });

        // 创建管理员
      await apiClient.post('/install/create-admin', admin);

        // 完成安装
        const r = await apiClient.post('/install/complete', {
            import_sample_data: false
        });

      if (r.success) window.location.href = '/login';
      else setErr(r.error||'安装失败');
    } catch (e: any) {
        setErr('安装失败: ' + (e.message || '未知错误'));
    } finally {
        setBusy(false);
    }
  };

  const next = async () => {
    if (step === 1 && !await checkDb()) return;
      if (step === 2 && !await runMigration()) return;
    if (step < steps.length - 1) setStep(s => s+1);
    else await complete();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-950 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8"><div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center"><Server className="w-6 h-6 text-white"/></div><h1 className="text-2xl font-bold text-gray-900 dark:text-white">安装 FastBlog</h1></div>

        {/* Steps */}
        <div className="flex gap-2 mb-8 justify-center">
          {steps.map((s,i) => (
            <div key={s.id} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${i===step ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700' : i<step ? 'bg-green-50 text-green-600' : 'bg-gray-100 dark:bg-gray-800 text-gray-400'}`}>
              {i<step ? <Check className="w-4 h-4"/> : <s.icon className="w-4 h-4"/>}{s.label}
            </div>
          ))}
        </div>

        {err && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">{err}</div>}

        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 shadow-xl border border-gray-100 dark:border-gray-800">
          {/* Step 0: Prerequisites */}
          {step === 0 && <div className="space-y-3">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">系统环境检查</p>
            {prereqs.length ? prereqs.map((p,i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-xl"><span className="text-sm">{p.name||p.check||'-'}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full ${p.passed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{p.passed ? '通过' : '失败'}</span>
              </div>
            )) : <div className="animate-pulse space-y-3">{[1,2,3].map(i=><div key={i} className="h-12 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div>}
          </div>}

          {/* Step 1: Database */}
          {step === 1 && <div className="space-y-3">
            {['host','port','name','user','pass'].map(f => (
              <input key={f} type={f==='pass'?'password':'text'} value={(db as any)[f]} onChange={e=>setDb(p=>({...p,[f]:e.target.value}))}
                placeholder={{host:'主机',port:'端口',name:'数据库名',user:'用户名',pass:'密码'}[f]} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
            ))}
          </div>}

            {/* Step 2: Migration */}
            {step === 2 && <div className="space-y-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">数据库迁移</p>
                {migrationStatus.message ? (
                    <div
                        className={`p-4 rounded-xl ${migrationStatus.success ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'}`}>
                        <div className="flex items-center gap-2">
                            {migrationStatus.success ? <Check className="w-5 h-5"/> :
                                <Loader className="w-5 h-5 animate-spin"/>}
                            <span className="text-sm font-medium">{migrationStatus.message}</span>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-8">
                        <Loader className="w-8 h-8 animate-spin mx-auto mb-3 text-blue-600"/>
                      <p className="text-sm text-gray-500 dark:text-gray-400">点击"下一步"开始数据库迁移...</p>
                    </div>
                )}
                <div className="text-xs text-gray-400 mt-2">
                    <p>此步骤将：</p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>创建数据库表结构</li>
                        <li>执行数据迁移脚本</li>
                        <li>初始化系统配置</li>
                    </ul>
                </div>
            </div>}

            {/* Step 3: Site */}
            {step === 3 && <div className="space-y-3">
            <input type="text" value={site.name} onChange={e=>setSite(p=>({...p,name:e.target.value}))} placeholder="站点名称" className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
            <input type="text" value={site.desc} onChange={e=>setSite(p=>({...p,desc:e.target.value}))} placeholder="站点描述" className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
            <input type="url" value={site.url} onChange={e=>setSite(p=>({...p,url:e.target.value}))} placeholder="站点 URL" className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
          </div>}

            {/* Step 4: Admin */}
            {step === 4 && <div className="space-y-3">
            <input type="text" value={admin.username} onChange={e=>setAdmin(p=>({...p,username:e.target.value}))} placeholder="管理员用户名" className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
            <input type="email" value={admin.email} onChange={e=>setAdmin(p=>({...p,email:e.target.value}))} placeholder="管理员邮箱" className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
            <input type="password" value={admin.password} onChange={e=>setAdmin(p=>({...p,password:e.target.value}))} placeholder="管理员密码" className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
          </div>}

          {/* Navigation */}
          <div className="flex justify-between mt-6 pt-4 border-t border-gray-100 dark:border-gray-800">
            <button onClick={()=>setStep(s=>s-1)} disabled={step===0||busy} className="px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 flex items-center gap-1"><ArrowLeft className="w-4 h-4"/>上一步</button>
            <button onClick={next} disabled={busy} className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl text-sm font-medium hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 flex items-center gap-1 shadow-lg">
              {busy ? <Loader className="w-4 h-4 animate-spin"/> : null}{step < steps.length-1 ? '下一步' : '完成安装'}<ArrowRight className="w-4 h-4"/>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
