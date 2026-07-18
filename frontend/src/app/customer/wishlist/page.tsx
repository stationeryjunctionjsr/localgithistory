'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useWishlist } from '@/context/WishlistContext';
import { useAuth } from '@/context/AuthContext';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { trackRemoveFromWishlist } from '@/utils/analytics';
import Header from '@/components/Header';
import api from '@/utils/api';
import { addGuestCartItem } from '@/utils/guestStore';
import { toast } from 'react-toastify';

export default function WishlistPage() {
  const { user } = useAuth();
  const { items, loading, removeFromWishlist } = useWishlist();
  const list = Array.isArray(items) ? items : ((items as any)?.items ?? []);
  const [addingToCart, setAddingToCart] = useState<string | null>(null);

  const handleAddToCart = async (productId: string, product: any) => {
    if (!productId) return;
    setAddingToCart(productId);
    try {
      if (user) {
        await api.post('/cart', { productId, quantity: 1 });
      } else {
        addGuestCartItem(productId, 1, product);
      }
      toast.success('Added to cart');
    } catch {
      toast.error('Failed to add to cart');
    } finally {
      setAddingToCart(null);
    }
  };



  return (
    <>
      <Header />
      <div className="min-h-screen w-full max-w-full overflow-x-hidden pb-24 md:pb-8">
        <div className="container mx-auto px-4 py-6">
        <h1 className="mb-6 text-2xl font-bold">Wishlist</h1>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-emerald-800" />
          </div>
        ) : list.length === 0 ? (
          <div className="rounded-2xl border border-gray-100 bg-white p-8 text-center shadow-sm">
            <p className="mb-4 text-gray-600">Your wishlist is empty.</p>
            <Link
              href="/customer"
              className="inline-block rounded-full bg-emerald-800 px-6 py-2 font-medium text-white hover:bg-emerald-900"
            >
              Browse Products
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((item: any) => {
              const product = item?.product || item;
              const productId = product?._id || item?._id;
              const name = product?.name || 'Item';
              const price = product?.price;
              const img = product?.displayImage || product?.images?.[0];
              return (
                <div
                  key={productId || item._id}
                  className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm"
                >
                  <Link href={`/customer/product/${productId}`} className="block">
                    <div className="relative aspect-square bg-gray-50">
                      <img
                        src={getImageUrlWithFallback(img)}
                        alt={name}
                        className="h-full w-full object-cover"
                      />
                    </div>
                  </Link>
                  <div className="p-4">
                    <Link href={`/customer/product/${productId}`}>
                      <h3 className="line-clamp-2 font-semibold text-gray-900">{name}</h3>
                    </Link>
                    {price != null && <p className="mt-1 font-bold text-gray-900">₹{price}</p>}
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => handleAddToCart(productId, product)}
                        disabled={addingToCart === productId}
                        className="flex-1 rounded-md bg-emerald-800 px-3 py-1.5 text-sm font-medium text-white transition-opacity hover:bg-emerald-900 disabled:opacity-60"
                      >
                        {addingToCart === productId ? 'Adding…' : 'Add to Cart'}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (productId) {
                            trackRemoveFromWishlist({
                              productId,
                              productName: name,
                              source: 'wishlist_page',
                            });
                            removeFromWishlist(productId);
                          }
                        }}
                        className="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50"
                      >
                        Remove
                      </button>
                      <Link
                        href={`/customer/product/${productId}`}
                        className="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                      >
                        View
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        </div>
      </div>
    </>
  );
}
