'use client';

import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface RFMSegmentsChartProps { startDate: Date | null; endDate: Date | null; }

const COLORS: Record<string, string> = {
  Champion: '#10b981', Loyal: '#6366f1', Promising: '#f59e0b', 'At Risk': '#ef4444', Dormant: '#9ca3af',
};

export default function RFMSegmentsChart({ startDate, endDate }: RFMSegmentsChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/rfm-segments', { params });
      setData(r.data || []);
    } catch (e) { logger.error('rfm-segments', e); setData([]); } finally { setLoading(false); }
  };

  const segments = Object.entries(COLORS).map(([seg, color]) => {
    const rows = data.filter(r => r.segment === seg);
    return { name: seg, value: rows.length, revenue: rows.reduce((s, r) => s + (r.totalSpend || 0), 0), color };
  }).filter(s => s.value > 0);

  const total = segments.reduce((s, seg) => s + seg.value, 0);

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-3 text-lg font-semibold">Customer Segments (RFM)</h3>
      {loading ? (
        <div className="flex h-64 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : segments.length === 0 ? (
        <div className="flex h-64 items-center justify-center"><p className="text-gray-500">No data for this date range</p></div>
      ) : (
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="flex-1">
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={segments} cx="50%" cy="50%" innerRadius={48} outerRadius={78} paddingAngle={3} dataKey="value">
                  {segments.map((seg, i) => <Cell key={i} fill={seg.color} />)}
                </Pie>
                <Tooltip formatter={(v: number, n: string) => [`${v} customers`, n]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex min-w-[160px] flex-col justify-center gap-2">
            {segments.map(seg => (
              <div key={seg.name} className="flex items-center justify-between gap-2 text-sm">
                <div className="flex items-center gap-1.5">
                  <span className="inline-block h-3 w-3 rounded-full" style={{ background: seg.color }} />
                  <span className="font-medium">{seg.name}</span>
                </div>
                <div className="text-right text-xs text-gray-500">
                  <div>{seg.value} ({total > 0 ? Math.round(seg.value / total * 100) : 0}%)</div>
                  <div>&#8377;{Math.round(seg.revenue).toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
