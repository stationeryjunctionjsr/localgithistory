import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'fs';

test.describe('Accessibility Audit', () => {
  const routes = [
    '/',
    '/customer/cart',
    '/customer/profile',
    '/admin/dashboard'
  ];

  for (const route of routes) {
    test(`Should not have any automatically detectable accessibility issues on ${route}`, async ({ page }, testInfo) => {
      // Mock API responses if necessary, or assume the app runs
      await page.goto(`http://localhost:3000${route}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1000); // Allow dynamic content to settle
      
      const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
      
      // Save results
      fs.writeFileSync(`a11y-report-${route.replace(/\//g, '-')}.json`, JSON.stringify(accessibilityScanResults, null, 2));

      // Assert that there are no violations
      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }
});
