'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';

interface SalesByProductProps {
  startDate: Date | null;
  endDate: Date | null;
  currency: 'INR' | 'USD';
  limit?: number;
}

export default function SalesByProduct({
  startDate,
  endDate,
  currency,
  limit = 10,
}: SalesByProductProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate, limit]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = { limit };
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();

      const response = await api.get('/analytics/sales-by-product', { params });
      setData(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch sales by product:', error);
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
        <h3 className="mb-4 text-lg font-semibold">Total sales by product</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Total sales by product</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-4 text-lg font-semibold">Total sales by product</h3>
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="text-sm">{item.name || 'Unknown Product'}</span>
            <span className="text-sm font-medium">{formatCurrency(item.revenue || 0)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
