/**
 * P13-2: 全局样式系统 - 类型定义和预设库
 *
 * 提供一键切换全站配色方案、字体/间距全局变量、样式预设库功能
 */

export interface GlobalStyleConfig {
    id: number;
    name: string; // 配置名称（如 "Dark Mode"）
    slug: string; // 配置标识符（如 "dark-mode"）
    is_active: boolean; // 是否当前启用
    theme_type: 'light' | 'dark' | 'custom'; // 主题类型
    color_scheme: ColorScheme; // 配色方案
    typography: TypographyConfig; // 字体配置
    spacing: SpacingConfig; // 间距配置
    border_radius: BorderRadiusConfig; // 圆角配置
    shadows?: ShadowConfig; // 阴影配置
    breakpoints?: BreakpointConfig; // 响应式断点
    css_variables?: Record<string, string>; // 自定义 CSS 变量
    preview_image?: string; // 预览图 URL
    created_by?: number; // 创建者用户 ID
    created_at: string;
    updated_at: string;
}

export interface ColorScheme {
    primary: string; // 主色
    secondary: string; // 次要色
    accent: string; // 强调色
    background: string; // 背景色
    surface: string; // 表面色（卡片等）
    text: string; // 文字色
    text_secondary: string; // 次要文字色
    border: string; // 边框色
    success: string; // 成功色
    warning: string; // 警告色
    error: string; // 错误色
    info: string; // 信息色
}

export interface TypographyConfig {
    font_family: string; // 字体系列
    font_size_base: number; // 基础字号（px）
    line_height: number; // 行高
    heading_weights: {
        h1: number; // H1 字重
        h2: number; // H2 字重
        h3: number; // H3 字重
        h4: number; // H4 字重
        h5: number; // H5 字重
        h6: number; // H6 字重
    };
    heading_sizes: {
        h1: number; // H1 字号
        h2: number; // H2 字号
        h3: number; // H3 字号
        h4: number; // H4 字号
        h5: number; // H5 字号
        h6: number; // H6 字号
    };
}

export interface SpacingConfig {
    padding_base: number; // 基础内边距（px）
    margin_base: number; // 基础外边距（px）
    gap_sizes: {
        xs: number; // 4px
        sm: number; // 8px
        md: number; // 16px
        lg: number; // 24px
        xl: number; // 32px
        xxl: number; // 48px
    };
}

export interface BorderRadiusConfig {
    sm: number; // 小圆角（2px）
    md: number; // 中圆角（4px）
    lg: number; // 大圆角（8px）
    xl: number; // 超大圆角（16px）
    full: number; // 完全圆角（9999px）
}

export interface ShadowConfig {
    sm: string; // 小阴影
    md: string; // 中阴影
    lg: string; // 大阴影
    xl: string; // 超大阴影
}

export interface BreakpointConfig {
    sm: number; // 640px
    md: number; // 768px
    lg: number; // 1024px
    xl: number; // 1280px
    xxl: number; // 1536px
}

/**
 * P13-2: 预定义样式预设库
 */
