/**
 * P13-1: 可嵌套块组件
 *
 * 支持 Column > Paragraph > Image 等嵌套结构
 * 使用 dnd-kit 实现拖拽排序和嵌套拖拽
 */

import {useState} from 'react';
import {useSortable} from '@dnd-kit/sortable';
import {CSS} from '@dnd-kit/utilities';
import {Edit3, GripVertical, Plus, Trash2} from 'lucide-react';
import type {NestedBlock} from '@/lib/page-builder/nested-blocks';
import {BLOCK_DEFINITIONS} from '@/lib/page-builder/nested-blocks';

interface NestedSortableBlockProps {
    block: NestedBlock;
    index: number;
    path: string; // 块的路径（用于唯一标识，如 "0.1.2"）
    onDelete: (path: string) => void;
    onAddChild?: (parentPath: string, childType: string) => void;
    onUpdateBlock?: (path: string, updates: Partial<NestedBlock>) => void;
    depth?: number; // 当前嵌套深度
}

export function NestedSortableBlock({
                                        block,
                                        index,
                                        path,
                                        onDelete,
                                        onAddChild,
                                        onUpdateBlock,
                                        depth = 0
                                    }: NestedSortableBlockProps) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({id: path});

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
        marginLeft: depth > 0 ? `${depth * 24}px` : 0, // 嵌套缩进
    };

    const blockDef = BLOCK_DEFINITIONS.find(b => b.name === block.type);
  const __Icon = blockDef?.icon || 'Layout';
    const [showStyleEditor, setShowStyleEditor] = useState(false);
  const [showChildPicker, setShowChildPicker] = useState(false);
    const [blockStyles, setBlockStyles] = useState(block.styles || {});

    // P13-1: 样式可视化控制器
    const handleStyleChange = (key: string, value: any) => {
        const newStyles = {...blockStyles, [key]: value};
        setBlockStyles(newStyles);
        if (onUpdateBlock) {
            onUpdateBlock(path, {styles: newStyles});
        }
    };

    // P13-1: 检查是否可以添加子块
    const canAddChildren = blockDef?.allowedChildren && blockDef.allowedChildren.length > 0;
    const maxChildrenReached = blockDef?.maxChildren !== undefined &&
        (block.children?.length || 0) >= blockDef.maxChildren;

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`border rounded-lg p-4 hover:shadow-md transition bg-white dark:bg-gray-800 relative group ${
                depth > 0 ? 'mt-2' : ''
            }`}
        >
            {/* 拖拽手柄 */}
            <div
                {...attributes}
                {...listeners}
                className="absolute left-2 top-1/2 -translate-y-1/2 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition"
            >
                <GripVertical className="w-5 h-5 text-gray-400"/>
            </div>

            <div className="ml-8">
                {/* 块头部 */}
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{block.type}</span>
                        {depth > 0 && (
                            <span className="text-xs text-gray-400">(嵌套层级 {depth})</span>
                        )}
                    </div>
                    <div className="flex items-center gap-1">
                      {/* 添加子块按钮 + 类型选择器 */}
                        {canAddChildren && !maxChildrenReached && onAddChild && (
                          <div className="relative">
                            <button
                              onClick={() => setShowChildPicker(!showChildPicker)}
                              className="p-1.5 text-gray-400 hover:text-green-600 transition"
                              title="添加子块"
                            >
                              <Plus className="w-4 h-4"/>
                            </button>

                            {/* 子块类型选择器弹出菜单 */}
                            {showChildPicker && blockDef?.allowedChildren && (
                              <div
                                className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg py-1 min-w-[140px]">
                                {blockDef.allowedChildren.map((childType) => {
                                  const childDef = BLOCK_DEFINITIONS.find(b => b.name === childType);
                                  return (
                                    <button
                                      key={childType}
                                      onClick={() => {
                                        onAddChild(path, childType);
                                        setShowChildPicker(false);
                                      }}
                                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-600 transition flex items-center gap-2"
                                    >
                                      <span
                                        className="text-gray-700 dark:text-gray-300">{childDef?.description || childType}</span>
                                    </button>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        )}

                        {/* 样式编辑器 */}
                        <button
                            onClick={() => setShowStyleEditor(!showStyleEditor)}
                            className="p-1.5 text-gray-400 hover:text-purple-600 transition"
                            title="样式编辑器"
                        >
                            <Edit3 className="w-4 h-4"/>
                        </button>

                        {/* 删除按钮 */}
                        <button
                            onClick={() => onDelete(path)}
                            className="p-1.5 text-gray-400 hover:text-red-600 transition"
                        >
                            <Trash2 className="w-4 h-4"/>
                        </button>
                    </div>
                </div>

                {/* P13-1: 样式控制器面板 */}
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

                {/* 块数据预览 */}
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    {JSON.stringify(block.data, null, 2).slice(0, 200)}...
                </div>

                {/* P13-1: 子块列表（递归渲染） */}
                {block.children && block.children.length > 0 && (
                    <div className="mt-3 pl-4 border-l-2 border-blue-200 dark:border-blue-800">
                        <div className="text-xs text-gray-400 mb-2">
                            子块 ({block.children.length})
                        </div>
                        {block.children.map((child, childIndex) => (
                            <NestedSortableBlock
                                key={child.id}
                                block={child}
                                index={childIndex}
                                path={`${path}.${childIndex}`}
                                onDelete={onDelete}
                                onAddChild={onAddChild}
                                onUpdateBlock={onUpdateBlock}
                                depth={depth + 1}
                            />
                        ))}
                    </div>
                )}

                {/* 空子块提示 */}
                {canAddChildren && (!block.children || block.children.length === 0) && (
                    <div
                        className="mt-3 p-3 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-lg text-center">
                        <p className="text-xs text-gray-400">
                            此块可以包含子块，点击"+"按钮添加
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
