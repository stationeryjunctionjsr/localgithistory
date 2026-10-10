'use client';

/**
 * Zustand-based cart store with dual-cart support for Hyperlocal & Pan-India modes.
 *
 * - hyperlocalCart: Contains items added while in 'Shop for your area' (hyperlocal zone) mode.
 * - panIndiaCart: Contains items added while in 'Shop from India' (1P courier) mode.
 * - activeMode: Mirrors the PincodeContext activeMode, bridged via CartStoreSync.
 *
 * The `useActiveCart` selector always returns the cart for the currently active mode,
 * preserving backward compatibility with all consumer components.
 *
 * Migration note: Consumers that previously used `cart` should use `useActiveCart()` selector.
 * CartContext.tsx useCart() hook still delegates to this store.
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
import { usePincode } from '@/context/PincodeContext';

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
  /** Hyperlocal cart: items added while in 'Shop for your area' mode */
  hyperlocalCart: Cart | null;
  /** Pan-India cart: items added while in 'Shop from India' mode */
  panIndiaCart: Cart | null;
  /** Currently active fulfillment mode, synced from PincodeContext via CartStoreSync */
  activeMode: 'hyperlocal' | 'pan_india';
  loading: boolean;
  isCartOpen: boolean;
  duesInfo: any;

  /**
   * Backward-compatible `cart` field — mirrors the active mode's cart.
   * Existing consumers (Header, ProductCatalog, ProductDetailClient, etc.) can
   * keep using `useCartStore((s) => s.cart)` without modification.
   * Updated via set() in fetchCart and setActiveMode.
   */
  cart: Cart | null;

  /**
   * Auth bridge — set by <CartStoreSync /> component (not from AuthContext
   * directly, to keep this store free of React context dependencies).
   */
  _user: any | null;

  // ── Actions ──────────────────────────────────────────────────────────────
  setUser: (user: any | null) => void;
  setActiveMode: (mode: 'hyperlocal' | 'pan_india') => void;
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
    hyperlocalCart: null,
    panIndiaCart: null,
    activeMode: 'hyperlocal',
    // Backward-compatible `cart` field — mirrors the active mode's cart.
    // Updated in setActiveMode and fetchCart so existing s.cart consumers work without changes.
    cart: null as Cart | null,
    loading: true,
    isCartOpen: false,
    duesInfo: null,
    _user: null,

    setUser: (user) => {
      set({ _user: user });
      get().fetchCart();
    },

    setActiveMode: (mode) => {
      const { hyperlocalCart, panIndiaCart } = get();
      set({
        activeMode: mode,
        // Update backward-compat cart to the new mode's cart (may be null if not yet fetched)
        cart: mode === 'hyperlocal' ? hyperlocalCart : panIndiaCart,
      });
      // Fetch the newly-active mode's cart if not already loaded
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
      const { _user, activeMode } = get();
      try {
        if (_user) {
          const response = await api.get('/cart', { params: { fulfillment_type: activeMode } });
          const cartData = response.data;
          if (activeMode === 'hyperlocal') {
            set({ hyperlocalCart: cartData, cart: cartData });
          } else {
            set({ panIndiaCart: cartData, cart: cartData });
          }
          get().fetchDuesInfo();
        } else {
          // Guest cart: items tagged with fulfillment_type, default to activeMode
          const guestItems = getGuestCart();
          const modeItems = guestItems.filter(
            (g: any) => (g.fulfillment_type || 'hyperlocal') === activeMode,
          );
          const refreshedItems = await Promise.all(
            modeItems.map(async (g: any) => {
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
          saveGuestCart(guestItems); // persist all items (not just the filtered mode)
          const subtotal = refreshedItems.reduce(
            (s: number, g: any) => s + (g.product?.price || 0) * g.quantity,
            0,
          );
          const cartData: Cart = {
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
          };
          if (activeMode === 'hyperlocal') {
            set({ hyperlocalCart: cartData, cart: cartData });
          } else {
            set({ panIndiaCart: cartData, cart: cartData });
          }
        }
      } catch (error) {
        logger.error('Error fetching cart:', error);
      } finally {
        set({ loading: false });
      }
    },

    addToCart: async (productId, quantity, product, variantAttributes, sellAsCase) => {
      const { _user, activeMode } = get();

      // Optimistic update: add the item to the correct mode-cart immediately
      if (product) {
        set((state) => {
          const targetCart =
            activeMode === 'hyperlocal' ? state.hyperlocalCart : state.panIndiaCart;
          const existing = targetCart?.items?.find((i) => i.product?.id === productId);
          if (existing) {
            const updatedItems = targetCart!.items.map((i) =>
              i.product?.id === productId
                ? { ...i, quantity: i.quantity + quantity, subtotal: i.price * (i.quantity + quantity) }
                : i,
            );
            const updatedCart = {
              ...targetCart!,
              items: updatedItems,
              subtotal: updatedItems.reduce((s, i) => s + i.price * i.quantity, 0),
            };
            return activeMode === 'hyperlocal'
              ? { hyperlocalCart: updatedCart }
              : { panIndiaCart: updatedCart };
          }
          const price = product.price || product.mrp || 0;
          const newItem: CartItem = {
            id: productId, // temporary id, will be replaced on fetchCart
            product: { id: productId, ...product },
            price,
            quantity,
            subtotal: price * quantity,
          };
          const items = [...(targetCart?.items || []), newItem];
          const updatedCart = {
            items,
            subtotal: (targetCart?.subtotal || 0) + price * quantity,
          };
          return activeMode === 'hyperlocal'
            ? { hyperlocalCart: updatedCart }
            : { panIndiaCart: updatedCart };
        });
      }

      try {
        if (_user) {
          const sessionId =
            typeof window !== 'undefined' ? localStorage.getItem('sessionId') : null;
          await api.post('/cart', {
            productId,
            quantity,
            variantAttributes,
            sellAsCase,
            sessionId,
            fulfillment_type: activeMode,
          });
        } else {
          addGuestCartItem(productId, quantity, { ...product, fulfillment_type: activeMode });
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
      const { _user, activeMode } = get();

      // Optimistic update on the correct mode-cart
      set((state) => {
        const targetCart =
          activeMode === 'hyperlocal' ? state.hyperlocalCart : state.panIndiaCart;
        if (!targetCart?.items) return state;
        const updatedItems = targetCart.items.map((i) => {
          const id = _user ? i.id : i.product?.id || i.id;
          if (id === itemId) {
            return { ...i, quantity, subtotal: i.price * quantity };
          }
          return i;
        });
        const updatedCart = {
          ...targetCart,
          items: updatedItems,
          subtotal: updatedItems.reduce((s, i) => s + i.price * i.quantity, 0),
        };
        return activeMode === 'hyperlocal'
          ? { hyperlocalCart: updatedCart }
          : { panIndiaCart: updatedCart };
      });

      try {
        if (_user) {
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
      const { _user, activeMode } = get();

      // Optimistic update on the correct mode-cart
      set((state) => {
        const targetCart =
          activeMode === 'hyperlocal' ? state.hyperlocalCart : state.panIndiaCart;
        if (!targetCart?.items) return state;
        const updatedItems = targetCart.items.filter((i) => {
          const id = _user ? i.id : i.product?.id || i.id;
          return id !== itemId;
        });
        const updatedCart = {
          ...targetCart,
          items: updatedItems,
          subtotal: updatedItems.reduce((s, i) => s + i.price * i.quantity, 0),
        };
        return activeMode === 'hyperlocal'
          ? { hyperlocalCart: updatedCart }
          : { panIndiaCart: updatedCart };
      });

      try {
        if (_user) {
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
 * Selector that returns the cart for the currently active fulfillment mode.
 * Use this wherever `cart` was previously accessed for full backward compatibility.
 */
export const useActiveCart = () =>
  useCartStore((s) =>
    s.activeMode === 'hyperlocal' ? s.hyperlocalCart : s.panIndiaCart,
  );

/**
 * Drop this inside <AuthProvider> in layout.tsx.
 * Bridges AuthContext user → cartStore.setUser() and
 * PincodeContext activeMode → cartStore.setActiveMode().
 * Also replicates the visibility-change polling that CartContext previously owned.
 */
export function CartStoreSync() {
  const { user } = useAuth();
  const { activeMode } = usePincode();

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

  useEffect(() => {
    // Sync active mode changes from PincodeContext into the cart store
    useCartStore.getState().setActiveMode(activeMode);
  }, [activeMode]);

  return null;
}
