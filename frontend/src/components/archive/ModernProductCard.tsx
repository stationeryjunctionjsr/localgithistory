'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { useTheme } from '@/context/ThemeContext';
// import { useWishlist } from '@/context/WishlistContext';
import { useWishlistStore } from '@/store/wishlistStore';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import { addGuestCartItem } from '@/utils/guestStore';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { toast } from 'react-toastify';
import {
  recordEvent,
  trackEcommerceEvent,
  trackAddToWishlist,
  trackRemoveFromWishlist,
  getSessionId,
} from '@/utils/analytics';
import { useShare } from '@/hooks/useShare';
import styles from './ModernProductCard.module.css';
import QuickVariantModal from '../QuickVariantModal';
import AuthModal from '@/components/AuthModal';
import { logger } from '@/utils/logger';

// Custom SVG Components
// eslint-disable-next-line unused-imports/no-unused-vars
const StarIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);

const StarIconSolid = ({ className }: { className?: string }) => (
  <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);

const HeartIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);

const HeartIconSolid = ({ className }: { className?: string }) => (
  <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);

const ShoppingBagIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
    <line x1="3" y1="6" x2="21" y2="6" />
    <path d="M16 10a4 4 0 0 1-8 0" />
  </svg>
);

const ShareIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <circle cx="18" cy="5" r="3" />
    <circle cx="6" cy="12" r="3" />
    <circle cx="18" cy="19" r="3" />
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
  </svg>
);

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
  customerPurchaseCount?: number;
  wholesalerPurchaseCount?: number;
  variations?: any[];
}

interface ModernProductCardProps {
  product: Product;
  viewMode?: 'grid' | 'list';
  showQuickActions?: boolean;
  onProductClick?: (productId: string) => void;
  className?: string;
}

