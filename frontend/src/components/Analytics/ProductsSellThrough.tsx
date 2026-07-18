'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';

interface ProductsSellThroughProps {
  startDate: Date | null;
  endDate: Date | null;
  limit?: number;
}

export default function ProductsSellThrough({
  startDate,
  endDate,
  limit = 10,
}: ProductsSellThroughProps) {
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

      const response = await api.get('/analytics/products-sell-through', { params });
      setData(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch products sell-through:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Products by sell-through rate</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Products by sell-through rate</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-4 text-lg font-semibold">Products by sell-through rate</h3>
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium">{item.name || 'Unknown Product'}</p>
              <p className="text-xs text-gray-500">
                Sold: {item.sold || 0} | Stock: {item.stock || 0}
              </p>
            </div>
            <span className="text-sm font-bold">{item.sell_through_rate?.toFixed(1) || 0}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
