'use client';

import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface SalesOverTimeChartProps {
  startDate: Date | null;
  endDate: Date | null;
  currency: 'INR' | 'USD';
}

export default function SalesOverTimeChart({
  startDate,
  endDate,
  currency,
}: SalesOverTimeChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = { group_by: 'hour' };
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();

      const response = await api.get('/analytics/sales-over-time', { params });
      setData(response.data || []);
      setLoading(false);
    } catch (error: any) {
      logger.error('Failed to fetch sales over time:', error);
      setLoading(false);
      setData([]); // Ensure data is empty array on error
    }
  };

  const formatCurrency = (amount: number) => {
    if (currency === 'USD') {
      return `$${(amount / 82).toFixed(2)}`;
    }
    return `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  };

  const totalSales = data.reduce((sum, item) => sum + (item.sales || 0), 0);

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md md:rounded-none">
        <h3 className="mb-4 text-lg font-semibold">Total sales over time</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md md:rounded-none">
        <h3 className="mb-4 text-lg font-semibold">Total sales over time</h3>
        <div className="flex h-64 flex-col items-center justify-center">
          <p className="mb-2 text-gray-500">No data for this date range</p>
          <p className="text-xs text-gray-400">Check console for API errors</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-2 text-lg font-semibold">Total sales over time</h3>
      <p className="mb-4 text-2xl font-bold">{formatCurrency(totalSales)}</p>
      <div style={{ width: '100%', height: '300px', minHeight: '300px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="period"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => formatCurrency(value)} />
            <Tooltip
              formatter={(value: any) => formatCurrency(value)}
              labelStyle={{ color: '#000' }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="sales"
              stroke="#3B82F6"
              strokeWidth={2}
              name="Sales"
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
