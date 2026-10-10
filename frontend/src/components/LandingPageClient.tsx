'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { usePincode } from '@/context/PincodeContext';
import api from '@/utils/api';
import ProductCatalog from '@/components/ProductCatalog';
import InfiniteCarousel from '@/components/InfiniteCarousel';
import RecentlyViewed from '@/components/RecentlyViewed';
import AuthModal from '@/components/AuthModal';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import ThemeSwitcher from '@/components/ThemeSwitcher';
import StatsCounter from '@/components/StatsCounter';
import HeroCarousel from '@/components/HeroCarousel';
import HoverProductCard from '@/components/HoverProductCard';
import { getImageUrlWithFallback, getImageUrl } from '@/utils/imageUrl';
import Link from 'next/link';
import { Suspense } from 'react';
import { logger } from '@/utils/logger';

export interface LandingPageClientProps {
  initialProducts?: any[];
  initialBanners?: any[];
  initialCategories?: any[];
  initialCategoryTags?: any[];
  initialBrands?: any[];
  initialCollections?: any[];
  initialRecommendations?: {
    newArrivals?: any[];
    customerFavourites?: any[];
    trendingNow?: any[];
    sectionOrder?: string[];
  };
  initialGoogleRating?: { rating: number; reviewCount: string };
}

/**
 * Main Landing Page Content
 * Handles the visual elements and the redirection logic for logged-in users.
 */
