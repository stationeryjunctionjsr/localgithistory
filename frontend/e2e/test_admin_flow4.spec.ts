import { test, expect } from '@playwright/test';

test.describe('Flow 4: Admin Panel - Delivery Charges, Pincodes, Zones', () => {
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

    await page.route('**/api/categories**', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: [{ _id: 'cat_1', name: 'Mock Category', description: 'Mock Description', isActive: true }] });
      } else {
        await route.fulfill({ json: { success: true }, status: 201 });
      }
    });

    await page.route('**/api/category-tags**', async route => {
      await route.fulfill({ json: [{ _id: 'tag_1', name: 'Mock Tag' }] });
    });
    
    await page.route('**/api/page-info/**', async route => {
      await route.fulfill({ json: { page: {}, columns: {} } });
    });

    page.on('response', response => {
      if (response.status() === 401) {
        console.log(`[401] ${response.url()}`);
      }
    });

    // Mock background provider requests that otherwise return 401 and trigger a global redirect to /
    await page.route('**/api/notifications**', async route => {
      await route.fulfill({ json: [] });
    });
    await page.route('**/api/cart**', async route => {
      await route.fulfill({ json: { items: [], total: 0 } });
    });
    await page.route('**/api/wishlist**', async route => {
      await route.fulfill({ json: [] });
    });
    await page.route('**/api/order-feedback/eligible**', async route => {
      await route.fulfill({ json: { eligible: false } });
    });
    await page.route('**/api/activity**', async route => {
      await route.fulfill({ json: { success: true } });
    });
    await page.route('**/api/tracking**', async route => {
      await route.fulfill({ json: { success: true } });
    });
    await page.route('**/api/auth/refresh**', async route => {
      await route.fulfill({ json: { token: 'fake', refreshToken: 'fake', sessionId: 'fake' }, status: 200 });
    });
    
    // Make sure we mock the analytics dashboard data since this flow might load the dashboard stats
    await page.route('**/api/analytics/dashboard-data', async route => {
      await route.fulfill({ json: {
        totalRevenue: 0,
        totalOrders: 0,
        averageOrderValue: 0,
        conversionRate: 0,
        revenueData: [],
        ordersByStatus: []
      } });
    });
  });

  test('Delivery Zones renders', async ({ page }) => {
    // Intercept the API call for delivery zones to provide mock data
    await page.route('**/api/delivery-zones**', async route => {
      await route.fulfill({ json: [{ _id: 'zone_1', name: 'Mock Zone', active: true }] });
    });
    
    await page.goto('/admin/delivery-zones');
    
    // Check if the page title renders (could be "Delivery Zones" or similar)
    await expect(page.locator('h1').filter({ hasText: 'Zone' })).toBeVisible({ timeout: 10000 });
  });

  test('Delivery Charges renders', async ({ page }) => {
    // Intercept the API call for delivery charges
    await page.route('**/api/delivery-charges**', async route => {
      await route.fulfill({ json: [{ _id: 'charge_1', zone: 'zone_1', cost: 50, active: true }] });
    });
    
    await page.goto('/admin/delivery-charges');
    
    // Check if the page title renders
    await expect(page.locator('h1').filter({ hasText: 'Charge' })).toBeVisible({ timeout: 10000 });
  });
});
