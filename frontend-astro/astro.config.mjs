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
        start_url: '/',
        icons: [
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webp}'],
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
      build: {
          // 代码分割优化
          rollupOptions: {
              output: {
                  manualChunks: {
                      'vendor-react': ['react', 'react-dom'],
                      'vendor-query': ['@tanstack/react-query'],
                      'vendor-motion': ['framer-motion'],
                      'vendor-icons': ['lucide-react'],
                      'vendor-radix': [
                          '@radix-ui/react-dialog',
                          '@radix-ui/react-dropdown-menu',
                          '@radix-ui/react-select',
                          '@radix-ui/react-tabs',
                          '@radix-ui/react-toast',
                          '@radix-ui/react-accordion',
                          '@radix-ui/react-avatar',
                          '@radix-ui/react-popover',
                          '@radix-ui/react-switch',
                          '@radix-ui/react-checkbox',
                      ],
                      'vendor-editor': [
                          '@tiptap/react',
                          '@tiptap/starter-kit',
                          '@tiptap/pm',
                          '@tiptap/extension-link',
                          '@tiptap/extension-image',
                          '@tiptap/extension-placeholder',
                          '@tiptap/extension-code-block-lowlight',
                          '@tiptap/extension-table',
                          '@tiptap/extension-table-cell',
                          '@tiptap/extension-table-header',
                          '@tiptap/extension-table-row',
                          '@tiptap/extension-task-list',
                          '@tiptap/extension-task-item',
                          '@tiptap/extension-text-align',
                          '@tiptap/extension-underline',
                          '@tiptap/extension-highlight',
                          '@tiptap/extension-typography',
                          '@tiptap/extension-floating-menu',
                          '@tiptap/extension-text-style',
                          '@tiptap/extension-color',
                          '@tiptap/extension-font-family',
                      ],
                      'vendor-collab': [
                          'yjs',
                          'y-websocket',
                          'y-prosemirror',
                          '@tiptap/extension-collaboration',
                          '@tiptap/extension-collaboration-cursor',
                      ],
                  },
              },
          },
          // 启用 CSS 代码分割
          cssCodeSplit: true,
          // 压缩选项
          minify: 'esbuild',
          // 生产环境移除 console/debugger
          target: 'es2022',
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
