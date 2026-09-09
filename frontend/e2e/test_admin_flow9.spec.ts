import { test, expect } from '@playwright/test';

test.describe('Flow 9: Admin Panel - User Management', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept auth to fake an admin login
    await page.route('**/api/auth/me', async route => {
      const json = {
        _id: 'admin_123',
        name: 'Super Admin',
        email: 'admin@example.com',
        role: 'super_admin',
        isActive: true,
      };
      await route.fulfill({ json });
    });

    await page.route('**/api/page-info/**', async route => {
      await route.fulfill({ json: { page: {}, columns: {} } });
    });

    // Mock background provider requests to prevent 401 redirects
    await page.route('**/api/notifications**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/cart**', async route => route.fulfill({ json: { items: [], total: 0 } }));
    await page.route('**/api/wishlist**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/order-feedback/eligible**', async route => route.fulfill({ json: { eligible: false } }));
    await page.route('**/api/activity**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/tracking**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/auth/refresh**', async route => route.fulfill({ json: { token: 'fake', refreshToken: 'fake', sessionId: 'fake' }, status: 200 }));
    
    // Flow 9 specific mocks
    await page.route('**/api/users**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/orders**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/system-settings**', async route => route.fulfill({ json: {} }));
    await page.route('**/api/settings**', async route => route.fulfill({ json: { commissionRates: [] } }));
  });

  test('Users renders', async ({ page }) => {
    await page.goto('/admin/users');
    await expect(page.getByRole('heading', { name: /Users/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Sellers renders', async ({ page }) => {
    await page.goto('/admin/sellers');
    await expect(page.getByRole('heading', { name: /Sellers/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Valets renders', async ({ page }) => {
    await page.goto('/admin/valets');
    await expect(page.getByRole('heading', { name: /Valets/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
