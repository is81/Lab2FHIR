// @ts-check
import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5173';

test.describe('权限模式：公开查询 + 导入需登录', () => {

  test('首页无需登录即可访问', async ({ page }) => {
    await page.goto(BASE);
    // 应直接进入首页，不会被重定向到 /login
    await expect(page).not.toHaveURL(/\/login/);
    // 页面标题
    await expect(page.locator('.app-header h2')).toHaveText('首页');
    // 统计卡片应可见
    await expect(page.locator('.stat-card').first()).toBeVisible({ timeout: 5000 });
  });

  test('报告列表无需登录即可访问', async ({ page }) => {
    await page.goto(BASE + '/reports');
    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.locator('.app-header h2')).toHaveText('报告列表');
    // 报告表格或空状态应可见
    await expect(page.locator('.el-table, .el-empty').first()).toBeVisible({ timeout: 5000 });
  });

  test('报告详情无需登录即可访问', async ({ page }) => {
    // 访问已知的 report id=1
    await page.goto(BASE + '/reports/1');
    await expect(page).not.toHaveURL(/\/login/);
    // 详情页应显示解析结果、PDF、FHIR 三栏或至少标题
    await expect(page.locator('.detail-layout, .app-header')).toBeVisible({ timeout: 5000 });
  });

  test('导入页可见且无需登录', async ({ page }) => {
    await page.goto(BASE + '/import');
    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.locator('.app-header h2')).toHaveText('导入报告');
    // 拖拽上传区域应可见
    await expect(page.locator('.el-upload-dragger').first()).toBeVisible({ timeout: 5000 });
  });

  test('登录 API：错误凭据返回 401', async ({ request }) => {
    const resp = await request.post(BASE + '/api/auth/login', {
      data: { username: 'admin', password: 'wrong' }
    });
    expect(resp.status()).toBe(401);
    const body = await resp.json();
    expect(body.detail).toBe('用户名或密码错误');
  });

  test('登录 API：正确凭据获得 JWT token', async ({ request }) => {
    const resp = await request.post(BASE + '/api/auth/login', {
      data: { username: 'admin', password: 'admin123' }
    });
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.access_token).toBeTruthy();
    expect(body.user.role).toBe('pathology_staff');
    expect(body.token_type).toBe('bearer');
  });

  test('未登录时 POST /convert 被拒绝（401）', async ({ request }) => {
    // 发送不含文件的请求 → 422，但认证层先拦截返回 401
    const resp = await request.post(BASE + '/api/convert');
    expect(resp.status()).toBe(401);
    const body = await resp.json();
    expect(body.detail).toBe('请先登录');
  });

  test('登录后携带 token 可访问 stats', async ({ request }) => {
    // 先登录
    const loginResp = await request.post(BASE + '/api/auth/login', {
      data: { username: 'admin', password: 'admin123' }
    });
    const { access_token } = await loginResp.json();

    // 用 token 访问 stats
    const statsResp = await request.get(BASE + '/api/stats', {
      headers: { 'Authorization': `Bearer ${access_token}` }
    });
    expect(statsResp.status()).toBe(200);
    const body = await statsResp.json();
    expect(body).toHaveProperty('total');
    expect(body).toHaveProperty('type_counts');
  });

  test('GET /reports 无需登录即可访问', async ({ request }) => {
    const resp = await request.get(BASE + '/api/reports');
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
  });

  test('GET /stats 无需登录即可访问', async ({ request }) => {
    const resp = await request.get(BASE + '/api/stats');
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toHaveProperty('total');
  });

});
