'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';
import { logger } from '@/utils/logger';

interface SLAContentProps {
  isAdmin?: boolean;
}

export default function SLAContent({ isAdmin = false }: SLAContentProps) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState(isAdmin ? 'my_orders' : 'my_orders');
  const [orders, setOrders] = useState<any[]>([]);
  const [valets, setValets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const LIMIT = 50;

  useEffect(() => {
    fetchValets();
  }, []);

  useEffect(() => {
    fetchOrders();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, statusFilter, page]);

  const fetchValets = async () => {
    try {
      const response = await api.get('/users?role=valet');
      setValets(response.data || []);
    } catch (e) {
      logger.error('Failed to fetch valets', e);
    }
  };

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), limit: String(LIMIT) });
      if (statusFilter) params.set('status', statusFilter);
      
      let endpoint = '';
      if (isAdmin) {
        endpoint = '/orders/admin/sub-orders';
        if (activeTab === 'my_orders') {
          params.set('sellerId', (user as any)?._id || '');
        }
      } else {
        endpoint = '/orders/seller-orders';
      }

      const res = await api.get(`${endpoint}?${params.toString()}`);
      setOrders(res.data.subOrders || []);
      setTotal(res.data.totalCount || 0);
    } catch (e: any) {
      toast.error('Failed to fetch SLA data');
    } finally {
      setLoading(false);
    }
  };

  const calculateExpectedTime = (order: any) => {
    const isUrgent = order.isUrgentDelivery;
    const slot = order.deliverySlot;
    const createdDate = new Date(order.createdAt);
    
    if (isUrgent) {
      return new Date(createdDate.getTime() + 1 * 60 * 60 * 1000);
    } else if (slot && slot.date && slot.endTime) {
      return new Date(`${slot.date}T${slot.endTime}:00`);
    } else {
      return new Date(createdDate.getTime() + 24 * 60 * 60 * 1000);
    }
  };

  const getSLAMetStatus = (order: any, expectedTime: Date) => {
    if (order.status === 'delivered') {
      const deliveredTime = order.deliveredAt ? new Date(order.deliveredAt) : null;
      if (deliveredTime && deliveredTime <= expectedTime) {
        return { label: 'Met', color: 'bg-green-100 text-green-800' };
      }
      return { label: 'Breached', color: 'bg-red-100 text-red-800' };
    } else if (order.status === 'cancelled' || order.status === 'declined') {
      return { label: 'N/A', color: 'bg-gray-100 text-gray-800' };
    } else {
      const now = new Date();
      if (now > expectedTime) {
        return { label: 'Breached', color: 'bg-red-100 text-red-800' };
      }
      return { label: 'On Track', color: 'bg-blue-100 text-blue-800' };
    }
  };

  return (
    <div className="h-full flex flex-col min-h-0 bg-white rounded-lg shadow-md p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
          Delivery SLA Report
          <RefreshButton onRefresh={fetchOrders} />
        </h1>
      </div>

      {isAdmin && (
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => { setActiveTab('my_orders'); setPage(1); }}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                activeTab === 'my_orders'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              My Orders
            </button>
            <button
              onClick={() => { setActiveTab('all_orders'); setPage(1); }}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                activeTab === 'all_orders'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              All Orders
            </button>
          </nav>
        </div>
      )}

      <div className="mb-6 flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 px-4 py-2"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="processing">Processing</option>
          <option value="shipped">Shipped</option>
          <option value="out_for_delivery">Out for Delivery</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10 bg-gray-100 shadow-sm">
            <tr>
              <th className="border p-3 text-left">Order #</th>
              <th className="border p-3 text-left">Date & Time</th>
              <th className="border p-3 text-left">Pincode</th>
              <th className="border p-3 text-left">Seller</th>
              <th className="border p-3 text-left">Valet</th>
              <th className="border p-3 text-left">Time Expected</th>
              <th className="border p-3 text-left">Time Delivered</th>
              <th className="border p-3 text-left">SLA Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-gray-500">Loading...</td>
              </tr>
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-gray-500">No SLA records found.</td>
              </tr>
            ) : (
              orders.map((order) => {
                const expectedTime = calculateExpectedTime(order);
                const slaStatus = getSLAMetStatus(order, expectedTime);
                const valetName = valets.find((v) => v._id === order.assignedValet)?.name || 'Unassigned';
                const pincode = order.shippingAddress?.zipCode || order.shippingAddress?.pincode || '—';

                return (
                  <tr key={order._id} className="hover:bg-gray-50 border-b">
                    <td className="p-3">
                      <div className="font-semibold">{order.subOrderNumber || order.orderNumber}</div>
                      {order.isUrgentDelivery && <span className="text-xs text-red-600 font-bold">⚡ Urgent</span>}
                      {order.deliverySlot && <span className="text-xs text-blue-600 font-bold">🕒 Slot</span>}
                    </td>
                    <td className="p-3">
                      {new Date(order.createdAt).toLocaleString('en-IN')}
                    </td>
                    <td className="p-3">{pincode}</td>
                    <td className="p-3">{order.sellerName || 'Platform'}</td>
                    <td className="p-3">{valetName}</td>
                    <td className="p-3">{expectedTime.toLocaleString('en-IN')}</td>
                    <td className="p-3">
                      {order.deliveredAt ? new Date(order.deliveredAt).toLocaleString('en-IN') : '—'}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${slaStatus.color}`}>
                        {slaStatus.label}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {total > LIMIT && (
        <div className="flex items-center justify-end gap-4 pt-4 border-t mt-4">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-4 py-2 border rounded-md disabled:opacity-50"
          >
            Previous
          </button>
          <span>Page {page} of {Math.ceil(total / LIMIT)}</span>
          <button
            disabled={page * LIMIT >= total}
            onClick={() => setPage((p) => p + 1)}
            className="px-4 py-2 border rounded-md disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
