import { MetadataRoute } from 'next';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://www.stationeryjunction.com';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/admin/', '/customer/orders/', '/customer/cart/', '/wholesaler/cart/'],
    },
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}
