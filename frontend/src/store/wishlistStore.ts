/**
 * STANDBY — not wired into the application yet.
 *
 * Zustand-based replacement for WishlistContext. Provides the same public API
 * so migration is a drop-in swap:
 *
 *   Before:  const { items, addToWishlist } = useWishlist();
 *   After:   const items = useWishlistStore(s => s.items);
 *            const addToWishlist = useWishlistStore(s => s.addToWishlist);
 *
 * Migration steps when ready:
 *   1. Add <WishlistStoreSync /> inside <AuthProvider> in layout.tsx
 *   2. Remove <WishlistProvider> from layout.tsx
 *   3. Replace `useWishlist()` calls with selector imports from this store
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import api from '@/utils/api';
import {
  getGuestWishlist,
  addGuestWishlistItem,
  removeGuestWishlistItem,
} from '@/utils/guestStore';
import type { WishlistItem } from '@sj/api-client';

export type { WishlistItem };

interface WishlistState {
  items: WishlistItem[];
  loading: boolean;

  /** Auth bridge — set by <WishlistStoreSync /> */
  _user: any | null;

  // ── Actions ──────────────────────────────────────────────────────────────
  setUser: (user: any | null) => void;
  fetchWishlist: () => Promise<void>;
  addToWishlist: (productId: string, sessionId?: string, product?: any) => Promise<void>;
  removeFromWishlist: (productId: string) => Promise<void>;
  isInWishlist: (productId: string) => boolean;
}

export const useWishlistStore = create<WishlistState>()(
  subscribeWithSelector((set, get) => ({
    items: [],
    loading: true,
    _user: null,

    setUser: (user) => {
      set({ _user: user });
      get().fetchWishlist();
    },

    fetchWishlist: async () => {
      const user = get()._user;
      try {
        set({ loading: true });
        if (user) {
          const response = await api.get('/wishlist');
          const data = response.data;
          set({ items: Array.isArray(data) ? data : data?.items || [] });
        } else {
          const guestItems = getGuestWishlist();
          set({
            items: guestItems.map((g: any) => ({
              _id: g.productId,
              product: g.product || { _id: g.productId, name: '', price: 0, images: [] },
              addedAt: new Date().toISOString(),
            })) as WishlistItem[],
          });
        }
      } catch (error) {
        console.error('Error fetching wishlist:', error);
      } finally {
        set({ loading: false });
      }
    },

    addToWishlist: async (productId, sessionId, product) => {
      const user = get()._user;
      try {
        if (user) {
          await api.post('/wishlist', { productId, sessionId });
          await get().fetchWishlist();
        } else {
          let productData = product;
          if (!productData) {
            try {
              const res = await api.get(`/products/public/${productId}`);
              productData = res.data;
            } catch {
              // keep productData undefined
            }
          }
          addGuestWishlistItem(productId, productData);
          await get().fetchWishlist();
        }
      } catch (error) {
        console.error('Error adding to wishlist:', error);
      }
    },

    removeFromWishlist: async (productId) => {
      const user = get()._user;
      try {
        if (user) {
          await api.delete(`/wishlist/${productId}`);
          await get().fetchWishlist();
        } else {
          removeGuestWishlistItem(productId);
          await get().fetchWishlist();
        }
      } catch (error) {
        console.error('Error removing from wishlist:', error);
      }
    },

    isInWishlist: (productId) => {
      return get().items.some((item) => item.product._id === productId);
    },
  })),
);

/**
 * STANDBY — Drop this inside <AuthProvider> in layout.tsx when activating.
 * Bridges AuthContext user changes → wishlistStore.setUser().
 */
export function WishlistStoreSync() {
  return null;
}
