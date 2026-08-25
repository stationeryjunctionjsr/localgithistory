'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface SalesBreakdownProps {
  startDate: Date | null;
  endDate: Date | null;
  currency: 'INR' | 'USD';
}

export default function SalesBreakdown({ startDate, endDate, currency }: SalesBreakdownProps) {
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

      const response = await api.get('/analytics/sales-breakdown', { params });
      setData(response.data);
      setLoading(false);
    } catch (error) {
      logger.error('Failed to fetch sales breakdown:', error);
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
        <h3 className="mb-4 text-lg font-semibold">Total sales breakdown</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Total sales breakdown</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  const breakdownItems = [
    { label: 'Gross sales', value: data.gross_sales || 0 },
    { label: 'Discounts', value: data.discounts || 0 },
    { label: 'Returns', value: data.returns || 0 },
    { label: 'Net sales', value: data.net_sales || 0 },
    { label: 'Shipping charges', value: data.shipping_charges || 0 },
    { label: 'Return fees', value: data.return_fees || 0 },
    { label: 'Taxes', value: data.taxes || 0 },
    { label: 'Total sales', value: data.total_sales || 0 },
  ];

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-4 text-lg font-semibold">Total sales breakdown</h3>
      <div className="space-y-3">
        {breakdownItems.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="text-sm text-gray-600">{item.label}</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">{formatCurrency(item.value)}</span>
              <div className="h-1 w-16 rounded bg-gray-200"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
