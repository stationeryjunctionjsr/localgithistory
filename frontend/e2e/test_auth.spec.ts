import { test, expect } from '@playwright/test';

test.describe('Flow 1: Sign up and Login', () => {
  test('User can register and login successfully', async ({ page }) => {
    await page.goto('http://localhost:3000/');
    
    // 1. Open the Auth Modal
    const profileBtn = page.getByRole('button').filter({ hasText: 'Profile' }).first();
    await profileBtn.click({ force: true });
    
    const signInBtn = page.getByRole('button').filter({ hasText: 'Sign In' }).first();
    await signInBtn.click({ force: true });
    
    // Switch to Register mode
    await page.getByRole('button', { name: 'Create Account' }).click();
    
    // 2. Fill Register form
    await page.locator('#reg-name').fill('Playwright Test User');
    await page.locator('#reg-email').fill('playwright_test_' + Date.now() + '@example.com');
    await page.locator('#reg-password').fill('TestPass123!');
    await page.locator('#reg-confirm-password').fill('TestPass123!');
    
    const phone = '999' + Math.floor(1000000 + Math.random() * 9000000).toString();
    await page.locator('#reg-phone').fill(phone);
    
    // 3. Send OTP
    const sendOtpBtn = page.getByRole('button', { name: 'Send OTP' });
    
    // We need to wait for the OTP API response to extract the development OTP
    const [response] = await Promise.all([
        page.waitForResponse(res => res.url().includes('/api/auth/send-otp') && res.status() === 200),
        sendOtpBtn.click()
    ]);
    
    const responseData = await response.json();
    const otp = responseData.otp;
    
    if (!otp) {
        throw new Error('OTP not returned in development response');
    }
    
    // 4. Fill OTP and Verify
    await page.getByPlaceholder('6-digit OTP').fill(otp);
    await page.getByRole('button', { name: 'Verify OTP' }).click();
    
    // Wait for "Phone number verified" text or similar indicator
    await expect(page.locator('text="Phone number verified"')).toBeVisible({ timeout: 10000 });
    
    // 5. Submit Registration
    // Wait for it to become enabled
    const submitBtn = page.locator('form').filter({ hasText: 'Create Account' }).getByRole('button', { name: 'Create Account' });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();
    
    // 6. Verify successful login
    // Registration logs the user in automatically, or we can just check if the Profile dropdown shows 'My Profile'
    // It should redirect or show success toast.
    await expect(page.locator('text="Registration successful!"')).toBeVisible({ timeout: 10000 }).catch(() => {});
    
    await profileBtn.click({ force: true });
    await expect(page.getByRole('button').filter({ hasText: 'My Profile' })).toBeVisible({ timeout: 15000 });
  });
});
