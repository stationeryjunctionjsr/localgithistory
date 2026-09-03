'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface SalesHeatmapProps { startDate: Date | null; endDate: Date | null; }

const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function SalesHeatmap({ startDate, endDate }: SalesHeatmapProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState<'orderCount'|'revenue'>('orderCount');

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/sales-heatmap', { params });
      setData(r.data || []);
    } catch (e) { logger.error('sales-heatmap', e); setData([]); } finally { setLoading(false); }
  };

  const grid: Record<string,Record<number,number>> = {};
  DAYS.forEach(d => { grid[d] = {}; });
  data.forEach(row => {
    if (!grid[row.dayOfWeek]) grid[row.dayOfWeek] = {};
    grid[row.dayOfWeek][row.hour] = metric === 'orderCount' ? row.orderCount : row.revenue;
  });
  const allVals = data.map(r => metric === 'orderCount' ? r.orderCount : r.revenue).filter(Boolean);
  const maxVal = allVals.length > 0 ? Math.max(...allVals) : 1;

  const cellColor = (val: number) => {
    if (!val) return '#f9fafb';
    const t = val / maxVal;
    const r = Math.round(224 - t * (224 - 67));
    const g = Math.round(231 - t * (231 - 56));
    const b = Math.round(254 - t * (254 - 202));
    return `rgb(${r},${g},${b})`;
  };

  const fmt = (h: number) => `${h === 0 ? 12 : h > 12 ? h - 12 : h}${h < 12 ? 'a' : 'p'}`;

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Sales Heatmap</h3>
        <div className="flex gap-1">
          {(['orderCount','revenue'] as const).map(m => (
            <button key={m} onClick={() => setMetric(m)}
              className={`rounded px-2 py-1 text-xs ${metric === m ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
              {m === 'orderCount' ? 'Orders' : 'Revenue'}
            </button>
          ))}
        </div>
      </div>
      {loading ? (
        <div className="flex h-56 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : data.length === 0 ? (
        <div className="flex h-56 items-center justify-center"><p className="text-gray-500">No data for this date range</p></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className="w-8 pr-1 text-right text-gray-400"></th>
                {HOURS.map(h => (
                  <th key={h} className={`text-center font-normal text-gray-400 ${h % 6 === 0 ? '' : 'opacity-0'}`} style={{fontSize:9}}>
                    {h % 6 === 0 ? fmt(h) : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DAYS.map(day => (
                <tr key={day}>
                  <td className="pr-1 text-right text-xs font-medium text-gray-500" style={{fontSize:9}}>{day.slice(0,3)}</td>
                  {HOURS.map(h => {
                    const val = grid[day]?.[h] || 0;
                    return (
                      <td key={h} title={`${day} ${fmt(h)}: ${val.toLocaleString()}`}>
                        <div className="h-4 w-full rounded-sm" style={{ backgroundColor: cellColor(val) }} />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-2 flex items-center gap-1 text-xs text-gray-400">
            <span>Less</span>
            {[0.1,0.3,0.5,0.7,0.9].map(f => (
              <div key={f} className="h-3 w-4 rounded-sm" style={{ backgroundColor: cellColor(maxVal * f) }} />
            ))}
            <span>More</span>
          </div>
        </div>
      )}
    </div>
  );
}
