'use client';

import { useState, useEffect, useRef } from 'react';
import { usePincode } from '@/context/PincodeContext';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

/**
 * Map of { sellerId → unavailableUntil (ISO 8601 UTC string) }
 * for sellers in the current pincode's zone who are in an active time-off window.
 *
 * An empty map means every seller in the zone is currently available.
 */
export type SellerAvailabilityMap = Record<string, string>;

const CACHE_TTL_MS = 60_000; // re-fetch at most once per minute

let _cachedPincode: string | null = null;
let _cachedMap: SellerAvailabilityMap = {};
let _cacheExpiry = 0;

/**
 * Hook that returns the seller availability map for the current pincode's zone.
 *
 * Usage in a product card:
 *   const { sellerAvailability } = useSellerAvailability();
 *   const sellerId = product.sellers?.[0]?.sellerId;
 *   const unavailableUntil = sellerId ? sellerAvailability[sellerId] : undefined;
 *   // If truthy → show grey overlay + "Back at {format(unavailableUntil)}"
 */
export function useSellerAvailability() {
  const { pincode } = usePincode();
  const [sellerAvailability, setSellerAvailability] = useState<SellerAvailabilityMap>({});
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!pincode) {
      setSellerAvailability({});
      return;
    }

    // Serve module-level cache if still fresh and same pincode
    if (
      pincode === _cachedPincode &&
      Date.now() < _cacheExpiry
    ) {
      setSellerAvailability(_cachedMap);
      return;
    }

    // Cancel any in-flight request for a previous pincode
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    api
      .get('/seller-availability/zone-status', {
        params: { pincode },
        signal: abortRef.current.signal,
      })
      .then((res) => {
        const map: SellerAvailabilityMap = res.data?.unavailableSellers ?? {};
        // Update module-level cache
        _cachedPincode = pincode;
        _cachedMap = map;
        _cacheExpiry = Date.now() + CACHE_TTL_MS;
        setSellerAvailability(map);
      })
      .catch((err) => {
        if (err?.name === 'CanceledError' || err?.name === 'AbortError') return;
        logger.warn('useSellerAvailability: failed to fetch zone status', err);
        setSellerAvailability({});
      });

    return () => {
      abortRef.current?.abort();
    };
  }, [pincode]);

  return { sellerAvailability };
}

/**
 * Format an ISO UTC timestamp into a readable "back at" string.
 * E.g. "2026-09-23T18:00:00Z" → "6:00 PM" (today) or "Wed, 24 Sep 6:00 PM"
 */
export function formatUnavailableUntil(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const isToday =
      date.getDate() === now.getDate() &&
      date.getMonth() === now.getMonth() &&
      date.getFullYear() === now.getFullYear();

    if (isToday) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString([], {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'later';
  }
}
