import { test, expect } from '@playwright/test';

test.describe('Admin - Delivery Setup (Charges, Pincodes, Zones)', () => {
  test.beforeEach(async ({ page }) => {
    // Auth Mocks
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({ json: { _id: 'admin_123', name: 'Super Admin', email: 'admin@example.com', role: 'super_admin', isActive: true } });
    });
    
    // Page Info & Meta
    await page.route('**/api/page-info/**', async route => route.fulfill({ json: { page: {}, columns: {} } }));
    
    // Mock List Endpoints
    await page.route('**/api/delivery-zones**', async route => route.fulfill({ json: [{ _id: 'zone_1', name: 'North Zone', defaultCapacity: 50, isActive: true }] }));
    await page.route('**/api/pincodes**', async route => route.fulfill({ json: [{ _id: 'pin_1', code: '110001', city: 'Delhi', state: 'Delhi', isActive: true }] }));
    await page.route('**/api/delivery-charges**', async route => route.fulfill({ json: [{ _id: 'charge_1', charge: 50, minCartValue: 500, isActive: true }] }));
  });

  test('Delivery Zones renders', async ({ page }) => {
    await page.goto('/admin/delivery-zones');
    await expect(page.getByRole('heading', { name: /Delivery Zones/i }).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('North Zone')).toBeVisible({ timeout: 10000 });
  });

  test('Pincodes renders', async ({ page }) => {
    await page.goto('/admin/pincodes');
    await expect(page.getByRole('heading', { name: /Pincodes/i }).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('110001')).toBeVisible({ timeout: 10000 });
  });

  test('Delivery Charges renders', async ({ page }) => {
    await page.goto('/admin/delivery-charges');
    await expect(page.getByRole('heading', { name: /Delivery Charges/i }).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('500').first()).toBeVisible({ timeout: 10000 }); // minCartValue
  });
});
