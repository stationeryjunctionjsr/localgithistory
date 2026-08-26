'use client';

import { useState, useEffect } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface SubOrder {
  _id: string;
  subOrderNumber: string;
  parentOrderNumber: string;
  sellerName: string;
  sellerId: string;
  items: any[];
  subtotal: number;
  shipping: number;
  total: number;
  status: string;
  isUrgentDelivery: boolean;
  createdAt: string;
  // Commission fields
  commissionPct?: number | null;
  commissionAmount?: number | null;
  commissionStatus?: 'unrealized' | 'realized' | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#f59e0b',
  confirmed: '#3b82f6',
  processing: '#8b5cf6',
  shipped: '#06b6d4',
  out_for_delivery: '#f97316',
  delivered: '#22c55e',
  cancelled: '#ef4444',
};

const COMMISSION_STATUS_CONFIG = {
  unrealized: {
    label: 'Unrealized',
    bg: '#fef3c720',
    color: '#d97706',
    dot: '#f59e0b',
    icon: '⏳',
    title: 'Commission will be realized after the return period ends',
  },
  realized: {
    label: 'Realized',
    bg: '#dcfce720',
    color: '#16a34a',
    dot: '#22c55e',
    icon: '✓',
    title: 'Commission has been realized — return period has elapsed',
  },
} as const;

