import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
  vus: __ENV.VUS,
  duration: __ENV.DURATION || '2m',
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