export const STYLE_PRESETS: Omit<GlobalStyleConfig, 'id' | 'created_at' | 'updated_at'>[] = [
    // 浅色主题
    {
        name: 'Light Mode',
        slug: 'light-mode',
        is_active: false,
        theme_type: 'light',
        color_scheme: {
            primary: '#3b82f6',
            secondary: '#64748b',
            accent: '#8b5cf6',
            background: '#ffffff',
            surface: '#f8fafc',
            text: '#0f172a',
            text_secondary: '#64748b',
            border: '#e2e8f0',
            success: '#10b981',
            warning: '#f59e0b',
            error: '#ef4444',
            info: '#3b82f6'
        },
        typography: {
            font_family: 'Inter, system-ui, sans-serif',
            font_size_base: 16,
            line_height: 1.6,
            heading_weights: {h1: 800, h2: 700, h3: 600, h4: 600, h5: 600, h6: 600},
            heading_sizes: {h1: 48, h2: 36, h3: 30, h4: 24, h5: 20, h6: 16}
        },
        spacing: {
            padding_base: 16,
            margin_base: 16,
            gap_sizes: {xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48}
        },
        border_radius: {sm: 2, md: 4, lg: 8, xl: 16, full: 9999},
        shadows: {
            sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
            md: '0 4px 6px rgba(0, 0, 0, 0.1)',
            lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
            xl: '0 20px 25px rgba(0, 0, 0, 0.15)'
        },
        breakpoints: {sm: 640, md: 768, lg: 1024, xl: 1280, xxl: 1536}
    },

    // 深色主题
    {
        name: 'Dark Mode',
        slug: 'dark-mode',
        is_active: false,
        theme_type: 'dark',
        color_scheme: {
            primary: '#60a5fa',
            secondary: '#94a3b8',
            accent: '#a78bfa',
            background: '#0f172a',
            surface: '#1e293b',
            text: '#f8fafc',
            text_secondary: '#94a3b8',
            border: '#334155',
            success: '#34d399',
            warning: '#fbbf24',
            error: '#f87171',
            info: '#60a5fa'
        },
        typography: {
            font_family: 'Inter, system-ui, sans-serif',
            font_size_base: 16,
            line_height: 1.6,
            heading_weights: {h1: 800, h2: 700, h3: 600, h4: 600, h5: 600, h6: 600},
            heading_sizes: {h1: 48, h2: 36, h3: 30, h4: 24, h5: 20, h6: 16}
        },
        spacing: {
            padding_base: 16,
            margin_base: 16,
            gap_sizes: {xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48}
        },
        border_radius: {sm: 2, md: 4, lg: 8, xl: 16, full: 9999},
        shadows: {
            sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
            md: '0 4px 6px rgba(0, 0, 0, 0.4)',
            lg: '0 10px 15px rgba(0, 0, 0, 0.5)',
            xl: '0 20px 25px rgba(0, 0, 0, 0.6)'
        },
        breakpoints: {sm: 640, md: 768, lg: 1024, xl: 1280, xxl: 1536}
    },

    // 极简风格
    {
        name: 'Minimal',
        slug: 'minimal',
        is_active: false,
        theme_type: 'custom',
        color_scheme: {
            primary: '#000000',
            secondary: '#666666',
            accent: '#000000',
            background: '#ffffff',
            surface: '#fafafa',
            text: '#000000',
            text_secondary: '#666666',
            border: '#e5e5e5',
            success: '#22c55e',
            warning: '#eab308',
            error: '#dc2626',
            info: '#3b82f6'
        },
        typography: {
            font_family: 'Helvetica Neue, Arial, sans-serif',
            font_size_base: 18,
            line_height: 1.8,
            heading_weights: {h1: 300, h2: 300, h3: 400, h4: 400, h5: 400, h6: 400},
            heading_sizes: {h1: 56, h2: 42, h3: 32, h4: 26, h5: 22, h6: 18}
        },
        spacing: {
            padding_base: 24,
            margin_base: 24,
            gap_sizes: {xs: 8, sm: 12, md: 24, lg: 32, xl: 48, xxl: 64}
        },
        border_radius: {sm: 0, md: 0, lg: 0, xl: 0, full: 9999},
        shadows: {
            sm: 'none',
            md: 'none',
            lg: 'none',
            xl: 'none'
        },
        breakpoints: {sm: 640, md: 768, lg: 1024, xl: 1280, xxl: 1536}
    },

    // 企业风格
    {
        name: 'Corporate',
        slug: 'corporate',
        is_active: false,
        theme_type: 'custom',
        color_scheme: {
            primary: '#1e40af',
            secondary: '#475569',
            accent: '#0ea5e9',
            background: '#f8fafc',
            surface: '#ffffff',
            text: '#1e293b',
            text_secondary: '#64748b',
            border: '#cbd5e1',
            success: '#059669',
            warning: '#d97706',
            error: '#dc2626',
            info: '#0284c7'
        },
        typography: {
            font_family: 'Roboto, system-ui, sans-serif',
            font_size_base: 16,
            line_height: 1.5,
            heading_weights: {h1: 700, h2: 600, h3: 600, h4: 500, h5: 500, h6: 500},
            heading_sizes: {h1: 40, h2: 32, h3: 28, h4: 24, h5: 20, h6: 16}
        },
        spacing: {
            padding_base: 16,
            margin_base: 16,
            gap_sizes: {xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48}
        },
        border_radius: {sm: 2, md: 4, lg: 6, xl: 8, full: 9999},
        shadows: {
            sm: '0 1px 3px rgba(0, 0, 0, 0.12)',
            md: '0 4px 6px rgba(0, 0, 0, 0.1)',
            lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
            xl: '0 20px 25px rgba(0, 0, 0, 0.15)'
        },
        breakpoints: {sm: 640, md: 768, lg: 1024, xl: 1280, xxl: 1536}
    }
];

/**
 * P13-2: 将样式配置转换为 CSS 变量
 */
export function generateCSSVariables(config: GlobalStyleConfig): string {
    const {color_scheme, typography, spacing, border_radius, shadows, css_variables} = config;

    let css = ':root {\n';

    // 颜色变量
    Object.entries(color_scheme).forEach(([key, value]) => {
        css += `  --color-${key}: ${value};\n`;
    });

    // 字体变量
    css += `  --font-family: ${typography.font_family};\n`;
    css += `  --font-size-base: ${typography.font_size_base}px;\n`;
    css += `  --line-height: ${typography.line_height};\n`;

    Object.entries(typography.heading_weights).forEach(([key, value]) => {
        css += `  --heading-weight-${key}: ${value};\n`;
    });

    Object.entries(typography.heading_sizes).forEach(([key, value]) => {
        css += `  --heading-size-${key}: ${value}px;\n`;
    });

    // 间距变量
    css += `  --padding-base: ${spacing.padding_base}px;\n`;
    css += `  --margin-base: ${spacing.margin_base}px;\n`;

    Object.entries(spacing.gap_sizes).forEach(([key, value]) => {
        css += `  --gap-${key}: ${value}px;\n`;
    });

    // 圆角变量
    Object.entries(border_radius).forEach(([key, value]) => {
        css += `  --radius-${key}: ${value}px;\n`;
    });

    // 阴影变量
    if (shadows) {
        Object.entries(shadows).forEach(([key, value]) => {
            css += `  --shadow-${key}: ${value};\n`;
        });
    }

    // 自定义 CSS 变量
    if (css_variables) {
        Object.entries(css_variables).forEach(([key, value]) => {
            css += `  --${key}: ${value};\n`;
        });
    }

    css += '}\n';

    return css;
}

/**
 * P13-2: 应用样式配置到文档
 */
export function applyGlobalStyle(config: GlobalStyleConfig): void {
    // 移除旧的样式标签
    const oldStyle = document.getElementById('global-style-config');
    if (oldStyle) {
        oldStyle.remove();
    }

    // 生成并注入新的 CSS 变量
    const cssVariables = generateCSSVariables(config);
    const styleElement = document.createElement('style');
    styleElement.id = 'global-style-config';
    styleElement.textContent = cssVariables;
    document.head.appendChild(styleElement);

    // 更新 body class
    document.body.classList.remove('theme-light', 'theme-dark', 'theme-custom');
    document.body.classList.add(`theme-${config.theme_type}`);
}
