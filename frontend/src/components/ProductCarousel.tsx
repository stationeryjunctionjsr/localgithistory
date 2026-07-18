'use client';

import { useRef } from 'react';
import { getImageUrlWithFallback, IMAGE_PLACEHOLDER_DATA_URI } from '@/utils/imageUrl';
import { useTheme } from '@/context/ThemeContext';

interface Product {
  _id?: string;
  name: string;
  displayImage?: string;
  displayPrice?: number;
  displayStock?: number;
  variants?: any[];
}

interface ProductCarouselProps {
  products: Product[];
  basePath: string;
  onProductClick?: (product: Product) => void;
}

export default function ProductCarousel({
  products,
  // eslint-disable-next-line unused-imports/no-unused-vars
  basePath,
  onProductClick,
}: ProductCarouselProps) {
  const { theme } = useTheme();
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: -300, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: 300, behavior: 'smooth' });
    }
  };

  if (!products || products.length === 0) {
    return null;
  }

  return (
    <div className="w-full">
      <div className="group relative w-full">
        <button
          className="absolute left-2 top-1/2 z-10 flex h-9 w-9 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full border-2 border-white/20 text-xl font-bold text-white opacity-0 shadow-2xl transition-all focus-within:opacity-100 hover:scale-110 focus:opacity-100 active:scale-95 group-hover:opacity-100 md:h-11 md:w-11 md:text-2xl md:opacity-100"
          style={{ background: theme.gradient }}
          onClick={scrollLeft}
          aria-label="Scroll left"
        >
          ‹
        </button>
        <div
          ref={scrollContainerRef}
          className="scrollbar-thin flex gap-4 overflow-x-auto scroll-smooth px-2 py-4 md:gap-6 md:px-12"
          style={{
            scrollbarWidth: 'thin',
            scrollbarColor: '#d63031 #f5e6d3',
          }}
        >
          {products.map((product) => (
            <div
              key={product._id || product.displayImage}
              onClick={() => onProductClick && onProductClick(product)}
              className="flex h-full w-52 flex-none cursor-pointer flex-col overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md active:scale-[0.99] sm:w-56 md:w-64 md:rounded-none"
            >
              {product.displayImage && (
                <div className="relative h-48 w-full overflow-hidden bg-gray-100">
                  <img
                    src={getImageUrlWithFallback(product.displayImage)}
                    alt={product.name}
                    className="h-full w-full object-cover"
                    style={{
                      opacity:
                        product.displayStock !== undefined && product.displayStock === 0 ? 0.5 : 1,
                      filter:
                        product.displayStock !== undefined && product.displayStock === 0
                          ? 'grayscale(50%)'
                          : 'none',
                      transition: 'opacity 0.3s, filter 0.3s',
                    }}
                    onError={(e: any) => {
                      e.target.src = IMAGE_PLACEHOLDER_DATA_URI;
                    }}
                  />
                  {product.displayStock !== undefined && product.displayStock === 0 && (
                    <div className="absolute right-2 top-2 rounded bg-yellow-400 bg-opacity-90 px-2 py-1 text-xs font-bold text-black md:rounded-none">
                      Stock Out
                    </div>
                  )}
                </div>
              )}
              <div className="flex flex-1 flex-col gap-1.5 p-3 md:p-4">
                <h4 className="truncate text-sm font-semibold text-gray-800">{product.name}</h4>
                {product.displayPrice !== undefined && (
                  <p className="text-lg font-bold text-red-600 md:text-xl">
                    ₹{product.displayPrice.toFixed(2)}
                  </p>
                )}
                {product.displayStock !== undefined && (
                  <p
                    className={`text-sm font-medium ${product.displayStock > 0 ? 'text-green-600' : 'text-red-600'}`}
                  >
                    {product.displayStock > 0 ? `${product.displayStock} in stock` : 'Out of stock'}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
        <button
          className="absolute right-2 top-1/2 z-10 flex h-9 w-9 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full border-2 border-white/20 text-xl font-bold text-white opacity-0 shadow-2xl transition-all focus-within:opacity-100 hover:scale-110 focus:opacity-100 active:scale-95 group-hover:opacity-100 md:h-11 md:w-11 md:text-2xl md:opacity-100"
          style={{ background: theme.gradient }}
          onClick={scrollRight}
          aria-label="Scroll right"
        >
          ›
        </button>
      </div>
    </div>
  );
}
