'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { useWishlist } from '@/context/WishlistContext';
import { useCart } from '@/context/CartContext';
import AuthModal from './AuthModal';
import GeneralFeedbackModal from './GeneralFeedbackModal';
import api from '@/utils/api';
import Link from 'next/link';
import styles from './Header.module.css';
import { trackBackendFilterClick } from '@/utils/analytics';
import AccessibilityPanel from './AccessibilityPanel';

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

export default function Header() {
  const { user, logout } = useAuth();
  const { theme } = useTheme();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const { items: wishlistItems } = useWishlist();
  const { cart, openCart } = useCart();
  const router = useRouter();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const pathname = usePathname();

  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
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
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [popularTerms, setPopularTerms] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const moreRef = useRef<HTMLDivElement>(null);

  // Fetch category tags, brands, categories, and promo strips
  useEffect(() => {
    fetchCategoryTags();
    fetchBrands();
    fetchCategories();
    fetchPromoStrips();
  }, []);

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
      const [recentRes, suggestionsRes] = await Promise.all([
        api.get('/tracking/recent', { params: { sessionId, limit: 5 } }),
        api.get('/tracking/suggestions', { params: { limit: 8 } }),
      ]);
      setRecentSearches(recentRes.data || []);
      setPopularTerms(suggestionsRes.data?.popularTerms || []);
    } catch (e) {
      console.error('Failed to fetch suggestions', e);
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
      console.error('Error fetching category tags:', error);
    }
  };

  const fetchBrands = async () => {
    try {
      const response = await api.get('/brands/public');
      const brandList = response.data?.brands || response.data || [];
      setBrands(brandList.filter((b: Brand) => b.name));
    } catch (error) {
      console.error('Error fetching brands:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories/public');
      const cats = response.data?.categories || response.data || [];
      setCategories(cats.filter((c: Category) => c.name));
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  // Get categories for a specific tag
  const getCategoriesForTag = (tagName: string): Category[] => {
    const targetTag = tagName.toLowerCase();
    return categories.filter((c) => {
      const tag = c.categoryTag || (c.categoryTags && c.categoryTags[0]) || (c.tags && c.tags[0]);
      return (tag || "").toLowerCase() === targetTag;
    });
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
      router.push(`${getBasePath()}?searchTerm=${encodeURIComponent(searchQuery.trim())}`);
      // Assuming Next.js router.push resolves or completes, we should reset.
      // But Next.js app router doesn't return a promise on push.
      // Resetting after a short delay or letting the new page mount is typical.
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
  const visibleTags = categoryTags.slice(0, maxVisibleTags);
  const overflowTags = categoryTags.slice(maxVisibleTags);

  return (
    <header className={`${styles.header} hidden md:block`}>
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
          <Link
            href={getBasePath() === '/customer' ? '/customer?reset=true' : getBasePath()}
            className={styles.logo}
          >
            <span style={{ color: theme.primary }}>Stationery Junction</span>
          </Link>

          {/* Navigation - Category Tags from Super Admin */}
          <nav className={styles.nav} ref={navRef} aria-label="Main navigation">
            {visibleTags.map((tag: CategoryTag) => (
              <div
                key={tag._id}
                className={`${styles.navItem} ${activeCategory === tag._id ? styles.active : ''}`}
                onMouseEnter={() => {
                  setActiveCategory(tag._id);
                }}
                onMouseLeave={() => setActiveCategory(null)}
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
                  <div className={styles.megaMenu} style={{ borderTopColor: theme.primary }}>
                    <div className={styles.megaMenuContent}>
                      {getCategoriesForTag(tag.name).map((cat: Category) => (
                        <div key={cat._id} className={styles.megaMenuCol}>
                          <h4
                            style={{ color: theme.primary }}
                            onClick={(e) => {
                              e.stopPropagation();
                              trackBackendFilterClick('category', cat.name);
                              router.push(
                                `/categories/${encodeURIComponent(cat.slug || cat.name)}`
                              );
                              setActiveCategory(null);
                            }}
                          >
                            {cat.name}
                          </h4>
                          <ul>
                            {cat.subCategories && cat.subCategories.length > 0 ? (
                              cat.subCategories.map((sub: string) => (
                                <li
                                  key={sub}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    trackBackendFilterClick('subcategory', sub);
                                    router.push(
                                      `/categories/${encodeURIComponent(cat.slug || cat.name)}?subCategory=${encodeURIComponent(sub)}`
                                    );
                                    setActiveCategory(null);
                                  }}
                                >
                                  {sub}
                                </li>
                              ))
                            ) : (
                              <li
                                style={{ color: '#94969f', fontStyle: 'italic', fontSize: '11px' }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  trackBackendFilterClick('category', cat.name);
                                  router.push(
                                    `/categories/${encodeURIComponent(cat.slug || cat.name)}`
                                  );
                                  setActiveCategory(null);
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
              <input
                type="text"
                id="header-search-input"
                placeholder="Search for products, brands and more"
                value={searchQuery}
                aria-label="Search for products, brands and more"
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
                  ) : (recentSearches.length > 0 || popularTerms.length > 0) ? (
                    <>
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
                      <AccessibilityPanel />
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
                        className="flex items-center gap-3 px-5 py-2.5 text-left text-sm text-gray-700 hover:bg-[#1a4d33]/5 w-full"
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
                        className="flex items-center gap-3 px-5 py-2.5 text-left text-sm text-gray-700 hover:bg-[#1a4d33]/5 w-full"
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
                        className="flex items-center gap-3 px-5 py-2.5 text-left text-sm text-gray-700 hover:bg-[#1a4d33]/5 w-full"
                      >
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        >
                          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                        </svg>
                        <span>Privacy Policy</span>
                      </button>
                      </div>
                      <AccessibilityPanel />
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
    </header>
  );
}
