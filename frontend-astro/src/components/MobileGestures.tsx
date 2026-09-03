/**
 * 移动端手势组件 - React 岛屿
 *
 * 优化项：
 * - 使用 passive 触摸监听提升滚动性能
 * - 添加触摸阈值防抖（避免误触）
 * - 支持双击前进/后退
 * - 减少不必要的重渲染
 */

'use client';

import {useEffect, useRef, useCallback} from 'react';

interface GestureOptions {
  /** 左滑返回阈值 (px)，默认 80 */
  threshold?: number;
  /** 左边缘触发区域 (px)，默认 50 */
  edgeZone?: number;
  /** 是否启用双击返回，默认 false */
  enableDoubleTapBack?: boolean;
}

const MobileGestures = ({
  threshold = 80,
  edgeZone = 50,
  enableDoubleTapBack = false,
}: GestureOptions = {}) => {
  const touchStartX = useRef(0);
  const touchStartY = useRef(0);
  const touchStartTime = useRef(0);
  const lastTapTime = useRef(0);

  const handleTouchStart = useCallback((e: TouchEvent) => {
    const touch = e.touches[0];
    touchStartX.current = touch.clientX;
    touchStartY.current = touch.clientY;
    touchStartTime.current = Date.now();
  }, []);

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchStartX.current;
    const deltaY = touch.clientY - touchStartY.current;
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);
    const elapsed = Date.now() - touchStartTime.current;

    // 快速滑动才触发（时间 < 300ms）
    if (elapsed > 300) return;

    // 右滑返回（在屏幕左边缘，水平滑动 > 垂直滑动）
    if (
      deltaX > threshold &&
      absDeltaX > absDeltaY &&
      touchStartX.current < edgeZone &&
      absDeltaX > threshold
    ) {
      window.history.back();
    }

    // 双击返回（可选）
    if (enableDoubleTapBack) {
      const now = Date.now();
      if (now - lastTapTime.current < 300) {
        // 双击判定：两次坐标相近且水平滑动小
        if (absDeltaX < 30 && absDeltaY < 30) {
          const canGoBack = window.history.length > 1;
          canGoBack ? window.history.back() : window.history.forward();
        }
      }
      lastTapTime.current = now;
    }
  }, [threshold, edgeZone, enableDoubleTapBack]);

  useEffect(() => {
    // 使用 passive: true 提升滚动性能，避免主线程阻塞
    window.addEventListener('touchstart', handleTouchStart, {passive: true});
    window.addEventListener('touchend', handleTouchEnd, {passive: true});

    return () => {
      window.removeEventListener('touchstart', handleTouchStart);
      window.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchEnd]);

  return null;
};

export default MobileGestures;
