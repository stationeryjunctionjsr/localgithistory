'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import InfoButton from '@/components/InfoButton';
import api from '@/utils/api';
import RefreshButton from './RefreshButton';

interface DashboardStats {
  totalProducts: number;
  totalWholesalers: number;
  totalCustomers: number;
  totalValets: number;
  totalOrders: number;
  totalRevenue: number;
}

interface TopProduct {
  productId: string;
  productName: string;
  quantity: number;
  revenue: number;
}

interface TopUser {
  userId: string;
  userName: string;
  userEmail: string;
  role: string;
  revenue: number;
}

interface SearchItem {
  term: string;
  count: number;
  avgProductsFound?: number;
}

interface ViewItem {
  productName: string;
  count: number;
}

export default function DashboardStats() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalProducts: 0,
    totalWholesalers: 0,
    totalCustomers: 0,
    totalValets: 0,
    totalOrders: 0,
    totalRevenue: 0,
  });
  const [dateFilter, setDateFilter] = useState('all');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [topWholesalers, setTopWholesalers] = useState<TopUser[]>([]);
  const [topCustomers, setTopCustomers] = useState<TopUser[]>([]);
  const [filteredRevenue, setFilteredRevenue] = useState(0);
  const [mostSearched, setMostSearched] = useState<SearchItem[]>([]);
  const [mostViewed, setMostViewed] = useState<ViewItem[]>([]);
  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    if (user?.role === 'super_admin') {
      fetchPageInfo();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFilter, customStartDate, customEndDate, user]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/dashboard');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const getDateRange = () => {
    const now = new Date();
    let startDate,
      endDate = new Date(now);

    switch (dateFilter) {
      case 'day':
        startDate = new Date(now);
        startDate.setHours(0, 0, 0, 0);
        break;
      case 'week':
        startDate = new Date(now);
        startDate.setDate(now.getDate() - 7);
        startDate.setHours(0, 0, 0, 0);
        break;
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'year':
        startDate = new Date(now.getFullYear(), 0, 1);
        break;
      case 'custom':
        if (customStartDate && customEndDate) {
          startDate = new Date(customStartDate);
          endDate = new Date(customEndDate);
          endDate.setHours(23, 59, 59, 999);
        } else {
          return null;
        }
        break;
      default:
        return null;
    }

    return { startDate, endDate };
  };

  // Fetch dashboard data using aggregated endpoint
  const fetchStats = async () => {
    try {
      setLoading(true);
      const dateRange = getDateRange();
      const params: any = {};
      if (dateRange) {
        params.start_date = dateRange.startDate.toISOString();
        params.end_date = dateRange.endDate.toISOString();
      }
      const response = await api.get('/analytics/dashboard-data', { params });
      const data = response.data;
      const s = data.stats;
      setStats({
        totalProducts: s.totalProducts || 0,
        totalWholesalers: s.totalWholesalers || 0,
        totalCustomers: s.totalCustomers || 0,
        totalValets: s.totalValets || 0,
        totalOrders: s.totalOrders || 0,
        totalRevenue: s.totalRevenue || 0,
      });
      setFilteredRevenue(s.totalRevenue || 0);
      setTopProducts(data.topProducts || []);
      setTopWholesalers(data.topWholesalers || []);
      setTopCustomers(data.topCustomers || []);
      setMostSearched(data.mostSearched || []);
      setMostViewed(data.mostViewed || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data', error);
    } finally {
      setLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600"></div>
        <p className="text-sm text-slate-500">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 overflow-y-auto pr-2 pb-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="inline-flex items-center gap-3 text-xl font-bold text-slate-800 md:text-2xl">
          <InfoButton
            info={
              user?.role === 'super_admin' && pageInfo.page?.description
                ? pageInfo.page.description
                : undefined
            }
          >
            Dashboard Overview
          </InfoButton>
          <RefreshButton onRefresh={fetchStats} />
        </h2>
        {/* Date Filter */}
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-slate-600">Date:</label>
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 md:rounded-none"
          >
            <option value="all">All Time</option>
            <option value="day">Today</option>
            <option value="week">Last 7 Days</option>
            <option value="month">This Month</option>
            <option value="year">This Year</option>
            <option value="custom">Custom Range</option>
          </select>
          {dateFilter === 'custom' && (
            <>
              <input
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 md:rounded-none"
              />
              <span className="text-sm text-slate-500">to</span>
              <input
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 md:rounded-none"
              />
            </>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:gap-4 lg:grid-cols-4 xl:grid-cols-7">
        <div className="rounded-xl border border-l-4 border-slate-100 border-l-indigo-500 bg-white p-4 shadow-sm md:rounded-none md:p-5">
          <h3 className="mb-1 inline-flex items-baseline gap-1 text-xs font-medium text-slate-500 md:text-sm">
            <InfoButton
              info={
                user?.role === 'super_admin' && pageInfo.columns?.totalProducts
                  ? pageInfo.columns.totalProducts
                  : undefined
              }
            >
              Total Products
            </InfoButton>
          </h3>
          <p className="text-xl font-bold text-indigo-600 md:text-2xl">{stats.totalProducts}</p>
        </div>
        <div className="rounded-xl border border-l-4 border-slate-100 border-l-emerald-500 bg-white p-4 shadow-sm md:rounded-none md:p-5">
          <h3 className="mb-1 inline-flex items-baseline gap-1 text-xs font-medium text-slate-500 md:text-sm">
            <InfoButton
              info={
                user?.role === 'super_admin' && pageInfo.columns?.businessCustomers
                  ? pageInfo.columns.businessCustomers
                  : undefined
              }
            >
              Business Customers
            </InfoButton>
          </h3>
          <p className="text-xl font-bold text-emerald-600 md:text-2xl">{stats.totalWholesalers}</p>
        </div>
        <div className="rounded-xl border border-l-4 border-slate-100 border-l-emerald-500 bg-white p-4 shadow-sm md:rounded-none md:p-5">
          <h3 className="mb-1 inline-flex items-baseline gap-1 text-xs font-medium text-slate-500 md:text-sm">
            <InfoButton
              info={
                user?.role === 'super_admin' && pageInfo.columns?.customers
                  ? pageInfo.columns.customers
                  : undefined
              }
            >
              Retail Customers
            </InfoButton>
          </h3>
          <p className="text-xl font-bold text-emerald-600 md:text-2xl">{stats.totalCustomers}</p>
        </div>
        <div className="rounded-xl border border-l-4 border-slate-100 border-l-amber-500 bg-white p-4 shadow-sm md:rounded-none md:p-5">
          <h3 className="mb-1 inline-flex items-baseline gap-1 text-xs font-medium text-slate-500 md:text-sm">
            <InfoButton
              info={
                user?.role === 'super_admin' && pageInfo.columns?.valets
                  ? pageInfo.columns.valets
                  : undefined
              }
            >
              Valets
            </InfoButton>
          </h3>
          <p className="text-xl font-bold text-amber-600 md:text-2xl">{stats.totalValets}</p>
        </div>
        <div className="rounded-xl border border-l-4 border-slate-100 border-l-amber-500 bg-white p-4 shadow-sm md:rounded-none md:p-5">
          <h3 className="mb-1 inline-flex items-baseline gap-1 text-xs font-medium text-slate-500 md:text-sm">
            <InfoButton
              info={
                user?.role === 'super_admin' && pageInfo.columns?.totalOrders
                  ? pageInfo.columns.totalOrders
                  : undefined
              }
            >
              Total Orders
            </InfoButton>
          </h3>
          <p className="text-xl font-bold text-amber-600 md:text-2xl">{stats.totalOrders}</p>
        </div>
        <div className="rounded-xl border border-l-4 border-slate-100 border-l-rose-500 bg-white p-4 shadow-sm md:rounded-none md:p-5">
          <h3 className="mb-1 inline-flex items-baseline gap-1 text-xs font-medium text-slate-500 md:text-sm">
            <InfoButton
              info={
                user?.role === 'super_admin' && pageInfo.columns?.revenue
                  ? pageInfo.columns.revenue
                  : undefined
              }
            >
              Revenue {dateFilter !== 'all' ? `(${dateFilter})` : ''}
            </InfoButton>
          </h3>
          <p className="text-xl font-bold text-rose-600 md:text-2xl">
            ₹{filteredRevenue.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Two Column Layout for Tables */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Top 5 Highest-Selling Products */}
        <div className="rounded-lg bg-white p-6 shadow-md md:rounded-none">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              Top 5 Highest-Selling Products {dateFilter !== 'all' ? `(${dateFilter})` : ''}
            </h3>
            <a href="/admin/reports" className="text-sm text-blue-600 hover:text-blue-800">
              View All →
            </a>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="px-4 py-2 text-left font-medium text-gray-700">Product Name</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-700">Quantity Sold</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-700">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {topProducts.length > 0 ? (
                  topProducts.slice(0, 5).map((product, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50/80">
                      <td className="max-w-[180px] truncate px-3 py-2.5 text-slate-800">
                        {product.productName}
                      </td>
                      <td className="px-3 py-2.5 text-slate-700">{product.quantity}</td>
                      <td className="px-3 py-2.5 font-medium text-slate-800">
                        ₹{product.revenue.toFixed(2)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-sm text-slate-500">
                      No sales data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top 5 Retail Customers */}
        <div className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm md:rounded-none md:p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800 md:text-lg">
              Top 5 Retail Customers by Revenue {dateFilter !== 'all' ? `(${dateFilter})` : ''}
            </h3>
            <a
              href="/admin/reports"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              View All →
            </a>
          </div>
          <div className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">Name</th>
                  <th className="hidden px-3 py-2.5 text-left font-medium text-slate-600 sm:table-cell">
                    Email
                  </th>
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {topCustomers.length > 0 ? (
                  topCustomers.slice(0, 5).map((customer, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50/80">
                      <td className="px-3 py-2.5 text-slate-800">{customer.userName}</td>
                      <td className="hidden max-w-[160px] truncate px-3 py-2.5 text-slate-600 sm:table-cell">
                        {customer.userEmail}
                      </td>
                      <td className="px-3 py-2.5 font-medium text-slate-800">
                        ₹{customer.revenue.toFixed(2)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-sm text-slate-500">
                      No retail customer data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top 5 Wholesalers */}
        <div className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm md:rounded-none md:p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800 md:text-lg">
              Top 5 Business Customers by Revenue {dateFilter !== 'all' ? `(${dateFilter})` : ''}
            </h3>
            <a
              href="/admin/reports"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              View All →
            </a>
          </div>
          <div className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">Name</th>
                  <th className="hidden px-3 py-2.5 text-left font-medium text-slate-600 sm:table-cell">
                    Email
                  </th>
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {topWholesalers.length > 0 ? (
                  topWholesalers.slice(0, 5).map((wholesaler, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50/80">
                      <td className="px-3 py-2.5 text-slate-800">{wholesaler.userName}</td>
                      <td className="hidden max-w-[160px] truncate px-3 py-2.5 text-slate-600 sm:table-cell">
                        {wholesaler.userEmail}
                      </td>
                      <td className="px-3 py-2.5 font-medium text-slate-800">
                        ₹{wholesaler.revenue.toFixed(2)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-sm text-slate-500">
                      No wholesaler data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 5 Most Searched Items */}
        <div className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm md:rounded-none md:p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800 md:text-lg">
              5 Most Searched Items
            </h3>
            <a
              href="/admin/analytics"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              View All →
            </a>
          </div>
          <div className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">Search Term</th>
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">Count</th>
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">
                    Avg Products Found
                  </th>
                </tr>
              </thead>
              <tbody>
                {mostSearched.length > 0 ? (
                  mostSearched.map((item, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50/80">
                      <td className="px-3 py-2.5 text-slate-800">{item.term}</td>
                      <td className="px-3 py-2.5 font-medium text-slate-800">{item.count}</td>
                      <td className="px-3 py-2.5 font-medium text-slate-800">
                        {item.avgProductsFound ?? 'N/A'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-sm text-slate-500">
                      No search data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 5 Most Viewed Products */}
        <div className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm md:rounded-none md:p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800 md:text-lg">
              5 Most Viewed Products
            </h3>
            <a
              href="/admin/analytics"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              View All →
            </a>
          </div>
          <div className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">Product Name</th>
                  <th className="px-3 py-2.5 text-left font-medium text-slate-600">Views</th>
                </tr>
              </thead>
              <tbody>
                {mostViewed.length > 0 ? (
                  mostViewed.map((item, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50/80">
                      <td className="max-w-[180px] truncate px-3 py-2.5 text-slate-800">
                        {item.productName}
                      </td>
                      <td className="px-3 py-2.5 font-medium text-slate-800">{item.count}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={2} className="py-6 text-center text-sm text-slate-500">
                      No view data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
