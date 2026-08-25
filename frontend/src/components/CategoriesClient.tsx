'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/utils/api';
import { useAuth } from '@/context/AuthContext';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { logger } from '@/utils/logger';
// Add carousel import if missing

export interface CategoriesClientProps {
  initialCategories?: any[];
  initialCategoryTags?: any[];
  initialBanners?: any[];
}

export default function CategoriesClient({
  initialCategories,
  initialCategoryTags,
  initialBanners,
}: CategoriesClientProps) {
  const router = useRouter();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const [categories, setCategories] = useState<
    Array<{ _id?: string; name: string; slug?: string; images?: string[]; categoryTags?: string[] }>
  >(initialCategories || []);
  const [categoryTags, setCategoryTags] = useState<
    Array<{ _id?: string; name?: string; description?: string }>
  >(initialCategoryTags || []);
  const [loading, setLoading] = useState(!initialCategories);
  const [banners, setBanners] = useState<any[]>(initialBanners || []);
  const [searchQuery, setSearchQuery] = useState('');

  const effectiveRole = user?.effectiveRole || user?.role || 'customer';
  const basePath = user?.role === 'wholesaler' ? '/wholesaler' : '/customer';

  // Vibrant gradient palette for category cards
  const gradients = [
    'from-violet-500 to-purple-600',
    'from-amber-400 to-orange-500',
    'from-emerald-400 to-teal-600',
    'from-sky-400 to-blue-600',
    'from-rose-400 to-pink-600',
    'from-lime-400 to-green-600',
    'from-fuchsia-400 to-purple-600',
    'from-cyan-400 to-teal-500',
    'from-red-400 to-rose-600',
    'from-indigo-400 to-blue-600',
  ];

  useEffect(() => {
    const load = async () => {
      if (initialCategories && initialCategories.length > 0) {
        // Initial data was provided by Server Component, skip fetching public data again immediately
        return;
      }
      try {
        const [categoryRes, tagRes, bannerRes] = await Promise.all([
          api.get('/categories/public/'),
          api.get('/category-tags/active'),
          api.get('/banners/public/', {
            params: {
              position: 'categories',
              pageType: 'all_categories',
              userRole: effectiveRole,
            },
          }),
        ]);

        const raw = categoryRes.data?.data ?? categoryRes.data ?? [];
        const list = Array.isArray(raw)
          ? raw
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
        setCategories(list);
        const tags = Array.isArray(tagRes.data) ? tagRes.data : tagRes.data?.data || [];
        setCategoryTags(tags.filter((t: any) => t && t.name));

        const activeBanners = (bannerRes.data || []).filter(
          (b: any) =>
            b.isActive && (b.targetAudience === 'all' || b.targetAudience === effectiveRole)
        );
        setBanners(activeBanners);
      } catch (e) {
        logger.error('Failed to fetch categories or banners', e);
        setCategories([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [effectiveRole, initialCategories]);

  const handleCategoryClick = (cat: { name: string; slug?: string }) => {
    const slug = cat.slug || cat.name;
    router.push(`/categories/${encodeURIComponent(slug)}`);
  };

  const filteredCategories = useMemo(
    () =>
      categories.filter((cat) =>
        String(cat?.name || '')
          .toLowerCase()
          .includes(searchQuery.toLowerCase())
      ),
    [categories, searchQuery]
  );

  const groupedCategories = useMemo(() => {
    const groups = categoryTags.map((tagObj) => {
      const tagName = tagObj.name || '';
      return {
        tag: tagName,
        description: tagObj.description || tagName,
        categories: filteredCategories.filter((c) =>
          (c.categoryTags || []).some((t) => t.toLowerCase() === tagName.toLowerCase())
        ),
      };
    });

    const usedTagNames = new Set(categoryTags.map((t) => (t.name || '').toLowerCase()));
    const untagged = filteredCategories.filter(
      (c) => !(c.categoryTags || []).some((t) => usedTagNames.has(t.toLowerCase()))
    );

    if (untagged.length > 0) {
      groups.push({
        tag: 'Other',
        description: 'Other Collections',
        categories: untagged,
      });
    }

    return groups.filter((g) => g.categories.length > 0);
  }, [filteredCategories, categoryTags]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Hero Section */}
      <HeroBanner
        banners={banners}
        title="All Categories"
        subtitle="Discover products by their type and utility"
        stat={`Exploring ${categories.length} categories`}
        breadcrumbs={[
          { label: 'Home', href: user ? basePath : '/' },
          { label: 'Categories' },
        ]}
        hideThumbnail={true}
      />

      {/* Main Content */}
      <main className="pb-20">
        {loading ? (
          <div className="flex min-h-[400px] flex-col items-center justify-center gap-4">
            <div className="border-3 h-12 w-12 animate-spin rounded-full border-gray-200 border-t-emerald-600"></div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-gray-400">
              Loading Categories
            </p>
          </div>
        ) : groupedCategories.length === 0 ? (
          <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-gray-400">
            <span className="mb-4 text-5xl" aria-hidden>
              🔍
            </span>
            <p className="text-lg font-bold text-gray-600">No categories found</p>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="mt-4 text-sm font-bold uppercase tracking-wider text-emerald-600 hover:underline"
              >
                Clear Search
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-10 pt-6">
            {groupedCategories.map((group, groupIndex) => (
              <section key={group.tag} className="px-4 md:px-8 xl:px-12">
                {/* Section Header */}
                <div className="mb-6 flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div
                        className={`h-8 w-1 rounded-full bg-gradient-to-b ${gradients[groupIndex % gradients.length]}`}
                      />
                      <div>
                        <h2 className="text-lg font-medium uppercase tracking-widest text-gray-900 md:text-xl">
                          {group.tag}
                        </h2>
                        <p className="mt-0.5 hidden text-xs font-medium text-gray-400 md:block">
                          {group.description}
                        </p>
                      </div>
                    </div>
                  </div>
                  <span className="text-xs font-bold uppercase tracking-widest text-gray-300">
                    {group.categories.length} items
                  </span>
                </div>

                {/* Category Cards Grid */}
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 md:gap-4 lg:grid-cols-5 xl:grid-cols-6">
                  {group.categories.map((cat: any, index) => {
                    const catName = cat?.name ?? '';
                    const catImage = cat?.images?.[0]
                      ? getImageUrlWithFallback(cat.images[0])
                      : null;
                    const gradient = gradients[(index + groupIndex * 3) % gradients.length];

                    return (
                      <button
                        key={catName}
                        onClick={() => handleCategoryClick(cat)}
                        className="group relative overflow-hidden rounded-2xl border border-gray-100/80 bg-white shadow-sm transition-all duration-500 hover:shadow-xl active:scale-[0.97]"
                      >
                        {/* Image / Gradient Background */}
                        <div className="relative aspect-[4/3] overflow-hidden">
                          {catImage ? (
                            <>
                              <img
                                src={catImage}
                                alt={catName}
                                className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
                              />
                              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
                            </>
                          ) : (
                            <div
                              className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-90`}
                            >
                              <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_70%,rgba(255,255,255,0.2),transparent)]" />
                            </div>
                          )}

                          {/* Category Name Overlay */}
                          <div className="absolute inset-0 flex flex-col items-center justify-center p-3">
                            <h3
                              className={`text-center text-sm font-semibold uppercase leading-tight tracking-wide md:text-base ${catImage ? 'text-white drop-shadow-lg' : 'text-white'}`}
                            >
                              {catName}
                            </h3>
                          </div>

                          {/* Hover Arrow */}
                          <div className="absolute bottom-3 right-3 flex h-7 w-7 translate-y-2 items-center justify-center rounded-full bg-white/20 opacity-0 backdrop-blur-sm transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100">
                            <svg
                              className="h-3.5 w-3.5 text-white"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                              strokeWidth="2.5"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
