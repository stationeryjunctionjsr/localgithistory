'use client';

import React, { useState, useEffect } from 'react';
import { logger } from '@/utils/logger';

const PLAY_STORE_URL =
  process.env.NEXT_PUBLIC_PLAY_STORE_URL ||
  'https://play.google.com/store/apps/details?id=com.stationeryjunction.app';
const ANDROID_PACKAGE = process.env.NEXT_PUBLIC_ANDROID_PACKAGE || 'com.stationeryjunction.app';
const APP_SCHEME = 'stationeryjunction';

export default function AndroidAppBanner() {
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [isAndroidMobile, setIsAndroidMobile] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const ua = navigator.userAgent.toLowerCase();
    const android = /android/i.test(ua);
    const mobile = /mobile|webos|tablet/i.test(ua) || window.innerWidth < 768;
    const isStandalone =
      (window as any).matchMedia?.('(display-mode: standalone)').matches ||
      (navigator as any).standalone === true;
    const isAndroidMobileBrowser = android && mobile && !isStandalone;

    setIsAndroidMobile(isAndroidMobileBrowser);
    if (!isAndroidMobileBrowser) return;

    try {
      const stored = localStorage.getItem('android_app_banner_dismissed');
      if (stored === 'true') setDismissed(true);
      else setVisible(true);
    } catch {
      setVisible(true);
    }
  }, []);

  const handleDismiss = () => {
    setVisible(false);
    setDismissed(true);
    try {
      localStorage.setItem('android_app_banner_dismissed', 'true');
    } catch (e) { logger.warn("Silent catch block:", e);  }
  };

  const handleDownload = () => {
    window.open(PLAY_STORE_URL, '_blank', 'noopener,noreferrer');
  };

  const handleOpenInApp = () => {
    const path =
      typeof window !== 'undefined' ? window.location.pathname + window.location.search : '';
    const pathPart = path.replace(/^\//, '');
    // Intent URL: opens app if installed, else can fall back to Play Store
    const intentUrl = `intent://${pathPart
}#Intent;scheme=${APP_SCHEME};package=${ANDROID_PACKAGE};S.browser_fallback_url=${encodeURIComponent(PLAY_STORE_URL)};end`;
    window.location.href = intentUrl;
  };

  if (!visible || !isAndroidMobile || dismissed) return null;

  return (
    <div
      className="sticky top-0 z-[49] flex items-center justify-between gap-3 border-b border-[#0f3322] bg-[#1a4d33] px-4 py-3 text-white md:hidden"
      style={{ paddingTop: 'max(12px, env(safe-area-inset-top))' }}
    >
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold">Get the Stationery Junction app</p>
        <p className="mt-0.5 text-xs text-white/80">Faster experience & exclusive offers</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={handleOpenInApp}
          className="rounded-lg bg-white/20 px-3 py-2 text-xs font-bold uppercase tracking-wide text-white active:bg-white/30"
        >
          Open in App
        </button>
        <button
          type="button"
          onClick={handleDownload}
          className="rounded-lg bg-white px-3 py-2 text-xs font-bold uppercase tracking-wide text-[#1a4d33] active:bg-gray-100"
        >
          Download App
        </button>
        <button
          type="button"
          onClick={handleDismiss}
          className="-mr-1 rounded-full p-2 text-white/80 hover:text-white active:bg-white/10"
          aria-label="Dismiss"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  );
}
