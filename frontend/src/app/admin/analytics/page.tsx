'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import KPICard from '@/components/Analytics/KPICard';
import SalesOverTimeChart from '@/components/Analytics/SalesOverTimeChart';
import SalesBreakdown from '@/components/Analytics/SalesBreakdown';
import AverageOrderValueChart from '@/components/Analytics/AverageOrderValueChart';
import SalesByChannel from '@/components/Analytics/SalesByChannel';
import SalesByProduct from '@/components/Analytics/SalesByProduct';
import ConversionRateChart from '@/components/Analytics/ConversionRateChart';
import ConversionBreakdown from '@/components/Analytics/ConversionBreakdown';
import SessionsByDevice from '@/components/Analytics/SessionsByDevice';
import SessionsByLocation from '@/components/Analytics/SessionsByLocation';
import ProductsSellThrough from '@/components/Analytics/ProductsSellThrough';
import CustomerCohort from '@/components/Analytics/CustomerCohort';
import SessionsByLandingPage from '@/components/Analytics/SessionsByLandingPage';
import UserEngagementChart from '@/components/Analytics/UserEngagementChart';
import CheckoutFunnelChart from '@/components/Analytics/CheckoutFunnelChart';
import LegacyReportsComponents from '@/components/Analytics/LegacyReportsComponents';
// New analytics chart components
import ActiveVisitorsNow from '@/components/Analytics/ActiveVisitorsNow';
import SessionsOverTimeChart from '@/components/Analytics/SessionsOverTimeChart';
import BounceRateChart from '@/components/Analytics/BounceRateChart';
import SalesHeatmap from '@/components/Analytics/SalesHeatmap';
import RFMSegmentsChart from '@/components/Analytics/RFMSegmentsChart';
import BuyerFrequencyChart from '@/components/Analytics/BuyerFrequencyChart';
import SearchConversionWidget from '@/components/Analytics/SearchConversionWidget';
import TopSearchesNoClicksChart from '@/components/Analytics/TopSearchesNoClicksChart';
import SalesByChannelDetailedChart from '@/components/Analytics/SalesByChannelDetailedChart';
import InventoryRunwayChart from '@/components/Analytics/InventoryRunwayChart';

interface KPIData {
  gross_sales: number;
  returning_customer_rate: number;
  orders_fulfilled: number;
  orders: number;
}