function LandingPageContent({ props }: { props: LandingPageClientProps }) {
  const { user } = useAuth();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const { theme } = useTheme();
  const { isPincodeModalOpen, isMandatory, pincode } = usePincode();
  const router = useRouter();
  const searchParams = useSearchParams();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [showHamburger, setShowHamburger] = useState(false);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [showCategories, setShowCategories] = useState(false);
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');
  const [banners, setBanners] = useState<any[]>(props.initialBanners || []);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [categories, setCategories] = useState<any[]>(props.initialCategories || []);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedCategoryTag, setSelectedCategoryTag] = useState<string | null>(null);

  const filterActive = (arr: any[]) => (arr || []).filter((p: any) => p && p.isActive !== false);

  // eslint-disable-next-line unused-imports/no-unused-vars
  const [newArrivals, setNewArrivals] = useState<any[]>(
    filterActive(props.initialRecommendations?.newArrivals || [])
  );
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [customerFavourites, setCustomerFavourites] = useState<any[]>(
    filterActive(props.initialRecommendations?.customerFavourites || [])
  );
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [trendingNow, setTrendingNow] = useState<any[]>(
    filterActive(props.initialRecommendations?.trendingNow || [])
  );
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [sectionOrder, setSectionOrder] = useState<string[]>(
    props.initialRecommendations?.sectionOrder?.length
      ? props.initialRecommendations.sectionOrder
      : ['new_arrivals', 'customer_favourites', 'trending_now']
  );
  const [searchTerm, setSearchTerm] = useState('');
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [categoryTags, setCategoryTags] = useState<any[]>(props.initialCategoryTags || []);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [brands, setBrands] = useState<{ id?: string; name: string; logoUrl?: string }[]>(
    props.initialBrands || []
  );
  const [isMobile, setIsMobile] = useState(false);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [products, setProducts] = useState<any[]>(props.initialProducts || []);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [collections, setCollections] = useState<any[]>(props.initialCollections || []);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const [selectedRecoCategory, setSelectedRecoCategory] = useState<string | null>(null);
  const [selectedRecoSubCategory, setSelectedRecoSubCategory] = useState<string | null>(null);

  const categoryCounts = useMemo(() => {
    const counts: { [key: string]: number } = {};
    products.forEach((p) => {
      const catName = typeof p.category === 'object' ? p.category?.name : p.category;
      if (catName) counts[catName] = (counts[catName] || 0) + 1;
    });
    return counts;
  }, [products]);

  /** tag name → set of category names that belong to that tag (built from loaded categories) */
  const tagToCategoryNames = useMemo(() => {
    const map = new Map<string, Set<string>>();
    categories.forEach((cat: any) => {
      const tag = cat.categoryTag || cat.category_tag;
      if (tag) {
        if (!map.has(tag)) map.set(tag, new Set());
        map.get(tag)!.add(cat.name);
      }
    });
    return map;
  }, [categories]);

  /** Filter pill options — active category tags (e.g. "Stationery", "Toys", "Food") */
  const recoCategoryOptions = useMemo(() => {
    return categoryTags
      .filter((t: any) => t.isActive !== false && t.name)
      .map((t: any) => t.name as string);
  }, [categoryTags]);

  /** Distinct subcategories within the products of the selected category tag */
  const recoSubCategoryOptions = useMemo(() => {
    if (!selectedRecoCategory) return [];
    const catNames = tagToCategoryNames.get(selectedRecoCategory);
    if (!catNames || catNames.size === 0) return [];
    const subs = new Set<string>();
    [...newArrivals, ...customerFavourites, ...trendingNow].forEach((p: any) => {
      const cat = typeof p.category === 'object' ? p.category?.name : p.category;
      if (catNames.has(cat) && p.sub_category) subs.add(p.sub_category);
    });
    return Array.from(subs).sort();
  }, [selectedRecoCategory, tagToCategoryNames, newArrivals, customerFavourites, trendingNow]);

  /** All products whose category belongs to the selected tag — for StatsCounter & brand filtering */
  const filteredStatsProducts = useMemo(() => {
    if (!selectedRecoCategory) return products;
    const catNames = tagToCategoryNames.get(selectedRecoCategory);
    if (!catNames || catNames.size === 0) return products;
    return products.filter((p: any) => {
      const cat = typeof p.category === 'object' ? p.category?.name : p.category;
      return catNames.has(cat);
    });
  }, [selectedRecoCategory, tagToCategoryNames, products]);

  /** Distinct brand count within the filtered product set */
  const filteredStatsBrandCount = useMemo(() => {
    if (!selectedRecoCategory) return brands.length;
    const brandNames = new Set<string>();
    filteredStatsProducts.forEach((p: any) => {
      const b = typeof p.brand === 'object' ? p.brand?.name : p.brand;
      if (b) brandNames.add(b);
    });
    return brandNames.size || brands.length;
  }, [selectedRecoCategory, filteredStatsProducts, brands]);

  /** Filter recommendation items by the active category tag (and optional subcategory) */
  const applyRecoFilter = (items: any[]) => {
    if (!selectedRecoCategory) return items;
    const catNames = tagToCategoryNames.get(selectedRecoCategory);
    if (!catNames || catNames.size === 0) return items;
    return items.filter((p: any) => {
      const cat = typeof p.category === 'object' ? p.category?.name : p.category;
      if (!catNames.has(cat)) return false;
      if (selectedRecoSubCategory && p.sub_category !== selectedRecoSubCategory) return false;
      return true;
    });
  };

  // Detect mobile view
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Redirect logged-in users to their respective dashboards
  useEffect(() => {
    if (user) {
      const userRole = user.effectiveRole || user.role;
      switch (userRole) {
        case 'super_admin':
          router.replace('/admin');
          break;
        case 'wholesaler':
          router.replace('/wholesaler');
          break;
        case 'customer':
          router.replace('/customer');
          break;
        case 'valet':
          router.replace('/valet');
          break;
        default:
          break;
      }
    }
  }, [user, router]);

  // eslint-disable-next-line unused-imports/no-unused-vars
  const [googleRating, setGoogleRating] = useState(
    props.initialGoogleRating || { rating: 0, reviewCount: '' }
  );

  useEffect(() => {
    // We already have initial SSR data, so we only fetch banners dynamically when isMobile updates
    fetchBanners();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMobile]);

  useEffect(() => {
    // Check for category or categoryTag in URL query params
    const resetParam = searchParams.get('reset');
    const categoryParam = searchParams.get('category');
    const categoryTagParam = searchParams.get('categoryTag');
    const collectionParam = searchParams.get('collection');
    const searchTermParam = searchParams.get('searchTerm');

    if (resetParam === 'true') {
      setSelectedCategory('');
      setSelectedCategoryTag(null);
      setSelectedCollection(null);
      setSearchTerm('');
      router.replace('/');
      return;
    }

    if (searchTermParam) {
      setSearchTerm(searchTermParam);
      setSelectedCategory('');
      setSelectedCategoryTag(null);
      setSelectedCollection(null);
    } else if (collectionParam) {
      setSelectedCollection(collectionParam);
      setSelectedCategory('');
      setSelectedCategoryTag(null);
    } else if (categoryTagParam) {
      setSelectedCategoryTag(categoryTagParam);
      setSelectedCategory('');
      setSelectedCollection(null);
    } else if (categoryParam) {
      setSelectedCategory(categoryParam);
      setSelectedCategoryTag(null);
      setSelectedCollection(null);
    } else {
      setSelectedCategory('');
      setSelectedCategoryTag(null);
      setSelectedCollection(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.toString()]);

  const fetchBanners = async () => {
    try {
      const position = isMobile ? 'homepage_mobile' : 'homepage_web';
      const userRole = user?.role || 'guest';
      const response = await api.get(`/banners/public?position=${position}&userRole=${userRole}`);
      const activeBanners = (response.data || []).filter((b: any) => b.isActive);
      setBanners(activeBanners);
    } catch (error) {
      logger.error('Failed to fetch banners', error);
    }
  };

  const handleCategoryClick = (category: string, subCategory?: string) => {
    if (subCategory) {
      router.push(
        `/categories/${encodeURIComponent(category)}?subCategory=${encodeURIComponent(subCategory)}`
      );
    } else {
      router.push(`/categories/${encodeURIComponent(category)}`);
    }
    setShowCategories(false);
    setShowHamburger(false);
  };



  // Re-fetch recommendations from the server whenever the category tag filter changes.
  // Includes pincode so the server can apply zone filtering for the guest's location.
  useEffect(() => {
    const fetchTaggedRecommendations = async () => {
      try {
        const params: Record<string, string> = {};
        if (pincode) params.pincode = pincode;
        if (selectedRecoCategory) params.categoryTag = selectedRecoCategory;
        const response = await api.get('/recommendations', { params });
        const data = response.data || {};
        const filterActive = (arr: any[]) => (arr || []).filter((p: any) => p && p.isActive !== false);
        setNewArrivals(filterActive(data.newArrivals || []));
        setCustomerFavourites(filterActive(data.customerFavourites || []));
        setTrendingNow(filterActive(data.trendingNow || []));
        if (Array.isArray(data.sectionOrder) && data.sectionOrder.length) {
          setSectionOrder(data.sectionOrder);
        }
      } catch (e) {
        logger.error('Failed to fetch tagged recommendations', e);
      }
    };
    fetchTaggedRecommendations();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRecoCategory]);

  return (
    <div className="min-h-screen bg-gray-50 pb-20 md:pb-0">
      {/* Header always visible — contains the pincode picker button */}
      <Header />

      {/* Page body: blurred + non-interactive while pincode gate is active */}
      <div
        className="transition-all duration-700 ease-out"
        aria-hidden={undefined}
      >
      {!selectedCategory && !selectedCategoryTag && !selectedCollection && !searchTerm && (
        <>
          <HeroCarousel banners={banners} />

          {/* ── Continue Browsing (Recently Viewed) ── only when user has history */}
          {user && (
            <div className="px-4 pb-2 pt-6 md:px-8 xl:px-12">
              <RecentlyViewed
                basePath={user.role === 'wholesaler' ? '/wholesaler/products' : '/customer/products'}
                limit={8}
                title="Continue Browsing"
              />
            </div>
          )}

          {/* ── Category / Subcategory Filter Pills ── */}
          {recoCategoryOptions.length > 1 && (
            <div className="px-4 pb-4 pt-6 md:px-8 xl:px-12">
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => {
                    setSelectedRecoCategory(null);
                    setSelectedRecoSubCategory(null);
                  }}
                  className={`rounded-full border px-4 py-1.5 text-xs font-semibold transition-all ${
                    !selectedRecoCategory
                      ? 'border-[#1a4d33] bg-[#1a4d33] text-white shadow-sm'
                      : 'border-gray-200 bg-white text-gray-600 hover:border-[#1a4d33] hover:text-[#1a4d33]'
                  }`}
                >
                  All
                </button>
                {recoCategoryOptions.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => {
                      setSelectedRecoCategory(cat === selectedRecoCategory ? null : cat);
                      setSelectedRecoSubCategory(null);
                    }}
                    className={`rounded-full border px-4 py-1.5 text-xs font-semibold transition-all ${
                      selectedRecoCategory === cat
                        ? 'border-[#1a4d33] bg-[#1a4d33] text-white shadow-sm'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-[#1a4d33] hover:text-[#1a4d33]'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
              {selectedRecoCategory && recoSubCategoryOptions.length > 1 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    onClick={() => setSelectedRecoSubCategory(null)}
                    className={`rounded-full border px-3 py-1 text-[11px] font-medium transition-all ${
                      !selectedRecoSubCategory
                        ? 'border-amber-500 bg-amber-500 text-white'
                        : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-amber-400 hover:text-amber-600'
                    }`}
                  >
                    All {selectedRecoCategory}
                  </button>
                  {recoSubCategoryOptions.map((sub) => (
                    <button
                      key={sub}
                      onClick={() =>
                        setSelectedRecoSubCategory(sub === selectedRecoSubCategory ? null : sub)
                      }
                      className={`rounded-full border px-3 py-1 text-[11px] font-medium transition-all ${
                        selectedRecoSubCategory === sub
                          ? 'border-amber-500 bg-amber-500 text-white'
                          : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-amber-400 hover:text-amber-600'
                      }`}
                    >
                      {sub}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <StatsCounter
            productCount={filteredStatsProducts.length}
            brandCount={filteredStatsBrandCount}
          />
        </>
      )}

      <main className="w-full px-4 py-8 md:px-8 xl:px-12">
        {/* Visually hidden h1 for SEO — the hero carousel and section headings serve as visible headings */}
        <h1 className="sr-only">Stationery Junction — Premium Stationery &amp; Art Supplies</h1>

        {/* Recommendation sections — new_arrivals always first, then bandit-ordered rest */}
        {!selectedCategory &&
          !selectedCategoryTag &&
          !selectedCollection &&
          !searchTerm &&
          (() => {
            const filteredNewArrivals = applyRecoFilter(newArrivals);
            const filteredCustomerFavourites = applyRecoFilter(customerFavourites);
            const filteredTrendingNow = applyRecoFilter(trendingNow);

            const allSections: {
              key: string;
              label: string;
              title: string;
              subtitle: string;
              items: any[];
              show: boolean;
            }[] = [
              {
                key: 'new_arrivals',
                label: 'Just Landed',
                title: 'New Arrivals',
                subtitle:
                  'Discover our latest additions — fresh designs and premium quality pieces just for you.',
                items: filteredNewArrivals,
                show: filteredNewArrivals.length > 0,
              },
              {
                key: 'customer_favourites',
                label: 'Your picks',
                title: 'Customer Favourites',
                subtitle: 'Bestsellers loved by customers.',
                items: filteredCustomerFavourites,
                show: filteredCustomerFavourites.length > 0,
              },
              {
                key: 'trending_now',
                label: 'Hot right now',
                title: 'Trending Now',
                subtitle: 'What customers are buying right now.',
                items: filteredTrendingNow,
                show: filteredTrendingNow.length > 0,
              },
            ];
            const styles: Record<string, { span: string; bar: string }> = {
              new_arrivals: { span: 'text-[#D4AF37]', bar: 'from-[#1a4d33] to-[#D4AF37]' },
              customer_favourites: { span: 'text-[#1a4d33]', bar: 'from-[#1a4d33] to-[#D4AF37]' },
              trending_now: { span: 'text-amber-600', bar: 'from-amber-500 to-amber-200' },
            };
            // new_arrivals always first, rest follow bandit order
            const newArrSec = allSections.find((s) => s.key === 'new_arrivals');
            const banditOrder = (
              sectionOrder.length ? sectionOrder : ['customer_favourites', 'trending_now']
            ).filter((s) => s !== 'new_arrivals');
            const rest = banditOrder
              .map((s) => allSections.find((sec) => sec.key === s))
              .filter((sec): sec is NonNullable<typeof sec> => !!sec && sec.show);
            const ordered = [...(newArrSec && newArrSec.show ? [newArrSec] : []), ...rest];
            return (
              <>
                {/* Empty state when filter yields no results */}
                {ordered.length === 0 && selectedRecoCategory && (
                  <div className="mb-16 flex flex-col items-center gap-3 py-16 text-center text-gray-400">
                    <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 105 11a6 6 0 0012 0z" />
                    </svg>
                    <p className="text-sm font-medium">
                      No recommendations in{' '}
                      <span className="font-semibold text-gray-600">
                        {selectedRecoSubCategory || selectedRecoCategory}
                      </span>{' '}
                      right now.
                    </p>
                    <button
                      onClick={() => {
                        setSelectedRecoCategory(null);
                        setSelectedRecoSubCategory(null);
                      }}
                      className="text-xs font-semibold text-[#1a4d33] underline underline-offset-2 hover:text-[#143b27]"
                    >
                      Show all recommendations
                    </button>
                  </div>
                )}

                {ordered.map((sec) => (
                  <section key={sec.key} className="mb-20">
                    <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
                      <div className="relative">
                        <span
                          className={`${styles[sec.key]?.span || ''} mb-2 block text-xs font-semibold uppercase tracking-[0.2em]`}
                        >
                          {sec.label}
                        </span>
                        <h2 className="text-3xl font-semibold text-gray-900 md:text-4xl">
                          {sec.title}
                        </h2>
                        <p className="mt-2 max-w-md text-sm text-gray-500">{sec.subtitle}</p>
                        <div
                          className={`absolute -left-4 bottom-0 top-0 w-1 bg-gradient-to-b ${styles[sec.key]?.bar || ''} hidden rounded-full md:block`}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 md:gap-6 lg:grid-cols-5 xl:grid-cols-6">
                      {sec.items
                        .slice(0, expandedSections[sec.key] ? 24 : 6)
                        .map((p: any, index: number) => (
                          <div
                            key={p.id}
                            className="animate-fade-in-up opacity-0"
                            style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'forwards' }}
                          >
                            <HoverProductCard
                              product={{ ...p, isNew: false, bestSeller: false }}
                              onClick={() => router.push(`/customer/product/${p.id}`)}
                            />
                          </div>
                        ))}
                    </div>

                    {sec.items.length > 6 && (
                      <div className="relative mt-12 flex justify-center border-t border-gray-100 pt-8">
                        <button
                          onClick={() =>
                            setExpandedSections((prev) => ({ ...prev, [sec.key]: !prev[sec.key] }))
                          }
                          className="absolute -top-6 flex items-center gap-2 rounded-full border border-gray-200 bg-white px-8 py-3 font-semibold text-gray-900 shadow-sm transition-all hover:shadow-md"
                        >
                          {expandedSections[sec.key] ? (
                            <>
                              Show less
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                              </svg>
                            </>
                          ) : (
                            <>
                              Show more
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </section>
                ))}
              </>
            );
          })()}


        {collections.length > 0 &&
          !selectedCategory &&
          !selectedCategoryTag &&
          !selectedCollection &&
          !searchTerm && (
            <section className="mb-20">
              <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
                <div className="relative">
                  <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-amber-500">
                    Curated For You
                  </span>
                  <h2 className="text-3xl font-semibold text-gray-900 md:text-4xl">
                    Featured Collections
                  </h2>
                  <p className="mt-2 max-w-md text-sm text-gray-500">
                    Thoughtfully curated sets designed to meet your every stationery need.
                  </p>
                  <div className="absolute -left-4 bottom-0 top-0 hidden w-1 rounded-full bg-gradient-to-b from-amber-400 to-amber-200 md:block" />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                {collections.map((col: any, index: number) => (
                  <div
                    key={col.id}
                    className="animate-fade-in-up group relative aspect-[4/3] cursor-pointer overflow-hidden rounded-2xl opacity-0 shadow-lg"
                    style={{ animationDelay: `${index * 100}ms`, animationFillMode: 'forwards' }}
                    onClick={() => router.push(`/collections/${encodeURIComponent(col.id)}`)}
                  >
                    <img
                      src={getImageUrlWithFallback(col.imageUrl)}
                      alt={col.name}
                      className="absolute inset-0 h-full w-full object-cover transition-transform duration-[8000ms] ease-out group-hover:scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-80 transition-opacity duration-500 group-hover:opacity-90" />
                    <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-8">
                      <div className="transform transition-transform duration-500 group-hover:translate-y-[-8px]">
                        <h3 className="mb-2 text-xl font-semibold leading-tight text-white md:text-2xl">
                          {col.name}
                        </h3>
                        <p className="mb-4 line-clamp-2 max-w-[90%] text-sm text-white/70">
                          {col.description}
                        </p>
                        <div className="flex translate-y-2 transform items-center gap-2 text-xs font-semibold uppercase tracking-wider text-white opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100">
                          <span>Explore Collection</span>
                          <svg
                            className="h-4 w-4 transform transition-transform group-hover:translate-x-1"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M17 8l4 4m0 0l-4 4m4-4H3"
                            />
                          </svg>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

        {(() => {
          const visibleCats = selectedRecoCategory
            ? categories.filter((c: any) => {
                const catNames = tagToCategoryNames.get(selectedRecoCategory);
                return catNames ? catNames.has(c.name) : true;
              })
            : categories;
          return visibleCats.length > 0 &&
           !selectedCategory &&
           !selectedCategoryTag &&
           !selectedCollection &&
           !searchTerm && (
            <section className="mb-20">
              <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
                <div className="relative">
                  <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-emerald-500">
                    Browse Our Range
                  </span>
                  <h2 className="text-3xl font-semibold text-gray-900 md:text-4xl">
                    Shop by Category
                  </h2>
                  <p className="mt-2 max-w-md text-sm text-gray-500">
                    Discover premium stationery organized for easy browsing.
                  </p>
                  <div className="absolute -left-4 bottom-0 top-0 hidden w-1 rounded-full bg-gradient-to-b from-[#1a4d33] to-[#D4AF37] md:block" />
                </div>
                <button
                  onClick={() => router.push('/categories')}
                  className="group inline-flex items-center gap-2 text-sm font-semibold text-gray-900 transition-colors hover:text-[#1a4d33]"
                >
                  View All Categories
                  <svg
                    className="h-4 w-4 transition-transform group-hover:translate-x-1"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M17 8l4 4m0 0l-4 4m4-4H3"
                    />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-3 gap-4 sm:grid-cols-4 md:grid-cols-6 md:gap-5 lg:grid-cols-8">
                {visibleCats.slice(0, isMobile ? 9 : 16).map((cat, index) => (
                  <button
                    type="button"
                    key={cat.name}
                    onClick={() => handleCategoryClick(cat.name)}
                    className="animate-fade-in-up group flex flex-col items-center opacity-0 transition-all duration-300"
                    style={{ animationDelay: `${index * 30}ms`, animationFillMode: 'forwards' }}
                  >
                    <div className="relative mb-3 h-16 w-16 transform overflow-hidden rounded-full shadow-md ring-2 ring-transparent transition-all duration-300 group-hover:scale-105 group-hover:shadow-xl group-hover:ring-emerald-200 sm:h-20 sm:w-20 md:h-24 md:w-24">
                      {cat.images && cat.images.length > 0 ? (
                        <img
                          src={getImageUrlWithFallback(cat.images[0])}
                          alt={cat.name}
                          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
                          <svg
                            className="h-8 w-8 text-gray-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="1.5"
                              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                    <div className="w-full text-center">
                      <h3 className="line-clamp-2 px-1 text-xs font-semibold leading-tight text-gray-800 transition-colors group-hover:text-[#1a4d33] sm:text-sm">
                        {cat.name}
                      </h3>
                      <p className="mt-0.5 text-[10px] font-medium text-gray-400">
                        {categoryCounts[cat.name] || 0} items
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          );
        })()}

        {(() => {
          const visibleBrands = selectedRecoCategory
            ? brands.filter((b: any) => {
                const bName = typeof b === 'string' ? b : b?.name || '';
                const brandNamesInTag = new Set(
                  filteredStatsProducts
                    .map((p: any) => (typeof p.brand === 'object' ? p.brand?.name : p.brand))
                    .filter(Boolean)
                );
                return brandNamesInTag.has(bName);
              })
            : brands;
          return visibleBrands.length > 0 &&
          !selectedCategory &&
          !selectedCategoryTag &&
          !selectedCollection &&
          !searchTerm && (
            <section className="mb-20">
              <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
                <div className="relative">
                  <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-sky-500">
                    Trusted Names
                  </span>
                  <h2 className="text-3xl font-semibold text-gray-900 md:text-4xl">
                    Featured Brands
                  </h2>
                  <p className="mt-2 max-w-md text-sm text-gray-500">
                    Shop from the brands you know and love.
                  </p>
                  <div className="absolute -left-4 bottom-0 top-0 hidden w-1 rounded-full bg-gradient-to-b from-[#1a4d33] to-[#D4AF37] md:block" />
                </div>
                <Link
                  href="/brands"
                  className="group inline-flex items-center gap-2 text-sm font-semibold text-gray-900 transition-colors hover:text-[#1a4d33]"
                >
                  View All Brands
                  <svg
                    className="h-4 w-4 transition-transform group-hover:translate-x-1"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M17 8l4 4m0 0l-4 4m4-4H3"
                    />
                  </svg>
                </Link>
              </div>
              <InfiniteCarousel
                items={visibleBrands.map((b) => {
                  const name = typeof b === 'string' ? b : b?.name || '';
                  const id = typeof b === 'object' && b?.id ? b.id : name;
                  const logoUrl =
                    typeof b === 'object' && b?.logoUrl ? getImageUrl(b.logoUrl) : null;
                  return {
                    id,
                    title: name,
                    image: logoUrl || undefined,
                    link: `/brands/${encodeURIComponent(name)}`,
                    type: 'brand' as const,
                  };
                })}
                speed={60}
              />
            </section>
          );
        })()}


        {(selectedCategory || selectedCategoryTag || selectedCollection || searchTerm) && (
          <>
            {searchTerm && (
              <HeroBanner
                title={`"${searchTerm}"`}
                subtitle={`Showing results for your search`}
                breadcrumbs={[{ label: 'Home', href: '/' }, { label: 'Search Results' }]}
                hideThumbnail={true}
              />
            )}
            <div className={`w-full ${searchTerm ? 'mt-4' : 'py-4'}`}>
              <ProductCatalog
                category={selectedCategory}
                categoryTag={selectedCategoryTag}
                collection={selectedCollection}
                brand={searchParams.get('brand') || ''}
                filter={searchParams.get('filter') || ''}
                searchTerm={searchTerm}
                showFilters={true}
                hideHeader={!!searchTerm}
              />
            </div>
          </>
        )}
      </main>

      {showAuthModal && (
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          initialMode={authModalMode}
        />
      )}

      {googleRating.rating > 0 &&
        !selectedCategory &&
        !selectedCategoryTag &&
        !selectedCollection &&
        !searchTerm && (
          <div className="mb-8 w-full px-4 py-4 md:px-12 xl:px-20">
            <div className="flex flex-col items-center justify-between gap-6 rounded-2xl border border-gray-100 bg-white p-6 shadow-sm md:flex-row md:p-8">
              <div className="flex items-center gap-6">
                <div className="rounded-full bg-blue-600 p-3 shadow-md">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-1 .67-2.26 1.07-3.71 1.07-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path d="M5.84 14.11c-.22-.67-.35-1.39-.35-2.11s.13-1.44.35-2.11V7.05H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.95l3.66-2.84z" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.05l3.66 2.84c.87-2.6 3.3-4.51 6.16-4.51z" />
                  </svg>
                </div>
                <div>
                  <div className="mb-1 flex items-center gap-1.5">
                    {[...Array(5)].map((_, i) => (
                      <svg
                        key={i}
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill={i < Math.floor(googleRating.rating) ? '#fbbf24' : '#e5e7eb'}
                      >
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                      </svg>
                    ))}
                    <span className="ml-2 text-xl font-semibold text-gray-800">
                      {googleRating.rating} / 5
                    </span>
                  </div>
                  <p className="text-sm font-semibold uppercase leading-none tracking-widest text-gray-500">
                    Verified by {googleRating.reviewCount} Happy Customers on Google
                  </p>
                </div>
              </div>
              <a
                href="https://share.google/6nwo4Mqy2qMRtztbF"
                target="_blank"
                rel="noopener noreferrer"
                className="whitespace-nowrap rounded-full bg-gray-900 px-8 py-3 text-xs font-semibold uppercase tracking-widest text-white shadow-md transition-all hover:bg-gray-800 active:scale-95"
              >
                WRITE A REVIEW
              </a>
            </div>
          </div>
        )}

      </div>{/* end blur wrapper */}

      <ThemeSwitcher />
    </div>
  );
}

export default function LandingPageClient(props: LandingPageClientProps) {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50">Loading...</div>
      }
    >
      <LandingPageContent props={props} />
    </Suspense>
  );
}
