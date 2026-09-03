/**
 * 虚拟列表组件 - 优化长列表渲染性能
 *
 * 支持：
 * - 固定行高模式（性能最优）
 * - 动态行高模式（预估 + 动态测量）
 * - 底部加载触发
 *
 * 使用方式：
 * ```tsx
 * // 固定行高
 * <VirtualList items={items} itemHeight={60} renderItem={...} />
 *
 * // 动态行高
 * <VirtualList items={items} estimateHeight={80} renderItem={...} />
 *
 * // 带无限滚动
 * <VirtualList items={items} itemHeight={60} renderItem={...}
 *   onLoadMore={loadMore} hasMore={hasMore} loadingMore={loading} />
 * ```
 */

'use client';

import React, {useCallback, useEffect, useRef, useState, useMemo} from 'react';

export interface VirtualListProps<T> {
  /** 数据项 */
  items: T[];
  /** 列表总高度（容器高度） */
  height: number;
  /** 固定行高（模式下使用） */
  itemHeight?: number;
  /** 预估行高（动态模式下使用） */
  estimateHeight?: number;
  /** 每项额外填充 */
  itemPadding?: number;
  /** 渲染单个项 */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** 列表宽度 */
  width?: number | string;
  /** 数据为空时渲染 */
  emptyComponent?: React.ReactNode;
  /** 滚动容器 className */
  className?: string;
  /** 是否启用动态高度测量 */
  dynamic?: boolean;
  /** 加载下一页回调 */
  onLoadMore?: () => void;
  /** 是否还有更多数据 */
  hasMore?: boolean;
  /** 是否正在加载更多 */
  loadingMore?: boolean;
  /** item key 获取函数 */
  keyExtractor?: (item: T, index: number) => string;
}

interface ItemMeasure {
  height: number;
  measured: boolean;
}

export function VirtualList<T = any>({
  items,
  height,
  itemHeight = 60,
  estimateHeight,
  itemPadding = 0,
  renderItem,
  width = '100%',
  emptyComponent,
  className = '',
  dynamic = false,
  onLoadMore,
  hasMore = false,
  loadingMore = false,
  keyExtractor = (_, i) => String(i),
}: VirtualListProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const measureRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const [scrollTop, setScrollTop] = useState(0);
  // 动态模式下存储每项实际高度
  const [measures, setMeasures] = useRef<Map<number, ItemMeasure>>(new Map()).current;

  const effectiveHeight = estimateHeight || itemHeight;

  // 计算偏移量表（动态模式下用于精确定位）
  const offsets = useMemo(() => {
    const result: number[] = [0];
    for (let i = 0; i < items.length; i++) {
      const m = measures.get(i);
      const h = (m?.measured ? m.height : effectiveHeight) + itemPadding;
      result.push(result[i] + h);
    }
    return result;
  }, [items.length, measures, effectiveHeight, itemPadding]);

  // 计算可见范围
  const {startIdx, endIdx, offsetY} = useMemo(() => {
    const buffer = 5;
    const visibleHeight = height;

    // 二分查找起始索引
    let lo = 0, hi = items.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (offsets[mid] < scrollTop) {
        lo = mid + 1;
      } else {
        hi = mid;
      }
    }

    const start = Math.max(0, lo - buffer);
    let end = start + Math.ceil(visibleHeight / effectiveHeight) + buffer * 2;
    if (end > items.length) end = items.length;

    const offset = start > 0 ? offsets[start] : 0;

    return {startIdx: start, endIdx: end, offsetY: offset};
  }, [scrollTop, items.length, height, effectiveHeight, offsets]);

  // 测量真实高度（动态模式）
  const setMeasureRef = useCallback((el: HTMLDivElement | null, index: number) => {
    if (!el) {
      measureRefs.current.delete(index);
      return;
    }
    measureRefs.current.set(index, el);

    if (dynamic) {
      requestAnimationFrame(() => {
        const h = el.offsetHeight;
        const existing = measures.get(index);
        if (!existing || !existing.measured || existing.height !== h) {
          measures.set(index, {height: h, measured: true});
          setScrollTop((prev: number) => prev); // 触发重新计算
        }
      });
    }
  }, [dynamic, measures]);

  // 滚动处理
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const st = e.currentTarget.scrollTop;
    setScrollTop(st);

    // 无限滚动：接近底部时触发
    if (onLoadMore && hasMore && !loadingMore) {
      const {scrollHeight, clientHeight} = e.currentTarget;
      if (st + clientHeight >= scrollHeight - 200) {
        onLoadMore();
      }
    }
  }, [onLoadMore, hasMore, loadingMore]);

  if (!items.length) {
    return (
      <div className={className} style={{height, width}}>
        {emptyComponent || (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            暂无数据
          </div>
        )}
      </div>
    );
  }

  const totalHeight = offsets[offsets.length - 1];
  const visibleItems = items.slice(startIdx, endIdx);

  return (
    <div
      ref={containerRef}
      className={`overflow-auto ${className}`}
      style={{height, width}}
      onScroll={handleScroll}
    >
      <div style={{height: totalHeight, position: 'relative', width: '100%'}}>
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map((item, sliceIdx) => {
            const realIdx = startIdx + sliceIdx;
            return (
              <div
                key={keyExtractor(item, realIdx)}
                ref={(el) => setMeasureRef(el, realIdx)}
              >
                {renderItem(item, realIdx)}
              </div>
            );
          })}
        </div>
      </div>
      {loadingMore && (
        <div className="flex justify-center py-3 text-sm text-gray-400">
          <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-blue-500 rounded-full"/>
        </div>
      )}
    </div>
  );
}

/** 简化版：固定行高的虚拟列表 Hook */
export function useVirtualList<T = any>({
  items,
  itemHeight,
  containerHeight,
}: {
  items: T[];
  itemHeight: number;
  containerHeight: number;
}) {
  const [scrollTop, setScrollTop] = useState(0);
  const totalHeight = items.length * itemHeight;

  const visibleItems = useMemo(() => {
    const startIdx = Math.max(0, Math.floor(scrollTop / itemHeight) - 2);
    const visibleCount = Math.ceil(containerHeight / itemHeight) + 4;
    const endIdx = Math.min(items.length, startIdx + visibleCount);

    return {
      startIdx,
      endIdx,
      items: items.slice(startIdx, endIdx),
      offsetY: startIdx * itemHeight,
    };
  }, [scrollTop, items, itemHeight, containerHeight]);

  const onScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {visibleItems, totalHeight, onScroll};
}