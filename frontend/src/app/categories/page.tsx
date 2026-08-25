import CategoriesClient from '@/components/CategoriesClient';
import { Suspense } from 'react';
import type { Metadata } from 'next';
import { CategoriesPageSkeleton } from '@/components/PageSkeletons';

export const dynamic = 'force-dynamic';

export const revalidate = 300; // 5 minutes caching

export const metadata: Metadata = {
  title: 'Browse Categories | Stationery Junction',
  description:
    'Explore all stationery categories — notebooks, pens, art supplies, office essentials and more. Find exactly what you need at Stationery Junction.',
  alternates: { canonical: 'https://www.stationeryjunction.com/categories' },
  openGraph: {
    title: 'Browse Categories | Stationery Junction',
    description:
      'Explore all stationery categories — notebooks, pens, art supplies, office essentials and more.',
    url: 'https://www.stationeryjunction.com/categories',
    type: 'website',
  },
};

export default async function CategoriesPage() {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  if (!baseURL) {
    throw new Error('NEXT_PUBLIC_API_URL is not defined');
  }
  const fetchOptions: RequestInit = {
    next: { revalidate: 300 },
    headers: { 'Content-Type': 'application/json' },
  };

  const [categoryRes, tagRes, bannerRes] = await Promise.all([
    fetch(`${baseURL}/categories/public/`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/category-tags/active`, fetchOptions).catch(() => null),
    fetch(
      `${baseURL}/banners/public/?position=categories&pageType=all_categories&userRole=guest`,
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
  const [categoriesRaw, tagRaw, bannerRaw] = await Promise.all([
    extractJson(categoryRes, true),
    extractJson(tagRes),
    extractJson(bannerRes),
  ]);

  // Format categories
  const rRaw = categoriesRaw?.data ?? categoriesRaw ?? [];
  const categoriesList = Array.isArray(rRaw)
    ? rRaw
        .map((c: any) =>
          typeof c === 'object' && c !== null && (c.name || c.title)
            ? {
                _id: c._id,
                name: c.name || c.title,
                slug: c.slug,
                images: c.images || [],
                categoryTags: c.categoryTags || [],
              }
            : {
                name: typeof c === 'string' ? c : String(c?.name ?? c),
                images: [],
                categoryTags: [],
              }
        )
        .filter((c: any) => c && c.name)
    : [];

  // Format tags
  const tags = Array.isArray(tagRaw) ? tagRaw : tagRaw?.data || [];
  const tagList = tags.filter((t: any) => t && t.name);

  // Format banners
  const activeBanners = Array.isArray(bannerRaw)
    ? bannerRaw.filter(
        (b: any) => b.isActive && (b.targetAudience === 'all' || b.targetAudience === 'guest')
      )
    : [];

  return (
    <Suspense fallback={<CategoriesPageSkeleton />}>
      <CategoriesClient
        initialCategories={categoriesList}
        initialCategoryTags={tagList}
        initialBanners={activeBanners}
      />
    </Suspense>
  );
}
