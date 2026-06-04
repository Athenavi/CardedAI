import {defineConfig, devices} from '@playwright/test';

/**
 * Playwright E2E 测试配置
 *
 * 使用方式：
 *   BASE_URL=http://localhost:4321 npx playwright test
 *   npx playwright test --ui        # UI 模式
 *   npx playwright test --headed    # 有头模式
 */

const baseURL = process.env.BASE_URL || 'http://localhost:4321';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', {open: 'never'}],
    ['list'],
  ],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: {...devices['Desktop Chrome']},
    },
    {
      name: 'mobile-chrome',
      use: {...devices['Pixel 5']},
    },
  ],
  /* 可选：自动启动前端 dev server */
  // webServer: {
  //   command: 'npm run dev',
  //   url: baseURL,
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120_000,
  // },
});
