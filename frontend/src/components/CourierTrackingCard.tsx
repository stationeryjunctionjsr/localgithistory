'use client';

import React from 'react';

interface CourierTrackingCardProps {
  partnerName?: string;
  awbCode?: string;
  trackingId?: string;
  estimatedDelivery?: string;
}

/**
 * CourierTrackingCard — shown inside customer order details for Pan-India
 * courier orders (fulfillment_type === 'courier'). Displays partner name, AWB,
 * expected delivery date, and a direct link to track on the courier's website.
 */
export default function CourierTrackingCard({
  partnerName,
  awbCode,
  trackingId,
  estimatedDelivery,
}: CourierTrackingCardProps) {
  const trackingRef = awbCode || trackingId || '';

  const trackingUrls: Record<string, string> = {
    delhivery: `https://www.delhivery.com/track/package/${trackingRef}`,
    shiprocket: `https://shiprocket.co/tracking/${trackingRef}`,
    blue_dart: `https://www.bluedart.com/tracking?trackFor=0&trackNo=${trackingRef}`,
    dtdc: `https://www.dtdc.in/trace.asp?strCnno=${trackingRef}`,
  };

  const partnerKey = (partnerName || '').toLowerCase().replace(/\s+/g, '_');
  const trackingUrl = trackingUrls[partnerKey] || '#';

  const formatDeliveryDate = (dateStr?: string) => {
    if (!dateStr) return null;
    try {
      return new Date(dateStr).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const formattedDate = formatDeliveryDate(estimatedDelivery);

  return (
    <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📦</span>
        <p className="text-sm font-semibold text-blue-800">Courier Delivery</p>
      </div>

      <div className="space-y-1.5 text-sm text-gray-700">
        {partnerName && (
          <div className="flex items-center gap-2">
            <span className="w-28 text-xs font-medium text-gray-500">Partner</span>
            <span className="font-semibold text-gray-800">{partnerName}</span>
          </div>
        )}
        {trackingRef && (
          <div className="flex items-center gap-2">
            <span className="w-28 text-xs font-medium text-gray-500">AWB / Tracking</span>
            <code className="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-mono text-blue-700">
              #{trackingRef}
            </code>
          </div>
        )}
        {formattedDate && (
          <div className="flex items-center gap-2">
            <span className="w-28 text-xs font-medium text-gray-500">Expected by</span>
            <span className="font-semibold text-gray-800">{formattedDate}</span>
          </div>
        )}
      </div>

      {trackingRef && trackingUrl !== '#' && (
        <a
          href={trackingUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-blue-600 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-blue-700"
        >
          Track on Courier Website
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      )}

      {!trackingRef && (
        <p className="mt-3 text-xs text-blue-600 italic">
          Tracking information will be available once the order is dispatched.
        </p>
      )}
    </div>
  );
}