export default function SellerOrdersPage() {
  const [subOrders, setSubOrders] = useState<SubOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [sellerFilter, setSellerFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Commission summary for displayed rows
  const visibleWithCommission = subOrders.filter(
    (o) => o.commissionStatus && o.sellerId
  );
  const totalUnrealized = visibleWithCommission
    .filter((o) => o.commissionStatus === 'unrealized')
    .reduce((s, o) => s + (o.commissionAmount || 0), 0);
  const totalRealized = visibleWithCommission
    .filter((o) => o.commissionStatus === 'realized')
    .reduce((s, o) => s + (o.commissionAmount || 0), 0);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), limit: '50' });
      if (statusFilter) params.set('status', statusFilter);
      if (sellerFilter) params.set('sellerId', sellerFilter);
      const res = await api.get(`/orders/admin/sub-orders?${params}`);
      setSubOrders(res.data.subOrders || []);
      setTotal(res.data.totalCount || 0);
    } catch (err) {
      logger.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter, sellerFilter]);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Seller Orders</h1>
        <p style={{ color: '#6b7280', fontSize: 14 }}>
          Sub-orders managed by marketplace sellers ({total} total)
        </p>
      </div>

      {/* Commission Summary Cards */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <div style={{
          background: 'linear-gradient(135deg, #fff7ed, #fef3c7)',
          border: '1px solid #fde68a',
          borderRadius: 12,
          padding: '16px 24px',
          minWidth: 200,
          flex: 1,
        }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: '#92400e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
            ⏳ Unrealized Commission
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#d97706' }}>
            ₹{totalUnrealized.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: 12, color: '#b45309', marginTop: 4 }}>Pending return period</div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)',
          border: '1px solid #bbf7d0',
          borderRadius: 12,
          padding: '16px 24px',
          minWidth: 200,
          flex: 1,
        }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: '#14532d', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
            ✓ Realized Commission
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#16a34a' }}>
            ₹{totalRealized.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: 12, color: '#15803d', marginTop: 4 }}>Return period elapsed</div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #f8fafc, #f1f5f9)',
          border: '1px solid #e2e8f0',
          borderRadius: 12,
          padding: '16px 24px',
          minWidth: 200,
          flex: 1,
        }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
            Total Commission (page)
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
            ₹{(totalUnrealized + totalRealized).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>Across {visibleWithCommission.length} seller orders</div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          style={{
            padding: '8px 12px', borderRadius: 8, border: '1px solid #e5e7eb',
            fontSize: 14, background: '#fff', cursor: 'pointer',
          }}
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
        <input
          type="text"
          placeholder="Filter by Seller ID..."
          value={sellerFilter}
          onChange={(e) => { setSellerFilter(e.target.value); setPage(1); }}
          style={{
            padding: '8px 12px', borderRadius: 8, border: '1px solid #e5e7eb',
            fontSize: 14, minWidth: 220,
          }}
        />
      </div>

      {/* Table */}
      <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                {['Sub-Order #', 'Parent Order', 'Seller', 'Items', 'Subtotal', 'Shipping', 'Total', 'Commission', 'Status', 'Date'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#374151', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={10} style={{ padding: 40, textAlign: 'center', color: '#9ca3af' }}>Loading...</td>
                </tr>
              ) : subOrders.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ padding: 40, textAlign: 'center', color: '#9ca3af' }}>No seller orders found</td>
                </tr>
              ) : subOrders.map((so) => (
                <tr key={so._id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#1f2937' }}>{so.subOrderNumber}</td>
                  <td style={{ padding: '12px 16px', color: '#6b7280' }}>{so.parentOrderNumber}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontWeight: 500 }}>{so.sellerName || '—'}</span>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#6b7280' }}>{so.items?.length ?? 0}</td>
                  <td style={{ padding: '12px 16px' }}>₹{Number(so.subtotal).toFixed(2)}</td>
                  <td style={{ padding: '12px 16px' }}>₹{Number(so.shipping).toFixed(2)}</td>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>₹{Number(so.total).toFixed(2)}</td>

                  {/* Commission Column */}
                  <td style={{ padding: '12px 16px', minWidth: 160 }}>
                    {!so.sellerId ? (
                      <span style={{ color: '#9ca3af', fontSize: 12 }}>Platform order</span>
                    ) : so.commissionStatus == null ? (
                      <span style={{ color: '#9ca3af', fontSize: 12 }}>—</span>
                    ) : (() => {
                      const cfg = COMMISSION_STATUS_CONFIG[so.commissionStatus as keyof typeof COMMISSION_STATUS_CONFIG];
                      return (
                        <div title={cfg.title}>
                          <div style={{ fontWeight: 600, color: '#1f2937', fontSize: 13 }}>
                            {so.commissionPct != null ? `${so.commissionPct}%` : '—'}
                            {so.commissionAmount != null && (
                              <span style={{ color: cfg.color, marginLeft: 4 }}>
                                = ₹{Number(so.commissionAmount).toFixed(2)}
                              </span>
                            )}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 3 }}>
                            <span style={{
                              display: 'inline-flex', alignItems: 'center', gap: 4,
                              padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                              background: cfg.bg, color: cfg.color,
                              border: `1px solid ${cfg.dot}40`,
                            }}>
                              <span style={{ width: 5, height: 5, borderRadius: '50%', background: cfg.dot, display: 'inline-block' }} />
                              {cfg.icon} {cfg.label}
                            </span>
                          </div>
                        </div>
                      );
                    })()}
                  </td>

                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                      background: `${STATUS_COLORS[so.status] || '#9ca3af'}20`,
                      color: STATUS_COLORS[so.status] || '#9ca3af',
                    }}>
                      {so.status?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </span>
                    {so.isUrgentDelivery && (
                      <span style={{ marginLeft: 6, fontSize: 11, color: '#ef4444', fontWeight: 600 }}>⚡ URGENT</span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px', color: '#6b7280', whiteSpace: 'nowrap' }}>
                    {so.createdAt ? new Date(so.createdAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > 50 && (
          <div style={{ display: 'flex', gap: 8, padding: '16px 20px', justifyContent: 'flex-end', borderTop: '1px solid #f3f4f6' }}>
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              style={{ padding: '6px 14px', borderRadius: 8, border: '1px solid #e5e7eb', cursor: page === 1 ? 'not-allowed' : 'pointer', background: '#fff' }}
            >
              Previous
            </button>
            <span style={{ padding: '6px 12px', fontSize: 14, color: '#6b7280' }}>Page {page}</span>
            <button
              disabled={page * 50 >= total}
              onClick={() => setPage(p => p + 1)}
              style={{ padding: '6px 14px', borderRadius: 8, border: '1px solid #e5e7eb', cursor: page * 50 >= total ? 'not-allowed' : 'pointer', background: '#fff' }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
