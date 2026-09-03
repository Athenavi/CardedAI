/**
 * 响应式检测 Hook
 *
 * 提供：
 * - 设备类型检测（手机/平板/桌面）
 * - 屏幕方向检测
 * - 视口高度监控（处理移动端键盘弹出）
 * - 高度变化回调
 * - 配色方案检测
 * - 运动偏好检测（无障碍）
 */

import {useEffect, useState, useCallback} from 'react';

export interface ResponsiveInfo {
  /** 设备宽度 */
  width: number;
  /** 设备高度（含键盘弹出时自动更新） */
  height: number;
  /** 是否为横屏 */
  isLandscape: boolean;
  /** 屏幕方向 */
  orientation: 'portrait' | 'landscape';
  /** 是否为手机 */
  isPhone: boolean;
  /** 是否为平板 */
  isTablet: boolean;
  /** 是否为深色模式 */
  prefersDark: boolean;
  /** 是否偏好减少动效 */
  prefersReducedMotion: boolean;
  /** 是否高对比度模式 */
  prefersHighContrast: boolean;
  /** 视口可见高度（键盘弹出时会变化） */
  visualViewportHeight: number;
  /** 视口可见宽度 */
  visualViewportWidth: number;
  /** 是否有键盘弹出（高度突然减小） */
  isKeyboardVisible: boolean;
  /** DPR (设备像素比) */
  dpr: number;
}

function getResponsiveInfo(): ResponsiveInfo {
  if (typeof window === 'undefined') {
    return {
      width: 0,
      height: 0,
      isLandscape: false,
      orientation: 'portrait',
      isPhone: false,
      isTablet: false,
      prefersDark: false,
      prefersReducedMotion: false,
      prefersHighContrast: false,
      visualViewportHeight: 0,
      visualViewportWidth: 0,
      isKeyboardVisible: false,
      dpr: 1,
    };
  }

  const width = window.innerWidth;
  const height = window.innerHeight;
  const vv = (window as any).visualViewport;
  const vvHeight = vv ? vv.height : height;
  const vvWidth = vv ? vv.width : width;

  // 键盘检测：可见视口高度比预期小显著
  const heightDiff = height - vvHeight;
  const isKeyboardVisible = heightDiff > 150;

  return {
    width,
    height: vvHeight,
    isLandscape: width > height,
    orientation: width > height ? 'landscape' : 'portrait',
    isPhone: width < 768 && /mobi|android/i.test(navigator.userAgent || ''),
    isTablet: width >= 768 && width < 1024,
    prefersDark: window.matchMedia('(prefers-color-scheme: dark)').matches,
    prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    prefersHighContrast: window.matchMedia('(prefers-contrast: more)').matches,
    visualViewportHeight: vvHeight,
    visualViewportWidth: vvWidth,
    isKeyboardVisible,
    dpr: window.devicePixelRatio || 1,
  };
}

/**
 * 响应式信息 Hook
 */
export function useResponsive() {
  const [info, setInfo] = useState<ResponsiveInfo>(getResponsiveInfo());

  useEffect(() => {
    const handleResize = () => setInfo(getResponsiveInfo());

    // visualViewport change 事件（处理键盘弹出）
    const handleVisualViewportChange = () => setInfo(getResponsiveInfo());

    // 方向变化
    const handleOrientationChange = () => setInfo(getResponsiveInfo());

    // 配色方案变化
    const darkMQ = window.matchMedia('(prefers-color-scheme: dark)');
    const darkHandler = () => setInfo(getResponsiveInfo());
    if (darkMQ.addEventListener) {
      darkMQ.addEventListener('change', darkHandler);
    } else if (darkMQ.addListener) {
      // Legacy
      darkMQ.addListener(darkHandler);
    }

    window.addEventListener('resize', handleResize, {passive: true});
    window.addEventListener('orientationchange', handleOrientationChange, {passive: true});
    (window as any).visualViewport?.addEventListener('resize', handleVisualViewportChange, {passive: true});

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
      (window as any).visualViewport?.removeEventListener('resize', handleVisualViewportChange);
      if (darkMQ.removeEventListener) {
        darkMQ.removeEventListener('change', darkHandler);
      } else if (darkMQ.removeListener) {
        darkMQ.removeListener(darkHandler);
      }
    };
  }, []);

  return info;
}

/**
 * 仅获取视口高度（含键盘检测）
 */
export function useViewportHeight(): { height: number; isKeyboardVisible: boolean } {
  const [state, setState] = useState(() => {
    const vv = (typeof window !== 'undefined' && (window as any).visualViewport);
    return {
      height: vv ? vv.height : window.innerHeight,
      isKeyboardVisible: false,
    };
  });

  useEffect(() => {
    const handleResize = () => {
      const fullHeight = window.innerHeight;
      const vv = (window as any).visualViewport;
      const vvHeight = vv ? vv.height : fullHeight;
      setState({
        height: vvHeight,
        isKeyboardVisible: fullHeight - vvHeight > 150,
      });
    };

    window.addEventListener('resize', handleResize, {passive: true});
    (window as any).visualViewport?.addEventListener('resize', handleResize, {passive: true});
    return () => {
      window.removeEventListener('resize', handleResize);
      (window as any).visualViewport?.removeEventListener('resize', handleResize);
    };
  }, []);

  return state;
}