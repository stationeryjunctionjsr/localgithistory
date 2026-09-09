import { test, expect } from '@playwright/test';

test.describe('Flow 13: Admin Panel - Misc', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({ json: { _id: 'admin_123', name: 'Super Admin', email: 'admin@example.com', role: 'super_admin', isActive: true } });
    });
    await page.route('**/api/page-info/**', async route => { await route.fulfill({ json: { page: {}, columns: {} } }); });
    await page.route('**/api/notifications**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/cart**', async route => route.fulfill({ json: { items: [], total: 0 } }));
    await page.route('**/api/wishlist**', async route => route.fulfill({ json: [] }));
    await page.route('**/api/order-feedback/eligible**', async route => route.fulfill({ json: { eligible: false } }));
    await page.route('**/api/activity**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/tracking**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/auth/refresh**', async route => route.fulfill({ json: { token: 'fake', refreshToken: 'fake', sessionId: 'fake' }, status: 200 }));
    
    await page.route('**/api/contacts/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
  });

  test('Contacts renders', async ({ page }) => {
    await page.goto('/admin/contacts');
    await expect(page.getByRole('heading', { name: /Contact Management/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
