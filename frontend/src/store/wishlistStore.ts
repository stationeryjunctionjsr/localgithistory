'use client';

/**
 * Zustand-based replacement for WishlistContext. Provides the same public API
 * so migration is a drop-in swap.
 *
 * WishlistContext.tsx now delegates its useWishlist() hook to this store, so
 * no consumer components need to change their imports.
 *
 * Migration steps applied:
 *   1. <WishlistStoreSync /> added inside <AuthProvider> in layout.tsx
 *   2. <WishlistProvider> commented out from layout.tsx
 *   3. WishlistContext.tsx useWishlist() now reads from this store
 */

import { useEffect } from 'react';
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import api from '@/utils/api';
import {
  getGuestWishlist,
  addGuestWishlistItem,
  removeGuestWishlistItem,
} from '@/utils/guestStore';
import { logger } from '@/utils/logger';
import { useAuth } from '@/context/AuthContext';

// Matching the WishlistItem shape from WishlistContext.tsx exactly
export interface WishlistItem {
  id: string;
  product: {
    id: string;
    name: string;
    price: number;
    images: string[];
  };
  addedAt: string;
}

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
          // For guest users, get from unified guestStore
          const guestItems = getGuestWishlist();
          const mapped = guestItems.map((g: any) => ({
            id: g.productId,
            product: g.product || { id: g.productId, name: '', price: 0, images: [] },
            addedAt: new Date().toISOString(),
          }));
          set({ items: mapped as any });
        }
      } catch (error) {
        logger.error('Error fetching wishlist:', error);
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
            } catch (err) {
              logger.error('Failed to fetch product for guest wishlist', err);
            }
          }
          addGuestWishlistItem(productId, productData);
          await get().fetchWishlist();
        }
      } catch (error) {
        logger.error('Error adding to wishlist:', error);
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
        logger.error('Error removing from wishlist:', error);
      }
    },

    isInWishlist: (productId) => {
      return get().items.some((item) => item.product.id === productId);
    },
  })),
);

/**
 * Drop this inside <AuthProvider> in layout.tsx.
 * Bridges AuthContext user → wishlistStore.setUser(), replicates the
 * visibility polling and 'guest-data-synced' listener from WishlistContext.
 */
export function WishlistStoreSync() {
  const { user } = useAuth();

  useEffect(() => {
    // Bridge auth state into store (triggers fetchWishlist internally)
    useWishlistStore.getState().setUser(user ?? null);

    // guest-data-synced fires when guest localStorage is hydrated after login
    const handleSync = () => useWishlistStore.getState().fetchWishlist();
    window.addEventListener('guest-data-synced', handleSync);

    // Sync wishlist on tab focus (instant) and every 60s when the tab is visible.
    // Poll is paused when the tab is hidden to avoid unnecessary DB load.
    let interval: ReturnType<typeof setInterval> | null = setInterval(
      () => useWishlistStore.getState().fetchWishlist(),
      60_000,
    );

    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (interval) { clearInterval(interval); interval = null; }
      } else {
        useWishlistStore.getState().fetchWishlist(); // Immediately refresh on return
        interval = setInterval(() => useWishlistStore.getState().fetchWishlist(), 60_000);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      window.removeEventListener('guest-data-synced', handleSync);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (interval) clearInterval(interval);
    };
  }, [user]);

  return null;
}
