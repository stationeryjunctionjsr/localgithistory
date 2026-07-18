'use client';

import React, { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useCart, CartItem } from '@/context/CartContext';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import styles from './CartOverlay.module.css';

export default function CartOverlay() {
  const { cart, loading, isCartOpen, closeCart, updateQuantity, removeFromCart, duesInfo } = useCart();
  const { theme } = useTheme();
  const { user } = useAuth();
  const router = useRouter();
  const drawerRef = useRef<HTMLDivElement>(null);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeCart();
      }
    };
    if (isCartOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent body scrolling when cart is open
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isCartOpen, closeCart]);

  if (!isCartOpen) return null;

  const items = cart?.items || [];
  const subtotal = cart?.subtotal || 0;

  // Calculate total product-level savings if any product has mrp > price
  const totalSavings = items.reduce((sum, item) => {
    const mrp = item.product?.mrp || item.price;
    if (mrp > item.price) {
      return sum + (mrp - item.price) * item.quantity;
    }
    return sum;
  }, 0);

  const handleQtyChange = async (item: CartItem, delta: number) => {
    let step = 1;
    if (item.sellAsCase && item.product?.quantityPerCase) {
      step = item.product.quantityPerCase;
    }
    const currentQty = item.quantity;
    const newQty = currentQty + delta * step;

    if (newQty < step) {
      await removeFromCart(item._id);
    } else {
      await updateQuantity(item._id, newQty);
    }
  };

  const handleCheckoutRedirect = () => {
    closeCart();
    router.push('/customer/cart');
  };

  // Delivery progress calculation (free delivery on orders above 499)
  const deliveryThreshold = 499;
  const progressPercent = Math.min((subtotal / deliveryThreshold) * 100, 100);
  const remainingForFreeDelivery = deliveryThreshold - subtotal;

  return (
    <>
      {/* Backdrop overlay */}
      <div
        className={`${styles.backdrop} ${isCartOpen ? styles.backdropOpen : ''}`}
        onClick={closeCart}
        aria-hidden="true"
      />

      {/* Slide-out Drawer */}
      <div
        ref={drawerRef}
        className={`${styles.drawer} ${isCartOpen ? styles.drawerOpen : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="cart-overlay-title"
      >
        {/* Header */}
        <div className={styles.header}>
          <h3 id="cart-overlay-title">SHOPPING CART ({items.length})</h3>
          <button
            onClick={closeCart}
            className={styles.closeBtn}
            aria-label="Close cart drawer"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Body Content */}
        {loading && items.length === 0 ? (
          <div className={styles.emptyState}>
            <svg
              className="animate-spin"
              width="36"
              height="36"
              viewBox="0 0 24 24"
              fill="none"
              stroke={theme.primary}
              strokeWidth="3"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
            </svg>
            <p style={{ color: 'var(--text-muted)' }}>Loading your cart...</p>
          </div>
        ) : items.length === 0 ? (
          <div className={styles.emptyState}>
            <svg
              className={styles.emptyIcon}
              width="64"
              height="64"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="9" cy="21" r="1" />
              <circle cx="20" cy="21" r="1" />
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
            </svg>
            <h4 className={styles.emptyTitle}>Your Cart is Empty</h4>
            <p className={styles.emptyText}>
              Add items to your cart to see them here and proceed to checkout.
            </p>
            <button onClick={closeCart} className={styles.shopNowBtn} style={{ backgroundColor: theme.primary }}>
              Shop Now
            </button>
          </div>
        ) : (
          <div className={styles.body}>
            {items.map((item) => {
              const imageSrc = getImageUrlWithFallback(item.product?.images?.[0]);
              const mrp = item.product?.mrp || item.price;
              const hasProductDiscount = mrp > item.price;

              return (
                <div key={item._id} className={styles.item}>
                  <div className={styles.imageContainer}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={imageSrc}
                      alt={item.product?.name || 'Product'}
                      className={styles.image}
                    />
                  </div>

                  <div className={styles.itemDetails}>
                    <div>
                      <h4 className={styles.itemName}>
                        {item.product?.name || 'Product'}
                      </h4>
                      {item.sellAsCase && (
                        <span style={{ fontSize: '11px', color: theme.primary, fontWeight: 600 }}>
                          [CASE OF {item.product?.quantityPerCase || 1}]
                        </span>
                      )}
                    </div>

                    <div className={styles.quantityActions}>
                      <div>
                        <span className={styles.itemPrice}>
                          ₹{item.price.toFixed(2)}
                        </span>
                        {hasProductDiscount && (
                          <span className={styles.originalPrice}>
                            ₹{mrp.toFixed(2)}
                          </span>
                        )}
                      </div>

                      <div className={styles.qtySelector}>
                        <button
                          onClick={() => handleQtyChange(item, -1)}
                          className={styles.qtyBtn}
                          aria-label="Decrease quantity"
                        >
                          -
                        </button>
                        <span className={styles.qtyValue}>{item.quantity}</span>
                        <button
                          onClick={() => handleQtyChange(item, 1)}
                          className={styles.qtyBtn}
                          aria-label="Increase quantity"
                        >
                          +
                        </button>
                      </div>

                      <button
                        onClick={() => removeFromCart(item._id)}
                        className={styles.deleteBtn}
                        aria-label="Remove item"
                      >
                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                          <line x1="10" y1="11" x2="10" y2="17" />
                          <line x1="14" y1="11" x2="14" y2="17" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer CTAs */}
        {items.length > 0 && (
          <div className={styles.footer}>
            {/* Delivery threshold reminder */}
            <div className={styles.deliveryProgress}>
              <div className={styles.deliveryText}>
                {remainingForFreeDelivery > 0 ? (
                  <span>
                    Add <strong>₹{remainingForFreeDelivery.toFixed(2)}</strong> more for <strong>FREE Delivery</strong>
                  </span>
                ) : (
                  <span style={{ color: '#00b894', fontWeight: 600 }}>
                    🎉 Your order qualifies for FREE Delivery!
                  </span>
                )}
              </div>
              <div className={styles.progressBarBg}>
                <div
                  className={styles.progressBarFill}
                  style={{
                    width: `${progressPercent}%`,
                    background: theme.gradient,
                  }}
                />
              </div>
            </div>

            {/* Subtotal & Product Discount Savings */}
            <div className={styles.priceRow}>
              <span className={styles.subtotalLabel}>Subtotal:</span>
              <span className={styles.subtotalValue}>₹{subtotal.toFixed(2)}</span>
            </div>

            {totalSavings > 0 && (
              <div className={styles.discountInfo}>
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 8 8 12 12 16" />
                  <line x1="16" y1="12" x2="8" y2="12" />
                </svg>
                <span>Product discount savings: ₹{totalSavings.toFixed(2)}</span>
              </div>
            )}

            <div className={styles.actionButtons}>
              {user && ((user as any).effectiveRole === 'wholesaler' || user.role === 'wholesaler') && duesInfo?.hasOverdueBills ? (
                <button
                  onClick={() => {
                    closeCart();
                    router.push('/customer/cart?showDues=true');
                  }}
                  className={styles.checkoutBtn}
                  style={{
                    background: 'linear-gradient(135deg, #d63031, #ff7675)',
                    boxShadow: '0 4px 12px rgba(214, 48, 49, 0.3)',
                    color: '#fff',
                  }}
                >
                  🔴 Clear Dues
                </button>
              ) : (
                <button
                  onClick={handleCheckoutRedirect}
                  className={styles.checkoutBtn}
                  style={{
                    background: theme.gradient,
                    boxShadow: `0 4px 12px ${theme.shadow}`,
                  }}
                >
                  Proceed to Checkout
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
              )}
              <button
                onClick={closeCart}
                className={styles.continueBtn}
                style={{
                  color: theme.primary,
                  borderColor: theme.primary,
                }}
              >
                Continue Shopping
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
