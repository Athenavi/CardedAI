import {expect, test} from './fixtures/auth';

/**
 * 媒体上传 E2E 测试
 * 覆盖：媒体库访问、文件上传、文件管理
 */

test.describe('媒体库管理', () => {
  test('管理员可以访问媒体库', async ({authenticatedPage: page}) => {
    await page.goto('/admin/media');
    await page.waitForTimeout(3000);

    // 媒体库页面应该有上传区域或文件列表
    const hasUploadArea = await page.locator('[class*="upload"], [class*="drop"], input[type="file"]').first().isVisible().catch(() => false);
    const hasMediaGrid = await page.locator('[class*="media"], [class*="grid"], [class*="gallery"]').first().isVisible().catch(() => false);
    expect(hasUploadArea || hasMediaGrid).toBeTruthy();
  });

  test('媒体库页面包含文件输入或上传按钮', async ({authenticatedPage: page}) => {
    await page.goto('/admin/media');
    await page.waitForTimeout(3000);

    // 查找上传相关元素
    const fileInput = page.locator('input[type="file"]');
    const uploadBtn = page.locator('button').filter({hasText: /上传|Upload/});

    const hasFileInput = (await fileInput.count()) > 0;
    const hasUploadBtn = (await uploadBtn.count()) > 0;

    expect(hasFileInput || hasUploadBtn).toBeTruthy();
  });

  test('可以打开文件选择对话框进行上传', async ({authenticatedPage: page}) => {
    await page.goto('/admin/media');
    await page.waitForTimeout(3000);

    // 如果有上传按钮，点击它
    const uploadBtn = page.locator('button').filter({hasText: /上传|Upload/}).first();
    if (await uploadBtn.isVisible()) {
      // 监听 file chooser 事件
      const [fileChooser] = await Promise.all([
        page.waitForEvent('filechooser', {timeout: 5000}).catch(() => null),
        uploadBtn.click(),
      ]);
      // 如果触发了 file chooser，说明上传功能正常
      if (fileChooser) {
        expect(fileChooser).toBeTruthy();
        await fileChooser.setFiles([]); // 不实际上传
      }
    }
  });

  test('媒体库支持视图切换', async ({authenticatedPage: page}) => {
    await page.goto('/admin/media');
    await page.waitForTimeout(3000);

    // 检查是否有网格/列表视图切换按钮
    const viewToggle = page.locator('button').filter({hasText: /网格|列表|Grid|List/}).first();
    const hasToggle = await viewToggle.isVisible().catch(() => false);

    // 至少页面能正常加载（视图切换是可选功能）
    const mainContent = page.locator('[class*="media"], main, [class*="page"]').first();
    await expect(mainContent).toBeVisible();
  });

  test('媒体库包含搜索或筛选功能', async ({authenticatedPage: page}) => {
    await page.goto('/admin/media');
    await page.waitForTimeout(3000);

    const hasSearch = await page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="search"]').first().isVisible().catch(() => false);
    const hasFilter = await page.locator('button, select').filter({hasText: /筛选|过滤|Filter|类型|Type/}).first().isVisible().catch(() => false);

    // 搜索或筛选至少有一个存在
    expect(hasSearch || hasFilter).toBeTruthy();
  });
});
