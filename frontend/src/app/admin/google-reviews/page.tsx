'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateTimeIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';

export default function GoogleReviewsManagement() {
  const { user } = useAuth();
  const [ratingData, setRatingData] = useState({ rating: 0, reviewCount: '', lastUpdated: '' });
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchRating();
  }, []);

  const fetchRating = async () => {
    try {
      const res = await api.get('/google-reviews/rating');
      setRatingData(res.data);
    } catch (_e) {
      toast.error('Failed to fetch current rating');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const res = await api.post('/google-reviews/refresh');
      if (res.data) {
        setRatingData(res.data);
        toast.success('Successfully synced live data from Google!');
      }
    } catch (e: any) {
      console.error(e);
      const errorMsg =
        e.response?.data?.detail ||
        e.message ||
        'Google is currently blocking the request. Please try again later.';
      toast.error(errorMsg);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;

  return (
    <div className="mx-auto max-w-2xl p-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex items-center justify-between">
          <h1 className="mb-2 inline-flex items-center gap-3 text-2xl font-bold text-slate-800">
            Google Reviews Integration <RefreshButton onRefresh={fetchRating} />
          </h1>
        </div>
        <p className="mb-8 text-slate-500">
          Manage how your Google Business rating appears on the customer dashboard.
        </p>

        <div className="mb-8 flex flex-col items-center rounded-xl bg-slate-50 p-6 text-center">
          <div className="mb-4 rounded-full bg-blue-600 p-4 shadow-lg">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="white">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-1 .67-2.26 1.07-3.71 1.07-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path d="M5.84 14.11c-.22-.67-.35-1.39-.35-2.11s.13-1.44.35-2.11V7.05H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.95l3.66-2.84z" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.05l3.66 2.84c.87-2.6 3.3-4.51 6.16-4.51z" />
            </svg>
          </div>

          {loading ? (
            <div className="flex animate-pulse flex-col items-center">
              <div className="mb-2 h-8 w-24 rounded bg-slate-200"></div>
              <div className="h-4 w-40 rounded bg-slate-200"></div>
            </div>
          ) : (
            <>
              <div className="mb-2 flex items-center gap-2">
                <span className="text-4xl font-black text-slate-800">{ratingData.rating}</span>
                <div className="flex">
                  {[...Array(5)].map((_, i) => (
                    <svg
                      key={i}
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill={i < Math.floor(ratingData.rating) ? '#fbbf24' : '#e5e7eb'}
                    >
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                    </svg>
                  ))}
                </div>
              </div>
              <p className="text-sm font-bold uppercase tracking-widest text-slate-600">
                {ratingData.reviewCount} Reviews on Google
              </p>
            </>
          )}
        </div>

        <div className="space-y-4">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-4 font-bold text-white shadow-lg shadow-indigo-200 transition-all hover:bg-indigo-700 disabled:opacity-50"
          >
            {isRefreshing ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            ) : (
              <>
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Refresh from Google Link
              </>
            )}
          </button>

          <p className="text-center text-[10px] italic text-slate-400">
            This will attempt to scrape the latest rating from your Google reviews link. Note that
            Google&apos;s bot protection may occasionally block this.
          </p>

          {ratingData.lastUpdated && (
            <div className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-100 bg-slate-50 py-2 text-[11px] text-slate-400">
              <svg
                className="h-3 w-3 text-emerald-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span>Last synced: {formatDateTimeIST(ratingData.lastUpdated)}</span>
            </div>
          )}
        </div>

        <div className="mt-12 border-t border-slate-100 pt-8">
          <h3 className="mb-4 font-bold text-slate-800">Link Configuration</h3>
          <div className="flex items-center justify-between gap-4 rounded-lg bg-slate-50 p-4">
            <code className="break-all text-xs text-slate-600">
              https://share.google/6nwo4Mqy2qMRtztbF
            </code>
            <a
              href="https://share.google/6nwo4Mqy2qMRtztbF"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 text-xs font-bold text-indigo-600 hover:underline"
            >
              Open Link
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
