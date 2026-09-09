import { test, expect } from '@playwright/test';

test.describe('Flow 15: Seller Panel - Reporting and Ops', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/auth/me', async route => {
      // The components strictly check for 'wholesaler' role but the layout checks for 'seller' or 'wholesaler' + 'isSellerAdmin'
      await route.fulfill({ json: { 
        _id: 'seller_123', 
        name: 'John Seller', 
        email: 'seller@example.com', 
        role: 'wholesaler', 
        isSellerAdmin: true, 
        isActive: true 
      } });
    });
    await page.route('**/api/page-info/**', async route => { await route.fulfill({ json: { page: {}, columns: {} } }); });
    await page.route('**/api/notifications**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/cart**', async route => route.fulfill({ json: { items: [], total: 0 } }));
    await page.route('**/api/wishlist**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/order-feedback/eligible**', async route => route.fulfill({ json: { eligible: false } }));
    await page.route('**/api/activity**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/tracking**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/auth/refresh**', async route => route.fulfill({ json: { token: 'fake', refreshToken: 'fake', sessionId: 'fake' }, status: 200 }));
    
    // Flow 15 specific mocks
    await page.route('**/api/analytics/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/reports/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/seller/requests/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/requests/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/sla/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/orders/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/users?role=valet**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
  });

  test('Analytics renders', async ({ page }) => {
    await page.goto('/seller-admin/analytics');
    await expect(page.getByRole('heading', { name: /My Analytics/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Reports renders', async ({ page }) => {
    await page.goto('/seller-admin/reports');
    await expect(page.getByRole('heading', { name: /My Reports/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Profile renders', async ({ page }) => {
    await page.goto('/seller-admin/profile');
    await expect(page.getByRole('heading', { name: /My Profile/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Requests renders', async ({ page }) => {
    await page.goto('/seller-admin/requests');
    await expect(page.getByRole('heading', { name: /Support Requests/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('SLA renders', async ({ page }) => {
    await page.goto('/seller-admin/sla');
    await expect(page.getByRole('heading', { name: /Delivery SLA Report/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Valet Scheduler renders', async ({ page }) => {
    await page.goto('/seller-admin/valet-scheduler');
    await expect(page.getByRole('heading', { name: /Valet Scheduler/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
