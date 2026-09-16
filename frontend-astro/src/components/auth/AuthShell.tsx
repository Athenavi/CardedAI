'use client';

import React from 'react';

interface AuthShellProps {
  /** 标题上方的引文（取自品牌 tagline） */
  tagline?: string;
  title: string;
  subtitle?: string;
  /** 表单下方内容（切换链接、条款等） */
  footnote?: React.ReactNode;
  /** 页面最底部内容（统计、用户评价、特性行） */
  note?: React.ReactNode;
  children: React.ReactNode;
}

/**
 * 认证页外壳（登录 / 注册共用）—— 单栏沉浸式
 *
 * 版式：整页纸色留白，中央一条编辑栏（大屏两侧为发丝竖线）。
 * 层次顺序固定为 tagline → 衬线大标题 → 副文 → 墨蓝短横线 → 表单 → 脚注 → 底部注记，
 * 不出现色块面板、卡片套卡片与重阴影。
 */
export default function AuthShell({tagline, title, subtitle, footnote, note, children}: AuthShellProps) {
  return (
    <div className="flex min-h-[calc(100dvh-3.5rem)] justify-center px-5 sm:px-8">
      <div className="flex w-full max-w-[34rem] flex-col lg:border-x lg:border-border/60 lg:px-14">
        <div className="flex flex-1 flex-col justify-center py-14 sm:py-16">
          {tagline && (
            <p className="mb-4 text-[11px] tracking-[0.24em] text-muted-foreground">{tagline}</p>
          )}

          <h1 className="editorial-title text-[1.9rem] leading-[1.15] text-foreground sm:text-[2.15rem]">
            {title}
          </h1>

          {subtitle && (
            <p className="mt-3 max-w-[30rem] text-sm leading-relaxed text-muted-foreground">{subtitle}</p>
          )}

          <div className="mt-8 h-px w-12 bg-primary" aria-hidden="true"/>

          <div className="mt-8">{children}</div>

          {footnote && (
            <div className="mt-10 border-t border-border pt-6 text-sm text-muted-foreground">{footnote}</div>
          )}
        </div>

        {note && <div className="border-t border-border py-7">{note}</div>}
      </div>
    </div>
  );
}
