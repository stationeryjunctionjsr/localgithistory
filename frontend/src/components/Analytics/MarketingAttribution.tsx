'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';

interface MarketingAttributionProps {
  startDate: Date | null;
  endDate: Date | null;
  currency: 'INR' | 'USD';
}

export default function MarketingAttribution({
  startDate,
  endDate,
  currency,
}: MarketingAttributionProps) {
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

      const response = await api.get('/analytics/marketing-attribution', { params });
      setData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch marketing attribution:', error);
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    if (currency === 'USD') {
      return `$${(amount / 82).toFixed(2)}`;
    }
    return `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Sales attributed to marketing</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Sales attributed to marketing</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-4 text-lg font-semibold">Sales attributed to marketing</h3>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm">Marketing Sales</span>
          <span className="text-sm font-medium">{formatCurrency(data.marketing_sales || 0)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm">Total Sales</span>
          <span className="text-sm font-medium">{formatCurrency(data.total_sales || 0)}</span>
        </div>
        <div className="flex items-center justify-between border-t pt-2">
          <span className="text-sm font-semibold">Attribution</span>
          <span className="text-sm font-bold">{data.attribution_percentage?.toFixed(1) || 0}%</span>
        </div>
      </div>
    </div>
  );
}
