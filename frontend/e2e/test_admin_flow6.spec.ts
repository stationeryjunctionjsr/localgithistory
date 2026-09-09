import { test, expect } from '@playwright/test';

test.describe('Flow 6: Admin Panel - Collections and Search Tags', () => {
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
    
    // Flow 6 specific mocks
    await page.route('**/api/collections**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/search-tags**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/categories**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/brands**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/products/**', async route => route.fulfill({ json: [] }));
  });

  test('Collections renders', async ({ page }) => {
    await page.goto('/admin/collections');
    await expect(page.getByRole('button', { name: /Add Collection/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Search Tags renders', async ({ page }) => {
    await page.goto('/admin/search-tags');
    await expect(page.getByRole('button', { name: /Add Search Tag/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
