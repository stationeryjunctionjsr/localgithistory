import { test, expect } from '@playwright/test';

test.describe('Flow 10: Admin Panel - Content and Reviews', () => {
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
    
    // Flow 10 specific mocks - Force 500 so they don't crash from invalid schema mocks
    await page.route('**/api/content/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/faq/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/settings/google-rating**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/reviews/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/products**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/users**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
  });

  test('About Us Management renders', async ({ page }) => {
    await page.goto('/admin/about-management');
    await expect(page.getByRole('heading', { name: /About Us Page/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Privacy Management renders', async ({ page }) => {
    await page.goto('/admin/privacy-management');
    await expect(page.getByRole('heading', { name: /Privacy Policy/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('FAQ Management renders', async ({ page }) => {
    await page.goto('/admin/faq-management');
    await expect(page.getByRole('heading', { name: /FAQ Management/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Google Reviews renders', async ({ page }) => {
    await page.goto('/admin/google-reviews');
    await expect(page.getByRole('heading', { name: /Google Reviews Integration/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Reviews Moderation renders', async ({ page }) => {
    await page.goto('/admin/reviews');
    await expect(page.getByRole('heading', { name: /Review & Rating Moderation/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
