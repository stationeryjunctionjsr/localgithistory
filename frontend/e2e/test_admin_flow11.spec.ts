import { test, expect } from '@playwright/test';

test.describe('Flow 11: Admin Panel - Support and Operations', () => {
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
    
    // Flow 11 specific mocks
    // Return 500 error for all these arrays so components gracefully degrade to empty states
    await page.route('**/api/support/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/feedback/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/requests/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/push-notifications/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/analytics/pincode-searches**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
  });

  test('Support renders', async ({ page }) => {
    await page.goto('/admin/support');
    await expect(page.getByRole('heading', { name: /Support Tickets/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Feedback renders', async ({ page }) => {
    await page.goto('/admin/feedback');
    await expect(page.getByRole('heading', { name: /Customer Feedback/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Requests renders', async ({ page }) => {
    await page.goto('/admin/requests');
    await expect(page.getByRole('heading', { name: /Product Availability Requests/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Seller Requests renders', async ({ page }) => {
    await page.goto('/admin/seller-requests');
    await expect(page.getByRole('heading', { name: /Seller Requests/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Push Notifications renders', async ({ page }) => {
    await page.goto('/admin/push-notifications');
    await expect(page.getByRole('heading', { name: /Push Notification Management/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Pincode Searches renders', async ({ page }) => {
    await page.goto('/admin/pincode-searches');
    await expect(page.getByRole('heading', { name: /Pincode Searches & Hyperlocal Demand/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
