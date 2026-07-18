'use client';

import { useEffect, useRef, RefObject } from 'react';
import { trackRecommendationSectionView } from '@/utils/analytics';

/**
 * Call trackRecommendationSectionView when the recommendation section enters the viewport.
 * Use the returned ref on the section element. Fires at most once per mount.
 */
export function useRecommendationSectionView(
  slot: string = 'home_recommendations',
  options?: { rootMargin?: string; threshold?: number }
): RefObject<HTMLDivElement> {
  const ref = useRef<HTMLDivElement | null>(null);
  const fired = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || fired.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (!entry?.isIntersecting || fired.current) return;
        fired.current = true;
        trackRecommendationSectionView(slot);
      },
      {
        rootMargin: options?.rootMargin ?? '0px',
        threshold: options?.threshold ?? 0.2,
      }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [slot, options?.rootMargin, options?.threshold]);

  return ref;
}
