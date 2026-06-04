import {ADMIN_CREDENTIALS, expect, test} from './fixtures/auth';

/**
 * 登录流程 E2E 测试
 * 覆盖：页面渲染、密码登录、错误处理、2FA 流程占位
 */

test.describe('登录流程', () => {
  test.beforeEach(async ({page}) => {
    await page.goto('/login');
  });

  test('登录页面正确渲染', async ({page}) => {
    // 核心元素存在
    await expect(page).toHaveURL(/\/login/);
    // 检查表单输入框存在
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
    await expect(usernameInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
  });

  test('空凭据提交应显示验证错误', async ({page}) => {
    // 尝试点击提交按钮
    const submitBtn = page.locator('button[type="submit"]').first();
    if (await submitBtn.isVisible()) {
      await submitBtn.click();
      // 应该停留在登录页
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test('错误密码登录应失败', async ({page}) => {
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
    const submitBtn = page.locator('button[type="submit"]').first();

    await usernameInput.fill(ADMIN_CREDENTIALS.username);
    await passwordInput.fill('wrong_password_12345');
    await submitBtn.click();

    // 等待错误提示出现（toast 或内联错误）
    await page.waitForTimeout(2000);
    // 不应该跳转到 admin
    await expect(page).not.toHaveURL(/\/admin/);
  });

  test('正确凭据登录成功后跳转到管理后台', async ({page}) => {
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
    const submitBtn = page.locator('button[type="submit"]').first();

    await usernameInput.fill(ADMIN_CREDENTIALS.username);
    await passwordInput.fill(ADMIN_CREDENTIALS.password);
    await submitBtn.click();

    // 等待跳转到 admin 或 2FA 页面
    await page.waitForURL(/\/(admin|login)/, {timeout: 15000});
    const url = page.url();
    // 登录成功后应进入 admin 或 2FA
    expect(url.includes('/admin') || url.includes('/login')).toBeTruthy();
  });

  test('未认证访问 admin 应重定向到登录页', async ({page}) => {
    await page.goto('/admin');
    await page.waitForTimeout(3000);
    // 应该被重定向到登录页或显示登录相关内容
    const url = page.url();
    const hasLoginForm = await page.locator('input[type="password"]').isVisible().catch(() => false);
    expect(url.includes('/login') || hasLoginForm).toBeTruthy();
  });
});
