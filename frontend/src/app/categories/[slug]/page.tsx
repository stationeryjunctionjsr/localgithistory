import CategoriesDetailClient from '@/components/CategoriesDetailClient';
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
  const canonicalUrl = `https://www.stationeryjunction.com/categories/${encodeURIComponent(slug)}`;
  return {
    title: `${decodedSlug} | Categories | Stationery Junction`,
    description: `Shop for ${decodedSlug} and explore premium stationery.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `${decodedSlug} | Stationery Junction`,
      description: `Shop for ${decodedSlug} and explore premium stationery.`,
      url: canonicalUrl,
      type: 'website',
    },
  };
}

export default async function CategoryDetailPage({ params }: { params: Promise<{ slug: string }> }) {
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

  // Pre-fetch Category Info & Banners
  const [categoriesRes, bannersRes] = await Promise.all([
    fetch(`${baseURL}/categories/public/`, fetchOptions).catch(() => null),
    fetch(
      `${baseURL}/banners/public?pageType=Category&pageId=${encodeURIComponent(slug)}&userRole=guest`,
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

  const [categoriesRaw, bannersRaw] = await Promise.all([
    extractJson(categoriesRes, true),
    extractJson(bannersRes),
  ]);

  // Extract relevant category
  let categoryInfo = null;
  if (categoriesRaw) {
    const list = Array.isArray(categoriesRaw)
      ? categoriesRaw
      : categoriesRaw?.data || categoriesRaw?.categories || [];
    const match =
      list.find((c: any) => (c?.slug || c?.name || '').toLowerCase() === slug.toLowerCase()) ||
      list.find((c: any) => (c?.name || '').toLowerCase() === slug.toLowerCase());
    if (match) {
      categoryInfo = {
        _id: match._id,
        name: match.name || slug,
        slug: match.slug,
        images: match.images || [],
        subCategories: match.subCategories || [],
        isReturnable: match.isReturnable || false,
      };
    }
  }

  const initialBanners = Array.isArray(bannersRaw) ? bannersRaw : [];

  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-white text-xs uppercase tracking-widest text-gray-400">
          Loading Category...
        </div>
      }
    >
      <CategoriesDetailClient
        initialCategoryInfo={categoryInfo || { name: slug }}
        initialBanners={initialBanners}
      />
    </Suspense>
  );
}
