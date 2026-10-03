import CustomerClient from '@/components/CustomerClient';
import { Suspense } from 'react';
import type { Metadata } from 'next';

export const dynamic = 'force-dynamic';

export const revalidate = 60; // 1 minute caching for the dashboard so inventory feels fresh but layout is fast

export const metadata: Metadata = {
  title: 'Shop Stationery | Notebooks, Pens & More | Stationery Junction',
  description:
    'Browse our full range of stationery — notebooks, pens, markers, art supplies and more. Quality products at great prices, delivered across India.',
  alternates: { canonical: 'https://www.stationeryjunction.com/customer' },
  openGraph: {
    title: 'Shop Stationery | Stationery Junction',
    description:
      'Browse notebooks, pens, markers, art supplies and more. Quality stationery delivered across India.',
    url: 'https://www.stationeryjunction.com/customer',
    type: 'website',
  },
};

export default async function CustomerDashboardPage() {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  if (!baseURL) {
    throw new Error('NEXT_PUBLIC_API_URL is not defined');
  }
  const fetchOptions: RequestInit = {
    next: { revalidate: 60 },
    headers: { 'Content-Type': 'application/json' },
  };

  // Fetch as much public foundational data as possible on the server
  // User-specific data is still handled on the client (recommendations, user metadata)
  const [
    productsRes,
    categoriesRes,
    tagsRes,
    brandsRes,
    collectionsRes,
    bannersRes,
    googleRatingRes,
  ] = await Promise.all([
    fetch(`${baseURL}/products/public`, fetchOptions).catch(() => null),
    // forHomepage flag commented out — all zone-available categories now show on homepage; display is row-limited in the UI
    fetch(`${baseURL}/categories/public`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/category-tags/active`, fetchOptions).catch(() => null),
    // forHomepage flag commented out — all zone-available brands now show on homepage; display is row-limited in the UI
    fetch(`${baseURL}/brands/public`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/collections/public?visiblePage=Home&pageType=Home`, fetchOptions).catch(
      () => null
    ),
    fetch(`${baseURL}/banners/public?position=homepage_web&userRole=customer`, fetchOptions).catch(
      () => null
    ),
    fetch(`${baseURL}/google-reviews/rating`, fetchOptions).catch(() => null), // Short TTL or public metric
  ]);

  const extractJson = async (res: Response | null, label: string, critical: boolean = false) => {
    if (res === null) {
      console.error(`[fetch] network error: ${label}`);
      if (critical) throw new Error(`Network error: ${label}`);
      return null;
    }
    if (!res.ok) {
      console.error(`[fetch] status ${res.status}: ${label}`);
      if (critical) throw new Error(`API failed with status ${res.status}: ${label}`);
      return null;
    }
    return res.json().catch((e) => {
      if (critical) throw e;
      return null;
    });
  };

  const [productsRaw, categoriesRaw, tagsRaw, brandsRaw, colRaw, bannersRaw, googleRatingRaw] =
    await Promise.all([
      extractJson(productsRes, 'products/public', true),
      extractJson(categoriesRes, 'categories/public', true),
      extractJson(tagsRes, 'category-tags/active', true),
      extractJson(brandsRes, 'brands/public', true),
      extractJson(collectionsRes, 'collections/public'),
      extractJson(bannersRes, 'banners/public'),
      extractJson(googleRatingRes, 'google-reviews/rating'),
    ]);

  const products = productsRaw?.products || productsRaw || [];
  let categories = [];
  if (categoriesRaw?.data) categories = categoriesRaw.data;
  else if (Array.isArray(categoriesRaw)) categories = categoriesRaw;

  // Format active categories — preserve categoryTag so the frontend can build tag→category lookups for filtering
  categories = categories
    .filter((cat: any) => cat.isActive !== false)
    .map((cat: any) => ({
      name: cat.name,
      images: cat.images && cat.images.length > 0 ? cat.images : [],
      description: cat.description || '',
      categoryTag: cat.categoryTag || cat.category_tag || '',
    }));

  const brands = Array.isArray(brandsRaw) ? brandsRaw : brandsRaw?.brands || [];
  const collections = colRaw?.data || colRaw || [];
  const categoryTags = tagsRaw?.data || tagsRaw || [];
  const activeBanners = Array.isArray(bannersRaw) ? bannersRaw.filter((b: any) => b.isActive) : [];

  const stats = {
    googleRating: googleRatingRaw || { rating: 5.0, reviewCount: '421' },
  };

  // Detect a total API blackout: all three critical fetches failed with no response at all.
  // This distinguishes an empty store (would return ok:true + empty array) from a network/server outage.
  const apiDown =
    (productsRes === null || !productsRes.ok) &&
    (categoriesRes === null || !categoriesRes.ok) &&
    (brandsRes === null || !brandsRes.ok);

  if (apiDown) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gray-50 px-6 text-center">
        <svg
          className="h-16 w-16 text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
          />
        </svg>
        <h2 className="text-lg font-semibold text-gray-700">Could not load the store</h2>
        <p className="max-w-sm text-sm text-gray-500">
          We&apos;re having trouble reaching our servers. Please check your connection and refresh
          the page.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-2 rounded-full bg-emerald-800 px-6 py-2.5 text-sm font-semibold text-white hover:bg-emerald-900"
        >
          Refresh
        </button>
      </div>
    );
  }

  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50 text-xs uppercase tracking-widest text-[#1a4d33]">
          Loading Dashboard...
        </div>
      }
    >
      <CustomerClient
        initialProducts={products}
        initialCategories={categories}
        initialCategoryTags={categoryTags}
        initialBrands={brands}
        initialCollections={collections}
        initialBanners={activeBanners}
        initialStats={stats}
      />
    </Suspense>
  );
}
