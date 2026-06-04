/**
 * Magazine Theme Configuration
 */

export const themeConfig = {
    colors: {
        primary: '#dc2626',      // Red - Bold and attention-grabbing
        secondary: '#1f2937',    // Gray 800
        accent: '#f59e0b',       // Amber
        background: '#ffffff',
        foreground: '#111827',
        muted: '#f9fafb',
        border: '#e5e7eb',
    },

    layout: {
        sidebarPosition: 'right',
        contentWidth: 'max-w-7xl',
        showSidebar: true,
        gridColumns: 3,
        headerStyle: 'magazine',
        footerStyle: 'multi-column',
    },

    typography: {
        fontFamily: 'Merriweather, Georgia, serif',
        headingFont: 'Montserrat, sans-serif',
        fontSize: '16px',
        lineHeight: 1.8,
        headingWeight: 800,
    },

    features: {
        showFeaturedPosts: true,
        featuredPostsCount: 3,
        showCategorySections: true,
        showReadingTime: true,
        showWordCount: false,
        showRelatedPosts: true,
        showAuthorBox: true,
        stickyHeader: true,
        breakingNewsBar: true,
    },
};

export default themeConfig;
