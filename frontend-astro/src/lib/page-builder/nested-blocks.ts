/**
 * P13-1: 块嵌套功能 - 嵌套块类型定义
 *
 * 支持 Column > Paragraph > Image 等嵌套结构
 */

export interface NestedBlock {
    id: string; // 唯一标识（用于 dnd-kit）
    type: string; // 块类型
    data: any; // 块数据
    styles?: Record<string, any>; // 样式配置
    children?: NestedBlock[]; // 子块（嵌套支持）
    preview_html?: string; // 预览 HTML
}

export interface BlockDefinition {
    name: string;
    category: string;
    description: string;
    icon: string;
    allowedParents?: string[]; // 允许的父块类型（空表示可在根级别）
    allowedChildren?: string[]; // 允许的子块类型（空表示不允许嵌套）
    maxChildren?: number; // 最大子块数量
    defaultData: any;
}

// P13-1: 预定义块类型及其嵌套规则
export const BLOCK_DEFINITIONS: BlockDefinition[] = [
    // 容器块（可嵌套）
    {
        name: 'column-container',
        category: 'layout',
        description: '列容器 - 可包含多个列',
        icon: 'Grid',
        allowedParents: [], // 可在根级别
        allowedChildren: ['column'], // 只允许 column 作为直接子元素
        maxChildren: 6,
        defaultData: {columns: 2, gap: 16}
    },
    {
        name: 'column',
        category: 'layout',
        description: '单列 - 可包含内容块',
        icon: 'Layout',
        allowedParents: ['column-container'], // 只能在 column-container 内
        allowedChildren: ['paragraph', 'heading', 'image', 'video', 'button', 'cta-section'],
        maxChildren: undefined, // 无限制
        defaultData: {width: '50%', alignment: 'left'}
    },

    // 内容块（不可嵌套或有限嵌套）
    {
        name: 'paragraph',
        category: 'content',
        description: '段落文本',
        icon: 'Type',
        allowedParents: ['column', 'hero-section', 'features-grid', 'testimonials', 'team-members'],
        allowedChildren: [], // 不允许嵌套
        maxChildren: 0,
        defaultData: {text: '在此输入文本...', fontSize: 16, lineHeight: 1.6}
    },
    {
        name: 'heading',
        category: 'content',
        description: '标题',
        icon: 'Type',
        allowedParents: ['column', 'hero-section', 'cta-section', 'faq-section'],
        allowedChildren: [],
        maxChildren: 0,
        defaultData: {text: '标题文本', level: 2, align: 'center'}
    },
    {
        name: 'image',
        category: 'media',
        description: '图片',
        icon: 'ImageIcon',
        allowedParents: ['column', 'hero-section', 'features-grid', 'testimonials', 'team-members'],
        allowedChildren: [],
        maxChildren: 0,
        defaultData: {src: '', alt: '', caption: '', borderRadius: 8}
    },
    {
        name: 'video',
        category: 'media',
        description: '视频',
        icon: 'Video',
        allowedParents: ['column', 'hero-section'],
        allowedChildren: [],
        maxChildren: 0,
        defaultData: {src: '', autoplay: false, controls: true}
    },
    {
        name: 'button',
        category: 'interactive',
        description: '按钮',
        icon: 'DollarSign',
        allowedParents: ['column', 'hero-section', 'cta-section'],
        allowedChildren: [],
        maxChildren: 0,
        defaultData: {text: '点击我', url: '#', variant: 'primary', size: 'md'}
    },

    // 营销组件（可包含简单嵌套）
    {
        name: 'hero-section',
        category: 'marketing',
        description: 'Hero 区域',
        icon: 'Star',
        allowedParents: [],
        allowedChildren: ['heading', 'paragraph', 'button', 'image'],
        maxChildren: 5,
        defaultData: {backgroundColor: '#f0f9ff', padding: 64}
    },
    {
        name: 'features-grid',
        category: 'marketing',
        description: '特性网格',
        icon: 'Grid',
        allowedParents: [],
        allowedChildren: ['heading', 'paragraph', 'image'],
        maxChildren: 12,
        defaultData: {columns: 3, gap: 24}
    },
    {
        name: 'cta-section',
        category: 'marketing',
        description: '行动号召区域',
        icon: 'MessageSquare',
        allowedParents: [],
        allowedChildren: ['heading', 'paragraph', 'button'],
        maxChildren: 4,
        defaultData: {backgroundColor: '#1e40af', textColor: '#ffffff'}
    },
    {
        name: 'testimonials',
        category: 'marketing',
        description: '客户评价',
        icon: 'Users',
        allowedParents: [],
        allowedChildren: ['heading', 'paragraph', 'image'],
        maxChildren: 6,
        defaultData: {layout: 'grid', columns: 2}
    },
    {
        name: 'faq-section',
        category: 'marketing',
        description: '常见问题',
        icon: 'HelpCircle',
        allowedParents: [],
        allowedChildren: ['heading', 'paragraph'],
        maxChildren: 20,
        defaultData: {accordion: true}
    },
    {
        name: 'team-members',
        category: 'marketing',
        description: '团队成员',
        icon: 'Users',
        allowedParents: [],
        allowedChildren: ['heading', 'paragraph', 'image'],
        maxChildren: 12,
        defaultData: {columns: 4, showSocial: true}
    },
    {
        name: 'contact-form',
        category: 'marketing',
        description: '联系表单',
        icon: 'Mail',
        allowedParents: [],
        allowedChildren: [],
        maxChildren: 0,
        defaultData: {fields: ['name', 'email', 'message']}
    }
];

