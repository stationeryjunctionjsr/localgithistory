import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Realistic spike test:
// Simulates a sudden surge of real users — each hitting ONE endpoint per iteration,
// then pausing to read. This avoids the artificial 4x socket multiplier of http.batch().
export const options = {
  stages: [
    // Baseline: 10 users for 20s
    { duration: '20s', target: 10 },

    // Sudden spike to 500 users in 10s
    { duration: '10s', target: 500 },

    // Hold spike at 500 users for 30s
    { duration: '30s', target: 500 },

    // Drop back to 10 users in 10s
    { duration: '10s', target: 10 },

    // Recovery evaluation: 10 users for 30s
    { duration: '30s', target: 10 },

    // Cool down
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    // 95% of requests during spike & recovery under 500ms
    http_req_duration: ['p(95)<500'],
    // Overall error rate under 1%
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = 'http://localhost:8000';

// Public catalog endpoints a real user would hit, one at a time
const ENDPOINTS = [
  { url: `${BASE_URL}/api/products/public`,   label: 'products' },
  { url: `${BASE_URL}/api/categories/public`, label: 'categories' },
  { url: `${BASE_URL}/api/brands/public`,     label: 'brands' },
  { url: `${BASE_URL}/api/banners/public`,    label: 'banners' },
];

export default function () {
  // Each iteration: one request from a random endpoint
  const endpoint = randomItem(ENDPOINTS);

  const res = http.get(endpoint.url);

  check(res, {
    [`${endpoint.label} status is 200`]: (r) => r.status === 200,
    [`${endpoint.label} response time < 500ms`]: (r) => r.timings.duration < 500,
  });

  // Simulate user think/read time: 1–3 seconds between actions
  sleep(Math.random() * 2 + 1);
}
