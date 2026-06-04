import {useState} from 'react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
// P6-1: 集成 dnd-kit 实现拖拽排序
import {DndContext, PointerSensor, useSensor, useSensors, closestCenter} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    verticalListSortingStrategy,
    useSortable,
} from '@dnd-kit/sortable';
import {CSS} from '@dnd-kit/utilities';
import {
  Layout,
  Plus,
  Save,
  Eye,
  Trash2,
  Edit3,
  GripVertical,
  Image as ImageIcon,
  Video,
  Grid,
  Star,
  MessageSquare,
  DollarSign,
  HelpCircle,
  Users,
  Mail,
  Monitor,
  Smartphone,
  Tablet
} from 'lucide-react';

interface PageData {
    id: number;
    title: string;
    slug: string;
    blocks_data: any[];
    template_name?: string;
    is_published: boolean;
    created_at?: string;
    updated_at?: string;
}

interface ComponentTemplate {
    name: string;
    category: string;
    description: string;
    preview_html: string;
    default_data: any;
}

const COMPONENT_ICONS: Record<string, any> = {
    'hero-section': Star,
    'features-grid': Grid,
    'cta-section': MessageSquare,
    'testimonials': Users,
    'pricing-table': DollarSign,
    'faq-section': HelpCircle,
    'team-members': Users,
    'contact-form': Mail
};

// P6-1: 可排序块组件（支持拖拽）
function SortableBlock({
                           block,
                           index,
                           onDelete,
                       }: {
    block: any;
    index: number;
    onDelete: (index: number) => void;
}) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({id: index});

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    const Icon = COMPONENT_ICONS[block.type] || Layout;
    const [showStyleEditor, setShowStyleEditor] = useState(false);
    const [blockStyles, setBlockStyles] = useState(block.styles || {});

    // P6-3: 样式可视化控制器
    const handleStyleChange = (key: string, value: any) => {
        const newStyles = {...blockStyles, [key]: value};
        setBlockStyles(newStyles);
        // 实际项目中需要同步到父组件
    };

    return (
        <div ref={setNodeRef} style={style}
             className="border rounded-lg p-4 hover:shadow-md transition bg-white dark:bg-gray-800 relative group">
            {/* 拖拽手柄 */}
            <div {...attributes} {...listeners}
                 className="absolute left-2 top-1/2 -translate-y-1/2 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition">
                <GripVertical className="w-5 h-5 text-gray-400"/>
            </div>

            <div className="ml-8">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-blue-600"/>
                        <span className="text-sm font-medium">{block.type}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <button
                            onClick={() => setShowStyleEditor(!showStyleEditor)}
                            className="p-1.5 text-gray-400 hover:text-purple-600 transition"
                            title="样式编辑器"
                        >
                            <Edit3 className="w-4 h-4"/>
                        </button>
                        <button
                            onClick={() => onDelete(index)}
                            className="p-1.5 text-gray-400 hover:text-red-600 transition"
                        >
                            <Trash2 className="w-4 h-4"/>
                        </button>
                    </div>
                </div>

                {/* P6-3: 样式控制器面板 */}
                {showStyleEditor && (
                    <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-xs text-gray-500 dark:text-gray-400 block mb-1">背景色</label>
                                <input
                                    type="color"
                                    value={blockStyles.backgroundColor || '#ffffff'}
                                    onChange={(e) => handleStyleChange('backgroundColor', e.target.value)}
                                    className="w-full h-8 rounded cursor-pointer"
                                />
                            </div>
                            <div>
                              <label className="text-xs text-gray-500 dark:text-gray-400 block mb-1">文字色</label>
                                <input
                                    type="color"
                                    value={blockStyles.color || '#000000'}
                                    onChange={(e) => handleStyleChange('color', e.target.value)}
                                    className="w-full h-8 rounded cursor-pointer"
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                            <div>
                              <label className="text-xs text-gray-500 dark:text-gray-400 block mb-1">Padding</label>
                                <input
                                    type="number"
                                    value={blockStyles.padding || 16}
                                    onChange={(e) => handleStyleChange('padding', parseInt(e.target.value))}
                                    className="w-full px-2 py-1 border rounded text-sm"
                                />
                            </div>
                            <div>
                              <label className="text-xs text-gray-500 dark:text-gray-400 block mb-1">Margin</label>
                                <input
                                    type="number"
                                    value={blockStyles.margin || 0}
                                    onChange={(e) => handleStyleChange('margin', parseInt(e.target.value))}
                                    className="w-full px-2 py-1 border rounded text-sm"
                                />
                            </div>
                            <div>
                              <label className="text-xs text-gray-500 dark:text-gray-400 block mb-1">圆角</label>
                                <input
                                    type="number"
                                    value={blockStyles.borderRadius || 8}
                                    onChange={(e) => handleStyleChange('borderRadius', parseInt(e.target.value))}
                                    className="w-full px-2 py-1 border rounded text-sm"
                                />
                            </div>
                        </div>
                    </div>
                )}

              <div className="text-xs text-gray-500 dark:text-gray-400">
                    {JSON.stringify(block.data, null, 2).slice(0, 200)}...
                </div>
            </div>
        </div>
    );
}

