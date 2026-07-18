'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { useAuth } from '@/context/AuthContext';

interface Brand {
  _id?: string;
  name?: string;
  logoUrl?: string;
  logo?: string;
}

interface Category {
  _id: string;
  name: string;
  subCategories?: string[];
}

export interface BrandsClientProps {
  initialBrands?: Brand[];
  initialCategories?: Category[];
  initialBanners?: any[];
}

export default function BrandsClient({
  initialBrands,
  initialCategories,
  initialBanners,
}: BrandsClientProps) {
  const router = useRouter();
  const { user } = useAuth();

  // Data State
  const [allBrands, setAllBrands] = useState<Brand[]>(initialBrands || []);
  const [categories, setCategories] = useState<Category[]>(initialCategories || []);
  const [banners, setBanners] = useState<any[]>(initialBanners || []);

  // UI State
  const [loading, setLoading] = useState(!initialBrands);
  const [loadingFilter, setLoadingFilter] = useState(false);
  const [search, setSearch] = useState('');

  // Filter Selection
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [selectedSubCategory, setSelectedSubCategory] = useState<string>('');
  const [filteredBrandNames, setFilteredBrandNames] = useState<Set<string> | null>(null); // null means no category filter active

  const effectiveRole = user?.effectiveRole || user?.role || 'guest';
  const basePath = user?.role === 'wholesaler' ? '/wholesaler' : '/customer';

  // Initial Load
  useEffect(() => {
    const load = async () => {
      if (initialBrands && initialBrands.length > 0) return; // Skip if loaded by SSR
      setLoading(true);
      try {
        const [brandsRes, catsRes, bannerRes] = await Promise.all([
          api.get('/brands/public'),
          api.get('/categories/public'),
          api
            .get('/banners/public', {
              params: {
                pageType: 'all_brands',
                position: 'all_brands',
                userRole: effectiveRole,
              },
            })
            .catch(() => ({ data: [] })),
        ]);
        setAllBrands(Array.isArray(brandsRes.data) ? brandsRes.data : brandsRes.data?.brands || []);
        setCategories(Array.isArray(catsRes.data) ? catsRes.data : catsRes.data?.data || []);
        const activeBanners = (bannerRes.data || []).filter(
          (b: any) =>
            b.isActive && (b.targetAudience === 'all' || b.targetAudience === effectiveRole)
        );
        setBanners(activeBanners);
      } catch {
        setAllBrands([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [effectiveRole, initialBrands]);

  // Filter Logic - Fetch eligible brands when category changes
  useEffect(() => {
    const fetchEligibleBrands = async () => {
      if (!selectedCategory) {
        setFilteredBrandNames(null);
        return;
      }

      setLoadingFilter(true);
      try {
        const params: any = { category: selectedCategory.name, limit: 1 }; // Limit 1 is faster, we just need the 'brands' aggregation
        if (selectedSubCategory) params.subCategory = selectedSubCategory;

        const res = await api.get('/products/public', { params });
        const eligibleBrands = res.data.brands || [];
        setFilteredBrandNames(new Set(eligibleBrands));
      } catch (error) {
        console.error('Error filtering brands', error);
        setFilteredBrandNames(new Set()); // No results on error
      } finally {
        setLoadingFilter(false);
      }
    };
    fetchEligibleBrands();
  }, [selectedCategory, selectedSubCategory]);

  // Final Derived List
  const displayedBrands = useMemo(() => {
    let list = allBrands;

    // Apply Category/SubCategory Filter (via fetched eligible names)
    if (filteredBrandNames !== null) {
      list = list.filter((b) => b.name && filteredBrandNames.has(b.name));
    }

    // Apply Search
    const term = search.trim().toLowerCase();
    if (term) {
      list = list.filter((b) => (b.name || '').toLowerCase().includes(term));
    }

    return list;
  }, [allBrands, filteredBrandNames, search]);

  const breadcrumbs = [
    { label: 'Home', href: user ? basePath : '/' },
    { label: 'Brands' },
  ];

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="w-full">
        {/* Hero Section */}
        <HeroBanner
          banners={banners}
          title="All Brands"
          subtitle="Discover products from our trusted brand partners"
          stat={`Showing ${displayedBrands.length} brand${displayedBrands.length !== 1 ? 's' : ''}`}
          breadcrumbs={breadcrumbs}
          hideThumbnail={true}
        />

        <main className="mx-auto max-w-[1600px] px-4 py-4 md:px-6">
          <div className="flex flex-col gap-6 md:flex-row">
            {/* Sidebar Filters */}
            <div className="w-full flex-shrink-0 md:w-64">
              <div className="sticky top-28 rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
                <h2 className="mb-4 text-lg font-semibold uppercase tracking-widest text-slate-800">
                  Filters
                </h2>

                {/* Categories */}
                <div className="mb-2">
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-700">
                    Category
                  </h3>
                  <div className="custom-scrollbar max-h-[500px] space-y-2 overflow-y-auto pr-2">
                    <label className="group flex cursor-pointer items-center gap-3 rounded p-1 hover:bg-slate-50">
                      <div className="relative flex items-center">
                        <input
                          type="radio"
                          name="category_filter"
                          checked={selectedCategory === null}
                          onChange={() => {
                            setSelectedCategory(null);
                            setSelectedSubCategory('');
                          }}
                          className="peer h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </div>
                      <span
                        className={`text-sm ${!selectedCategory ? 'font-medium text-indigo-600' : 'text-slate-600 group-hover:text-slate-900'}`}
                      >
                        All Categories
                      </span>
                    </label>

                    {categories.map((cat) => (
                      <div key={cat._id}>
                        <label className="group flex cursor-pointer items-center gap-3 rounded p-1 hover:bg-slate-50">
                          <div className="relative flex items-center">
                            <input
                              type="radio"
                              name="category_filter"
                              checked={selectedCategory?._id === cat._id}
                              onChange={() => {
                                setSelectedCategory(cat);
                                setSelectedSubCategory('');
                              }}
                              className="peer h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            />
                          </div>
                          <span
                            className={`text-sm transition-colors group-hover:text-slate-900 ${selectedCategory?._id === cat._id ? 'font-medium text-indigo-600' : 'text-slate-600'}`}
                          >
                            {cat.name}
                          </span>
                        </label>

                        {/* Sub-Categories (Show inline when category is selected) */}
                        {selectedCategory?._id === cat._id &&
                          cat.subCategories &&
                          cat.subCategories.length > 0 && (
                            <div className="animate-fadeIn ml-7 mt-1.5 space-y-1.5 border-l-2 border-indigo-100 pl-3">
                              <label className="group flex cursor-pointer items-center gap-2 py-0.5">
                                <input
                                  type="radio"
                                  name="sub_category_filter"
                                  checked={selectedSubCategory === ''}
                                  onChange={() => setSelectedSubCategory('')}
                                  className="h-3.5 w-3.5 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                <span
                                  className={`text-xs ${!selectedSubCategory ? 'font-medium text-indigo-600' : 'text-slate-500 group-hover:text-slate-700'}`}
                                >
                                  All
                                </span>
                              </label>
                              {cat.subCategories.map((sub) => (
                                <label
                                  key={sub}
                                  className="group flex cursor-pointer items-center gap-2 py-0.5"
                                >
                                  <input
                                    type="radio"
                                    name="sub_category_filter"
                                    checked={selectedSubCategory === sub}
                                    onChange={() => setSelectedSubCategory(sub)}
                                    className="h-3.5 w-3.5 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                  />
                                  <span
                                    className={`text-xs transition-colors group-hover:text-slate-700 ${selectedSubCategory === sub ? 'font-medium text-indigo-600' : 'text-slate-500'}`}
                                  >
                                    {sub}
                                  </span>
                                </label>
                              ))}
                            </div>
                          )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="min-w-0 flex-1">
              {/* Grid */}
              {loading || loadingFilter ? (
                <div className="flex min-h-[400px] flex-col items-center justify-center">
                  <div className="mb-4 h-10 w-10 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600"></div>
                  <p className="font-medium text-slate-500">
                    {loading ? 'Loading brands...' : 'Filtering brands...'}
                  </p>
                </div>
              ) : displayedBrands.length > 0 ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                  {displayedBrands.map((item) => (
                    <button
                      key={item._id || item.name}
                      type="button"
                      onClick={() => router.push(`/brands/${encodeURIComponent(item.name || '')}`)}
                      className="group relative flex aspect-square flex-col items-center justify-center overflow-hidden rounded-xl border border-slate-100 bg-white p-3 text-center shadow-sm transition-all hover:border-indigo-100 hover:shadow-md"
                    >
                      <div className="mb-3 flex h-32 w-32 items-center justify-center rounded-full bg-slate-50 transition-transform duration-300 group-hover:scale-110">
                        {item.logoUrl || item.logo ? (
                          <img
                            src={getImageUrlWithFallback(item.logoUrl || item.logo)}
                            alt={item.name || ''}
                            className="h-24 w-24 object-contain mix-blend-multiply"
                          />
                        ) : (
                          <span className="text-4xl font-semibold text-slate-400 opacity-50">
                            {(item.name || '?')[0].toUpperCase()}
                          </span>
                        )}
                      </div>
                      <h3 className="line-clamp-2 text-sm font-medium text-slate-800 transition-colors group-hover:text-indigo-600">
                        {item.name}
                      </h3>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="flex min-h-[400px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50">
                  <span className="mb-4 text-4xl">🏢</span>
                  <h3 className="text-lg font-semibold text-slate-800">No brands found</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Try adjusting your filters or search terms
                  </p>
                  <button
                    onClick={() => {
                      setSelectedCategory(null);
                      setSelectedSubCategory('');
                      setSearch('');
                    }}
                    className="mt-6 rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:text-slate-900"
                  >
                    Clear all filters
                  </button>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
