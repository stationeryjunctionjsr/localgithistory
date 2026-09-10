'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'react-hot-toast';
import { useAuth } from '@/context/AuthContext';
import { useCart } from '@/context/CartContext';
import api from '@/utils/api';
import { recordEvent, trackBackendProductClick, trackBackendFilterClick, getSessionId, trackEcommerceEvent } from '@/utils/analytics';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import AuthModal from '@/components/AuthModal';
import { usePincode } from '@/context/PincodeContext';
import UnserviceableLocationBanner from '@/components/UnserviceableLocationBanner';
import { logger } from '@/utils/logger';

// pageMode controls what appears as chips (on the page) vs. filters (in sidebar):
//   'category'    → sub-categories as chips on page, brands in filters (no categories, no sub-categories in sidebar)
//   'brand'       → categories as chips on page, sub-categories in filters, NO brands in sidebar
//   'collection'  → categories as chips on page, sub-categories & brands in sidebar
//   'general'     → categories in sidebar, sub-categories & brands in sidebar (default)
type PageMode = 'category' | 'brand' | 'collection' | 'general';

/** Server page size for catalog requests (matches admin-style discrete pages, not infinite scroll). */
const PRODUCTS_PAGE_SIZE = 24;

interface ProductCatalogProps {
  category?: string;
  subCategory?: string;
  categoryTag?: string | null;
  collection?: string | null;
  brand?: string;
  showFilters?: boolean;
  searchTerm?: string;
  filter?: string;
  basePath?: string;
  hideSubCategoryFilters?: boolean;
  pageMode?: PageMode;
  imageUrl?: string;
  description?: string;
  hideHeader?: boolean;
  hideBreadcrumbs?: boolean;
}

// Fallback component showing popular products when search yields no results
function PopularProductsFallback() {
  const [popularProducts, setPopularProducts] = useState<any[]>([]);
  const router = useRouter();

  useEffect(() => {
    const fetchPopular = async () => {
      try {
        const res = await api.get('/products/public?sort=popular&limit=8');
        setPopularProducts((res.data?.products || res.data || []).slice(0, 8));
      } catch (error) {
        logger.error('Failed to fetch popular products:', error);
      }
    };
    fetchPopular();
  }, []);

  if (popularProducts.length === 0) return null;

  return (
    <div className="mx-auto grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
      {popularProducts.map((product: any) => (
        <button
          key={product._id}
          onClick={() => router.push(`/customer/product/${product._id}`)}
          className="rounded-lg bg-gray-50 p-3 text-left transition-colors hover:bg-gray-100"
        >
          {(product.displayImage || product.images?.[0]) && (
            <div className="mb-2 aspect-square w-full overflow-hidden rounded bg-white">
              <img
                src={getImageUrlWithFallback(product.displayImage || product.images[0])}
                alt={product.name}
                className="h-full w-full object-contain"
              />
            </div>
          )}
          <p className="line-clamp-2 text-xs font-medium text-gray-900">{product.name}</p>
          <p className="mt-0.5 text-xs text-gray-500">
            ₹{(product.price || product.mrp || 0).toLocaleString()}
          </p>
        </button>
      ))}
    </div>
  );
}

