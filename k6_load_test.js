import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Baseline Load Test (600 VUs)
export const options = {
  stages: [
    // Baseline: 1 user
    { duration: '30s', target: 1 },
    // Ramp to 150
    { duration: '30s', target: 150 },
    // Ramp to 350
    { duration: '1m', target: 350 },
    // Peak at 600 users
    { duration: '2m', target: 600 },
    // Cool down
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    // 95% of all requests must complete within 500ms
    http_req_duration: ['p(95)<500'],
    // Error rate must stay below 1%
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = 'http://localhost:8000';

const ENDPOINTS = [
  { url: `${BASE_URL}/api/products/public`,   label: 'products' },
  { url: `${BASE_URL}/api/categories/public`, label: 'categories' },
  { url: `${BASE_URL}/api/brands/public`,     label: 'brands' },
  { url: `${BASE_URL}/api/banners/public`,    label: 'banners' },
];

export default function () {
  const endpoint = randomItem(ENDPOINTS);
  const res = http.get(endpoint.url);

  check(res, {
    [`${endpoint.label} status is 200`]: (r) => r.status === 200,
    [`${endpoint.label} response time < 500ms`]: (r) => r.timings.duration < 500,
  });

  // Simulate user think/read time: 1–3 seconds between actions
  sleep(Math.random() * 2 + 1);
}
