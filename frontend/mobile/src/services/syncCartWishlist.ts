import Toast from 'react-native-toast-message';
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
        if (__DEV__) {
          console.warn(`Failed to sync cart item ${item.productId}`, e);
        }
        // keep items that fail to sync
        failedCartItems.push(item);
      }
    }
    if (failedCartItems.length > 0) {
      Toast.show({ type: 'error', text1: 'Sync Error', text2: 'Some cart items failed to sync' });
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
  } catch (e: any) {
    if (__DEV__) {
      console.warn('Cart sync failed entirely', e);
    }
    Toast.show({ type: 'error', text1: 'Sync Error', text2: 'Cart sync failed entirely' });
  }

  // ── Wishlist ──────────────────────────────────────────────────────
  try {
    const guestWishlist = await getGuestWishlist();
    const failedWishlistItems: any[] = [];
    for (const item of guestWishlist) {
      try {
        await api.post('/wishlist', { productId: item.productId });
      } catch (e) {
        if (__DEV__) {
          console.warn(`Failed to sync wishlist item ${item.productId}`, e);
        }
        failedWishlistItems.push(item);
      }
    }
    if (failedWishlistItems.length > 0) {
      Toast.show({ type: 'error', text1: 'Sync Error', text2: 'Some wishlist items failed to sync' });
      await clearGuestWishlist();
      for (const item of failedWishlistItems) {
        const { addGuestWishlistItem } = require('./guestStore');
        await addGuestWishlistItem(item.productId, item.product);
      }
    } else if (guestWishlist.length > 0) {
      await clearGuestWishlist();
    }
  } catch (e: any) {
    if (__DEV__) {
      console.warn('Wishlist sync failed entirely', e);
    }
    Toast.show({ type: 'error', text1: 'Sync Error', text2: 'Wishlist sync failed entirely' });
  }
}
