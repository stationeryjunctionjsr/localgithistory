'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import dynamic from 'next/dynamic';
import { useAuth } from '@/context/AuthContext';
import { logger } from '@/utils/logger';

const DispatchValetModal = dynamic(() => import('@/components/DispatchValetModal'), { ssr: false });

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending:         { bg: '#fef9c3', text: '#a16207' },
  confirmed:       { bg: '#dbeafe', text: '#1d4ed8' },
  processing:      { bg: '#ede9fe', text: '#6d28d9' },
  pending_valet:   { bg: '#fef3c7', text: '#b45309' },
  shipped:         { bg: '#cffafe', text: '#0e7490' },
  out_for_delivery:{ bg: '#ffedd5', text: '#c2410c' },
  delivered:       { bg: '#dcfce7', text: '#15803d' },
  cancelled:       { bg: '#fee2e2', text: '#b91c1c' },
};
const STATUSES = ['pending','confirmed','processing','pending_valet','shipped','out_for_delivery','cancelled'];

interface SubOrder {
  _id: string;
  subOrderNumber: string;
  parentOrderNumber: string;
  parentOrderId?: string;
  items: any[];
  subtotal: number;
  shipping: number;
  total: number;
  status: string;
  isUrgentDelivery: boolean;
  createdAt: string;
  user?: any;
  deliverySlotId?: string;
}

export default function SellerOrdersPage() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<SubOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [dispatchTarget, setDispatchTarget] = useState<SubOrder | null>(null);
  const LIMIT = 20;

  const sellerPincode: string = (user as any)?.address?.zipCode || (user as any)?.address?.pincode || '';

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), limit: String(LIMIT) });
      if (statusFilter) params.set('status', statusFilter);
      const res = await api.get(`/orders/seller-orders?${params}`);
      setOrders(res.data.subOrders || []);
      setTotal(res.data.totalCount || 0);
    } catch (e) {
      logger.error(e);
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => { fetchOrders(); }, [fetchOrders]);

  const handleStatusChange = async (id: string, newStatus: string) => {
    setUpdating(id);
    try {
      await api.put(`/orders/seller-orders/${id}/status`, { status: newStatus });
      toast.success('Order status updated');
      fetchOrders();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to update status');
    } finally {
      setUpdating(null);
    }
  };

  const statusLabel = (s: string) =>
    s === 'pending_valet'
      ? '⏳ Waiting for Valet'
      : s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div style={{ padding: '28px 24px' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#111827', margin: 0 }}>My Orders</h1>
        <p style={{ color: '#6b7280', fontSize: 14, marginTop: 4 }}>{total} sub-orders</p>
      </div>

      {/* Filter */}
      <div style={{ marginBottom: 20 }}>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 14, background: '#fff', cursor: 'pointer' }}
        >
          <option value="">All Statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{statusLabel(s)}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div style={{ background: '#fff', borderRadius: 14, boxShadow: '0 1px 4px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#f9fafb' }}>
                {['Sub-Order #', 'Parent Order', 'Items', 'Subtotal', 'Shipping', 'Total', 'Status', 'Actions', 'Date'].map((h) => (
                  <th key={h} style={{ padding: '11px 14px', textAlign: 'left', fontWeight: 600, color: '#374151', borderBottom: '1px solid #f0f0f0', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={9} style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>Loading…</td></tr>
              ) : orders.length === 0 ? (
                <tr><td colSpan={9} style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>No orders found</td></tr>
              ) : orders.map((o) => {
                const sc = STATUS_COLORS[o.status] || { bg: '#f3f4f6', text: '#374151' };
                const canDispatch = o.status === 'processing';
                const isPendingValet = o.status === 'pending_valet';
                return (
                  <tr key={o._id} style={{ borderBottom: '1px solid #f9fafb' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: '#4f46e5', whiteSpace: 'nowrap' }}>
                      {o.subOrderNumber}
                      {o.isUrgentDelivery && <span style={{ marginLeft: 6, fontSize: 11, color: '#ef4444', fontWeight: 700 }}>⚡</span>}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#6b7280', whiteSpace: 'nowrap' }}>{o.parentOrderNumber}</td>
                    <td style={{ padding: '12px 14px', color: '#374151' }}>{o.items?.length ?? 0}</td>
                    <td style={{ padding: '12px 14px' }}>₹{Number(o.subtotal).toFixed(2)}</td>
                    <td style={{ padding: '12px 14px' }}>₹{Number(o.shipping).toFixed(2)}</td>
                    <td style={{ padding: '12px 14px', fontWeight: 700 }}>₹{Number(o.total).toFixed(2)}</td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600, background: sc.bg, color: sc.text, whiteSpace: 'nowrap' }}>
                        {statusLabel(o.status)}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', whiteSpace: 'nowrap' }}>
                      {canDispatch ? (
                        <button
                          onClick={() => setDispatchTarget(o)}
                          style={{
                            padding: '6px 14px', borderRadius: 8, border: 'none',
                            background: '#6d28d9', color: '#fff', fontWeight: 700,
                            fontSize: 13, cursor: 'pointer',
                          }}
                        >
                          🚀 Dispatch
                        </button>
                      ) : isPendingValet ? (
                        <button
                          onClick={() => setDispatchTarget(o)}
                          style={{
                            padding: '6px 14px', borderRadius: 8, border: '1px solid #fcd34d',
                            background: '#fffbeb', color: '#92400e', fontWeight: 600,
                            fontSize: 13, cursor: 'pointer',
                          }}
                        >
                          🔄 Reassign
                        </button>
                      ) : (
                        <select
                          value={o.status}
                          disabled={updating === o._id}
                          onChange={(e) => handleStatusChange(o._id, e.target.value)}
                          style={{ padding: '5px 8px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13, cursor: 'pointer', opacity: updating === o._id ? 0.5 : 1 }}
                        >
                          {STATUSES.map((s) => (
                            <option key={s} value={s}>{statusLabel(s)}</option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#9ca3af', fontSize: 13, whiteSpace: 'nowrap' }}>
                      {o.createdAt ? new Date(o.createdAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > LIMIT && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '14px 18px', borderTop: '1px solid #f3f4f6', justifyContent: 'flex-end' }}>
            <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}
              style={{ padding: '6px 14px', borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff', cursor: page === 1 ? 'not-allowed' : 'pointer', opacity: page === 1 ? 0.4 : 1 }}>
              ← Prev
            </button>
            <span style={{ fontSize: 13, color: '#6b7280' }}>Page {page} of {Math.ceil(total / LIMIT)}</span>
            <button disabled={page * LIMIT >= total} onClick={() => setPage((p) => p + 1)}
              style={{ padding: '6px 14px', borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff', cursor: page * LIMIT >= total ? 'not-allowed' : 'pointer', opacity: page * LIMIT >= total ? 0.4 : 1 }}>
              Next →
            </button>
          </div>
        )}
      </div>

      {/* Dispatch Modal */}
      {dispatchTarget && (
        <DispatchValetModal
          orderId={dispatchTarget.parentOrderId || dispatchTarget._id}
          orderNumber={dispatchTarget.subOrderNumber}
          sellerPincode={sellerPincode}
          deliverySlotId={dispatchTarget.deliverySlotId}
          isUrgent={dispatchTarget.isUrgentDelivery}
          onSuccess={() => { setDispatchTarget(null); fetchOrders(); }}
          onClose={() => setDispatchTarget(null)}
        />
      )}
    </div>
  );
}
