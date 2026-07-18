import { test, expect } from '@playwright/test';

test('Critical Flow: Navigation and checking categories', async ({ page }) => {
  // Go to homepage
  await page.goto('/');

  // Check if categories section is visible (using a more specific and visible selector)
  await expect(page.locator('h2:has-text("Shop by Category")').first()).toBeVisible();

  // Try navigating to a catalog page
  const categoryLink = page.locator('a[href="/categories"]').filter({ visible: true }).first();
  if (await categoryLink.isVisible()) {
    await categoryLink.click();
    await expect(page).toHaveURL(/.*categories/);
  }
});
