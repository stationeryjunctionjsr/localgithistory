'use client';

import { useCallback } from 'react';
import { toast } from 'react-toastify';

export interface ShareOptions {
  title?: string;
  text?: string;
  url: string;
}

export function useShare() {
  const share = useCallback(async (options: ShareOptions) => {
    const { title = '', text = '', url } = options;
    const fullUrl = url.startsWith('http')
      ? url
      : typeof window !== 'undefined'
        ? `${window.location.origin}${url}`
        : url;

    if (typeof navigator !== 'undefined' && navigator.share) {
      try {
        await navigator.share({
          title: title || 'Stationery Junction',
          text: text || title,
          url: fullUrl,
        });
        toast.success('Link shared');
        return true;
      } catch (err: any) {
        if (err?.name === 'AbortError') return false;
        // Fallback to copy
      }
    }

    try {
      await navigator.clipboard.writeText(fullUrl);
      toast.success('Link copied to clipboard');
      return true;
    } catch {
      toast.error('Could not copy link');
      return false;
    }
  }, []);

  const canShare = typeof navigator !== 'undefined' && !!navigator.share;
  return { share, canShare };
}
