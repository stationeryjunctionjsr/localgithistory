import { test, expect } from '@playwright/test';

test.describe('Flow 14: Seller Panel - Core', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept auth to fake a seller login
    await page.route('**/api/auth/me', async route => {
      const json = {
        _id: 'seller_123',
        name: 'John Seller',
        email: 'seller@example.com',
        role: 'seller',
        isActive: true,
        sellerPermissions: { allowDeliverySlots: true }
      };
      await route.fulfill({ json });
    });

    await page.route('**/api/page-info/**', async route => {
      await route.fulfill({ json: { page: {}, columns: {} } });
    });

    // Mock background provider requests
    await page.route('**/api/notifications**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/cart**', async route => route.fulfill({ json: { items: [], total: 0 } }));
    await page.route('**/api/wishlist**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/order-feedback/eligible**', async route => route.fulfill({ json: { eligible: false } }));
    await page.route('**/api/activity**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/tracking**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/auth/refresh**', async route => route.fulfill({ json: { token: 'fake', refreshToken: 'fake', sessionId: 'fake' }, status: 200 }));
    
    // Flow 14 specific mocks - Force 500 so they don't crash from invalid schema mocks
    await page.route('**/api/products/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/categories/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/orders/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/seller/delivery-settings/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/seller/delivery-slots/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/delivery-slots/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/seller/discounts/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/discounts/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    // Dashboard analytics
    await page.route('**/api/analytics/seller/kpi**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/analytics/seller/recent-orders**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/analytics/seller/top-products**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/seller/settings/delivery**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
  });

  test('Dashboard root renders', async ({ page }) => {
    await page.goto('/seller-admin');
    await expect(page.getByRole('heading', { name: /Welcome back/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Products renders', async ({ page }) => {
    await page.goto('/seller-admin/products');
    await expect(page.getByRole('heading', { name: /Products/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Categories renders', async ({ page }) => {
    await page.goto('/seller-admin/categories');
    await expect(page.getByRole('heading', { name: /My Categories/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Orders renders', async ({ page }) => {
    await page.goto('/seller-admin/orders');
    await expect(page.getByRole('heading', { name: /My Orders/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Delivery Settings renders', async ({ page }) => {
    await page.goto('/seller-admin/delivery-settings');
    await expect(page.getByRole('heading', { name: /Delivery & Serviceability Settings/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Delivery Slots renders', async ({ page }) => {
    await page.goto('/seller-admin/delivery-slots');
    await expect(page.getByRole('heading', { name: /Delivery Slots/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Discounts renders', async ({ page }) => {
    await page.goto('/seller-admin/discounts');
    await expect(page.getByRole('heading', { name: /My Discounts/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
