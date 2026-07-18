'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import { formatDateTimeIST, formatDateIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';

const ITEMS_PER_PAGE = 10;

const reportIcons: Record<string, React.ReactNode> = {
  selling: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  ),
  abandonments: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
      />
    </svg>
  ),
  business: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
      />
    </svg>
  ),
  retail: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  ),
  returning: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  ),
  searched: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  ),
  viewed: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
      />
    </svg>
  ),
  'drop-offs': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
      />
    </svg>
  ),
  engagement: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  ),
  'user-type': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
      />
    </svg>
  ),
  'business-stats': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  ),
  'retail-stats': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"
      />
    </svg>
  ),
  returns: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
      />
    </svg>
  ),
  'payment-methods': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
      />
    </svg>
  ),
  'revenue-by-category': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
      />
    </svg>
  ),
  'inventory-alerts': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  ),
  'fulfillment-time': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  ),
  'coupon-usage': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"
      />
    </svg>
  ),
  'sales-by-location': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  'new-vs-returning': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  ),
  'items-bought-together': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  ),
  'zero-result-searches': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
    </svg>
  ),
  'sales-by-device': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  ),
  'products-sell-through': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  'aov-over-time': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  'top-returned-products': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 15v-1a4 4 0 00-4-4H8m0 0l3 3m-3-3l3-3m9 14V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16l4-2 4 2 4-2 4 2z" />
    </svg>
  ),
  'inventory-value': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  'most-abandoned-products': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
};

