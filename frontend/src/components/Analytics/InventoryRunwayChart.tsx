'use client';

import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface InventoryRunwayChartProps { startDate: Date | null; endDate: Date | null; limit?: number; }

const riskColor = (days: number | null) => {
  if (days === null) return '#d1d5db';
  if (days <= 7) return '#ef4444';
  if (days <= 21) return '#f59e0b';
  return '#10b981';
};

export default function InventoryRunwayChart({ startDate, endDate, limit = 15 }: InventoryRunwayChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/inventory-runway', { params });
      const rows = (r.data || []).filter((row: any) => row.daysRemaining !== null).slice(0, limit);
      setData(rows);
    } catch (e) { logger.error('inventory-runway', e); setData([]); } finally { setLoading(false); }
  };

  const critical = data.filter(r => r.daysRemaining !== null && r.daysRemaining <= 7).length;
  const warning = data.filter(r => r.daysRemaining !== null && r.daysRemaining > 7 && r.daysRemaining <= 21).length;

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <div className="mb-2 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold">Inventory Runway</h3>
          <p className="text-xs text-gray-400">Days of stock left at current sell rate</p>
        </div>
        <div className="flex gap-3 text-xs">
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" />{critical} critical</span>
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-400" />{warning} warning</span>
        </div>
      </div>
      {loading ? (
        <div className="flex h-64 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : data.length === 0 ? (
        <div className="flex h-64 items-center justify-center"><p className="text-gray-500">No products with sales data</p></div>
      ) : (
        <ResponsiveContainer width="100%" height={Math.max(200, data.length * 26)}>
          <BarChart data={data} layout="vertical" margin={{ top:0, right:30, left:0, bottom:0 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
            <XAxis type="number" tick={{ fontSize:11 }} unit=" d" />
            <YAxis dataKey="name" type="category" tick={{ fontSize:10 }} width={110}
              tickFormatter={(v: string) => v.length > 16 ? v.slice(0, 15) + '\u2026' : v} />
            <Tooltip formatter={(v: any) => [`${v} days`, 'Days Remaining']} labelFormatter={(l: any) => `Product: ${l}`} />
            <Bar dataKey="daysRemaining" radius={[0,3,3,0]} name="Days Remaining">
              {data.map((row, i) => <Cell key={i} fill={riskColor(row.daysRemaining)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
      <div className="mt-2 flex gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" />&le; 7 days</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-400" />8-21 days</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-green-500" />&gt; 21 days</span>
      </div>
    </div>
  );
}
