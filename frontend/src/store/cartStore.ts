'use client';

/**
 * Zustand-based replacement for CartContext. Provides the same public API
 * (same method names, same state shape) so migration is a drop-in swap.
 *
 * CartContext.tsx now delegates its useCart() hook to this store, so no
 * consumer components need to change their imports.
 *
 * Migration steps applied:
 *   1. <CartStoreSync /> added inside <AuthProvider> in layout.tsx
 *      (bridges AuthContext user → store's setUser)
 *   2. <CartProvider> commented out from layout.tsx
 *   3. CartContext.tsx useCart() now reads from this store
 */

import { useEffect } from 'react';
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import api from '@/utils/api';
import {
  getGuestCart,
  addGuestCartItem,
  updateGuestCartQty,
  removeGuestCartItem,
  saveGuestCart,
} from '@/utils/guestStore';
import { trackBackendCartAdd } from '@/utils/analytics';
import { logger } from '@/utils/logger';
import { useAuth } from '@/context/AuthContext';

// Matching the CartItem/Cart shape from CartContext.tsx exactly
export interface CartItem {
  id: string; // Product ID for guest, item ID for logged-in
  product: {
    id: string;
    name: string;
    price: number;
    mrp?: number;
    images?: string[];
    quantityPerCase?: number;
    mrpPerCase?: number;
    [key: string]: any;
  };
  price: number;
  quantity: number;
  subtotal?: number;
  sellAsCase?: boolean;
}

export interface Cart {
  items: CartItem[];
  subtotal: number;
}

interface CartState {
  cart: Cart | null;
  loading: boolean;
  isCartOpen: boolean;
  duesInfo: any;

  /**
   * Auth bridge — set by <CartStoreSync /> component (not from AuthContext
   * directly, to keep this store free of React context dependencies).
   */
  _user: any | null;

  // ── Actions ──────────────────────────────────────────────────────────────
  setUser: (user: any | null) => void;
  setIsCartOpen: (open: boolean) => void;
  openCart: () => void;
  closeCart: () => void;
  fetchCart: () => Promise<void>;
  fetchDuesInfo: () => Promise<void>;
  addToCart: (
    productId: string,
    quantity: number,
    product?: any,
    variantAttributes?: Record<string, string>,
    sellAsCase?: boolean,
  ) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeFromCart: (itemId: string) => Promise<void>;
}

