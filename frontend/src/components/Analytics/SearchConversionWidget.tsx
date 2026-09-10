'use client';

import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface SearchConversionWidgetProps { startDate: Date | null; endDate: Date | null; }

export default function SearchConversionWidget({ startDate, endDate }: SearchConversionWidgetProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/search-conversion', { params });
      const row = Array.isArray(r.data) ? r.data[0] : r.data;
      setData(row || null);
    } catch (e) { logger.error('search-conversion', e); } finally { setLoading(false); }
  };

  const pieData = data ? [
    { name: 'Converted', value: data.convertedSessions },
    { name: 'Not Converted', value: data.nonConvertedSessions },
  ] : [];

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-3 text-lg font-semibold">Search → Order Rate</h3>
      {loading ? (
        <div className="flex h-40 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : !data || data.totalSearchSessions === 0 ? (
        <div className="flex h-40 items-center justify-center"><p className="text-gray-500">No data for this date range</p></div>
      ) : (
        <div className="flex items-center gap-3">
          <div className="relative flex-shrink-0">
            <ResponsiveContainer width={110} height={110}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={32} outerRadius={50} dataKey="value" paddingAngle={3}>
                  <Cell fill="#10b981" /><Cell fill="#e5e7eb" />
                </Pie>
                <Tooltip formatter={((v: any, n: any) => [v, n]) as any} />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <span className="text-lg font-bold text-gray-800">{data.conversionRate}%</span>
            </div>
          </div>
          <div className="flex flex-col gap-2 text-sm">
            <div><span className="font-semibold">{data.totalSearchSessions}</span><span className="ml-1 text-gray-500">search sessions</span></div>
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
              <span className="font-medium">{data.convertedSessions}</span>
              <span className="text-gray-500">ordered</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-gray-200" />
              <span className="font-medium">{data.nonConvertedSessions}</span>
              <span className="text-gray-500">left without ordering</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
