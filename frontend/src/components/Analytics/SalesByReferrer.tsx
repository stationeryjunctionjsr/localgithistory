'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface SalesByReferrerProps {
  startDate: Date | null;
  endDate: Date | null;
  currency: 'INR' | 'USD';
}

export default function SalesByReferrer({ startDate, endDate, currency }: SalesByReferrerProps) {
  const [data, setData] = useState<any[]>([]);
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

      const response = await api.get('/analytics/sales-by-referrer', { params });
      setData(response.data || []);
      setLoading(false);
    } catch (error) {
      logger.error('Failed to fetch sales by referrer:', error);
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
        <h3 className="mb-4 text-lg font-semibold">Sessions by referrer</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Sessions by referrer</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-4 text-lg font-semibold">Sessions by referrer</h3>
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="text-sm capitalize">{item.referrer || 'Unknown'}</span>
            <span className="text-sm font-medium">{formatCurrency(item.sales || 0)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
