/**
 * P13-1: 嵌套块拖拽管理工具
 *
 * 提供在嵌套结构中查找、更新、删除块的工具函数
 */

import type {NestedBlock} from '@/lib/page-builder/nested-blocks';

/**
 * P13-1: 根据路径查找块
 * @param blocks 块列表
 * @param path 路径（如 "0.1.2"）
 * @returns 找到的块及其父块引用
 */
export function findBlockByPath(
    blocks: NestedBlock[],
    path: string
): { block: NestedBlock; parent: NestedBlock | null; index: number } | null {
    const indices = path.split('.').map(Number);

    let currentBlocks = blocks;
    let parent: NestedBlock | null = null;
    let currentBlock: NestedBlock | null = null;

    for (let i = 0; i < indices.length; i++) {
        const index = indices[i];

        if (index >= currentBlocks.length) {
            return null;
        }

        currentBlock = currentBlocks[index];

        if (i === indices.length - 1) {
            // 到达目标块
            return {
                block: currentBlock,
                parent,
                index
            };
        }

        // 继续深入子块
        if (currentBlock.children) {
            parent = currentBlock;
            currentBlocks = currentBlock.children;
        } else {
            return null;
        }
    }

    return null;
}

/**
 * P13-1: 根据路径删除块
 * @param blocks 块列表
 * @param path 路径
 * @returns 更新后的块列表
 */
export function deleteBlockByPath(blocks: NestedBlock[], path: string): NestedBlock[] {
    const indices = path.split('.').map(Number);
    const newBlocks = [...blocks];

    // 如果是根级别
    if (indices.length === 1) {
        newBlocks.splice(indices[0], 1);
        return newBlocks;
    }

    // 递归删除子块
    const parentPath = indices.slice(0, -1).join('.');
    const result = findBlockByPath(newBlocks, parentPath);

    if (result && result.block.children) {
        result.block.children = [...result.block.children];
        result.block.children.splice(indices[indices.length - 1], 1);
    }

    return newBlocks;
}

/**
 * P13-1: 根据路径更新块
 * @param blocks 块列表
 * @param path 路径
 * @param updates 更新内容
 * @returns 更新后的块列表
 */
export function updateBlockByPath(
    blocks: NestedBlock[],
    path: string,
    updates: Partial<NestedBlock>
): NestedBlock[] {
    const indices = path.split('.').map(Number);
    const newBlocks = [...blocks];

    // 如果是根级别
    if (indices.length === 1) {
        newBlocks[indices[0]] = {...newBlocks[indices[0]], ...updates};
        return newBlocks;
    }

    // 递归更新子块
    const parentPath = indices.slice(0, -1).join('.');
    const result = findBlockByPath(newBlocks, parentPath);

    if (result && result.block.children) {
        const childIndex = indices[indices.length - 1];
        result.block.children = [...result.block.children];
        result.block.children[childIndex] = {
            ...result.block.children[childIndex],
            ...updates
        };
    }

    return newBlocks;
}

/**
 * P13-1: 在指定路径的块中添加子块
 * @param blocks 块列表
 * @param parentPath 父块路径
 * @param newBlock 新块
 * @returns 更新后的块列表
 */
export function addChildBlock(
    blocks: NestedBlock[],
    parentPath: string,
    newBlock: NestedBlock
): NestedBlock[] {
    const result = findBlockByPath(blocks, parentPath);

    if (!result) {
        return blocks;
    }

    const newBlocks = [...blocks];
    const targetBlock = findBlockByPath(newBlocks, parentPath);

    if (targetBlock) {
        targetBlock.block.children = [
            ...(targetBlock.block.children || []),
            newBlock
        ];
    }

    return newBlocks;
}

/**
 * P13-1: 移动块（拖拽排序）
 * @param blocks 块列表
 * @param fromPath 源路径
 * @param toPath 目标路径
 * @returns 更新后的块列表
 */
export function moveBlock(
    blocks: NestedBlock[],
    fromPath: string,
    toPath: string
): NestedBlock[] {
    // 首先找到并移除源块
    const fromResult = findBlockByPath(blocks, fromPath);
    if (!fromResult) {
        return blocks;
    }

    const movedBlock = {...fromResult.block};
    let newBlocks = deleteBlockByPath(blocks, fromPath);

    // 然后插入到目标位置
    const toIndices = toPath.split('.').map(Number);

    // 如果目标是根级别
    if (toIndices.length === 1) {
        newBlocks.splice(toIndices[0], 0, movedBlock);
        return newBlocks;
    }

    // 插入到子块中
    const parentPath = toIndices.slice(0, -1).join('.');
    const targetResult = findBlockByPath(newBlocks, parentPath);

    if (targetResult && targetResult.block.children) {
        targetResult.block.children = [...targetResult.block.children];
        targetResult.block.children.splice(toIndices[toIndices.length - 1], 0, movedBlock);
    }

    return newBlocks;
}

/**
 * P13-1: 计算块的总数量（包括所有子块）
 * @param blocks 块列表
 * @returns 总数量
 */
export function countTotalBlocks(blocks: NestedBlock[]): number {
    let count = 0;

    for (const block of blocks) {
        count += 1;
        if (block.children && block.children.length > 0) {
            count += countTotalBlocks(block.children);
        }
    }

    return count;
}

/**
 * P13-1: 获取块的最大嵌套深度
 * @param blocks 块列表
 * @param currentDepth 当前深度
 * @returns 最大深度
 */
export function getMaxDepth(blocks: NestedBlock[], currentDepth: number = 0): number {
    let maxDepth = currentDepth;

    for (const block of blocks) {
        if (block.children && block.children.length > 0) {
            const childDepth = getMaxDepth(block.children, currentDepth + 1);
            maxDepth = Math.max(maxDepth, childDepth);
        }
    }

    return maxDepth;
}
