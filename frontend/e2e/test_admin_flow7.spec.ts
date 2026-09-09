import { test, expect } from '@playwright/test';

test.describe('Flow 7: Admin Panel - Orders and Returns', () => {
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
    
    // Flow 7 specific mocks
    await page.route('**/api/orders**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/returns**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/returns/admin/all**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/users?role=valet**', async route => route.fulfill({ json: [] }));
  });

  test('Order Management renders', async ({ page }) => {
    await page.goto('/admin/orders');
    await expect(page.getByRole('heading', { name: /Order Management/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Returns Management renders', async ({ page }) => {
    await page.goto('/admin/returns-management');
    await expect(page.getByRole('heading', { name: /Returns Management/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Seller Orders renders', async ({ page }) => {
    // This endpoint might be named differently, so globally mock everything seller-order related
    await page.route('**/api/seller-orders**', async route => route.fulfill({ json: [] }));
    
    await page.goto('/admin/seller-orders');
    await expect(page.getByRole('heading', { name: /Seller Orders/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
