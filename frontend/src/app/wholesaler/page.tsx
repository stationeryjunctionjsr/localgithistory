import WholesalerClient from '@/components/WholesalerClient';
import { Suspense } from 'react';

export const dynamic = 'force-dynamic';

export const revalidate = 60; // 1 minute caching for the dashboard so inventory feels fresh but layout is fast

export default async function WholesalerDashboardPage() {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  if (!baseURL) {
    throw new Error('NEXT_PUBLIC_API_URL is not defined');
  }
  const fetchOptions: RequestInit = {
    next: { revalidate: 60 },
    headers: { 'Content-Type': 'application/json' },
  };

  // Fetch B2B specific banners, along with public shared catalogues
  const [
    categoriesRes,
    brandsRes,
    collectionsRes,
    homeBannersRes,
    wholeBannersRes,
    googleRatingRes,
    productsRes,
  ] = await Promise.all([
    fetch(`${baseURL}/categories/public?forHomepage=true`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/brands/public`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/collections/public?visiblePage=Home&pageType=Home`, fetchOptions).catch(
      () => null
    ),
    fetch(`${baseURL}/banners/public?position=homepage&targetAudience=all`, fetchOptions).catch(
      () => null
    ),
    fetch(`${baseURL}/banners/public?position=wholesaler`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/google-reviews/rating`, fetchOptions).catch(() => null),
    fetch(`${baseURL}/products/public?includeFacets=false&skinny=true`, fetchOptions).catch(() => null),
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

  const [categoriesRaw, brandsRaw, colRaw, homeBannersRaw, wholeBannersRaw, googleRatingRaw, productsRaw] =
    await Promise.all([
      extractJson(categoriesRes, 'categories/public', true),
      extractJson(brandsRes, 'brands/public', true),
      extractJson(collectionsRes, 'collections/public'),
      extractJson(homeBannersRes, 'banners/homepage'),
      extractJson(wholeBannersRes, 'banners/wholesaler'),
      extractJson(googleRatingRes, 'google-reviews/rating'),
      extractJson(productsRes, 'products/public'),
    ]);

  let categories = [];
  if (categoriesRaw?.data) categories = categoriesRaw.data;
  else if (Array.isArray(categoriesRaw)) categories = categoriesRaw;

  // Format active categories purely as needed
  categories = categories
    .filter((cat: any) => cat.isActive !== false)
    .map((cat: any) => ({
      name: cat.name,
      images: cat.images && cat.images.length > 0 ? cat.images : [],
      description: cat.description || '',
    }));

  const brands = Array.isArray(brandsRaw) ? brandsRaw : brandsRaw?.brands || [];
  const collections = colRaw?.data || colRaw || [];

  // Combine & filter Wholesaler & Homepage generic Banners
  const allBanners = [
    ...(Array.isArray(wholeBannersRaw) ? wholeBannersRaw : []),
    ...(Array.isArray(homeBannersRaw) ? homeBannersRaw : []),
  ];
  const uniqueBanners = allBanners.filter(
    (banner, index, self) => index === self.findIndex((b) => b._id === banner._id)
  );

  const activeBanners = uniqueBanners.filter(
    (b: any) =>
      b.isActive &&
      b.isPublished !== false &&
      (b.targetAudience === 'all' || b.targetAudience === 'wholesaler')
  );

  const products = productsRaw?.products || productsRaw || [];

  const stats = {
    googleRating: googleRatingRaw || { rating: 5.0, reviewCount: '421' },
    productCount: products.length,
    brandCount: brands.length,
  };

  // Detect a total API blackout: all three critical fetches failed with no response at all.
  // This distinguishes an empty catalogue (ok:true + empty array) from a network/server outage.
  const apiDown =
    (categoriesRes === null || !categoriesRes.ok) &&
    (brandsRes === null || !brandsRes.ok) &&
    (collectionsRes === null || !collectionsRes.ok);

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
        <a
          href="/wholesaler"
          className="mt-2 rounded-full bg-emerald-800 px-6 py-2.5 text-sm font-semibold text-white hover:bg-emerald-900"
        >
          Refresh
        </a>
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
      <WholesalerClient
        initialCategories={categories}
        initialBrands={brands}
        initialCollections={collections}
        initialBanners={activeBanners}
        initialStats={stats}
      />
    </Suspense>
  );
}
