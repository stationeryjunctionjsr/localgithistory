'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import SalesOverTimeChart from '@/components/Analytics/SalesOverTimeChart';
import SalesByProduct from '@/components/Analytics/SalesByProduct';
import ProductsSellThrough from '@/components/Analytics/ProductsSellThrough';
import SalesHeatmap from '@/components/Analytics/SalesHeatmap';
import InventoryRunwayChart from '@/components/Analytics/InventoryRunwayChart';
import BuyerFrequencyChart from '@/components/Analytics/BuyerFrequencyChart';

interface KPIData {
  gross_sales: number;
  returning_customer_rate: number;
  orders_fulfilled: number;
  orders: number;
}

type DateRangeKey = 'today' | 'week' | 'month' | 'year' | 'custom';

export default function SellerAnalyticsDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [kpiData, setKpiData] = useState<KPIData | null>(null);
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [dateRange, setDateRange] = useState<DateRangeKey>('month');
  const [currency, setCurrency] = useState<'INR' | 'USD'>('INR');
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  useEffect(() => {
    updateDateRange();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateRange]);

  useEffect(() => {
    if (startDate && endDate) fetchKPIData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  const updateDateRange = () => {
    const now = new Date();
    let start: Date;
    const end = new Date();
    switch (dateRange) {
      case 'today':  start = new Date(now.getFullYear(), now.getMonth(), now.getDate()); break;
      case 'week':   start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); break;
      case 'month':  start = new Date(now.getFullYear(), now.getMonth(), 1); break;
      case 'year':   start = new Date(now.getFullYear(), 0, 1); break;
      case 'custom': return; // use picker values
      default:       start = new Date(now.getFullYear(), now.getMonth(), 1);
    }
    setStartDate(start);
    setEndDate(end);
  };

  const fetchKPIData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();
      // seller_id is resolved automatically server-side from auth token
      const response = await api.get('/analytics/kpi', { params });
      setKpiData(response.data);
      setLastRefreshed(new Date());
    } catch (error: any) {
      toast.error(`Failed to fetch analytics: ${error.response?.data?.detail || error.message}`);
      setKpiData({ gross_sales: 0, returning_customer_rate: 0, orders_fulfilled: 0, orders: 0 });
    } finally {
      setLoading(false);
    }
  };

  const fmtCurrency = (v: number) =>
    currency === 'USD'
      ? `$${(v / 82).toFixed(2)}`
      : `\u20B9${v.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

  if (!user || !['wholesaler', 'super_admin'].includes(user.role)) {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h2 className="mb-2 text-xl font-bold text-red-800">Access Denied</h2>
          <p className="text-red-600">This page is only available to sellers.</p>
        </div>
      </div>
    );
  }

  const kpi = kpiData || { gross_sales: 0, returning_customer_rate: 0, orders_fulfilled: 0, orders: 0 };

  const kpiCards = [
    { title: 'Your Sales', value: fmtCurrency(kpi.gross_sales), icon: '\u20B9', color: 'bg-green-50 border-green-200 text-green-700' },
    { title: 'Orders', value: kpi.orders.toLocaleString(), icon: '\uD83D\uDCE6', color: 'bg-blue-50 border-blue-200 text-blue-700' },
    { title: 'Fulfilled', value: kpi.orders_fulfilled.toLocaleString(), icon: '\u2705', color: 'bg-indigo-50 border-indigo-200 text-indigo-700' },
    { title: 'Repeat Rate', value: `${kpi.returning_customer_rate}%`, icon: '\uD83D\uDD04', color: 'bg-amber-50 border-amber-200 text-amber-700' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6 rounded-lg bg-white p-6 shadow-md">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Analytics</h1>
            <p className="text-sm text-gray-500">
              Data scoped to your store &middot; Last updated: {lastRefreshed.toLocaleTimeString()}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {(['today', 'week', 'month', 'year', 'custom'] as DateRangeKey[]).map((r) => (
              <button
                key={r}
                onClick={() => setDateRange(r)}
                className={`rounded px-3 py-1 text-sm capitalize ${dateRange === r ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >
                {r}
              </button>
            ))}
            {dateRange === 'custom' && (
              <div className="flex items-center gap-2 rounded border p-1">
                <input type="date" value={startDate?.toISOString().split('T')[0] || ''}
                  onChange={(e) => setStartDate(e.target.value ? new Date(e.target.value) : null)}
                  className="rounded border px-2 py-0.5 text-sm" />
                <span className="text-gray-400">-</span>
                <input type="date" value={endDate?.toISOString().split('T')[0] || ''}
                  onChange={(e) => {
                    const d = e.target.value ? new Date(e.target.value) : null;
                    if (d) d.setHours(23, 59, 59, 999);
                    setEndDate(d);
                  }}
                  className="rounded border px-2 py-0.5 text-sm" />
              </div>
            )}
            <button
              onClick={() => setCurrency(currency === 'INR' ? 'USD' : 'INR')}
              className="rounded bg-gray-100 px-3 py-1 text-sm text-gray-600 hover:bg-gray-200"
            >
              {currency === 'INR' ? '\u20B9 INR' : '$ USD'}
            </button>
            <button
              onClick={fetchKPIData}
              className="rounded bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-700"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
        {kpiCards.map((c) => (
          <div key={c.title} className={`rounded-lg border p-4 ${c.color}`}>
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium opacity-80">{c.title}</p>
              <span className="text-xl">{c.icon}</span>
            </div>
            <p className={`mt-2 text-2xl font-bold ${loading ? 'opacity-40' : ''}`}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* Row 1 — Sales over time + Top products */}
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <SalesOverTimeChart startDate={startDate} endDate={endDate} currency={currency} />
        <SalesByProduct startDate={startDate} endDate={endDate} currency={currency} limit={8} />
      </div>

      {/* Row 2 — Sales heatmap + Buyer frequency */}
      <h3 className="mb-4 mt-6 border-b px-1 pb-2 text-lg font-bold text-gray-700">Store Patterns</h3>
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <SalesHeatmap startDate={startDate} endDate={endDate} />
        <BuyerFrequencyChart startDate={startDate} endDate={endDate} currency={currency} />
      </div>

      {/* Row 3 — Inventory */}
      <h3 className="mb-4 mt-6 border-b px-1 pb-2 text-lg font-bold text-gray-700">Inventory Intelligence</h3>
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <InventoryRunwayChart startDate={startDate} endDate={endDate} limit={12} />
        <ProductsSellThrough startDate={startDate} endDate={endDate} limit={10} />
      </div>
    </div>
  );
}
