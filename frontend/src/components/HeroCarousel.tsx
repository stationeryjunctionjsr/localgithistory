'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getImageUrlWithFallback } from '@/utils/imageUrl';

interface Banner {
  _id: string;
  title?: string;
  subtitle?: string;
  image?: string;
  imageUrl?: string;
  link?: string;
  linkUrl?: string;
  isActive: boolean;
}

interface HeroCarouselProps {
  banners: Banner[];
}

export default function HeroCarousel({ banners }: HeroCarouselProps) {
  const router = useRouter();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  useEffect(() => {
    if (banners.length > 1) {
      const interval = setInterval(() => {
        setIsTransitioning(true);
        setTimeout(() => {
          setCurrentIndex((prev) => (prev + 1) % banners.length);
          setIsTransitioning(false);
        }, 500);
      }, 6000);
      return () => clearInterval(interval);
    }
  }, [banners.length]);

  const handleSlideChange = (newIndex: number) => {
    if (newIndex === currentIndex) return;
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentIndex(newIndex);
      setIsTransitioning(false);
    }, 300);
  };

  if (banners.length === 0) {
    // Fallback hero when no banners
    return (
      <div className="relative h-[400px] w-full overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-black md:h-[550px] lg:h-[600px]">
        {/* Animated Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `radial-gradient(circle at 25% 25%, rgba(255,255,255,0.1) 1px, transparent 1px),
                                         radial-gradient(circle at 75% 75%, rgba(255,255,255,0.1) 1px, transparent 1px)`,
              backgroundSize: '60px 60px',
            }}
          />
        </div>

        {/* Floating Elements */}
        <div className="absolute left-[10%] top-20 h-32 w-32 animate-pulse rounded-full bg-gradient-to-br from-rose-500/20 to-pink-500/10 blur-3xl" />
        <div
          className="absolute bottom-32 right-[15%] h-40 w-40 animate-pulse rounded-full bg-gradient-to-br from-amber-500/20 to-orange-500/10 blur-3xl"
          style={{ animationDelay: '1s' }}
        />

        {/* Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center px-4">
          <div
            className={`text-center transition-all duration-1000 ${isLoaded ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`}
          >
            <p className="mb-4 text-xs font-medium uppercase tracking-[0.3em] text-rose-400 md:text-sm">
              Premium Stationery Collection
            </p>
            <h1 className="mb-6 text-4xl font-semibold leading-tight text-white md:text-6xl lg:text-7xl">
              <span className="block">Elevate Your</span>
              <span className="block bg-gradient-to-r from-rose-400 via-pink-400 to-amber-400 bg-clip-text text-transparent">
                Workspace
              </span>
            </h1>
            <p className="mx-auto mb-10 max-w-xl text-sm leading-relaxed text-gray-400 md:text-base">
              Discover our curated collection of premium stationery designed to inspire creativity
              and productivity.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <button
                onClick={() => router.push('/products')}
                className="group relative overflow-hidden rounded-full bg-gradient-to-r from-rose-500 to-pink-500 px-8 py-4 text-sm font-semibold uppercase tracking-wider text-white shadow-2xl shadow-rose-500/30 transition-all duration-300 hover:scale-105 hover:shadow-rose-500/50 active:scale-95 md:px-12 md:py-5"
              >
                <span className="relative z-10">Visit the Shop</span>
                <div className="absolute inset-0 bg-gradient-to-r from-rose-600 to-pink-600 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
              </button>
              <button
                onClick={() => router.push('/brands')}
                className="group rounded-full border border-white/20 bg-white/10 px-8 py-4 text-sm font-semibold uppercase tracking-wider text-white backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:border-white/40 hover:bg-white/20 active:scale-95 md:px-12 md:py-5"
              >
                Explore Brands
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const currentBanner = banners[currentIndex];

  return (
    <div
      className={`group relative h-[400px] w-full overflow-hidden bg-gray-900 md:h-[550px] lg:h-[600px] ${currentBanner?.linkUrl ? 'cursor-pointer' : ''}`}
      onClick={(e) => {
        if ((e.target as HTMLElement).closest('button')) return;
        if (currentBanner?.linkUrl) {
          router.push(currentBanner.linkUrl);
        }
      }}
    >
      {/* Background Images with Ken Burns Effect */}
      {banners.map((banner, idx) => (
        <div
          key={banner._id}
          className={`absolute inset-0 transition-all duration-1000 ease-out ${
            idx === currentIndex ? 'scale-100 opacity-100' : 'scale-105 opacity-0'
          }`}
        >
          <img
            src={getImageUrlWithFallback(banner.imageUrl || banner.image)}
            alt={banner.title || 'Special Offer'}
            className={`h-full w-full object-cover transition-transform duration-[8000ms] ease-out ${
              idx === currentIndex ? 'scale-110' : 'scale-100'
            }`}
          />
        </div>
      ))}

      {/* Premium Multi-layer Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-r from-black/30 via-transparent to-black/30" />

      {/* Subtle Vignette Effect */}
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.3) 100%)',
        }}
      />

      {/* Floating Decorative Elements */}
      <div
        className="absolute left-[5%] top-1/4 h-2 w-2 animate-ping rounded-full bg-rose-400/60"
        style={{ animationDuration: '3s' }}
      />
      <div
        className="absolute right-[8%] top-1/3 h-1.5 w-1.5 animate-ping rounded-full bg-amber-400/60"
        style={{ animationDuration: '4s', animationDelay: '1s' }}
      />
      <div
        className="absolute bottom-1/3 left-[12%] h-1 w-1 animate-ping rounded-full bg-white/40"
        style={{ animationDuration: '2.5s', animationDelay: '0.5s' }}
      />

      {/* Content Overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-end px-4 pb-16 md:pb-20 lg:pb-24">
        {/* Tagline - Animated */}
        <div
          className={`mb-8 text-center transition-all duration-700 ${isTransitioning ? 'translate-y-4 opacity-0' : 'translate-y-0 opacity-100'}`}
        >
          {currentBanner.title && (
            <>
              <p className="mb-3 animate-fade-in text-[10px] font-medium uppercase tracking-[0.4em] text-rose-300/80 md:text-xs">
                ✦ Limited Collection ✦
              </p>
              <h2 className="mb-3 text-2xl font-semibold leading-tight text-white drop-shadow-lg md:text-4xl lg:text-5xl">
                {currentBanner.title}
              </h2>
            </>
          )}
          {currentBanner.subtitle && (
            <p className="mx-auto max-w-lg text-sm leading-relaxed text-gray-300/90 md:text-base">
              {currentBanner.subtitle}
            </p>
          )}
        </div>

        {/* Premium CTA Buttons */}
        <div
          className={`flex flex-wrap justify-center gap-4 transition-all delay-100 duration-700 md:gap-6 ${isTransitioning ? 'translate-y-4 opacity-0' : 'translate-y-0 opacity-100'}`}
        >
          <button
            onClick={() => router.push('/products')}
            className="group relative overflow-hidden rounded-full bg-gradient-to-r from-rose-500 to-pink-500 px-8 py-3.5 text-xs font-semibold uppercase tracking-wider text-white shadow-2xl shadow-rose-500/25 transition-all duration-500 hover:scale-105 hover:shadow-rose-500/40 active:scale-95 md:px-12 md:py-4 md:text-sm"
          >
            {/* Shine effect on hover */}
            <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
            <span className="relative z-10 flex items-center gap-2">
              <span>Visit the Shop</span>
              <svg
                className="h-4 w-4 transition-transform group-hover:translate-x-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </span>
          </button>
          <button
            onClick={() => router.push('/brands')}
            className="group rounded-full border border-white/30 bg-white/10 px-8 py-3.5 text-xs font-semibold uppercase tracking-wider text-white backdrop-blur-md transition-all duration-500 hover:scale-105 hover:border-white/50 hover:bg-white/20 active:scale-95 md:px-12 md:py-4 md:text-sm"
          >
            <span className="flex items-center gap-2">
              <span>Explore Brands</span>
              <svg
                className="h-4 w-4 transition-transform group-hover:rotate-45"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </span>
          </button>
        </div>
      </div>

      {/* Premium Pagination Dots */}
      {banners.length > 1 && (
        <div className="absolute bottom-6 left-1/2 z-20 flex -translate-x-1/2 items-center gap-3 md:bottom-8">
          {banners.map((_, idx) => (
            <button
              key={idx}
              onClick={() => handleSlideChange(idx)}
              className={`relative transition-all duration-500 ${
                idx === currentIndex ? 'w-8 md:w-10' : 'w-2 hover:w-3 md:w-2.5'
              } h-2 overflow-hidden rounded-full md:h-2.5`}
            >
              {/* Background */}
              <div
                className={`absolute inset-0 transition-colors duration-300 ${
                  idx === currentIndex
                    ? 'bg-gradient-to-r from-rose-400 to-pink-400'
                    : 'bg-white/40 hover:bg-white/60'
                }`}
              />
              {/* Progress indicator for active dot */}
              {idx === currentIndex && (
                <div
                  className="absolute inset-0 origin-left bg-white/30"
                  style={{
                    animation: 'progress 6s linear infinite',
                  }}
                />
              )}
            </button>
          ))}
        </div>
      )}

      {/* Glassmorphism Navigation Arrows */}
      <button
        onClick={() => handleSlideChange((currentIndex - 1 + banners.length) % banners.length)}
        className="absolute left-4 top-1/2 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white opacity-0 backdrop-blur-md transition-all duration-300 hover:scale-110 hover:border-white/40 hover:bg-white/20 group-hover:opacity-100 md:left-8 md:h-14 md:w-14"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
      <button
        onClick={() => handleSlideChange((currentIndex + 1) % banners.length)}
        className="absolute right-4 top-1/2 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white opacity-0 backdrop-blur-md transition-all duration-300 hover:scale-110 hover:border-white/40 hover:bg-white/20 group-hover:opacity-100 md:right-8 md:h-14 md:w-14"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      {/* Bottom Gradient Fade for smooth transition to content */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-gray-50 to-transparent" />

      {/* CSS Keyframes for progress animation */}
      <style jsx>{`
        @keyframes progress {
          from {
            transform: scaleX(0);
          }
          to {
            transform: scaleX(1);
          }
        }
      `}</style>
    </div>
  );
}
