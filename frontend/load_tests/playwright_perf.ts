import { test, expect } from '@playwright/test';

// Define thresholds
const PERFORMANCE_BUDGETS = {
  homepage: {
    maxLCP: 2500, // 2.5s
    maxFID: 100,  // 100ms
    maxCLS: 0.1,  // 0.1
    maxTTFB: 800, // 800ms
  },
  productsPage: {
    maxLCP: 3000,
    maxTTFB: 1000,
  }
};

test.describe('Core Web Vitals & Frontend Performance Vitals', () => {
  const targetUrl = process.env.LOAD_TEST_FRONTEND_URL || 'http://localhost:3000';

  test('Homepage performance budget validation', async ({ page }) => {
    // Inject PerformanceObserver scripts to gather metrics
    const client = await page.context().newCDPSession(page);
    await client.send('Performance.enable');

    const [response] = await Promise.all([
      page.goto(targetUrl),
      page.waitForResponse(res => res.url() === targetUrl || res.url().includes('/api/products')),
    ]);

    // Measure page load and timings using window.performance API
    const metrics = await page.evaluate(() => {
      const perf = window.performance;
      const navigation = perf.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paintEntries = perf.getEntriesByType('paint');
      
      const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint');
      
      return {
        ttfb: navigation ? navigation.responseStart - navigation.requestStart : null,
        domInteractive: navigation ? navigation.domInteractive : null,
        loadTime: navigation ? navigation.loadEventEnd : null,
        fcp: fcp ? fcp.startTime : null,
      };
    });

    console.log('--- Homepage Metrics ---');
    console.log(`TTFB: ${metrics.ttfb?.toFixed(2)} ms`);
    console.log(`DOM Interactive: ${metrics.domInteractive?.toFixed(2)} ms`);
    console.log(`Load Event End: ${metrics.loadTime?.toFixed(2)} ms`);
    console.log(`FCP: ${metrics.fcp?.toFixed(2)} ms`);

    if (metrics.ttfb) {
      expect(metrics.ttfb).toBeLessThan(PERFORMANCE_BUDGETS.homepage.maxTTFB);
    }
  });

  test('Products list loading performance validation', async ({ page }) => {
    const productsUrl = `${targetUrl}/products`;
    
    const startTime = Date.now();
    await page.goto(productsUrl);
    
    // Wait for the grid of products to be rendered
    await page.waitForSelector('[id^="product-card"]', { timeout: 10000 });
    const loadDuration = Date.now() - startTime;
    
    console.log('--- Products Listing Page ---');
    console.log(`Time to load and render products: ${loadDuration} ms`);
    
    expect(loadDuration).toBeLessThan(PERFORMANCE_BUDGETS.productsPage.maxLCP);
  });
});
