import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: [
        'src/lib/schemas/**',
        'src/lib/api/base-client.ts',
        'src/lib/hooks/**',
        'src/components/ui/toast-provider.tsx',
        'src/components/ui/confirm-provider.tsx',
      ],
    },
  },
});
