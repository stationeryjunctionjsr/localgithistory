'use client';

import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface SalesByChannelDetailedChartProps { startDate: Date | null; endDate: Date | null; currency: 'INR'|'USD'; }

type TabKey = 'revenue'|'orders'|'aov';

export default function SalesByChannelDetailedChart({ startDate, endDate, currency }: SalesByChannelDetailedChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<TabKey>('revenue');

  useEffect(() => { fetchData(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      const r = await api.get('/analytics/reports/sales-by-channel-detailed', { params });
      setData(r.data || []);
    } catch (e) { logger.error('sales-by-channel-detailed', e); setData([]); } finally { setLoading(false); }
  };

  const fmt = (v: number) => currency === 'USD' ? `$${(v/82).toFixed(0)}` : `\u20B9${Math.round(v).toLocaleString('en-IN')}`;
  const TABS: {key:TabKey;label:string;dataKey:string;formatter:(v:number)=>string}[] = [
    {key:'revenue',label:'Revenue',dataKey:'revenue',formatter:fmt},
    {key:'orders',label:'Orders',dataKey:'orderCount',formatter:(v)=>v.toLocaleString()},
    {key:'aov',label:'AOV',dataKey:'aov',formatter:fmt},
  ];
  const CLRS: Record<string,string> = {'Desktop Web':'#6366f1','Mobile Web':'#10b981','Mobile App':'#f59e0b'};
  const active = TABS.find(t => t.key === tab)!;

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Sales by Channel</h3>
        <div className="flex gap-1">
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`rounded px-2 py-1 text-xs ${tab === t.key ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>
      {loading ? (
        <div className="flex h-52 items-center justify-center"><p className="text-gray-500">Loading...</p></div>
      ) : data.length === 0 ? (
        <div className="flex h-52 items-center justify-center"><p className="text-gray-500">No data for this date range</p></div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={data} margin={{ top:0, right:10, left:0, bottom:0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis dataKey="channelLabel" tick={{ fontSize:11 }} />
              <YAxis tick={{ fontSize:11 }} tickFormatter={v => active.formatter(v)} width={65} />
              <Tooltip formatter={(v: number) => [active.formatter(v), active.label]} />
              <Bar dataKey={active.dataKey} radius={[4,4,0,0]}>
                {data.map((d,i) => {
                  // eslint-disable-next-line react/jsx-key
                  const C = CLRS[d.channelLabel] || '#6366f1';
                  return <rect key={i} fill={C} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-2 flex justify-around text-center text-xs text-gray-500">
            {data.map(d => (
              <div key={d.channelLabel}>
                <div className="font-semibold text-gray-800">{d.revenuePct}%</div>
                <div>{d.channelLabel}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
