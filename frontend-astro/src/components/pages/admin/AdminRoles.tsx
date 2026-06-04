'use client';

import React, {useState, useMemo, useEffect} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {StatCard} from '@/components/admin/shared-ui';
import {
  Shield,
  Edit,
  Trash2,
  Plus,
  X,
  Check,
  AlertTriangle,
  Users,
  Search,
  Key,
  UserCheck,
  Crown,
  Lock,
  Unlock,
  ChevronDown,
  CheckCircle2,
  XCircle,
  Loader,
  Hash,
  Layers,
  Settings,
  FileText,
  MessageSquare,
  Image,
  BarChart3,
  Globe,
  Bell
} from 'lucide-react';

// ─── Permission resource type icons ───────────────────
const RESOURCE_ICONS: Record<string, {
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  gradient: string;
  color: string
}> = {
  article: {icon: FileText, gradient: 'from-blue-500 to-cyan-500', color: 'text-blue-600 dark:text-blue-400'},
  user: {icon: Users, gradient: 'from-purple-500 to-pink-500', color: 'text-purple-600 dark:text-purple-400'},
  comment: {icon: MessageSquare, gradient: 'from-amber-500 to-orange-500', color: 'text-amber-600 dark:text-amber-400'},
  media: {icon: Image, gradient: 'from-emerald-500 to-teal-500', color: 'text-emerald-600 dark:text-emerald-400'},
  category: {icon: Layers, gradient: 'from-rose-500 to-red-500', color: 'text-rose-600 dark:text-rose-400'},
  system: {icon: Settings, gradient: 'from-gray-500 to-gray-600', color: 'text-gray-600 dark:text-gray-400'},
  analytics: {
    icon: BarChart3,
    gradient: 'from-indigo-500 to-violet-500',
    color: 'text-indigo-600 dark:text-indigo-400'
  },
  seo: {icon: Globe, gradient: 'from-teal-500 to-cyan-500', color: 'text-teal-600 dark:text-teal-400'},
  notification: {icon: Bell, gradient: 'from-pink-500 to-rose-500', color: 'text-pink-600 dark:text-pink-400'},
  rbac: {icon: Key, gradient: 'from-violet-500 to-purple-500', color: 'text-violet-600 dark:text-violet-400'},
};

const getResourceConfig = (rt: string) => RESOURCE_ICONS[rt] || {
  icon: Shield,
  gradient: 'from-gray-500 to-gray-600',
  color: 'text-gray-600 dark:text-gray-400'
};


// ─── Section Title ────────────────────────────────────
const SectionTitle: React.FC<{
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  title: string;
  subtitle?: string;
  action?: React.ReactNode
}> = ({
                                                                                                             icon: Icon,
                                                                                                             title,
                                                                                                             subtitle,
                                                                                                             action
                                                                                                           }) => (
    <div className="flex items-center justify-between mb-5">
      <div className="flex items-center gap-3">
        <div
            className="w-9 h-9 rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
          <Icon className="w-4.5 h-4.5 text-gray-600 dark:text-gray-300"/>
        </div>
        <div>
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
);

// ─── Skeleton ─────────────────────────────────────────
const RolesSkeleton = () => (
    <div className="space-y-0 animate-pulse">
      {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="flex items-center gap-4 px-6 py-5 border-b border-gray-100 dark:border-gray-800">
            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-lg w-32"/>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-lg w-48"/>
            </div>
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-full w-16"/>
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-full w-16"/>
            <div className="flex gap-1">
              <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
              <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
            </div>
          </div>
      ))}
    </div>
);

// ─── Empty State ──────────────────────────────────────
const EmptyState: React.FC<{
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  title: string;
  desc: string;
  action?: React.ReactNode
}> = ({
                                                                                                      icon: Icon,
                                                                                                      title,
                                                                                                      desc,
                                                                                                      action
                                                                                                    }) => (
    <div className="flex flex-col items-center justify-center py-16 px-6">
      <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-300 dark:text-gray-600"/>
      </div>
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <p className="text-xs text-gray-400 dark:text-gray-500 dark:text-gray-400 mt-1">{desc}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
);

