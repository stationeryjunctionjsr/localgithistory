'use client';

import React, { useState, useRef, useEffect, Suspense } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { useWishlist } from '@/context/WishlistContext';
import { useCart } from '@/context/CartContext';
import { usePincode } from '@/context/PincodeContext';
import AuthModal from './AuthModal';
import GeneralFeedbackModal from './GeneralFeedbackModal';
import api from '@/utils/api';
import Link from 'next/link';
import styles from './Header.module.css';
import { trackBackendFilterClick } from '@/utils/analytics';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import CustomerNotificationsModal from './CustomerNotificationsModal';
import AccessibilityModal from './AccessibilityModal';
import { logger } from '@/utils/logger';

interface CategoryTag {
  _id: string;
  name: string;
}

interface Category {
  _id: string;
  name: string;
  slug?: string;
  categoryTag?: string;
  categoryTags?: string[];
  tags?: string[];
  subCategories?: string[];
}

interface Brand {
  _id: string;
  name: string;
  slug?: string;
  categories?: string[];
}

interface PromoStrip {
  _id: string;
  text: string;
  isActive: boolean;
}

/** Inner component that safely reads search params inside a Suspense boundary. */
function SearchParamsReader({ onRead }: { onRead: (tag: string | null) => void }) {
  const searchParams = useSearchParams();
  const tag = searchParams.get('categoryTag') || null;
  useEffect(() => { onRead(tag); }, [tag, onRead]);
  return null;
}

