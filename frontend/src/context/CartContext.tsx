'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import api from '@/utils/api';
import {
  getGuestCart,
  addGuestCartItem,
  updateGuestCartQty,
  removeGuestCartItem,
  saveGuestCart,
} from '@/utils/guestStore';
import { trackBackendCartAdd } from '@/utils/analytics';

export interface CartItem {
  _id: string; // Product ID for guest, item ID for logged in
  product: {
    _id: string;
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
  sellAsCase?: boolean;
}

export interface Cart {
  items: CartItem[];
  subtotal: number;
}

interface CartContextType {
  cart: Cart | null;
  loading: boolean;
  isCartOpen: boolean;
  setIsCartOpen: (open: boolean) => void;
  openCart: () => void;
  closeCart: () => void;
  fetchCart: () => Promise<void>;
  addToCart: (
    productId: string,
    quantity: number,
    product?: any,
    variantAttributes?: Record<string, string>,
    sellAsCase?: boolean
  ) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeFromCart: (itemId: string) => Promise<void>;
  duesInfo: any;
  fetchDuesInfo: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider = ({ children }: { children: React.ReactNode }) => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const { user } = useAuth();
  const [duesInfo, setDuesInfo] = useState<any>(null);

  const fetchDuesInfo = async () => {
    if (user && ((user as any).effectiveRole === 'wholesaler' || (user as any).role === 'wholesaler')) {
      try {
        const response = await api.get('/payments/dues');
        setDuesInfo(response.data);
      } catch (error) {
        console.error('Error fetching wholesaler dues:', error);
        setDuesInfo(null);
      }
    } else {
      setDuesInfo(null);
    }
  };

  const fetchCart = async () => {
    try {
      if (user) {
        const response = await api.get('/cart');
        setCart(response.data);
        fetchDuesInfo();
      } else {
        const guestItems = getGuestCart();
        const refreshedItems = await Promise.all(
          guestItems.map(async (g) => {
            try {
              const res = await api.get(`/products/public/${g.productId}`, {
                params: { role: 'customer' },
              });
              return {
                ...g,
                product: res.data,
              };
            } catch (err) {
              console.error(`Failed to refresh price for product ${g.productId}`, err);
              return g;
            }
          })
        );
        saveGuestCart(refreshedItems);

        const refreshedSubtotal = refreshedItems.reduce(
          (s, g) => s + (g.product?.price || 0) * g.quantity,
          0
        );

        setCart({
          items: refreshedItems.map((g) => {
            const itemPrice = g.product?.price || 0;
            const itemQty = g.quantity || 1;
            return {
              _id: g.productId,
              product: g.product || { _id: g.productId, name: 'Product', price: 0 },
              price: itemPrice,
              quantity: itemQty,
              subtotal: itemPrice * itemQty,
            };
          }),
          subtotal: refreshedSubtotal,
        });
      }
    } catch (error) {
      console.error('Error fetching cart in context:', error);
    } finally {
      setLoading(false);
    }
  };

  // Sync cart on mount, when user changes, on tab focus (instant), and
  // every 60s in the background (cross-device sync). Previously 5s which
  // generated excessive traffic — 60s is sufficient for multi-device use.
  useEffect(() => {
    fetchCart();
    const handleFocus = () => fetchCart();
    window.addEventListener('focus', handleFocus);
    const interval = setInterval(fetchCart, 60_000);
    return () => {
      window.removeEventListener('focus', handleFocus);
      clearInterval(interval);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const openCart = () => setIsCartOpen(true);
  const closeCart = () => setIsCartOpen(false);

  const addToCart = async (
    productId: string,
    quantity: number,
    product?: any,
    variantAttributes?: Record<string, string>,
    sellAsCase?: boolean
  ) => {
    // Optimistic update: add the item immediately
    if (product) {
      setCart((prev) => {
        const existing = prev?.items?.find((i) => i.product?._id === productId);
        if (existing) {
          const updatedItems = prev!.items.map((i) =>
            i.product?._id === productId
              ? { ...i, quantity: i.quantity + quantity, subtotal: i.price * (i.quantity + quantity) }
              : i
          );
          return {
            ...prev!,
            items: updatedItems,
            subtotal: updatedItems.reduce((s, i) => s + (i.price * i.quantity), 0),
          };
        }
        const price = product.price || product.mrp || 0;
        const newItem: CartItem = {
          _id: productId, // temporary id, will be replaced on fetchCart
          product: { _id: productId, ...product },
          price,
          quantity,
          subtotal: price * quantity,
        } as any;
        const items = [...(prev?.items || []), newItem];
        return {
          items,
          subtotal: (prev?.subtotal || 0) + price * quantity,
        };
      });
    }
    try {
      if (user) {
        const sessionId = typeof window !== 'undefined' ? localStorage.getItem('sessionId') : null;
        await api.post('/cart', {
          productId,
          quantity,
          variantAttributes,
          sellAsCase,
          sessionId,
        });
      } else {
        addGuestCartItem(productId, quantity, product);
        trackBackendCartAdd(productId, quantity).catch(() => {});
      }
      await fetchCart();
      setIsCartOpen(true); // Automatically slide open overlay
    } catch (error) {
      console.error('Error adding item to cart in context:', error);
      await fetchCart(); // revert optimistic update
      throw error;
    }
  };

  const updateQuantity = async (itemId: string, quantity: number) => {
    // Optimistic update
    setCart((prev) => {
      if (!prev?.items) return prev;
      const updatedItems = prev.items.map((i) => {
        const id = user ? i._id : i.product?._id || i._id;
        if (id === itemId) {
          return { ...i, quantity, subtotal: i.price * quantity };
        }
        return i;
      });
      return {
        ...prev,
        items: updatedItems,
        subtotal: updatedItems.reduce((s, i) => s + (i.price * i.quantity), 0),
      };
    });
    try {
      if (user) {
        await api.put(`/cart/${itemId}`, { quantity });
      } else {
        updateGuestCartQty(itemId, quantity); // For guest, itemId is productId
      }
      await fetchCart();
    } catch (error) {
      console.error('Error updating cart item quantity in context:', error);
      await fetchCart(); // revert optimistic update
      throw error;
    }
  };

  const removeFromCart = async (itemId: string) => {
    // Optimistic update
    setCart((prev) => {
      if (!prev?.items) return prev;
      const updatedItems = prev.items.filter((i) => {
        const id = user ? i._id : i.product?._id || i._id;
        return id !== itemId;
      });
      return {
        ...prev,
        items: updatedItems,
        subtotal: updatedItems.reduce((s, i) => s + (i.price * i.quantity), 0),
      };
    });
    try {
      if (user) {
        await api.delete(`/cart/${itemId}`);
      } else {
        removeGuestCartItem(itemId); // For guest, itemId is productId
      }
      await fetchCart();
    } catch (error) {
      console.error('Error removing item from cart in context:', error);
      await fetchCart(); // revert optimistic update
      throw error;
    }
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        isCartOpen,
        setIsCartOpen,
        openCart,
        closeCart,
        fetchCart,
        addToCart,
        updateQuantity,
        removeFromCart,
        duesInfo,
        fetchDuesInfo,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
