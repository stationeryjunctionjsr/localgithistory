'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import api from '@/utils/api';
import ProductCatalog from '@/components/ProductCatalog';
import InfiniteCarousel from '@/components/InfiniteCarousel';
import AuthModal from '@/components/AuthModal';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import ThemeSwitcher from '@/components/ThemeSwitcher';
import StatsCounter from '@/components/StatsCounter';
import HeroCarousel from '@/components/HeroCarousel';
import HoverProductCard from '@/components/HoverProductCard';
import { getImageUrlWithFallback, getImageUrl } from '@/utils/imageUrl';
import Link from 'next/link';
import { useRecommendationSectionView } from '@/hooks/useRecommendationSectionView';
import { trackRecommendationProductClick } from '@/utils/analytics';
import { useCart } from '@/context/CartContext';

export interface CustomerClientProps {
  initialProducts?: any[];
  initialCategories?: any[];
  initialCategoryTags?: any[];
  initialCollections?: any[];
  initialBanners?: any[];
  initialBrands?: any[];
  initialStats?: any;
}

export default function CustomerClient({
  initialProducts,
  initialCategories,
  initialCategoryTags,
  initialCollections,
  initialBanners,
  initialBrands,
  initialStats,
}: CustomerClientProps) {
  const { user } = useAuth();
  const { cart, addToCart, updateQuantity, removeFromCart } = useCart();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const { theme } = useTheme();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [showAuthModal, setShowAuthModal] = useState(false);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');
  const [banners, setBanners] = useState<any[]>(initialBanners || []);
  const [categories, setCategories] = useState<any[]>(initialCategories || []);
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [categoryTags, setCategoryTags] = useState<any[]>(initialCategoryTags || []);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedCategoryTag, setSelectedCategoryTag] = useState<string | null>(null);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [brands, setBrands] = useState<{ _id?: string; name: string; logoUrl?: string }[]>(
    initialBrands || []
  );
  const [isMobile, setIsMobile] = useState(false);
  const [products, setProducts] = useState<any[]>(initialProducts || []);
  const [collections, setCollections] = useState<any[]>(initialCollections || []);
  const [newArrivals, setNewArrivals] = useState<any[]>([]);
  const [customerFavourites, setCustomerFavourites] = useState<any[]>([]);
  const [trendingNow, setTrendingNow] = useState<any[]>([]);
  const [explore, setExplore] = useState<any[]>([]);
  const [googleRating, setGoogleRating] = useState(
    initialStats?.googleRating || { rating: 5.0, reviewCount: '421' }
  );
  const [sectionOrder, setSectionOrder] = useState<string[]>([
    'new_arrivals',
    'customer_favourites',
    'trending_now',
    'explore',
  ]);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const newArrivalsRef = useRecommendationSectionView('new_arrivals');
  const customerFavouritesRef = useRecommendationSectionView('customer_favourites');
  const trendingNowRef = useRecommendationSectionView('trending_now');
  const exploreRef = useRecommendationSectionView('explore');

  const categoryCounts = useMemo(() => {
    const counts: { [key: string]: number } = {};
    products.forEach((p) => {
      const catName = typeof p.category === 'object' ? p.category?.name : p.category;
      if (catName) counts[catName] = (counts[catName] || 0) + 1;
    });
    return counts;
  }, [products]);

  // Detect mobile view
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Redirect other roles
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
        case 'valet':
          router.replace('/valet');
          break;
        default:
          break;
      }
    } else {
      // If not logged in, redirect to landing page? Or let them browse?
      // Since this is /customer, maybe redirect to landing if guest?
      // router.replace('/landingpage')
    }
  }, [user, router]);

  // Only fetch user-specific data that changes based on auth state.
  // Public data (products, categories, brands, collections, google rating)
  // comes pre-fetched from the server component via initial* props.
  useEffect(() => {
    /* 
    // Commented out to prevent redundant client-side API requests that duplicate SSR data:
    fetchProducts();
    fetchCategories();
    fetchBrands();
    fetchCollections();
    fetchGoogleRating();
    */
    fetchBanners();
    fetchRecommendations();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMobile, user]);

  /*
  // Commented out to prevent redundant client-side fetching (data is now SSR-loaded via initialStats):
  const fetchGoogleRating = async () => {
    try {
      const res = await api.get('/google-reviews/rating');
      if (res.data) setGoogleRating(res.data);
    } catch (e) {
      console.error('Failed to fetch google rating', e);
    }
  };

  // Commented out to prevent redundant client-side fetching (data is now SSR-loaded via initialProducts):
  const fetchProducts = async () => {
    try {
      const response = await api.get('/products/public');
      const allProducts = response.data.products || response.data || [];
      setProducts(allProducts);
    } catch (error) {
      console.error('Failed to fetch products', error);
    }
  };

  // Commented out to prevent redundant client-side fetching (data is now SSR-loaded via initialBrands):
  const fetchBrands = async () => {
    try {
      const res = await api.get('/brands/public', { params: { forHomepage: true } });
      setBrands(Array.isArray(res.data) ? res.data : res.data?.brands || []);
    } catch (e) {
      console.error('Failed to fetch brands', e);
      setBrands([]);
    }
  };

  // Commented out to prevent redundant client-side fetching (data is now SSR-loaded via initialCategories):
  const fetchCategories = async () => {
    try {
      try {
        const response = await api.get('/categories/public', { params: { forHomepage: true } });
        const categoryData = response.data || [];
        const activeCategories = categoryData
          .filter((cat: any) => cat.isActive !== false)
          .map((cat: any) => ({
            name: cat.name,
            images: cat.images && cat.images.length > 0 ? cat.images : [],
            description: cat.description || '',
          }));
        setCategories(activeCategories);
      } catch (categoryError) {
        console.warn('Category API not available, falling back to products', categoryError);
        const response = await api.get('/products/public');
        const products = response.data.products || response.data || [];
        const uniqueCategoryNames: string[] = Array.from(
          new Set(products.map((p: any) => p.category).filter(Boolean))
        );
        setCategories(
          uniqueCategoryNames.map((name: string) => ({
            name,
            images: [] as string[],
            description: '',
          }))
        );
      }
    } catch (error) {
      console.error('Failed to fetch categories', error);
      setCategories([]);
    }
  };

  // Commented out to prevent redundant client-side fetching (data is now SSR-loaded via initialCollections):
  const fetchCollections = async () => {
    try {
      const response = await api.get('/collections/public', {
        params: { visiblePage: 'Home', pageType: 'Home' },
      });
      setCollections(response.data || []);
    } catch (error) {
      console.error('Failed to fetch collections', error);
    }
  };
  */



  const fetchRecommendations = async () => {
    try {
      const response = await api.get('/recommendations');
      const data = response.data || {};
      const filterActive = (arr: any[]) =>
        (arr || []).filter((p: any) => p && p.isActive !== false);
      setNewArrivals(filterActive(data.newArrivals || []));
      setCustomerFavourites(filterActive(data.customerFavourites || []));
      setTrendingNow(filterActive(data.trendingNow || []));
      setExplore(filterActive(data.explore || []));
      setSectionOrder(
        Array.isArray(data.sectionOrder)
          ? data.sectionOrder
          : ['new_arrivals', 'customer_favourites', 'trending_now', 'explore']
      );
    } catch (e) {
      console.error('Failed to fetch recommendations', e);
    }
  };
  const fetchBanners = async () => {
    try {
      const position = isMobile ? 'homepage_mobile' : 'homepage_web';
      const userRole = user?.effectiveRole || user?.role || 'guest';
      const response = await api.get(`/banners/public?position=${position}&userRole=${userRole}`);

      // The backend already filters by isActive, isPublished, and userRole/Segments
      // We just ensure we have an array and do a final safety check
      const activeBanners = (response.data || []).filter((b: any) => b.isActive);
      setBanners(activeBanners);
    } catch (error) {
      console.error('Failed to fetch banners', error);
    }
  };

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
      router.replace('/customer');
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
  }, [searchParams.toString()]);

  const handleToggleSection = (sectionKey: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionKey]: !prev[sectionKey],
    }));
  };

  const handleCategoryClick = (category: string, subCategory?: string) => {
    // Navigate to the dedicated category page for consistency with All Categories page
    if (subCategory) {
      router.push(
        `/categories/${encodeURIComponent(category)}?subCategory=${encodeURIComponent(subCategory)}`
      );
    } else {
      router.push(`/categories/${encodeURIComponent(category)}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20 md:pb-0">
      <Header />

      {!selectedCategory && !selectedCategoryTag && !selectedCollection && !searchTerm && (
        <>
          <HeroCarousel banners={banners} />
          <StatsCounter productCount={products.length} brandCount={brands.length} />
        </>
      )}

      <main className="w-full px-4 py-8 md:px-8 xl:px-12">
        {/* Recommendation sections — new_arrivals always first ("Just Landed"), then bandit-ordered rest */}
        {!selectedCategory &&
          !selectedCategoryTag &&
          !selectedCollection &&
          !searchTerm &&
          (() => {
            const allSections: {
              key: string;
              label: string;
              title: string;
              subtitle: string;
              ref: React.RefObject<HTMLDivElement>;
              items: any[];
              slot: string;
              show: boolean;
            }[] = [
              {
                key: 'new_arrivals',
                label: 'Just Landed',
                title: 'New Arrivals',
                subtitle:
                  'Discover our latest additions — fresh designs and premium quality pieces just for you.',
                ref: newArrivalsRef,
                items: newArrivals,
                slot: 'new_arrivals',
                show: newArrivals.length > 0,
              },
              {
                key: 'customer_favourites',
                label: 'Your picks',
                title: 'Customer Favourites',
                subtitle: 'Bestsellers loved by customers.',
                ref: customerFavouritesRef,
                items: customerFavourites,
                slot: 'customer_favourites',
                show: customerFavourites.length > 0,
              },
              {
                key: 'trending_now',
                label: 'Hot right now',
                title: 'Trending Now',
                subtitle: 'What retail customers are buying (search-to-sale, last 7 days).',
                ref: trendingNowRef,
                items: trendingNow,
                slot: 'trending_now',
                show: trendingNow.length > 0,
              },
              {
                key: 'explore',
                label: 'Discover',
                title: 'Explore',
                subtitle: 'Best sellers from categories you might like to try.',
                ref: exploreRef,
                items: explore,
                slot: 'explore',
                show: explore.length > 0 && !!user,
              },
            ];
            const styles: Record<string, { span: string; bar: string }> = {
              new_arrivals: { span: 'text-[#D4AF37]', bar: 'from-[#1a4d33] to-[#D4AF37]' },
              customer_favourites: { span: 'text-[#1a4d33]', bar: 'from-[#1a4d33] to-[#D4AF37]' },
              trending_now: { span: 'text-amber-600', bar: 'from-amber-500 to-amber-200' },
              explore: { span: 'text-violet-600', bar: 'from-violet-500 to-violet-200' },
            };
            // new_arrivals always first, rest follow bandit order
            const newArrSec = allSections.find((s) => s.key === 'new_arrivals');
            const banditOrder = (
              sectionOrder.length
                ? sectionOrder
                : ['customer_favourites', 'trending_now', 'explore']
            ).filter((s) => s !== 'new_arrivals');
            const rest = banditOrder
              .map((s) => allSections.find((sec) => sec.key === s))
              .filter((sec): sec is NonNullable<typeof sec> => !!sec && sec.show);
            const ordered = [...(newArrSec && newArrSec.show ? [newArrSec] : []), ...rest];
            return ordered.map((sec) => (
              <section key={sec.key} ref={sec.ref} className="mb-20">
                <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
                  <div className="relative">
                    <span
                      className={`${styles[sec.key]?.span || ''} mb-2 block text-xs font-semibold uppercase tracking-[0.2em]`}
                    >
                      {sec.label}
                    </span>
                    <h2 className="text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
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
                        key={p._id}
                        className="animate-fade-in-up opacity-0"
                        style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'forwards' }}
                      >
                        <HoverProductCard
                          product={{ ...p, isNew: false, bestSeller: false }}
                          onClick={() => {
                            trackRecommendationProductClick({
                              productId: p._id,
                              productName: p.name,
                              recommendationSlot: sec.slot,
                            });
                            router.push(`/customer/product/${p._id}`);
                          }}
                          cartQuantity={
                            cart?.items?.find((i: any) => (i.product?._id || i.product) === p._id)
                              ?.quantity || 0
                          }
                          onAddToCart={(e) => {
                            e.stopPropagation();
                            addToCart(p._id, 1, p);
                          }}
                          onIncrement={(e) => {
                            e.stopPropagation();
                            const item = cart?.items?.find(
                              (i: any) => (i.product?._id || i.product) === p._id
                            );
                            if (item) updateQuantity(item._id, (item.quantity || 1) + 1);
                          }}
                          onDecrement={(e) => {
                            e.stopPropagation();
                            const item = cart?.items?.find(
                              (i: any) => (i.product?._id || i.product) === p._id
                            );
                            if (item) {
                              if ((item.quantity || 1) <= 1) removeFromCart(item._id);
                              else updateQuantity(item._id, (item.quantity || 1) - 1);
                            }
                          }}
                        />
                      </div>
                    ))}
                </div>

                {sec.items.length > 6 && (
                  <div className="relative mt-12 flex justify-center border-t border-gray-100 pt-8">
                    <button
                      onClick={() => handleToggleSection(sec.key)}
                      className="absolute -top-6 flex items-center gap-2 rounded-full border border-gray-200 bg-white px-8 py-3 font-semibold text-gray-900 shadow-sm transition-all hover:shadow-md"
                    >
                      {expandedSections[sec.key] ? (
                        <>
                          Show less
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 15l7-7 7 7"
                            />
                          </svg>
                        </>
                      ) : (
                        <>
                          Show more
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 9l-7 7-7-7"
                            />
                          </svg>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </section>
            ));
          })()}

        {/* Collections Section */}
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
                  <h2 className="text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
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
                    key={col._id}
                    className="animate-fade-in-up group relative aspect-[4/3] cursor-pointer overflow-hidden rounded-2xl opacity-0 shadow-lg"
                    style={{ animationDelay: `${index * 100}ms`, animationFillMode: 'forwards' }}
                    onClick={() => router.push(`/collections/${encodeURIComponent(col._id)}`)}
                  >
                    <img
                      src={getImageUrlWithFallback(col.imageUrl)}
                      alt={col.name}
                      className="absolute inset-0 h-full w-full object-cover transition-transform duration-[8000ms] ease-out group-hover:scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-80 transition-opacity duration-500 group-hover:opacity-90" />
                    <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-8">
                      <div className="transform transition-transform duration-500 group-hover:translate-y-[-8px]">
                        <h3 className="mb-2 text-xl font-bold leading-tight text-white md:text-2xl">
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
                    <div className="absolute right-4 top-4 h-8 w-8 rounded-tr-lg border-r-2 border-t-2 border-white/30 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
                  </div>
                ))}
              </div>
            </section>
          )}

        {/* Shop by Category Section */}
        {categories.length > 0 &&
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
                  <h2 className="text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
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
                {categories.slice(0, 24).map((cat, index) => (
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
                      <div className="absolute inset-0 rounded-full bg-emerald-500/0 transition-colors duration-300 group-hover:bg-emerald-500/10" />
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

              <div className="mt-8 text-center md:hidden">
                <button
                  onClick={() => router.push('/categories')}
                  className="inline-flex items-center gap-2 rounded-full bg-[#1a4d33] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#143b27]"
                >
                  See All Categories
                  <svg
                    className="h-4 w-4"
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
            </section>
          )}

        {/* Brands Section */}
        {brands.length > 0 &&
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
                  <h2 className="text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
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
                items={brands.map((b) => {
                  const name = typeof b === 'string' ? b : b?.name || '';
                  const id = typeof b === 'object' && b?._id ? b._id : name;
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
          )}

        {/* Product Catalog (search, filter, category, collection views) */}
        {(selectedCategory || selectedCategoryTag || selectedCollection || searchTerm) && (
          <>
            {/* Search Hero Banner - text only, no thumbnail */}
            {searchTerm && (
              <HeroBanner
                title={`"${searchTerm}"`}
                subtitle={`Showing results for your search`}
                breadcrumbs={[{ label: 'Home', href: '/customer' }, { label: 'Search Results' }]}
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

      {/* Auth Modal */}
      {showAuthModal && (
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          initialMode={authModalMode}
        />
      )}

      {/* Theme Switcher */}
      <ThemeSwitcher />

      {/* Bottom Google Ratings */}
      {!selectedCategory && !selectedCategoryTag && !selectedCollection && !searchTerm && (
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
                  <span className="ml-2 text-xl font-black text-gray-800">
                    {googleRating.rating} / 5
                  </span>
                </div>
                <p className="text-sm font-bold uppercase leading-none tracking-widest text-gray-500">
                  Verified by {googleRating.reviewCount} Happy Customers on Google
                </p>
              </div>
            </div>
            <a
              href="https://share.google/6nwo4Mqy2qMRtztbF"
              target="_blank"
              rel="noopener noreferrer"
              className="whitespace-nowrap rounded-full bg-gray-900 px-8 py-3 text-xs font-black uppercase tracking-widest text-white shadow-md transition-all hover:bg-gray-800 active:scale-95"
            >
              WRITE A REVIEW
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
