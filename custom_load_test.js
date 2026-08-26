import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
  stages: [
    { duration: '30s', target: 1 },
    { duration: '30s', target: 50 },
    { duration: '30s', target: 100 },
    { duration: '30s', target: 250 },
    { duration: '30s', target: 400 },
    { duration: '30s', target: 500 },
    { duration: '30s', target: 600 },
    { duration: '20m', target: 600 }, // Sustain for 20 minutes
    { duration: '1m', target: 0 },
  ],
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
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
  });

  sleep(Math.random() * 2 + 1);
}
