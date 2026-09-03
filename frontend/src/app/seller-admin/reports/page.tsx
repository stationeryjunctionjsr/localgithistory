'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateIST } from '@/utils/dateUtils';
import InfoButton from '@/components/InfoButton';
import RefreshButton from '@/components/Admin/RefreshButton';

const ITEMS_PER_PAGE = 15;

// ─── Icons ───────────────────────────────────────────────────────────────────

const reportIcons: Record<string, React.ReactNode> = {
  selling: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  'revenue-by-category': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
    </svg>
  ),
  'inventory-alerts': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  'fulfillment-time': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  'payment-methods': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  ),
  'sales-by-location': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  'coupon-usage': (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
    </svg>
  ),
  returns: (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
    </svg>
  ),
  'products-sell-through': (
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
};

// ─── Report definitions ───────────────────────────────────────────────────────

type ColDef = {
  header: string;
  key: string | ((row: any, i: number) => any);
  display?: (row: any) => React.ReactNode;
  sortable?: boolean;
};

type ReportDef = {
  id: string;
  category: string;
  title: string;
  description: string;
  endpoint: string;
  columns: ColDef[];
};

const SELLER_REPORTS: ReportDef[] = [
  // ── Sales & Revenue ────────────────────────────────────────────────────────
  {
    id: 'selling',
    category: 'Sales & Revenue',
    title: 'Highest Selling Products',
    description: 'Your top-selling products by quantity and revenue within the selected period.',
    endpoint: '/analytics/sales-by-product?limit=100',
    columns: [
      { header: 'RANK', key: (_row: any, i: number) => i + 1, sortable: false },
      { header: 'PRODUCT', key: 'name', sortable: true },
      { header: 'QTY SOLD', key: 'quantity', sortable: true },
      { header: 'REVENUE', key: 'revenue', display: (row: any) => `₹${Number(row.revenue).toFixed(2)}`, sortable: true },
    ],
  },
  {
    id: 'revenue-by-category',
    category: 'Sales & Revenue',
    title: 'Revenue by Category',
    description: 'Revenue breakdown across your product categories with units sold and order count.',
    endpoint: '/analytics/reports/revenue-by-category?limit=50',
    columns: [
      { header: 'CATEGORY', key: 'category', sortable: true },
      { header: 'REVENUE', key: 'revenue', display: (row: any) => `₹${Number(row.revenue ?? 0).toFixed(2)}`, sortable: true },
      { header: 'UNITS SOLD', key: 'quantity', sortable: true },
      { header: 'ORDERS', key: 'orderCount', sortable: true },
    ],
  },
  {
    id: 'payment-methods',
    category: 'Sales & Revenue',
    title: 'Payment Methods',
    description: 'How your customers prefer to pay — order volume and revenue by payment method.',
    endpoint: '/analytics/reports/payment-methods',
    columns: [
      { header: 'METHOD', key: 'paymentMethod', sortable: true },
      { header: 'ORDERS', key: 'orderCount', sortable: true },
      { header: 'REVENUE', key: 'revenue', display: (row: any) => `₹${Number(row.revenue ?? 0).toFixed(2)}`, sortable: true },
      { header: 'AVG ORDER', key: 'avgOrderValue', display: (row: any) => `₹${Number(row.avgOrderValue ?? 0).toFixed(2)}`, sortable: true },
    ],
  },
  {
    id: 'coupon-usage',
    category: 'Sales & Revenue',
    title: 'Coupon Usage',
    description: 'Which discount codes are being used on your orders and how much revenue they generated.',
    endpoint: '/analytics/reports/coupon-usage',
    columns: [
      { header: 'COUPON CODE', key: 'couponCode', sortable: true },
      { header: 'USED', key: 'usageCount', sortable: true },
      { header: 'TOTAL DISCOUNT', key: 'totalDiscountGiven', display: (row: any) => `₹${Number(row.totalDiscountGiven ?? 0).toFixed(2)}`, sortable: true },
      { header: 'REVENUE', key: 'totalRevenue', display: (row: any) => `₹${Number(row.totalRevenue ?? 0).toFixed(2)}`, sortable: true },
    ],
  },
  {
    id: 'returns',
    category: 'Sales & Revenue',
    title: 'Returns & Refunds',
    description: 'All return/refund requests for your orders — statuses, refund values, and dates.',
    endpoint: '/analytics/reports/returns',
    columns: [
      { header: 'RETURN ID', key: 'returnId', sortable: true },
      { header: 'CUSTOMER', key: 'userName', sortable: true },
      { header: 'STATUS', key: 'status', sortable: true },
      { header: 'REFUND VALUE', key: 'refundValue', display: (row: any) => `₹${Number(row.refundValue ?? 0).toFixed(2)}`, sortable: true },
      { header: 'ITEMS', key: 'itemCount', sortable: true },
      { header: 'DATE', key: 'createdAt', display: (row: any) => formatDateIST(row.createdAt), sortable: true },
    ],
  },
  // ── Inventory ──────────────────────────────────────────────────────────────
  {
    id: 'inventory-alerts',
    category: 'Inventory',
    title: 'Inventory Alerts',
    description: 'Your products running low on stock (≤20 units), including out-of-stock items.',
    endpoint: '/analytics/reports/inventory-alerts?threshold=20',
    columns: [
      { header: 'PRODUCT', key: 'name', sortable: true },
      { header: 'SKU', key: 'sku', sortable: true },
      { header: 'CATEGORY', key: 'category', sortable: true },
      { header: 'STOCK', key: 'stock', sortable: true },
      {
        header: 'STATUS',
        key: 'status',
        display: (row: any) => (
          <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
            row.status === 'out_of_stock' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
          }`}>
            {row.status === 'out_of_stock' ? 'Out of Stock' : 'Low Stock'}
          </span>
        ),
        sortable: true,
      },
    ],
  },
  {
    id: 'inventory-value',
    category: 'Inventory',
    title: 'Inventory Value by Category',
    description: 'Total capital tied up in your current active inventory, grouped by product category.',
    endpoint: '/analytics/reports/inventory-value-by-category',
    columns: [
      { header: 'CATEGORY', key: 'category', sortable: true },
      { header: 'PRODUCTS', key: 'productCount', sortable: true },
      { header: 'TOTAL UNITS', key: 'totalStock', sortable: true },
      { header: 'INVENTORY VALUE', key: 'inventoryValue', display: (row: any) => `₹${Number(row.inventoryValue ?? 0).toFixed(2)}`, sortable: true },
    ],
  },
  {
    id: 'products-sell-through',
    category: 'Inventory',
    title: 'Product Sell-Through Rate',
    description: 'Inventory velocity: units sold vs current stock. Helps identify fast movers and items needing clearance.',
    endpoint: '/analytics/products-sell-through?limit=50',
    columns: [
      { header: 'PRODUCT', key: 'name', sortable: true },
      { header: 'CATEGORY', key: 'category', sortable: true },
      { header: 'UNITS SOLD', key: 'unitsSold', sortable: true },
      { header: 'CURRENT STOCK', key: 'currentStock', sortable: true },
      { header: 'SELL-THROUGH', key: 'sellThroughRate', display: (row: any) => `${Number(row.sellThroughRate ?? 0).toFixed(1)}%`, sortable: true },
    ],
  },
  // ── Logistics ──────────────────────────────────────────────────────────────
  {
    id: 'fulfillment-time',
    category: 'Logistics',
    title: 'Order Fulfillment Time',
    description: 'Time taken from order placement to completion for your orders — useful for operational efficiency tracking.',
    endpoint: '/analytics/reports/fulfillment-time',
    columns: [
      { header: 'ORDER #', key: 'orderNumber', sortable: true },
      { header: 'CUSTOMER', key: 'userName', sortable: true },
      { header: 'STATUS', key: 'status', sortable: true },
      { header: 'HOURS', key: 'fulfillmentHours', sortable: true },
      { header: 'DAYS', key: 'fulfillmentDays', sortable: true },
      { header: 'ORDER VALUE', key: 'orderTotal', display: (row: any) => `₹${Number(row.orderTotal ?? 0).toFixed(2)}`, sortable: true },
      { header: 'CREATED', key: 'createdAt', display: (row: any) => formatDateIST(row.createdAt), sortable: true },
    ],
  },
  {
    id: 'sales-by-location',
    category: 'Logistics',
    title: 'Sales by Location',
    description: 'Revenue, orders, and units sold broken down by delivery destination — see where your customers are.',
    endpoint: '/analytics/reports/sales-by-location?limit=100',
    columns: [
      { header: 'LOCATION', key: 'location', sortable: true },
      { header: 'REVENUE', key: 'revenue', display: (row: any) => `₹${Number(row.revenue ?? 0).toFixed(2)}`, sortable: true },
      { header: 'ORDERS', key: 'orderCount', sortable: true },
      { header: 'UNITS SOLD', key: 'quantity', sortable: true },
    ],
  },
  // ── Returns ────────────────────────────────────────────────────────────────
  {
    id: 'top-returned-products',
    category: 'Returns',
    title: 'Top Returned Products',
    description: 'Your products most frequently returned or requested for refund, alongside estimated revenue lost.',
    endpoint: '/analytics/reports/top-returned-products?limit=50',
    columns: [
      { header: 'PRODUCT', key: 'productName', sortable: true },
      { header: 'CATEGORY', key: 'category', sortable: true },
      { header: 'RETURN COUNT', key: 'returnCount', sortable: true },
      { header: 'UNITS RETURNED', key: 'quantityReturned', sortable: true },
      { header: 'REVENUE LOST', key: 'revenueLost', display: (row: any) => `₹${Number(row.revenueLost ?? 0).toFixed(2)}`, sortable: true },
    ],
  },
  // ── Order Financials ───────────────────────────────────────────────────────
  {
    id: 'net-sales',
    category: 'Order Financials',
    title: 'Net Sales by Order',
    description: 'Per-order breakdown from gross sales to net: discounts, tax, shipping deducted for full financial transparency.',
    endpoint: '/analytics/reports/net-sales',
    columns: [
      { header: 'ORDER #', key: 'orderNumber', sortable: true },
      { header: 'CUSTOMER', key: 'customerName', sortable: true },
      { header: 'GROSS', key: 'grossSales', display: (row: any) => `₹${Number(row.grossSales ?? 0).toFixed(2)}`, sortable: true },
      { header: 'DISCOUNT', key: 'discount', display: (row: any) => `₹${Number(row.discount ?? 0).toFixed(2)}`, sortable: true },
      { header: 'TAX', key: 'tax', display: (row: any) => `₹${Number(row.tax ?? 0).toFixed(2)}`, sortable: true },
      { header: 'SHIPPING', key: 'shipping', display: (row: any) => `₹${Number(row.shipping ?? 0).toFixed(2)}`, sortable: true },
      { header: 'NET SALES', key: 'netSales', display: (row: any) => `₹${Number(row.netSales ?? 0).toFixed(2)}`, sortable: true },
      { header: 'STATUS', key: 'status', sortable: true },
      { header: 'DATE', key: 'createdAt', display: (row: any) => formatDateIST(row.createdAt), sortable: true },
    ],
  },
  {
    id: 'sales-heatmap',
    category: 'Order Financials',
    title: 'Sales Heatmap (Day × Hour)',
    description: 'Peak order windows by day-of-week and hour-of-day. Discover when your customers shop most to optimize promotions.',
    endpoint: '/analytics/reports/sales-heatmap',
    columns: [
      { header: 'DAY OF WEEK', key: 'dayOfWeek', sortable: true },
      { header: 'HOUR', key: 'hour', display: (row: any) => `${String(row.hour).padStart(2, '0')}:00`, sortable: true },
      { header: 'ORDERS', key: 'orderCount', sortable: true },
      { header: 'REVENUE', key: 'revenue', display: (row: any) => `₹${Number(row.revenue ?? 0).toFixed(2)}`, sortable: true },
    ],
  },
  {
    id: 'inventory-runway',
    category: 'Inventory',
    title: 'Days of Inventory Remaining',
    description: 'Estimated days until each product runs out, based on 30-day average daily sales. Most critical items appear first.',
    endpoint: '/analytics/reports/inventory-runway',
    columns: [
      { header: 'PRODUCT', key: 'name', sortable: true },
      { header: 'CATEGORY', key: 'category', sortable: true },
      { header: 'STOCK', key: 'currentStock', sortable: true },
      { header: 'SOLD (30D)', key: 'unitsSold30d', sortable: true },
      { header: 'AVG/DAY', key: 'avgDailySales', sortable: true },
      { header: 'DAYS LEFT', key: 'daysRemaining', display: (row: any) => row.daysRemaining != null ? String(row.daysRemaining) : '∞', sortable: true },
    ],
  },
  {
    id: 'discounts-audit',
    category: 'Order Financials',
    title: 'Discounts & Coupons Audit',
    description: 'Per-order coupon and discount breakdown — see which orders had discounts, the coupon codes used, and the net impact on revenue.',
    endpoint: '/analytics/reports/discounts-audit',
    columns: [
      { header: 'ORDER #', key: 'orderNumber', sortable: true },
      { header: 'CUSTOMER', key: 'customerName', sortable: true },
      { header: 'COUPON', key: 'couponCode', display: (row: any) => row.couponCode || '—', sortable: true },
      { header: 'TYPE', key: 'discountType', display: (row: any) => row.discountType || '—', sortable: true },
      { header: 'GROSS', key: 'grossSales', display: (row: any) => `\u20B9${Number(row.grossSales ?? 0).toFixed(2)}`, sortable: true },
      { header: 'DISCOUNT', key: 'discount', display: (row: any) => `\u20B9${Number(row.discount ?? 0).toFixed(2)}`, sortable: true },
      { header: 'DISCOUNT %', key: 'discountPct', display: (row: any) => `${Number(row.discountPct ?? 0).toFixed(1)}%`, sortable: true },
      { header: 'NET', key: 'netSales', display: (row: any) => `\u20B9${Number(row.netSales ?? 0).toFixed(2)}`, sortable: true },
    ],
  },
  {
    id: 'products-pct-sold',
    category: 'Inventory',
    title: 'Products by % Sold',
    description: 'Units sold as a percentage of opening stock. Highlights fast-movers and slow-movers for restocking decisions.',
    endpoint: '/analytics/reports/products-pct-sold',
    columns: [
      { header: 'PRODUCT', key: 'name', sortable: true },
      { header: 'CATEGORY', key: 'category', sortable: true },
      { header: 'SKU', key: 'sku', sortable: true },
      { header: 'SOLD', key: 'unitsSold', sortable: true },
      { header: 'CURRENT STOCK', key: 'currentStock', sortable: true },
      { header: 'OPENING STOCK', key: 'openingStock', sortable: true },
      { header: '% SOLD', key: 'pctSold', display: (row: any) => `${Number(row.pctSold ?? 0).toFixed(1)}%`, sortable: true },
    ],
  },
];


// ─── Date helpers ─────────────────────────────────────────────────────────────

type DateFilter = 'all' | 'today' | 'yesterday' | '7days' | '30days' | 'thisMonth' | 'lastMonth' | 'custom';

function getDateRange(filter: DateFilter, customStart: string, customEnd: string) {
  if (filter === 'all') return { start: null, end: null };
  if (filter === 'custom') {
    return {
      start: customStart ? new Date(customStart) : null,
      end: customEnd ? new Date(customEnd) : null,
    };
  }
  const end = new Date();
  let start = new Date();
  if (filter === 'today') { start.setHours(0, 0, 0, 0); }
  else if (filter === 'yesterday') {
    start.setDate(start.getDate() - 1); start.setHours(0, 0, 0, 0);
    end.setDate(end.getDate() - 1); end.setHours(23, 59, 59, 999);
  }
  else if (filter === '7days') { start.setDate(start.getDate() - 7); }
  else if (filter === '30days') { start.setDate(start.getDate() - 30); }
  else if (filter === 'thisMonth') { start = new Date(end.getFullYear(), end.getMonth(), 1); }
  else if (filter === 'lastMonth') {
    const s = new Date(end.getFullYear(), end.getMonth() - 1, 1);
    const e = new Date(end.getFullYear(), end.getMonth(), 0);
    return { start: s, end: e };
  }
  return { start, end };
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function SellerReportsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [reportSearch, setReportSearch] = useState('');
  const [innerSearch, setInnerSearch] = useState('');
  const [dateFilter, setDateFilter] = useState<DateFilter>('all');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportsData, setReportsData] = useState<Record<string, any[]>>({});
  const [pages, setPages] = useState<Record<string, number>>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const activeConfig = useMemo(
    () => SELLER_REPORTS.find((r) => r.id === activeTab) || null,
    [activeTab]
  );

  const fetchActiveReport = useCallback(async (reportId: string) => {
    if (!reportId) return;
    const cfg = SELLER_REPORTS.find((r) => r.id === reportId);
    if (!cfg) return;
    setLoading(true);
    try {
      const { start, end } = getDateRange(dateFilter, customStart, customEnd);
      const params: Record<string, string> = {};
      if (start) params.start_date = start.toISOString();
      if (end) params.end_date = end.toISOString();
      const res = await api.get(cfg.endpoint, { params });
      const raw = res.data;
      setReportsData((prev) => ({ ...prev, [reportId]: Array.isArray(raw) ? raw : raw?.products || [] }));
      setPages((prev) => ({ ...prev, [reportId]: 1 }));
      setInnerSearch('');
      setSortKey(null);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  }, [dateFilter, customStart, customEnd]);

  useEffect(() => {
    if (activeTab) fetchActiveReport(activeTab);
  }, [fetchActiveReport, activeTab]);

  // Grouped sidebar
  const filteredReports = useMemo(() =>
    SELLER_REPORTS.filter(
      (r) =>
        r.title.toLowerCase().includes(reportSearch.toLowerCase()) ||
        r.category.toLowerCase().includes(reportSearch.toLowerCase())
    ), [reportSearch]);

  const groupedReports = useMemo(() => {
    const groups: Record<string, typeof SELLER_REPORTS> = {};
    filteredReports.forEach((r) => {
      if (!groups[r.category]) groups[r.category] = [];
      groups[r.category].push(r);
    });
    return groups;
  }, [filteredReports]);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  const processedData = useMemo(() => {
    if (!activeTab || !reportsData[activeTab]) return [];
    let data = [...reportsData[activeTab]];
    if (innerSearch) {
      const q = innerSearch.toLowerCase();
      data = data.filter((row) =>
        Object.values(row).some((val) => val && val.toString().toLowerCase().includes(q))
      );
    }
    if (sortKey) {
      data.sort((a, b) => {
        const va = a[sortKey]; const vb = b[sortKey];
        if (va < vb) return sortOrder === 'asc' ? -1 : 1;
        if (va > vb) return sortOrder === 'asc' ? 1 : -1;
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

  const handleExportCSV = () => {
    const data = reportsData[activeTab!];
    if (!data || data.length === 0) { toast.info('No data to export'); return; }
    const cols = activeConfig!.columns;
    const headers = cols.map((c) => c.header);
    const rows = data.map((row, i) =>
      cols.map((c) => {
        if (c.display) {
          const val = c.display(row);
          return typeof val === 'string' ? val : '';
        }
        const key = c.key;
        return typeof key === 'function' ? key(row, i) : (row[key as string] ?? '');
      })
    );
    const csv = [headers.join(','), ...rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${activeTab}-report.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className="flex min-h-screen flex-col bg-slate-50/50"
      style={{ fontFamily: 'var(--app-font-family)', fontWeight: 'var(--app-font-weight)' as any }}
    >
      {/* Page Header */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white px-8 py-5">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-800">My Reports</h1>
          <p className="text-xs text-slate-500">
            Data scoped to your store —{' '}
            <span className="font-semibold text-indigo-600">{user?.companyName || user?.name}</span>
          </p>
        </div>
      </div>

      <div className="flex flex-1 flex-col lg:flex-row">
        {/* Sidebar backdrop */}
        {!isSidebarCollapsed && (
          <div
            className="fixed top-[156px] left-0 lg:left-[88px] right-0 bottom-0 z-10 bg-black/15 backdrop-blur-[1px] transition-opacity duration-200"
            onClick={() => setIsSidebarCollapsed(true)}
            aria-hidden
          />
        )}

        {/* Sidebar */}
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
                  <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
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
                  <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ transform: 'rotate(180deg)' }}>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
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
                          onClick={() => { setActiveTab(item.id); setIsSidebarCollapsed(true); }}
                          className={`flex w-full flex-shrink-0 items-center gap-3 rounded-lg text-left text-sm font-medium transition-colors ${isSidebarCollapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2.5'} ${
                            isActive
                              ? 'bg-indigo-50 text-indigo-700 shadow-sm ring-1 ring-indigo-200/80'
                              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                          }`}
                          title={isSidebarCollapsed ? item.title : undefined}
                        >
                          <div className={`flex h-5 w-5 flex-shrink-0 items-center justify-center ${isActive ? 'text-indigo-700' : 'text-slate-500'}`}>
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

        {/* Main workspace */}
        <div className="flex-1 overflow-y-auto pl-16">
          {activeConfig ? (
            <div className="flex min-h-full flex-col bg-white">
              {/* Report header */}
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
                            className="min-w-[300px] rounded-md border-2 border-slate-200 px-3 py-1.5 pr-8 text-xs font-medium outline-none focus:border-indigo-400"
                          />
                          <span className="absolute right-2.5 top-2 text-xs opacity-30">🔍</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Controls row */}
                  <div className="flex flex-wrap items-center gap-3">
                    {/* Date filter */}
                    <div className="flex items-center rounded-md border-2 border-slate-200 bg-slate-50 p-0.5">
                      <select
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value as DateFilter)}
                        className="cursor-pointer border-0 bg-transparent px-3 py-1.5 text-xs font-bold text-slate-600 outline-none"
                      >
                        <option value="all">All Time</option>
                        <option value="today">Today</option>
                        <option value="yesterday">Yesterday</option>
                        <option value="7days">Last 7 Days</option>
                        <option value="30days">Last 30 Days</option>
                        <option value="thisMonth">This Month</option>
                        <option value="lastMonth">Last Month</option>
                        <option value="custom">📅 Custom</option>
                      </select>
                    </div>

                    {/* Custom date pickers */}
                    {dateFilter === 'custom' && (
                      <div className="flex items-center gap-2">
                        <input
                          type="date"
                          value={customStart}
                          onChange={(e) => setCustomStart(e.target.value)}
                          className="rounded-md border-2 border-indigo-200 bg-indigo-50 px-2 py-1.5 text-xs font-bold text-indigo-700 outline-none"
                        />
                        <span className="text-xs text-slate-400">→</span>
                        <input
                          type="date"
                          value={customEnd}
                          onChange={(e) => setCustomEnd(e.target.value)}
                          className="rounded-md border-2 border-indigo-200 bg-indigo-50 px-2 py-1.5 text-xs font-bold text-indigo-700 outline-none"
                        />
                      </div>
                    )}

                    {/* CSV Export */}
                    <button
                      onClick={handleExportCSV}
                      className="flex items-center gap-2 rounded-md px-6 py-2 text-sm font-medium text-white shadow-md transition-all"
                      style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
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
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-100 border-t-indigo-500" />
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Processing</p>
                  </div>
                ) : processedData.length === 0 ? (
                  <div className="py-32 text-center">
                    <p className="text-xs font-medium uppercase tracking-widest text-slate-400">No data for this period</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-200 bg-slate-50 text-slate-500">
                          {activeConfig.columns.map((c, i) => (
                            <th
                              key={i}
                              className={`px-8 py-4 text-left text-[11px] font-bold uppercase tracking-wider ${c.sortable ? 'cursor-pointer hover:text-indigo-600' : ''}`}
                              onClick={() => c.sortable && typeof c.key === 'string' && handleSort(c.key)}
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

              {/* Pagination footer */}
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
                      onClick={() => setPages((p) => ({ ...p, [activeTab!]: (p[activeTab!] || 1) - 1 }))}
                      className="rounded-md bg-gray-600 px-4 py-2 text-sm font-bold text-white shadow-sm transition-colors hover:bg-gray-700 disabled:opacity-30"
                    >
                      Previous
                    </button>
                    <button
                      disabled={pages[activeTab!] >= Math.ceil(processedData.length / ITEMS_PER_PAGE)}
                      onClick={() => setPages((p) => ({ ...p, [activeTab!]: (p[activeTab!] || 1) + 1 }))}
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
                Select a report
              </h2>
              <p className="mt-2 max-w-xs text-xs text-slate-400">
                Use the explorer on the left to load your store reports.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
