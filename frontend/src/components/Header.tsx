'use client';

import React, { useState, useRef, useEffect, Suspense } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
// import { useWishlist } from '@/context/WishlistContext';
// import { useCart } from '@/context/CartContext';
import { useWishlistStore } from '@/store/wishlistStore';
import { useCartStore } from '@/store/cartStore';
import { usePincode } from '@/context/PincodeContext';
import AuthModal from './AuthModal';
import GeneralFeedbackModal from './GeneralFeedbackModal';
import api from '@/utils/api';
import Link from 'next/link';
import Image from 'next/image';
import styles from './Header.module.css';
import { trackBackendFilterClick } from '@/utils/analytics';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import CustomerNotificationsModal from './CustomerNotificationsModal';
import AccessibilityModal from './AccessibilityModal';
import { logger } from '@/utils/logger';

interface CategoryTag {
  id: string;
  name: string;
}

interface Category {
  id: string;
  name: string;
  slug?: string;
  categoryTag?: string;
  categoryTags?: string[];
  tags?: string[];
  subCategories?: string[];
}

interface Brand {
  id: string;
  name: string;
  slug?: string;
  categories?: string[];
}

interface PromoStrip {
  id: string;
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
  // const { items: wishlistItems } = useWishlist();
  // const { cart, openCart } = useCart();
  const wishlistItems = useWishlistStore((s) => s.items);
  const cart          = useCartStore((s) => s.cart);
  const openCart      = useCartStore((s) => s.openCart);
  const {
    pincode,
    city,
    openPincodeModal,
    availableModes,
    activeMode,
    setActiveMode,
    checkAndSetPincode,
  } = usePincode();
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
  const [showLocationDropdown, setShowLocationDropdown] = useState(false);
  const [pincodeInput, setPincodeInput] = useState('');
  const [pincodeError, setPincodeError] = useState<string | null>(null);
  const [isApplyingPincode, setIsApplyingPincode] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [popularTerms, setPopularTerms] = useState<string[]>([]);
  const [popularCategories, setPopularCategories] = useState<string[]>([]);
  const [popularBrands, setPopularBrands] = useState<string[]>([]);
  const [isVoiceListening, setIsVoiceListening] = useState(false);
  const [isScanningImage, setIsScanningImage] = useState(false);
  const headerFileInputRef = useRef<HTMLInputElement | null>(null);
  const headerRecognitionRef = useRef<any>(null);

