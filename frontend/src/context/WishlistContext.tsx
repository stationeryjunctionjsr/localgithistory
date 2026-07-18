'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import api from '@/utils/api';
import {
  getGuestWishlist,
  removeGuestWishlistItem,
  addGuestWishlistItem,
} from '@/utils/guestStore';

interface WishlistItem {
  _id: string;
  product: {
    _id: string;
    name: string;
    price: number;
    images: string[];
  };
  addedAt: string;
}

interface WishlistContextType {
  items: WishlistItem[];
  loading: boolean;
  addToWishlist: (productId: string, sessionId?: string, product?: any) => Promise<void>;
  removeFromWishlist: (productId: string) => Promise<void>;
  isInWishlist: (productId: string) => boolean;
  fetchWishlist: () => Promise<void>;
}

const WishlistContext = createContext<WishlistContextType | undefined>(undefined);

export const WishlistProvider = ({ children }: { children: React.ReactNode }) => {
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchWishlist = async () => {
    try {
      setLoading(true);
      if (user) {
        const response = await api.get('/wishlist');
        const data = response.data;
        setItems(Array.isArray(data) ? data : data?.items || []);
      } else {
        // For guest users, get from unified guestStore
        const guestItems = getGuestWishlist();
        const mapped = guestItems.map((g) => ({
          _id: g.productId,
          product: g.product || { _id: g.productId, name: '', price: 0, images: [] },
          addedAt: new Date().toISOString(),
        }));
        setItems(mapped as any);
      }
    } catch (error) {
      console.error('Error fetching wishlist:', error);
    } finally {
      setLoading(false);
    }
  };

  // Sync wishlist on mount, when user changes, on tab focus (instant), and
  // every 60s in the background (cross-device sync). Previously 5s.
  useEffect(() => {
    fetchWishlist();
    const handleSync = () => fetchWishlist();
    window.addEventListener('guest-data-synced', handleSync);
    const handleFocus = () => fetchWishlist();
    window.addEventListener('focus', handleFocus);
    const interval = setInterval(fetchWishlist, 60_000);
    return () => {
      window.removeEventListener('guest-data-synced', handleSync);
      window.removeEventListener('focus', handleFocus);
      clearInterval(interval);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const addToWishlist = async (productId: string, sessionId?: string, product?: any) => {
    try {
      if (user) {
        await api.post('/wishlist', { productId, sessionId });
        await fetchWishlist();
      } else {
        let productData = product;
        if (!productData) {
          try {
            const res = await api.get(`/products/public/${productId}`);
            productData = res.data;
          } catch (err) {
            console.error('Failed to fetch product for guest wishlist', err);
          }
        }
        addGuestWishlistItem(productId, productData);
        await fetchWishlist();
      }
    } catch (error) {
      console.error('Error adding to wishlist:', error);
    }
  };

  const removeFromWishlist = async (productId: string) => {
    try {
      if (user) {
        await api.delete(`/wishlist/${productId}`);
        await fetchWishlist();
      } else {
        removeGuestWishlistItem(productId);
        await fetchWishlist();
      }
    } catch (error) {
      console.error('Error removing from wishlist:', error);
    }
  };

  const isInWishlist = (productId: string) => {
    return items.some((item) => item.product._id === productId);
  };

  return (
    <WishlistContext.Provider
      value={{
        items,
        loading,
        addToWishlist,
        removeFromWishlist,
        isInWishlist,
        fetchWishlist,
      }}
    >
      {children}
    </WishlistContext.Provider>
  );
};

export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
};
