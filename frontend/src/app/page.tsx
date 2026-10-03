import LandingPageClient from '@/components/LandingPageClient';
import type { Metadata } from 'next';

export const dynamic = 'force-dynamic';

export const revalidate = 300; // Revalidate every 5 minutes (300 seconds)

export const metadata: Metadata = {
  title: 'Stationery Junction | Premium Stationery & Art Supplies Online',
  description:
    'Shop notebooks, pens, markers, art supplies and more at Stationery Junction. Retail and wholesale stationery delivered across India. Quality brands at best prices.',
  alternates: { canonical: 'https://www.stationeryjunction.com' },
  openGraph: {
    title: 'Stationery Junction | Premium Stationery Online',
    description:
      'Shop notebooks, pens, markers, art supplies and more. Wholesale and retail stationery delivered across India.',
    url: 'https://www.stationeryjunction.com',
    siteName: 'Stationery Junction',
    images: [{ url: '/og-image.jpg', width: 1200, height: 630, alt: 'Stationery Junction' }],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Stationery Junction | Premium Stationery Online',
    description: 'Shop notebooks, pens, markers and art supplies. Wholesale & retail across India.',
    images: ['/og-image.jpg'],
  },
};

export default async function Home() {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  if (!baseURL) {
    throw new Error('NEXT_PUBLIC_API_URL is not defined');
  }

  // Headers for fetching (don't need auth since it's the public guest view)
  const fetchOptions: RequestInit = {
    next: { revalidate: 300 }, // 5 minutes cache
    headers: { 'Content-Type': 'application/json' },
  };

  // Pre-fetch all data necessary for the landing page concurrently
  const [
    productsRes,
    bannersRes,
    categoriesRes,
    categoryTagsRes,
    brandsRes,
    collectionsRes,
    recommendationsRes,
    googleRatingRes,
  ] = await Promise.all([
    fetch(`${baseURL}/products/public?includeFacets=false&skinny=true`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/banners/public?position=homepage_web&userRole=guest`, fetchOptions).catch(
      () => null
    ),
    // forHomepage flag commented out — all zone-available categories now show on homepage; display is row-limited in the UI
    fetch(`${baseURL}/categories/public`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/category-tags/active`, fetchOptions).catch(() => null),
    // forHomepage flag commented out — all zone-available brands now show on homepage; display is row-limited in the UI
    fetch(`${baseURL}/brands/public`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/collections/public?visiblePage=Home&pageType=Home`, fetchOptions).catch(
      () => null
    ),
    fetch(`${baseURL}/recommendations`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/google-reviews/rating`, fetchOptions).catch(() => null),
  ]);

  // Process JSON responses
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

  const [
    productsRaw,
    banners,
    categoriesRaw,
    categoryTags,
    brandsRaw,
    collections,
    recommendations,
    googleRating,
  ] = await Promise.all([
    extractJson(productsRes, true),
    extractJson(bannersRes),
    extractJson(categoriesRes, true),
    extractJson(categoryTagsRes, true),
    extractJson(brandsRes, true),
    extractJson(collectionsRes),
    extractJson(recommendationsRes),
    extractJson(googleRatingRes),
  ]);

  // Format data
  const products = productsRaw?.products || productsRaw || [];

  // Format categories — preserve categoryTag so the frontend can build tag→category lookups for filtering
  let categories: any[] = [];
  if (categoriesRaw && Array.isArray(categoriesRaw)) {
    categories = categoriesRaw
      .filter((cat: any) => cat.isActive !== false)
      .map((cat: any) => ({
        name: cat.name,
        images: cat.images && cat.images.length > 0 ? cat.images : [],
        description: cat.description || '',
        categoryTag: cat.categoryTag || cat.category_tag || '',
      }));
  }

  // Format brands
  const brands = Array.isArray(brandsRaw) ? brandsRaw : brandsRaw?.brands || [];

  // Format banners
  const activeBanners = Array.isArray(banners) ? banners.filter((b: any) => b.isActive) : [];

  return (
    <LandingPageClient
      initialProducts={products}
      initialBanners={activeBanners}
      initialCategories={categories}
      initialCategoryTags={categoryTags || []}
      initialBrands={brands}
      initialCollections={collections || []}
      initialRecommendations={recommendations || undefined}
      initialGoogleRating={googleRating || { rating: 0, reviewCount: '' }}
    />
  );
}
