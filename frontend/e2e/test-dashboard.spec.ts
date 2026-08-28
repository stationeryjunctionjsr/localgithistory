import { test, expect } from '@playwright/test';
test('Dashboard renders without crashing', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(3000);
  await page.evaluate(() => (window as any).openAuthModal('register'));
  
  await page.fill('#reg-name', 'Test User');
  await page.fill('input[name="email"]', `test_${Date.now()}@test.com`);
  await page.fill('input[name="password"]', 'Pass123!');
  await page.fill('input[name="confirmPassword"]', 'Pass123!');
  await page.fill('input[name="phone"]', '9' + Math.floor(Math.random() * 1000000000).toString().padEnd(9, '0'));
  
  await page.click('button:has-text("Send OTP")');
  await page.waitForTimeout(1000);
  
  await page.evaluate(() => {
    const btn = document.querySelector('button[type="submit"]');
    if (btn) {
      const form = btn.closest('form');
      if (form) form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
  });

  await expect(page).toHaveURL(/.*\/customer/, { timeout: 15000 });
  await expect(page.locator('text=My Orders')).toBeVisible({ timeout: 10000 });
});
