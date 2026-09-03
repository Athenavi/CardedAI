/**
 * React Profiler Wrapper
 *
 * 开发环境下使用 React Profiler 监控组件渲染性能。
 * 集成 Chrome DevTools、Lighthouse 性能面板。
 * 生产环境自动禁用（not rendered）。
 *
 * 使用方式：
 *   <ReactProfiler id="App">{children}</ReactProfiler>
 *
 * DevTools 集成：
 *   - Performance marks 自动写入 performance timeline
 *   - 在 DevTools → Performance 中可见所有 mark 和 measure
 *   - Lighthouse 运行时审计可直接采集
 */

'use client';

import React, {type PropsWithChildren} from 'react';
import {onReactProfilerRender} from '@/lib/performance';

interface ReactProfilerProps {
  id: string;
}

export const ReactProfiler: React.FC<PropsWithChildren<ReactProfilerProps>> = ({id, children}) => {
  // 使用 React 18+ Profiler API
  return (
    <React.Profiler id={id} onRender={onReactProfilerRender as any}>
      {children}
    </React.Profiler>
  );
};

// 默认导出同时指向组件和性能回调，方便按需使用
export {onReactProfilerRender as profilerOnRender} from '@/lib/performance';
export default ReactProfiler;