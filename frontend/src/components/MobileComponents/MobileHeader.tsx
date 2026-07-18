'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import api from '@/utils/api';
import Link from 'next/link';

interface CategoryTag {
  _id?: string;
  name?: string;
}

interface Category {
  _id?: string;
  name?: string;
  slug?: string;
  categoryTags?: string[];
  subCategories?: string[];
}

interface Brand {
  _id?: string;
  name?: string;
}

export default function MobileHeader() {
  const router = useRouter();
  const pathname = usePathname() || '';
  const { user } = useAuth();
  const { theme } = useTheme();

  const isCartPage = pathname.includes('/cart');
  const isWishlistPage = pathname.includes('/wishlist');
  const isProfilePage = pathname.includes('/profile');
  const isOrdersPage = pathname.includes('/orders');
  const isSupportPage = pathname.includes('/support');
  const isProductPage = pathname.includes('/product/');
  const isCategoryDetail = pathname.startsWith('/categories/') && pathname !== '/categories';
  const isBrandDetail = pathname.startsWith('/brands/') && pathname !== '/brands';

  const showBackButton = isCartPage || isWishlistPage || isProfilePage || isOrdersPage || isSupportPage || isProductPage || isCategoryDetail || isBrandDetail;

  let headerTitle = 'Stationery Junction';
  if (isCartPage) {
    headerTitle = 'Cart';
  } else if (isWishlistPage) {
    headerTitle = 'Wishlist';
  } else if (isProfilePage) {
    headerTitle = 'Profile';
  } else if (isOrdersPage) {
    headerTitle = 'My Orders';
  } else if (isSupportPage) {
    headerTitle = 'Support';
  } else if (isProductPage) {
    headerTitle = 'Product Details';
  } else if (isCategoryDetail) {
    headerTitle = 'Category';
  } else if (isBrandDetail) {
    headerTitle = 'Brand';
  }

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryTags, setCategoryTags] = useState<CategoryTag[]>([]);
  const [tagData, setTagData] = useState<
    Record<string, { categories: Category[]; brands: Brand[] }>
  >({});
  const [expandedTag, setExpandedTag] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    if (isMenuOpen && categoryTags.length === 0) {
      loadMenuData();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMenuOpen]);

  useEffect(() => {
    const fetchCartCount = async () => {
      if (!user) {
        const { getGuestCart } = await import('@/utils/guestStore');
        setCartCount(getGuestCart().length);
        return;
      }
      try {
        const res = await api.get('/cart');
        const items = res.data?.items || res.data || [];
        setCartCount(items.length);
      // eslint-disable-next-line unused-imports/no-unused-vars
      } catch (e) {
        // Silent fail
      }
    };
    fetchCartCount();
  }, [user]);

  const loadMenuData = async () => {
    setLoading(true);
    try {
      const tagsRes = await api.get('/category-tags/active');
      setCategoryTags((tagsRes.data || []).filter((t: any) => t.name));
    } catch (e) {
      console.error('Failed to load menu data', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchTagDetailData = async (tagName: string) => {
    if (tagData[tagName]) return;
    try {
      const [catsRes, brandsRes] = await Promise.all([
        api.get(`/categories/public/tags/${encodeURIComponent(tagName)}/categories`),
        api.get(`/categories/public/tags/${encodeURIComponent(tagName)}/brands`),
      ]);
      setTagData((prev) => ({
        ...prev,
        [tagName]: {
          categories: catsRes.data || [],
          brands: brandsRes.data || [],
        },
      }));
    } catch (error) {
      console.error(`Error fetching data for tag ${tagName}:`, error);
    }
  };

  const getCategoriesForTag = (tagName: string) => {
    return tagData[tagName]?.categories || [];
  };

  const toggleTag = (tagName: string) => {
    if (expandedTag === tagName) {
      setExpandedTag(null);
    } else {
      setExpandedTag(tagName);
      fetchTagDetailData(tagName);
    }
  };

  const getHomePath = () => {
    if (!user) return '/';
    if (user.role === 'customer') return '/customer';
    if (user.role === 'wholesaler') return '/wholesaler';
    return '/';
  };

  const getUserBasePath = () => {
    if (!user) return '/customer';
    if (user.role === 'customer') return '/customer';
    if (user.role === 'wholesaler') return '/wholesaler';
    return '/customer';
  };

  const navigateToCategory = (category: Category, subCategory?: string) => {
    const slug = category.slug || category.name || '';
    const query = subCategory ? `?subCategory=${encodeURIComponent(subCategory)}` : '';
    router.push(`/categories/${encodeURIComponent(slug)}${query}`);
    setIsMenuOpen(false);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`${getUserBasePath()}?searchTerm=${encodeURIComponent(searchQuery.trim())}`);
      setShowSearch(false);
      setSearchQuery('');
    }
  };

  // Smart back navigation — falls back to a sensible route if there is no browser history
  const getBackFallback = () => {
    if (isOrdersPage) return `${getUserBasePath()}/profile`;
    if (isCategoryDetail) return '/categories';
    if (isBrandDetail) return '/brands';
    return getHomePath();
  };

  const handleGoBack = () => {
    if (typeof window !== 'undefined' && window.history.length > 1) {
      router.back();
    } else {
      router.push(getBackFallback());
    }
  };

  return (
    <>
      {/* Main Header */}
      <header
        className="sticky top-0 z-50 border-b border-gray-100 bg-white md:hidden"
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        <div className="flex h-14 items-center justify-between px-4">
          {/* Left / Center: Hamburger & Logo OR Back Button & Title */}
          {showBackButton ? (
            <div className="flex items-center gap-3">
              <button
                onClick={handleGoBack}
                className="-ml-2 flex h-10 w-10 items-center justify-center rounded-full transition-colors active:bg-gray-100"
                style={{ color: theme.primary }}
                aria-label="Go back"
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
              </button>
              <span
                className="text-base font-bold tracking-tight text-neutral-900"
                suppressHydrationWarning={true}
              >
                {headerTitle}
              </span>
            </div>
          ) : (
            <>
              {/* Left: Hamburger Menu */}
              <button
                onClick={() => setIsMenuOpen(true)}
                className="-ml-2 flex h-10 w-10 items-center justify-center rounded-full transition-colors active:bg-gray-100"
                style={{ color: theme.primary }}
                aria-label="Open menu"
                suppressHydrationWarning={true}
              >
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="3" y1="12" x2="21" y2="12"></line>
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
              </button>

              {/* Center: Logo - match app green on mobile */}
              <button
                onClick={() => router.push(getHomePath())}
                className="font-serif text-base font-bold tracking-tight transition-opacity active:opacity-70 md:text-lg"
                style={{ color: theme.primary }}
                suppressHydrationWarning={true}
              >
                Stationery Junction
              </button>
            </>
          )}

          {/* Right: Search & Cart / Wishlist */}
          <div className="flex items-center">
            {isCartPage ? (
              user && (
                <Link
                  href={`${getUserBasePath()}/wishlist`}
                  className="mr-1 flex items-center gap-1 text-xs font-bold uppercase tracking-wider"
                  style={{ color: theme.primary }}
                >
                  <span>❤️</span>
                  <span>Wishlist</span>
                </Link>
              )
            ) : (
              <>
                <button
                  onClick={() => setShowSearch(!showSearch)}
                  className="flex h-10 w-10 items-center justify-center rounded-full text-gray-600 transition-colors active:bg-gray-100"
                  aria-label="Search"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  </svg>
                </button>
                <button
                  onClick={() => router.push(`${getUserBasePath()}/cart`)}
                  className="relative -mr-2 flex h-10 w-10 items-center justify-center rounded-full text-gray-600 transition-colors active:bg-gray-100"
                  aria-label="Cart"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"></path>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <path d="M16 10a4 4 0 0 1-8 0"></path>
                  </svg>
                  {cartCount > 0 && (
                    <span className="absolute right-1 top-1 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
                      {cartCount}
                    </span>
                  )}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Search Bar - Expandable */}
        {showSearch && (
          <div className="animate-in slide-in-from-top-2 px-4 pb-3 duration-200">
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search products..."
                autoFocus
                className="h-10 w-full rounded-full bg-gray-100 pl-10 pr-4 text-sm transition-all focus:bg-white focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
              <svg
                className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 flex h-5 w-5 -translate-y-1/2 items-center justify-center text-gray-400"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              )}
            </form>
          </div>
        )}
      </header>

      {/* Side Drawer Menu */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-[100] md:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setIsMenuOpen(false)}
            style={{ animation: 'fadeIn 0.2s ease-out' }}
          />

          {/* Drawer - match app: white, "Browse" title, green accents */}
          <div
            className="absolute bottom-0 left-0 top-0 flex w-[85%] max-w-[320px] flex-col bg-white shadow-2xl"
            style={{ animation: 'slideInLeft 0.25s ease-out' }}
          >
            {/* Drawer Header - Browse + Close (match app) */}
            <div
              className="flex items-center justify-between border-b border-gray-100 px-5 py-4"
              style={{ paddingTop: 'calc(env(safe-area-inset-top) + 16px)' }}
            >
              <span className="font-serif text-xl font-bold" style={{ color: theme.primary }}>
                Browse
              </span>
              <button
                onClick={() => setIsMenuOpen(false)}
                className="flex h-10 w-10 items-center justify-center rounded-full transition-colors active:bg-gray-100"
                style={{ color: theme.primary }}
                aria-label="Close menu"
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            {/* Menu Content - Category tags (match app) */}
            <div className="flex-1 overflow-y-auto">
              <div className="px-5 py-4">
                {loading ? (
                  <div className="flex justify-center py-8">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900"></div>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {categoryTags.map((tag) => (
                      <div key={tag._id}>
                        <button
                          onClick={() => toggleTag(tag.name!)}
                          className="flex w-full items-center justify-between rounded-lg py-3 text-left transition-colors active:bg-gray-50"
                        >
                          <span
                            className={`text-lg font-bold transition-colors ${expandedTag === tag.name ? '' : ''}`}
                            style={{ color: theme.primary }}
                          >
                            {tag.name}
                          </span>
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className={`text-gray-400 transition-transform duration-200 ${expandedTag === tag.name ? 'rotate-180' : ''}`}
                          >
                            <polyline points="6 9 12 15 18 9"></polyline>
                          </svg>
                        </button>

                        {expandedTag === tag.name && (
                          <div
                            className="space-y-2 pb-2 pl-3"
                            style={{ animation: 'fadeIn 0.2s ease-out' }}
                          >
                            {getCategoriesForTag(tag.name || '').map((cat) => (
                              <div key={cat._id}>
                                <button
                                  onClick={() => navigateToCategory(cat)}
                                  className="w-full py-3 text-left text-sm font-bold transition-colors"
                                  style={{ color: theme.primary }}
                                >
                                  {cat.name}
                                </button>
                                {cat.subCategories && cat.subCategories.length > 0 && (
                                  <div className="ml-1 space-y-1 border-l-2 border-gray-100 pl-3">
                                    {cat.subCategories.map((sub) => (
                                      <button
                                        key={sub}
                                        onClick={() => navigateToCategory(cat, sub)}
                                        className="w-full py-2 text-left text-xs text-gray-500 transition-colors active:opacity-80"
                                      >
                                        {sub}
                                      </button>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                            {getCategoriesForTag(tag.name || '').length === 0 &&
                              !tagData[tag.name!] && (
                                <div className="py-2 text-xs text-gray-400">Loading...</div>
                              )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Drawer Footer - match app green CTA */}
            <div
              className="border-t border-gray-100 bg-gray-50 p-4"
              style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 16px)' }}
            >
              {user ? (
                <button
                  onClick={() => {
                    setIsMenuOpen(false);
                    router.push(`${getUserBasePath()}/profile`);
                  }}
                  className="mb-2 flex w-full items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium text-white transition-opacity active:opacity-90"
                  style={{ backgroundColor: theme.primary }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                  My Account
                </button>
              ) : (
                <button
                  onClick={() => {
                    setIsMenuOpen(false);
                    router.push('/login');
                  }}
                  className="mb-2 w-full py-2.5 text-sm font-semibold underline"
                  style={{ color: theme.primary }}
                >
                  Sign in / Register
                </button>
              )}
              <p className="text-center text-[10px] font-medium text-gray-400">
                v{process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* CSS Animations */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        @keyframes slideInLeft {
          from {
            transform: translateX(-100%);
          }
          to {
            transform: translateX(0);
          }
        }
      `}</style>
    </>
  );
}
