'use client';

import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface BuyerFrequencyChartProps { startDate: Date | null; endDate: Date | null; currency: 'INR' | 'USD'; }

const COLORS = ['#6366f1', '#10b981'];

export default function BuyerFrequencyChart({ startDate, endDate, currency }: BuyerFrequencyChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/customer-frequency', { params });
      setData(r.data || []);
    } catch (e) { logger.error('customer-frequency', e); setData([]); } finally { setLoading(false); }
  };

  const fmt = (v: any) => currency === 'USD' ? `$${(v / 82).toFixed(0)}` : `\u20B9${Math.round(v).toLocaleString('en-IN')}`;
  const pieData = data.map(d => ({ name: d.type, value: d.customers }));

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-3 text-lg font-semibold">One-Time vs Repeat Buyers</h3>
      {loading ? (
        <div className="flex h-52 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : data.length === 0 ? (
        <div className="flex h-52 items-center justify-center"><p className="text-gray-500">No data for this date range</p></div>
      ) : (
        <div className="flex items-center gap-4">
          <ResponsiveContainer width={130} height={130}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={38} outerRadius={62} dataKey="value" paddingAngle={4}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={((v: any, n: any) => [`${v} customers`, n]) as any} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-1 flex-col gap-2">
            {data.map((row, i) => (
              <div key={row.type} className="rounded-lg p-2.5" style={{ background: COLORS[i] + '14' }}>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full" style={{ background: COLORS[i] }} />
                  <span className="text-sm font-semibold">{row.type}</span>
                </div>
                <div className="mt-1 grid grid-cols-3 gap-1 text-xs text-gray-600">
                  <div><div className="font-medium">{row.customers}</div><div>customers</div></div>
                  <div><div className="font-medium">{row.orders}</div><div>orders</div></div>
                  <div><div className="font-medium">{fmt(row.revenue)}</div><div>revenue</div></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
