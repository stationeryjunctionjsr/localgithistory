'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface SessionsOverTimeChartProps {
  startDate: Date | null;
  endDate: Date | null;
}

export default function SessionsOverTimeChart({ startDate, endDate }: SessionsOverTimeChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/sessions-over-time', { params });
      setData(r.data || []);
    } catch (e) { logger.error('sessions-over-time', e); setData([]); } finally { setLoading(false); }
  };

  const fmt = (p: string) => p ? new Date(p).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : '';
  const totalS = data.reduce((s, d) => s + (d.sessions || 0), 0);
  const totalV = data.reduce((s, d) => s + (d.uniqueVisitors || 0), 0);

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <div className="mb-1 flex items-start justify-between">
        <h3 className="text-lg font-semibold">Sessions Over Time</h3>
        <div className="text-right text-xs text-gray-500">
          <div>{totalS.toLocaleString()} sessions</div>
          <div>{totalV.toLocaleString()} unique visitors</div>
        </div>
      </div>
      {loading ? (
        <div className="flex h-52 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : data.length === 0 ? (
        <div className="flex h-52 items-center justify-center"><p className="text-gray-500">No data for this date range</p></div>
      ) : (
        <ResponsiveContainer width="100%" height={210}>
          <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="period" tickFormatter={fmt} tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: number, n: string) => [v.toLocaleString(), n]} labelFormatter={fmt} />
            <Legend />
            <Line type="monotone" dataKey="sessions" stroke="#6366f1" strokeWidth={2} dot={false} name="Sessions" />
            <Line type="monotone" dataKey="uniqueVisitors" stroke="#10b981" strokeWidth={2} dot={false} name="Unique Visitors" />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
