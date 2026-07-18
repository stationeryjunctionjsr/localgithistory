'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';

interface ConversionRateChartProps {
  startDate: Date | null;
  endDate: Date | null;
}

interface FunnelStage {
  count: number;
  percentage: number;
  drop_percentage: number;
}

interface FunnelData {
  sessions?: FunnelStage;
  added_to_cart?: FunnelStage;
  reached_checkout?: FunnelStage;
  completed?: FunnelStage;
  overall_conversion_rate?: number;
}

const STAGES: { key: keyof FunnelData; label: string; color: string }[] = [
  { key: 'sessions', label: 'Sessions', color: '#6366f1' },
  { key: 'added_to_cart', label: 'Added to Cart', color: '#8b5cf6' },
  { key: 'reached_checkout', label: 'Reached Checkout', color: '#a78bfa' },
  { key: 'completed', label: 'Completed', color: '#10b981' },
];

export default function ConversionRateChart({ startDate, endDate }: ConversionRateChartProps) {
  const [data, setData] = useState<FunnelData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = { group_by: 'day' };
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();

      const response = await api.get('/analytics/conversion-rate', { params });
      // API returns a dict (funnel), not an array
      const d = response.data;
      setData(d && typeof d === 'object' && !Array.isArray(d) ? d : null);
    } catch (error) {
      console.error('Failed to fetch conversion rate:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Conversion Funnel</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!data || !data.sessions) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Conversion Funnel</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  const sessionCount = data.sessions?.count || 1;
  const overallRate = data.overall_conversion_rate?.toFixed(1) ?? '0.0';

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-1 text-lg font-semibold">Conversion Funnel</h3>
      <p className="mb-4 text-2xl font-bold text-indigo-600">{overallRate}%</p>

      <div className="space-y-3">
        {STAGES.map(({ key, label, color }) => {
          const stage = data[key] as FunnelStage | undefined;
          if (!stage) return null;
          const width = Math.max(4, (stage.count / sessionCount) * 100);
          return (
            <div key={key}>
              <div className="mb-1 flex items-center justify-between text-xs text-gray-600">
                <span className="font-medium">{label}</span>
                <span>
                  {stage.count.toLocaleString()} &nbsp;
                  <span className="text-gray-400">({stage.percentage?.toFixed(1)}%)</span>
                </span>
              </div>
              <div className="h-5 w-full overflow-hidden rounded-full bg-gray-100">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${width}%`, backgroundColor: color }}
                />
              </div>
              {stage.drop_percentage > 0 && (
                <p className="mt-0.5 text-right text-[10px] text-red-400">
                  ▼ {stage.drop_percentage.toFixed(1)}% drop
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
