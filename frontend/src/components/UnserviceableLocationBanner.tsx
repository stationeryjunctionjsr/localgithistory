'use client';

import React from 'react';
import { usePincode } from '@/context/PincodeContext';

interface UnserviceableLocationBannerProps {
  className?: string;
}

export default function UnserviceableLocationBanner({ className = '' }: UnserviceableLocationBannerProps) {
  const { pincode, city, state, openPincodeModal } = usePincode();

  return (
    <div className={`mx-auto max-w-3xl px-4 py-16 text-center ${className}`}>
      <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-amber-50 shadow-inner border border-amber-200/60 animate-in zoom-in-90 duration-300">
        <span className="text-4xl">📍</span>
      </div>

      <h2 className="text-2xl font-bold tracking-tight text-neutral-900 sm:text-3xl">
        We are not in your city yet, but we will come soon!
      </h2>

      <p className="mx-auto mt-3 max-w-xl text-sm sm:text-base text-neutral-600 leading-relaxed">
        Delivery is currently not available for{' '}
        <span className="font-semibold text-neutral-900">
          PIN code {pincode || 'entered'}
          {city ? ` (${city}${state ? `, ${state}` : ''})` : ''}
        </span>
        . We operate hyperlocally with verified local sellers and are expanding to your neighborhood rapidly.
      </p>

      <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
        <button
          onClick={() => openPincodeModal(false)}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1a4d33] px-6 py-3.5 text-sm font-bold text-white shadow-md transition-all hover:bg-[#143e29] hover:shadow-lg active:scale-95"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span>Check Another Pincode</span>
        </button>
      </div>

      <div className="mt-12 rounded-2xl border border-dashed border-gray-200 bg-gray-50/50 p-6 text-xs text-gray-500">
        <p className="font-medium text-gray-700 mb-1">Are you a local retailer or seller in this area?</p>
        <p>Join Stationery Junction to offer rapid hyperlocal delivery to customers in your locality.</p>
      </div>
    </div>
  );
}
