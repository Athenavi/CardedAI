/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      // 自定义断点（移动端优先）
      screens: {
        'xs': '475px',   // 小屏手机
        'sm': '640px',   // 竖屏手机
        'md': '768px',   // 平板
        'lg': '1024px',  // 小桌面
        'xl': '1280px',  // 桌面
        '2xl': '1536px', // 大屏桌面
      },
      // 触摸友好配置
      spacing: {
        'touch-target': '44px', // WCAG 触摸目标最小 44px
      },
      borderRadius: {
        'touch': '12px', // 触摸友好圆角
      },
      // 响应式安全区域（适配刘海/底部横条）
      inset: {
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
      padding: {
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
    },
  },
  plugins: [
    // 触摸友好的 hover 行为：移动端禁用 hover
    require('tailwindcss/plugin')((({ addVariant, addUtilities }) => {
      // 仅桌面端启用 hover 样式
      addVariant('desktop-hover', '@media (hover: hover) and (pointer: fine)');
      // 仅触摸设备
      addVariant('touch-only', '@media (pointer: coarse)');
      // 高对比度模式
      addVariant('high-contrast', '@media (prefers-contrast: more)');
      // 减少动效
      addVariant('reduce-motion', '@media (prefers-reduced-motion: reduce)');
    }))( {}),
  ],
};