/**
 * P13-1: 检查块是否可以添加到指定父块中
 */
export function canAddBlockToParent(
    childType: string,
    parentType: string | null // null 表示根级别
): boolean {
    const childDef = BLOCK_DEFINITIONS.find(b => b.name === childType);
    if (!childDef) return false;

    // 检查子块是否允许该父块
    if (parentType === null) {
        return childDef.allowedParents?.length === 0 || childDef.allowedParents?.includes('root') || !childDef.allowedParents;
    }

    return childDef.allowedParents?.includes(parentType) || false;
}

/**
 * P13-1: 检查父块是否可以接受该子块类型
 */
export function canParentAcceptChild(
    parentType: string,
    childType: string,
    currentChildrenCount: number
): boolean {
    const parentDef = BLOCK_DEFINITIONS.find(b => b.name === parentType);
    if (!parentDef) return false;

    // 检查父块是否允许该子块类型
    if (parentDef.allowedChildren && !parentDef.allowedChildren.includes(childType)) {
        return false;
    }

    // 检查最大子块数量限制
    if (parentDef.maxChildren !== undefined && currentChildrenCount >= parentDef.maxChildren) {
        return false;
    }

    return true;
}

/**
 * P13-1: 生成唯一块 ID
 */
export function generateBlockId(): string {
    return `block_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * P13-1: 将扁平块列表转换为嵌套结构（向后兼容）
 */
export function convertFlatBlocksToNested(flatBlocks: any[]): NestedBlock[] {
    return flatBlocks.map((block, index) => ({
        id: block.id || generateBlockId(),
        type: block.type,
        data: block.data,
        styles: block.styles,
        preview_html: block.preview_html,
        children: block.children ? convertFlatBlocksToNested(block.children) : []
    }));
}

/**
 * P13-1: 将嵌套块列表转换为扁平结构（用于 API 存储）
 */
export function convertNestedBlocksToFlat(nestedBlocks: NestedBlock[]): any[] {
    return nestedBlocks.map(block => ({
        id: block.id,
        type: block.type,
        data: block.data,
        styles: block.styles,
        preview_html: block.preview_html,
        children: block.children && block.children.length > 0
            ? convertNestedBlocksToFlat(block.children)
            : undefined
    }));
}
