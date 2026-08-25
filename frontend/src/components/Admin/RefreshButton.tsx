'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { logger } from '@/utils/logger';

interface RefreshButtonProps {
  onRefresh?: () => Promise<any> | any;
}

export default function RefreshButton({ onRefresh }: RefreshButtonProps) {
  const router = useRouter();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (onRefresh) {
      try {
        await Promise.resolve(onRefresh());
      } catch (err) {
        logger.error('Failed to run onRefresh:', err);
      }
    } else {
      router.refresh();
    }
    setTimeout(() => {
      setIsRefreshing(false);
    }, 600);
  };

  return (
    <button
      onClick={handleRefresh}
      disabled={isRefreshing}
      className="inline-flex items-center justify-center text-slate-400 hover:text-slate-600 active:scale-90 transition-all duration-350 disabled:pointer-events-none focus:outline-none"
      title="Refresh Page"
      aria-label="Refresh Page"
    >
      <svg
        className={`h-5 w-5 transition-transform duration-500 ${isRefreshing ? 'animate-spin' : 'hover:rotate-180'}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        strokeWidth={2.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
        <path d="M3 3v5h5" />
        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
        <path d="M16 16h5v5" />
      </svg>
    </button>
  );
}

