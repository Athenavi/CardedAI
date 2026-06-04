/**
 * Modern Minimal Theme Configuration
 * 现代简约主题配置 - 支持代码高亮、目录、深色模式
 */

export const themeConfig = {
    // 颜色方案 - 简约现代风格，支持代码高亮
    colors: {
        primary: '#3b82f6',      // Blue
        secondary: '#64748b',    // Slate
        accent: '#f59e0b',       // Amber
        background: '#ffffff',   // White
        foreground: '#1f2937',   // Gray 800
        muted: '#f3f4f6',        // Gray 100
        border: '#e5e7eb',       // Gray 200
        code_background: '#1e293b',  // Slate 800
        code_text: '#e2e8f0',        // Slate 200
    },

    // 布局配置
    layout: {
        sidebarPosition: 'right',
        contentWidth: 'max-w-5xl',
        showSidebar: true,
        showToc: true,           // 显示目录
        tocPosition: 'sticky',   // 粘性定位
        headerStyle: 'centered',
        footerStyle: 'simple',
    },

    // 排版配置
    typography: {
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        codeFont: 'Fira Code, JetBrains Mono, monospace',
        fontSize: '16px',
        lineHeight: 1.75,
        headingWeight: 600,
        headingLetterSpacing: '-0.025em',
    },

    // 组件样式
    components: {
        borderRadius: '0.5rem',
        shadowStyle: 'medium',
        buttonStyle: 'default',
    },

    // 功能开关
    features: {
        showComments: true,
        showShareButtons: true,
        showRelatedPosts: true,
        showTableOfContents: true,
        enableDarkMode: true,
        autoDarkMode: true,       // 自动跟随系统
        showCodeLineNumbers: true,
        showCopyButton: true,
        showReadingTime: true,
        showWordCount: true,
        showAuthorBox: true,
        smoothScroll: true,
        lazyLoadImages: true,
    },
};

export default themeConfig;
