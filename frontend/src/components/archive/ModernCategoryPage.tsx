'use client';

import React, { useState, useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import ModernHeader from './ModernHeader';
import ModernFilters from './ModernFilters';
import ModernProductCard from './ModernProductCard';
import { SortIcon } from '../Icons/HeaderIcons';
import api from '@/utils/api';
import styles from './ModernCategoryPage.module.css';

interface Product {
  _id: string;
  name: string;
  description?: string;
  price: number;
  originalPrice?: number;
  discount?: number;
  images: string[];
  category: string;
  brand: string;
  stock: number;
  rating?: number;
  reviews?: number;
  isAd?: boolean;
  badge?: string;
}

interface FilterSection {
  id: string;
  title: string;
  type: 'checkbox' | 'radio' | 'range' | 'search';
  options?: { id: string; name: string; count?: number }[];
  min?: number;
  max?: number;
  unit?: string;
}

const PAGE_SIZE = 24;

export default function ModernCategoryPage() {
  const { theme } = useTheme();
  const { user } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState('recommended');
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [queryGen, setQueryGen] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const skipFilterBumpRef = useRef(true);

  // Extract category from pathname
  const pathSegments = pathname.split('/');
  const category = pathSegments[pathSegments.length - 1] || 'all';
  const categoryName = category.charAt(0).toUpperCase() + category.slice(1).replace('-', ' ');

  useEffect(() => {
    if (skipFilterBumpRef.current) {
      skipFilterBumpRef.current = false;
      return;
    }
    setQueryGen((g) => g + 1);
    setCurrentPage(1);
  }, [category, sortBy, activeFilters]);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams();

        params.append('page', String(currentPage));
        params.append('limit', String(PAGE_SIZE));

        if (category !== 'all') {
          params.append('category', category);
        }

        const sortParam =
          sortBy === 'recommended'
            ? 'popular'
            : sortBy === 'price-low'
              ? 'price_asc'
              : sortBy === 'price-high'
                ? 'price_desc'
                : sortBy === 'newest'
                  ? 'newest'
                  : sortBy === 'popular'
                    ? 'popular'
                    : sortBy === 'rating'
                      ? 'popular'
                      : 'popular';
        params.append('sort', sortParam);

        Object.entries(activeFilters).forEach(([key, value]) => {
          if (Array.isArray(value) && value.length > 0) {
            params.append(key, value.join(','));
          } else if (value && typeof value === 'object') {
            if (value.min) params.append(`${key}_min`, value.min);
            if (value.max) params.append(`${key}_max`, value.max);
          } else if (value && value !== 'all') {
            params.append(key, value);
          }
        });

        const endpoint = user ? '/products' : '/products/public';
        const role = user?.effectiveRole || user?.role || 'customer';
        if (!user) {
          params.append('role', role);
        }

        const response = await api.get(endpoint, { params });
        const list = response.data.products || response.data || [];
        setProducts(list);
        setTotalCount(response.data.totalCount ?? list.length);
      } catch (error) {
        console.error('Error fetching products:', error);
        setProducts([]);
        setTotalCount(0);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [queryGen, currentPage, category, sortBy, activeFilters, user]);

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  const handleCatalogPageChange = (newPage: number) => {
    if (loading || newPage < 1 || newPage > totalPages || newPage === currentPage) return;
    setCurrentPage(newPage);
  };

  const handleFilterChange = (filterId: string, value: any) => {
    setActiveFilters((prev) => ({
      ...prev,
      [filterId]: value,
    }));
  };

  const handleClearAllFilters = () => {
    setActiveFilters({});
  };

  const getUserBasePath = () => {
    if (!user) return '/';
    if (user.role === 'customer') return '/customer';
    if (user.role === 'wholesaler') return '/wholesaler';
    if (user.role === 'valet') return '/valet';
    return '/';
  };

  // Mock filter data - in real app, this would come from API
  const filters: FilterSection[] = [
    {
      id: 'gender',
      title: 'Gender',
      type: 'radio',
      options: [
        { id: 'men', name: 'Men', count: 1234 },
        { id: 'women', name: 'Women', count: 2345 },
        { id: 'boys', name: 'Boys', count: 567 },
        { id: 'girls', name: 'Girls', count: 890 },
      ],
    },
    {
      id: 'categories',
      title: 'Categories',
      type: 'checkbox',
      options: [
        { id: 'lipstick', name: 'Lipstick', count: 18410 },
        { id: 'foundation', name: 'Foundation', count: 12345 },
        { id: 'mascara', name: 'Mascara', count: 8765 },
        { id: 'eyeliner', name: 'Eyeliner', count: 6543 },
        { id: 'nail-polish', name: 'Nail Polish', count: 4321 },
        { id: 'face-wash', name: 'Face Wash', count: 9876 },
        { id: 'moisturizer', name: 'Moisturizer', count: 7654 },
        { id: 'sunscreen', name: 'Sunscreen', count: 5432 },
      ],
    },
    {
      id: 'brand',
      title: 'Brand',
      type: 'search',
    },
    {
      id: 'price',
      title: 'Price',
      type: 'range',
      min: 0,
      max: 10000,
      unit: '₹',
    },
    {
      id: 'rating',
      title: 'Customer Rating',
      type: 'checkbox',
      options: [
        { id: '4', name: '4★ & above', count: 1234 },
        { id: '3', name: '3★ & above', count: 2345 },
        { id: '2', name: '2★ & above', count: 3456 },
        { id: '1', name: '1★ & above', count: 4567 },
      ],
    },
  ];

  const sortOptions = [
    { value: 'recommended', label: 'Recommended' },
    { value: 'price-low', label: 'Price: Low to High' },
    { value: 'price-high', label: 'Price: High to Low' },
    { value: 'newest', label: 'Newest First' },
    { value: 'popular', label: 'Popular' },
    { value: 'rating', label: 'Customer Rating' },
  ];

  return (
    <div className={styles.modernCategoryPage}>
      <ModernHeader />

      {/* Breadcrumbs */}
      <div className={styles.breadcrumbs}>
        <div className={styles.container}>
          <button onClick={() => router.push(getUserBasePath())} className={styles.breadcrumbLink}>
            Home
          </button>
          <span className={styles.breadcrumbSeparator}>/</span>
          <span className={styles.breadcrumbCurrent}>{categoryName}</span>
        </div>
      </div>

      <div className={styles.container}>
        <div className={styles.categoryContent}>
          {/* Filters Sidebar */}
          <aside
            className={`${styles.filtersSidebar} ${showMobileFilters ? styles.mobileOpen : ''}`}
          >
            <ModernFilters
              filters={filters}
              activeFilters={activeFilters}
              onFilterChange={handleFilterChange}
              onClearAll={handleClearAllFilters}
            />
          </aside>

          {/* Main Content */}
          <main className={styles.mainContent}>
            {/* Header */}
            <div className={styles.contentHeader}>
              <div className={styles.headerTop}>
                <h1 className={styles.pageTitle}>{categoryName}</h1>
                <span className={styles.productCount}>{products.length} products</span>
              </div>

              <div className={styles.headerControls}>
                {/* Mobile Filter Toggle */}
                <button
                  className={styles.mobileFilterToggle}
                  onClick={() => setShowMobileFilters(!showMobileFilters)}
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="4" y1="21" x2="4" y2="14" />
                    <line x1="4" y1="10" x2="4" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12" y2="3" />
                    <line x1="20" y1="21" x2="20" y2="16" />
                    <line x1="20" y1="12" x2="20" y2="3" />
                    <line x1="1" y1="14" x2="7" y2="14" />
                    <line x1="9" y1="8" x2="15" y2="8" />
                    <line x1="17" y1="16" x2="23" y2="16" />
                  </svg>
                  Filters
                </button>

                {/* Sort Dropdown */}
                <div className={styles.sortDropdown}>
                  <label className={styles.sortLabel}>
                    <SortIcon />
                    Sort by:
                  </label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className={styles.sortSelect}
                  >
                    {sortOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* View Toggle */}
                <div className={styles.viewToggle}>
                  <button
                    className={`${styles.viewButton} ${viewMode === 'grid' ? styles.active : ''}`}
                    onClick={() => setViewMode('grid')}
                  >
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <rect x="3" y="3" width="7" height="7" />
                      <rect x="14" y="3" width="7" height="7" />
                      <rect x="14" y="14" width="7" height="7" />
                      <rect x="3" y="14" width="7" height="7" />
                    </svg>
                  </button>
                  <button
                    className={`${styles.viewButton} ${viewMode === 'list' ? styles.active : ''}`}
                    onClick={() => setViewMode('list')}
                  >
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <line x1="8" y1="6" x2="21" y2="6" />
                      <line x1="8" y1="12" x2="21" y2="12" />
                      <line x1="8" y1="18" x2="21" y2="18" />
                      <line x1="3" y1="6" x2="3.01" y2="6" />
                      <line x1="3" y1="12" x2="3.01" y2="12" />
                      <line x1="3" y1="18" x2="3.01" y2="18" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Products Grid */}
            <div className={styles.productsSection}>
              {loading ? (
                <div className={styles.loadingState}>
                  <div className={styles.spinner}></div>
                  <p>Loading products...</p>
                </div>
              ) : products.length === 0 ? (
                <div className={styles.emptyState}>
                  <svg
                    width="64"
                    height="64"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.35-4.35" />
                  </svg>
                  <h3>No products found</h3>
                  <p>Try adjusting your filters or search terms</p>
                  <button
                    className={styles.clearFiltersBtn}
                    onClick={handleClearAllFilters}
                    style={{ background: theme.gradient }}
                  >
                    Clear all filters
                  </button>
                </div>
              ) : (
                <>
                  <div className={`${styles.productsGrid} ${styles[viewMode]}`}>
                    {products.map((product) => (
                      <ModernProductCard key={product._id} product={product} viewMode={viewMode} />
                    ))}
                  </div>
                  {totalPages > 1 && (
                    <div className="mt-6 flex items-center justify-center gap-4">
                      <button
                        type="button"
                        onClick={() => handleCatalogPageChange(currentPage - 1)}
                        disabled={currentPage === 1 || loading}
                        className="rounded-lg bg-gray-600 px-4 py-2 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-600">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCatalogPageChange(currentPage + 1)}
                        disabled={currentPage === totalPages || loading}
                        className="rounded-lg bg-gray-600 px-4 py-2 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </main>
        </div>
      </div>

      {/* Mobile Filter Overlay */}
      {showMobileFilters && (
        <>
          <div className={styles.mobileFilterOverlay} onClick={() => setShowMobileFilters(false)} />
          <div className={styles.mobileFilterPanel}>
            <div className={styles.mobileFilterHeader}>
              <h2>Filters</h2>
              <button
                onClick={() => setShowMobileFilters(false)}
                className={styles.closeMobileFilters}
              >
                ×
              </button>
            </div>
            <ModernFilters
              filters={filters}
              activeFilters={activeFilters}
              onFilterChange={handleFilterChange}
              onClearAll={handleClearAllFilters}
            />
          </div>
        </>
      )}
    </div>
  );
}
