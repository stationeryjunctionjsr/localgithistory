/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  skipTrailingSlashRedirect: true,
  experimental: {
    webpackBuildWorker: false,
  },

  // Skip type-checking during dev builds for faster HMR
  typescript: { ignoreBuildErrors: process.env.NODE_ENV !== 'production' },
  eslint: { ignoreDuringBuilds: process.env.NODE_ENV !== 'production' },

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Image optimisation – serve WebP/AVIF automatically, long CDN TTL
  images: {
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 86400, // 24 h for optimised images
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost' },
      // OCI Object Storage — restrict to the project's specific namespace/bucket hostname.
      // Update the hostname below to match your OCI region and namespace, e.g.:
      //   <namespace>.objectstorage.<region>.oci.customer-oci.com
      { protocol: 'https', hostname: '*.objectstorage.*.oci.customer-oci.com' },
      { protocol: 'https', hostname: '*.objectstorage.*.oraclecloud.com' },
      // Add any other specific CDN / media host here. Avoid wildcards like '**'.
    ],
  },

  async redirects() {
    return [
      {
        source: '/brand/:name',
        destination: '/brands/:name',
        permanent: true,
      },
      {
        source: '/landingpage',
        destination: '/',
        permanent: true,
      },
    ];
  },

  async rewrites() {
    return [
      {
        source: '/api/:path*/',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*/`.replace('/api/api/', '/api/'),
      },
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`.replace('/api/api/', '/api/'),
      },
    ];
  },

  async headers() {
    // CSP, Referrer-Policy, and Permissions-Policy are set dynamically by
    // middleware.ts with a per-request nonce. Only cache-control rules live here.
    const routes = [
      {
        source: '/uploads/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=86400, stale-while-revalidate=604800' },
        ],
      },
      // NOTE: We deliberately do NOT set Cache-Control for /api/* here.
      // The backend sets appropriate Cache-Control headers per endpoint:
      //   - GET /api/products/public  → public, max-age=300, stale-while-revalidate=60
      //   - GET /api/media            → public, max-age=2700, stale-while-revalidate=300
      //   - Mutation endpoints        → no-store (not set here)
      // Setting no-store here would override those backend headers and break
      // browser/CDN caching for public catalog pages.
    ];

    // Long-lived caching for hashed build assets — production only. In dev, caching
    // `/_next/static` as immutable makes the browser keep old webpack chunks across
    // `next dev` restarts while module IDs change, causing:
    // TypeError: Cannot read properties of undefined (reading 'call') (options.factory).
    if (process.env.NODE_ENV === 'production') {
      routes.splice(0, 0, {
        source: '/_next/static/:path*',
        headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }],
      });
    }

    return routes;
  },

  // Enable gzip/brotli compression via the built-in server
  compress: true,

  // Disable webpack cache and build workers in dev mode to prevent file-locking conflicts on Windows
  // webpack: (config, { dev }) => {
  //   if (dev) {
  //     config.cache = false;
  //   }
  //   return config;
  // },

  // Output standalone build for leaner Docker / server deploys (optional)
  output: 'standalone',
};

module.exports = nextConfig;
