import { test, expect } from '@playwright/test';

test.describe('Flow 1: Sign up and Login', () => {
  test('User can register and login successfully', async ({ page }) => {
    // Add network listeners
    page.on('request', async req => {
        if (req.url().includes('/api/tracking/error')) {
            try { console.log('FRONTEND ERROR TRACKED:', req.postData()); } catch(e) {}
        }
    });
    page.on('response', res => console.log('<<', res.status(), res.url()));
    page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));

    await page.goto('http://localhost:3000/');
    // Wait for Next.js hydration so window.openAuthModal is available
    await page.waitForTimeout(3000);
    
    // 1. Open the Auth Modal
    // Use the global function exposed for E2E testing to reliably open the modal on both desktop and mobile
    await page.evaluate(() => {
        (window as any).openAuthModal('register');
    });
    
    // Wait for the modal to be visible and ready
    await page.waitForTimeout(500);
    
    // Disable MSG91 SDK to force the frontend to use the local backend /api/auth/send-otp fallback
    await page.evaluate(() => {
        (window as any).disableMSG91 = true;
    });
    
    // 2. Fill Register form
    await page.locator('#reg-name').fill('Playwright Test User');
    await page.locator('#reg-email').fill('playwright_test_' + Date.now() + '@example.com');
    await page.locator('#reg-password').fill('TestPass123!');
    await page.locator('#reg-confirm-password').fill('TestPass123!');
    
    // Generate a unique 10-digit phone number starting with 999
    const phone = '999' + Math.floor(1000000 + Math.random() * 9000000).toString();
    await page.locator('#reg-phone').fill(phone);
    
    // Wait for React state to update
    await page.waitForTimeout(1000);
    


    // Check modal text
    const modalText = await page.locator('.relative.w-full.max-w-md').innerText();
    console.log("Modal text:", modalText);

    // 3. Send OTP
    const sendOtpBtn = page.locator('button', { hasText: 'Send OTP' }).first();
    // We need to wait for the OTP API response to extract the development OTP
    console.log("Clicking Send OTP...");
    const [response] = await Promise.all([
      page.waitForResponse(res => res.url().includes('/api/auth/send-otp')),
      sendOtpBtn.evaluate(btn => (btn as HTMLElement).click())
    ]);
    const responseData = await response.json();
    const otp = responseData.otp;
    console.log('Extracted OTP:', otp);
    if (!otp) {
      throw new Error('OTP was not found in the response!');
    }
    
    // 4. Fill OTP and Verify
    await page.getByPlaceholder('6-digit OTP').fill(otp.toString());
    await page.locator('button', { hasText: 'Verify' }).first().evaluate(btn => (btn as HTMLElement).click());
    
    // Wait for "Phone number verified" text or similar indicator
    await expect(page.locator('text=Phone number verified').first()).toBeVisible({ timeout: 10000 });
    
    // 5. Submit Registration
    // Wait for it to become enabled
    const submitBtn = page.locator('button[type="submit"]', { hasText: 'Register' }).first();
    await expect(submitBtn).toBeEnabled({ timeout: 10000 });
    // Force form submission via JS to bypass any Playwright click interception quirks
    await submitBtn.evaluate((btn) => {
      const form = btn.closest('form');
      if (form) form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      else (btn as HTMLElement).click();
    });
    
    // 6. Verify successful login
    // Registration logs the user in automatically and redirects to /customer
    await expect(page).toHaveURL(/.*\/customer/, { timeout: 15000 });
  });
});
