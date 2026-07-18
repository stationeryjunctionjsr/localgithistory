/**
 * STANDBY — not wired into the application yet.
 *
 * Zustand-based replacement for CartContext. Provides the same public API
 * (same method names, same state shape) so migration is a drop-in swap:
 *
 *   Before:  const { cart, addToCart } = useCart();
 *   After:   const cart = useCartStore(s => s.cart);
 *            const addToCart = useCartStore(s => s.addToCart);
 *
 * Migration steps when ready:
 *   1. Add <CartStoreSync /> inside <AuthProvider> in layout.tsx
 *      (bridges AuthContext user → store's setUser)
 *   2. Remove <CartProvider> from layout.tsx
 *   3. Replace `useCart()` calls with selector imports from this store
 */

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
import type { Cart, CartItem } from '@sj/api-client';

export type { Cart, CartItem };

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
              } catch {
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
              items: refreshedItems.map((g: any) => ({
                _id: g.productId,
                product: g.product || { _id: g.productId, name: 'Product', price: 0 },
                price: g.product?.price || 0,
                quantity: g.quantity || 1,
              })),
              subtotal,
            },
          });
        }
      } catch (error) {
        console.error('Error fetching cart:', error);
      } finally {
        set({ loading: false });
      }
    },

    addToCart: async (productId, quantity, product, variantAttributes, sellAsCase) => {
      const user = get()._user;

      // Optimistic update
      if (product) {
        set((state) => {
          const existing = state.cart?.items?.find((i) => i.product?._id === productId);
          if (existing) {
            const updatedItems = state.cart!.items.map((i) =>
              i.product?._id === productId
                ? { ...i, quantity: i.quantity + quantity }
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
            _id: productId,
            product: { _id: productId, ...product },
            price,
            quantity,
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
          trackBackendCartAdd(productId, quantity).catch(() => {});
        }
        await get().fetchCart();
        set({ isCartOpen: true });
      } catch (error) {
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
          const id = user ? i._id : i.product?._id || i._id;
          return id === itemId ? { ...i, quantity } : i;
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
          updateGuestCartQty(itemId, quantity);
        }
        await get().fetchCart();
      } catch (error) {
        await get().fetchCart();
        throw error;
      }
    },

    removeFromCart: async (itemId) => {
      const user = get()._user;

      // Optimistic update
      set((state) => {
        if (!state.cart?.items) return state;
        const updatedItems = state.cart.items.filter((i) => {
          const id = user ? i._id : i.product?._id || i._id;
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
          removeGuestCartItem(itemId);
        }
        await get().fetchCart();
      } catch (error) {
        await get().fetchCart();
        throw error;
      }
    },
  })),
);

/**
 * STANDBY — Drop this component inside <AuthProvider> in layout.tsx when
 * activating the store. It bridges AuthContext → cartStore without coupling
 * the store itself to React context.
 *
 * Usage in layout.tsx:
 *   import { CartStoreSync } from '@/store/cartStore';
 *   // Inside <AuthProvider>:
 *   <CartStoreSync />
 */
export function CartStoreSync() {
  // Will be implemented when wiring: reads useAuth() and calls useCartStore.getState().setUser()
  // Using a useEffect that subscribes to user changes.
  return null;
}
