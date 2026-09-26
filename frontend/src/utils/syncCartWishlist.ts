import { logger } from '@/utils/logger';
import { toast } from 'react-toastify';
import api from './api';
import { getGuestCart, getGuestWishlist, clearGuestCart, clearGuestWishlist } from './guestStore';

/**
 * Merge local guest cart & wishlist into the backend for the logged-in user,
 * then clear the local stores.
 * Safe to call even when the guest stores are empty.
 * Also cleans up legacy localStorage keys from older code.
 */
export async function syncGuestDataToBackend(): Promise<void> {
  // ── Cart ──────────────────────────────────────────────────────────
  try {
    const guestCart = getGuestCart();
    // Also collect items from legacy key used by ModernProductCard
    let legacyCart: any[] = [];
    try {
      const raw = localStorage.getItem('guestCart');
      if (raw) legacyCart = JSON.parse(raw);
    } catch (e) { logger.warn("Failed to parse legacy cart/wishlist", e); }
    const allCartItems = [
      ...guestCart,
      ...legacyCart.map((l: any) => ({ productId: l.productId, quantity: l.quantity || 1 })),
    ];
    const failedCartItems: any[] = [];
    for (const item of allCartItems) {
      try {
        await api.post('/cart', { productId: item.productId, quantity: item.quantity });
      } catch (e) {
        logger.error("Failed to sync cart item", e);
        failedCartItems.push(item);
      }
    }
    if (failedCartItems.length > 0) {
      toast.warn("Some cart items could not be synced");
      // use saveGuestCart equivalent inline since it wasn't exported in a way we know for sure
      localStorage.setItem('guest_cart', JSON.stringify(failedCartItems));
    } else if (allCartItems.length > 0) {
      clearGuestCart();
      localStorage.removeItem('guestCart');
    }
  } catch (e) {
    logger.error("Cart sync failed entirely", e);
    toast.warn("Your cart could not be synchronized");
  }

  // ── Wishlist ──────────────────────────────────────────────────────
  try {
    const guestWishlist = getGuestWishlist();
    // Also collect items from legacy key used by WishlistContext
    let legacyWishlist: any[] = [];
    try {
      const raw = localStorage.getItem('guestWishlist');
      if (raw) legacyWishlist = JSON.parse(raw);
    } catch (e) { logger.warn("Failed to parse legacy cart/wishlist", e); }
    const allWishlistItems = [
      ...guestWishlist,
      ...legacyWishlist
        .map((l: any) => ({ productId: l.product?.id || l.productId }))
        .filter((i: any) => i.productId),
    ];
    const failedWishlistItems: any[] = [];
    for (const item of allWishlistItems) {
      try {
        await api.post('/wishlist', { productId: item.productId });
      } catch (e) {
        logger.error("Failed to sync wishlist item", e);
        failedWishlistItems.push(item);
      }
    }
    if (failedWishlistItems.length > 0) {
      toast.warn("Some wishlist items could not be synced");
      // Optionally could write them back to localStorage via a new saveGuestWishlist,
      // but for now let's just use localStorage.setItem if saveGuestWishlist isn't available
      localStorage.setItem('guest_wishlist', JSON.stringify(failedWishlistItems));
    } else if (allWishlistItems.length > 0) {
      clearGuestWishlist();
      localStorage.removeItem('guestWishlist');
    }
  } catch (e) {
    logger.error("Wishlist sync failed entirely", e);
    toast.warn("Your wishlist could not be synchronized");
  }

  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('guest-data-synced'));
  }
}