export default function ProductCatalog({
  category: propCategory = '',
  subCategory: propSubCategory = '',
  categoryTag: propCategoryTag = null,
  collection: propCollection = null,
  brand: propBrand = '',
  showFilters = true,
  searchTerm: propSearchTerm = '',
  filter: propFilter = '',
  basePath: propBasePath,
  hideSubCategoryFilters = false,
  pageMode = 'general',
  // eslint-disable-next-line unused-imports/no-unused-vars
  imageUrl = '',
  description = '',
  hideHeader = false,
  hideBreadcrumbs = false,
}: ProductCatalogProps) {
  // Add disabled option styles only
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .disabled-option {
        opacity: 0.4;
        cursor: not-allowed !important;
        pointer-events: none;
      }
      .disabled-option input {
        cursor: not-allowed !important;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  const { isServiceable, pincode } = usePincode();
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState(propSearchTerm);
  const [category, setCategory] = useState(propCategory);
  const [subCategory, setSubCategory] = useState(propSubCategory);
  const [selectedSort, setSelectedSort] = useState('newest');
  const [usedFuzzy, setUsedFuzzy] = useState(false);
  const [suggestedQuery, setSuggestedQuery] = useState('');
  const [filters, setFilters] = useState<{
    type: string;
    value: string;
    brand: string[];
    minPrice: string;
    maxPrice: string;
    minDiscount: string;
    bestSeller: boolean;
    popularity: string; // 'new' | 'best_selling' | 'trending' | ''
    categoryTag: string;
    collections: string[];
    availability: string[]; // 'available' | 'stock_out'
  }>({
    type: '',
    value: '',
    brand: [],
    minPrice: '',
    maxPrice: '',
    minDiscount: '',
    bestSeller: false,
    popularity: propFilter || '',
    categoryTag: '',
    collections: [] as string[],
    availability: ['available', 'stock_out'],
  });
  const [totalProducts, setTotalProducts] = useState(0);
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [brands, setBrands] = useState<string[]>([]);
  const [subCategories, setSubCategories] = useState<string[]>([]);
  const [typeValueGroups, setTypeValueGroups] = useState<any[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [categoryTags, setCategoryTags] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [availableCollections, setAvailableCollections] = useState<string[]>([]);
  const [allCollections, setAllCollections] = useState<{ _id: string; name: string }[]>([]);
  const [allProducts, setAllProducts] = useState<any[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [priceRange, setPriceRange] = useState({ min: 0, max: 10000 });
  const [priceRangeBounds, setPriceRangeBounds] = useState({ min: 0, max: 10000 }); // Constant bounds
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [tempMinPrice, setTempMinPrice] = useState<string>('');
  const [tempMaxPrice, setTempMaxPrice] = useState<string>('');
  const [isDraggingMin, setIsDraggingMin] = useState(false);
  const [isDraggingMax, setIsDraggingMax] = useState(false);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [wishlistedIds, setWishlistedIds] = useState<Set<string>>(new Set());
  const productsGridRef = useRef<HTMLElement>(null);
  const router = useRouter();
  const { user } = useAuth();
  const { addToCart, cart, updateQuantity, removeFromCart, fetchCart } = useCart();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingWishlistProductId, setPendingWishlistProductId] = useState<string | null>(null);
  const [pendingWishlistProductName, setPendingWishlistProductName] = useState<string | null>(null);
  const [bundleItems, setBundleItems] = useState<any[]>([]);

  // Back to top scroll detection - only show when scrolling down
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      if (currentScrollY > 400 && currentScrollY > lastScrollY) {
        setShowBackToTop(true);
      } else {
        setShowBackToTop(false);
      }
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  // Mouse move handler for slider dragging
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingMin && !isDraggingMax) return;

      const slider = document.querySelector('.range-slider') as HTMLElement;
      if (!slider) return;

      const rect = slider.getBoundingClientRect();
      const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const value = Math.round(
        priceRangeBounds.min + percent * (priceRangeBounds.max - priceRangeBounds.min)
      );

      if (isDraggingMin) {
        setTempMinPrice(value.toString());
      } else if (isDraggingMax) {
        setTempMaxPrice(value.toString());
      }
    };

    const handleMouseUp = () => {
      if (isDraggingMin || isDraggingMax) {
        setFilters((prev) => ({
          ...prev,
          minPrice: tempMinPrice,
          maxPrice: tempMaxPrice,
        }));
      }
      setIsDraggingMin(false);
      setIsDraggingMax(false);
    };

    if (isDraggingMin || isDraggingMax) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDraggingMin, isDraggingMax, priceRangeBounds]);



  // Get base path based on user role or prop
  const getBasePath = () => {
    if (propBasePath) return propBasePath;
    if (user?.role === 'wholesaler') return '/wholesaler';
    return '/customer';
  };
  const basePath = getBasePath();

  useEffect(() => {
    setCategory(propCategory);
    setSubCategory(propSubCategory);
    setSearchTerm(propSearchTerm);
    if (propBrand != null) {
      setFilters((prev: any) => ({
        ...prev,
        brand: [propBrand],
        popularity: propFilter || prev.popularity,
      }));
    } else if (propFilter) {
      setFilters((prev: any) => ({ ...prev, popularity: propFilter }));
    }
  }, [propCategory, propSubCategory, propSearchTerm, propBrand, propFilter]);

  useEffect(() => {
    if (user) {
      api.get('/wishlist').then((res) => {
        const items = res.data?.items || res.data || [];
        const ids = new Set<string>(items.map((w: any) => w.product?._id || w.productId).filter(Boolean));
        setWishlistedIds(ids);
      }).catch((e) => logger.warn("Background task failed", e));
    }
  }, [user]);

  useEffect(() => {
    // Fetch all collections to get names
    const fetchCollections = async () => {
      try {
        const res = await api.get('/collections/public');
        const data = Array.isArray(res.data) ? res.data : res.data?.data || [];
        setAllCollections(data);
      } catch (e) {
        logger.error('Error fetching collections', e);
      }
    };
    fetchCollections();

    setPage(1);
    fetchProducts(1);
    if (typeof window !== 'undefined') {
      localStorage.setItem('hasVisited', 'true');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    category,
    subCategory,
    searchTerm,
    selectedSort,
    filters,
    propCategoryTag,
    propCollection,
    selectedCategories,
    pincode,
    isServiceable,
  ]);

  // Fetch bundles in parallel with products when filters are active
  useEffect(() => {
    const fetchBundles = async () => {
      const hasFilter = !!(searchTerm || category || propCategoryTag || filters.brand.length > 0);
      if (!hasFilter) {
        setBundleItems([]);
        return;
      }
      try {
        const params = new URLSearchParams();
        if (searchTerm) params.set('q', searchTerm);
        if (category) params.set('category', category);
        if (filters.brand.length > 0) params.set('brand', filters.brand[0]);
        params.set('limit', '6');
        const res = await api.get(`/bundles/search?${params.toString()}`);
        const bundles = (res.data?.bundles || []).filter((b: any) => b.isAvailable);
        setBundleItems(bundles);
      } catch {
        setBundleItems([]);
      }
    };
    fetchBundles();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, category, filters.brand, propCategoryTag]);

  // Reset price range bounds when category or search changes
  useEffect(() => {
    setPriceRangeBounds({ min: 0, max: 10000 });
  }, [category, subCategory, searchTerm, propCategoryTag, propCollection]);

  const fetchProducts = async (pageNumber: number = 1) => {
    try {
      setFetchError(false);
      setLoading(true);
      setUsedFuzzy(false);
      setSuggestedQuery('');

      // Use public endpoint if user is not authenticated, otherwise use authenticated endpoint
      const endpoint = user ? '/products' : '/products/public';

      // Build API URL with query parameters
      const params = new URLSearchParams();

      params.append('page', pageNumber.toString());
      params.append('limit', String(PRODUCTS_PAGE_SIZE));

      if (category) params.append('category', category);
      if (subCategory) params.append('subCategory', subCategory);
      if (searchTerm) params.append('search', searchTerm);
      if (propCategoryTag) params.append('categoryTag', propCategoryTag);
      // Include selected categories from filter checkboxes
      if (selectedCategories.length > 0) params.append('categories', selectedCategories.join(','));
      if (filters.brand.length > 0) params.append('brand', filters.brand.join(','));
      if (filters.minPrice) params.append('minPrice', filters.minPrice);
      if (filters.maxPrice) params.append('maxPrice', filters.maxPrice);
      if (filters.minDiscount) params.append('minDiscount', filters.minDiscount);
      if (filters.bestSeller) params.append('bestSeller', 'true');
      if (filters.popularity) params.append('popularity', filters.popularity);
      if (propCollection) params.append('collection', propCollection);
      else if (filters.collections && filters.collections.length > 0)
        params.append('collection', filters.collections.join(','));
      if (filters.type) params.append('type', filters.type);
      if (filters.value) params.append('value', filters.value);
      params.append('includeFacets', (pageNumber === 1).toString());
      params.append('skinny', 'true');
      if (filters.availability && filters.availability.length === 1) {
        params.append('availability', filters.availability[0]);
      }
      params.append('sort', selectedSort);
      // Pass pincode so the backend can filter products to the user's delivery zone
      if (pincode) params.append('pincode', pincode);

      let url = endpoint;
      if (params.toString()) {
        url += '?' + params.toString();
      }

      const response = await api.get(url);
      let fetchedProducts = response.data.products || response.data || [];
      const count = response.data.totalCount || response.data.length || fetchedProducts.length;
      setTotalProducts(count);
      setUsedFuzzy(!!response.data.usedFuzzy);
      setSuggestedQuery(response.data.suggestedQuery || '');

      // Track search for trending conversion (productIds = results shown)
      if (searchTerm && pageNumber === 1) {
        const productIds = (fetchedProducts || []).map((p: any) => p._id || p.id).filter(Boolean);
        api
          .post('/tracking/search', {
            searchTerm,
            resultsCount: count,
            sessionId: getSessionId() || undefined,
            productIds: productIds.length ? productIds : undefined,
          })
          .catch((e) => logger.warn("Background task failed", e));
      }

      const availableBrands = response.data.brands || [];
      const availableCategories = response.data.categories || [];
      const availableSubCategories = response.data.subCategories || [];
      const availableCols = response.data.collections || [];

      const seenIds = new Set<string>();
      const updatedProducts = fetchedProducts.filter((p: any) => {
        const id = p._id || p.id;
        if (!id) return true;
        if (seenIds.has(id)) return false;
        seenIds.add(id);
        return true;
      });

      // Helper: product is in stock
      const isInStock = (p: any) => p.stock != null && Number(p.stock) > 0;

      // Apply client-side sorting while keeping available first, then stock out (when not filtering by availability)
      let filteredProducts = [...updatedProducts];
      const sortCompare = (a: any, b: any): number => {
        switch (selectedSort) {
          case 'popular':
            return (b.popularity || 0) - (a.popularity || 0);
          case 'price_asc':
            return (a.price || a.mrp || 0) - (b.price || b.mrp || 0);
          case 'price_desc':
            return (b.price || b.mrp || 0) - (a.price || a.mrp || 0);
          case 'name_asc':
            return (a.name || '').localeCompare(b.name || '');
          case 'name_desc':
            return (b.name || '').localeCompare(a.name || '');
          case 'newest':
          default:
            return new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime();
        }
      };

      if (filters.availability && filters.availability.length !== 1) {
        const available = filteredProducts.filter(isInStock).sort(sortCompare);
        const stockOut = filteredProducts.filter((p: any) => !isInStock(p)).sort(sortCompare);
        filteredProducts = [...available, ...stockOut];
      } else {
        filteredProducts.sort(sortCompare);
      }

      setProducts(filteredProducts);
      setPage(pageNumber);
      setAllProducts(fetchedProducts);

        // Update filters from backend aggregate data if available, otherwise fallback to local extraction
        // IMPORTANT: Extract from allProducts (unfiltered) to ensure filter options reflect ALL available products
        const unfilteredProducts = fetchedProducts;
        if (pageNumber === 1) {
          setBrands(
            availableBrands.length > 0
              ? availableBrands
              : (Array.from(
                  new Set(unfilteredProducts.map((p: any) => p.brand).filter(Boolean))
                ) as string[])
          );
          setSubCategories(
            availableSubCategories.length > 0
              ? availableSubCategories
              : (Array.from(
                  new Set(unfilteredProducts.map((p: any) => p.subCategory).filter(Boolean))
                ) as string[])
          );
          setCategories(
            availableCategories.length > 0
              ? availableCategories
              : (Array.from(
                  new Set(unfilteredProducts.map((p: any) => p.category).filter(Boolean))
                ) as string[])
          );
          // Extract collections - use backend data first, else extract from products
          setAvailableCollections(
            availableCols.length > 0
              ? availableCols
              : (Array.from(
                  new Set(unfilteredProducts.map((p: any) => p.collection).filter(Boolean))
                ) as string[])
          );
        }

      // Calculate price range bounds from displayed products (before price filter is applied)
      // Get products after applying all filters except price filter
      let productsForPriceRange = [...fetchedProducts];

      // Apply category filter
      if (selectedCategories.length > 0) {
        productsForPriceRange = productsForPriceRange.filter((p) =>
          selectedCategories.includes(p.category)
        );
      }

      // Apply brand filter
      if (filters.brand.length > 0) {
        productsForPriceRange = productsForPriceRange.filter((p) =>
          filters.brand.includes(p.brand)
        );
      }

      // Apply other filters (but not price)
      if (filters.type && filters.value) {
        productsForPriceRange = productsForPriceRange.filter(
          (p) => p.type === filters.type && p.value === filters.value
        );
      }
      if (filters.categoryTag) {
        productsForPriceRange = productsForPriceRange.filter(
          (p) => p.categoryTag === filters.categoryTag
        );
      }
      if (searchTerm) {
        productsForPriceRange = productsForPriceRange.filter(
          (p) =>
            p.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            p.brand?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            p.category?.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }

      const prices = productsForPriceRange
        .map((p: any) => p.price || p.mrp || 0)
        .filter((price: number) => price > 0);
      if (prices.length > 0) {
        const minPrice = Math.floor(Math.min(...prices));
        const maxPrice = Math.ceil(Math.max(...prices));

        // Only update bounds if they haven't been set or if category/search changed (not price filter)
        const shouldUpdateBounds = priceRangeBounds.min === 0 && priceRangeBounds.max === 10000;

        if (shouldUpdateBounds) {
          setPriceRangeBounds({ min: minPrice, max: maxPrice });
          // Update filter defaults if needed
          if (!filters.minPrice) setFilters((prev) => ({ ...prev, minPrice: minPrice.toString() }));
          if (!filters.maxPrice) setFilters((prev) => ({ ...prev, maxPrice: maxPrice.toString() }));
        }
      }

      // Extract type-value groups - Use updatedProducts to ensure we have the latest data including current fetch
      // If we differ extraction to useEffect based on products, it might cycle.
      // Better to extract from the data we just decided to display.
      const sourceForExtraction = updatedProducts;

      const groups: { [key: string]: Set<string> } = {};
      sourceForExtraction.forEach((p: any) => {
        if (p.type && p.value) {
          if (!groups[p.type]) {
            groups[p.type] = new Set();
          }
          groups[p.type].add(p.value);
        }
      });

      const typeValueGroupsArray = Object.entries(groups).map(([type, values]) => ({
        type,
        values: Array.from(values),
      }));
      setTypeValueGroups(typeValueGroupsArray);

      // Extract category tags
      const newTags = Array.from(
        new Set(sourceForExtraction.map((p: any) => p.categoryTag).filter(Boolean))
      ) as string[];
      setCategoryTags(newTags);
    } catch (error) {
      logger.error('Error fetching products:', error);
      setProducts([]);
      if (pageNumber === 1) setFetchError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleProductClick = (product: any) => {
    trackBackendProductClick(product._id, product.name, 'catalog_grid');
    
    // Pass browsing context to the product detail page so breadcrumbs can adapt
    const queryParams = new URLSearchParams();
    if (propBrand) queryParams.set('refBrand', propBrand);
    if (propCollection) queryParams.set('refCollection', propCollection);
    
    const queryString = queryParams.toString();
    const productUrl = `${basePath}/product/${product._id}${queryString ? `?${queryString}` : ''}`;
    router.push(productUrl);
  };

  const handleWishlistToggle = async (productId: string, productName: string = '') => {
    if (!user) {
      setPendingWishlistProductId(productId);
      setPendingWishlistProductName(productName || null);
      setShowAuthModal(true);
      return;
    }
    try {
      if (wishlistedIds.has(productId)) {
        await api.delete(`/wishlist/${productId}`);
        setWishlistedIds((prev) => { const next = new Set(prev); next.delete(productId); return next; });
        toast.success(`${productName || 'Item'} removed from wishlist`);
      } else {
        await api.post('/wishlist', { productId });
        setWishlistedIds((prev) => new Set(prev).add(productId));
        toast.success(`${productName || 'Item'} added to wishlist`);
      }
    } catch (_error) {
      toast.error('Could not update wishlist');
    }
  };

  const handleAddToCart = async (
    productId: string,
    quantity: number = 1,
    productName: string = ''
  ) => {
    try {
      const product = products.find((p: any) => p._id === productId);
      await addToCart(productId, quantity, product);
      
      // Track add to cart event for GTM/GA4
      const price = product?.price || product?.mrp || 0;
      trackEcommerceEvent('add_to_cart', {
        value: price * quantity,
        items: [
          {
            item_id: product?._id,
            item_name: product?.name,
            price: price,
            item_brand: product?.brand,
            item_category: product?.category,
            quantity: quantity,
          },
        ],
      });

      toast.success(`${productName} added to cart!`);
    } catch (error) {
      logger.error('Error adding to cart:', error);
      toast.error('Failed to add to cart');
    }
  };

  const handleNotifyMe = async (productId: string, productName: string) => {
    try {
      if (user?.email) {
        await api.post(`/products/${productId}/notify-me`, {});
        toast.success(`We will notify you at ${user.email} once ${productName} is restocked!`);
      } else {
        const email = window.prompt(`Enter your email to get notified when "${productName}" is back in stock:`);
        if (email === null) return; // User cancelled
        const trimmedEmail = email.trim();
        if (!trimmedEmail || !trimmedEmail.includes('@')) {
          toast.error('Please enter a valid email address.');
          return;
        }
        await api.post(`/products/${productId}/notify-me`, { email: trimmedEmail });
        toast.success(`We will notify you at ${trimmedEmail} once ${productName} is restocked!`);
      }
    } catch (err: any) {
      logger.error('Failed to register notification', err);
      toast.error(err.response?.data?.detail || 'Failed to register restock notification');
    }
  };

  const handleFilterReset = () => {
    setFilters({
      type: '',
      value: '',
      brand: [],
      collections: [],
      minPrice: '',
      maxPrice: '',
      minDiscount: '',
      bestSeller: false,
      popularity: '',
      categoryTag: '',
      availability: ['available', 'stock_out'],
    });
    setSubCategory('');
    setSelectedCategories([]);
    setSearchTerm('');
    setSelectedSort('popular');
    fetchProducts(1);
  };

  const handleBrandChange = (brand: string, checked: boolean) => {
    const newFilters = {
      ...filters,
      brand: checked ? [...filters.brand, brand] : filters.brand.filter((b) => b !== brand),
    };
    setFilters(newFilters);
    recordEvent({
      type: 'brand_click',
      payload: { brand, active: newFilters.brand.includes(brand) },
    });
    if (checked) trackBackendFilterClick('brand', brand);
    // useEffect will automatically refetch when filters change
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  const handleTypeChange = (type: string) => {
    const newFilters = {
      ...filters,
      type: filters.type === type ? '' : type,
      value: '', // Reset value when type changes
    };
    setFilters(newFilters);
    recordEvent({ type: 'category_click', payload: { type, active: newFilters.type === type } });
    if (newFilters.type === type) trackBackendFilterClick('type', type);
    // useEffect will automatically refetch when filters change
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  const handleValueChange = (value: string) => {
    const newFilters = {
      ...filters,
      value: filters.value === value ? '' : value,
    };
    setFilters(newFilters);
    recordEvent({ type: 'list_click', payload: { value, active: newFilters.value === value } });
    if (newFilters.value === value) trackBackendFilterClick('value', value);
    // useEffect will automatically refetch when filters change
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  const handleCategoryTagChange = (tag: string) => {
    const newFilters = {
      ...filters,
      categoryTag: filters.categoryTag === tag ? '' : tag,
    };
    setFilters(newFilters);
    recordEvent({ type: 'tag_click', payload: { tag, active: newFilters.categoryTag === tag } });
    if (newFilters.categoryTag === tag) trackBackendFilterClick('category_tag', tag);
    // useEffect will automatically refetch when filters change
  };

  const handleCollectionChange = (colId: string, checked: boolean) => {
    const newFilters = {
      ...filters,
      collections: checked
        ? [...(filters.collections || []), colId]
        : (filters.collections || []).filter((c) => c !== colId),
    };
    setFilters(newFilters);
    recordEvent({ type: 'collection_click', payload: { collection: colId, active: checked } });
    if (checked) trackBackendFilterClick('collection', colId);
  };

  const handleCategoryChange = (cat: string, checked: boolean) => {
    const newCategories = checked
      ? [...selectedCategories, cat]
      : selectedCategories.filter((c) => c !== cat);
    setSelectedCategories(newCategories);
    if (checked) trackBackendFilterClick('category', cat);
    // useEffect will automatically refetch when selectedCategories changes
  };

  // Helper function to get filtered products for smart disabling
  // eslint-disable-next-line unused-imports/no-unused-vars
  const getFilteredProductsForOptions = () => {
    let filtered = allProducts;

    // Apply selected categories
    if (selectedCategories.length > 0) {
      filtered = filtered.filter((p) => selectedCategories.includes(p.category));
    }

    // Apply selected brands
    if (filters.brand.length > 0) {
      filtered = filtered.filter((p) => filters.brand.includes(p.brand));
    }

    // Apply price range
    if (filters.minPrice) {
      filtered = filtered.filter((p) => (p.price || p.mrp || 0) >= parseFloat(filters.minPrice));
    }
    if (filters.maxPrice) {
      filtered = filtered.filter((p) => (p.price || p.mrp || 0) <= parseFloat(filters.maxPrice));
    }

    // Apply other filters
    if (filters.type) {
      filtered = filtered.filter((p) => p.type === filters.type);
    }
    if (filters.value) {
      filtered = filtered.filter((p) => p.value === filters.value);
    }
    if (filters.minDiscount) {
      filtered = filtered.filter((p) => {
        const price = p.price || p.mrp || 0;
        const mrp = p.mrp || p.price || 0;
        const discount = mrp > 0 ? ((mrp - price) / mrp) * 100 : 0;
        return discount >= parseFloat(filters.minDiscount);
      });
    }
    if (filters.bestSeller) {
      filtered = filtered.filter((p) => p.bestSeller === true);
    }
    if (filters.categoryTag) {
      filtered = filtered.filter(
        (p) => (p.tags || []).includes(filters.categoryTag) || p.categoryTag === filters.categoryTag
      );
    }

    if (filters.popularity) {
      filtered = filtered.filter((p) => (p.tags || []).includes(filters.popularity));
    }

    return filtered;
  };

  // Dual-handle slider handlers
  // eslint-disable-next-line unused-imports/no-unused-vars
  const handleSliderChange = (type: 'min' | 'max', value: number) => {
    // Use bounds for slider calculation, but only update selected values
    const currentMin = parseInt(filters.minPrice) || priceRangeBounds.min;
    const currentMax = parseInt(filters.maxPrice) || priceRangeBounds.max;

    if (type === 'min') {
      // Ensure min doesn't exceed max and is within bounds
      const newMin = Math.max(priceRangeBounds.min, Math.min(value, currentMax - 1));
      setFilters({ ...filters, minPrice: newMin.toString() });
    } else {
      // Ensure max doesn't go below min and is within bounds
      const newMax = Math.min(priceRangeBounds.max, Math.max(value, currentMin + 1));
      setFilters({ ...filters, maxPrice: newMax.toString() });
    }
    // useEffect will automatically refetch when filters change
  };

  // Calculate slider percentages
  // eslint-disable-next-line unused-imports/no-unused-vars
  const minPricePercentage =
    priceRangeBounds.max > priceRangeBounds.min
      ? (((parseInt(filters.minPrice) || priceRangeBounds.min) - priceRangeBounds.min) /
          (priceRangeBounds.max - priceRangeBounds.min)) *
        100
      : 0;
  // eslint-disable-next-line unused-imports/no-unused-vars
  const maxPricePercentage =
    priceRangeBounds.max > priceRangeBounds.min
      ? (((parseInt(filters.maxPrice) || priceRangeBounds.max) - priceRangeBounds.min) /
          (priceRangeBounds.max - priceRangeBounds.min)) *
        100
      : 0;

  if (isServiceable === false) {
    return <UnserviceableLocationBanner />;
  }

  if (loading) {
    return (
      <div className="mx-auto w-full max-w-[1440px] px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-4 sm:gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="flex h-[360px] animate-pulse flex-col overflow-hidden rounded-2xl bg-white shadow-sm">
              <div className="aspect-[3/4] w-full bg-gray-200" />
              <div className="flex flex-1 flex-col p-4">
                <div className="mb-2 h-3 w-1/3 rounded bg-gray-200" />
                <div className="mb-3 h-4 w-3/4 rounded bg-gray-200" />
                <div className="mt-auto flex items-baseline gap-2">
                  <div className="h-5 w-1/4 rounded bg-gray-200" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center px-4">
        <div className="mb-4 text-center text-lg font-medium text-gray-900">Failed to load products</div>
        <p className="mb-6 text-center text-sm text-gray-500">There was an error connecting to the server. Please check your connection and try again.</p>
        <button 
          onClick={() => fetchProducts(1)} 
          className="rounded-full bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  const filteredProducts = products;
  const totalPages = Math.max(1, Math.ceil(totalProducts / PRODUCTS_PAGE_SIZE));

  // Merge bundles into product list: insert 1 bundle after every 8 products, append remainder at end
  const displayItems: any[] = (() => {
    if (!bundleItems.length) return filteredProducts;
    const merged: any[] = [];
    let bundleIdx = 0;
    filteredProducts.forEach((product: any, i: number) => {
      merged.push(product);
      if ((i + 1) % 8 === 0 && bundleIdx < bundleItems.length) {
        merged.push({ ...bundleItems[bundleIdx++], isBundle: true });
      }
    });
    while (bundleIdx < bundleItems.length) {
      merged.push({ ...bundleItems[bundleIdx++], isBundle: true });
    }
    return merged;
  })();

  const handleCatalogPageChange = (newPage: number) => {
    if (loading || newPage < 1 || newPage > totalPages) return;
    if (newPage === page) return;
    void fetchProducts(newPage);
    requestAnimationFrame(() =>
      productsGridRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    );
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  const newlyAdded = [...products]
    .sort(
      (a: any, b: any) =>
        new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime()
    )
    .slice(0, 10);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const showNewlyAdded = !category && !searchTerm;

  // Determine page name and logo based on source
  const getPageInfo = () => {
    let name = 'All Products';
    let logo: string | null = null;

    if (searchTerm) {
      name = searchTerm.charAt(0).toUpperCase() + searchTerm.slice(1).toLowerCase();
      return { name, logo };
    }

    if (propCategoryTag) {
      if (filters.popularity === 'new') name = `New Arrivals in ${propCategoryTag}`;
      else if (filters.popularity === 'best_selling') name = `Best sellers in ${propCategoryTag}`;
      else if (filters.popularity === 'trending') name = `Trending now in ${propCategoryTag}`;
      else name = `All ${propCategoryTag}`;
      return { name, logo };
    }

    if (category) {
      name = `${category}`;
      return { name, logo: 'category_icon' };
    }

    if (propBrand) {
      name = `${propBrand}`;
      return { name, logo: 'brand_icon' };
    }

    // If viewing a collection, don't show "All Products"
    if (propCollection) {
      // eslint-disable-next-line unused-imports/no-unused-vars
      const collectionName =
        allCollections.find((c) => c._id === propCollection)?.name ||
        allCollections.find((c) => c.name === propCollection)?.name ||
        propCollection;
      name = ''; // Don't show name since it's already in the header
      return { name, logo };
    }

    if (filters.popularity === 'best_selling' && !propCategoryTag) {
      name = 'Best Sellers';
    }

    return { name, logo };
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const { name: pageName, logo: pageLogo } = getPageInfo();

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-gray-50">
      {/* Breadcrumbs - Consistent with product detail page */}
      {!hideHeader && !hideBreadcrumbs && (
        <div className="border-b border-gray-100 bg-white px-2 py-1.5 text-xs font-medium tracking-wide text-gray-500">
          <div className="flex w-full flex-wrap items-center gap-1.5">
            <Link
              href={user ? basePath : '/'}
              className="flex items-center gap-1.5 transition-colors hover:text-gray-900"
            >
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
              Home
            </Link>
            {category && (
              <>
                <svg
                  className="h-3 w-3 text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                {/* If a subCategory is also active, make the category crumb a navigable link */}
                {subCategory ? (
                  <Link
                    href={`/categories/${encodeURIComponent(category)}`}
                    className="transition-colors hover:text-gray-900"
                  >
                    {category}
                  </Link>
                ) : (
                  <span className="font-semibold text-gray-800">{category}</span>
                )}
              </>
            )}
            {subCategory && (
              <>
                <svg
                  className="h-3 w-3 text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <span className="font-semibold text-gray-800">{subCategory}</span>
              </>
            )}
            {propBrand && (
              <>
                <svg
                  className="h-3 w-3 text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-gray-600">{propBrand}</span>
              </>
            )}
            {searchTerm && (
              <>
                <svg
                  className="h-3 w-3 text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-gray-600">&quot;{searchTerm}&quot;</span>
              </>
            )}
            {propCollection && (
              <>
                <svg
                  className="h-3 w-3 text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-gray-600">
                  {allCollections.find((c) => c._id === propCollection)?.name ||
                    allCollections.find((c) => c.name === propCollection)?.name ||
                    propCollection}
                </span>
              </>
            )}
            {filters.popularity && (
              <>
                <svg
                  className="h-3 w-3 text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-gray-600">
                  {filters.popularity === 'new'
                    ? 'New Arrivals'
                    : filters.popularity === 'best_selling'
                      ? 'Best Sellers'
                      : filters.popularity === 'trending'
                        ? 'Trending Now'
                        : filters.popularity}
                </span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Top Bar - Header, Product Count, Sort */}
      <div className="border-b border-gray-100 bg-white px-2 py-2">
        <div className="flex w-full flex-wrap items-center justify-between gap-3">
          {/* Left: Page Name & Count */}
          <div className="flex items-center gap-3">
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-gray-600 md:text-base">
                  Displaying <span className="font-semibold text-gray-900">{totalProducts}</span>{' '}
                  {totalProducts === 1 ? 'product' : 'products'}
                </p>
              </div>
              {description && (
                <p className="mt-1 line-clamp-1 text-[10px] text-gray-500 md:text-xs">
                  {description}
                </p>
              )}
            </div>
          </div>

          {/* Right: Sort & View Options */}
          <div className="flex items-center gap-3">
            {/* Sort Dropdown */}
            <div className="flex items-center gap-2">
              <span className="hidden text-xs font-medium text-gray-500 sm:inline">Sort:</span>
              <div className="relative">
                <select
                  value={selectedSort}
                  onChange={(e) => setSelectedSort(e.target.value)}
                  className="cursor-pointer appearance-none rounded-md border border-gray-200 bg-white py-1.5 pl-3 pr-7 text-xs font-medium text-gray-700 transition-colors hover:border-gray-300 focus:border-gray-400 focus:ring-1 focus:ring-gray-400"
                >
                  <option value="popular">Popular</option>
                  <option value="newest">Newest</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="price_desc">Price: High to Low</option>
                </select>
                <svg
                  className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex w-full flex-col md:flex-row md:h-[calc(100vh-73px)] md:overflow-hidden">
        {/* Mobile Filter Toggle Button */}
        {showFilters && (
          <button
            onClick={() => setShowMobileFilters(!showMobileFilters)}
            className="fixed bottom-20 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-full bg-gray-900 px-6 py-3 text-white shadow-xl transition-colors hover:bg-gray-800 md:hidden"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
            </svg>
            <span className="text-sm font-semibold">Filters</span>
            {(filters.brand.length > 0 ||
              filters.minPrice ||
              filters.maxPrice ||
              filters.minDiscount ||
              filters.type ||
              filters.availability) && (
              <span className="ml-1 rounded-full bg-white px-1.5 py-0.5 text-xs font-bold text-gray-900">
                {filters.brand.length +
                  (filters.minPrice ? 1 : 0) +
                  (filters.maxPrice ? 1 : 0) +
                  (filters.minDiscount ? 1 : 0) +
                  (filters.type ? 1 : 0) +
                  (filters.availability ? 1 : 0)}
              </span>
            )}
          </button>
        )}

        {/* Sidebar */}
        {showFilters && (
          <>
            {showMobileFilters && (
              <div
                className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
                onClick={() => setShowMobileFilters(false)}
              />
            )}
            <div
              className={`w-full flex-shrink-0 md:w-[260px] ${showMobileFilters ? 'block' : 'hidden md:block'}`}
            >
              <div className="fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col overflow-hidden border-r border-gray-100 bg-white shadow-xl md:relative md:sticky md:top-[73px] md:z-auto md:h-[calc(100vh-73px)] md:max-h-[calc(100vh-73px)] md:w-auto md:shadow-none">
                {/* Filter Header */}
                <div className="flex flex-shrink-0 items-center justify-between border-b border-gray-100 bg-white p-4">
                  <div className="flex items-center gap-2">
                    <svg
                      className="h-5 w-5 text-gray-700"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                    </svg>
                    <h3 className="text-sm font-semibold uppercase tracking-widest text-gray-900">
                      Filters
                    </h3>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleFilterReset}
                      className="text-xs font-medium text-gray-500 underline underline-offset-2 transition-colors hover:text-gray-900"
                    >
                      Clear All
                    </button>
                    <button
                      onClick={() => setShowMobileFilters(false)}
                      className="rounded-full p-1 transition-colors hover:bg-gray-100 md:hidden"
                    >
                      <svg
                        className="h-5 w-5 text-gray-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </div>
                </div>

                <div className="flex-1 space-y-0.5 overflow-x-hidden overflow-y-auto p-3">
                  {/* Categories - show in sidebar for general or collection mode; for brand/category modes, categories are chips on the page or not relevant */}
                  {(pageMode === 'general' || pageMode === 'collection') &&
                    !category &&
                    categories.length > 0 && (
                      <div className="pb-2">
                        <h4 className="mb-2 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-900">
                          Categories
                          {selectedCategories.length > 0 && (
                            <span className="text-[10px] font-medium normal-case text-gray-500">
                              {selectedCategories.length} selected
                            </span>
                          )}
                        </h4>
                        <div className="max-h-48 space-y-1 overflow-y-auto pr-1">
                          {categories.map((cat) => (
                            <label
                              key={cat}
                              className="group flex cursor-pointer items-center gap-2.5 rounded px-1 py-0.5 transition-colors hover:bg-gray-50"
                            >
                              <input
                                type="checkbox"
                                checked={selectedCategories.includes(cat)}
                                onChange={(e) => handleCategoryChange(cat, e.target.checked)}
                                className="h-4 w-4 cursor-pointer rounded border-gray-300 text-gray-900 focus:ring-gray-900 focus:ring-offset-0"
                              />
                              <span
                                className={`break-words text-sm transition-colors ${selectedCategories.includes(cat) ? 'font-medium text-gray-900' : 'text-gray-600 group-hover:text-gray-900'}`}
                              >
                                {cat}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Sub-categories - show in desktop for all modes except when hideSubCategoryFilters is true */}
                  {subCategories.length > 0 && !hideSubCategoryFilters && (
                    <div className="border-t border-gray-100 py-2">
                      <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-900">
                        Sub-categories
                      </h4>
                      <div className="max-h-48 space-y-1.5 overflow-y-auto pr-1">
                        {subCategories.map((sub) => (
                          <label
                            key={sub}
                            className="group flex cursor-pointer items-center gap-2.5 rounded px-1 py-1 transition-colors hover:bg-gray-50"
                          >
                            <input
                              type="checkbox"
                              checked={subCategory === sub}
                              onChange={() => setSubCategory(subCategory === sub ? '' : sub)}
                              className="h-4 w-4 cursor-pointer rounded border-gray-300 text-gray-900 focus:ring-gray-900 focus:ring-offset-0"
                            />
                            <span
                              className={`break-words text-sm transition-colors ${subCategory === sub ? 'font-medium text-gray-900' : 'text-gray-600 group-hover:text-gray-900'}`}
                            >
                              {sub}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Collections Filter */}
                  {availableCollections.length > 0 && (
                    <div className="border-t border-gray-100 py-2">
                      <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-900">
                        Collections
                      </h4>
                      <div className="max-h-48 space-y-1 overflow-y-auto pr-1">
                        {availableCollections.map((colId) => {
                          const colName =
                            allCollections.find((c) => c._id === colId)?.name ||
                            allCollections.find((c) => c.name === colId)?.name ||
                            colId;
                          return (
                            <label
                              key={colId}
                              className="group flex cursor-pointer items-center gap-2.5 rounded px-1 py-0.5 transition-colors hover:bg-gray-50"
                            >
                              <input
                                type="checkbox"
                                checked={(filters.collections || []).includes(colId)}
                                onChange={(e) => handleCollectionChange(colId, e.target.checked)}
                                className="h-4 w-4 cursor-pointer rounded border-gray-300 text-gray-900 focus:ring-gray-900 focus:ring-offset-0"
                              />
                              <span
                                className={`break-words text-sm transition-colors ${(filters.collections || []).includes(colId) ? 'font-medium text-gray-900' : 'text-gray-600 group-hover:text-gray-900'}`}
                              >
                                {colName}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Brands - hide for brand mode (auto-filtered by brand), show for category/collection/general */}
                  {brands.length > 0 && pageMode !== 'brand' && (
                    <div className="border-t border-gray-100 py-2">
                      <h4 className="mb-2 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-gray-800">
                        Brands
                        {filters.brand.length > 0 && (
                          <span className="text-[10px] font-medium normal-case text-gray-500">
                            {filters.brand.length} selected
                          </span>
                        )}
                      </h4>
                      <div className="max-h-48 space-y-1 overflow-y-auto pr-1">
                        {brands.map((brandInfo: any) => {
                          const brandName =
                            typeof brandInfo === 'string' ? brandInfo : brandInfo.name;
                          return (
                            <label
                              key={brandName}
                              className="group flex cursor-pointer items-center gap-2.5 rounded px-1 py-0.5 transition-colors hover:bg-gray-50"
                            >
                              <input
                                type="checkbox"
                                checked={filters.brand.includes(brandName)}
                                onChange={(e) => handleBrandChange(brandName, e.target.checked)}
                                className="h-4 w-4 cursor-pointer rounded border-gray-300 text-gray-900 focus:ring-gray-900 focus:ring-offset-0"
                              />
                              <span
                                className={`break-words text-sm transition-colors ${filters.brand.includes(brandName) ? 'font-medium text-gray-900' : 'text-gray-600 group-hover:text-gray-900'}`}
                              >
                                {brandName}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Price Range */}
                  <div className="border-t border-gray-100 py-2">
                    <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-800">
                      Price Range
                    </h4>
                    <div className="px-2">
                      <div className="mb-4 flex justify-between text-xs font-bold text-gray-500">
                        <span>₹{priceRangeBounds.min}</span>
                        <span>₹{priceRangeBounds.max}</span>
                      </div>
                      <div className="range-slider relative h-8">
                        <div className="slider-track absolute top-1/2 h-1 w-full -translate-y-1/2 rounded-full bg-gray-200"></div>
                        {(() => {
                          const curMin = isDraggingMin
                            ? parseInt(tempMinPrice)
                            : parseInt(filters.minPrice) || priceRangeBounds.min;
                          const curMax = isDraggingMax
                            ? parseInt(tempMaxPrice)
                            : parseInt(filters.maxPrice) || priceRangeBounds.max;
                          const minPct =
                            ((curMin - priceRangeBounds.min) /
                              (priceRangeBounds.max - priceRangeBounds.min)) *
                            100;
                          const maxPct =
                            ((curMax - priceRangeBounds.min) /
                              (priceRangeBounds.max - priceRangeBounds.min)) *
                            100;

                          return (
                            <>
                              <div
                                className="slider-range absolute top-1/2 h-1 -translate-y-1/2 rounded-full bg-gray-900"
                                style={{ left: `${minPct}%`, width: `${maxPct - minPct}%` }}
                              ></div>
                              <div
                                className="slider-thumb absolute top-1/2 z-10 h-4 w-4 -translate-x-1/2 -translate-y-1/2 cursor-pointer rounded-full border-2 border-white bg-gray-900 shadow-md transition-transform hover:scale-110"
                                style={{ left: `${minPct}%` }}
                                onMouseDown={() => {
                                  setTempMinPrice(
                                    filters.minPrice || priceRangeBounds.min.toString()
                                  );
                                  setTempMaxPrice(
                                    filters.maxPrice || priceRangeBounds.max.toString()
                                  );
                                  setIsDraggingMin(true);
                                }}
                              >
                                <div className="slider-value absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-gray-900 px-1.5 py-0.5 text-[10px] text-white">
                                  ₹
                                  {isDraggingMin
                                    ? tempMinPrice
                                    : filters.minPrice || priceRangeBounds.min}
                                </div>
                              </div>
                              <div
                                className="slider-thumb absolute top-1/2 z-10 h-4 w-4 -translate-x-1/2 -translate-y-1/2 cursor-pointer rounded-full border-2 border-white bg-gray-900 shadow-md transition-transform hover:scale-110"
                                style={{ left: `${maxPct}%` }}
                                onMouseDown={() => {
                                  setTempMinPrice(
                                    filters.minPrice || priceRangeBounds.min.toString()
                                  );
                                  setTempMaxPrice(
                                    filters.maxPrice || priceRangeBounds.max.toString()
                                  );
                                  setIsDraggingMax(true);
                                }}
                              >
                                <div className="slider-value absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-gray-900 px-1.5 py-0.5 text-[10px] text-white">
                                  ₹
                                  {isDraggingMax
                                    ? tempMaxPrice
                                    : filters.maxPrice || priceRangeBounds.max}
                                </div>
                              </div>
                            </>
                          );
                        })()}
                      </div>
                    </div>
                  </div>

                  {/* Availability */}
                  <div className="border-t border-gray-100 py-2">
                    <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-800">
                      Availability
                    </h4>
                    <div className="space-y-2">
                      {[
                        { label: 'Available', value: 'available' },
                        { label: 'Stock out', value: 'stock_out' },
                      ].map((item) => (
                        <label
                          key={item.value}
                          className="group flex cursor-pointer items-center gap-2 py-1"
                        >
                          <input
                            type="checkbox"
                            checked={filters.availability.includes(item.value)}
                            onChange={(e) => {
                              const newAvailability = e.target.checked
                                ? [...filters.availability, item.value]
                                : filters.availability.filter((a) => a !== item.value);
                              setFilters({ ...filters, availability: newAvailability });
                            }}
                            className="h-4 w-4 cursor-pointer rounded border-gray-300 text-gray-900 focus:ring-gray-900 focus:ring-offset-0"
                          />
                          <span
                            className={`break-words text-sm transition-colors ${filters.availability.includes(item.value) ? 'font-semibold text-gray-900' : 'text-gray-600 group-hover:text-gray-900'}`}
                          >
                            {item.label}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Attributes/Variants - Moved above Discount */}
                  {typeValueGroups.map((group) => (
                    <div key={group.type} className="border-t border-gray-100 pt-4">
                      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-900">
                        {group.type}
                      </h4>
                      <div className="space-y-2">
                        {group.values.map((value: string) => (
                          <label
                            key={value}
                            className="group flex cursor-pointer items-center gap-3"
                          >
                            <input
                              type="checkbox"
                              checked={filters.type === group.type && filters.value === value}
                              onChange={() => {
                                if (filters.type === group.type && filters.value === value) {
                                  setFilters({ ...filters, type: '', value: '' });
                                } else {
                                  setFilters({ ...filters, type: group.type, value: value });
                                }
                              }}
                              className="h-4 w-4 cursor-pointer rounded border-2 border-gray-300 text-gray-900 focus:ring-gray-500"
                            />
                            <span className="text-sm font-medium text-gray-700 transition-colors group-hover:text-gray-900">
                              {value}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* Discount Range Slider */}
                  <div className="border-t border-gray-100 py-4">
                    <h4 className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-gray-800">
                      Min. Discount
                    </h4>
                    <div className="px-1 pb-2">
                      <div className="relative pt-1">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          step="5"
                          value={filters.minDiscount || '0'}
                          onChange={(e) => {
                            e.preventDefault();
                            setFilters({ ...filters, minDiscount: e.target.value });
                          }}
                          onMouseDown={(e) => e.stopPropagation()}
                          className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-gray-900"
                        />
                        <div className="mt-3 flex items-center justify-between">
                          <span className="text-xs font-medium text-gray-700">
                            {filters.minDiscount || '0'}% off & more
                          </span>
                          {filters.minDiscount && filters.minDiscount !== '0' && (
                            <button
                              onClick={(e) => {
                                e.preventDefault();
                                setFilters({ ...filters, minDiscount: '' });
                              }}
                              className="text-[10px] font-medium text-gray-500 underline underline-offset-2 hover:text-gray-900"
                            >
                              Clear
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Bottom padding for scroll */}
                  <div className="pb-6"></div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Products Grid */}
        <div className="min-w-0 flex-1 md:overflow-y-auto">
          <section ref={productsGridRef} className="p-0">
            {usedFuzzy && suggestedQuery && (
              <div className="mb-4 flex items-center justify-between rounded-xl border border-amber-100 bg-gradient-to-r from-amber-50 to-orange-50 p-4 text-sm text-amber-800 shadow-sm transition-all hover:shadow">
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-amber-500 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span>
                    Showing results for <span className="font-semibold italic text-amber-950">&quot;{suggestedQuery}&quot;</span> instead of <span className="line-through text-gray-400">&quot;{searchTerm}&quot;</span>. 
                    {searchTerm && (
                      <span> Did you mean <button onClick={() => {
                        setSearchTerm(suggestedQuery);
                      }} className="font-bold text-orange-600 underline decoration-orange-400 hover:text-orange-700 transition-colors">&quot;{suggestedQuery}&quot;</button>?</span>
                    )}
                  </span>
                </div>
                <span className="hidden sm:inline-block text-[9px] bg-amber-100 text-amber-800 font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">
                  Typo Corrected
                </span>
              </div>
            )}
            {filteredProducts.length === 0 ? (
              <div className="rounded-2xl border border-gray-100 bg-white py-12 text-center shadow-sm">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
                  <svg
                    className="h-8 w-8 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900">No products found</h3>
                {searchTerm ? (
                  <div className="mb-4">
                    <p className="mb-3 text-sm text-gray-500">
                      We couldn&apos;t find anything matching &quot;
                      <span className="font-medium text-gray-700">{searchTerm}</span>&quot;
                    </p>
                    <div className="mb-4 space-y-1 text-sm text-gray-500">
                      <p className="font-medium text-gray-600">Suggestions:</p>
                      <ul className="list-none space-y-0.5">
                        <li>Check the spelling of your search term</li>
                        <li>Try using more general keywords</li>
                        <li>Try searching for a product category or brand</li>
                      </ul>
                    </div>
                  </div>
                ) : (
                  <p className="mb-4 text-sm text-gray-500">
                    Try adjusting your filters or search terms
                  </p>
                )}
                <div className="flex flex-wrap justify-center gap-3">
                  <button
                    onClick={handleFilterReset}
                    className="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-800"
                  >
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
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                    Clear all filters
                  </button>
                  {searchTerm && (
                    <button
                      onClick={() => setSearchTerm('')}
                      className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                    >
                      Clear search
                    </button>
                  )}
                </div>

                {/* Popular Products Fallback */}
                {searchTerm && products.length === 0 && (
                  <div className="mt-8 border-t border-gray-100 pt-8">
                    <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-600">
                      Popular Products
                    </h4>
                    <PopularProductsFallback />
                  </div>
                )}
              </div>
            ) : (
              <>
                {/* Product Grid */}
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-2 sm:gap-3 md:grid-cols-3 md:gap-4 lg:grid-cols-4 xl:grid-cols-5">
                  {displayItems.map((product: any, _index: number) => {
                    // ── Bundle card variables ──────────────────────────────
                    const isBundle = !!product.isBundle;
                    const bundleCopiesInCart = isBundle
                      ? (() => {
                          if (!cart?.items?.length || !product.items?.length) return 0;
                          const counts = product.items.map((bItem: any) => {
                            const ci = cart.items.find(
                              (i: any) =>
                                i.bundleId === product._id &&
                                (i.product?._id || i.product) === bItem.productId
                            );
                            return ci ? Math.floor(ci.quantity / (bItem.quantity || 1)) : 0;
                          });
                          return Math.min(...counts);
                        })()
                      : 0;
                    const discountPercent =
                      !isBundle && product.mrp && product.mrp > product.price
                        ? Math.round(((product.mrp - product.price) / product.mrp) * 100)
                        : 0;

                    return (
                      <div
                        key={product._id}
                        onClick={() => { if (!isBundle) handleProductClick(product); }}
                        className={`group flex ${isBundle ? 'cursor-default' : 'cursor-pointer'} flex-col overflow-hidden rounded-lg border bg-white transition-all duration-200 hover:shadow-lg active:scale-[0.98] sm:rounded-xl border-gray-100 hover:border-gray-200`}
                      >
                        {/* Image Container */}
                        <div className="relative aspect-square overflow-hidden bg-gray-50">
                          <img
                            src={getImageUrlWithFallback(
                              product.displayImage || (product.images && product.images[0])
                            )}
                            alt={product.name}
                            loading="lazy"
                            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                            style={{
                              opacity: !isBundle && (!product.stock || product.stock === 0) ? 0.5 : 1,
                              filter: !isBundle && (!product.stock || product.stock === 0) ? 'grayscale(50%)' : 'none',
                            }}
                          />

                          {/* Badges */}
                          <div className="absolute left-2 top-2 flex flex-col gap-1">
                            {!isBundle && (!product.stock || product.stock === 0) && (
                              <span className="rounded bg-gray-900/90 px-2 py-0.5 text-[9px] font-bold uppercase text-white backdrop-blur-sm">
                                Sold Out
                              </span>
                            )}
                            {!isBundle && product.bestSeller && product.stock > 0 && (
                              <span className="rounded bg-amber-400 px-2 py-0.5 text-[9px] font-bold uppercase text-amber-900">
                                Bestseller
                              </span>
                            )}
                            {!isBundle && product.isNew && product.stock > 0 && (
                              <span className="rounded bg-emerald-500 px-2 py-0.5 text-[9px] font-bold uppercase text-white">
                                New
                              </span>
                            )}
                            {!isBundle && product.previouslyBought && (
                              <span className="rounded bg-indigo-100 px-2 py-0.5 text-[9px] font-bold uppercase text-indigo-700">
                                Previously Bought
                              </span>
                            )}
                          </div>

                          {/* Wishlist Button — hidden for bundles */}
                          {!isBundle && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleWishlistToggle(product._id, product.name);
                            }}
                            className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-white/90 opacity-0 shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:shadow-md group-hover:opacity-100"
                          >
                            <svg
                              className={`h-4 w-4 transition-colors ${wishlistedIds.has(product._id) ? 'text-rose-500' : 'text-gray-600 hover:text-rose-500'}`}
                              fill={wishlistedIds.has(product._id) ? 'currentColor' : 'none'}
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                              />
                            </svg>
                          </button>
                          )}

                           {/* Quick Add Button / Quantity Selector */}
                           {(isBundle ? true : product.stock > 0) && (() => {
                             // ── Bundle counter ────────────────────────────
                             if (isBundle) {
                               if (bundleCopiesInCart > 0) {
                                 return (
                                   <div
                                     onClick={(e) => e.stopPropagation()}
                                     className="absolute bottom-0 left-0 right-0 flex items-stretch bg-gray-900/95 backdrop-blur-sm"
                                   >
                                     <button
                                       onClick={async (e) => {
                                         e.stopPropagation();
                                         // Decrement all bundle items by their spec quantity
                                         for (const bItem of (product.items || [])) {
                                           const ci = cart?.items?.find(
                                             (i: any) =>
                                               i.bundleId === product._id &&
                                               (i.product?._id || i.product) === bItem.productId
                                           );
                                           if (!ci) continue;
                                           const newQty = ci.quantity - (bItem.quantity || 1);
                                           try {
                                             if (newQty <= 0) await removeFromCart(ci._id);
                                             else await updateQuantity(ci._id, newQty);
                                           } catch { /* silent */ }
                                         }
                                       }}
                                       className="flex w-10 flex-shrink-0 items-center justify-center py-2.5 text-lg font-bold text-white hover:bg-white/10 transition-colors sm:w-12"
                                       aria-label="Remove one bundle"
                                     >
                                       −
                                     </button>
                                     <span className="flex flex-1 items-center justify-center text-sm font-bold text-white">{bundleCopiesInCart}</span>
                                     <button
                                       onClick={async (e) => {
                                         e.stopPropagation();
                                         try {
                                           await api.post(`/bundles/${product._id}/add-to-cart`);
                                           await fetchCart();
                                           toast.success('Bundle added!');
                                         } catch (err: any) {
                                           toast.error(err?.response?.data?.detail || 'Could not add bundle');
                                         }
                                       }}
                                       className="flex w-10 flex-shrink-0 items-center justify-center py-2.5 text-lg font-bold text-white active:bg-white/20 hover:bg-white/10 transition-colors sm:w-12"
                                       aria-label="Add one bundle"
                                     >
                                       +
                                     </button>
                                   </div>
                                 );
                               }
                               // First-time add for bundle
                               return (
                                 <button
                                   onClick={async (e) => {
                                     e.stopPropagation();
                                     try {
                                       await api.post(`/bundles/${product._id}/add-to-cart`);
                                       await fetchCart();
                                       toast.success('Bundle added to cart!');
                                     } catch (err: any) {
                                       toast.error(err?.response?.data?.detail || 'Could not add bundle');
                                     }
                                   }}
                                   className="absolute bottom-0 left-0 right-0 flex items-center justify-center gap-1 bg-gray-900/95 py-2.5 text-[10px] font-semibold uppercase tracking-wide text-white opacity-100 sm:opacity-0 sm:group-hover:opacity-100 backdrop-blur-sm transition-all duration-300 sm:text-xs md:translate-y-full md:group-hover:translate-y-0"
                                 >
                                   <svg className="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                     <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                                   </svg>
                                   <span className="hidden xs:inline sm:hidden md:inline">Add to Cart</span>
                                   <span className="xs:hidden sm:inline md:hidden">Add</span>
                                 </button>
                               );
                             }

                             // ── Regular product counter ───────────────────
                              const cartItem = cart?.items?.find((item: any) => {
                                const pId = item.product?._id || item.product || item._id;
                                return pId === product._id;
                              });
                              const quantityInCart = cartItem ? cartItem.quantity : 0;

                              if (quantityInCart > 0) {
                                 return (
                                   <div
                                     onClick={(e) => e.stopPropagation()}
                                     className="absolute bottom-0 left-0 right-0 flex items-stretch bg-gray-900/95 backdrop-blur-sm"
                                   >
                                     <button
                                       onClick={async (e) => {
                                         e.stopPropagation();
                                         if (!cartItem) return;
                                         try {
                                           if (quantityInCart === 1) {
                                             await removeFromCart(cartItem!._id);
                                           } else {
                                             await updateQuantity(cartItem!._id, quantityInCart - 1);
                                           }
                                         } catch (_error) {
                                           toast.error('Failed to update quantity');
                                         }
                                       }}
                                       className="flex w-10 flex-shrink-0 items-center justify-center py-2.5 text-lg font-bold text-white active:bg-white/20 hover:bg-white/10 transition-colors sm:w-12"
                                       aria-label="Decrease quantity"
                                     >
                                       −
                                     </button>
                                     <span className="flex flex-1 items-center justify-center text-sm font-bold text-white">
                                       {quantityInCart}
                                     </span>
                                     <button
                                       onClick={async (e) => {
                                         e.stopPropagation();
                                         if (!cartItem) return;
                                         try {
                                           await updateQuantity(cartItem!._id, quantityInCart + 1);
                                         } catch (_error) {
                                           toast.error('Failed to update quantity');
                                         }
                                       }}
                                       className="flex w-10 flex-shrink-0 items-center justify-center py-2.5 text-lg font-bold text-white active:bg-white/20 hover:bg-white/10 transition-colors sm:w-12"
                                       aria-label="Increase quantity"
                                     >
                                       +
                                     </button>
                                   </div>
                                 );
                               }

                              return (
                               <button
                                 onClick={(e) => {
                                   e.stopPropagation();
                                   handleAddToCart(product._id, 1, product.name);
                                 }}
                                 className="absolute bottom-0 left-0 right-0 flex items-center justify-center gap-1 bg-gray-900/95 py-2.5 text-[10px] font-semibold uppercase tracking-wide text-white opacity-100 sm:opacity-0 sm:group-hover:opacity-100 backdrop-blur-sm transition-all duration-300 sm:text-xs md:translate-y-full md:group-hover:translate-y-0"
                               >
                                 <svg
                                   className="h-3.5 w-3.5 flex-shrink-0"
                                   fill="none"
                                   viewBox="0 0 24 24"
                                   stroke="currentColor"
                                   strokeWidth="2"
                                 >
                                   <path
                                     strokeLinecap="round"
                                     strokeLinejoin="round"
                                     d="M12 4v16m8-8H4"
                                   />
                                 </svg>
                                 <span className="hidden xs:inline sm:hidden md:inline">Add to Cart</span>
                                 <span className="xs:hidden sm:inline md:hidden">Add</span>
                               </button>
                              );
                           })()}
 
                           {(!isBundle && (!product.stock || product.stock <= 0)) && (
                             <button
                               onClick={(e) => {
                                 e.stopPropagation();
                                 handleNotifyMe(product._id, product.name);
                               }}
                               className="absolute bottom-0 left-0 right-0 flex items-center justify-center gap-1.5 bg-[#ff3f6c] py-2 text-[10px] font-semibold uppercase tracking-wide text-white opacity-0 backdrop-blur-sm transition-all duration-300 group-hover:opacity-100 sm:py-2.5 sm:text-xs md:translate-y-full md:group-hover:translate-y-0"
                             >
                               <svg
                                 className="h-3.5 w-3.5 sm:h-4 sm:w-4"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                                 strokeWidth="2.5"
                               >
                                 <path
                                   strokeLinecap="round"
                                   strokeLinejoin="round"
                                   d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                                 />
                               </svg>
                               Notify Me
                             </button>
                           )}
                         </div>

                        {/* Product Info */}
                        <div className="flex flex-1 flex-col p-2 sm:p-3">
                          {/* Brand / Bundle label */}
                          <p className="mb-0.5 truncate text-[9px] font-medium uppercase tracking-wide text-gray-400 sm:mb-1 sm:text-[10px]">
                            {isBundle ? (product.brand || 'Bundle') : (product.brand || 'Stationery Junction')}
                          </p>

                          {/* Name */}
                          <h3 className="mb-1.5 line-clamp-2 flex-1 text-xs font-medium leading-snug text-gray-900 sm:mb-2 sm:text-sm">
                            {product.name}
                          </h3>

                          {/* Price */}
                          <div className="flex flex-wrap items-baseline gap-1 sm:gap-2">
                            <span className="text-sm font-bold text-gray-900 sm:text-base">
                              ₹{(product.price || product.mrp || 0).toLocaleString()}
                            </span>
                            {isBundle && product.totalMrp && product.totalMrp > product.price && (
                              <>
                                <span className="text-[10px] text-gray-400 line-through sm:text-xs">
                                  ₹{product.totalMrp.toLocaleString()}
                                </span>
                                <span className="text-[10px] font-semibold text-emerald-600 sm:text-xs">
                                  Save {product.savingsPercent}%
                                </span>
                              </>
                            )}
                            {!isBundle && product.mrp && product.mrp > product.price && (
                              <>
                                <span className="text-[10px] text-gray-400 line-through sm:text-xs">
                                  ₹{product.mrp.toLocaleString()}
                                </span>
                                <span className="text-[10px] font-semibold text-emerald-600 sm:text-xs">
                                  {discountPercent}%
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {totalPages > 1 && products.length > 0 && (
                  <div className="mt-6 flex items-center justify-center gap-4">
                    <button
                      type="button"
                      onClick={() => handleCatalogPageChange(page - 1)}
                      disabled={page === 1 || loading}
                      className="rounded-lg bg-gray-600 px-4 py-2 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <span className="text-sm text-gray-600">
                      Page {page} of {totalPages}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCatalogPageChange(page + 1)}
                      disabled={page === totalPages || loading}
                      className="rounded-lg bg-gray-600 px-4 py-2 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </div>

      {/* Back to Top Button - Shows on scroll down */}
      {showBackToTop && (
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="animate-fade-in-up fixed bottom-24 right-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-gray-900 text-white shadow-lg transition-all duration-300 hover:bg-gray-800 md:bottom-8"
          aria-label="Back to top"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        </button>
      )}

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => {
          setShowAuthModal(false);
          setPendingWishlistProductId(null);
          setPendingWishlistProductName(null);
        }}
        redirectOnSuccess={false}
        onSuccess={async () => {
          if (pendingWishlistProductId) {
            try {
              await api.post('/wishlist', { productId: pendingWishlistProductId });
              setWishlistedIds((prev) => new Set(prev).add(pendingWishlistProductId));
              toast.success(`${pendingWishlistProductName || 'Item'} added to wishlist`);
            // eslint-disable-next-line unused-imports/no-unused-vars
            } catch (error) {
              toast.error('Failed to add to wishlist');
            }
          }
        }}
      />
    </div>
  );
}
