import BrandsClient from '@/components/BrandsClient';
import { Suspense } from 'react';
import { Metadata } from 'next';
import { BrandsPageSkeleton } from '@/components/PageSkeletons';

export const dynamic = 'force-dynamic';

export const revalidate = 300; // 5 minutes caching

export const metadata: Metadata = {
  title: 'Brands | Stationery Junction',
  description: 'Discover premium stationery from our trusted brand partners.',
  alternates: { canonical: 'https://www.stationeryjunction.com/brands' },
  openGraph: {
    title: 'Brands | Stationery Junction',
    description: 'Discover premium stationery from our trusted brand partners.',
    url: 'https://www.stationeryjunction.com/brands',
    type: 'website',
  },
};

export default async function BrandsPage() {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  if (!baseURL) {
    throw new Error('NEXT_PUBLIC_API_URL is not defined');
  }
  const fetchOptions: RequestInit = {
    next: { revalidate: 300 },
    headers: { 'Content-Type': 'application/json' },
  };

  const [brandsRes, catsRes, bannerRes] = await Promise.all([
    fetch(`${baseURL}/brands/public`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/categories/public`, fetchOptions).catch(() => null),
    fetch(
      `${baseURL}/banners/public?pageType=all_brands&position=all_brands&userRole=guest`,
      fetchOptions
    ).catch(() => null),
  ]);

  const extractJson = async (res: Response | null, critical: boolean = false) => {
    if (!res || !res.ok) {
      if (critical) throw new Error(`API failed with status ${res?.status}`);
      return null;
    }
    return res.json().catch((e) => {
      if (critical) throw e;
      return null;
    });
  };
  const [brandsRaw, catsRaw, bannerRaw] = await Promise.all([
    extractJson(brandsRes, true),
    extractJson(catsRes),
    extractJson(bannerRes),
  ]);

  const brands = Array.isArray(brandsRaw?.data)
    ? brandsRaw.data
    : brandsRaw?.brands || brandsRaw || [];
  const categories = Array.isArray(catsRaw?.data) ? catsRaw.data : catsRaw || [];

  // Filter out inactive banners and ensure target audience logic applies
  const activeBanners = Array.isArray(bannerRaw)
    ? bannerRaw.filter(
        (b: any) => b.isActive && (b.targetAudience === 'all' || b.targetAudience === 'guest')
      )
    : [];

  return (
    <Suspense fallback={<BrandsPageSkeleton />}>
      <BrandsClient
        initialBrands={brands}
        initialCategories={categories}
        initialBanners={activeBanners}
      />
    </Suspense>
  );
}
