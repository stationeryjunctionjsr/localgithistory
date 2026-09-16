import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Nonce-based Content Security Policy middleware.
 *
 * A fresh cryptographic nonce is generated on every request. It is:
 *  - Embedded in the CSP header so only scripts carrying this nonce run.
 *  - Forwarded as the `x-nonce` request header so layout.tsx can pass it
 *    to <Script nonce={nonce}> and any inline dangerouslySetInnerHTML blocks.
 *
 * Once layout.tsx and all <Script> components are updated to use the nonce,
 * remove 'unsafe-inline' from script-src.  'strict-dynamic' is already present
 * so scripts loaded by nonced scripts are trusted automatically.
 *
 * TODO (next phase):
 *   1. Update layout.tsx to read x-nonce and pass it to all <Script> tags
 *   2. Remove 'unsafe-inline' from script-src below
 *   3. Test GTM / Clarity / MSG91 still load correctly
 *   4. Evaluate removing 'unsafe-eval' (may break Next.js Turbopack — test first)
 */

export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? '';

  const cspDirectives = [
    `default-src 'self'`,
    // 'unsafe-inline' kept temporarily until layout.tsx / <Script> tags carry the nonce.
    // 'strict-dynamic' means browsers that support it will trust scripts loaded by nonced
    // scripts automatically; the explicit domain list is a fallback for older browsers.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com https://www.clarity.ms https://verify.msg91.com https://pass.hostnsoft.com`,
    `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`,
    `font-src 'self' https://fonts.gstatic.com`,
    `img-src 'self' data: blob: https:`,
    `connect-src 'self' https://www.google-analytics.com https://www.clarity.ms https://control.msg91.com https://verify.msg91.com https://pass.hostnsoft.com ${apiUrl}`.trim(),
    `frame-src 'self' https://www.google.com https://www.googletagmanager.com https://verify.msg91.com https://pass.hostnsoft.com`,
    `object-src 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
  ].join('; ');

  // Forward nonce to the app as a request header.
  // layout.tsx reads it with: headers().get('x-nonce')
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-nonce', nonce);

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  });

  response.headers.set('Content-Security-Policy', cspDirectives);
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=(self), payment=()',
  );

  return response;
}

export const config = {
  matcher: [
    // Run on all routes except static assets — those get headers from next.config.js
    {
      source: '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|bmp|css|js|woff2?|ttf|eot)$).*)',
      missing: [
        { type: 'header', key: 'next-router-prefetch' },
        { type: 'header', key: 'purpose', value: 'prefetch' },
      ],
    },
  ],
};
