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
          // chunk 大小警告阈值（RichEditor 已经懒加载，564kB 可接受）
          chunkSizeWarningLimit: 600,
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
                      }
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
