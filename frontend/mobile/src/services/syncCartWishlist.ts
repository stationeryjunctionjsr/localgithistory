import api from '../api/client';
import { getGuestCart, getGuestWishlist, clearGuestCart, clearGuestWishlist } from './guestStore';

/**
 * Merge local guest cart & wishlist into the backend for the logged-in user,
 * then clear the local stores.
 * Safe to call even when the guest stores are empty.
 */
export async function syncGuestDataToBackend(): Promise<void> {
  // ── Cart ──────────────────────────────────────────────────────────
  try {
    const guestCart = await getGuestCart();
    for (const item of guestCart) {
      try {
        await api.post('/cart', { productId: item.productId, quantity: item.quantity });
      } catch {
        // silently skip items that fail (e.g. product removed, stock issue)
      }
    }
    if (guestCart.length > 0) await clearGuestCart();
  } catch {
    // ignore
  }

  // ── Wishlist ──────────────────────────────────────────────────────
  try {
    const guestWishlist = await getGuestWishlist();
    for (const item of guestWishlist) {
      try {
        await api.post('/wishlist', { productId: item.productId });
      } catch {
        // silently skip
      }
    }
    if (guestWishlist.length > 0) await clearGuestWishlist();
  } catch {
    // ignore
  }
}
