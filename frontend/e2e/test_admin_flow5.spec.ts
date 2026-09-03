import { test, expect } from '@playwright/test';

test.describe('Flow 5: Admin Panel - Segments and Discounts', () => {
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

    // Mock background provider requests that otherwise return 401 and trigger a global redirect to /
    await page.route('**/api/notifications**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/cart**', async route => route.fulfill({ json: { items: [], total: 0 } }));
    await page.route('**/api/wishlist**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/order-feedback/eligible**', async route => route.fulfill({ json: { eligible: false } }));
    await page.route('**/api/activity**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/tracking**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/auth/refresh**', async route => route.fulfill({ json: { token: 'fake', refreshToken: 'fake', sessionId: 'fake' }, status: 200 }));
    
    // Flow 5 specific mocks to prevent 401 redirects
    await page.route('**/api/brands/**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/categories/public**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/products/**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/users/**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/bundles/admin/all**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/collections/**', async route => route.fulfill({ json: [] }));
  });

  test('Retail Customer Segments renders', async ({ page }) => {
    await page.route('**/api/customer-segments**', async route => {
      await route.fulfill({ json: [] });
    });
    
    await page.goto('/admin/retail-customer-segments');
    await expect(page.getByRole('heading', { name: /Retail Customer Segments/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Business Customer Segments renders', async ({ page }) => {
    await page.route('**/api/customer-segments**', async route => {
      await route.fulfill({ json: [] });
    });
    
    await page.goto('/admin/business-customer-segments');
    await expect(page.getByRole('heading', { name: /Business Customer Segments/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Retail Discounts renders', async ({ page }) => {
    await page.route('**/api/coupons**', async route => {
      await route.fulfill({ json: [] });
    });
    
    await page.goto('/admin/retail-discounts');
    await expect(page.getByRole('heading', { name: /Retail Discounts/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Business Discounts renders', async ({ page }) => {
    await page.route('**/api/schemes**', async route => {
      await route.fulfill({ json: [] });
    });
    
    await page.goto('/admin/business-discounts');
    await expect(page.getByRole('heading', { name: /Business Discounts/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
