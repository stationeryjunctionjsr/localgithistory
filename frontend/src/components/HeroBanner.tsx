'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { getImageUrlWithFallback } from '@/utils/imageUrl';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface Banner {
  id: string;
  imageUrl?: string;
  image?: string;
  title?: string;
  description?: string;
  link?: string;
  linkUrl?: string;
}

interface HeroBannerProps {
  /** Full-width banner images (Option A) - can be single or array */
  banners?: Banner[];
  /** Fallback title if no banner title */
  title: string;
  /** Subtitle/description fallback */
  subtitle?: string;
  /** Product count or similar stat */
  stat?: string;
  /** Breadcrumb items */
  breadcrumbs?: BreadcrumbItem[];
  /** Thumbnail/logo for compact split (Option B) */
  thumbnailUrl?: string;
  /** Fallback initial when no image */
  fallbackInitial?: string;
  /** Auto-play interval in ms */
  autoPlayInterval?: number;
  /** Hide thumbnail in Option B (for text-only hero like search) */
  hideThumbnail?: boolean;
}

/**
 * HeroBanner - Consistent hero section for listing pages (brands, categories, collections).
 *
 * Includes Carousel support for Multiple Banners.
 */
export default function HeroBanner({
  banners = [],
  title,
  subtitle,
  stat,
  breadcrumbs = [],
  thumbnailUrl,
  fallbackInitial,
  autoPlayInterval = 5000,
  hideThumbnail = false,
}: HeroBannerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  const nextSlide = useCallback(() => {
    if (banners.length <= 1) return;
    setCurrentIndex((prev) => (prev + 1) % banners.length);
  }, [banners.length]);

  const prevSlide = useCallback(() => {
    if (banners.length <= 1) return;
    setCurrentIndex((prev) => (prev - 1 + banners.length) % banners.length);
  }, [banners.length]);

  useEffect(() => {
    if (banners.length <= 1 || isHovered || !autoPlayInterval) return;
    const timer = setInterval(nextSlide, autoPlayInterval);
    return () => clearInterval(timer);
  }, [banners.length, isHovered, autoPlayInterval, nextSlide]);

  // Breadcrumb renderer
  const renderBreadcrumbs = (light: boolean = false) => (
    <nav className="flex flex-wrap items-center gap-1.5 text-sm" aria-label="Breadcrumb">
      {breadcrumbs.map((crumb, i) => (
        <React.Fragment key={i}>
          {i > 0 && (
            <svg
              className={`h-3 w-3 ${light ? 'text-white/40' : 'text-gray-300'}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          )}
          {crumb.href ? (
            <Link
              href={crumb.href}
              className={`transition-colors ${light ? 'text-white/70 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
            >
              {crumb.label}
            </Link>
          ) : (
            <span className={`font-semibold ${light ? 'text-white' : 'text-gray-900'}`}>
              {crumb.label}
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );

  // ─── Option A: Carousel Banner (when banners exist) ──────────
  if (banners && banners.length > 0) {
    return (
      <div
        className="group relative w-full"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="relative h-[250px] w-full overflow-hidden bg-gray-900 shadow-inner md:h-[350px] lg:h-[400px]">
          {/* Slides */}
          {banners.map((banner, index) => {
            const imgUrl = getImageUrlWithFallback(banner.imageUrl || banner.image);
            const link = banner.link || banner.linkUrl;
            const content = (
              <div
                key={banner.id || index}
                className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${index === currentIndex ? 'z-10 opacity-100' : 'z-0 opacity-0'}`}
              >
                <Image
                  src={imgUrl}
                  alt={banner.title || title}
                  fill
                  sizes="100vw"
                  className="object-cover"
                  priority={index === 0}
                />
                {/* Overlay Gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

                {/* Content info overlay */}
                <div className="absolute inset-0 flex flex-col justify-end p-6 pb-12 md:p-10 lg:px-16 lg:pb-16">
                  <div className="animate-fadeInUp max-w-3xl">
                    <h1 className="mb-3 text-2xl font-medium leading-tight text-white drop-shadow-lg md:text-4xl lg:text-5xl">
                      {banner.title || title}
                    </h1>
                    <p className="max-w-xl text-sm font-medium text-white/80 drop-shadow md:text-lg">
                      {banner.description || subtitle}
                    </p>
                  </div>
                </div>
              </div>
            );

            return link ? (
              <Link href={link} key={banner.id || index}>
                {content}
              </Link>
            ) : (
              content
            );
          })}

          {/* Navigation Controls - Breadcrumbs and Stat */}
          <div className="pointer-events-none absolute left-0 right-0 top-0 z-20 p-6 md:px-10 lg:px-16">
            <div className="pointer-events-auto flex items-start justify-between">
              {breadcrumbs.length > 0 && renderBreadcrumbs(true)}
            </div>
          </div>

          {/* Navigation Arrows */}
          {banners.length > 1 && (
            <>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  prevSlide();
                }}
                className="absolute left-4 top-1/2 z-30 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/30 bg-white/20 text-white opacity-0 backdrop-blur-md transition-all hover:bg-white/40 group-hover:opacity-100"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2.5"
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  nextSlide();
                }}
                className="absolute right-4 top-1/2 z-30 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/30 bg-white/20 text-white opacity-0 backdrop-blur-md transition-all hover:bg-white/40 group-hover:opacity-100"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </>
          )}

          {/* Indicators */}
          {banners.length > 1 && (
            <div className="absolute bottom-6 left-1/2 z-30 flex -translate-x-1/2 gap-2">
              {banners.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentIndex(i)}
                  className={`h-1.5 rounded-full transition-all duration-300 ${i === currentIndex ? 'w-8 bg-white' : 'w-2 bg-white/40 hover:bg-white/60'}`}
                />
              ))}
            </div>
          )}
        </div>

        {/* Stat bar below banner */}
        {stat && (
          <div className="border-b border-gray-100 bg-white px-6 py-2 md:px-10 lg:px-16">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">{stat}</p>
          </div>
        )}
      </div>
    );
  }

  // ─── Option B: Compact Split (fallback) ───────────────────────
  return (
    <div className="w-full border-b border-gray-100 bg-white">
      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <div className="px-6 pb-1 pt-3 md:px-10 lg:px-16">{renderBreadcrumbs(false)}</div>
      )}

      {/* Compact split layout */}
      <div
        className={`px-6 md:px-10 lg:px-16 ${breadcrumbs.length > 0 ? 'pb-5 pt-2 md:pb-6' : 'py-5 md:py-6'} flex items-center gap-6 md:gap-10`}
      >
        {/* Thumbnail */}
        {!hideThumbnail && (thumbnailUrl || fallbackInitial) && (
          <div className="relative flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-[2rem] border border-gray-100 bg-gradient-to-br from-gray-50 via-white to-gray-50 p-4 shadow-md md:h-32 md:w-32">
            {thumbnailUrl ? (
              <Image
                src={thumbnailUrl}
                alt={title}
                fill
                sizes="128px"
                className="object-contain"
              />
            ) : (
              <span className="text-4xl font-black text-gray-200 md:text-5xl">
                {fallbackInitial}
              </span>
            )}
          </div>
        )}

        {/* Info */}
        <div className="min-w-0 flex-1">
          <h1 className="mb-2 truncate text-2xl font-medium uppercase leading-none tracking-widest text-gray-900 md:text-4xl">
            {title}
          </h1>
          {subtitle && (
            <p className="max-w-2xl text-sm font-medium leading-relaxed text-gray-500 md:text-lg">
              {subtitle}
            </p>
          )}
          {stat && (
            <p className="mt-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-gray-300 md:text-xs">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500/50"></span>
              {stat}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
