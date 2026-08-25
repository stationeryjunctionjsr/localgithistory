import BrandDetailClient from '@/components/BrandDetailClient';
import { Metadata } from 'next';
import { Suspense } from 'react';

export const revalidate = 300; // 5 minutes caching
export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const decodedSlug = decodeURIComponent(slug);
  const canonicalUrl = `https://www.stationeryjunction.com/brands/${encodeURIComponent(slug)}`;
  return {
    title: `${decodedSlug} | Brands | Stationery Junction`,
    description: `Shop authentic products from ${decodedSlug}.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `${decodedSlug} | Stationery Junction`,
      description: `Shop authentic products from ${decodedSlug}.`,
      url: canonicalUrl,
      type: 'website',
    },
  };
}

export default async function BrandDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  if (!baseURL) {
    throw new Error('NEXT_PUBLIC_API_URL is not defined');
  }
  const { slug: rawSlug } = await params;
  const slug = decodeURIComponent(rawSlug);
  const fetchOptions: RequestInit = {
    next: { revalidate: 300 },
    headers: { 'Content-Type': 'application/json' },
  };

  const [brandsRes, bannersRes] = await Promise.all([
    fetch(`${baseURL}/brands/public`, fetchOptions).catch(() => null),
    fetch(
      `${baseURL}/banners/public?pageType=Brand&pageId=${encodeURIComponent(slug)}&userRole=guest`,
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

  const [brandsRaw, bannersRaw] = await Promise.all([
    extractJson(brandsRes, true),
    extractJson(bannersRes),
  ]);

  let brandInfo = null;
  if (brandsRaw) {
    const list = Array.isArray(brandsRaw) ? brandsRaw : brandsRaw?.brands || brandsRaw?.data || [];
    const match = list.find((b: any) => (b?.name || '').toLowerCase() === slug.toLowerCase());
    if (match) {
      brandInfo = {
        _id: match._id,
        name: match.name || slug,
        logoUrl: match.logoUrl,
        logo: match.logo,
        description: match.description,
      };
    }
  }

  const initialBanners = Array.isArray(bannersRaw) ? bannersRaw.filter((b: any) => b.isActive) : [];

  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-white text-xs uppercase tracking-widest text-gray-400">
          Loading Brand...
        </div>
      }
    >
      <BrandDetailClient
        initialBrandInfo={brandInfo || { name: slug }}
        initialBanners={initialBanners}
      />
    </Suspense>
  );
}
