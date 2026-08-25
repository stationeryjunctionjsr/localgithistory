'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import { getImageUrl } from '@/utils/imageUrl';
import { logger } from '@/utils/logger';

const POPUP_SHOWN_KEY = 'launch_popup_shown_date';

export default function LaunchPopup() {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [banner, setBanner] = useState<any>(null);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const checkAndFetchPopup = async () => {
      try {
        // Only show inside the native mobile app (React Native WebView).
        // window.ReactNativeWebView is injected by react-native-webview and is
        // the same check that Expo's own DOM component bridge uses internally.
        const isNativeApp =
          typeof window !== 'undefined' &&
          typeof (window as any).ReactNativeWebView !== 'undefined';

        if (!isNativeApp) return;

        // Only show once per day
        const today = new Date().toISOString().split('T')[0];
        const lastShown = localStorage.getItem(POPUP_SHOWN_KEY);

        if (lastShown === today) return;

        setLoading(true);
        const res = await api.get('/banners/public', {
          params: { pageType: 'launch_modal' },
        });

        const banners = res.data || [];
        if (banners.length > 0) {
          setBanner(banners[0]);
          setVisible(true);
          localStorage.setItem(POPUP_SHOWN_KEY, today);
        }
      } catch (error) {
        logger.error('Error fetching launch popup:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAndFetchPopup();
  }, []);

  if (!visible || !banner) return null;

  const handlePress = () => {
    if (!banner) return;

    let targetUrl = banner.linkUrl;

    // Check for specific redirection rules in visibilityRules
    const launchRule = banner.visibilityRules?.find(
      (r: any) => r.pageType?.toLowerCase() === 'launch_modal'
    );
    if (launchRule && launchRule.pageIds?.length > 0) {
      const type = (launchRule.redirectType || 'category').toLowerCase();
      const id = launchRule.pageIds[0];
      if (type === 'category') targetUrl = `/categories/${encodeURIComponent(id)}`;
      else if (type === 'brand') targetUrl = `/brands/${encodeURIComponent(id)}`;
      else if (type === 'collection') targetUrl = `/collections/${encodeURIComponent(id)}`;
    }

    if (targetUrl) {
      router.push(targetUrl);
    }
    setVisible(false);
  };

  return (
    <div className="fixed inset-0 z-[2000] flex animate-fade-in items-end justify-center bg-black/50 backdrop-blur-[2px]">
      <div className="relative flex h-[60%] w-full animate-slide-up flex-col overflow-hidden rounded-t-[32px] bg-white shadow-2xl">
        <button
          onClick={() => setVisible(false)}
          className="absolute right-4 top-4 z-20 flex h-10 w-10 items-center justify-center rounded-full bg-gray-100 text-gray-500 transition-colors hover:bg-gray-200"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="relative h-1/2 w-full shrink-0" onClick={handlePress}>
            <img
              src={getImageUrl(banner.imageUrl || banner.image) || undefined}
              alt={banner.title || 'Special Offer'}
              className="h-full w-full object-cover"
            />
            <div className="absolute inset-x-0 top-0 mx-auto mt-3 h-1 w-12 rounded-full bg-gray-300 opacity-50" />
            <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent" />
          </div>

          <div className="flex flex-1 flex-col items-center justify-center bg-white/30 p-6 text-center backdrop-blur-sm">
            {banner.title && (
              <h2 className="mb-2 px-4 text-2xl font-black leading-tight tracking-tight text-gray-900">
                {banner.title}
              </h2>
            )}
            {banner.description && (
              <p className="mb-6 line-clamp-3 max-w-[280px] text-sm font-medium text-gray-600">
                {banner.description}
              </p>
            )}
            <button
              onClick={handlePress}
              className="flex w-full max-w-[280px] items-center justify-center gap-2 rounded-xl bg-[#ff3f6c] py-4 text-sm font-bold uppercase tracking-wider text-white shadow-lg shadow-[#ff3f6c]/20 transition-all active:scale-95"
            >
              <span>Explore Now</span>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
