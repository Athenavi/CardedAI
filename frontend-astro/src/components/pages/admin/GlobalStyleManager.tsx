/**
 * P13-2: 全局样式管理器组件
 *
 * 提供一键切换全站配色方案、字体/间距配置、样式预设库选择功能
 */

import {useState} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {STYLE_PRESETS, GlobalStyleConfig, applyGlobalStyle} from '@/lib/page-builder/global-styles';
import {Palette, Save, Eye, Trash2, Check} from 'lucide-react';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';

interface GlobalStyleManagerProps {
    onClose?: () => void;
}

export function GlobalStyleManager({onClose}: GlobalStyleManagerProps) {
  const confirm = useConfirm();
  const toast = useToast();
    const qc = useQueryClient();
  const [_selectedPreset, _setSelectedPreset] = useState<string | null>(null);
    const [showPreview, setShowPreview] = useState(false);

    // 查询已保存的样式配置
    const {data: savedConfigs, isLoading} = useQuery({
        queryKey: ['global-style-configs'],
        queryFn: async () => {
            const res = await apiClient.get('/page-builder/global-styles');
            return res.data || [];
        }
    });

    // 激活样式配置
    const activateMut = useMutation({
        mutationFn: (id: number) => apiClient.post(`/page-builder/global-styles/${id}/activate`),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['global-style-configs']});
          toast.success('样式配置已激活！');
        }
    });

    // 删除样式配置
    const deleteMut = useMutation({
        mutationFn: (id: number) => apiClient.delete(`/page-builder/global-styles/${id}`),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['global-style-configs']});
          toast.success('样式配置已删除！');
        }
    });

    // 从预设创建配置
    const createFromPreset = async (presetSlug: string) => {
        const preset = STYLE_PRESETS.find(p => p.slug === presetSlug);
        if (!preset) return;

        try {
            await apiClient.post('/page-builder/global-styles', {
                name: preset.name,
                slug: `${preset.slug}-${Date.now()}`,
                theme_type: preset.theme_type,
                color_scheme: preset.color_scheme,
                typography: preset.typography,
                spacing: preset.spacing,
                border_radius: preset.border_radius,
                shadows: preset.shadows,
                breakpoints: preset.breakpoints
            });
            qc.invalidateQueries({queryKey: ['global-style-configs']});
          toast.success('样式配置已创建！');
        } catch (error) {
          toast.error('创建失败：' + ((error as any).response?.data?.detail || '未知错误'));
        }
    };

    // P13-2: 预览样式
    const handlePreview = (config: GlobalStyleConfig) => {
        applyGlobalStyle(config);
        setShowPreview(true);
        setTimeout(() => {
            // 恢复当前激活的样式
            const activeConfig = savedConfigs?.find((c: GlobalStyleConfig) => c.is_active);
            if (activeConfig) {
                applyGlobalStyle(activeConfig);
            }
            setShowPreview(false);
        }, 3000); // 3秒后恢复
    };

    return (
        <div className="space-y-6">
            {/* 头部 */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Palette className="w-5 h-5 text-blue-600"/>
                    <h3 className="font-semibold text-lg">全局样式系统</h3>
                </div>
                {onClose && (
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                        ✕
                    </button>
                )}
            </div>

            {/* 样式预设库 */}
            <div>
                <h4 className="text-sm font-semibold mb-3 text-gray-700 dark:text-gray-300">
                    📚 样式预设库（点击使用）
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {STYLE_PRESETS.map((preset) => (
                        <div
                            key={preset.slug}
                            className="border rounded-xl p-4 hover:border-blue-600 hover:shadow-md cursor-pointer transition bg-white dark:bg-gray-900"
                        >
                            {/* 预览色块 */}
                            <div className="mb-3 h-20 rounded-lg overflow-hidden flex">
                                <div
                                    className="flex-1"
                                    style={{backgroundColor: preset.color_scheme.background}}
                                />
                                <div
                                    className="flex-1"
                                    style={{backgroundColor: preset.color_scheme.primary}}
                                />
                                <div
                                    className="flex-1"
                                    style={{backgroundColor: preset.color_scheme.accent}}
                                />
                            </div>

                            <div className="flex items-start justify-between mb-2">
                                <span className="font-medium text-sm">{preset.name}</span>
                                <span
                                  className="text-[10px] px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full capitalize">
                                    {preset.theme_type}
                                </span>
                            </div>

                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                                {preset.typography.font_family.split(',')[0]}
                            </p>

                            <div className="flex gap-2">
                                <button
                                    onClick={() => createFromPreset(preset.slug)}
                                    className="flex-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition"
                                >
                                    使用此预设
                                </button>
                                <button
                                    onClick={() => handlePreview(preset as GlobalStyleConfig)}
                                    className="px-3 py-1.5 border text-xs rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                                    title="预览3秒"
                                >
                                    <Eye className="w-4 h-4"/>
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 已保存的配置 */}
            <div>
                <h4 className="text-sm font-semibold mb-3 text-gray-700 dark:text-gray-300">
                    💾 已保存的配置
                </h4>

                {isLoading ? (
                    <div className="text-center py-8 text-gray-400">加载中...</div>
                ) : !savedConfigs?.length ? (
                    <div className="text-center py-8 text-gray-400 border-2 border-dashed rounded-lg">
                        <Palette className="w-12 h-12 mx-auto mb-3 opacity-30"/>
                        <p>尚未保存任何样式配置</p>
                        <p className="text-xs mt-1">从上方预设库创建您的第一个配置</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {savedConfigs.map((config: GlobalStyleConfig) => (
                            <div
                                key={config.id}
                                className={`border rounded-lg p-4 flex items-center justify-between ${
                                    config.is_active
                                        ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                                        : 'bg-white dark:bg-gray-900'
                                }`}
                            >
                                <div className="flex items-center gap-3">
                                    {/* 颜色预览 */}
                                    <div className="flex gap-1">
                                        <div
                                            className="w-6 h-6 rounded"
                                            style={{backgroundColor: config.color_scheme.primary}}
                                        />
                                        <div
                                            className="w-6 h-6 rounded"
                                            style={{backgroundColor: config.color_scheme.accent}}
                                        />
                                        <div
                                            className="w-6 h-6 rounded"
                                            style={{backgroundColor: config.color_scheme.background}}
                                        />
                                    </div>

                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium text-sm">{config.name}</span>
                                            {config.is_active && (
                                                <span
                                                  className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full flex items-center gap-1">
                                                    <Check className="w-3 h-3"/>
                                                    当前启用
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-xs text-gray-400">
                                            {config.theme_type} • {config.typography.font_family.split(',')[0]}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-2">
                                    {!config.is_active && (
                                        <>
                                            <button
                                                onClick={() => handlePreview(config)}
                                                className="p-2 text-gray-400 hover:text-blue-600 transition"
                                                title="预览"
                                            >
                                                <Eye className="w-4 h-4"/>
                                            </button>
                                            <button
                                                onClick={() => activateMut.mutate(config.id)}
                                                className="p-2 text-gray-400 hover:text-green-600 transition"
                                                title="激活"
                                            >
                                                <Save className="w-4 h-4"/>
                                            </button>
                                        </>
                                    )}
                                    <button
                                      onClick={async () => {
                                        if (await confirm({message: '确定要删除此样式配置吗？', variant: 'danger'})) {
                                                deleteMut.mutate(config.id);
                                            }
                                        }}
                                        className="p-2 text-gray-400 hover:text-red-600 transition"
                                        title="删除"
                                    >
                                        <Trash2 className="w-4 h-4"/>
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* 预览提示 */}
            {showPreview && (
                <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg">
                    预览模式（3秒后自动恢复）
                </div>
            )}
        </div>
    );
}
