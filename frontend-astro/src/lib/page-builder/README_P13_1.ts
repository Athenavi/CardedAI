/**
 * ============================================================================
 * P13-1: 块嵌套功能实现指南
 * ============================================================================
 *
 * 本模块实现了 PageBuilder 的块嵌套功能，支持 Column > Paragraph > Image 等复杂布局。
 *
 * 核心文件：
 * 1. nested-blocks.ts - 类型定义和块规则
 * 2. NestedSortableBlock.tsx - 可嵌套块组件
 * 3. nested-dnd.ts - 拖拽管理工具
 *
 * 使用示例：
 *
 * ```typescript
 * import { NestedBlock, BLOCK_DEFINITIONS } from '@/lib/page-builder/nested-blocks';
 * import { NestedSortableBlock } from '@/components/pages/admin/NestedSortableBlock';
 * import { deleteBlockByPath, updateBlockByPath } from '@/lib/page-builder/nested-dnd';
 *
 * // 1. 创建嵌套块结构
 * const blocks: NestedBlock[] = [
 *   {
 *     id: 'block_1',
 *     type: 'column-container',
 *     data: { columns: 2 },
 *     children: [
 *       {
 *         id: 'block_2',
 *         type: 'column',
 *         data: { width: '50%' },
 *         children: [
 *           { id: 'block_3', type: 'heading', data: { text: '标题' } },
 *           { id: 'block_4', type: 'paragraph', data: { text: '内容' } }
 *         ]
 *       }
 *     ]
 *   }
 * ];
 *
 * // 2. 渲染嵌套块
 * <NestedSortableBlock
 *   block={blocks[0]}
 *   index={0}
 *   path="0"
 *   onDelete={(path) => setBlocks(deleteBlockByPath(blocks, path))}
 *   onUpdateBlock={(path, updates) => setBlocks(updateBlockByPath(blocks, path, updates))}
 * />
 *
 * // 3. 检查块的嵌套规则
 * canAddBlockToParent('paragraph', 'column'); // true
 * canParentAcceptChild('column', 'heading', 2); // true (如果 maxChildren > 2)
 * ```
 *
 * 关键特性：
 *
 * 1. **嵌套规则系统**
 *    - 每个块类型定义了 allowedParents 和 allowedChildren
 *    - 自动验证嵌套合法性，防止无效结构
 *    - 支持最大子块数量限制（maxChildren）
 *
 * 2. **路径寻址**
 *    - 使用点分路径（如 "0.1.2"）唯一标识嵌套块
 *    - 支持在任意层级查找、更新、删除块
 *    - 拖拽排序时自动更新路径
 *
 * 3. **递归渲染**
 *    - NestedSortableBlock 组件递归渲染子块
 *    - 每层嵌套增加缩进和深度标记
 *    - 样式独立配置，不相互影响
 *
 * 4. **拖拽支持**
 *    - 同级别块可以拖拽排序
 *    - 跨级别拖拽需要特殊处理（需监听 over 事件检测目标父块，见下方待实现功能）
 *    - 拖拽时显示视觉反馈（透明度变化）
 *
 * 待实现功能：
 *
 * - [ ] 跨级别拖拽（将块从一个父块移动到另一个父块）
 * - [ ] 可视化子块选择器（点击"+"按钮时弹出）
 * - [ ] 嵌套块的实时预览（右侧预览区渲染嵌套结构）
 * - [ ] 撤销/重做历史栈（P13-5）
 * - [ ] 块模式库（P13-3，预建嵌套布局组合）
 *
 * 性能优化建议：
 *
 * 1. 对于深层嵌套（>5层），考虑虚拟化渲染
 * 2. 使用 React.memo 避免不必要的重渲染
 * 3. 拖拽时使用 requestAnimationFrame 优化流畅度
 * 4. 大型页面考虑分页加载块列表
 *
 * 兼容性说明：
 *
 * - convertFlatBlocksToNested() 可将旧的扁平结构转换为嵌套结构
 * - convertNestedBlocksToFlat() 可将嵌套结构转换回扁平结构（用于 API 存储）
 * - 后端 API 无需修改，只需调整序列化/反序列化逻辑
 *
 * ============================================================================
 */

export {}; // 仅作为文档
