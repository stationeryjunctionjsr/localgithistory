'use client';

/**
 * RecentlyViewed
 * ==============
 * Self-fetching carousel of recently browsed products.
 * Works for logged-in users (user_id) and guests (sessionId from analytics).
 *
 * Usage:
 *   <RecentlyViewed basePath="/customer/products" limit={8} excludeProductId="abc" />
 *
 * Props
 * -----
 * basePath        – the listing base URL, e.g. "/customer/products"
 * limit           – max products to show (default 8)
 * excludeProductId – optional: skip the currently viewed product (PDP use-case)
 * title           – section heading (default "Continue Browsing")
 */

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import { getSessionId } from '@/utils/analytics';
import { getImageUrlWithFallback, IMAGE_PLACEHOLDER_DATA_URI } from '@/utils/imageUrl';
import { useTheme } from '@/context/ThemeContext';

interface RecentProduct {
  productId: string;
  productName: string;
  displayImage?: string;
  price?: number;
}

interface RecentlyViewedProps {
  basePath: string;
  limit?: number;
  excludeProductId?: string;
  title?: string;
}

export default function RecentlyViewed({
  basePath,
  limit = 8,
  excludeProductId,
  title = 'Continue Browsing',
}: RecentlyViewedProps) {
  const [products, setProducts] = useState<RecentProduct[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { theme } = useTheme();

  useEffect(() => {
    const sessionId = getSessionId();
    api
      .get('/tracking/recent-products', { params: { sessionId, limit: limit + 2 } })
      .then((res) => {
        const data: RecentProduct[] = res.data || [];
        const filtered = excludeProductId
          ? data.filter((p) => p.productId !== excludeProductId)
          : data;
        setProducts(filtered.slice(0, limit));
      })
      .catch(() => {}); // silent – non-critical
  }, [limit, excludeProductId]);

  if (products.length === 0) return null;

  const scroll = (dir: 'left' | 'right') => {
    scrollRef.current?.scrollBy({ left: dir === 'left' ? -280 : 280, behavior: 'smooth' });
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between px-4 md:px-6">
        <h2 className="text-base font-bold text-gray-900 md:text-lg">{title}</h2>
      </div>

      {/* Carousel */}
      <div className="group relative w-full">
        {/* Left arrow */}
        <button
          onClick={() => scroll('left')}
          aria-label="Scroll left"
          className="absolute left-1 top-1/2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border-2 border-white/30 text-lg font-bold text-white opacity-0 shadow-lg transition-all hover:scale-110 group-hover:opacity-100 md:h-10 md:w-10"
          style={{ background: theme.gradient }}
        >
          ‹
        </button>

        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto scroll-smooth px-4 py-2 md:gap-4 md:px-10"
          style={{ scrollbarWidth: 'none' }}
        >
          {products.map((p) => (
            <button
              key={p.productId}
              type="button"
              onClick={() => router.push(`${basePath}/product/${p.productId}`)}
              className="group/card flex w-36 flex-none flex-col overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md active:scale-[0.98] md:w-44"
            >
              {/* Image */}
              <div className="relative h-36 w-full overflow-hidden bg-gray-50 md:h-44">
                <img
                  src={getImageUrlWithFallback(p.displayImage)}
                  alt={p.productName}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover/card:scale-105"
                  onError={(e: any) => { e.target.src = IMAGE_PLACEHOLDER_DATA_URI; }}
                />
              </div>

              {/* Info */}
              <div className="flex flex-col gap-0.5 p-2.5">
                <p className="line-clamp-2 text-left text-xs font-semibold leading-tight text-gray-800">
                  {p.productName}
                </p>
                {p.price != null && (
                  <p className="text-left text-sm font-bold text-red-600">
                    ₹{p.price.toFixed(2)}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Right arrow */}
        <button
          onClick={() => scroll('right')}
          aria-label="Scroll right"
          className="absolute right-1 top-1/2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border-2 border-white/30 text-lg font-bold text-white opacity-0 shadow-lg transition-all hover:scale-110 group-hover:opacity-100 md:h-10 md:w-10"
          style={{ background: theme.gradient }}
        >
          ›
        </button>
      </div>
    </div>
  );
}
