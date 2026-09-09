import { test, expect } from '@playwright/test';

test.describe('Flow 12: Admin Panel - Config and Finance', () => {
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
    
    // Flow 12 specific mocks
    await page.route('**/api/settings/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/commission/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/ads/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    
    // Referrals will just stay stuck loading if it returns 500, so we mock a valid response structure
    await page.route('**/api/referrals/**', async route => route.fulfill({ 
      status: 200, 
      json: { 
        retail: { segment: 'retail', discountType: 'fixed', discountValue: 0, isActive: false }, 
        business: { segment: 'business', discountType: 'fixed', discountValue: 0, isActive: false } 
      } 
    }));
    
    await page.route('**/api/sla/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/feature-flags/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/delivery-slots/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/orders/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
    await page.route('**/api/payments/**', async route => route.fulfill({ status: 500, json: { detail: 'error' } }));
  });

  test('Payments renders', async ({ page }) => {
    await page.goto('/admin/payments');
    await expect(page.getByRole('heading', { name: /Payment Management/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Commission renders', async ({ page }) => {
    await page.goto('/admin/commission');
    await expect(page.getByRole('heading', { name: /Commission/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Ads renders', async ({ page }) => {
    await page.goto('/admin/ads');
    await expect(page.getByRole('heading', { name: /Ad Campaigns/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Referral Bonus renders', async ({ page }) => {
    await page.goto('/admin/referral-bonus');
    await expect(page.getByRole('heading', { name: /Referral Bonus Settings/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('SLA renders', async ({ page }) => {
    await page.goto('/admin/sla');
    await expect(page.getByRole('heading', { name: /Delivery SLA Report/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Feature Flags renders', async ({ page }) => {
    await page.goto('/admin/feature-flags');
    await expect(page.getByRole('heading', { name: /Feature Flags Management/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Delivery Slots renders', async ({ page }) => {
    await page.goto('/admin/delivery-slots');
    await expect(page.getByRole('heading', { name: /Delivery Slots/i }).first()).toBeVisible({ timeout: 10000 });
  });

  test('Profile renders', async ({ page }) => {
    await page.goto('/admin/profile');
    await expect(page.getByRole('heading', { name: /My Profile/i }).first()).toBeVisible({ timeout: 10000 });
  });
});
