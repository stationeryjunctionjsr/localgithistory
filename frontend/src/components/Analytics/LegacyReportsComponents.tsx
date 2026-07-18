'use client';

import { useState, useEffect } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';

interface ReportData {
  ordersByStatus: Record<string, number>;
  revenueByMonth: Array<{ month: string; revenue: number }>;
  topProducts: Array<{ name: string; quantity: number; revenue: number }>;
  ordersByPaymentMethod: Record<string, number>;
}

interface LegacyReportsComponentsProps {
  startDate: Date | null;
  endDate: Date | null;
}

export default function LegacyReportsComponents({
  startDate,
  endDate,
}: LegacyReportsComponentsProps) {
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState<ReportData | null>(null);

  useEffect(() => {
    fetchReports();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  const fetchReports = async () => {
    try {
      setLoading(true);

      const ordersResponse = await api.get('/orders');
      const allOrders = ordersResponse.data || [];

      // Filter orders by date range
      const filteredOrders = allOrders.filter((order: any) => {
        if (!order.createdAt) return false;
        const orderDate = new Date(order.createdAt);

        if (startDate && orderDate < startDate) return false;
        if (endDate && orderDate > endDate) return false;

        return true;
      });

      // Orders by status
      const ordersByStatus: Record<string, number> = {};
      filteredOrders.forEach((order: any) => {
        const status = order.status || 'unknown';
        ordersByStatus[status] = (ordersByStatus[status] || 0) + 1;
      });

      // Orders by payment method
      const ordersByPaymentMethod: Record<string, number> = {};
      filteredOrders.forEach((order: any) => {
        const method = order.paymentMethod || 'unknown';
        ordersByPaymentMethod[method] = (ordersByPaymentMethod[method] || 0) + 1;
      });

      // Revenue by month (last 12 months)
      const now = new Date();
      const revenueByMonth: Array<{ month: string; revenue: number }> = [];
      for (let i = 11; i >= 0; i--) {
        const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const monthName = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        const monthStart = new Date(date.getFullYear(), date.getMonth(), 1);
        const monthEnd = new Date(date.getFullYear(), date.getMonth() + 1, 0);

        const monthRevenue = allOrders
          .filter((order: any) => {
            if (!order.createdAt) return false;
            const orderDate = new Date(order.createdAt);
            return orderDate >= monthStart && orderDate <= monthEnd;
          })
          .reduce((sum: number, order: any) => sum + (order.total || 0), 0);

        revenueByMonth.push({ month: monthName, revenue: monthRevenue });
      }

      // Top products (by quantity sold)
      const productSales: Record<string, { name: string; quantity: number; revenue: number }> = {};
      filteredOrders.forEach((order: any) => {
        order.items?.forEach((item: any) => {
          const productId = item.product?._id || item.product;
          const productName = item.product?.name || 'Unknown Product';
          if (!productSales[productId]) {
            productSales[productId] = { name: productName, quantity: 0, revenue: 0 };
          }
          productSales[productId].quantity += item.quantity || 0;
          productSales[productId].revenue += item.subtotal || 0;
        });
      });

      const topProducts = Object.values(productSales)
        .sort((a, b) => b.quantity - a.quantity)
        .slice(0, 10);

      setReportData({
        ordersByStatus,
        revenueByMonth,
        topProducts,
        ordersByPaymentMethod,
      });
      setLoading(false);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch legacy reports data');
      setLoading(false);
    }
  };

  const downloadTableCSV = (data: any[], filename: string) => {
    if (!data || data.length === 0) {
      toast.info('No data available to export');
      return;
    }
    const replacer = (_key: string, value: any) => (value === null ? '' : value);
    const header = Object.keys(data[0]);
    const csv = [
      header.join(','),
      ...data.map((row: any) =>
        header.map((fieldName) => JSON.stringify(row[fieldName], replacer)).join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', filename);
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading || !reportData) {
    return (
      <div className="flex justify-center p-6">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        {/* Orders by Status */}
        <div className="rounded-lg border bg-white p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Orders by Status</h3>
            <button
              onClick={() =>
                downloadTableCSV(
                  Object.entries(reportData.ordersByStatus).map(([status, count]) => ({
                    status,
                    count,
                  })),
                  'orders_by_status.csv'
                )
              }
              className="text-sm text-blue-600 hover:underline"
            >
              CSV
            </button>
          </div>
          <div className="space-y-2">
            {Object.entries(reportData.ordersByStatus).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className="capitalize">{status}</span>
                <span className="font-bold">{count}</span>
              </div>
            ))}
            {Object.keys(reportData.ordersByStatus).length === 0 && (
              <p className="text-center text-gray-500">No orders in this period</p>
            )}
          </div>
        </div>

        {/* Orders by Payment Method */}
        <div className="rounded-lg border bg-white p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Orders by Payment Method</h3>
            <button
              onClick={() =>
                downloadTableCSV(
                  Object.entries(reportData.ordersByPaymentMethod).map(([method, count]) => ({
                    method,
                    count,
                  })),
                  'orders_by_payment.csv'
                )
              }
              className="text-sm text-blue-600 hover:underline"
            >
              CSV
            </button>
          </div>
          <div className="space-y-2">
            {Object.entries(reportData.ordersByPaymentMethod).map(([method, count]) => (
              <div key={method} className="flex items-center justify-between">
                <span className="capitalize">{method}</span>
                <span className="font-bold">{count}</span>
              </div>
            ))}
            {Object.keys(reportData.ordersByPaymentMethod).length === 0 && (
              <p className="text-center text-gray-500">No payment data available</p>
            )}
          </div>
        </div>
      </div>

      {/* Revenue by Month */}
      <div className="mb-6 rounded-lg border bg-white p-4">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Revenue by Month (Last 12 Months)</h3>
          <button
            onClick={() => downloadTableCSV(reportData.revenueByMonth, 'revenue_by_month.csv')}
            className="text-sm text-blue-600 hover:underline"
          >
            Export CSV
          </button>
        </div>
        <div className="space-y-2">
          {reportData.revenueByMonth.map((item, index) => (
            <div key={index} className="flex items-center gap-4">
              <div className="w-24 text-sm">{item.month}</div>
              <div className="relative h-6 flex-1 rounded-full bg-gray-200">
                <div
                  className="flex h-6 items-center justify-end rounded-full bg-green-600 pr-2"
                  style={{
                    width: `${Math.max(2, (item.revenue / Math.max(...reportData.revenueByMonth.map((r) => r.revenue), 1)) * 100)}%`,
                  }}
                >
                  {item.revenue > 0 && (
                    <span className="text-xs font-bold text-white">
                      ₹{item.revenue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Products */}
      <div className="mb-6 rounded-lg border bg-white p-4">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Top 10 Products by Sales</h3>
          <button
            onClick={() => downloadTableCSV(reportData.topProducts, 'top_products.csv')}
            className="text-sm text-blue-600 hover:underline"
          >
            Export CSV
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
                  Product
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
                  Quantity Sold
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
                  Revenue
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {reportData.topProducts.length > 0 ? (
                reportData.topProducts.map((product, index) => (
                  <tr key={index}>
                    <td className="px-4 py-2">{product.name}</td>
                    <td className="px-4 py-2">{product.quantity}</td>
                    <td className="px-4 py-2">
                      ₹{product.revenue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="px-4 py-2 text-center text-gray-500">
                    No product sales in this period
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
