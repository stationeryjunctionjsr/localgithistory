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
    } catch {}
    const allCartItems = [
      ...guestCart,
      ...legacyCart.map((l: any) => ({ productId: l.productId, quantity: l.quantity || 1 })),
    ];
    for (const item of allCartItems) {
      try {
        await api.post('/cart', { productId: item.productId, quantity: item.quantity });
      } catch {
        // silently skip items that fail
      }
    }
    if (allCartItems.length > 0) {
      clearGuestCart();
      localStorage.removeItem('guestCart');
    }
  } catch {
    // ignore
  }

  // ── Wishlist ──────────────────────────────────────────────────────
  try {
    const guestWishlist = getGuestWishlist();
    // Also collect items from legacy key used by WishlistContext
    let legacyWishlist: any[] = [];
    try {
      const raw = localStorage.getItem('guestWishlist');
      if (raw) legacyWishlist = JSON.parse(raw);
    } catch {}
    const allWishlistItems = [
      ...guestWishlist,
      ...legacyWishlist
        .map((l: any) => ({ productId: l.product?._id || l.productId }))
        .filter((i: any) => i.productId),
    ];
    for (const item of allWishlistItems) {
      try {
        await api.post('/wishlist', { productId: item.productId });
      } catch {
        // silently skip
      }
    }
    if (allWishlistItems.length > 0) {
      clearGuestWishlist();
      localStorage.removeItem('guestWishlist');
    }
  } catch {
    // ignore
  }

  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('guest-data-synced'));
  }
}
