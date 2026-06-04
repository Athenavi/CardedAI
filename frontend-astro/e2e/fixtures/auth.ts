import {type Page, test as base} from '@playwright/test';

/**
 * E2E 测试共享 fixtures
 *
 * 提供认证后的 page 上下文，避免每个测试都要手动登录。
 */

/** 测试用管理员凭证 */
export const ADMIN_CREDENTIALS = {
  username: process.env.E2E_ADMIN_USER || 'admin',
  password: process.env.E2E_ADMIN_PASS || 'admin123',
};

/** 通过 API 获取 JWT token 并注入到浏览器 localStorage */
async function loginViaAPI(page: Page, baseURL: string, creds = ADMIN_CREDENTIALS) {
  // 先访问目标站点以设置 origin
  await page.goto(baseURL || '/');

  // 通过 API 登录获取 token
  const resp = await page.evaluate(async ({url, username, password}) => {
    const r = await fetch(`${url}/api/v1/auth/login`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password}),
    });
    return r.json();
  }, {url: baseURL || '', username: creds.username, password: creds.password});

  if (resp?.data?.access_token) {
    await page.evaluate((token) => {
      localStorage.setItem('access_token', token);
    }, resp.data.access_token);
  }
}

/** 自定义 test fixture，注入 authenticated page */
export const test = base.extend<{ authenticatedPage: Page }>({
  authenticatedPage: async ({page, baseURL}, use) => {
    await loginViaAPI(page, baseURL!);
    await use(page);
  },
});

export {expect} from '@playwright/test';
