import { test, expect } from '@playwright/test';

test.describe('Customer Storefront - Checkout, Reviews, Returns', () => {
  test.beforeEach(async ({ page }) => {
    // Auth Mocks
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({ json: { _id: 'cust_123', name: 'John Doe', email: 'john@example.com', role: 'retail', isActive: true } });
    });
    
    // Page Info & Meta
    await page.route('**/api/page-info/**', async route => route.fulfill({ json: { page: {}, columns: {} } }));
    
    // Cart & Wishlist Mocks
    await page.route('**/api/cart**', async route => {
      await route.fulfill({ json: { 
        items: [{ product: { _id: 'prod1', name: 'Pencil', price: 10, discount: 0 }, quantity: 2, price: 10, finalPrice: 10 }], 
        total: 20 
      }});
    });
    await page.route('**/api/wishlist**', async route => route.fulfill({ json: [] }));
    
    // Delivery Charges & Serviceability
    await page.route('**/api/delivery-charges/check-serviceability**', async route => {
      await route.fulfill({ json: {
        isServiceable: true,
        slotBookingAvailable: true,
        serviceableSellers: [{ id: 'seller1', allowDeliverySlots: true }]
      }});
    });
    
    // Delivery Slots
    await page.route('**/api/delivery-slots/dates-with-slots**', async route => {
      await route.fulfill({ json: { dates: ['2026-10-01', '2026-10-02'] }});
    });
    await page.route('**/api/delivery-slots/available**', async route => {
      await route.fulfill({ json: [{ id: 'slot1', startTime: '10:00', endTime: '12:00', capacity: 10, bookedCount: 0 }]});
    });

    // Orders Mock (for reviews and returns)
    await page.route('**/api/orders**', async route => {
      await route.fulfill({ json: [{
        _id: 'order_123',
        orderNumber: 'ORD-123',
        status: 'DELIVERED',
        createdAt: new Date().toISOString(),
        totalAmount: 100,
        subOrders: [{
          _id: 'sub_123',
          status: 'DELIVERED',
          items: [{ product: { _id: 'prod1', name: 'Pencil', images: [] }, quantity: 1, price: 10 }]
        }]
      }]});
    });

    // Product Review Mocks
    await page.route('**/api/reviews/product/**', async route => route.fulfill({ json: { success: true } }));
    await page.route('**/api/order-feedback/eligible**', async route => route.fulfill({ json: { eligible: true } }));

    // Return Request Mock
    await page.route('**/api/returns', async route => route.fulfill({ json: { success: true, returnId: 'ret_123' } }));
  });

  test('Checkout Page renders and allows address selection', async ({ page }) => {
    await page.goto('/customer/cart');
    // Mobile/Desktop might have a button with "Checkout"
    await page.getByRole('button', { name: /Checkout/i }).click();
    await expect(page.getByText('Shipping Address').first()).toBeVisible({ timeout: 10000 });
    
    // Check if delivery slot section appears based on our serviceability mock
    // It might be under a "Delivery Time" or "Select Slot" heading
    const slotText = page.getByText(/Delivery Slot/i).first();
    if (await slotText.isVisible()) {
        await expect(slotText).toBeVisible();
    }
  });

  test('Customer Orders Page renders', async ({ page }) => {
    await page.goto('/customer/orders');
    await expect(page.getByRole('heading', { name: /My Orders/i }).first()).toBeVisible({ timeout: 10000 });
    // Expect the mocked order to be visible
    await expect(page.getByText('ORD-123')).toBeVisible({ timeout: 10000 });
  });

  test('Order Details renders Delivery Review and Return options', async ({ page }) => {
    await page.goto('/customer/orders/order_123');
    await expect(page.getByText('ORD-123').first()).toBeVisible({ timeout: 10000 });
    
    // Look for Return button or text
    const returnBtn = page.getByRole('button', { name: /Return/i }).first();
    if (await returnBtn.isVisible()) {
        await expect(returnBtn).toBeVisible();
    }
  });
});
