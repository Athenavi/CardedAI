# FastBlog Default Theme

FastBlog 默认主题 - 简洁、现代、响应式设计

**适用版本**: FastBlog V0.3.0+

## 特性

- ✅ 响应式设计,支持移动端
- ✅ 深色模式支持
- ✅ 侧边栏可配置(左/右/隐藏)
- ✅ 自定义颜色方案
- ✅ 灵活的排版设置
- ✅ 评论系统集成
- ✅ 社交分享按钮
- ✅ 相关文章推荐
- ✅ 目录导航

## 主题文件结构

```
default/
├── metadata.json      # 主题元数据（名称、版本、作者等）
├── theme.json         # 主题运行时配置（颜色、布局、排版）
├── theme.config.js    # 前端构建配置（Astro + TailwindCSS）
├── styles.css         # 自定义样式
├── screenshot.svg     # 主题预览截图
├── README.md          # 本文件
└── templates/         # Astro 组件模板
```

## 配置

### metadata.json — 主题元数据

定义主题的基本信息，用于管理后台展示和版本管理：

```json
{
  "name": "Default",
  "slug": "default",
  "version": "1.0.0",
  "description": "FastBlog 默认主题",
  "author": "FastBlog Team",
  "tags": ["blog", "minimal", "responsive"],
  "requires": ">=0.3.0",
  "supports": ["articles", "comments", "seo", "dark-mode"]
}
```

### theme.json — 运行时主题配置

用于后端渲染和主题切换时的配置：

```json
{
  "settings": {
    "colors": {
      "primary": "#3b82f6",
      "secondary": "#64748b",
      "background": "#ffffff",
      "text": "#1e293b"
    },
    "layout": {
      "sidebar_position": "right",
      "content_width": "max-w-4xl"
    },
    "typography": {
      "font_family": "Inter",
      "font_size": "16px",
      "line_height": "1.75"
    }
  }
}
```

### theme.config.js — 前端构建配置

用于 Astro 前端的 TailwindCSS 和组件配置：

```javascript
export const themeConfig = {
    colors: {
        primary: '#3b82f6',
        secondary: '#64748b',
        accent: '#f59e0b',
        background: '#ffffff',
        text: '#1e293b',
    },
    layout: {
        sidebarPosition: 'right',
        contentWidth: 'max-w-4xl',
    },
    typography: {
        fontFamily: 'Inter',
        fontSize: '16px',
        lineHeight: '1.75',
    },
    features: {
        showComments: true,
        showShareButtons: true,
        showRelatedPosts: true,
        showTableOfContents: true,
        enableDarkMode: true,
    }
};
```

## 自定义

1. 复制 `default` 主题目录为新目录（如 `my-theme`）
2. 修改 `metadata.json` 中的主题信息（name, slug, version）
3. 调整 `theme.config.js` 中的颜色、布局和功能开关
4. 在 `theme.json` 中同步更新运行时配置
5. 在后台激活新主题

## 支持的功能

| 功能                | 说明         |
|-------------------|------------|
| Custom Logo       | 自定义站点 Logo |
| Custom Header     | 自定义头部区域    |
| Featured Image    | 文章特色图片     |
| Post Thumbnails   | 文章缩略图      |
| Comments          | 评论系统       |
| Dark Mode         | 深色模式       |
| Table of Contents | 文章目录导航     |
| Social Share      | 社交分享按钮     |
| Related Posts     | 相关文章推荐     |

## 许可证

MIT License