export default function Reports() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [reportSearch, setReportSearch] = useState('');
  const [innerSearch, setInnerSearch] = useState('');
  const [dateFilter, setDateFilter] = useState('all');
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [customStart, setCustomStart] = useState('');
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [customEnd, setCustomEnd] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportsData, setReportsData] = useState<Record<string, any[]>>({});
  const [pages, setPages] = useState<Record<string, number>>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Sort state
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const getDateRange = useCallback(() => {
    if (dateFilter === 'custom') {
      return {
        start: customStart ? new Date(customStart) : null,
        end: customEnd ? new Date(customEnd) : null,
      };
    }
    const end = new Date();
    let start = new Date();
    switch (dateFilter) {
      case 'today':
        start.setHours(0, 0, 0, 0);
        break;
      case 'yesterday':
        start.setDate(start.getDate() - 1);
        start.setHours(0, 0, 0, 0);
        end.setDate(end.getDate() - 1);
        end.setHours(23, 59, 59, 999);
        break;
      case '7days':
        start.setDate(start.getDate() - 7);
        break;
      case '30days':
        start.setDate(start.getDate() - 30);
        break;
      case 'thisMonth':
        start = new Date(end.getFullYear(), end.getMonth(), 1);
        break;
      case 'lastMonth':
        start = new Date(end.getFullYear(), end.getMonth() - 1, 1);
        const lastMonthEnd = new Date(end.getFullYear(), end.getMonth(), 0);
        return { start, end: lastMonthEnd };
      default:
        return { start: null, end: null };
    }
    return { start, end };
  }, [dateFilter, customStart, customEnd]);

  const fetchActiveReport = useCallback(
    async (reportId: string) => {
      if (!reportId) return;
      setLoading(true);
      try {
        const { start, end } = getDateRange();
        const params: any = {};
        if (start) params.start_date = start.toISOString();
        if (end) params.end_date = end.toISOString();

        const endpoints: Record<string, string> = {
          searched: '/tracking/most-searched?limit=100',
          viewed: '/tracking/most-viewed?limit=100',
          'drop-offs': '/tracking/drop-off-points?limit=100',
          abandonments: '/tracking/cart-abandonments?limit=100',
          returning: '/tracking/returning-users',
          'user-type': '/analytics/reports/items-by-user-type',
          selling: '/analytics/sales-by-product?limit=100',
          business: '/analytics/reports/top-users?role=wholesaler&limit=100',
          retail: '/analytics/reports/top-users?role=customer&limit=100',
          engagement: '/analytics/all-user-engagement',
          'business-stats': '/analytics/reports/user-order-stats?role=wholesaler',
          'retail-stats': '/analytics/reports/user-order-stats?role=customer',
          returns: '/analytics/reports/returns',
          'payment-methods': '/analytics/reports/payment-methods',
          'revenue-by-category': '/analytics/reports/revenue-by-category?limit=50',
          'inventory-alerts': '/analytics/reports/inventory-alerts?threshold=20',
          'fulfillment-time': '/analytics/reports/fulfillment-time',
          'coupon-usage': '/analytics/reports/coupon-usage',
          'sales-by-location': '/analytics/reports/sales-by-location?limit=100',
          'new-vs-returning': '/analytics/reports/new-vs-returning',
          'items-bought-together': '/analytics/reports/items-bought-together?limit=50',
          'zero-result-searches': '/tracking/zero-result-searches?limit=100',
          'sales-by-device': '/analytics/reports/sales-by-device',
          'products-sell-through': '/analytics/products-sell-through?limit=50',
          'aov-over-time': '/analytics/sales-over-time?group_by=day',
          'top-returned-products': '/analytics/reports/top-returned-products?limit=50',
          'inventory-value': '/analytics/reports/inventory-value-by-category',
          'most-abandoned-products': '/tracking/most-abandoned-products?limit=50',
        };

        const res = await api.get(endpoints[reportId], { params });
        let data = res.data;
        if (reportId === 'engagement' && res.data.user_metrics) data = res.data.user_metrics;

        setReportsData((prev) => ({ ...prev, [reportId]: Array.isArray(data) ? data : [] }));
        setPages((prev) => ({ ...prev, [reportId]: 1 }));
        setInnerSearch('');
        setSortKey(null);
      } catch (error) {
        console.error(`Error fetching report ${reportId}:`, error);
        toast.error(`Could not load report data`);
      } finally {
        setLoading(false);
      }
    },
    [getDateRange]
  );

  useEffect(() => {
    if (activeTab) fetchActiveReport(activeTab);
  }, [fetchActiveReport, activeTab]);

  const reportsConfig = useMemo(
    () => [
      {
        id: 'selling',
        category: 'Sales & Revenue',
        title: 'Highest Selling Products',
        description:
          'Comprehensive analysis of product performance metrics tracking which items are generating the most volume and revenue within your store ecosystem.',
        columns: [
          { header: 'RANK', key: (row: any, i: number) => i + 1, sortable: false },
          { header: 'PRODUCT', key: 'name', sortable: true },
          { header: 'QTY', key: 'quantity', sortable: true },
          {
            header: 'REVENUE',
            key: 'revenue',
            display: (row: any) => `₹${row.revenue.toFixed(2)}`,
            sortable: true,
          },
        ],
      },
      {
        id: 'abandonments',
        category: 'Sales & Revenue',
        title: 'Cart Abandonments',
        description:
          'Analyze behavioral patterns behind potential lost sales. This report tracks cart sessions that were initialized but never completed as orders.',
        columns: [
          {
            header: 'USER',
            key: 'userId',
            display: (row: any) => row.userId || 'Guest',
            sortable: true,
          },
          {
            header: 'VALUE',
            key: 'cartValue',
            display: (row: any) => `₹${row.cartValue.toFixed(2)}`,
            sortable: true,
          },
          { header: 'ITEMS', key: (row: any) => row.cartItems.length, sortable: false },
          {
            header: 'TIME',
            key: 'timestamp',
            display: (row: any) => formatDateTimeIST(row.timestamp),
            sortable: true,
          },
        ],
      },
      {
        id: 'business',
        category: 'Customers',
        title: 'Top Business Customers',
        description:
          'B2B rankings identifying your most valuable wholesalers and business-tier customers based on total transaction volume.',
        columns: [
          { header: 'RANK', key: (row: any, i: number) => i + 1, sortable: false },
          { header: 'NAME', key: 'name', sortable: true },
          {
            header: 'REVENUE',
            key: 'revenue',
            display: (row: any) => `₹${row.revenue.toFixed(2)}`,
            sortable: true,
          },
        ],
      },
      {
        id: 'retail',
        category: 'Customers',
        title: 'Top Retail Customers',
        description:
          'In-depth look at your top-performing retail consumers, ordered by their total spending contribution to the business.',
        columns: [
          { header: 'NAME', key: 'name', sortable: true },
          { header: 'EMAIL', key: 'email', sortable: true },
          {
            header: 'REVENUE',
            key: 'revenue',
            display: (row: any) => `₹${row.revenue.toFixed(2)}`,
            sortable: true,
          },
        ],
      },
      {
        id: 'returning',
        category: 'Customers',
        title: 'Customer Retention',
        description:
          'Monitoring customer loyalty by identifying users who have returned to the platform for multiple interactions within the filtered timeframe.',
        columns: [
          { header: 'NAME', key: 'name', sortable: true },
          { header: 'EMAIL', key: 'email', sortable: true },
          {
            header: 'LAST SEEN',
            key: 'lastSeen',
            display: (row: any) => formatDateIST(row.lastSeen),
            sortable: true,
          },
        ],
      },
      {
        id: 'searched',
        category: 'Store Performance',
        title: 'Popular Search Terms',
        description:
          'Insights into consumer demand by tracking what keywords users are typing into your store search engine.',
        columns: [
          { header: 'TERM', key: 'term', sortable: true },
          { header: 'COUNT', key: 'count', sortable: true },
          { header: 'AVG RESULTS', key: 'avgProductsFound', sortable: true },
        ],
      },
      {
        id: 'viewed',
        category: 'Store Performance',
        title: 'Product Page Views',
        description:
          'Measuring organic interest and product placement effectiveness by tracking individual page visit metrics.',
        columns: [
          { header: 'PRODUCT', key: 'productName', sortable: true },
          { header: 'VIEWS', key: 'count', sortable: true },
        ],
      },
      {
        id: 'drop-offs',
        category: 'Store Performance',
        title: 'Page Exit Analysis',
        description:
          'Conversion funnel optimization report identifying critical pages where users frequently exit the site.',
        columns: [
          { header: 'PAGE', key: 'page', sortable: true },
          { header: 'COUNT', key: 'count', sortable: true },
        ],
      },
      {
        id: 'engagement',
        category: 'Logistics & Behavior',
        title: 'User Engagement',
        description:
          'High-level metrics on session behavior, quantifying how long and how often users interact with the platform.',
        columns: [
          { header: 'USER', key: 'name', sortable: true },
          { header: 'SESSIONS', key: 'totalSessions', sortable: true },
          {
            header: 'AVG MINS',
            key: 'averageSessionTimeSeconds',
            display: (row: any) => (row.averageSessionTimeSeconds / 60).toFixed(2),
            sortable: true,
          },
        ],
      },
      {
        id: 'user-type',
        category: 'Logistics & Behavior',
        title: 'Traffic by User Role',
        description:
          'Behavioral segmentation analyzing how differently Wholesalers, Customers, and Valets utilize store resources.',
        columns: [
          { header: 'ROLE', key: 'role', sortable: true },
          { header: 'SEARCHES', key: 'searches', sortable: true },
          { header: 'VIEWS', key: 'views', sortable: true },
        ],
      },
      {
        id: 'business-stats',
        category: 'Customers',
        title: 'Business customer order stats',
        description:
          'Order frequency, recency, and average value metrics for B2B/Wholesaler accounts.',
        columns: [
          { header: 'NAME', key: 'name', sortable: true },
          { header: 'TOTAL ORDERS', key: 'totalOrders', sortable: true },
          {
            header: 'AOV',
            key: 'averageOrderValue',
            display: (row: any) => `₹${row.averageOrderValue.toFixed(2)}`,
            sortable: true,
          },
          { header: 'AVG ORDERS/MO', key: 'avgOrdersPerMonth', sortable: true },
          { header: 'DAYS SINCE LAST', key: 'daysSinceLastOrder', sortable: true },
        ],
      },
      {
        id: 'retail-stats',
        category: 'Customers',
        title: 'Retail customer order stats',
        description:
          'Behavioral analytics including purchase recency and average order value for retail customers.',
        columns: [
          { header: 'NAME', key: 'name', sortable: true },
          { header: 'TOTAL ORDERS', key: 'totalOrders', sortable: true },
          {
            header: 'AOV',
            key: 'averageOrderValue',
            display: (row: any) => `₹${row.averageOrderValue.toFixed(2)}`,
            sortable: true,
          },
          { header: 'AVG ORDERS/MO', key: 'avgOrdersPerMonth', sortable: true },
          { header: 'DAYS SINCE LAST', key: 'daysSinceLastOrder', sortable: true },
        ],
      },
      // ── New Reports ────────────────────────────────────────────────────────
      {
        id: 'returns',
        category: 'Sales & Revenue',
        title: 'Returns & Refunds',
        description:
          'Track all return/refund requests, their statuses, estimated refund values, and associated orders to monitor post-sale operations.',
        columns: [
          { header: 'RETURN ID', key: 'returnId', sortable: true },
          { header: 'CUSTOMER', key: 'userName', sortable: true },
          { header: 'STATUS', key: 'status', sortable: true },
          {
            header: 'REFUND VALUE',
            key: 'refundValue',
            display: (row: any) => `₹${(row.refundValue ?? 0).toFixed(2)}`,
            sortable: true,
          },
          { header: 'ITEMS', key: 'itemCount', sortable: true },
          {
            header: 'DATE',
            key: 'createdAt',
            display: (row: any) => formatDateIST(row.createdAt),
            sortable: true,
          },
        ],
      },
      {
        id: 'payment-methods',
        category: 'Sales & Revenue',
        title: 'Payment Method Breakdown',
        description:
          'Analysis of which payment methods customers prefer, the order volume per method, and total revenue contribution.',
        columns: [
          { header: 'METHOD', key: 'paymentMethod', sortable: true },
          { header: 'ORDER COUNT', key: 'orderCount', sortable: true },
          {
            header: 'REVENUE',
            key: 'revenue',
            display: (row: any) => `₹${(row.revenue ?? 0).toFixed(2)}`,
            sortable: true,
          },
          {
            header: 'AVG ORDER VALUE',
            key: 'avgOrderValue',
            display: (row: any) => `₹${(row.avgOrderValue ?? 0).toFixed(2)}`,
            sortable: true,
          },
        ],
      },
      {
        id: 'revenue-by-category',
        category: 'Sales & Revenue',
        title: 'Revenue by Category',
        description:
          'Breakdown of total revenue, units sold, and order count per product category to identify top-performing segments.',
        columns: [
          { header: 'CATEGORY', key: 'category', sortable: true },
          {
            header: 'REVENUE',
            key: 'revenue',
            display: (row: any) => `₹${(row.revenue ?? 0).toFixed(2)}`,
            sortable: true,
          },
          { header: 'UNITS SOLD', key: 'quantity', sortable: true },
          { header: 'ORDERS', key: 'orderCount', sortable: true },
        ],
      },
      {
        id: 'inventory-alerts',
        category: 'Store Performance',
        title: 'Inventory Alerts',
        description:
          'Products with stock at or below 20 units — including out-of-stock items — to help prioritize restocking decisions.',
        columns: [
          { header: 'PRODUCT', key: 'name', sortable: true },
          { header: 'SKU', key: 'sku', sortable: true },
          { header: 'CATEGORY', key: 'category', sortable: true },
          { header: 'STOCK', key: 'stock', sortable: true },
          {
            header: 'STATUS',
            key: 'status',
            display: (row: any) => (
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                  row.status === 'out_of_stock'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-amber-100 text-amber-700'
                }`}
              >
                {row.status === 'out_of_stock' ? 'Out of Stock' : 'Low Stock'}
              </span>
            ),
            sortable: true,
          },
        ],
      },
      {
        id: 'fulfillment-time',
        category: 'Logistics & Behavior',
        title: 'Order Fulfillment Time',
        description:
          'Time taken from order placement to completion/delivery for each order — useful for tracking operational efficiency.',
        columns: [
          { header: 'ORDER #', key: 'orderNumber', sortable: true },
          { header: 'CUSTOMER', key: 'userName', sortable: true },
          { header: 'STATUS', key: 'status', sortable: true },
          { header: 'HOURS', key: 'fulfillmentHours', sortable: true },
          { header: 'DAYS', key: 'fulfillmentDays', sortable: true },
          {
            header: 'ORDER VALUE',
            key: 'orderTotal',
            display: (row: any) => `₹${(row.orderTotal ?? 0).toFixed(2)}`,
            sortable: true,
          },
          {
            header: 'CREATED',
            key: 'createdAt',
            display: (row: any) => formatDateIST(row.createdAt),
            sortable: true,
          },
        ],
      },
      {
        id: 'coupon-usage',
        category: 'Sales & Revenue',
        title: 'Coupon Usage',
        description:
          'Which discount codes are being used most, how much total discount has been applied, and the revenue those orders generated.',
        columns: [
          { header: 'COUPON CODE', key: 'couponCode', sortable: true },
          { header: 'TYPE', key: 'discountType', sortable: true },
          { header: 'VALUE', key: 'discountValue', sortable: true },
          { header: 'USAGE COUNT', key: 'usageCount', sortable: true },
          {
            header: 'TOTAL DISCOUNT',
            key: 'totalDiscountGiven',
            display: (row: any) => `₹${(row.totalDiscountGiven ?? 0).toFixed(2)}`,
            sortable: true,
          },
          {
            header: 'REVENUE',
            key: 'totalRevenue',
            display: (row: any) => `₹${(row.totalRevenue ?? 0).toFixed(2)}`,
            sortable: true,
          },
        ],
      },
      {
        id: 'sales-by-location',
        category: 'Sales & Revenue',
        title: 'Sales by Location',
        description:
          'Revenue, orders, and total units sold broken down by delivery destination (city/state).',
        columns: [
          { header: 'LOCATION', key: 'location', sortable: true },
          {
            header: 'REVENUE',
            key: 'revenue',
            display: (row: any) => `₹${(row.revenue ?? 0).toFixed(2)}`,
            sortable: true,
          },
          { header: 'ORDERS', key: 'orderCount', sortable: true },
          { header: 'UNITS SOLD', key: 'quantity', sortable: true },
        ],
      },
      {
        id: 'new-vs-returning',
        category: 'Customer Behavior',
        title: 'New vs Returning Sales',
        description: 'Revenue split between first-time buyers and returning customers.',
        columns: [
          { header: 'CUSTOMER TYPE', key: 'customerType', sortable: true },
          {
            header: 'REVENUE',
            key: 'revenue',
            display: (row: any) => `₹${(row.revenue ?? 0).toFixed(2)}`,
            sortable: true,
          },
          { header: 'ORDERS', key: 'orderCount', sortable: true },
        ],
      },
      {
        id: 'items-bought-together',
        category: 'Customer Behavior',
        title: 'Items Bought Together',
        description: 'Market basket analysis: pairs of products that are most frequently purchased in the same order.',
        columns: [
          { header: 'PRODUCT A', key: 'productAName', sortable: true },
          { header: 'PRODUCT B', key: 'productBName', sortable: true },
          { header: 'FREQUENCY', key: 'frequency', sortable: true },
        ],
      },
      {
        id: 'zero-result-searches',
        category: 'Store Performance',
        title: 'Zero-Result Searches',
        description: 'Search queries that returned exactly 0 products. Highly useful for identifying missing inventory or terminology gaps.',
        columns: [
          { header: 'SEARCH TERM', key: 'term', sortable: true },
          { header: 'SEARCH COUNT', key: 'count', sortable: true },
        ],
      },
      {
        id: 'sales-by-device',
        category: 'Customer Behavior',
        title: 'Sales by Device',
        description: 'Revenue and order count split by the device type used during the session (Desktop, Mobile, Tablet).',
        columns: [
          { header: 'DEVICE TYPE', key: 'deviceType', sortable: true },
          {
            header: 'REVENUE',
            key: 'revenue',
            display: (row: any) => `₹${(row.revenue ?? 0).toFixed(2)}`,
            sortable: true,
          },
          { header: 'ORDERS', key: 'orderCount', sortable: true },
        ],
      },
      {
        id: 'products-sell-through',
        category: 'Store Performance',
        title: 'Product Sell-Through Rate',
        description: 'Measures inventory velocity by comparing units sold vs current stock. Useful for re-ordering or clearance.',
        columns: [
          { header: 'PRODUCT', key: 'name', sortable: true },
          { header: 'CATEGORY', key: 'category', sortable: true },
          { header: 'UNITS SOLD', key: 'unitsSold', sortable: true },
          { header: 'CURRENT STOCK', key: 'currentStock', sortable: true },
          {
            header: 'SELL-THROUGH',
            key: 'sellThroughRate',
            display: (row: any) => `${(row.sellThroughRate ?? 0).toFixed(1)}%`,
            sortable: true,
          },
        ],
      },
      {
        id: 'aov-over-time',
        category: 'Sales & Revenue',
        title: 'Average Order Value (AOV)',
        description: 'Daily breakdown of total revenue, order count, and Average Order Value.',
        columns: [
          { header: 'DATE', key: 'period', sortable: true },
          {
            header: 'REVENUE',
            key: 'sales',
            display: (row: any) => `₹${(row.sales ?? 0).toFixed(2)}`,
            sortable: true,
          },
          { header: 'ORDERS', key: 'orderCount', sortable: true },
          {
            header: 'AOV',
            key: 'aov',
            display: (row: any) => `₹${(row.aov ?? 0).toFixed(2)}`,
            sortable: true,
          },
        ],
      },
      {
        id: 'top-returned-products',
        category: 'Products',
        title: 'Top Returned Products',
        description: 'Products that are most frequently returned or requested for refunds, alongside estimated revenue lost.',
        columns: [
          { header: 'PRODUCT', key: 'productName', sortable: true },
          { header: 'CATEGORY', key: 'category', sortable: true },
          { header: 'RETURN COUNT', key: 'returnCount', sortable: true },
          { header: 'UNITS RETURNED', key: 'quantityReturned', sortable: true },
          {
            header: 'REVENUE LOST',
            key: 'revenueLost',
            display: (row: any) => `₹${(row.revenueLost ?? 0).toFixed(2)}`,
            sortable: true,
          },
        ],
      },
      {
        id: 'inventory-value',
        category: 'Inventory',
        title: 'Inventory Value by Category',
        description: 'Total capital tied up in current active inventory, grouped by product category.',
        columns: [
          { header: 'CATEGORY', key: 'category', sortable: true },
          { header: 'PRODUCTS', key: 'productCount', sortable: true },
          { header: 'TOTAL UNITS', key: 'totalStock', sortable: true },
          {
            header: 'INVENTORY VALUE',
            key: 'inventoryValue',
            display: (row: any) => `₹${(row.inventoryValue ?? 0).toFixed(2)}`,
            sortable: true,
          },
        ],
      },
      {
        id: 'most-abandoned-products',
        category: 'Customer Behavior',
        title: 'Most Abandoned Products',
        description: 'Products that are most frequently added to cart but left unpurchased.',
        columns: [
          { header: 'PRODUCT', key: 'productName', sortable: true },
          { header: 'CATEGORY', key: 'category', sortable: true },
          { header: 'ABANDON COUNT', key: 'abandonCount', sortable: true },
          { header: 'UNITS ABANDONED', key: 'quantityAbandoned', sortable: true },
          {
            header: 'VALUE LOST',
            key: 'valueLost',
            display: (row: any) => `₹${(row.valueLost ?? 0).toFixed(2)}`,
            sortable: true,
          },
        ],
      },
    ],
    []
  );

  const filteredReports = useMemo(
    () =>
      reportsConfig.filter(
        (r) =>
          r.title.toLowerCase().includes(reportSearch.toLowerCase()) ||
          r.category.toLowerCase().includes(reportSearch.toLowerCase())
      ),
    [reportSearch, reportsConfig]
  );

  const groupedReports = useMemo(() => {
    const groups: Record<string, typeof reportsConfig> = {};
    filteredReports.forEach((r) => {
      if (!groups[r.category]) groups[r.category] = [];
      groups[r.category].push(r);
    });
    return groups;
  }, [filteredReports]);

  const activeConfig = useMemo(
    () => reportsConfig.find((r) => r.id === activeTab) || null,
    [activeTab, reportsConfig]
  );

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  // Final Data Processing (Filter -> Sort -> Page)
  const processedData = useMemo(() => {
    if (!activeTab || !reportsData[activeTab]) return [];

    let data = [...reportsData[activeTab]];

    // 1. Search Filter
    if (innerSearch) {
      const query = innerSearch.toLowerCase();
      data = data.filter((row) =>
        Object.values(row).some((val) => val && val.toString().toLowerCase().includes(query))
      );
    }

    // 2. Sort
    if (sortKey) {
      data.sort((a, b) => {
        const valA = a[sortKey];
        const valB = b[sortKey];

        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return data;
  }, [activeTab, reportsData, innerSearch, sortKey, sortOrder]);

  const currentItems = useMemo(() => {
    const page = pages[activeTab!] || 1;
    const start = (page - 1) * ITEMS_PER_PAGE;
    return processedData.slice(start, start + ITEMS_PER_PAGE);
  }, [processedData, pages, activeTab]);

  if (user?.role !== 'super_admin') return <div className="p-8">Access Denied</div>;

  return (
    <div
      className="flex min-h-screen flex-col bg-slate-50/50"
      style={{ fontFamily: 'var(--app-font-family)', fontWeight: 'var(--app-font-weight)' as any }}
    >
      {/* Global Common Header */}
      <div className="group sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white px-8 py-5">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-800">
            Business intelligence
          </h1>
          <p className="text-xs text-slate-500">Operational data engine & store analytics</p>
        </div>
      </div>

      <div className="flex flex-1 flex-col lg:flex-row">
        {/* Reports backdrop overlay for expanded sidebar */}
        {!isSidebarCollapsed && (
          <div
            className="fixed top-[156px] left-0 lg:left-[88px] right-0 bottom-0 z-10 bg-black/15 backdrop-blur-[1px] transition-opacity duration-200"
            onClick={() => setIsSidebarCollapsed(true)}
            aria-hidden
          />
        )}

        {/* Persistent Sidebar with Intelligence */}
        <div
          className={`fixed top-[156px] left-0 lg:left-[88px] h-[calc(100vh-156px)] z-20 flex flex-col overflow-hidden border-r border-slate-200 bg-white shadow-lg transition-all duration-300 ease-in-out ${isSidebarCollapsed ? 'w-16' : 'w-full lg:w-72'}`}
        >
          <div
            className={`scrollbar-none flex h-full flex-col gap-6 overflow-y-auto overflow-x-hidden transition-all ${isSidebarCollapsed ? 'items-center py-6' : 'min-w-[288px] p-6'}`}
          >
            {!isSidebarCollapsed ? (
              <div className="mb-2 flex items-center gap-2 px-2 w-full">
                <div className="group/search relative flex-1">
                  <input
                    type="text"
                    placeholder="Filter reports..."
                    value={reportSearch}
                    onChange={(e) => setReportSearch(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-xs font-semibold shadow-sm outline-none transition-all focus:border-indigo-500 focus:bg-white focus:ring-1 focus:ring-indigo-100"
                  />
                  <span className="absolute left-3 top-2.5 text-xs opacity-30">🔍</span>
                </div>
                <button
                  onClick={() => setIsSidebarCollapsed(true)}
                  className="flex flex-shrink-0 items-center justify-center rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                  title="Collapse menu"
                >
                  <svg
                    className="h-5 w-5 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                    />
                  </svg>
                </button>
              </div>
            ) : (
              <div className="mb-2 flex items-center justify-center px-2">
                <button
                  onClick={() => setIsSidebarCollapsed(false)}
                  className="flex flex-shrink-0 items-center justify-center rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                  title="Expand menu"
                >
                  <svg
                    className="h-5 w-5 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    style={{ transform: 'rotate(180deg)' }}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                    />
                  </svg>
                </button>
              </div>
            )}

            <div className={`space-y-6 ${isSidebarCollapsed ? 'w-full px-2' : ''}`}>
              {Object.entries(groupedReports).map(([category, items]) => (
                <div key={category} className="space-y-1">
                  {!isSidebarCollapsed && (
                    <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.15em] text-slate-400">
                      {category}
                    </p>
                  )}
                  <div className="space-y-0.5">
                    {items.map((item) => {
                      const isActive = activeTab === item.id;
                      return (
                        <button
                          key={item.id}
                          onClick={() => {
                            setActiveTab(item.id);
                            setIsSidebarCollapsed(true);
                          }}
                          className={`flex w-full flex-shrink-0 items-center gap-3 rounded-lg text-left text-sm font-medium transition-colors ${isSidebarCollapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2.5'} ${
                            isActive
                              ? 'bg-indigo-50 text-indigo-700 shadow-sm ring-1 ring-indigo-200/80'
                              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                          }`}
                          title={isSidebarCollapsed ? item.title : undefined}
                        >
                          <div
                            className={`flex h-5 w-5 flex-shrink-0 items-center justify-center ${isActive ? 'text-indigo-700' : 'text-slate-600 group-hover:text-slate-900'}`}
                          >
                            {reportIcons[item.id] || reportIcons.selling}
                          </div>
                          {!isSidebarCollapsed && (
                            <span className="flex-1 truncate">{item.title}</span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Analysis Workspace */}
        <div className="flex-1 overflow-y-auto pl-16">
          {activeConfig ? (
            <div className="flex min-h-full flex-col bg-white">
              {/* Report Header */}
              <div className="border-b border-slate-100 px-8 py-6">
                <div className="flex flex-col items-start justify-between gap-6 xl:flex-row xl:items-center">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-slate-100 bg-slate-50 text-indigo-600 shadow-inner">
                      <div className="scale-125">
                        {reportIcons[activeConfig.id] || reportIcons.selling}
                      </div>
                    </div>
                    <div>
                      <h2 className="inline-flex items-center gap-3 text-xl font-bold uppercase tracking-tight text-slate-800">
                        <InfoButton info={activeConfig.description} forceTooltip={true}>
                          {activeConfig.title}
                        </InfoButton>
                        <RefreshButton onRefresh={() => activeTab && fetchActiveReport(activeTab)} />
                      </h2>
                      <div className="mt-1.5 flex items-center gap-3">
                        <div className="relative">
                          <input
                            type="text"
                            placeholder={`Search in ${activeConfig.title}...`}
                            value={innerSearch}
                            onChange={(e) => setInnerSearch(e.target.value)}
                            className="min-w-[350px] rounded-md border-2 border-slate-200 px-3 py-1.5 pr-8 text-xs font-medium outline-none focus:border-primary-green"
                          />
                          <span className="absolute right-2.5 top-2 text-xs opacity-30">🔍</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center rounded-md border-2 border-slate-200 bg-slate-50 p-0.5">
                      <select
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value)}
                        className="cursor-pointer border-0 bg-transparent px-3 py-1.5 text-xs font-bold text-slate-600 outline-none"
                      >
                        <option value="all">All Time</option>
                        <option value="today">Today</option>
                        <option value="7days">Last 7 Days</option>
                        <option value="30days">Last 30 Days</option>
                        <option value="custom">📅 Custom</option>
                      </select>
                    </div>

                    <button
                      className="flex items-center gap-2 rounded-md px-6 py-2 text-sm font-medium text-white shadow-md transition-all"
                      style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
                      onClick={() => {
                        const data = reportsData[activeTab!];
                        if (!data || data.length === 0) {
                          toast.info('No data available to export');
                          return;
                        }
                        const cols = activeConfig!.columns;
                        const headers = cols.map((c) => c.header);
                        const rows = data.map((row, i) =>
                          cols.map((c) => {
                            if (c.display) {
                              // strip JSX — get plain text
                              const val = c.display(row);
                              return typeof val === 'string' ? val : '';
                            }
                            const key = c.key;
                            return typeof key === 'function' ? key(row, i) : (row[key as string] ?? '');
                          })
                        );
                        const csv = [
                          headers.join(','),
                          ...rows.map((r) =>
                            r
                              .map((v) => `"${String(v).replace(/"/g, '""')}"`)
                              .join(',')
                          ),
                        ].join('\n');
                        const blob = new Blob([csv], { type: 'text/csv' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${activeTab}-report.csv`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                    >
                      <span>📥</span> Export CSV
                    </button>
                  </div>
                </div>
              </div>

              {/* Data Table */}
              <div className="flex-1">
                {loading ? (
                  <div className="flex flex-col items-center justify-center gap-2 py-32">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-100 border-t-primary-green"></div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                      Processing
                    </p>
                  </div>
                ) : processedData.length === 0 ? (
                  <div className="py-32 text-center">
                    <p className="text-xs font-medium uppercase tracking-widest text-slate-400">
                      No matching results
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-200 bg-slate-50 text-slate-500">
                          {activeConfig.columns.map((c, i) => (
                            <th
                              key={i}
                              className={`px-8 py-4 text-left text-[11px] font-bold uppercase tracking-wider ${c.sortable ? 'cursor-pointer hover:text-primary-green' : ''}`}
                              onClick={() =>
                                c.sortable && handleSort(typeof c.key === 'string' ? c.key : '')
                              }
                            >
                              <div className="flex items-center gap-1">
                                {c.header}
                                {c.sortable && (
                                  <span className="text-[10px] opacity-40">
                                    {sortKey === c.key ? (sortOrder === 'asc' ? '▲' : '▼') : '⇅'}
                                  </span>
                                )}
                              </div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {currentItems.map((row, i) => (
                          <tr key={i} className="transition-colors hover:bg-slate-50/50">
                            {activeConfig.columns.map((c, j) => (
                              <td key={j} className="px-8 py-4 text-sm font-medium text-slate-700">
                                {c.display
                                  ? c.display(row)
                                  : typeof c.key === 'function'
                                    ? c.key(row, i)
                                    : row[c.key as string]}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Footer */}
              {!loading && processedData.length > 0 && (
                <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/50 p-6">
                  <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
                    Showing{' '}
                    {Math.min(processedData.length, (pages[activeTab!] - 1) * ITEMS_PER_PAGE + 1)}{' '}
                    to {Math.min(processedData.length, (pages[activeTab!] || 1) * ITEMS_PER_PAGE)}{' '}
                    of {processedData.length}
                  </p>
                  <div className="flex gap-1">
                    <button
                      disabled={pages[activeTab!] <= 1}
                      onClick={() =>
                        setPages((p) => ({ ...p, [activeTab!]: (p[activeTab!] || 1) - 1 }))
                      }
                      className="rounded-md bg-gray-600 px-4 py-2 text-sm font-bold text-white shadow-sm transition-colors hover:bg-gray-700 disabled:opacity-30"
                    >
                      Previous
                    </button>
                    <button
                      disabled={
                        pages[activeTab!] >= Math.ceil(processedData.length / ITEMS_PER_PAGE)
                      }
                      onClick={() =>
                        setPages((p) => ({ ...p, [activeTab!]: (p[activeTab!] || 1) + 1 }))
                      }
                      className="rounded-md bg-gray-600 px-4 py-2 text-sm font-bold text-white shadow-sm transition-colors hover:bg-gray-700 disabled:opacity-30"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex min-h-[500px] flex-col items-center justify-center bg-white text-center">
              <span className="mb-4 text-4xl opacity-20 grayscale">📊</span>
              <h2 className="text-lg font-bold uppercase tracking-tight text-slate-800">
                Select a dashboard module
              </h2>
              <p className="mt-2 max-w-xs text-xs text-slate-400">
                Use the explorer on the left to load business intelligence modules.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