  useEffect(() => {
    (window as any).openAuthModal = (mode: 'login' | 'register') => {
      setAuthModalMode(mode);
      setShowAuthModal(true);
    };
  }, []);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [recentProducts, setRecentProducts] = useState<{ productId: string; productName: string; displayImage?: string; price?: number }[]>([]);
  // Live autocomplete results fetched from /products/suggest while user types
  const [liveAutocomplete, setLiveAutocomplete] = useState<{ products: { productId: string; name: string }[]; brands: string[]; categories: string[] }>({ products: [], brands: [], categories: [] });
  const [loadingAutocomplete, setLoadingAutocomplete] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const moreRef = useRef<HTMLDivElement>(null);
  const locationRef = useRef<HTMLDivElement>(null);

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
      if (locationRef.current && !locationRef.current.contains(event.target as Node)) {
        setShowLocationDropdown(false);
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
      setPopularCategories(suggestionsRes.data?.popularCategories || []);
      setPopularBrands(suggestionsRes.data?.popularBrands || []);
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
      const response = await api.get('/promo-strips/active');
      const activeStrips = response.data || [];
      setPromoStrips(activeStrips);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      setPromoStrips([]);
    }
  };



  const [isSearching, setIsSearching] = useState(false);

  const toggleHeaderVoiceSearch = () => {
    if (isVoiceListening) {
      if (headerRecognitionRef.current) {
        headerRecognitionRef.current.stop();
      }
      setIsVoiceListening(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;

      recognition.onstart = () => setIsVoiceListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setSearchQuery(transcript);
          const scopedTag = activeCategoryTag;
          const searchUrl = scopedTag
            ? `${getBasePath()}?searchTerm=${encodeURIComponent(transcript.trim())}&categoryTag=${encodeURIComponent(scopedTag)}`
            : `${getBasePath()}?searchTerm=${encodeURIComponent(transcript.trim())}`;
          router.push(searchUrl);
          setShowSuggestions(false);
        }
      };
      recognition.onerror = () => setIsVoiceListening(false);
      recognition.onend = () => setIsVoiceListening(false);

      headerRecognitionRef.current = recognition;
      recognition.start();
    } catch {
      setIsVoiceListening(false);
    }
  };

  const handleHeaderImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    setIsScanningImage(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await api.post('/visual-search/scan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const data = res.data;
      if (data?.searchQuery) {
        setSearchQuery(data.searchQuery);
        const scopedTag = activeCategoryTag;
        const searchUrl = scopedTag
          ? `${getBasePath()}?searchTerm=${encodeURIComponent(data.searchQuery.trim())}&categoryTag=${encodeURIComponent(scopedTag)}`
          : `${getBasePath()}?searchTerm=${encodeURIComponent(data.searchQuery.trim())}`;
        router.push(searchUrl);
        setShowSuggestions(false);
      }
    } catch (err) {
      logger.error('Header visual search failed', err);
    } finally {
      setIsScanningImage(false);
    }
  };

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

  const handleApplyPincode = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setPincodeError(null);
    const clean = pincodeInput.replace(/\D/g, '').slice(0, 6);
    if (clean.length !== 6) {
      setPincodeError('Enter a valid 6-digit PIN code');
      return;
    }
    setIsApplyingPincode(true);
    try {
      const role = (user as any)?.role || 'customer';
      const result = await checkAndSetPincode(clean, role);
      if (result.success && result.isServiceable) {
        setShowLocationDropdown(false);
        setPincodeInput('');
      } else {
        setPincodeError(result.message || `Pincode ${clean} is not serviceable yet`);
      }
    } catch {
      setPincodeError('Failed to verify pincode');
    } finally {
      setIsApplyingPincode(false);
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
    <>
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
              <div key={strip.id} className={styles.bannerSlide}>
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
          </div>

          {/* Navigation - Category Tags from Super Admin */}
          <nav className={styles.nav} ref={navRef} aria-label="Main navigation">
            {visibleTags.map((tag: CategoryTag) => (
              <div
                key={tag.id}
                className={`${styles.navItem} ${activeCategory === tag.id ? styles.active : ''}`}
                tabIndex={0}
                role="button"
                aria-expanded={activeCategory === tag.id}
                aria-haspopup="true"
                onMouseEnter={() => {
                  setActiveCategory(tag.id);
                }}
                onMouseLeave={() => setActiveCategory(null)}
                onFocus={() => setActiveCategory(tag.id)}
                onBlur={(e) => {
                  // Only close if focus leaves the entire nav item (including mega menu children)
                  if (!e.currentTarget.contains(e.relatedTarget as Node)) {
                    setActiveCategory(null);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setActiveCategory(activeCategory === tag.id ? null : tag.id);
                  } else if (e.key === 'Escape') {
                    setActiveCategory(null);
                  } else if (e.key === 'Enter' && activeCategory === tag.id) {
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
                    borderBottomColor: activeCategory === tag.id ? theme.primary : 'transparent',
                  }}
                >
                  {tag.name.toUpperCase()}
                </span>

                {activeCategory === tag.id && (
                  <div className={styles.megaMenu} style={{ borderTopColor: theme.primary }} role="menu">
                    <div className={styles.megaMenuContent}>
                      {getCategoriesForTag(tag.name).map((cat: Category) => (
                        <div key={cat.id} className={styles.megaMenuCol}>
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
                              key={tag.id}
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

              <div className="flex items-center gap-1 pr-2">
                {/* Visual Search / Camera Button */}
                <button
                  type="button"
                  onClick={() => headerFileInputRef.current?.click()}
                  disabled={isScanningImage}
                  title="Search with image (Visual Search / OCR)"
                  className="cursor-pointer rounded p-1 text-gray-400 hover:text-gray-700 transition-colors"
                  aria-label="Scan image to search"
                >
                  {isScanningImage ? (
                    <svg className="h-4 w-4 animate-spin text-red-600" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <circle cx="12" cy="13" r="4" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </button>

                {/* Voice Search / Mic Button */}
                <button
                  type="button"
                  onClick={toggleHeaderVoiceSearch}
                  title={isVoiceListening ? 'Stop listening' : 'Voice Search (Speech to Text)'}
                  className={`cursor-pointer rounded-full p-1 transition-colors ${
                    isVoiceListening ? 'bg-red-600 text-white animate-pulse' : 'text-gray-400 hover:text-gray-700'
                  }`}
                  aria-label="Voice Search"
                >
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill={isVoiceListening ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </button>
              </div>

              <input
                type="file"
                ref={headerFileInputRef}
                onChange={handleHeaderImageUpload}
                accept="image/*"
                capture="environment"
                className="hidden"
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
                  ) : (recentProducts.length > 0 || recentSearches.length > 0 || popularTerms.length > 0 || popularCategories.length > 0 || popularBrands.length > 0) ? (
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
                                    <Image
                                      src={getImageUrlWithFallback(product.displayImage)}
                                      alt={product.productName}
                                      width={56}
                                      height={56}
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
                                          {product.displayImage && <Image src={getImageUrlWithFallback(product.displayImage)} alt={product.productName} width={32} height={32} className="h-full w-full object-contain" />}
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
                      {recentSearches.length > 0 && !searchQuery && (
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
                      {popularTerms.length > 0 && !searchQuery && (
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
                      {popularCategories.length > 0 && !searchQuery && (
                        <div className="border-t border-gray-50 p-4">
                          <h4 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                            Popular Categories
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {popularCategories.map((cat) => (
                              <button
                                key={cat}
                                onClick={() => {
                                  setShowSuggestions(false);
                                  router.push(`/categories/${encodeURIComponent(cat)}`);
                                }}
                                className="group flex items-center gap-1.5 rounded-full border border-gray-100 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-800"
                              >
                                <svg className="h-3.5 w-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                                </svg>
                                {cat}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      {popularBrands.length > 0 && !searchQuery && (
                        <div className="border-t border-gray-50 p-4">
                          <h4 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                            Popular Brands
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {popularBrands.map((brand) => (
                              <button
                                key={brand}
                                onClick={() => {
                                  setShowSuggestions(false);
                                  router.push(`/brands/${encodeURIComponent(brand)}`);
                                }}
                                className="group flex items-center gap-1.5 rounded-full border border-gray-100 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:border-blue-200 hover:bg-blue-50 hover:text-blue-800"
                              >
                                <svg className="h-3.5 w-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                                </svg>
                                {brand}
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
            {/* Delivery Location - Myntra style */}
            <div
              className={styles.actionItem}
              ref={locationRef}
              onMouseEnter={() => setShowLocationDropdown(true)}
              onMouseLeave={() => setShowLocationDropdown(false)}
            >
              <button
                type="button"
                onClick={() => setShowLocationDropdown((prev) => !prev)}
                aria-label={pincode ? `Delivery location: ${pincode}` : 'Select delivery location'}
                aria-expanded={showLocationDropdown}
                aria-haspopup="true"
              >
                <div className="relative flex items-center justify-center">
                  <svg
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                    focusable="false"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  {availableModes.includes('hyperlocal') && (
                    <span
                      className="absolute -top-1 -right-2 text-[10px] leading-none text-emerald-600 font-bold"
                      title="Hyperlocal delivery available"
                    >
                      ⚡
                    </span>
                  )}
                </div>
                <span className="text-[11px] font-bold tracking-tight text-neutral-800 mt-1 block text-center">
                  {pincode ? pincode : 'Location'}
                </span>
              </button>

              {showLocationDropdown && (
                <div
                  className="absolute right-0 top-full z-[1001] mt-2 w-72 rounded-2xl border border-gray-100 bg-white p-4 text-left shadow-2xl animate-in fade-in slide-in-from-top-2 duration-150"
                  role="dialog"
                  aria-label="Choose delivery location"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="pb-2 border-b border-gray-100">
                    <h4 className="text-sm font-bold text-gray-900">Choose delivery location</h4>
                    <p className="mt-0.5 text-[11px] text-gray-500 truncate">
                      {pincode ? (
                        <>
                          Delivering to: <span className="font-semibold text-gray-800">{city ? `${city}, ` : ''}{pincode}</span>
                        </>
                      ) : (
                        'Enter PIN for delivery options in your area'
                      )}
                    </p>
                  </div>

                  <form onSubmit={handleApplyPincode} className="mt-3">
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        maxLength={6}
                        value={pincodeInput}
                        onChange={(e) => {
                          setPincodeInput(e.target.value.replace(/\D/g, '').slice(0, 6));
                          setPincodeError(null);
                        }}
                        placeholder={pincode || "Enter 6-digit PIN"}
                        className="flex-1 px-3 py-1.5 text-xs font-semibold rounded-lg border border-gray-200 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#1a4d33] focus:border-transparent transition-all"
                      />
                      <button
                        type="submit"
                        disabled={isApplyingPincode || pincodeInput.length !== 6}
                        className="px-3 py-1.5 rounded-lg text-xs font-bold text-white transition-opacity disabled:opacity-40 disabled:cursor-not-allowed shadow-sm shrink-0"
                        style={{ backgroundColor: theme.primary }}
                      >
                        {isApplyingPincode ? '...' : 'Apply'}
                      </button>
                    </div>
                    {pincodeError && (
                      <p className="mt-1 text-[11px] font-medium text-rose-500">{pincodeError}</p>
                    )}
                  </form>

                  {/* Mode Switcher inside location popup */}
                  {availableModes.length === 2 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1.5">
                        Delivery Mode
                      </p>
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => setActiveMode('hyperlocal')}
                          className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-2 rounded-full text-xs font-semibold transition-all ${
                            activeMode === 'hyperlocal'
                              ? 'bg-[#1a4d33] text-white shadow-sm'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          <span>⚡</span>
                          <span>60 min</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setActiveMode('pan_india')}
                          className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-2 rounded-full text-xs font-semibold transition-all ${
                            activeMode === 'pan_india'
                              ? 'bg-blue-600 text-white shadow-sm'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          <span>🌐</span>
                          <span>All India</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

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

      </header>

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
    </>
  );
}
