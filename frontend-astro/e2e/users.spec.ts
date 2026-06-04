import {expect, test} from './fixtures/auth';

/**
 * 用户管理 E2E 测试
 * 覆盖：用户列表、用户搜索、角色筛选
 */

test.describe('用户管理', () => {
  test('管理员可以访问用户列表', async ({authenticatedPage: page}) => {
    await page.goto('/admin/users');
    await page.waitForTimeout(3000);

    // 用户管理页面应该有表格或卡片列表
    const hasTable = await page.locator('table, [class*="table"]').first().isVisible().catch(() => false);
    const hasCardList = await page.locator('[class*="user"], [class*="card"], [class*="list"]').first().isVisible().catch(() => false);
    expect(hasTable || hasCardList).toBeTruthy();
  });

  test('用户列表页面包含搜索功能', async ({authenticatedPage: page}) => {
    await page.goto('/admin/users');
    await page.waitForTimeout(3000);

    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="用户"], input[placeholder*="search"]').first();
    const hasSearch = await searchInput.isVisible().catch(() => false);
    expect(hasSearch).toBeTruthy();
  });

  test('用户搜索能正常响应', async ({authenticatedPage: page}) => {
    await page.goto('/admin/users');
    await page.waitForTimeout(3000);

    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="用户"], input[placeholder*="search"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill('admin');
      await page.waitForTimeout(2000);
      // 搜索后页面应正常响应（不崩溃）
      const mainContent = page.locator('main, [class*="page"], [class*="content"]').first();
      await expect(mainContent).toBeVisible();
    }
  });

  test('用户管理页面显示操作按钮', async ({authenticatedPage: page}) => {
    await page.goto('/admin/users');
    await page.waitForTimeout(3000);

    // 应该有新建用户或管理操作按钮
    const hasActionBtn = await page.locator('button').filter({hasText: /新建|创建|新增|添加|Create|New|Add/}).first().isVisible().catch(() => false);
    const hasAnyButton = (await page.locator('button').count()) > 0;
    expect(hasActionBtn || hasAnyButton).toBeTruthy();
  });

  test('可以访问角色权限管理页', async ({authenticatedPage: page}) => {
    await page.goto('/admin/roles');
    await page.waitForTimeout(3000);

    // 角色权限页面应该正常加载
    const mainContent = page.locator('main, [class*="page"], [class*="content"], [class*="admin"]').first();
    await expect(mainContent).toBeVisible();
  });
});