export default function Header() {
  const { user, logout } = useAuth();
  const { theme } = useTheme();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const { items: wishlistItems } = useWishlist();
  const { cart, openCart } = useCart();
  const { pincode, city, openPincodeModal } = usePincode();
  const router = useRouter();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const pathname = usePathname();
  const [activeCategoryTag, setActiveCategoryTag] = useState<string | null>(null);

  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [showNotificationsModal, setShowNotificationsModal] = useState(false);
  const [unreadNotifCount, setUnreadNotifCount] = useState(0);
  const cartCount = cart?.items.reduce((sum: number, item: any) => sum + (item.quantity || 0), 0) || 0;
  const [categoryTags, setCategoryTags] = useState<CategoryTag[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [brands, setBrands] = useState<Brand[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [categories, setCategories] = useState<Category[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [tagData, setTagData] = useState<
    Record<string, { categories: Category[]; brands: Brand[] }>
  >({});
  const [promoStrips, setPromoStrips] = useState<PromoStrip[]>([]);
  const [currentPromoIndex, setCurrentPromoIndex] = useState(0);
  const [showMoreTags, setShowMoreTags] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showAccessibilityModal, setShowAccessibilityModal] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [popularTerms, setPopularTerms] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [recentProducts, setRecentProducts] = useState<{ productId: string; productName: string; displayImage?: string; price?: number }[]>([]);
  // Live autocomplete results fetched from /products/suggest while user types
  const [liveAutocomplete, setLiveAutocomplete] = useState<{ products: { productId: string; name: string }[]; brands: string[]; categories: string[] }>({ products: [], brands: [], categories: [] });
  const [loadingAutocomplete, setLoadingAutocomplete] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const moreRef = useRef<HTMLDivElement>(null);

  const [availableCategories, setAvailableCategories] = useState<{ categoryNames: string[]; subCategories: Record<string, string[]>; brandNames: string[]; collectionNames: string[] } | null>(null);

  // Fetch category tags, brands, categories, and promo strips
  useEffect(() => {
    fetchCategoryTags();
    fetchBrands();
    fetchCategories();
    fetchPromoStrips();
  }, []);

  // Fetch available categories for current zone when pincode changes
  useEffect(() => {
    if (!pincode) {
      setAvailableCategories(null);
      return;
    }
    const currentRole = user?.effectiveRole || user?.role;
    const params: any = { pincode };
    if (currentRole) params.role = currentRole;
    
    api
      .get('/categories/available', { params })
      .then(res => setAvailableCategories(res.data))
      .catch(err => {
        logger.error('Failed to fetch available categories for zone', err);
        setAvailableCategories(null); // fail-open
      });
  }, [pincode]);

  // Debounced live autocomplete — fires 250ms after the user stops typing
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setLiveAutocomplete({ products: [], brands: [], categories: [] });
      return;
    }
    setLoadingAutocomplete(true);
    const timer = setTimeout(async () => {
      try {
        const params: Record<string, string> = { q: searchQuery.trim(), limit: '8' };
        if (activeCategoryTag) params.categoryTag = activeCategoryTag;
        // Pass effective role so backend can filter Wholesalers to Super Admin products
        const currentRole = user?.effectiveRole || user?.role;
        if (currentRole) params.role = currentRole;
        if (pincode) params.pincode = pincode;
        const res = await api.get('/products/suggest', { params });
        setLiveAutocomplete({
          products: res.data?.products || [],
          brands: res.data?.brands || [],
          categories: res.data?.categories || [],
        });
      } catch (e) { logger.warn("Silent catch block:", e); /* fail silently */ } finally {
        setLoadingAutocomplete(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, activeCategoryTag]);

  useEffect(() => {
    if (user) {
      const fetchUnreadCount = async () => {
        try {
          const res = await api.get('/push-notifications/inbox');
          const data = res.data || [];
          setUnreadNotifCount(data.filter((n: any) => !n.isRead).length);
        } catch (e) { logger.warn("Silent catch block:", e); /* fail silently */ }
      };
      fetchUnreadCount();
    }
  }, [user]);

  // Rotate promo strips seamlessly
  useEffect(() => {
    if (promoStrips.length > 1) {
      const interval = setInterval(() => {
        setIsTransitioning(true);
        setCurrentPromoIndex((prev) => prev + 1);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [promoStrips]);

  // Handle seamless loop reset
  useEffect(() => {
    if (currentPromoIndex === promoStrips.length) {
      const timer = setTimeout(() => {
        setIsTransitioning(false);
        setCurrentPromoIndex(0);
      }, 600); // Match CSS transition duration
      return () => clearTimeout(timer);
    }
  }, [currentPromoIndex, promoStrips.length]);



  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setShowProfileDropdown(false);
      }
      if (moreRef.current && !moreRef.current.contains(event.target as Node)) {
        setShowMoreTags(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchSuggestions = async () => {
    setLoadingSuggestions(true);
    try {
      const sessionId = localStorage.getItem('sessionId');
      const [recentRes, suggestionsRes, recentProductsRes] = await Promise.all([
        api.get('/tracking/recent', { params: { sessionId, limit: 5 } }),
        api.get('/tracking/suggestions', { params: { limit: 8 } }),
        api.get('/tracking/recent-products', { params: { sessionId, limit: 4 } }),
      ]);
      setRecentSearches(recentRes.data || []);
      setPopularTerms(suggestionsRes.data?.popularTerms || []);
      setRecentProducts(recentProductsRes.data || []);
    } catch (e) {
      logger.error('Failed to fetch suggestions', e);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleSearchBlur = () => {
    // Small delay to allow clicking on suggestions
    setTimeout(() => setShowSuggestions(false), 200);
  };

  const handleSuggestionClick = (term: string) => {
    setSearchQuery(term);
    router.push(`${getBasePath()}?searchTerm=${encodeURIComponent(term.trim())}`);
    setShowSuggestions(false);
  };

  const fetchCategoryTags = async () => {
    try {
      const response = await api.get('/category-tags/active');
      const tags = response.data || [];
      setCategoryTags(tags.filter((t: CategoryTag) => t.name));
    } catch (error) {
      logger.error('Error fetching category tags:', error);
    }
  };

  const fetchBrands = async () => {
    try {
      const response = await api.get('/brands/public');
      const brandList = response.data?.brands || response.data || [];
      setBrands(brandList.filter((b: Brand) => b.name));
    } catch (error) {
      logger.error('Error fetching brands:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories/public');
      const cats = response.data?.categories || response.data || [];
      setCategories(cats.filter((c: Category) => c.name));
    } catch (error) {
      logger.error('Error fetching categories:', error);
    }
  };

  // Get categories for a specific tag (filtered by zone availability)
  const getCategoriesForTag = (tagName: string): Category[] => {
    const targetTag = tagName.toLowerCase();
    const baseCats = categories.filter((c) => {
      const tag = c.categoryTag || (c.categoryTags && c.categoryTags[0]) || (c.tags && c.tags[0]);
      return (tag || "").toLowerCase() === targetTag;
    });

    if (!availableCategories) return baseCats; // no zone info, fail open

    return baseCats
      .filter((c) => availableCategories.categoryNames.includes(c.name))
      .map((c) => ({
        ...c,
        subCategories: (c.subCategories || []).filter((sub) =>
          (availableCategories.subCategories[c.name] || []).includes(sub)
        ),
      }));
  };

  // Get brands for categories under this tag
  // eslint-disable-next-line unused-imports/no-unused-vars
  const getBrandsForTag = (tagName: string): Brand[] => {
    return [];
  };

  const fetchPromoStrips = async () => {
    try {
      const response = await api.get('/promo-strips/active/');
      const activeStrips = response.data || [];
      setPromoStrips(activeStrips);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      setPromoStrips([]);
    }
  };



  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setIsSearching(true);
      // If the user is currently browsing a category tag, scope the search to that department
      const scopedTag = activeCategoryTag;
      const searchUrl = scopedTag
        ? `${getBasePath()}?searchTerm=${encodeURIComponent(searchQuery.trim())}&categoryTag=${encodeURIComponent(scopedTag)}`
        : `${getBasePath()}?searchTerm=${encodeURIComponent(searchQuery.trim())}`;
      router.push(searchUrl);
      setTimeout(() => {
        setIsSearching(false);
        setShowSuggestions(false);
      }, 500);
    }
  };

  const getBasePath = () => {
    if (!user) return '/';
    switch (user.role) {
      case 'customer':
        return '/customer';
      case 'wholesaler':
        return '/wholesaler';
      case 'super_admin':
        return '/admin';
      default:
        return '/';
    }
  };

  // Determine visible and overflow category tags
  const maxVisibleTags = 6;
  const filteredTags = categoryTags.filter(tag => getCategoriesForTag(tag.name).length > 0);
  const visibleTags = filteredTags.slice(0, maxVisibleTags);
  const overflowTags = filteredTags.slice(maxVisibleTags);

  return (
    <header className={`${styles.header} hidden md:block`}>
      <Suspense fallback={null}>
        <SearchParamsReader onRead={setActiveCategoryTag} />
      </Suspense>
      {/* Top Banner - Sliding Promo Strip */}
      {promoStrips.length > 0 && (
        <div className={styles.bannerContainer} style={{ background: theme.gradient }}>
          <div
            className={styles.bannerSlider}
            style={{
              transform: `translateX(-${currentPromoIndex * 100}%)`,
              transition: isTransitioning ? 'transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)' : 'none',
            }}
          >
            {promoStrips.map((strip) => (
              <div key={strip._id} className={styles.bannerSlide}>
                {strip.text}
              </div>
            ))}
            {/* Cloned first slide for seamless loop */}
            {promoStrips.length > 0 && (
              <div key="cloned-first" className={styles.bannerSlide}>
                {promoStrips[0].text}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Header */}
      <div className={styles.mainHeader}>
        <div className={styles.container}>
          {/* Logo - Goes to role-based dashboard, landing page for guests */}
          <div className="flex items-center gap-3 shrink-0">
            <Link
              href={getBasePath() === '/customer' ? '/customer?reset=true' : getBasePath()}
              className={styles.logo}
            >
              <span style={{ color: theme.primary }}>Stationery Junction</span>
            </Link>

            {/* Delivery Location Selector */}
            <button
              onClick={() => openPincodeModal(false)}
              className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full border border-emerald-700/20 bg-emerald-50/70 hover:bg-emerald-100/80 text-emerald-900 transition-colors text-xs font-semibold shrink-0 cursor-pointer shadow-sm"
              title="Change delivery location"
              type="button"
            >
              <svg className="h-3.5 w-3.5 text-emerald-700 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="max-w-[140px] truncate">
                {pincode ? `Deliver to ${pincode}${city ? ` (${city})` : ''}` : 'Select Pincode'}
              </span>
              <svg className="h-3 w-3 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Navigation - Category Tags from Super Admin */}
          <nav className={styles.nav} ref={navRef} aria-label="Main navigation">
            {visibleTags.map((tag: CategoryTag) => (
              <div
                key={tag._id}
                className={`${styles.navItem} ${activeCategory === tag._id ? styles.active : ''}`}
                tabIndex={0}
                role="button"
                aria-expanded={activeCategory === tag._id}
                aria-haspopup="true"
                onMouseEnter={() => {
                  setActiveCategory(tag._id);
                }}
                onMouseLeave={() => setActiveCategory(null)}
                onFocus={() => setActiveCategory(tag._id)}
                onBlur={(e) => {
                  // Only close if focus leaves the entire nav item (including mega menu children)
                  if (!e.currentTarget.contains(e.relatedTarget as Node)) {
                    setActiveCategory(null);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setActiveCategory(activeCategory === tag._id ? null : tag._id);
                  } else if (e.key === 'Escape') {
                    setActiveCategory(null);
                  } else if (e.key === 'Enter' && activeCategory === tag._id) {
                    trackBackendFilterClick('category_tag', tag.name);
                    router.push(`${getBasePath()}?categoryTag=${encodeURIComponent(tag.name)}`);
                  }
                }}
                onClick={() => {
                  trackBackendFilterClick('category_tag', tag.name);
                  router.push(`${getBasePath()}?categoryTag=${encodeURIComponent(tag.name)}`);
                }}
              >
                <span
                  style={{
                    borderBottomColor: activeCategory === tag._id ? theme.primary : 'transparent',
                  }}
                >
                  {tag.name.toUpperCase()}
                </span>

                {activeCategory === tag._id && (
                  <div className={styles.megaMenu} style={{ borderTopColor: theme.primary }} role="menu">
                    <div className={styles.megaMenuContent}>
                      {getCategoriesForTag(tag.name).map((cat: Category) => (
                        <div key={cat._id} className={styles.megaMenuCol}>
                          <h4
                            style={{ color: theme.primary }}
                            tabIndex={0}
                            role="menuitem"
                            onClick={(e) => {
                              e.stopPropagation();
                              trackBackendFilterClick('category', cat.name);
                              router.push(
                                `/categories/${encodeURIComponent(cat.slug || cat.name)}`
                              );
                              setActiveCategory(null);
                            }}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                e.stopPropagation();
                                trackBackendFilterClick('category', cat.name);
                                router.push(`/categories/${encodeURIComponent(cat.slug || cat.name)}`);
                                setActiveCategory(null);
                              }
                            }}
                          >
                            {cat.name}
                          </h4>
                          <ul>
                            {cat.subCategories && cat.subCategories.length > 0 ? (
                              cat.subCategories.map((sub: string) => (
                                <li
                                  key={sub}
                                  tabIndex={0}
                                  role="menuitem"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    trackBackendFilterClick('subcategory', sub);
                                    router.push(
                                      `/categories/${encodeURIComponent(cat.slug || cat.name)}?subCategory=${encodeURIComponent(sub)}`
                                    );
                                    setActiveCategory(null);
                                  }}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                      e.preventDefault();
                                      e.stopPropagation();
                                      trackBackendFilterClick('subcategory', sub);
                                      router.push(`/categories/${encodeURIComponent(cat.slug || cat.name)}?subCategory=${encodeURIComponent(sub)}`);
                                      setActiveCategory(null);
                                    }
                                  }}
                                >
                                  {sub}
                                </li>
                              ))
                            ) : (
                              <li
                                style={{ color: '#94969f', fontStyle: 'italic', fontSize: '11px' }}
                                tabIndex={0}
                                role="menuitem"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  trackBackendFilterClick('category', cat.name);
                                  router.push(
                                    `/categories/${encodeURIComponent(cat.slug || cat.name)}`
                                  );
                                  setActiveCategory(null);
                                }}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    trackBackendFilterClick('category', cat.name);
                                    router.push(`/categories/${encodeURIComponent(cat.slug || cat.name)}`);
                                    setActiveCategory(null);
                                  }
                                }}
                              >
                                All {cat.name}
                              </li>
                            )}
                          </ul>
                        </div>
                      ))}
                      {getCategoriesForTag(tag.name).length === 0 && (
                        <div className={styles.megaMenuCol}>
                          <h4 style={{ color: '#94969f', fontStyle: 'italic' }}>
                            No categories available
                          </h4>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}


            {/* More dropdown for overflow tags */}
            {overflowTags.length > 0 && (
              <div
                className={styles.navItem}
                ref={moreRef}
                onMouseEnter={() => setShowMoreTags(true)}
                onMouseLeave={() => setShowMoreTags(false)}
              >
                <span style={{ borderBottomColor: showMoreTags ? theme.primary : 'transparent' }}>
                  MORE ▾
                </span>
                {showMoreTags && (
                  <div
                    className={styles.megaMenu}
                    style={{ borderTopColor: theme.primary, minWidth: '200px' }}
                  >
                    <div className={styles.megaMenuContent} style={{ padding: '16px' }}>
                      <div className={styles.megaMenuCol}>
                        <h4 style={{ color: theme.primary }}>More Tags</h4>
                        <ul>
                          {overflowTags.map((tag: CategoryTag) => (
                            <li
                              key={tag._id}
                              onClick={() => {
                                trackBackendFilterClick('category_tag', tag.name);
                                router.push(
                                  `${getBasePath()}?categoryTag=${encodeURIComponent(tag.name)}`
                                );
                              }}
                            >
                              {tag.name}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </nav>

          {/* Search Bar */}
          <div className={styles.headerSearch}>
            <form className={styles.searchForm} onSubmit={handleSearch}>
              <div className={styles.searchIconWrapper}>
                {isSearching ? (
                  <svg
                    className={`${styles.searchIcon} animate-spin`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
                  </svg>
                ) : (
                  <svg
                    className={styles.searchIcon}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                )}
              </div>
              {/* Category scope chip — shown when user is browsing a department */}
              {activeCategoryTag && (
                <span
                  style={{ backgroundColor: `${theme.primary}15`, color: theme.primary, borderColor: `${theme.primary}40` }}
                  className="flex shrink-0 items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-semibold whitespace-nowrap"
                >
                  in {activeCategoryTag}
                  <button
                    type="button"
                    aria-label={`Remove ${activeCategoryTag} scope`}
                    onClick={() => router.push(getBasePath())}
                    className="ml-0.5 opacity-60 hover:opacity-100 transition-opacity"
                  >
                    ×
                  </button>
                </span>
              )}
              <input
                type="text"
                id="header-search-input"
                placeholder={activeCategoryTag ? `Search in ${activeCategoryTag}...` : 'Search for products, brands and more'}
                value={searchQuery}
                aria-label={activeCategoryTag ? `Search in ${activeCategoryTag}` : 'Search for products, brands and more'}
                aria-autocomplete="list"
                aria-expanded={showSuggestions}
                role="combobox"
                aria-controls="search-suggestions-list"
                onFocus={() => {
                  setShowSuggestions(true);
                  fetchSuggestions();
                }}
                onBlur={handleSearchBlur}
                onChange={(e) => setSearchQuery(e.target.value)}
              />

              {showSuggestions && (
                <div
                  id="search-suggestions-list"
                  role="listbox"
                  aria-label="Search suggestions"
                  className="absolute left-0 top-full z-[2000] mt-2 w-full animate-slide-up overflow-hidden rounded-xl border border-gray-100 bg-white shadow-2xl"
                >
                  {loadingSuggestions ? (
                    <div className="flex items-center gap-3 p-4 text-sm text-gray-400">
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
                      </svg>
                      Loading suggestions…
                    </div>
                  ) : (recentProducts.length > 0 || recentSearches.length > 0 || popularTerms.length > 0) ? (
                    <>
                      {/* Recently Browsed Products — shown when no query is typed yet */}
                      {recentProducts.length > 0 && !searchQuery && (
                        <div className="border-b border-gray-50 p-4">
                          <h4 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                            Recently Browsed
                          </h4>
                          <div className="grid grid-cols-4 gap-2">
                            {recentProducts.map((product) => (
                              <button
                                key={product.productId}
                                onClick={() => {
                                  setShowSuggestions(false);
                                  router.push(`${getBasePath()}/product/${product.productId}`);
                                }}
                                className="group flex flex-col items-center gap-1.5 rounded-lg p-2 text-center transition-colors hover:bg-gray-50"
                              >
                                <div className="h-14 w-14 overflow-hidden rounded-lg bg-gray-100">
                                  {product.displayImage ? (
                                    <img
                                      src={getImageUrlWithFallback(product.displayImage)}
                                      alt={product.productName}
                                      className="h-full w-full object-contain"
                                    />
                                  ) : (
                                    <div className="flex h-full w-full items-center justify-center">
                                      <svg className="h-6 w-6 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10" />
                                      </svg>
                                    </div>
                                  )}
                                </div>
                                <span className="line-clamp-2 text-[10px] leading-tight text-gray-600 group-hover:text-gray-900">
                                  {product.productName}
                                </span>
                                {product.price && (
                                  <span className="text-[10px] font-semibold" style={{ color: theme.primary }}>
                                    ₹{product.price.toLocaleString()}
                                  </span>
                                )}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* Autocomplete: match recently browsed product names against typed query */}
                      {/* Live autocomplete — server-side product/brand/category suggestions as user types */}
                      {searchQuery.trim().length >= 2 && (
                        <div className="border-b border-gray-50">
                          {loadingAutocomplete ? (
                            <div className="flex items-center gap-2 px-4 py-3 text-xs text-gray-400">
                              <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
                              </svg>
                              Searching…
                            </div>
                          ) : (liveAutocomplete.products.length > 0 || liveAutocomplete.brands.length > 0 || liveAutocomplete.categories.length > 0) ? (
                            <div className="p-2">
                              {/* Product name matches */}
                              {liveAutocomplete.products.map((p) => (
                                <button
                                  key={p.productId}
                                  onClick={() => {
                                    setShowSuggestions(false);
                                    router.push(`${getBasePath()}/product/${p.productId}`);
                                  }}
                                  className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors hover:bg-gray-50"
                                >
                                  <svg className="h-4 w-4 shrink-0 text-gray-300 group-hover:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                                  </svg>
                                  <span className="text-sm text-gray-700 group-hover:text-gray-900">{p.name}</span>
                                </button>
                              ))}
                              {/* Brand matches */}
                              {liveAutocomplete.brands.map((brand) => (
                                <button
                                  key={brand}
                                  onClick={() => {
                                    setShowSuggestions(false);
                                    router.push(`/brands/${encodeURIComponent(brand)}`);
                                  }}
                                  className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors hover:bg-gray-50"
                                >
                                  <svg className="h-4 w-4 shrink-0 text-blue-300 group-hover:text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                                  </svg>
                                  <span className="text-sm text-gray-700 group-hover:text-gray-900">{brand} <span className="text-xs text-gray-400">Brand</span></span>
                                </button>
                              ))}
                              {/* Category matches */}
                              {liveAutocomplete.categories.map((cat) => (
                                <button
                                  key={cat}
                                  onClick={() => {
                                    setShowSuggestions(false);
                                    router.push(`/categories/${encodeURIComponent(cat)}`);
                                  }}
                                  className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors hover:bg-gray-50"
                                >
                                  <svg className="h-4 w-4 shrink-0 text-green-300 group-hover:text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                                  </svg>
                                  <span className="text-sm text-gray-700 group-hover:text-gray-900">{cat} <span className="text-xs text-gray-400">Category</span></span>
                                </button>
                              ))}
                            </div>
                          ) : (
                            /* Fallback: client-side match against recently browsed products */
                            (() => {
                              const q = searchQuery.toLowerCase();
                              const matches = recentProducts.filter(p => p.productName.toLowerCase().includes(q));
                              if (!matches.length) return null;
                              return (
                                <div className="p-4">
                                  <h4 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-gray-400">Recently Browsed</h4>
                                  <div className="space-y-1">
                                    {matches.map((product) => (
                                      <button
                                        key={product.productId}
                                        onClick={() => { setShowSuggestions(false); router.push(`${getBasePath()}/product/${product.productId}`); }}
                                        className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors hover:bg-gray-50"
                                      >
                                        <div className="h-8 w-8 shrink-0 overflow-hidden rounded bg-gray-100">
                                          {product.displayImage && <img src={getImageUrlWithFallback(product.displayImage)} alt={product.productName} className="h-full w-full object-contain" />}
                                        </div>
                                        <span className="text-sm text-gray-700 group-hover:text-gray-900">{product.productName}</span>
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              );
                            })()
                          )}
                        </div>
                      )}
                      {recentSearches.length > 0 && (
                        <div className="border-b border-gray-50 p-4">
                          <h4 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                            Recent Searches
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {recentSearches.map((term) => (
                              <button
                                key={term}
                                onClick={() => handleSuggestionClick(term)}
                                className="rounded-full bg-gray-50 px-3 py-1.5 text-xs text-gray-600 transition-colors hover:bg-gray-100"
                              >
                                {term}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      {popularTerms.length > 0 && (
                        <div className="p-4">
                          <h4 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                            Popular Now
                          </h4>
                          <div className="space-y-1">
                            {popularTerms.map((term) => (
                              <button
                                key={term}
                                onClick={() => handleSuggestionClick(term)}
                                className="group flex w-full items-center rounded-lg px-3 py-2 text-left text-sm text-gray-700 transition-colors hover:bg-[#1a4d33]/5"
                              >
                                <svg
                                  className="mr-3 h-4 w-4 text-gray-300 group-hover:text-[#1a4d33]"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                                  />
                                </svg>
                                {term}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : null}
                </div>
              )}
            </form>
          </div>
          <div className={styles.actions}>
            {/* Profile */}
            <div className={styles.actionItem} ref={profileRef}>
              <button
                onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                aria-label={user ? `Profile menu for ${user.name?.split(' ')[0] || 'User'}` : 'Profile menu'}
                aria-expanded={showProfileDropdown}
                aria-haspopup="true"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path
                    d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    fill="none"
                  />
                  <circle
                    cx="12"
                    cy="7"
                    r="4"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    fill="none"
                  />
                </svg>
                <span>Profile</span>
              </button>

              {showProfileDropdown && (
                <div className={styles.dropdown}>
                  {user ? (
                    <>
                      <div className={styles.dropdownHeader}>
                        <strong>Hello, {user.name?.split(' ')[0] || 'User'}</strong>
                        <span>{user.email}</span>
                      </div>
                      <div className={styles.dropdownItems}>
                        <button
                          onClick={() => {
                            router.push(`${getBasePath()}/profile`);
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                          >
                            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                          </svg>
                          <span>My Profile</span>
                        </button>
                        <button
                          onClick={() => {
                            router.push(
                              user.role === 'valet' ? getBasePath() : `${getBasePath()}/orders`
                            );
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                          >
                            <rect x="2" y="4" width="20" height="16" rx="2" />
                            <path d="M7 8h10M7 12h6" />
                          </svg>
                          <span>{user.role === 'valet' ? 'Dashboard' : 'My Orders'}</span>
                        </button>
                        <button
                          onClick={() => {
                            setShowProfileDropdown(false);
                            setShowNotificationsModal(true);
                          }}
                        >
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                          </svg>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            Notifications
                            {unreadNotifCount > 0 && (
                              <span style={{
                                background: '#EF4444',
                                color: 'white',
                                borderRadius: '9999px',
                                fontSize: '10px',
                                fontWeight: 700,
                                padding: '1px 6px',
                                minWidth: '18px',
                                textAlign: 'center',
                                lineHeight: '16px',
                              }}>
                                {unreadNotifCount > 99 ? '99+' : unreadNotifCount}
                              </span>
                            )}
                          </span>
                        </button>
                        {(user.role === 'wholesaler' || user.effectiveRole === 'wholesaler') && (
                          <button
                            onClick={() => {
                              router.push(`${getBasePath()}/schemes`);
                              setShowProfileDropdown(false);
                            }}
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                            >
                              <path d="M12 2v20m-7-7h14M4 12h16M7 5l10 14" />
                            </svg>
                            <span>Schemes</span>
                          </button>
                        )}
                        <button
                          onClick={() => {
                            router.push(`${getBasePath()}/wishlist`);
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                          >
                            <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" />
                          </svg>
                          <span>Wishlist</span>
                        </button>
                        <button
                          onClick={() => {
                            router.push('/support');
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                          >
                            <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
                          </svg>
                          <span>Support</span>
                        </button>
                        <button
                          onClick={() => {
                            router.push('/faq');
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <circle cx="12" cy="12" r="10" />
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                            <line x1="12" y1="17" x2="12.01" y2="17" />
                          </svg>
                          <span>FAQ</span>
                        </button>
                        <button
                          onClick={() => {
                            router.push('/about');
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="16" x2="12" y2="12" />
                            <line x1="12" y1="8" x2="12.01" y2="8" />
                          </svg>
                          <span>About Us</span>
                        </button>
                        <button
                          onClick={() => {
                            router.push('/privacy-policy');
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                          </svg>
                          <span>Privacy Policy</span>
                        </button>
                        <button
                          onClick={() => {
                            setShowFeedbackModal(true);
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                          >
                            <path d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                          </svg>
                          <span>Give Feedback</span>
                        </button>
                        {user.role === 'super_admin' && (
                          <button
                            onClick={() => {
                              router.push('/admin');
                              setShowProfileDropdown(false);
                            }}
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                            >
                              <circle cx="12" cy="12" r="3" />
                              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
                            </svg>
                            <span>Admin Panel</span>
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setShowAccessibilityModal(true);
                            setShowProfileDropdown(false);
                          }}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                          >
                            <circle cx="12" cy="12" r="10" />
                            <path d="M12 8v4M12 16h.01" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          <span>Accessibility</span>
                        </button>
                        <button
                          onClick={() => {
                            logout();
                            router.push('/');
                            setShowProfileDropdown(false);
                          }}
                          className={styles.logoutBtn}
                        >
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            aria-hidden="true"
                            focusable="false"
                          >
                            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
                          </svg>
                          <span>Logout</span>
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className={styles.dropdownItems}>
                      <p
                        style={{
                          padding: '12px 20px',
                          fontSize: '13px',
                          color: '#94969f',
                          margin: 0,
                        }}
                      >
                        Welcome to Stationery Junction
                      </p>
                      <button
                        onClick={() => {
                          setAuthModalMode('login');
                          setShowAuthModal(true);
                          setShowProfileDropdown(false);
                        }}
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        >
                          <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M15 12H3" />
                        </svg>
                        <span>Sign In</span>
                      </button>
                      <button
                        onClick={() => {
                          setAuthModalMode('register');
                          setShowAuthModal(true);
                          setShowProfileDropdown(false);
                        }}
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        >
                          <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                          <circle cx="8.5" cy="7" r="4" />
                          <line x1="20" y1="8" x2="20" y2="14" />
                          <line x1="23" y1="11" x2="17" y2="11" />
                        </svg>
                        <span>Create Account</span>
                      </button>
                      <button
                        onClick={() => {
                          router.push('/customer/wishlist');
                          setShowProfileDropdown(false);
                        }}
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        >
                          <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" />
                        </svg>
                        <span>Wishlist</span>
                      </button>
                      <button
                        onClick={() => {
                          router.push('/support');
                          setShowProfileDropdown(false);
                        }}
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          aria-hidden="true"
                          focusable="false"
                        >
                          <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
                        </svg>
                        <span>Support</span>
                      </button>
                      <button
                        onClick={() => {
                          router.push('/faq');
                          setShowProfileDropdown(false);
                        }}
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                          <line x1="12" y1="17" x2="12.01" y2="17" />
                        </svg>
                        <span>FAQ</span>
                      </button>
                      <button
                        onClick={() => {
                          router.push('/about');
                          setShowProfileDropdown(false);
                        }}
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="16" x2="12" y2="12" />
                          <line x1="12" y1="8" x2="12.01" y2="8" />
                        </svg>
                        <span>About Us</span>
                      </button>
                      <button
                        onClick={() => {
                          router.push('/privacy-policy');
                          setShowProfileDropdown(false);
                        }}
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                        </svg>
                        <span>Privacy Policy</span>
                      </button>
                      <button
                        onClick={() => {
                          setShowAccessibilityModal(true);
                          setShowProfileDropdown(false);
                        }}
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <path d="M12 8v4M12 16h.01" />
                        </svg>
                        <span>Accessibility</span>
                      </button>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Cart */}
            <div
              className={styles.actionItem}
              onClick={openCart}
              role="button"
              aria-label={`Shopping cart, ${cartCount} item${cartCount !== 1 ? 's' : ''}`}
            >
              <button aria-hidden="true" tabIndex={-1}>
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="9" cy="21" r="1"></circle>
                  <circle cx="20" cy="21" r="1"></circle>
                  <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                </svg>
                {cartCount > 0 && <span className={styles.badge}>{cartCount}</span>}
                <span>Cart</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Auth Modal for Login/Register */}
      {showAuthModal && (
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          initialMode={authModalMode}
        />
      )}
      <GeneralFeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
      />
      <CustomerNotificationsModal
        isOpen={showNotificationsModal}
        onClose={() => setShowNotificationsModal(false)}
        onUnreadCountChange={setUnreadNotifCount}
      />
      <AccessibilityModal
        isOpen={showAccessibilityModal}
        onClose={() => setShowAccessibilityModal(false)}
      />
    </header>
  );
}
