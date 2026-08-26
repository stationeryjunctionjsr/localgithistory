'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  pending:          { bg: '#fef9c3', text: '#a16207' },
  confirmed:        { bg: '#dbeafe', text: '#1d4ed8' },
  processing:       { bg: '#ede9fe', text: '#6d28d9' },
  shipped:          { bg: '#cffafe', text: '#0e7490' },
  out_for_delivery: { bg: '#ffedd5', text: '#c2410c' },
  delivered:        { bg: '#dcfce7', text: '#15803d' },
  cancelled:        { bg: '#fee2e2', text: '#b91c1c' },
};

interface Stats { total: number; pending: number; delivered: number; revenue: number; }
interface SubOrder {
  _id: string; subOrderNumber: string; parentOrderNumber: string;
  total: number; status: string; createdAt: string; items: any[];
}

export default function SellerDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<Stats>({ total: 0, pending: 0, delivered: 0, revenue: 0 });
  const [recent, setRecent] = useState<SubOrder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/orders/seller-orders?page=1&limit=100');
        const orders: SubOrder[] = res.data.subOrders || [];
        const total = res.data.totalCount || orders.length;
        const pending = orders.filter(o => o.status === 'pending').length;
        const delivered = orders.filter(o => o.status === 'delivered').length;
        const revenue = orders.filter(o => o.status !== 'cancelled').reduce((s, o) => s + (o.total || 0), 0);
        setStats({ total, pending, delivered, revenue });
        setRecent(orders.slice(0, 5));
      } catch (e) {
        logger.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const statCards = [
    { label: 'Total Orders',   value: stats.total,                   color: '#6366f1', icon: '📦' },
    { label: 'Pending',        value: stats.pending,                  color: '#f59e0b', icon: '⏳' },
    { label: 'Delivered',      value: stats.delivered,                color: '#22c55e', icon: '✅' },
    { label: 'Revenue (est.)', value: `₹${stats.revenue.toFixed(0)}`, color: '#3b82f6', icon: '💰' },
  ];

  return (
    <div style={{ padding: '28px 24px', maxWidth: 1100 }}>
      {/* Welcome */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: '#111827', margin: 0 }}>
          Welcome back, {user?.companyName || user?.name || 'Seller'} 👋
        </h1>
        <p style={{ color: '#6b7280', marginTop: 4, fontSize: 14 }}>
          Here&apos;s a snapshot of your store performance
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        {statCards.map(card => (
          <div
            key={card.label}
            style={{
              background: '#fff', borderRadius: 14,
              padding: '20px 22px',
              boxShadow: '0 1px 4px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.04)',
              borderLeft: `4px solid ${card.color}`,
            }}
          >
            <div style={{ fontSize: 24, marginBottom: 8 }}>{card.icon}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#111827' }}>{loading ? '—' : card.value}</div>
            <div style={{ fontSize: 13, color: '#6b7280', marginTop: 2 }}>{card.label}</div>
          </div>
        ))}
      </div>

      {/* Recent orders */}
      <div style={{ background: '#fff', borderRadius: 14, boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
        <div style={{ padding: '18px 22px', borderBottom: '1px solid #f3f4f6', fontWeight: 600, fontSize: 16, color: '#111827' }}>
          Recent Orders
        </div>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#9ca3af' }}>Loading…</div>
        ) : recent.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#9ca3af' }}>No orders yet — your first order will appear here.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['Sub-Order #', 'Parent Order', 'Items', 'Total', 'Status', 'Date'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#374151', borderBottom: '1px solid #f3f4f6' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent.map(o => {
                  const sc = STATUS_COLORS[o.status] || { bg: '#f3f4f6', text: '#374151' };
                  return (
                    <tr key={o._id} style={{ borderBottom: '1px solid #f9fafb' }}>
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: '#4f46e5' }}>{o.subOrderNumber}</td>
                      <td style={{ padding: '12px 16px', color: '#6b7280' }}>{o.parentOrderNumber}</td>
                      <td style={{ padding: '12px 16px', color: '#6b7280' }}>{o.items?.length ?? 0}</td>
                      <td style={{ padding: '12px 16px', fontWeight: 600 }}>₹{Number(o.total).toFixed(2)}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600, background: sc.bg, color: sc.text }}>
                          {o.status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', color: '#9ca3af', fontSize: 13 }}>
                        {o.createdAt ? new Date(o.createdAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
