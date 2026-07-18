'use client';

import { useState, useEffect } from 'react';
import api from '@/utils/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';

interface UserEngagementChartProps {
  startDate: Date | null;
  endDate: Date | null;
}

export default function UserEngagementChart({ startDate, endDate }: UserEngagementChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const params: any = {};
        if (startDate) params.start_date = startDate.toISOString();
        if (endDate) params.end_date = endDate.toISOString();

        const response = await api.get('/analytics/all-user-engagement', { params });
        setData(response.data.duration_buckets);
      } catch (error) {
        console.error('Failed to fetch user engagement data', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [startDate, endDate]);

  if (loading) {
    return (
      <div className="flex h-80 items-center justify-center rounded-lg border bg-white p-4">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">User Engagement (Avg Session Duration)</h3>
        <p className="text-sm text-gray-500">Distribution of users by their average session time</p>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="range" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <RechartsTooltip cursor={{ fill: 'transparent' }} />
            <Bar dataKey="count" fill="#8884d8" radius={[4, 4, 0, 0]} name="Users Count" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
