'use client';

import React, { useEffect, useState } from 'react';
import api from '@/utils/api';

// ── Status configuration ───────────────────────────────────────────────────
interface StepConfig {
  key: string;
  label: string;
  icon: React.ReactNode;
  color: string; // Tailwind text/bg colour for active
}

const STEP_CONFIGS: StepConfig[] = [
  {
    key: 'placed',
    label: 'Order Placed',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'bg-violet-600',
  },
  {
    key: 'pending',
    label: 'Awaiting Confirmation',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'bg-yellow-500',
  },
  {
    key: 'confirmed',
    label: 'Confirmed',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    ),
    color: 'bg-blue-500',
  },
  {
    key: 'processing',
    label: 'Processing',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582M4.582 9A7.001 7.001 0 0112 5c2.637 0 4.95 1.37 6.3 3.43M20 20v-5h-.581M19.419 15A7.001 7.001 0 0112 19a6.995 6.995 0 01-6.3-3.43" />
      </svg>
    ),
    color: 'bg-indigo-500',
  },
  {
    key: 'shipped',
    label: 'Shipped',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
      </svg>
    ),
    color: 'bg-orange-500',
  },
  {
    key: 'out_for_delivery',
    label: 'Out for Delivery',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
      </svg>
    ),
    color: 'bg-amber-500',
  },
  {
    key: 'delivered',
    label: 'Delivered',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
    color: 'bg-green-500',
  },
];

// Terminal non-success statuses shown separately
const TERMINAL_CONFIGS: Record<string, StepConfig> = {
  cancelled: {
    key: 'cancelled',
    label: 'Cancelled',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    color: 'bg-red-500',
  },
  declined: {
    key: 'declined',
    label: 'Declined',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    ),
    color: 'bg-red-600',
  },
  returned: {
    key: 'returned',
    label: 'Returned',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
      </svg>
    ),
    color: 'bg-gray-500',
  },
};

// Happy-path step order (keys only)
const STEP_ORDER = ['placed', 'pending', 'confirmed', 'processing', 'shipped', 'out_for_delivery', 'delivered'];

// ── Helpers ────────────────────────────────────────────────────────────────
function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: true,
    });
  } catch {
    return iso;
  }
}

// ── Types ──────────────────────────────────────────────────────────────────
interface TimelineEntry {
  status: string;
  changedAt: string;
  changedBy?: string | null;
  note?: string | null;
}

interface OrderTimelineProps {
  orderId: string;
  currentStatus: string;
}

// ── Component ──────────────────────────────────────────────────────────────
export default function OrderTimeline({ orderId, currentStatus }: OrderTimelineProps) {
  const [entries, setEntries] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!orderId) return;
    setLoading(true);
    api.get(`/orders/${orderId}/timeline`)
      .then((res) => {
        setEntries(res.data?.timeline || []);
      })
      .catch(() => {
        // On failure synthesise a minimal timeline from current status
        setEntries([]);
      })
      .finally(() => setLoading(false));
  }, [orderId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <span className="h-6 w-6 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  // Determine which statuses have been reached (from history or from current status as fallback)
  const reachedStatuses = new Set(entries.map((e) => e.status));
  if (reachedStatuses.size === 0) {
    // Fallback: synthesise from currentStatus
    const idx = STEP_ORDER.indexOf(currentStatus);
    if (idx === -1) {
      reachedStatuses.add(currentStatus);
    } else {
      for (let i = 0; i <= idx; i++) reachedStatuses.add(STEP_ORDER[i]);
    }
  }

  // Find timestamp for each reached status from history
  const timestampFor = (key: string): string | null => {
    const entry = [...entries].reverse().find((e) => e.status === key);
    return entry ? entry.changedAt : null;
  };

  const isCancelled = reachedStatuses.has('cancelled') || reachedStatuses.has('declined') || reachedStatuses.has('returned');
  const terminalKey = ['cancelled', 'declined', 'returned'].find((k) => reachedStatuses.has(k));
  const terminalConfig = terminalKey ? TERMINAL_CONFIGS[terminalKey] : null;

  // Steps to render — if cancelled, show only steps up to last reached happy-path step + terminal
  const lastHappyIdx = isCancelled
    ? STEP_ORDER.reduce((best, k, i) => (reachedStatuses.has(k) ? i : best), -1)
    : STEP_ORDER.indexOf(currentStatus);

  const stepsToShow = isCancelled
    ? STEP_CONFIGS.slice(0, lastHappyIdx + 1)
    : STEP_CONFIGS;

  return (
    <div className="relative mt-2">
      <ol className="relative">
        {stepsToShow.map((step, idx) => {
          const isReached = reachedStatuses.has(step.key);
          const isCurrent = !isCancelled && step.key === currentStatus;
          const ts = timestampFor(step.key);
          const isLast = idx === stepsToShow.length - 1;

          return (
            <li key={step.key} className="relative flex gap-4 pb-6 last:pb-0">
              {/* Vertical connector line */}
              {!isLast && (
                <div
                  className={`absolute left-[18px] top-8 bottom-0 w-0.5 ${
                    isReached ? 'bg-violet-300' : 'bg-gray-200'
                  }`}
                />
              )}

              {/* Circle icon */}
              <div
                className={`relative z-10 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border-2 ${
                  isCurrent
                    ? `${step.color} border-transparent text-white shadow-md ring-2 ring-violet-300 ring-offset-2`
                    : isReached
                    ? `${step.color} border-transparent text-white`
                    : 'border-gray-200 bg-white text-gray-300'
                }`}
              >
                {step.icon}
              </div>

              {/* Text */}
              <div className="flex flex-col justify-center min-h-[36px]">
                <p
                  className={`text-sm font-semibold leading-tight ${
                    isCurrent ? 'text-gray-900' : isReached ? 'text-gray-700' : 'text-gray-400'
                  }`}
                >
                  {step.label}
                  {isCurrent && (
                    <span className="ml-2 rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-violet-700">
                      Current
                    </span>
                  )}
                </p>
                {ts && (
                  <p className="mt-0.5 text-xs text-gray-400">{formatDate(ts)}</p>
                )}
              </div>
            </li>
          );
        })}

        {/* Terminal (cancelled/declined/returned) step */}
        {isCancelled && terminalConfig && (
          <li className="relative flex gap-4 pb-0 mt-0">
            {/* No connector needed after terminal */}
            <div
              className={`relative z-10 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border-2 ${terminalConfig.color} border-transparent text-white`}
            >
              {terminalConfig.icon}
            </div>
            <div className="flex flex-col justify-center min-h-[36px]">
              <p className="text-sm font-semibold text-gray-900">
                {terminalConfig.label}
                <span className="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-red-600">
                  Final
                </span>
              </p>
              {timestampFor(terminalConfig.key) && (
                <p className="mt-0.5 text-xs text-gray-400">{formatDate(timestampFor(terminalConfig.key)!)}</p>
              )}
            </div>
          </li>
        )}
      </ol>
    </div>
  );
}
