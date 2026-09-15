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
    const failedCartItems: any[] = [];
    for (const item of guestCart) {
      try {
        await api.post('/cart', { productId: item.productId, quantity: item.quantity });
      } catch (e) {
        // keep items that fail to sync
        failedCartItems.push(item);
      }
    }
    if (failedCartItems.length > 0) {
      // Store back only the failed ones
      await api.post('/cart-error-log', { failedItems: failedCartItems }).catch((e: any) => console.warn('Background task failed', e)); // optional log
      // In mobile, getGuestCart gets from SecureStore or similar. We need to clear and re-add or directly set
      // We will just clear all then add the failed ones back.
      await clearGuestCart();
      for (const item of failedCartItems) {
        const { addGuestCartItem } = require('./guestStore');
        await addGuestCartItem(item.productId, item.quantity, item.product);
      }
    } else if (guestCart.length > 0) {
      await clearGuestCart();
    }
  } catch {
    // ignore
  }

  // ── Wishlist ──────────────────────────────────────────────────────
  try {
    const guestWishlist = await getGuestWishlist();
    const failedWishlistItems: any[] = [];
    for (const item of guestWishlist) {
      try {
        await api.post('/wishlist', { productId: item.productId });
      } catch {
        failedWishlistItems.push(item);
      }
    }
    if (failedWishlistItems.length > 0) {
      await clearGuestWishlist();
      for (const item of failedWishlistItems) {
        const { addGuestWishlistItem } = require('./guestStore');
        await addGuestWishlistItem(item.productId, item.product);
      }
    } else if (guestWishlist.length > 0) {
      await clearGuestWishlist();
    }
  } catch {
    // ignore
  }
}
