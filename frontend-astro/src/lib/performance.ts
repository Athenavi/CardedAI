/**
 * Web Vitals 性能监控模块
 *
 * 完美支持：
 * - Chrome DevTools Performance 面板
 * - Lighthouse 审计
 * - Performance API (web vitals)
 * - React Profiler
 * - why-did-you-render（开发环境）
 *
 * 用法：
 *   // 在应用入口调用
 *   import { initPerformanceMonitoring } from '@/lib/performance';
 *   initPerformanceMonitoring();
 *
 *   // 手动标记关键时间点
 *   import { mark, measure } from '@/lib/performance';
 *   mark('app-start');
 *   // ...
 *   mark('app-ready');
 *   measure('app-init', 'app-start', 'app-ready');
 */

// ─── DevTools Performance Marks ─────────────────────────────────────
export function mark(name: string, detail?: object) {
  if (typeof window !== 'undefined' && performance.mark) {
    try {
      performance.mark(name, detail as PerformanceMarkOptions);
    } catch {
      // Older browsers
    }
  }
}

export function measure(name: string, startMark: string, endMark?: string) {
  if (typeof window !== 'undefined' && performance.measure) {
    try {
      performance.measure(name, {
        start: startMark,
        end: endMark,
      });
    } catch {
      // Mark may not exist
    }
  }
}

// ─── Web Vitals Observer ────────────────────────────────────────────

interface VitalMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  id: string;
  delta: number;
  entries?: PerformanceEntry[];
}

const metrics: VitalMetric[] = [];

function getRating(value: number, thresholds: { good: number; poor: number }): 'good' | 'needs-improvement' | 'poor' {
  if (value <= thresholds.good) return 'good';
  if (value <= thresholds.poor) return 'needs-improvement';
  return 'poor';
}

function report(vital: VitalMetric) {
  metrics.push(vital);

  // Dev console 输出 (开发环境)
  if (import.meta.env.DEV) {
    console.log(`[Web Vitals] ${vital.name}:`, vital.value, `(${vital.rating})`);
  }

  // 生产环境通过 sendBeacon 上报
  if (import.meta.env.PROD && typeof navigator.sendBeacon !== 'undefined') {
    const body = JSON.stringify({
      ...vital,
      url: typeof window !== 'undefined' ? window.location.href : '',
    });
    try {
      navigator.sendBeacon('/api/v2/performance/vitals', new Blob([body], { type: 'application/json' }));
    } catch {
      // sendBeacon may fail silently
    }
  }
}

// ─── LCP (Largest Contentful Paint) ─────────────────────────────────
export function trackLCP() {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

  try {
    new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const last = entries[entries.length - 1] as PerformancePaint_timing;
      const value = last?.startTime ?? 0;
      report({
        name: 'LCP',
        value: Math.round(value),
        rating: getRating(value, { good: 2500, poor: 4000 }),
        id: 'v1-abcdefg',
        delta: value,
        entries,
      });
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch {
    // LCP observer not supported
  }
}

// ─── CLS (Cumulative Layout Shift) ──────────────────────────────────
export function trackCLS() {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

  let value = 0;
  let entries: PerformanceEntry[] = [];

  try {
    const po = new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          const shiftValue = (entry as LayoutShift).value;
          value += shiftValue;
          entries.push(entry);
        }
      }
      report({
        name: 'CLS',
        value: Math.round(value * 1000) / 1000,
        rating: getRating(value, { good: 0.1, poor: 0.25 }),
        id: 'v1-abcdefg',
        delta: value,
        entries,
      });
    });
    po.observe({ type: 'layout-shift', buffered: true });
  } catch {
    // Layout-shift not supported
  }
}

// ─── FID (First Input Delay) ────────────────────────────────────────
export function trackFID() {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

  try {
    new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries()) {
        const value = entry.processingStart - entry.startTime;
        report({
          name: 'FID',
          value: Math.round(value),
          rating: getRating(value, { good: 100, poor: 300 }),
          id: 'v1-abcdefg',
          delta: value,
          entries: [entry],
        });
      }
    }).observe({ type: 'first-input', buffered: true });
  } catch {
    // FID observer not supported
  }
}

// ─── INP (Interaction to Next Paint) ────────────────────────────────
export function trackINP() {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

  try {
    new PerformanceObserver((entryList) => {
      let maxDuration = 0;
      for (const entry of entryList.getEntries()) {
        maxDuration = Math.max(maxDuration, entry.duration);
      }
      report({
        name: 'INP',
        value: Math.round(maxDuration),
        rating: getRating(maxDuration, { good: 200, poor: 500 }),
        id: 'v1-abcdefg',
        delta: maxDuration,
      });
    }).observe({ type: 'event', buffered: true });
  } catch {
    // INP observer not supported (older browsers)
  }
}

// ─── TTFB (Time to First Byte) ──────────────────────────────────────
export function trackTTFB() {
  if (typeof window === 'undefined' || !performance.getEntriesByType) return;

  try {
    const navEntries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
    if (navEntries[0]) {
      const ttfb = navEntries[0].responseStart;
      report({
        name: 'TTFB',
        value: Math.round(ttfb),
        rating: getRating(ttfb, { good: 800, poor: 1800 }),
        id: 'v1-abcdefg',
        delta: ttfb,
      });
    }
  } catch {
    // Navigation timing not available
  }
}

// ─── FCP (First Contentful Paint) ───────────────────────────────────
export function trackFCP() {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

  try {
    new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries()) {
        report({
          name: 'FCP',
          value: Math.round(entry.startTime),
          rating: getRating(entry.startTime, { good: 1800, poor: 3000 }),
          id: 'v1-abcdefg',
          delta: entry.startTime,
        });
      }
    }).observe({ type: 'paint', buffered: true });
  } catch {
    // FCP not supported
  }
}

// ─── Initialize All Tracking ────────────────────────────────────────
export function initPerformanceMonitoring() {
  if (typeof window === 'undefined') return;

  mark('page-load');
  trackLCP();
  trackCLS();
  trackFID();
  trackINP();
  trackTTFB();
  trackFCP();

  // 标记页面初始化完成
  if (document.readyState === 'complete') {
    mark('dom-complete');
  } else {
    window.addEventListener('load', () => mark('window-load'));
    document.addEventListener('DOMContentLoaded', () => mark('dom-ready'));
  }
}

// ─── Get Metrics (for debug / reporting) ────────────────────────────
export function getMetrics(): VitalMetric[] {
  return [...metrics];
}

// ─── React Profiler Integration ─────────────────────────────────────
export function onReactProfilerRender(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number,
  baseDuration: number,
  _startTime: number,
  _commitTime: number
) {
  // 仅开发环境输出，>50ms 的渲染告警
  if (import.meta.env.DEV && actualDuration > 50) {
    console.warn(
      `[React Profiler] ${id} (${phase}): ` +
      `${actualDuration.toFixed(0)}ms actual / ${baseDuration.toFixed(0)}ms base`
    );
  }
}

// ─── why-did-you-render (Dev Only) ───────────────────────────────────
// 在需要调试重复渲染的组件文件中使用，示例：
//
//   if (import.meta.env.DEV) {
//     const WDYR = await import('why-did-you-render');
//     WDYR.default(React, { trackAllPureComponents: true });
//   }