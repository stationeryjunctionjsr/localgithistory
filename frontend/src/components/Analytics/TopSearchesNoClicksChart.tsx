'use client';

import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface TopSearchesNoClicksChartProps { startDate: Date | null; endDate: Date | null; limit?: number; }

export default function TopSearchesNoClicksChart({ startDate, endDate, limit = 10 }: TopSearchesNoClicksChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/searches-no-clicks', { params });
      setData((r.data || []).slice(0, limit));
    } catch (e) { logger.error('searches-no-clicks', e); setData([]); } finally { setLoading(false); }
  };

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-1 text-lg font-semibold">Searches with No Clicks</h3>
      <p className="mb-3 text-xs text-gray-400">Users searched but did not click any product</p>
      {loading ? (
        <div className="flex h-56 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : data.length === 0 ? (
        <div className="flex h-56 items-center justify-center"><p className="text-gray-500">No data for this date range</p></div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
            <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
            <YAxis dataKey="term" type="category" tick={{ fontSize: 11 }} width={90} />
            <Tooltip formatter={(v: number) => [v, 'Searches']} />
            <Bar dataKey="searchCount" fill="#f59e0b" radius={[0, 3, 3, 0]} name="Searches" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
