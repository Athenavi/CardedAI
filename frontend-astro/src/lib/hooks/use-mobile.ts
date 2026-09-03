/**
 * 移动端检测 Hook
 *
 * 提供设备类型、屏幕尺寸、触摸支持等信息。
 * 服务端渲染兼容（返回默认值）。
 */

import {useEffect, useState, useCallback} from 'react';

export interface MobileInfo {
  /** 是否为移动设备（宽度 < 768px） */
  isMobile: boolean;
  /** 是否为平板设备（768px ~ 1024px） */
  isTablet: boolean;
  /** 是否为桌面端（>= 1024px） */
  isDesktop: boolean;
  /** 设备是否支持触摸 */
  hasTouch: boolean;
  /** 当前视口宽度 */
  viewportWidth: number;
  /** 当前视口高度 */
  viewportHeight: number;
  /** 是否为 iOS */
  isIOS: boolean;
  /** 是否为 Android */
  isAndroid: boolean;
  /** 是否为 Safari */
  isSafari: boolean;
  /** 是否为低端设备（内存/处理器受限） */
  isLowEnd: boolean;
}

const DEFAULT_INFO: MobileInfo = {
  isMobile: false,
  isTablet: false,
  isDesktop: true,
  hasTouch: false,
  viewportWidth: 0,
  viewportHeight: 0,
  isIOS: false,
  isAndroid: false,
  isSafari: false,
  isLowEnd: false,
};

function getMobileInfo(): MobileInfo {
  if (typeof window === 'undefined' || typeof navigator === 'undefined') {
    return DEFAULT_INFO;
  }

  const width = window.innerWidth;
  const height = window.innerHeight;
  const ua = navigator.userAgent;

  return {
    isMobile: width < 768,
    isTablet: width >= 768 && width < 1024,
    isDesktop: width >= 1024,
    hasTouch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    viewportWidth: width,
    viewportHeight: height,
    isIOS: /iPad|iPhone|iPod/.test(ua) || (ua.includes('Mac') && navigator.maxTouchPoints > 0),
    isAndroid: /Android/.test(ua),
    isSafari: /Safari/.test(ua) && !/Chrome/.test(ua),
    // 低端设备判断：内存 < 4GB 或 连接速度慢
    isLowEnd: (navigator as any).deviceMemory ? (navigator as any).deviceMemory < 4 : false,
  };
}

/**
 * 移动端检测 Hook
 * @param breakpoint 自定义移动断点，默认 768px
 */
export function useMobile(breakpoint = 768) {
  const [info, setInfo] = useState<MobileInfo>(getMobileInfo());

  useEffect(() => {
    const handleResize = useCallback(() => {
      setInfo(getMobileInfo());
    }, []);

    // 使用 passive listener 提升滚动性能
    window.addEventListener('resize', handleResize, {passive: true});

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return info;
}

/**
 * 简化的移动端判断（仅返回布尔值）
 * @param breakpoint 自定义移动断点，默认 768px
 */
export function useIsMobile(breakpoint = 768): boolean {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < breakpoint : false
  );

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < breakpoint);
    window.addEventListener('resize', handleResize, {passive: true});
    return () => window.removeEventListener('resize', handleResize);
  }, [breakpoint]);

  return isMobile;
}