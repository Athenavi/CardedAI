/**
 * FastBlog Default Theme
 * 默认主题配置文件
 */

export const themeConfig = {
    // 颜色方案
    colors: {
        primary: '#3b82f6',
        secondary: '#64748b',
        accent: '#f59e0b',
        background: '#ffffff',
        foreground: '#1f2937',
        muted: '#f3f4f6',
        border: '#e5e7eb',
    },

    // 布局配置
    layout: {
        sidebarPosition: 'right', // 'left' | 'right' | 'none'
        contentWidth: 'max-w-4xl',
        showSidebar: true,
        showHeader: true,
        showFooter: true,
    },

    // 排版配置
    typography: {
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: '16px',
        lineHeight: 1.6,
        headingFontWeight: 700,
    },

    // 组件样式
    components: {
        borderRadius: '0.5rem',
        shadowStyle: 'medium', // 'none' | 'small' | 'medium' | 'large'
        buttonStyle: 'default', // 'default' | 'rounded' | 'pill'
    },

    // 功能开关
    features: {
        showComments: true,
        showShareButtons: true,
        showRelatedPosts: true,
        showTableOfContents: true,
        enableDarkMode: true,
    },
};

export default themeConfig;