function PageBuilderInner() {
  const toast = useToast();
    const qc = useQueryClient();
    const [selectedPage, setSelectedPage] = useState<PageData | null>(null);
    const [editingBlocks, setEditingBlocks] = useState<any[]>([]);
    const [showComponentLibrary, setShowComponentLibrary] = useState(false);
    // P6-2: split-view 实时预览（移除手动切换模式）
    const [previewDevice, setPreviewDevice] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');

    // P6-1: 配置拖拽传感器
    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8, // 8px 移动后激活拖拽
            },
        })
    );

    // P6-1: 拖拽结束处理
    const handleDragEnd = (event: any) => {
        const {active, over} = event;

        if (over && active.id !== over.id) {
            setEditingBlocks((items) => {
                const oldIndex = active.id;
                const newIndex = over.id;
                return arrayMove(items, oldIndex, newIndex);
            });
        }
    };

    // 查询页面列表
    const {data: pages, isLoading: pagesLoading} = useQuery({
        queryKey: ['page-builder-pages'],
        queryFn: async () => {
            const res = await apiClient.get('/page-builder/pages');
            return res.data || [];
        }
    });

    // 查询组件模板
    const {data: components} = useQuery({
        queryKey: ['component-templates'],
        queryFn: async () => {
            const res = await apiClient.get('/components/templates');
            return res.data || [];
        }
    });

    // 创建页面
    const createPageMut = useMutation({
        mutationFn: (data: { title: string; slug: string }) =>
            apiClient.post('/page-builder/pages', {
                ...data,
                blocks_data: [],
                is_published: false
            }),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['page-builder-pages']});
        }
    });

    // 保存页面
    const savePageMut = useMutation({
        mutationFn: ({id, blocks}: { id: number; blocks: any[] }) =>
            apiClient.put(`/page-builder/pages/${id}`, {blocks_data: blocks}),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['page-builder-pages']});
          toast.success('页面已保存！');
        }
    });

    // 发布页面
    const publishMut = useMutation({
        mutationFn: (id: number) => apiClient.post(`/page-builder/pages/${id}/publish`),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['page-builder-pages']});
          toast.success('页面已发布！');
        }
    });

    // 删除页面
  const __deleteMut = useMutation({
        mutationFn: (id: number) => apiClient.delete(`/page-builder/pages/${id}`),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['page-builder-pages']});
            setSelectedPage(null);
        }
    });

    const handleCreatePage = () => {
        const title = prompt('页面标题:');
        if (!title) return;

        const slug = title.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
        createPageMut.mutate({title, slug});
    };

    // P6-4: 从模板创建页面
    const handleCreateFromTemplate = async (templateId: string) => {
        const title = prompt('页面标题:');
        if (!title) return;

        const slug = title.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
        try {
          const __res = await apiClient.post('/page-builder/pages/from-template', {
                template_id: templateId,
                title,
                slug
            });
            qc.invalidateQueries({queryKey: ['page-builder-pages']});
            setShowComponentLibrary(false);
          toast.success('页面创建成功！');
        } catch (error) {
          toast.error('创建失败：' + ((error as any).response?.data?.detail || '未知错误'));
        }
    };

    const handleEditPage = (page: PageData) => {
        setSelectedPage(page);
        setEditingBlocks(page.blocks_data || []);
    };

    const handleAddComponent = (component: ComponentTemplate) => {
        setEditingBlocks([...editingBlocks, {
            type: component.name,
            data: component.default_data,
            preview_html: component.preview_html
        }]);
        setShowComponentLibrary(false);
    };

    const handleDeleteBlock = (index: number) => {
        setEditingBlocks(editingBlocks.filter((_, i) => i !== index));
    };

    const handleSave = () => {
        if (!selectedPage) return;
        savePageMut.mutate({id: selectedPage.id, blocks: editingBlocks});
    };

    const handlePublish = () => {
        if (!selectedPage) return;
        handleSave();
        setTimeout(() => publishMut.mutate(selectedPage.id), 500);
    };

    // P6-2: 响应式预览宽度
    const getPreviewWidth = () => {
        switch (previewDevice) {
            case 'mobile':
                return 'max-w-[375px]';
            case 'tablet':
                return 'max-w-[768px]';
            default:
                return 'max-w-4xl';
        }
    };

    return (
        <AdminShell title="页面构建器">
            <div className="flex gap-6 h-[calc(100vh-200px)]">
                {/* 左侧：页面列表 */}
                <div className="w-64 bg-white dark:bg-gray-900 rounded-xl border overflow-hidden flex flex-col">
                    <div className="px-4 py-3 border-b flex items-center justify-between">
                        <h3 className="font-semibold text-sm">页面列表</h3>
                        <button
                            onClick={handleCreatePage}
                            className="p-1.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-600 rounded-lg transition"
                            title="新建页面"
                        >
                            <Plus className="w-4 h-4"/>
                        </button>
                    </div>

                    {pagesLoading ? (
                        <div className="p-4 text-center text-sm text-gray-400">加载中...</div>
                    ) : !pages?.length ? (
                        <div className="p-4 text-center text-sm text-gray-400">暂无页面</div>
                    ) : (
                        <div className="flex-1 overflow-y-auto divide-y">
                            {pages.map((page: PageData) => (
                                <div
                                    key={page.id}
                                    onClick={() => handleEditPage(page)}
                                    className={`px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition ${
                                        selectedPage?.id === page.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                                    }`}
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm font-medium truncate">{page.title}</span>
                                        {page.is_published && (
                                            <span
                                              className="text-[10px] px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">已发布</span>
                                        )}
                                    </div>
                                    <div className="text-xs text-gray-400 font-mono truncate">/{page.slug}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* P6-2: 中间编辑区 + 右侧预览区 split-view */}
                <div className="flex-1 flex gap-4">
                    {/* 编辑区 */}
                    <div className="flex-1 bg-white dark:bg-gray-900 rounded-xl border overflow-hidden flex flex-col">
                        {!selectedPage ? (
                            <div className="flex-1 flex items-center justify-center text-gray-400">
                                <div className="text-center">
                                    <Layout className="w-16 h-16 mx-auto mb-4 opacity-30"/>
                                    <p>选择一个页面开始编辑</p>
                                </div>
                            </div>
                        ) : (
                            <>
                                {/* 工具栏 */}
                                <div className="px-4 py-3 border-b flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-semibold">{selectedPage.title}</h3>
                                        <span className="text-xs text-gray-400 font-mono">/{selectedPage.slug}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => setShowComponentLibrary(true)}
                                            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-1.5"
                                        >
                                            <Plus className="w-4 h-4"/>
                                            添加组件
                                        </button>
                                        <button
                                            onClick={handleSave}
                                            disabled={savePageMut.isPending}
                                            className="px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition flex items-center gap-1.5"
                                        >
                                            <Save className="w-4 h-4"/>
                                            保存
                                        </button>
                                        <button
                                            onClick={handlePublish}
                                            disabled={!selectedPage || publishMut.isPending}
                                            className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                                        >
                                            发布
                                        </button>
                                    </div>
                                </div>

                                {/* P6-1: 拖拽排序编辑区 */}
                                <div className="flex-1 overflow-y-auto p-6">
                                    <DndContext
                                        sensors={sensors}
                                        collisionDetection={closestCenter}
                                        onDragEnd={handleDragEnd}
                                    >
                                        <SortableContext
                                            items={editingBlocks.map((_, index) => index)}
                                            strategy={verticalListSortingStrategy}
                                        >
                                            <div className="max-w-4xl mx-auto space-y-4">
                                                {editingBlocks.map((block, index) => (
                                                    <SortableBlock
                                                        key={index}
                                                        block={block}
                                                        index={index}
                                                        onDelete={handleDeleteBlock}
                                                    />
                                                ))}
                                                {editingBlocks.length === 0 && (
                                                    <div
                                                        className="text-center py-12 border-2 border-dashed rounded-lg">
                                                        <Layout className="w-12 h-12 mx-auto mb-3 text-gray-300"/>
                                                        <p className="text-gray-400 mb-3">拖拽组件到这里或点击"添加组件"</p>
                                                        <button
                                                            onClick={() => setShowComponentLibrary(true)}
                                                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                                                        >
                                                            浏览组件库
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </SortableContext>
                                    </DndContext>
                                </div>
                            </>
                        )}
                    </div>

                    {/* P6-2: 实时预览区 */}
                    {selectedPage && (
                        <div
                            className="w-[500px] bg-gray-50 dark:bg-gray-950 rounded-xl border overflow-hidden flex flex-col">
                            <div
                                className="px-4 py-3 border-b flex items-center justify-between bg-white dark:bg-gray-900">
                                <h3 className="font-semibold text-sm">实时预览</h3>
                                {/* 响应式切换按钮 */}
                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={() => setPreviewDevice('desktop')}
                                        className={`p-1.5 rounded ${previewDevice === 'desktop' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
                                        title="桌面端"
                                    >
                                        <Monitor className="w-4 h-4"/>
                                    </button>
                                    <button
                                        onClick={() => setPreviewDevice('tablet')}
                                        className={`p-1.5 rounded ${previewDevice === 'tablet' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
                                        title="平板端"
                                    >
                                        <Tablet className="w-4 h-4"/>
                                    </button>
                                    <button
                                        onClick={() => setPreviewDevice('mobile')}
                                        className={`p-1.5 rounded ${previewDevice === 'mobile' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
                                        title="移动端"
                                    >
                                        <Smartphone className="w-4 h-4"/>
                                    </button>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto p-4">
                                <div
                                  className={`${getPreviewWidth()} mx-auto bg-white dark:bg-gray-900 shadow-lg rounded-lg min-h-[600px] p-6`}>
                                    {editingBlocks.map((block, index) => (
                                        <div key={index} className="mb-4">
                                            <div
                                                dangerouslySetInnerHTML={{__html: block.preview_html || `<div class="p-4 bg-gray-50 text-center text-gray-400">${block.type} 预览</div>`}}/>
                                        </div>
                                    ))}
                                    {editingBlocks.length === 0 && (
                                        <div className="text-center py-12 text-gray-400">
                                            <p>添加组件后将在此处显示预览</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 组件库对话框 */}
            {showComponentLibrary && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div
                        className="bg-white dark:bg-gray-900 rounded-2xl max-w-5xl w-full max-h-[80vh] overflow-hidden flex flex-col">
                        <div className="px-6 py-4 border-b flex items-center justify-between">
                            <h3 className="font-semibold text-lg">选择组件或模板</h3>
                            <button
                                onClick={() => setShowComponentLibrary(false)}
                                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                            >
                                ✕
                            </button>
                        </div>

                        {/* P6-4: 模板分类标签 */}
                        <div className="px-6 py-3 border-b bg-gray-50 dark:bg-gray-800">
                            <div className="flex gap-2 text-sm">
                                <span className="font-medium text-gray-700 dark:text-gray-300">快速开始：</span>
                                <button className="text-blue-600 hover:underline">全部</button>
                              <button className="text-gray-500 dark:text-gray-400 hover:text-blue-600">营销</button>
                              <button className="text-gray-500 dark:text-gray-400 hover:text-blue-600">企业</button>
                              <button className="text-gray-500 dark:text-gray-400 hover:text-blue-600">博客</button>
                              <button className="text-gray-500 dark:text-gray-400 hover:text-blue-600">作品集</button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6">
                            {/* P6-4: 预建模板区 */}
                            <div className="mb-6">
                                <h4 className="text-sm font-semibold mb-3 text-gray-700 dark:text-gray-300">📄
                                    预建页面模板（一键导入）</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                  {components?.filter((c) => c.id).map((template) => {
                                        const Icon = COMPONENT_ICONS[template.blocks?.[0]?.type] || Layout;
                                        return (
                                            <div
                                                key={template.id}
                                                className="border rounded-xl p-4 hover:border-green-600 hover:shadow-md cursor-pointer transition bg-gradient-to-br from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20"
                                            >
                                                <div className="flex items-start justify-between mb-2">
                                                    <div className="flex items-center gap-2">
                                                        <Icon className="w-5 h-5 text-green-600"/>
                                                        <span className="font-medium text-sm">{template.name}</span>
                                                    </div>
                                                    <span
                                                      className="text-[10px] px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">{template.category}</span>
                                                </div>
                                              <p
                                                className="text-xs text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">{template.description}</p>
                                                <button
                                                    onClick={() => handleCreateFromTemplate(template.id)}
                                                    className="w-full px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition"
                                                >
                                                    使用此模板
                                                </button>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* 组件库区 */}
                            <div>
                                <h4 className="text-sm font-semibold mb-3 text-gray-700 dark:text-gray-300">🧩
                                    单个组件（添加到当前页面）</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                  {components?.filter((c) => !c.id).map((comp: ComponentTemplate) => {
                                        const Icon = COMPONENT_ICONS[comp.name] || Layout;
                                        return (
                                            <div
                                                key={comp.name}
                                                onClick={() => handleAddComponent(comp)}
                                                className="border rounded-xl p-4 hover:border-blue-600 hover:shadow-md cursor-pointer transition"
                                            >
                                                <div className="flex items-center gap-2 mb-2">
                                                    <Icon className="w-5 h-5 text-blue-600"/>
                                                    <span className="font-medium">{comp.name}</span>
                                                </div>
                                              <p
                                                className="text-xs text-gray-500 dark:text-gray-400 mb-3">{comp.description}</p>
                                                <div className="text-[10px] text-gray-400">分类: {comp.category}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </AdminShell>
    );
}

export default function PageBuilder() {
    return (
        <AuthGuard>
            <QueryProvider>
                <PageBuilderInner/>
            </QueryProvider>
        </AuthGuard>
    );
}
