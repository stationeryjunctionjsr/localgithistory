'use client';

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { useTheme } from '@/context/ThemeContext';

interface CarouselItem {
  id: string;
  image?: string;
  title: string;
  subtitle?: string;
  link: string;
  type: 'product' | 'brand';
  /** For recommendation tracking: strategy (arm) when product from GET /recommendations */
  strategy?: string;
}

interface InfiniteCarouselProps {
  items: CarouselItem[];
  speed?: number; // Visual speed factor (time to scroll through 10 items)
  title?: string;
  titleClassName?: string;
  titleStyle?: React.CSSProperties;
  autoScroll?: boolean;
  /** Called before navigation when an item is clicked (e.g. for recommendation tracking) */
  onItemClick?: (item: CarouselItem) => void;
}

export default function InfiniteCarousel({
  items,
  speed = 30,
  title,
  titleClassName,
  titleStyle,
  autoScroll = true,
  onItemClick,
}: InfiniteCarouselProps) {
  const router = useRouter();
  const { theme } = useTheme();
  const [isPaused, setIsPaused] = useState(false);
  const scrollerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (!containerRef.current) return;
    const scrollAmount = containerRef.current.clientWidth * 0.8;
    containerRef.current.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth',
    });
  };

  // Only duplicate and auto-scroll if we have enough items to actually "carousel"
  const isScrollable = items.length > 5;
  const effectiveAutoScroll = autoScroll && isScrollable;
  const displayItems =
    items.length > 0
      ? effectiveAutoScroll
        ? [...items, ...items, ...items, ...items]
        : items
      : [];

  if (items.length === 0) return null;

  return (
    <div className="relative w-full overflow-hidden bg-white py-8">
      {title && (
        <h2
          className={`mb-6 px-4 text-2xl font-bold uppercase tracking-tight text-gray-800 md:px-0 ${titleClassName || ''}`}
          style={titleStyle}
        >
          {title}
        </h2>
      )}

      <div
        className="group relative w-full"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        {/* Navigation Buttons */}
        <button
          onClick={() => scroll('left')}
          className="absolute left-2 top-1/2 z-20 -translate-y-1/2 rounded-full border-2 border-white/20 p-3 text-white opacity-0 shadow-2xl transition-all hover:scale-110 active:scale-95 group-hover:opacity-100"
          style={{ background: theme.gradient }}
          aria-label="Previous"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>

        <button
          onClick={() => scroll('right')}
          className="absolute right-2 top-1/2 z-20 -translate-y-1/2 rounded-full border-2 border-white/20 p-3 text-white opacity-0 shadow-2xl transition-all hover:scale-110 active:scale-95 group-hover:opacity-100"
          style={{ background: theme.gradient }}
          aria-label="Next"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
          >
            <path d="M9 18l6-6-6-6" />
          </svg>
        </button>

        <div ref={containerRef} className="no-scrollbar overflow-x-auto scroll-smooth">
          <div
            ref={scrollerRef}
            className={`flex w-max gap-6 ${autoScroll ? 'animate-scroll' : ''} ${isPaused ? 'paused' : ''}`}
            style={
              {
                '--animation-duration': `${(items.length / 10) * speed}s`,
              } as React.CSSProperties
            }
          >
            {displayItems.map((item, idx) => (
              <div
                key={`${item.id}-${idx}`}
                onClick={() => {
                  if (item.type === 'brand') {
                    sessionStorage.removeItem('fromBrandsPage');
                  }
                  onItemClick?.(item);
                  router.push(item.link);
                }}
                className={`flex-shrink-0 cursor-pointer transition-transform hover:scale-105 ${
                  item.type === 'brand'
                    ? 'flex h-24 w-40 items-center justify-center rounded-lg border border-gray-100 bg-white shadow-sm hover:shadow-md'
                    : 'w-48 overflow-hidden rounded-lg border border-gray-100 bg-white shadow-sm hover:shadow-md'
                } `}
              >
                {item.type === 'brand' ? (
                  <div className="flex h-full w-full items-center justify-center p-4 text-center">
                    {item.image ? (
                      <img
                        src={item.image}
                        alt={item.title}
                        className="max-h-full max-w-full object-contain"
                      />
                    ) : (
                      <span className="text-xs font-semibold uppercase text-gray-800">
                        {item.title}
                      </span>
                    )}
                  </div>
                ) : (
                  <>
                    <div className="relative h-48 w-full bg-gray-50">
                      <img
                        src={getImageUrlWithFallback(item.image)}
                        alt={item.title}
                        className="h-full w-full object-cover"
                      />
                    </div>
                    <div className="p-3">
                      <h4
                        className="truncate text-xs font-bold uppercase text-gray-900"
                        title={item.title}
                      >
                        {item.title}
                      </h4>
                      {item.subtitle && (
                        <p className="mt-1 text-[10px] font-black uppercase text-red-600">
                          {item.subtitle}
                        </p>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
      <style jsx>{`
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
