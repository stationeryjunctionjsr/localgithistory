'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import Link from 'next/link';

interface BundleItem {
  productId: string;
  quantity: number;
  product?: {
    _id: string;
    name: string;
    sku: string;
    mrp: number;
    images?: string[];
    stock?: number;
  };
  lineMrp?: number;
}

interface Bundle {
  _id: string;
  name: string;
  description?: string;
  price: number;
  items: BundleItem[];
  imageUrl?: string;
  isActive: boolean;
  totalMrp: number;
  savings: number;
  savingsPercent: number;
  isAvailable: boolean;
}

export default function BundlesPage() {
  const { user } = useAuth();
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [loading, setLoading] = useState(true);
  const [addingToCart, setAddingToCart] = useState<string | null>(null);
  const [expandedBundle, setExpandedBundle] = useState<string | null>(null);

  useEffect(() => {
    fetchBundles();
  }, []);

  const fetchBundles = async () => {
    try {
      const res = await api.get('/bundles/');
      setBundles(res.data.bundles || []);
    } catch {
      toast.error('Failed to load bundles');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (bundle: Bundle) => {
    if (!user) {
      toast.info('Please sign in to add items to your cart');
      return;
    }
    setAddingToCart(bundle._id);
    try {
      await api.post(`/bundles/${bundle._id}/add-to-cart`);
      toast.success(`🎁 "${bundle.name}" added to your cart!`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Could not add bundle to cart');
    } finally {
      setAddingToCart(null);
    }
  };

  const imgSrc = (url?: string) =>
    url
      ? url.startsWith('http')
        ? url
        : `${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '')}${url}`
      : null;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 px-4 py-12">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse rounded-2xl bg-white p-6 shadow-sm">
                <div className="mb-4 h-40 rounded-xl bg-slate-200" />
                <div className="mb-2 h-5 w-2/3 rounded bg-slate-200" />
                <div className="h-4 w-full rounded bg-slate-100" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      <div className="mx-auto max-w-6xl px-4 py-12">
        {/* Header */}
        <div className="mb-10 text-center">
          <div className="mb-3 text-5xl">🎁</div>
          <h1 className="text-3xl font-extrabold text-slate-800 sm:text-4xl">Bundle Deals</h1>
          <p className="mt-3 text-base text-slate-500">
            Save more with our hand-picked product bundles — everything you need in one click.
          </p>
        </div>

        {bundles.length === 0 ? (
          <div className="rounded-2xl bg-white py-24 text-center shadow-sm">
            <div className="mb-4 text-5xl">📦</div>
            <h2 className="text-lg font-semibold text-slate-700">No bundles available right now</h2>
            <p className="mt-2 text-sm text-slate-400">Check back soon for special curated deals!</p>
            <Link
              href="/"
              className="mt-6 inline-block rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
            >
              Continue Shopping
            </Link>
          </div>
        ) : (
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {bundles.map((bundle) => (
              <div
                key={bundle._id}
                className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-lg"
              >
                {/* Bundle image / hero */}
                <div className="relative overflow-hidden bg-gradient-to-br from-violet-50 to-indigo-100">
                  {bundle.imageUrl ? (
                    <img
                      src={imgSrc(bundle.imageUrl) || ''}
                      alt={bundle.name}
                      className="h-48 w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="flex h-48 items-center justify-center">
                      <span className="text-7xl">🎁</span>
                    </div>
                  )}

                  {/* Savings badge */}
                  {bundle.savings > 0 && (
                    <div className="absolute left-3 top-3 rounded-full bg-emerald-500 px-3 py-1 text-xs font-bold text-white shadow-md">
                      {bundle.savingsPercent}% OFF
                    </div>
                  )}

                  {/* Unavailable overlay */}
                  {!bundle.isAvailable && (
                    <div className="absolute inset-0 flex items-center justify-center bg-slate-900/40 backdrop-blur-[1px]">
                      <span className="rounded-full bg-white/90 px-4 py-2 text-sm font-bold text-slate-700">
                        Currently Unavailable
                      </span>
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex flex-1 flex-col p-5">
                  <h2 className="mb-1 text-lg font-bold text-slate-800">{bundle.name}</h2>
                  {bundle.description && (
                    <p className="mb-4 text-sm text-slate-500 leading-relaxed">{bundle.description}</p>
                  )}

                  {/* Items preview */}
                  <div className="mb-4">
                    <button
                      onClick={() =>
                        setExpandedBundle(expandedBundle === bundle._id ? null : bundle._id)
                      }
                      className="flex w-full items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-100"
                    >
                      <span>
                        {bundle.items.length} item{bundle.items.length !== 1 ? 's' : ''} included
                      </span>
                      <span className="text-slate-400">
                        {expandedBundle === bundle._id ? '▲' : '▼'}
                      </span>
                    </button>

                    {expandedBundle === bundle._id && (
                      <div className="mt-2 space-y-2 rounded-xl border border-slate-100 bg-white p-2">
                        {bundle.items.map((item) => (
                          <div key={item.productId} className="flex items-center gap-2">
                            <div className="h-8 w-8 flex-shrink-0 overflow-hidden rounded border border-slate-200 bg-slate-100">
                              {item.product?.images?.[0] && (
                                <img
                                  src={imgSrc(item.product.images[0]) || ''}
                                  className="h-full w-full object-cover"
                                  alt=""
                                />
                              )}
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="truncate text-xs font-medium text-slate-700">
                                {item.product?.name ?? 'Product'}
                              </div>
                              <div className="text-[10px] text-slate-400">
                                Qty: {item.quantity} × ₹{item.product?.mrp ?? '?'}
                              </div>
                            </div>
                            <div className="text-xs font-semibold text-slate-600">
                              ₹{item.lineMrp?.toFixed(2) ?? '?'}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Pricing */}
                  <div className="mt-auto rounded-xl border border-slate-100 bg-gradient-to-r from-indigo-50 to-violet-50 p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[10px] font-medium uppercase tracking-wide text-slate-500">
                          Bundle Price
                        </div>
                        <div className="text-2xl font-extrabold text-indigo-700">
                          ₹{bundle.price.toFixed(2)}
                        </div>
                      </div>
                      {bundle.savings > 0 && (
                        <div className="text-right">
                          <div className="text-[10px] font-medium uppercase tracking-wide text-slate-500">
                            You save
                          </div>
                          <div className="text-lg font-bold text-emerald-600">
                            ₹{bundle.savings.toFixed(2)}
                          </div>
                          <div className="text-[10px] text-slate-400 line-through">
                            MRP ₹{bundle.totalMrp.toFixed(2)}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* CTA */}
                  <button
                    onClick={() => handleAddToCart(bundle)}
                    disabled={!bundle.isAvailable || addingToCart === bundle._id}
                    className={`mt-4 w-full rounded-xl py-3 text-sm font-bold transition-all duration-200 ${
                      !bundle.isAvailable
                        ? 'cursor-not-allowed bg-slate-100 text-slate-400'
                        : addingToCart === bundle._id
                          ? 'cursor-wait bg-indigo-400 text-white'
                          : 'bg-indigo-600 text-white shadow-md hover:bg-indigo-700 hover:shadow-lg active:scale-95'
                    }`}
                  >
                    {!bundle.isAvailable
                      ? 'Out of Stock'
                      : addingToCart === bundle._id
                        ? 'Adding to Cart…'
                        : '🛒 Add Bundle to Cart'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