// ─── Enhanced Modal ───────────────────────────────────
const Modal: React.FC<{
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  maxWidth?: string
}> = ({open, onClose, title, subtitle, children, maxWidth = 'max-w-lg'}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (open) {
      setIsVisible(true);
      requestAnimationFrame(() => setIsAnimating(true));
    } else {
      setIsAnimating(false);
      const timer = setTimeout(() => setIsVisible(false), 200);
      return () => clearTimeout(timer);
    }
  }, [open]);

  if (!isVisible) return null;
  return (
      <div
          className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-200 ${isAnimating ? 'bg-black/50 backdrop-blur-sm' : 'bg-black/0'}`}
          onClick={onClose}>
        <div
            className={`bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full ${maxWidth} max-h-[85vh] overflow-hidden transform transition-all duration-200 ${isAnimating ? 'scale-100 opacity-100 translate-y-0' : 'scale-95 opacity-0 translate-y-4'}`}
            onClick={e => e.stopPropagation()}>
          <div
              className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white text-base">{title}</h2>
              {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
            </div>
            <button onClick={onClose}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors">
              <X className="w-4.5 h-4.5"/>
            </button>
          </div>
          <div className="p-6 overflow-y-auto max-h-[calc(85vh-80px)]">{children}</div>
        </div>
      </div>
  );
};

// ─── Delete Confirm ───────────────────────────────────
const DeleteConfirm: React.FC<{ role: any; onConfirm: () => void; onCancel: () => void; isPending?: boolean }> = ({
                                                                                                                    role,
                                                                                                                    onConfirm,
                                                                                                                    onCancel,
                                                                                                                    isPending
                                                                                                                  }) => (
    <div className="text-center py-2">
      <div
          className="w-14 h-14 rounded-2xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
        <AlertTriangle className="w-7 h-7 text-red-500"/>
      </div>
      <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-1">确认删除角色</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        确定要删除角色「<span className="font-medium text-gray-700 dark:text-gray-300">{role.name}</span>」吗？
      </p>
      <p className="text-xs text-gray-400 mb-6">拥有该角色的用户将失去相关权限，此操作不可撤销。</p>
      <div className="flex items-center justify-center gap-3">
        <button onClick={onCancel}
                className="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors">
          取消
        </button>
        <button onClick={onConfirm} disabled={isPending}
                className="px-5 py-2.5 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors disabled:opacity-50 inline-flex items-center gap-2">
          {isPending && <Loader className="w-4 h-4 animate-spin"/>}
          确认删除
        </button>
      </div>
    </div>
);

/* ═══════════════════════════════════════════════════════
   Role Modal - Create/Edit Role with Permissions
   ═══════════════════════════════════════════════════════ */
function RoleModal({mode, role, permissions, onClose}: {
  mode: 'create' | 'edit';
  role?: any;
  permissions: any[];
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [name, setName] = useState(role?.name || '');
  const [slug, setSlug] = useState(role?.slug || '');
  const [desc, setDesc] = useState(role?.description || '');
  const [selectedPerms, setSelectedPerms] = useState<Set<string>>(() => {
    if (!role?.permission_codes) return new Set<string>();
    return new Set(role.permission_codes.map((c) => typeof c === 'string' ? c : String(c)));
  });
  const [error, setError] = useState('');
  const [searchPerms, setSearchPerms] = useState('');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Group permissions by resource_type
  const grouped = useMemo(() => {
    const acc: Record<string, any[]> = {};
    permissions.forEach((p) => {
      const rt = p.resource_type || p.code?.split(':')[0] || 'other';
      if (!acc[rt]) acc[rt] = [];
      acc[rt].push(p);
    });
    return acc;
  }, [permissions]);

  // Filter grouped permissions
  const filteredGrouped = useMemo(() => {
    if (!searchPerms) return grouped;
    const q = searchPerms.toLowerCase();
    const result: Record<string, any[]> = {};
    Object.entries(grouped).forEach(([rt, perms]) => {
      const filtered = perms.filter((p) =>
          (p.name || '').toLowerCase().includes(q) || (p.code || '').toLowerCase().includes(q)
      );
      if (filtered.length > 0) result[rt] = filtered;
    });
    return result;
  }, [grouped, searchPerms]);

  // Initialize expanded groups
  useEffect(() => {
    setExpandedGroups(new Set(Object.keys(grouped)));
  }, [grouped]);

  const togglePerm = (code: string) => {
    const s = new Set(selectedPerms);
    s.has(code) ? s.delete(code) : s.add(code);
    setSelectedPerms(s);
  };

  const toggleGroup = (rt: string) => {
    const s = new Set(expandedGroups);
    s.has(rt) ? s.delete(rt) : s.add(rt);
    setExpandedGroups(s);
  };

  const selectAllInGroup = (rt: string, perms: any[]) => {
    const s = new Set(selectedPerms);
    const allSelected = perms.every((p) => s.has(p.code || `${p.resource_type}:${p.action}`));
    perms.forEach((p) => {
      const code = p.code || `${p.resource_type}:${p.action}`;
      allSelected ? s.delete(code) : s.add(code);
    });
    setSelectedPerms(s);
  };

  const submitMut = useMutation({
    mutationFn: async () => {
      if (!name.trim()) throw new Error('角色名称不能为空');
      if (!slug.trim()) throw new Error('角色标识不能为空');
      const perms = [...selectedPerms];
      if (mode === 'create') {
        return apiClient.post('/api/v2/security/rbac/roles', {name, slug, description: desc, permission_codes: perms});
      } else {
        return apiClient.put(`/api/v2/security/rbac/roles/${role!.id}/permissions`, {permission_codes: perms});
      }
    },
    onSuccess: (res: any) => {
      if (!res.success) { setError(res.error || '操作失败'); return; }
      qc.invalidateQueries({queryKey: ['admin-roles']});
      onClose();
    },
    onError: (e: any) => setError(e.message || '请求失败'),
  });

  return (
      <Modal open={true} onClose={onClose}
             title={mode === 'create' ? '创建角色' : '编辑角色'}
             subtitle={mode === 'create' ? '定义一个新角色并分配权限' : `编辑角色「${role?.name}」的权限`}
             maxWidth="max-w-2xl">
        <div className="space-y-5">
          {error && (
              <div
                  className="flex items-center gap-2.5 p-3.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-xl border border-red-200 dark:border-red-800">
                <XCircle className="w-4.5 h-4.5 shrink-0"/>{error}
          </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">角色名称</label>
              <input type="text" value={name} onChange={e => setName(e.target.value)}
                     className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800/80 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                     placeholder="例如: 编辑者"/>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">角色标识</label>
              <input type="text" value={slug} onChange={e => setSlug(e.target.value)} disabled={mode === 'edit'}
                     className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800/80 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-mono"
                     placeholder="例如: editor"/>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">描述</label>
            <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={2}
                      className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800/80 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 resize-none transition-all"
                      placeholder="角色描述（可选）"/>
          </div>

          {/* Permissions */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">权限配置</label>
              <span
                  className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full font-medium">
              已选 {selectedPerms.size} 项
            </span>
            </div>

            {/* Permission search */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <input value={searchPerms} onChange={e => setSearchPerms(e.target.value)}
                     placeholder="搜索权限..."
                     className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"/>
            </div>

            <div
                className="max-h-72 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-xl divide-y divide-gray-100 dark:divide-gray-800">
              {Object.entries(filteredGrouped).map(([rt, perms]: [string, any[]]) => {
                const config = getResourceConfig(rt);
                const Icon = config.icon;
                const isExpanded = expandedGroups.has(rt);
                const allSelected = perms.every((p) => selectedPerms.has(p.code || `${p.resource_type}:${p.action}`));
                const someSelected = perms.some((p) => selectedPerms.has(p.code || `${p.resource_type}:${p.action}`));

                return (
                    <div key={rt}>
                      <button onClick={() => toggleGroup(rt)}
                              className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                        <div className="flex items-center gap-2.5">
                          <div
                              className={`w-7 h-7 rounded-lg bg-gradient-to-br ${config.gradient} flex items-center justify-center`}>
                            <Icon className="w-3.5 h-3.5 text-white"/>
                          </div>
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">{rt}</span>
                          <span className="text-[10px] text-gray-400">({perms.length})</span>
                          {allSelected && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500"/>}
                          {!allSelected && someSelected &&
                              <span className="w-3.5 h-3.5 rounded border-2 border-blue-500 bg-blue-500/30"/>}
                        </div>
                        <div className="flex items-center gap-2">
                          <button onClick={e => {
                            e.stopPropagation();
                            selectAllInGroup(rt, perms);
                          }}
                                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium transition-colors ${
                                      allSelected
                                          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                                        : 'bg-gray-100 text-gray-500 dark:text-gray-400 dark:bg-gray-800 dark:text-gray-400 hover:bg-blue-100 hover:text-blue-600'
                                  }`}>
                            {allSelected ? '全选 ✓' : '全选'}
                          </button>
                          <ChevronDown
                              className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}/>
                        </div>
                      </button>
                      {isExpanded && (
                          <div className="px-4 pb-3 flex flex-wrap gap-1.5">
                            {perms.map((p) => {
                              const code = p.code || `${p.resource_type}:${p.action}`;
                              const active = selectedPerms.has(code);
                              return (
                                  <button key={code} onClick={() => togglePerm(code)}
                                          className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all duration-150 ${
                                              active
                                                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-400 shadow-sm'
                                                  : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50/50 dark:hover:bg-blue-900/10'
                                          }`}>
                                    {active && <Check className="w-3 h-3 inline mr-0.5"/>}
                                    {p.name || code}
                                  </button>
                              );
                            })}
                          </div>
                      )}
                    </div>
                );
              })}
              {Object.keys(filteredGrouped).length === 0 && (
                  <div className="p-6 text-center text-sm text-gray-400">未找到匹配的权限</div>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-gray-100 dark:border-gray-800">
            <button onClick={onClose}
                    className="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors">
              取消
            </button>
            <button onClick={() => submitMut.mutate()} disabled={submitMut.isPending}
                    className="px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-xl transition-all shadow-lg shadow-blue-500/25 disabled:opacity-50 inline-flex items-center gap-2">
              {submitMut.isPending ? <><Loader className="w-4 h-4 animate-spin"/>保存中...</> : <><Check
                  className="w-4 h-4"/>{mode === 'create' ? '创建角色' : '保存更改'}</>}
            </button>
          </div>
        </div>
      </Modal>
  );
}

/* ═══════════════════════════════════════════════════════
   Users Modal - Show users with this role
   ═══════════════════════════════════════════════════════ */
function UsersModal({roleId, roleName, onClose}: {roleId: number; roleName: string; onClose: () => void}) {
  const {data: users, isLoading} = useQuery({
    queryKey: ['admin-role-users', roleId],
    queryFn: async () => {
      const res = await apiClient.get('/api/v2/dashboard/user-management/users', {per_page: 100});
      if (!res.success || !res.data) return [];
      return Array.isArray(res.data) ? res.data : (res.data.users || []);
    },
  });
  const assigned = (users || []).filter((u) =>
    u.roles?.some((r) => r.id === roleId)
  );

  return (
      <Modal open={true} onClose={onClose} title={`${roleName} 的用户`}
             subtitle={`共 ${assigned.length} 个用户拥有此角色`}>
        {isLoading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center gap-3 p-3">
                    <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full"/>
                    <div className="space-y-1.5 flex-1">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-lg w-24"/>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-lg w-32"/>
                    </div>
                  </div>
              ))}
            </div>
        ) : assigned.length === 0 ? (
            <div className="text-center py-8">
              <div
                  className="w-14 h-14 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-3">
                <Users className="w-7 h-7 text-gray-300 dark:text-gray-600"/>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">暂无用户拥有此角色</p>
            </div>
        ) : (
            <div className="space-y-2">
              {assigned.map((u) => {
                const initial = u.username?.[0]?.toUpperCase() || '?';
                const colors = ['from-blue-500 to-cyan-500', 'from-purple-500 to-pink-500', 'from-emerald-500 to-teal-500', 'from-amber-500 to-orange-500', 'from-rose-500 to-red-500'];
                const colorIdx = (u.id || 0) % colors.length;
                return (
                    <div key={u.id}
                         className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                      <div
                          className={`w-10 h-10 rounded-full bg-gradient-to-br ${colors[colorIdx]} flex items-center justify-center text-sm font-bold text-white shadow-sm`}>
                        {initial}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{u.username}</p>
                        <p className="text-xs text-gray-400 truncate">{u.email || '-'}</p>
                      </div>
                      {u.is_active !== false ? (
                          <span
                              className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-full text-[10px] font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"/>活跃
                  </span>
                      ) : (
                          <span
                            className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 rounded-full text-[10px] font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400"/>禁用
                  </span>
                      )}
                    </div>
                );
              })}
            </div>
        )}
      </Modal>
  );
}

/* ═══════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════ */
function RolesInner() {
  const qc = useQueryClient();
  const [modal, setModal] = useState<{mode: 'create' | 'edit'; role?: any} | null>(null);
  const [usersModal, setUsersModal] = useState<{id: number; name: string} | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const {data: roles, isLoading} = useQuery({
    queryKey: ['admin-roles'],
    queryFn: async () => {
      const res = await apiClient.get('/api/v2/security/rbac/roles');
      return res.success && res.data ? (Array.isArray(res.data) ? res.data : res.data.roles || []) : [];
    },
  });

  const {data: permissions} = useQuery({
    queryKey: ['admin-permissions'],
    queryFn: async () => {
      const res = await apiClient.get('/api/v2/security/rbac/permissions');
      return res.success && res.data ? (Array.isArray(res.data) ? res.data : res.data.permissions || []) : [];
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/security/rbac/roles/${id}`),
    onSuccess: (res: any) => {
      if (!res.success) return;
      qc.invalidateQueries({queryKey: ['admin-roles']});
      setDeleteTarget(null);
    },
  });

  // Filtered roles
  const filteredRoles = useMemo(() => {
    if (!roles) return [];
    if (!searchQuery) return roles;
    const q = searchQuery.toLowerCase();
    return roles.filter((r) =>
        r.name?.toLowerCase().includes(q) || r.slug?.toLowerCase().includes(q) || r.description?.toLowerCase().includes(q)
    );
  }, [roles, searchQuery]);

  // Stats
  const stats = useMemo(() => ({
    totalRoles: roles?.length || 0,
    systemRoles: roles?.filter((r) => r.is_system).length || 0,
    customRoles: roles?.filter((r) => !r.is_system).length || 0,
    totalPermissions: permissions?.length || 0,
    totalUsers: roles?.reduce((sum, r) => sum + (r.user_count || 0), 0) || 0,
  }), [roles, permissions]);

  return (
      <AdminShell title="角色权限" actions={
        <button onClick={() => setModal({mode: 'create'})}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-sm font-medium rounded-xl transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40">
          <Plus className="w-4 h-4"/>新建角色
        </button>
      }>
        {/* ═══ Stats Cards ═══ */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard icon={Shield} label="总角色数" value={stats.totalRoles} gradient="from-blue-500 to-cyan-500"/>
          <StatCard icon={Crown} label="系统角色" value={stats.systemRoles} gradient="from-purple-500 to-pink-500"/>
          <StatCard icon={Key} label="权限总数" value={stats.totalPermissions} gradient="from-amber-500 to-orange-500"/>
          <StatCard icon={UserCheck} label="用户分配" value={stats.totalUsers} gradient="from-emerald-500 to-teal-500"/>
        </div>

        {/* ═══ Roles Table ═══ */}
        <div
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
            <SectionTitle icon={Shield} title="角色列表"
                          subtitle={`共 ${stats.totalRoles} 个角色，${stats.totalPermissions} 项权限`}
                          action={
                            <div className="relative">
                              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                              <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                                     placeholder="搜索角色..."
                                     className="pl-9 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 w-56 transition-all"/>
                            </div>
                          }
            />
          </div>

          {isLoading ? (
              <RolesSkeleton/>
          ) : filteredRoles.length === 0 ? (
              <EmptyState icon={Shield} title={searchQuery ? '未找到匹配的角色' : '暂无角色'}
                          desc={searchQuery ? '尝试其他搜索关键词' : '创建您的第一个角色来管理权限'}
                          action={!searchQuery && (
                              <button onClick={() => setModal({mode: 'create'})}
                                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl transition-colors">
                                <Plus className="w-4 h-4"/>新建角色
                              </button>
                          )}
              />
          ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50/80 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                  <tr>
                    <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">角色</th>
                    <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden sm:table-cell">标识</th>
                    <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">权限</th>
                    <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">用户</th>
                    <th className="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">操作</th>
                  </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 dark:divide-gray-800/50">
                  {filteredRoles.map((r) => (
                      <tr key={r.id} className="group hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-sm ${
                                r.is_system
                                    ? 'bg-gradient-to-br from-purple-500 to-pink-500'
                                    : 'bg-gradient-to-br from-blue-500 to-cyan-500'
                            }`}>
                              {r.is_system ? <Crown className="w-5 h-5 text-white"/> :
                                  <Shield className="w-5 h-5 text-white"/>}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-gray-900 dark:text-white">{r.name}</span>
                                {r.is_system && (
                                    <span
                                        className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded text-[10px] font-semibold">
                                <Lock className="w-2.5 h-2.5"/>系统
                              </span>
                                )}
                              </div>
                              {r.description &&
                                  <p className="text-xs text-gray-400 mt-0.5 truncate max-w-[200px]">{r.description}</p>}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 hidden sm:table-cell">
                          <code
                              className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded-lg font-mono text-gray-600 dark:text-gray-400">{r.slug}</code>
                        </td>
                        <td className="px-6 py-4">
                      <span
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg text-xs font-medium">
                        <Key className="w-3 h-3"/>{r.permission_count || 0}
                      </span>
                    </td>
                        <td className="px-6 py-4 hidden md:table-cell">
                      <button onClick={() => setUsersModal({id: r.id, name: r.name})}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors">
                        <Users className="w-3 h-3"/>{r.user_count || 0}
                      </button>
                    </td>
                        <td className="px-6 py-4 text-right">
                          <div
                              className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => setModal({
                              mode: 'edit',
                              role: {...r, permission_codes: r.permission_codes || []}
                            })}
                                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl transition-colors"
                                    title="编辑权限">
                              <Edit className="w-4 h-4"/>
                            </button>
                            {!r.is_system && (
                                <button onClick={() => setDeleteTarget(r)}
                                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors"
                                        title="删除">
                            <Trash2 className="w-4 h-4"/>
                          </button>
                            )}
                          </div>
                    </td>
                  </tr>
                  ))}
                  </tbody>
                </table>
              </div>
          )}
        </div>

        {/* ═══ Modals ═══ */}
        {modal && <RoleModal mode={modal.mode} role={modal.role} permissions={permissions || []}
                             onClose={() => setModal(null)}/>}
        {usersModal &&
            <UsersModal roleId={usersModal.id} roleName={usersModal.name} onClose={() => setUsersModal(null)}/>}

        {/* Delete Confirm */}
        <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="确认删除">
          {deleteTarget && (
              <DeleteConfirm
                  role={deleteTarget}
                  onConfirm={() => deleteMut.mutate(deleteTarget.id)}
                  onCancel={() => setDeleteTarget(null)}
                  isPending={deleteMut.isPending}
              />
        )}
        </Modal>
      </AdminShell>
  );
}

export default function AdminRoles() {
  return <AuthGuard><QueryProvider><RolesInner/></QueryProvider></AuthGuard>;
}
