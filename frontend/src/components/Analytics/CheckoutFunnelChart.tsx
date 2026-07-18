'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';

interface CheckoutFunnelChartProps {
  startDate: Date | null;
  endDate: Date | null;
}

interface FunnelStage {
  count: number;
  percentage: number;
  drop_percentage?: number;
}

interface FunnelData {
  cart?: FunnelStage;
  shipping?: FunnelStage;
  review?: FunnelStage;
  payment?: FunnelStage;
  completed?: FunnelStage;
  overall_checkout_conversion?: number;
}

const STAGES: { key: keyof FunnelData; label: string; color: string }[] = [
  { key: 'cart', label: 'Cart View', color: '#6366f1' },
  { key: 'shipping', label: 'Shipping Address (Step 1)', color: '#8b5cf6' },
  { key: 'review', label: 'Order Review (Step 2)', color: '#a78bfa' },
  { key: 'payment', label: 'Payment Method (Step 3)', color: '#ec4899' },
  { key: 'completed', label: 'Completed Order', color: '#10b981' },
];

export default function CheckoutFunnelChart({ startDate, endDate }: CheckoutFunnelChartProps) {
  const [data, setData] = useState<FunnelData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();

      const response = await api.get('/analytics/checkout-funnel', { params });
      const d = response.data;
      setData(d && typeof d === 'object' && !Array.isArray(d) ? d : null);
    } catch (error) {
      console.error('Failed to fetch checkout funnel:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Checkout Funnel</h3>
        <div className="flex h-72 items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600"></div>
            <p className="text-sm text-gray-500">Loading checkout stages...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data || !data.cart) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Checkout Funnel</h3>
        <div className="flex h-72 items-center justify-center">
          <p className="text-gray-500">No checkout data available</p>
        </div>
      </div>
    );
  }

  const cartCount = data.cart?.count || 1;
  const overallRate = data.overall_checkout_conversion?.toFixed(1) ?? '0.0';

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Checkout Funnel</h3>
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Cart → Complete</span>
      </div>
      <p className="mb-4 text-2xl font-bold text-violet-600">{overallRate}% conversion</p>

      <div className="space-y-3.5">
        {STAGES.map(({ key, label, color }) => {
          const stage = data[key] as FunnelStage | undefined;
          if (!stage) return null;
          const width = Math.max(4, (stage.count / cartCount) * 100);
          return (
            <div key={key} className="group">
              <div className="mb-1 flex items-center justify-between text-xs text-gray-600">
                <span className="font-semibold group-hover:text-gray-900 transition-colors duration-150">{label}</span>
                <span>
                  {stage.count.toLocaleString()} &nbsp;
                  <span className="text-gray-400">({stage.percentage?.toFixed(1)}%)</span>
                </span>
              </div>
              <div className="h-5 w-full overflow-hidden rounded-full bg-gray-100 p-0.5">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out group-hover:opacity-90"
                  style={{ width: `${width}%`, backgroundColor: color }}
                />
              </div>
              {stage.drop_percentage !== undefined && stage.drop_percentage > 0 && (
                <div className="mt-0.5 flex justify-end gap-1 text-[10px] font-medium text-red-500 animate-pulse">
                  <span>▼ {stage.drop_percentage.toFixed(1)}% drop-off</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
