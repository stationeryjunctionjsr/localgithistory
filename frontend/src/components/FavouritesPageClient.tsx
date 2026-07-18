'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import Header from '@/components/Header';
import HoverProductCard from '@/components/HoverProductCard';

interface FavouritesPageClientProps {
  type: 'customer' | 'business';
}

interface Filters {
  categories: string[];
  subCategories: string[];
  brands: string[];
  states: string[];
  cities: string[];
}

const PRICE_MAX = 100000;

export default function FavouritesPageClient({ type }: FavouritesPageClientProps) {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  // Active filter state
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubCategory, setSelectedSubCategory] = useState('');
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedAvailable, setSelectedAvailable] = useState<'' | 'true' | 'false'>('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedCity, setSelectedCity] = useState('');

  // Data state
  const [products, setProducts] = useState<any[]>([]);
  const [filters, setFilters] = useState<Filters>({
    categories: [],
    subCategories: [],
    brands: [],
    states: [],
    cities: [],
  });
  const [cityName, setCityName] = useState('');
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterOpen, setFilterOpen] = useState(false);

  const isWholesaler = (user?.effectiveRole || user?.role) === 'wholesaler';

  // Redirect non-wholesalers
  useEffect(() => {
    if (!authLoading && (!user || !isWholesaler)) {
      router.push('/wholesaler');
    }
  }, [user, authLoading, isWholesaler, router]);

  const fetchProducts = useCallback(async () => {
    if (!user || !isWholesaler) return;
    setLoading(true);
    try {
      const params: Record<string, string> = { type };
      if (selectedCategory) params.category = selectedCategory;
      if (selectedSubCategory) params.sub_category = selectedSubCategory;
      if (selectedBrand) params.brand = selectedBrand;
      if (selectedAvailable) params.available = selectedAvailable;
      if (minPrice) params.min_price = minPrice;
      if (maxPrice) params.max_price = maxPrice;
      if (selectedState) params.state = selectedState;
      if (selectedCity) params.city = selectedCity;

      const res = await api.get('/recommendations/favourites', { params });
      const data = res.data || {};
      setProducts(data.products || []);
      setTotal(data.total || 0);
      setCityName(data.cityName || '');
      if (data.filters) {
        setFilters(data.filters);
      }
    } catch (err) {
      console.error('Failed to fetch favourites', err);
    } finally {
      setLoading(false);
    }
  }, [
    user, isWholesaler, type,
    selectedCategory, selectedSubCategory, selectedBrand,
    selectedAvailable, minPrice, maxPrice, selectedState, selectedCity,
  ]);

  // Initial load
  useEffect(() => {
    if (!authLoading && user && isWholesaler) {
      fetchProducts();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, user]);

  // Re-fetch on filter changes (debounced for price inputs)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (authLoading || !user || !isWholesaler) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchProducts();
    }, 350);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    selectedCategory, selectedSubCategory, selectedBrand,
    selectedAvailable, minPrice, maxPrice, selectedState, selectedCity,
  ]);

  // When state changes, clear city (cities will be re-loaded from server)
  const handleStateChange = (val: string) => {
    setSelectedState(val);
    setSelectedCity('');
  };

  // When category changes, clear sub-category
  const handleCategoryChange = (val: string) => {
    setSelectedCategory(val);
    setSelectedSubCategory('');
  };

  const handleProductClick = (p: any) => {
    router.push(`/wholesaler/product/${p._id}`);
  };

  const clearAllFilters = () => {
    setSelectedCategory('');
    setSelectedSubCategory('');
    setSelectedBrand('');
    setSelectedAvailable('');
    setMinPrice('');
    setMaxPrice('');
    setSelectedState('');
    setSelectedCity('');
  };

  const hasActiveFilters =
    selectedCategory || selectedSubCategory || selectedBrand ||
    selectedAvailable || minPrice || maxPrice || selectedState || selectedCity;

  const pageTitle = type === 'customer' ? 'Customer Favourites' : 'Business Favourites';
  const pageSubtitle =
    type === 'customer'
      ? 'Top products by retail customer sales, ranked highest to lowest.'
      : 'Top products by wholesaler order volume, ranked highest to lowest.';

  // Skeleton cards for loading state
  const SkeletonCard = () => (
    <div className="animate-pulse rounded-2xl bg-white overflow-hidden shadow-sm">
      <div className="aspect-[3/4] bg-gray-100" />
      <div className="p-3 space-y-2">
        <div className="h-3 bg-gray-100 rounded w-3/4" />
        <div className="h-3 bg-gray-100 rounded w-1/2" />
        <div className="h-4 bg-gray-100 rounded w-1/3" />
      </div>
    </div>
  );

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-emerald-700" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* ── Page Hero ── */}
      <div className="relative overflow-hidden bg-gradient-to-br from-[#1a4d33] via-[#1a4d33] to-emerald-800 px-6 py-14 md:px-12 xl:px-20">
        {/* decorative circles */}
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/5" />
        <div className="pointer-events-none absolute -bottom-16 -left-16 h-56 w-56 rounded-full bg-white/5" />

        <button
          onClick={() => router.push('/wholesaler')}
          className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-emerald-200 transition-colors hover:text-white"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </button>

        <div className="relative">
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.25em] text-emerald-300">
            {type === 'customer' ? 'RETAIL PICK' : 'PRO CHOICE'}
          </p>
          <h1 className="text-3xl font-black tracking-tight text-white md:text-5xl">
            {pageTitle}
            {cityName && (
              <span className="ml-3 inline-block rounded-full bg-white/15 px-4 py-1 text-base font-semibold text-emerald-100 backdrop-blur-sm md:text-xl">
                📍 {cityName}
              </span>
            )}
          </h1>
          <p className="mt-3 max-w-xl text-sm text-emerald-200 md:text-base">{pageSubtitle}</p>
        </div>
      </div>

      <div className="px-4 py-10 md:px-12 xl:px-20">
        <div className="flex flex-col gap-8 lg:flex-row">

          {/* ── Filter Sidebar (desktop) / Drawer (mobile) ── */}
          <>
            {/* Mobile filter toggle */}
            <div className="lg:hidden">
              <button
                onClick={() => setFilterOpen(true)}
                className="flex w-full items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-3.5 text-sm font-semibold text-gray-800 shadow-sm"
              >
                <span className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-emerald-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 4h18M7 8h10M10 12h4" />
                  </svg>
                  Filters
                  {hasActiveFilters && (
                    <span className="rounded-full bg-emerald-700 px-2 py-0.5 text-xs font-bold text-white">
                      ON
                    </span>
                  )}
                </span>
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* Mobile Drawer overlay */}
            {filterOpen && (
              <div
                className="fixed inset-0 z-40 bg-black/40 lg:hidden"
                onClick={() => setFilterOpen(false)}
              />
            )}

            {/* Sidebar — desktop always visible, mobile slide-in drawer */}
            <aside
              className={`fixed inset-y-0 left-0 z-50 w-80 overflow-y-auto bg-white p-6 shadow-xl transition-transform duration-300 lg:relative lg:inset-auto lg:z-auto lg:w-72 lg:translate-x-0 lg:rounded-2xl lg:shadow-sm lg:border lg:border-gray-100 lg:p-6 ${
                filterOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
              }`}
            >
              {/* Sidebar header */}
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-base font-bold text-gray-900">Filters</h2>
                <div className="flex items-center gap-3">
                  {hasActiveFilters && (
                    <button
                      onClick={clearAllFilters}
                      className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 transition-colors"
                    >
                      Clear all
                    </button>
                  )}
                  <button
                    onClick={() => setFilterOpen(false)}
                    className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 lg:hidden"
                  >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="space-y-6">
                {/* Category */}
                <FilterGroup label="Category">
                  <select
                    id="filter-category"
                    value={selectedCategory}
                    onChange={(e) => handleCategoryChange(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">All Categories</option>
                    {filters.categories.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </FilterGroup>

                {/* Sub-category — only show when category is selected or subCategories available */}
                {filters.subCategories.length > 0 && (
                  <FilterGroup label="Sub-category">
                    <select
                      id="filter-subcategory"
                      value={selectedSubCategory}
                      onChange={(e) => setSelectedSubCategory(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    >
                      <option value="">All Sub-categories</option>
                      {filters.subCategories.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </FilterGroup>
                )}

                {/* Brand */}
                {filters.brands.length > 0 && (
                  <FilterGroup label="Brand">
                    <select
                      id="filter-brand"
                      value={selectedBrand}
                      onChange={(e) => setSelectedBrand(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    >
                      <option value="">All Brands</option>
                      {filters.brands.map((b) => (
                        <option key={b} value={b}>{b}</option>
                      ))}
                    </select>
                  </FilterGroup>
                )}

                {/* Availability */}
                <FilterGroup label="Availability">
                  <div className="flex gap-2">
                    {(['', 'true', 'false'] as const).map((val) => (
                      <button
                        key={val}
                        onClick={() => setSelectedAvailable(val)}
                        className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                          selectedAvailable === val
                            ? 'border-emerald-600 bg-emerald-600 text-white'
                            : 'border-gray-200 bg-white text-gray-600 hover:border-emerald-400'
                        }`}
                      >
                        {val === '' ? 'All' : val === 'true' ? 'In Stock' : 'Out of Stock'}
                      </button>
                    ))}
                  </div>
                </FilterGroup>

                {/* Price range */}
                <FilterGroup label="Price (₹)">
                  <div className="flex items-center gap-2">
                    <input
                      id="filter-min-price"
                      type="number"
                      min={0}
                      placeholder="Min"
                      value={minPrice}
                      onChange={(e) => setMinPrice(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                    <span className="text-gray-400">–</span>
                    <input
                      id="filter-max-price"
                      type="number"
                      min={0}
                      placeholder="Max"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                </FilterGroup>

                {/* State — hidden for now; wholesaler's city is auto-applied */}
                <div className="hidden">
                {filters.states.length > 0 && (
                  <FilterGroup label="State">
                    <select
                      id="filter-state"
                      value={selectedState}
                      onChange={(e) => handleStateChange(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    >
                      <option value="">All States</option>
                      {filters.states.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </FilterGroup>
                )}
                </div>

                {/* City — hidden for now; wholesaler's city is auto-applied */}
                <div className="hidden">
                {filters.cities.length > 0 && (
                  <FilterGroup label="City">
                    <select
                      id="filter-city"
                      value={selectedCity}
                      onChange={(e) => setSelectedCity(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    >
                      <option value="">All Cities</option>
                      {filters.cities.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </FilterGroup>
                )}
                </div>
              </div>
            </aside>
          </>

          {/* ── Product Grid ── */}
          <div className="flex-1 min-w-0">
            {/* Result count bar */}
            <div className="mb-6 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                {loading ? (
                  <span className="inline-block h-4 w-32 animate-pulse rounded bg-gray-200" />
                ) : (
                  <>
                    <span className="font-semibold text-gray-900">{total}</span>{' '}
                    product{total !== 1 ? 's' : ''} found
                    {cityName && !selectedCity && (
                      <span className="ml-1 text-emerald-700">in {cityName}</span>
                    )}
                    {selectedCity && (
                      <span className="ml-1 text-emerald-700">in {selectedCity}</span>
                    )}
                  </>
                )}
              </p>
              <p className="text-xs font-medium uppercase tracking-widest text-gray-400">
                Ranked by sales
              </p>
            </div>

            {/* Grid */}
            {loading ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {Array.from({ length: 15 }).map((_, i) => (
                  <SkeletonCard key={i} />
                ))}
              </div>
            ) : products.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-white py-24 text-center">
                <svg className="mb-4 h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p className="text-base font-semibold text-gray-500">No products found</p>
                <p className="mt-1 text-sm text-gray-400">Try adjusting your filters.</p>
                {hasActiveFilters && (
                  <button
                    onClick={clearAllFilters}
                    className="mt-5 rounded-full bg-emerald-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800 transition-colors"
                  >
                    Clear filters
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {products.map((p, index) => (
                  <div
                    key={p._id}
                    className="animate-fade-in-up opacity-0"
                    style={{ animationDelay: `${Math.min(index, 20) * 40}ms`, animationFillMode: 'forwards' }}
                  >
                    <HoverProductCard
                      product={{ ...p, isNew: false, bestSeller: false }}
                      onClick={() => handleProductClick(p)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Small helper component ──
function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-2 text-xs font-bold uppercase tracking-widest text-gray-400">{label}</p>
      {children}
    </div>
  );
}