export const useCartStore = create<CartState>()(
  subscribeWithSelector((set, get) => ({
    cart: null,
    loading: true,
    isCartOpen: false,
    duesInfo: null,
    _user: null,

    setUser: (user) => {
      set({ _user: user });
      get().fetchCart();
    },

    setIsCartOpen: (open) => set({ isCartOpen: open }),
    openCart: () => set({ isCartOpen: true }),
    closeCart: () => set({ isCartOpen: false }),

    fetchDuesInfo: async () => {
      const user = get()._user;
      if (user && (user.effectiveRole === 'wholesaler' || user.role === 'wholesaler')) {
        try {
          const response = await api.get('/payments/dues');
          set({ duesInfo: response.data });
        } catch {
          set({ duesInfo: null });
        }
      } else {
        set({ duesInfo: null });
      }
    },

    fetchCart: async () => {
      const user = get()._user;
      try {
        if (user) {
          const response = await api.get('/cart');
          set({ cart: response.data });
          get().fetchDuesInfo();
        } else {
          const guestItems = getGuestCart();
          const refreshedItems = await Promise.all(
            guestItems.map(async (g: any) => {
              try {
                const res = await api.get(`/products/public/${g.productId}`, {
                  params: { role: 'customer' },
                });
                return { ...g, product: res.data };
              } catch (err) {
                logger.error(`Failed to refresh price for product ${g.productId}`, err);
                return g;
              }
            }),
          );
          saveGuestCart(refreshedItems);
          const subtotal = refreshedItems.reduce(
            (s: number, g: any) => s + (g.product?.price || 0) * g.quantity,
            0,
          );
          set({
            cart: {
              items: refreshedItems.map((g: any) => {
                const itemPrice = g.product?.price || 0;
                const itemQty = g.quantity || 1;
                return {
                  id: g.productId,
                  product: g.product || { id: g.productId, name: 'Product', price: 0 },
                  price: itemPrice,
                  quantity: itemQty,
                  subtotal: itemPrice * itemQty,
                };
              }),
              subtotal,
            },
          });
        }
      } catch (error) {
        logger.error('Error fetching cart:', error);
      } finally {
        set({ loading: false });
      }
    },

    addToCart: async (productId, quantity, product, variantAttributes, sellAsCase) => {
      const user = get()._user;

      // Optimistic update: add the item immediately
      if (product) {
        set((state) => {
          const existing = state.cart?.items?.find((i) => i.product?.id === productId);
          if (existing) {
            const updatedItems = state.cart!.items.map((i) =>
              i.product?.id === productId
                ? { ...i, quantity: i.quantity + quantity, subtotal: i.price * (i.quantity + quantity) }
                : i,
            );
            return {
              cart: {
                ...state.cart!,
                items: updatedItems,
                subtotal: updatedItems.reduce((s, i) => s + i.price * i.quantity, 0),
              },
            };
          }
          const price = product.price || product.mrp || 0;
          const newItem: CartItem = {
            id: productId, // temporary id, will be replaced on fetchCart
            product: { id: productId, ...product },
            price,
            quantity,
            subtotal: price * quantity,
          };
          const items = [...(state.cart?.items || []), newItem];
          return {
            cart: {
              items,
              subtotal: (state.cart?.subtotal || 0) + price * quantity,
            },
          };
        });
      }

      try {
        if (user) {
          const sessionId =
            typeof window !== 'undefined' ? localStorage.getItem('sessionId') : null;
          await api.post('/cart', { productId, quantity, variantAttributes, sellAsCase, sessionId });
        } else {
          addGuestCartItem(productId, quantity, product);
          trackBackendCartAdd(productId, quantity).catch((e) => logger.warn('Background task failed', e));
        }
        await get().fetchCart();
        set({ isCartOpen: true }); // Automatically slide open overlay
      } catch (error) {
        logger.error('Error adding item to cart:', error);
        await get().fetchCart(); // revert optimistic update
        throw error;
      }
    },

    updateQuantity: async (itemId, quantity) => {
      const user = get()._user;

      // Optimistic update
      set((state) => {
        if (!state.cart?.items) return state;
        const updatedItems = state.cart.items.map((i) => {
          const id = user ? i.id : i.product?.id || i.id;
          if (id === itemId) {
            return { ...i, quantity, subtotal: i.price * quantity };
          }
          return i;
        });
        return {
          cart: {
            ...state.cart,
            items: updatedItems,
            subtotal: updatedItems.reduce((s, i) => s + i.price * i.quantity, 0),
          },
        };
      });

      try {
        if (user) {
          await api.put(`/cart/${itemId}`, { quantity });
        } else {
          updateGuestCartQty(itemId, quantity); // For guest, itemId is productId
        }
        await get().fetchCart();
      } catch (error) {
        logger.error('Error updating cart item quantity:', error);
        await get().fetchCart(); // revert optimistic update
        throw error;
      }
    },

    removeFromCart: async (itemId) => {
      const user = get()._user;

      // Optimistic update
      set((state) => {
        if (!state.cart?.items) return state;
        const updatedItems = state.cart.items.filter((i) => {
          const id = user ? i.id : i.product?.id || i.id;
          return id !== itemId;
        });
        return {
          cart: {
            ...state.cart,
            items: updatedItems,
            subtotal: updatedItems.reduce((s, i) => s + i.price * i.quantity, 0),
          },
        };
      });

      try {
        if (user) {
          await api.delete(`/cart/${itemId}`);
        } else {
          removeGuestCartItem(itemId); // For guest, itemId is productId
        }
        await get().fetchCart();
      } catch (error) {
        logger.error('Error removing item from cart:', error);
        await get().fetchCart(); // revert optimistic update
        throw error;
      }
    },
  })),
);

/**
 * Drop this inside <AuthProvider> in layout.tsx.
 * Bridges AuthContext user → cartStore.setUser(), and replicates
 * the visibility-change polling that CartContext previously owned.
 */
export function CartStoreSync() {
  const { user } = useAuth();

  useEffect(() => {
    // Bridge auth state into store (triggers fetchCart internally)
    useCartStore.getState().setUser(user ?? null);

    // Sync cart on tab focus (instant) and every 60s when the tab is visible.
    // Poll is paused when the tab is hidden to avoid unnecessary DB load.
    let interval: ReturnType<typeof setInterval> | null = setInterval(
      () => useCartStore.getState().fetchCart(),
      60_000,
    );

    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (interval) { clearInterval(interval); interval = null; }
      } else {
        useCartStore.getState().fetchCart(); // Immediately refresh on return
        interval = setInterval(() => useCartStore.getState().fetchCart(), 60_000);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (interval) clearInterval(interval);
    };
  }, [user]);

  return null;
}
