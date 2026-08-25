'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface CustomerCohortProps {
  startDate: Date | null;
  endDate: Date | null;
}

export default function CustomerCohort({ startDate, endDate }: CustomerCohortProps) {
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

      const response = await api.get('/analytics/customer-cohort', { params });
      setData(response.data || []);
      setLoading(false);
    } catch (error) {
      logger.error('Failed to fetch customer cohort:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Customer cohort analysis</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Customer cohort analysis</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  // eslint-disable-next-line unused-imports/no-unused-vars
  const maxMonths = Math.max(...data.map((d) => d.months?.length || 0), 0);

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-4 text-lg font-semibold">Customer cohort analysis</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="p-2 text-left">Cohort</th>
              <th className="p-2 text-left">Months</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => (
              <tr key={index}>
                <td className="p-2">{item.cohort}</td>
                <td className="p-2">
                  <div className="flex gap-1">
                    {item.months?.map((count: number, monthIndex: number) => (
                      <span key={monthIndex} className="rounded bg-gray-100 px-1 py-0.5">
                        {count > 0 ? `${count}%` : '0%'}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
