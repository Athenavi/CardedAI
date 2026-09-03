/**
 * 页面切换动画组件
 *
 * 使用 CSS transform 实现 GPU 加速的非阻塞动画。
 * 支持：淡入/滑入/缩放 过渡。
 * 移动设备自动降级为淡入（减少计算量）。
 *
 * 使用方式：
 * ```tsx
 * <PageTransition>
 *   <YourPage />
 * </PageTransition>
 * ```
 */

'use client';

import React, {useEffect, useState, useCallback, useMemo} from 'react';
import {useIsMobile} from '@/lib/hooks/use-mobile';
import {useResponsive} from '@/lib/hooks/use-responsive';

export interface PageTransitionProps {
  children: React.ReactNode;
  /** 过渡类型 */
  mode?: 'fade' | 'slide' | 'scale';
  /** 持续时间 ms */
  duration?: number;
  /** 延迟 ms */
  delay?: number;
  /** key 变化时触发重新过渡 */
  key?: string;
}

export const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  mode = 'fade',
  duration = 200,
  delay = 0,
  key: forceKey,
}) => {
  const [visible, setVisible] = useState(false);
  const isMobile = useIsMobile();
  const {prefersReducedMotion} = useResponsive();

  // 移动设备或减少动效偏好时自动降级
  const effectiveMode = useMemo(() => {
    if (prefersReducedMotion || isMobile) return 'fade';
    return mode;
  }, [mode, isMobile, prefersReducedMotion]);

  const handleAnimationEnd = useCallback(() => {
    setVisible(true);
  }, []);

  useEffect(() => {
    setVisible(false);
    const timer = setTimeout(() => {
      setVisible(true);
    }, delay);
    return () => clearTimeout(timer);
  }, [forceKey, delay]);

  // 根据模式选择 CSS classes（使用 CSS transform，实现 GPU 加速）
  const animationClass = useMemo(() => {
    if (prefersReducedMotion) return 'opacity-100';

    if (!visible) {
      switch (effectiveMode) {
        case 'slide':
          return 'opacity-0 translate-y-4';
        case 'scale':
          return 'opacity-0 scale-[0.98]';
        default:
          return 'opacity-0';
      }
    }
    return '';
  }, [visible, effectiveMode, prefersReducedMotion]);

  // 使用内联 style 确保 transition 不被 Tailwind 覆盖
  const transitionStyle: React.CSSProperties = useMemo(() => ({
    transition: `opacity ${duration}ms ease, transform ${duration}ms ease`,
    willChange: 'opacity, transform',
  }), [duration]);

  return (
    <div
      className={`${animationClass} ${visible ? 'opacity-100 translate-y-0 scale-100' : ''}`}
      style={transitionStyle}
      onAnimationEnd={handleAnimationEnd}
    >
      {children}
    </div>
  );
};

/**
 * 带骨架屏的页面切换组件
 */
export const PageTransitionWithSkeleton: React.FC<
  PageTransitionProps & { skeleton?: React.ReactNode }
> = ({children, skeleton, ...props}) => {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(false);
    const timer = setTimeout(() => setReady(true), props.delay || 0);
    return () => clearTimeout(timer);
  }, [props.key, props.delay]);

  if (!ready) {
    return skeleton || (
      <div className="p-8 space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-1/4"/>
        <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2"/>
        <div className="h-40 bg-gray-200 dark:bg-gray-800 rounded"/>
      </div>
    );
  }

  return <PageTransition {...props}>{children}</PageTransition>;
};

export default PageTransition;