export default function ModernProductCard({
  product,
  viewMode = 'grid',
  showQuickActions = true,
  onProductClick,
  className = '',
}: ModernProductCardProps) {
  const { theme } = useTheme();
  // const { addToWishlist, isInWishlist, removeFromWishlist } = useWishlist();
  const addToWishlist      = useWishlistStore((s) => s.addToWishlist);
  const isInWishlist       = useWishlistStore((s) => s.isInWishlist);
  const removeFromWishlist = useWishlistStore((s) => s.removeFromWishlist);
  const { share } = useShare();
  const { user } = useAuth();
  const router = useRouter();

  const [isHovered, setIsHovered] = useState(false);
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  const [isWishlistLoading, setIsWishlistLoading] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showVariantModal, setShowVariantModal] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingWishlistAction, setPendingWishlistAction] = useState(false);

  // Auto-rotate images on hover
  React.useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isHovered && product.images && product.images.length > 1) {
      interval = setInterval(() => {
        setCurrentImageIndex((prev) => (prev + 1) % product.images.length);
      }, 1000);
    } else if (!isHovered) {
      setCurrentImageIndex(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isHovered, product.images]);

  const discountPercentage =
    product.discount ||
    (product.originalPrice
      ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
      : 0);

  const handleProductClick = () => {
    trackEcommerceEvent('view_item', {
      value: product.price,
      items: [
        {
          item_id: product._id,
          item_name: product.name,
          price: product.price,
          item_brand: product.brand,
          item_category: product.category,
          quantity: 1,
        },
      ],
    });
    recordEvent({ type: 'product_click', payload: { productId: product._id, name: product.name } });
    if (onProductClick) {
      onProductClick(product._id);
    } else {
      const basePath = user
        ? user.role === 'customer'
          ? '/customer'
          : user.role === 'wholesaler'
            ? '/wholesaler'
            : '/'
        : '/';
      router.push(`${basePath}/product/${product._id}`);
    }
  };

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.stopPropagation();

    // Check for variants
    if (product.variations && product.variations.length > 0) {
      setShowVariantModal(true);
      return;
    }

    setIsAddingToCart(true);
    try {
      const cartItem = {
        productId: product._id,
        quantity: 1,
        sessionId: getSessionId(),
      };

      if (user) {
        await api.post('/cart', cartItem);
      } else {
        addGuestCartItem(product._id, 1, product);
      }

      toast.success('Added to cart');
      trackEcommerceEvent('add_to_cart', {
        value: product.price,
        items: [
          {
            item_id: product._id,
            item_name: product.name,
            price: product.price,
            item_brand: product.brand,
            item_category: product.category,
            quantity: 1,
          },
        ],
      });
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      toast.error('Failed to add to cart');
    } finally {
      setIsAddingToCart(false);
    }
  };

  const handleVariantAddToCart = async (variant: any, quantity: number) => {
    setIsAddingToCart(true);
    try {
      const cartItem = {
        productId: product._id,
        variantId: variant?._id,
        quantity,
        sessionId: getSessionId(),
      };

      if (user) {
        await api.post('/cart', cartItem);
      } else {
        addGuestCartItem(product._id, quantity, {
          ...product,
          price: variant?.price || product.price,
          images: variant?.images || product.images,
        });
      }

      toast.success('Added to cart');
      setShowVariantModal(false);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      toast.error('Failed to add to cart');
    } finally {
      setIsAddingToCart(false);
    }
  };

  const handleWishlistToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsWishlistLoading(true);

    try {
      if (isInWishlist(product._id)) {
        trackRemoveFromWishlist({
          productId: product._id,
          productName: product.name,
          source: 'product_card',
        });
        await removeFromWishlist(product._id);
      } else {
        if (!user) {
          setPendingWishlistAction(true);
          setShowAuthModal(true);
          return;
        }
        trackAddToWishlist({
          productId: product._id,
          productName: product.name,
          source: 'product_card',
        });
        await addToWishlist(product._id, getSessionId());
      }
    } catch (error) {
      logger.error('Error toggling wishlist:', error);
    } finally {
      setIsWishlistLoading(false);
    }
  };

  const getProductUrl = () => {
    const base = typeof window !== 'undefined' ? window.location.origin : '';
    const path = user?.role === 'wholesaler' ? '/wholesaler' : '/customer';
    return `${base}${path}/product/${product._id}`;
  };

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    share({
      title: product.name,
      text: `${product.name} - ₹${product.price}`,
      url: getProductUrl(),
    });
  };

  const handleImageError = () => {
    setImageError(true);
  };

  const handleImageHover = (index: number) => {
    if (product.images && product.images.length > 1) {
      setCurrentImageIndex(index);
    }
  };

  const renderRating = () => {
    if (!product.rating) return null;

    return (
      <div className={styles.productRatingBadge}>
        <span className={styles.ratingValue}>{product.rating.toFixed(1)}</span>
        <StarIconSolid className={styles.ratingStarIcon} />
        <span className={styles.divider}>|</span>
        <span className={styles.reviewCount}>
          {product.reviews &&
            (product.reviews >= 1000 ? `${(product.reviews / 1000).toFixed(1)}k` : product.reviews)}
        </span>
      </div>
    );
  };

  const renderPurchaseCount = () => {
    let count = 0;
    let label = '';

    if (user?.role === 'wholesaler') {
      count = product.wholesalerPurchaseCount || 0;
      label = 'wholesalers';
    } else {
      count = product.customerPurchaseCount || 0;
      label = 'customers';
    }

    if (count === 0) return null;

    return (
      <div className={styles.purchaseCount}>
        <ShoppingBagIcon className={styles.bagIcon} />
        <span>
          Bought {count > 1000 ? `${(count / 1000).toFixed(1)}k+` : count} times by {label}
        </span>
      </div>
    );
  };

  return (
    <div
      className={`${styles.productCard} ${styles[viewMode]} ${isHovered ? styles.hovered : ''} ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleProductClick}
    >
      {/* Product Image */}
      <div className={styles.productImage}>
        {product.images && product.images.length > 0 && !imageError ? (
          <>
            <Image
              src={getImageUrlWithFallback(product.images[currentImageIndex])}
              alt={product.name}
              className={styles.productImg}
              onError={handleImageError}
              width={400}
              height={400}
              style={{ objectFit: 'cover' }}
            />

            {/* Image thumbnails on hover */}
            {isHovered && product.images.length > 1 && viewMode === 'grid' && (
              <div className={styles.imageThumbnails}>
                {product.images.slice(0, 4).map((_, index) => (
                  <div
                    key={index}
                    className={`${styles.thumbnail} ${currentImageIndex === index ? styles.active : ''}`}
                    onMouseEnter={() => handleImageHover(index)}
                  >
                    <Image
                      src={getImageUrlWithFallback(_)}
                      alt={`Thumbnail ${index + 1}`}
                      className={styles.thumbnailImg}
                      width={80}
                      height={80}
                      style={{ objectFit: 'cover' }}
                    />
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className={styles.noImage}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
            <span>No Image</span>
          </div>
        )}

        {/* Badges */}
        <div className={styles.badges}>
          {discountPercentage > 0 && (
            <span className={styles.discountBadge}>{discountPercentage}% OFF</span>
          )}
          {product.badge && (
            <span className={styles.customBadge} style={{ background: theme.primary }}>
              {product.badge}
            </span>
          )}
          {product.isAd && <span className={styles.adBadge}>AD</span>}
        </div>

        {/* Floating Rating Overlay */}
        {renderRating()}

        {/* Quick Actions */}
        {showQuickActions && isHovered && (
          <div className={styles.quickActions}>
            <button
              className={styles.quickActionBtn}
              onClick={handleWishlistToggle}
              disabled={isWishlistLoading}
              title={isInWishlist(product._id) ? 'Remove from wishlist' : 'Add to wishlist'}
            >
              {isInWishlist(product._id) ? (
                <HeartIconSolid className={styles.wishlistIconFilled} />
              ) : (
                <HeartIcon className={styles.wishlistIcon} />
              )}
            </button>

            <button
              className={styles.quickActionBtn}
              onClick={handleAddToCart}
              disabled={isAddingToCart || product.stock === 0}
              title="Add to cart"
            >
              <ShoppingBagIcon className={styles.cartIcon} />
            </button>

            <button
              type="button"
              className={styles.quickActionBtn}
              onClick={handleShare}
              title="Share"
              aria-label="Share product"
            >
              <ShareIcon className={styles.shareIcon} />
            </button>
          </div>
        )}
      </div>

      {/* Product Info */}
      <div className={styles.productInfo}>
        {/* Brand */}
        <div className={styles.productBrand}>{product.brand}</div>

        {/* Name */}
        <h3 className={styles.productName} title={product.name}>
          {product.name}
        </h3>

        {/* Purchase Count */}
        {renderPurchaseCount()}

        {/* Price */}
        <div className={styles.productPrice}>
          <span className={styles.currentPrice}>₹{product.price.toFixed(2)}</span>
          {discountPercentage > 0 && (
            <span className={styles.originalPrice}>
              ₹
              {product.originalPrice?.toFixed(2) ||
                (product.price * (1 + discountPercentage / 100)).toFixed(2)}
            </span>
          )}
          {discountPercentage > 0 && (
            <span className={styles.discountText}>{discountPercentage}% OFF</span>
          )}
        </div>

        {/* Stock Status */}
        {product.stock <= 5 && product.stock > 0 && (
          <div className={styles.lowStock}>Only {product.stock} left</div>
        )}

        {product.stock === 0 && <div className={styles.outOfStock}>Out of Stock</div>}

        {/* Add to Cart Button (Always visible) */}
        <div className={styles.addToCartContainer}>
          <button
            className={styles.addToCartBtn}
            onClick={handleAddToCart}
            disabled={isAddingToCart || product.stock === 0}
            style={{ background: theme.gradient }}
          >
            {isAddingToCart ? 'Adding...' : 'Add to Cart'}
          </button>
        </div>
      </div>

      <QuickVariantModal
        isOpen={showVariantModal}
        onClose={() => setShowVariantModal(false)}
        product={{ ...product, variants: product.variations }}
        onAddToCart={handleVariantAddToCart}
      />
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => {
          setShowAuthModal(false);
          setPendingWishlistAction(false);
        }}
        redirectOnSuccess={false}
        onSuccess={async () => {
          if (pendingWishlistAction) {
            try {
              await api.post('/wishlist', { productId: product._id, sessionId: getSessionId() });
              trackAddToWishlist({
                productId: product._id,
                productName: product.name,
                source: 'product_card',
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
