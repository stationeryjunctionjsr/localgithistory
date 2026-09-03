'use client';

import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface BounceRateChartProps { startDate: Date | null; endDate: Date | null; }

export default function BounceRateChart({ startDate, endDate }: BounceRateChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/bounce-rate', { params });
      setData(r.data || []);
    } catch (e) { logger.error('bounce-rate', e); setData([]); } finally { setLoading(false); }
  };

  const avg = data.length > 0 ? (data.reduce((s, d) => s + (d.bounceRate || 0), 0) / data.length).toFixed(1) : '—';
  const fmt = (p: string) => p ? new Date(p).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : '';

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <div className="mb-1 flex items-start justify-between">
        <h3 className="text-lg font-semibold">Bounce Rate</h3>
        <div className="text-right">
          <span className="text-2xl font-bold text-red-500">{avg}%</span>
          <p className="text-xs text-gray-400">avg over period</p>
        </div>
      </div>
      {loading ? (
        <div className="flex h-52 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : data.length === 0 ? (
        <div className="flex h-52 items-center justify-center"><p className="text-gray-500">No data for this date range</p></div>
      ) : (
        <ResponsiveContainer width="100%" height={190}>
          <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="bounceGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="period" tickFormatter={fmt} tick={{ fontSize: 11 }} />
            <YAxis unit="%" tick={{ fontSize: 11 }} domain={[0, 100]} />
            <Tooltip formatter={(v: number) => [`${v}%`, 'Bounce Rate']} labelFormatter={fmt} />
            <Area type="monotone" dataKey="bounceRate" stroke="#ef4444" strokeWidth={2} fill="url(#bounceGrad)" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
