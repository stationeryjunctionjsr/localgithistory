import { test, expect } from '@playwright/test';

test.describe('Flow 8: Admin Panel - Analytics and Financials', () => {
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
    
    // Flow 8 specific mocks
    // Return 500 so the components fall back to their catch blocks and set default safe values
    await page.route('**/api/reports**', async route => route.fulfill({ status: 500, json: { detail: 'mock error' } }));
    await page.route('**/api/analytics**', async route => route.fulfill({ status: 500, json: { detail: 'mock error' } }));
    
    // For arrays, return empty arrays to avoid map() crashes
    await page.route('**/api/orders/valet-payouts**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/settings**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/seller-orders/payouts**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/users?role=seller**', async route => route.fulfill({ json: [] }));
  });

  test('Reports renders', async ({ page }) => {
    await page.goto('/admin/reports');
    await expect(page.getByRole('heading', { name: /Business intelligence/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Analytics renders', async ({ page }) => {
    await page.goto('/admin/analytics');
    await expect(page.getByRole('heading', { name: /Analytics/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Valet Payout renders', async ({ page }) => {
    await page.goto('/admin/valet-payout');
    await expect(page.getByRole('heading', { name: /Valet Payout/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Seller Payouts renders', async ({ page }) => {
    await page.goto('/admin/seller-payouts');
    await expect(page.getByRole('heading', { name: /Seller Payouts/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
