'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { useWishlist } from '@/context/WishlistContext';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import { addGuestCartItem } from '@/utils/guestStore';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { trackAddToWishlist, trackRemoveFromWishlist, getSessionId } from '@/utils/analytics';
import styles from './ModernProductCatalog.module.css';
import AuthModal from '@/components/AuthModal';
import { toast } from 'react-toastify';

interface Product {
  _id: string;
  name: string;
  description?: string;
  price: number;
  images: string[];
  category: string;
  brand: string;
  stock: number;
  rating?: number;
  reviews?: number;
  discount?: number;
}

interface ModernProductCatalogProps {
  products?: Product[];
  loading?: boolean;
  showFilters?: boolean;
  itemsPerPage?: number;
}

export default function ModernProductCatalog({
  products: initialProducts,
  loading: initialLoading = false,
  showFilters = true,
  itemsPerPage = 12,
}: ModernProductCatalogProps) {
  const { theme } = useTheme();
  const { addToWishlist, isInWishlist, removeFromWishlist } = useWishlist();
  const { user } = useAuth();
  const router = useRouter();

  const [products, setProducts] = useState<Product[]>(initialProducts || []);
  const [loading, setLoading] = useState(initialLoading);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>(products);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [priceRange, setPriceRange] = useState({ min: 0, max: 10000 });
  const [sortBy, setSortBy] = useState('featured');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingWishlistProductId, setPendingWishlistProductId] = useState<string | null>(null);
  const [pendingWishlistProductName, setPendingWishlistProductName] = useState<string | null>(null);

  // Fetch products if not provided
  useEffect(() => {
    if (!initialProducts) {
      fetchProducts();
    }
  }, [initialProducts]);

  // Apply filters
  useEffect(() => {
    let filtered = products;

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter((product) => product.category === selectedCategory);
    }

    // Brand filter
    if (selectedBrand !== 'all') {
      filtered = filtered.filter((product) => product.brand === selectedBrand);
    }

    // Price filter
    filtered = filtered.filter(
      (product) => product.price >= priceRange.min && product.price <= priceRange.max
    );

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (product) =>
          product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          product.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Sort
    switch (sortBy) {
      case 'price-low':
        filtered.sort((a, b) => a.price - b.price);
        break;
      case 'price-high':
        filtered.sort((a, b) => b.price - a.price);
        break;
      case 'name':
        filtered.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case 'rating':
        filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0));
        break;
      default:
        // featured - keep original order
        break;
    }

    setFilteredProducts(filtered);
    setCurrentPage(1);
  }, [products, selectedCategory, selectedBrand, priceRange, sortBy, searchTerm]);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/products');
      setProducts(response.data.products || response.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (productId: string) => {
    try {
      if (user) {
        await api.post('/cart', { productId, quantity: 1 });
      } else {
        const product = products.find((p) => p._id === productId);
        addGuestCartItem(productId, 1, product);
      }
    } catch (error) {
      console.error('Error adding to cart:', error);
    }
  };

  const handleWishlistToggle = async (productId: string, productName?: string) => {
    try {
      if (isInWishlist(productId)) {
        trackRemoveFromWishlist({ productId, productName, source: 'catalog' });
        await removeFromWishlist(productId);
      } else {
        if (!user) {
          setPendingWishlistProductId(productId);
          setPendingWishlistProductName(productName || null);
          setShowAuthModal(true);
          return;
        }
        trackAddToWishlist({ productId, productName, source: 'catalog' });
        await addToWishlist(productId, getSessionId());
      }
    } catch (error) {
      console.error('Error toggling wishlist:', error);
    }
  };

  const handleProductClick = (productId: string) => {
    const basePath = user
      ? user.role === 'customer'
        ? '/customer'
        : user.role === 'wholesaler'
          ? '/wholesaler'
          : '/'
      : '/';
    router.push(`${basePath}/product/${productId}`);
  };

  // Get unique categories and brands
  const categories = ['all', ...Array.from(new Set(products.map((p) => p.category)))];
  const brands = ['all', ...Array.from(new Set(products.map((p) => p.brand)))];

  // Pagination
  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedProducts = filteredProducts.slice(startIndex, startIndex + itemsPerPage);

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner}></div>
        <p>Loading products...</p>
      </div>
    );
  }

  return (
    <div className={styles.modernProductCatalog}>
      {/* Header */}
      <div className={styles.catalogHeader}>
        <h1>Products</h1>
        <div className={styles.headerControls}>
          <div className={styles.searchBar}>
            <input
              type="text"
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={styles.searchInput}
            />
          </div>
          <div className={styles.viewToggle}>
            <button
              className={`${styles.viewButton} ${viewMode === 'grid' ? styles.active : ''}`}
              onClick={() => setViewMode('grid')}
            >
              Grid
            </button>
            <button
              className={`${styles.viewButton} ${viewMode === 'list' ? styles.active : ''}`}
              onClick={() => setViewMode('list')}
            >
              List
            </button>
          </div>
        </div>
      </div>

      <div className={styles.catalogContent}>
        {/* Filters Sidebar */}
        {showFilters && (
          <div className={styles.filtersSidebar}>
            <div className={styles.filterSection}>
              <h3>Category</h3>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className={styles.filterSelect}
              >
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category}
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.filterSection}>
              <h3>Brand</h3>
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className={styles.filterSelect}
              >
                {brands.map((brand) => (
                  <option key={brand} value={brand}>
                    {brand === 'all' ? 'All Brands' : brand}
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.filterSection}>
              <h3>Price Range</h3>
              <div className={styles.priceRange}>
                <input
                  type="number"
                  placeholder="Min"
                  value={priceRange.min}
                  onChange={(e) =>
                    setPriceRange((prev) => ({ ...prev, min: Number(e.target.value) }))
                  }
                  className={styles.priceInput}
                />
                <span>-</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={priceRange.max}
                  onChange={(e) =>
                    setPriceRange((prev) => ({ ...prev, max: Number(e.target.value) }))
                  }
                  className={styles.priceInput}
                />
              </div>
            </div>

            <div className={styles.filterSection}>
              <h3>Sort By</h3>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className={styles.filterSelect}
              >
                <option value="featured">Featured</option>
                <option value="price-low">Price: Low to High</option>
                <option value="price-high">Price: High to Low</option>
                <option value="name">Name</option>
                <option value="rating">Rating</option>
              </select>
            </div>
          </div>
        )}

        {/* Products Grid */}
        <div className={styles.productsContainer}>
          {paginatedProducts.length === 0 ? (
            <div className={styles.noProducts}>
              <p>No products found matching your criteria.</p>
            </div>
          ) : (
            <div className={`${styles.productsGrid} ${styles[viewMode]}`}>
              {paginatedProducts.map((product) => (
                <div
                  key={product._id}
                  className={styles.productCard}
                  onClick={() => handleProductClick(product._id)}
                >
                  <div className={styles.productImage}>
                    {product.images?.[0] ? (
                      <img
                        src={
                          getImageUrlWithFallback(product.images[0])
                        }
                        alt={product.name}
                        className={styles.productImg}
                      />
                    ) : (
                      <div className={styles.noImage}>No Image</div>
                    )}
                    {product.discount && (
                      <span className={styles.discountBadge}>-{product.discount}%</span>
                    )}
                  </div>

                  <div className={styles.productInfo}>
                    <h3 className={styles.productName}>{product.name}</h3>
                    <p className={styles.productBrand}>{product.brand}</p>

                    <div className={styles.productPrice}>
                      <span className={styles.currentPrice}>
                        ₹
                        {product.discount
                          ? (product.price * (1 - product.discount / 100)).toFixed(2)
                          : product.price.toFixed(2)}
                      </span>
                      {product.discount && (
                        <span className={styles.originalPrice}>₹{product.price.toFixed(2)}</span>
                      )}
                    </div>

                    {product.rating && (
                      <div className={styles.productRating}>
                        <span className={styles.stars}>
                          {'★'.repeat(Math.floor(product.rating))}
                          {'☆'.repeat(5 - Math.floor(product.rating))}
                        </span>
                        <span className={styles.ratingCount}>({product.reviews || 0})</span>
                      </div>
                    )}

                    <div className={styles.productActions}>
                      <button
                        className={styles.addToCartBtn}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToCart(product._id);
                        }}
                        style={{ background: theme.gradient }}
                      >
                        Add to Cart
                      </button>
                      <button
                        className={`${styles.wishlistBtn} ${isInWishlist(product._id) ? styles.inWishlist : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleWishlistToggle(product._id, product.name);
                        }}
                      >
                        {isInWishlist(product._id) ? '❤️' : '🤍'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                className={styles.paginationButton}
                onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </button>

              <span className={styles.pageInfo}>
                Page {currentPage} of {totalPages}
              </span>

              <button
                className={styles.paginationButton}
                onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
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
              await api.post('/wishlist', { productId: pendingWishlistProductId, sessionId: getSessionId() });
              trackAddToWishlist({
                productId: pendingWishlistProductId,
                productName: pendingWishlistProductName || undefined,
                source: 'catalog',
              });
              toast.success('Added to wishlist');
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
