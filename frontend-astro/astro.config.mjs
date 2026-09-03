import {defineConfig} from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';
import AstroPWA from '@vite-pwa/astro';
import path from 'path';
import {fileURLToPath} from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://astro.build/config
export default defineConfig({
  site: 'https://fastblog.example.com',
  output: 'static',

  image: {
    // 图片优化配置：移动端自动输出 WebP/AVIF，按断点生成多尺寸
    domains: [],
    service: {
      entry: '@img/sharp-webp',
    },
    // 预设移动端常用尺寸
    sizes: [
      400,
      750,
      1080,
      1200,
      1920,
      // 移动端视口
      '100vw',
      '50vw',
    ],
  },

  integrations: [
    react(),
    sitemap({
      i18n: {
        defaultLocale: 'zh-CN',
        locales: {
          'zh-CN': 'zh-CN',
          en: 'en',
          ar: 'ar',
          he: 'he',
        },
      },
    }),
    AstroPWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'FastBlog',
        short_name: 'FastBlog',
        description: 'A modern blog platform',
        theme_color: '#3b82f6',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait-primary',
        start_url: '/',
        categories: ['productivity', 'utilities'],
        icons: [
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable',
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,jpg,jpeg,gif,svg,webp,avif,woff2}'],
        // 网络优先 + 回退缓存策略，优化弱网络体验
        runtimeCaching: [
          {
            // API 请求：网络优先，失败回退缓存
            urlPattern: /\/api\//,
            handler: 'NetworkFirst',
            options: {
              networkTimeoutSeconds: 3,
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24, // 24h
              },
              networkTimeoutSeconds: 3,
            },
          },
          {
            // 静态资源：缓存优先
            urlPattern: /\/assets\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'static-assets',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30d
              },
            },
          },
          {
            // 图片：缓存优先
            urlPattern: /\.(png|jpg|jpeg|gif|svg|webp|avif)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 * 7, // 7d
              },
            },
          },
          {
            // Google Fonts：缓存优先
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365,
              },
            },
          },
          {
            // 字体文件：缓存优先
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: '字体-files-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365,
              },
            },
          },
        ],
      },
    }),
  ],

  vite: {
    plugins: [tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:9421',
          changeOrigin: true,
        },
      },
      // 移动端HMR优化
      hmr: {
        overlay: true,
      },
    },
    build: {
      // chunk 大小警告阈值
      chunkSizeWarningLimit: 500,
      // 代码分割优化
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('/react/') || id.includes('/react-dom/')) return 'vendor-react';
              if (id.includes('/@tanstack/react-query/')) return 'vendor-query';
              if (id.includes('/framer-motion/')) return 'vendor-motion';
              if (id.includes('/lucide-react/')) return 'vendor-icons';
              if (id.includes('/@radix-ui/')) return 'vendor-radix';
              if (id.includes('/@tiptap/') || id.includes('/lowlight/') || id.includes('/highlight.js/') || id.includes('/yjs/') || id.includes('/y-websocket/') || id.includes('/y-prosemirror/')) return 'vendor-editor';
              // 新增：图表库独立分包
              if (id.includes('/chart.js/') || id.includes('/react-chartjs-2/')) return 'vendor-chart';
              // 新增：lodash独立分包
              if (id.includes('/lodash-es/')) return 'vendor-lodash';
              // 新增：recharts独立分包
              if (id.includes('/recharts/')) return 'vendor-recharts';
              // 新增：dnd-kit独立分包
              if (id.includes('/@dnd-kit/')) return 'vendor-dnd';
              // 新增：表单库独立分包
              if (id.includes('/react-hook-form/') || id.includes('/@hookform/')) return 'vendor-form';
              // 新增：UI工具库
              if (id.includes('/class-variance-authority/') || id.includes('/tailwind-merge/') || id.includes('/clsx/')) return 'vendor-ui-utils';
            }
            return 'vendor';
          },
        },
      },
      // 启用 CSS 代码分割
      cssCodeSplit: true,
      // 压缩选项
      minify: 'esbuild',
      // 生产环境移除 console/debugger
      target: ['chrome103', 'safari15.4', 'firefox119', 'edge103'],
      // 移动端兼容性
      cssMinify: true,
    },
    esbuild: {
      // 生产环境自动移除 console.log 和 debugger
      drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : [],
    },
    // 预优化依赖
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        '@tanstack/react-query',
        'framer-motion',
        'lucide-react',
        'ky',
        'clsx',
        'tailwind-merge',
      ],
      exclude: [
        '@testing-library/react',
        '@testing-library/user-event',
        '@testing-library/dom',
        '@testing-library/jest-dom',
      ],
    },
  },

  i18n: {
    defaultLocale: 'zh-CN',
    locales: ['zh-CN', 'en', 'ar', 'he'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
