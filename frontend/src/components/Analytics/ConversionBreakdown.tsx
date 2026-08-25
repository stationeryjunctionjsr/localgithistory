'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface ConversionBreakdownProps {
  startDate: Date | null;
  endDate: Date | null;
}

export default function ConversionBreakdown({ startDate, endDate }: ConversionBreakdownProps) {
  const [data, setData] = useState<any>(null);
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

      const response = await api.get('/analytics/conversion-breakdown', { params });
      setData(response.data);
      setLoading(false);
    } catch (error) {
      logger.error('Failed to fetch conversion breakdown:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Conversion rate breakdown</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Conversion rate breakdown</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  const stages = [
    { key: 'sessions', label: 'Sessions' },
    { key: 'added_to_cart', label: 'Added to cart' },
    { key: 'reached_checkout', label: 'Reached checkout' },
    { key: 'completed', label: 'Completed' },
  ];

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-2 text-lg font-semibold">Conversion rate breakdown</h3>
      <p className="mb-4 text-xl font-bold">{data.overall_conversion_rate?.toFixed(1) || 0}% –</p>
      <div className="grid grid-cols-4 gap-2">
        {stages.map((stage) => {
          const stageData = data[stage.key] || {};
          return (
            <div key={stage.key} className="text-center">
              <p className="mb-1 text-xs text-gray-600">{stageData.percentage?.toFixed(1) || 0}%</p>
              <p className="mb-1 text-sm font-bold">{stageData.count || 0}</p>
              <div className="flex items-center justify-center gap-1">
                <svg
                  className="h-4 w-4 text-red-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
                <span className="text-xs text-gray-500">
                  {stageData.drop_percentage?.toFixed(1) || 0}%
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">{stage.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
