/**
 * 访问埋点（Phase 2）
 *
 * - 页面进入：上报 path + referrer
 * - 页面隐藏/卸载：补报停留时长（visibilitychange / pagehide）
 * - 用 navigator.sendBeacon 保证离开页面时请求也能发出
 * - 后端按 (访客指纹 + path) 做 30 秒去重，前端无需限流
 */

'use client';

import {useEffect} from 'react';

const ENDPOINT = '/api/v2/analytics/pageview';

const send = (body: Record<string, unknown>) => {
  try {
    const payload = JSON.stringify(body);
    const canBeacon = typeof navigator !== 'undefined' ? Boolean(navigator.sendBeacon) : false;
    if (canBeacon) {
      navigator.sendBeacon(ENDPOINT, new Blob([payload], {type: 'application/json'}));
      return;
    }
    fetch(ENDPOINT, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: payload,
      keepalive: true,
    }).catch(() => {
    });
  } catch {
    // 埋点失败不影响页面
  }
};

const AnalyticsBeacon: React.FC = () => {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const path = window.location.pathname + window.location.search;
    send({path, referrer: document.referrer || null});

    const startedAt = Date.now();
    let reported = false;
    const reportDuration = () => {
      if (reported) return;
      reported = true;
      send({path, duration_ms: Date.now() - startedAt});
    };

    const onVisibilityChange = () => {
      if (document.visibilityState === 'hidden') reportDuration();
    };

    document.addEventListener('visibilitychange', onVisibilityChange);
    window.addEventListener('pagehide', reportDuration);

    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('pagehide', reportDuration);
    };
  }, []);

  return null;
};

export default AnalyticsBeacon;