export default function AnalyticsDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [kpiData, setKpiData] = useState<KPIData | null>(null);
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [dateRange, setDateRange] = useState<'today' | 'week' | 'month' | 'year' | 'custom'>(
    'month'
  );
  const [currency, setCurrency] = useState<'INR' | 'USD'>('INR');
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  useEffect(() => {
    if (user?.role === 'super_admin') {
      updateDateRange();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, dateRange]);

  useEffect(() => {
    if (user?.role === 'super_admin' && startDate && endDate) {
      fetchKPIData();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, startDate, endDate]);

  const updateDateRange = () => {
    const now = new Date();
    let start: Date;
    let end = new Date();

    switch (dateRange) {
      case 'today':
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        break;
      case 'week':
        start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'month':
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'year':
        start = new Date(now.getFullYear(), 0, 1);
        break;
      case 'custom':
        // Use startDate and endDate from state
        return;
      default:
        start = new Date(now.getFullYear(), now.getMonth(), 1);
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

      const response = await api.get('/analytics/kpi', { params });
      setKpiData(response.data);
      setLastRefreshed(new Date());
      setLoading(false);
    } catch (error: any) {
      console.error('Analytics API Error:', error);
      toast.error(
        `Failed to fetch analytics data: ${error.response?.data?.detail || error.message || 'Unknown error'}`
      );
      setLoading(false);
      // Set default data to prevent blank page
      setKpiData({
        gross_sales: 0,
        returning_customer_rate: 0,
        orders_fulfilled: 0,
        orders: 0,
      });
    }
  };

  const handleRefresh = () => {
    fetchKPIData();
  };

  const formatCurrency = (amount: number) => {
    if (currency === 'USD') {
      return `$${(amount / 82).toFixed(2)}`; // Approximate conversion
    }
    return `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  };

  if (user?.role !== 'super_admin') {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h2 className="mb-2 text-xl font-bold text-red-800">Access Denied</h2>
          <p className="text-red-600">You must be logged in as super_admin to access this page.</p>
          <p className="mt-2 text-sm text-red-500">Current role: {user?.role || 'Not logged in'}</p>
        </div>
      </div>
    );
  }

  // Show loading state only if we don't have data yet
  if (loading && !kpiData) {
    return (
      <div className="p-6">
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
            <p className="text-gray-600">Loading analytics data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Ensure we have default data
  const displayKpiData = kpiData || {
    gross_sales: 0,
    returning_customer_rate: 0,
    orders_fulfilled: 0,
    orders: 0,
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6 rounded-lg bg-white p-6 shadow-md">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Analytics</h1>
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">
              Last refreshed: {lastRefreshed.toLocaleTimeString()}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setDateRange('today')}
                className={`rounded px-3 py-1 ${dateRange === 'today' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
              >
                Today
              </button>
              <button
                onClick={() => setDateRange('custom')}
                className={`rounded px-3 py-1 ${dateRange === 'custom' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
              >
                Custom
              </button>
              {dateRange === 'custom' && (
                <div className="flex items-center gap-2 rounded border p-1">
                  <input
                    type="date"
                    value={startDate?.toISOString().split('T')[0] || ''}
                    onChange={(e) => setStartDate(e.target.value ? new Date(e.target.value) : null)}
                    className="rounded border px-2 py-0.5 text-sm"
                  />
                  <span className="text-gray-500">-</span>
                  <input
                    type="date"
                    value={endDate?.toISOString().split('T')[0] || ''}
                    onChange={(e) => {
                      const date = e.target.value ? new Date(e.target.value) : null;
                      if (date) date.setHours(23, 59, 59, 999);
                      setEndDate(date);
                    }}
                    className="rounded border px-2 py-0.5 text-sm"
                  />
                </div>
              )}
              <button
                onClick={() => setCurrency(currency === 'INR' ? 'USD' : 'INR')}
                className="flex items-center gap-1 rounded bg-gray-200 px-3 py-1"
              >
                {currency === 'INR' ? '₹ INR' : '$ USD'}
              </button>
              <button
                onClick={handleRefresh}
                className="rounded px-3 py-1 text-sm text-white"
                style={{
                  background: 'linear-gradient(135deg, #17A2B8 0%, #117A8B 100%)',
                }}
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <KPICard
          title="Gross sales"
          value={formatCurrency(displayKpiData.gross_sales)}
          trend={0}
          startDate={startDate}
          endDate={endDate}
        />
        <KPICard
          title="Returning retail customer rate"
          value={`${displayKpiData.returning_customer_rate}%`}
          trend={0}
          startDate={startDate}
          endDate={endDate}
        />
        <KPICard
          title="Orders fulfilled"
          value={displayKpiData.orders_fulfilled.toString()}
          trend={0}
          startDate={startDate}
          endDate={endDate}
        />
        <KPICard
          title="Orders"
          value={displayKpiData.orders.toString()}
          trend={0}
          startDate={startDate}
          endDate={endDate}
        />
      </div>

      {/* Main Charts Row */}
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <SalesOverTimeChart startDate={startDate} endDate={endDate} currency={currency} />
        <SalesBreakdown startDate={startDate} endDate={endDate} currency={currency} />
      </div>

      {/* Second Row */}
      <div className="mb-6 grid gap-6 md:grid-cols-3">
        <SalesByChannel startDate={startDate} endDate={endDate} currency={currency} />
        <AverageOrderValueChart startDate={startDate} endDate={endDate} currency={currency} />
        <SalesByProduct startDate={startDate} endDate={endDate} currency={currency} limit={10} />
      </div>

      {/* Third Row - Funnels Side by Side */}
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <ConversionRateChart startDate={startDate} endDate={endDate} />
        <CheckoutFunnelChart startDate={startDate} endDate={endDate} />
      </div>

      {/* Fourth Row - Platform & Cohort Engagement */}
      <div className="mb-6 grid gap-6 md:grid-cols-3">
        <SessionsByDevice startDate={startDate} endDate={endDate} />
        <ConversionBreakdown startDate={startDate} endDate={endDate} />
        <UserEngagementChart startDate={startDate} endDate={endDate} />
      </div>

      {/* Fifth Row - Logistics & Products */}
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <ProductsSellThrough startDate={startDate} endDate={endDate} limit={10} />
        <SessionsByLocation startDate={startDate} endDate={endDate} />
      </div>

      {/* Sixth Row - Acquisition details */}
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <CustomerCohort startDate={startDate} endDate={endDate} />
        <SessionsByLandingPage startDate={startDate} endDate={endDate} />
      </div>

      {/* ── New Analytics Rows ────────────────────────────────────────── */}

      {/* Real-time + Sessions over time */}
      <h3 className="mb-4 mt-8 border-b px-2 pb-2 text-xl font-bold">Traffic & Acquisition</h3>
      <div className="mb-6 grid gap-6 md:grid-cols-3">
        <ActiveVisitorsNow refreshIntervalMs={30000} />
        <SessionsOverTimeChart startDate={startDate} endDate={endDate} />
        <BounceRateChart startDate={startDate} endDate={endDate} />
      </div>

      {/* Sales heatmap + Channel detailed */}
      <h3 className="mb-4 mt-8 border-b px-2 pb-2 text-xl font-bold">Sales Intelligence</h3>
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <SalesHeatmap startDate={startDate} endDate={endDate} />
        <SalesByChannelDetailedChart startDate={startDate} endDate={endDate} currency={currency} />
      </div>

      {/* Customer insights */}
      <h3 className="mb-4 mt-8 border-b px-2 pb-2 text-xl font-bold">Customer Insights</h3>
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <RFMSegmentsChart startDate={startDate} endDate={endDate} />
        <BuyerFrequencyChart startDate={startDate} endDate={endDate} currency={currency} />
      </div>

      {/* Search analytics */}
      <h3 className="mb-4 mt-8 border-b px-2 pb-2 text-xl font-bold">Search Analytics</h3>
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <SearchConversionWidget startDate={startDate} endDate={endDate} />
        <TopSearchesNoClicksChart startDate={startDate} endDate={endDate} limit={10} />
      </div>

      {/* Inventory intelligence */}
      <h3 className="mb-4 mt-8 border-b px-2 pb-2 text-xl font-bold">Inventory Intelligence</h3>
      <div className="mb-6">
        <InventoryRunwayChart startDate={startDate} endDate={endDate} limit={15} />
      </div>

      {/* Operational Reports */}
      <h3 className="mb-4 mt-8 border-b px-2 pb-2 text-xl font-bold">Operational Reports</h3>
      <LegacyReportsComponents startDate={startDate} endDate={endDate} />
    </div>
  );
}
