'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Image from 'next/image';
import { getImageUrlWithFallback } from '@/utils/imageUrl';

interface HoverProductCardProps {
  product: any;
  onClick: () => void;
  cartQuantity?: number;
  onAddToCart?: (e: React.MouseEvent) => void;
  onIncrement?: (e: React.MouseEvent) => void;
  onDecrement?: (e: React.MouseEvent) => void;
}

export default function HoverProductCard({ product, onClick, cartQuantity = 0, onAddToCart, onIncrement, onDecrement }: HoverProductCardProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  const images = useMemo(() => {
    const all = [];
    if (product.displayImage) all.push(product.displayImage);
    if (product.images && Array.isArray(product.images)) {
      product.images.forEach((img: string) => {
        if (img !== product.displayImage) all.push(img);
      });
    }
    return all.length > 0 ? all : [''];
  }, [product]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isHovered && images.length > 1) {
      interval = setInterval(() => {
        setCurrentImageIndex((prev) => (prev + 1) % images.length);
      }, 1200);
    }
    return () => clearInterval(interval);
  }, [isHovered, images]);

  const discountPercentage = useMemo(() => {
    if (product.mrp && product.price && product.mrp > product.price) {
      return Math.round(((product.mrp - product.price) / product.mrp) * 100);
    }
    return 0;
  }, [product.mrp, product.price]);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        setCurrentImageIndex(0);
      }}
      className="group relative flex h-full cursor-pointer flex-col overflow-hidden rounded-2xl bg-white transition-all duration-500 hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.15)]"
    >
      {/* Image Container */}
      <div className="relative aspect-[3/4] overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100">
        {/* Skeleton loader */}
        {!imageLoaded && (
          <div className="absolute inset-0 animate-pulse bg-gradient-to-r from-gray-100 via-gray-50 to-gray-100" />
        )}

        <Image
          src={getImageUrlWithFallback(images[currentImageIndex])}
          alt={product.name}
          fill
          sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
          className={`object-cover transition-all duration-700 ${
            isHovered ? 'scale-110' : 'scale-100'
          } ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setImageLoaded(true)}
          onError={() => setImageLoaded(true)}
        />

        {/* Gradient overlay on hover */}
        <div
          className={`absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent transition-opacity duration-300 ${
            isHovered ? 'opacity-100' : 'opacity-0'
          }`}
        />

        {/* Image indicators */}
        {images.length > 1 && (
          <div
            className={`absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-1.5 transition-opacity duration-300 ${
              isHovered ? 'opacity-100' : 'opacity-0'
            }`}
          >
            {images.map((_, idx) => (
              <div
                key={idx}
                className={`h-1 rounded-full transition-all duration-300 ${
                  idx === currentImageIndex ? 'w-4 bg-white' : 'w-1 bg-white/50'
                }`}
              />
            ))}
          </div>
        )}

        {/* Badges */}
        <div className="absolute left-3 top-3 flex flex-col gap-2">
          {product.bestSeller && (
            <div className="rounded-full bg-amber-400 px-2.5 py-1 text-[9px] font-bold uppercase text-amber-900 shadow-lg backdrop-blur-sm">
              Bestseller
            </div>
          )}
          {product.isNew && (
            <div className="rounded-full bg-emerald-500 px-2.5 py-1 text-[9px] font-bold uppercase text-white shadow-lg">
              New
            </div>
          )}
        </div>

        {/* Discount badge - Hidden for cleaner look */}
        {/* {discountPercentage > 0 && (
                    <div className="absolute top-3 right-3 bg-rose-500 text-white text-[10px] font-bold px-2 py-1 rounded-lg shadow-lg">
                        -{discountPercentage}%
                    </div>
                )} */}

        {/* Quick action button on hover */}
        <div
          className={`absolute bottom-3 left-3 right-3 transition-all duration-300 ${
            isHovered ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
          }`}
        >
          <button
            className="w-full rounded-lg bg-white/95 py-2.5 text-xs font-semibold uppercase tracking-wide text-gray-900 shadow-lg backdrop-blur-sm transition-colors hover:bg-white"
            onClick={(e) => {
              e.stopPropagation();
              onClick();
            }}
          >
            Quick View
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col p-4">
        {/* Brand */}
        <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
          {product.brand || 'Stationery Junction'}
        </p>

        {/* Product Name */}
        <h3 className="mb-3 line-clamp-2 text-sm font-semibold leading-snug text-gray-900 transition-colors duration-300 group-hover:text-rose-500">
          {product.name}
        </h3>

        {/* Price */}
        <div className="mt-auto flex items-baseline gap-2">
          <span className="text-base font-bold text-gray-900">
            ₹{product.price || product.mrp || 0}
          </span>
          {product.mrp && product.mrp > product.price && (
            <>
              <span className="text-xs text-gray-400 line-through">₹{product.mrp}</span>
              <span className="text-xs font-semibold text-rose-500">
                ({discountPercentage}% off)
              </span>
            </>
          )}
        </div>

        {/* Cart controls */}
        {onAddToCart && (
          <div className="mt-3" onClick={(e) => e.stopPropagation()}>
            {cartQuantity > 0 ? (
              <div className="flex items-center justify-between overflow-hidden rounded-lg border border-gray-200">
                <button
                  onClick={onDecrement}
                  className="flex h-8 w-8 items-center justify-center text-gray-700 transition-colors hover:bg-gray-100 active:bg-gray-200"
                  aria-label="Decrease quantity"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
                  </svg>
                </button>
                <span className="flex-1 text-center text-sm font-bold text-gray-900">{cartQuantity}</span>
                <button
                  onClick={onIncrement}
                  className="flex h-8 w-8 items-center justify-center text-gray-700 transition-colors hover:bg-gray-100 active:bg-gray-200"
                  aria-label="Increase quantity"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                </button>
              </div>
            ) : (
              <button
                onClick={onAddToCart}
                disabled={!product.stock || product.stock <= 0}
                className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-gray-900 py-2 text-xs font-semibold text-white transition-colors hover:bg-gray-700 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-400"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                {!product.stock || product.stock <= 0 ? 'Out of Stock' : 'Add to Cart'}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Subtle border that appears on hover */}
      <div
        className={`pointer-events-none absolute inset-0 rounded-2xl border-2 transition-colors duration-300 ${
          isHovered ? 'border-rose-100' : 'border-transparent'
        }`}
      />
    </div>
  );
}
