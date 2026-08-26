'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { logger } from '@/utils/logger';

interface SlotConfig {
  _id: string;
  date: string;
  segment: string;
  isActive: boolean;
  pincodes: string[];
  slots: Array<{
    id: string;
    startTime: string;
    endTime: string;
    isActive: boolean;
    isUrgent?: boolean;
    isFullDay?: boolean;
    capacity?: number;
    bookedCount?: number;
  }>;
}

export default function SellerDeliverySlotsPage() {
  const { user } = useAuth();
  const [configs, setConfigs] = useState<SlotConfig[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/delivery-slots');
      setConfigs(res.data || []);
    } catch (e) {
      logger.error(e);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchConfigs(); }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this delivery slot configuration?')) return;
    try {
      await api.delete(`/delivery-slots/${id}`);
      toast.success('Configuration deleted');
      fetchConfigs();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to delete');
    }
  };

  // If seller doesn't have permission, show info panel
  if (!user?.sellerPermissions?.allowDeliverySlots) {
    return (
      <div style={{ padding: '28px 24px' }}>
        <div style={{ background: '#fffbeb', border: '1px solid #fbbf24', borderRadius: 12, padding: 28, maxWidth: 480 }}>
          <div style={{ fontSize: 22, marginBottom: 12 }}>🔒</div>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#92400e', margin: '0 0 8px' }}>Permission Required</h2>
          <p style={{ color: '#78350f', fontSize: 14, margin: 0 }}>
            You don&apos;t have permission to manage delivery slots. Please contact the platform admin to enable this feature for your account.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '28px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#111827', margin: 0 }}>Delivery Slots</h1>
          <p style={{ color: '#6b7280', fontSize: 14, marginTop: 4 }}>
            Configure delivery time windows for your orders. You can only use pincodes approved by the platform.
          </p>
        </div>
        <a
          href="/admin/delivery-slots"
          style={{ padding: '9px 18px', background: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0', borderRadius: 9, fontSize: 14, fontWeight: 600, textDecoration: 'none' }}
        >
          View Platform Slots
        </a>
      </div>

      <div style={{ background: '#fff', borderRadius: 14, boxShadow: '0 1px 4px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>Loading…</div>
        ) : configs.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>
            No slot configurations yet. Slot management will be available soon via the API.
          </div>
        ) : configs.map(cfg => (
          <div key={cfg._id} style={{ padding: '16px 20px', borderBottom: '1px solid #f3f4f6' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
              <div>
                <span style={{ fontWeight: 700, color: '#111827' }}>{cfg.date}</span>
                <span style={{ marginLeft: 10, fontSize: 12, background: '#ede9fe', color: '#6d28d9', padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>
                  {cfg.segment}
                </span>
                <span style={{ marginLeft: 8, fontSize: 12, background: cfg.isActive ? '#dcfce7' : '#fee2e2', color: cfg.isActive ? '#15803d' : '#b91c1c', padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>
                  {cfg.isActive ? 'Active' : 'Inactive'}
                </span>
              </div>
              <button onClick={() => handleDelete(cfg._id)}
                style={{ padding: '5px 12px', background: '#fef2f2', color: '#dc2626', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
                Delete
              </button>
            </div>
            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>
              Pincodes: {cfg.pincodes?.join(', ') || 'All'}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {cfg.slots?.map(slot => (
                <div key={slot.id} style={{
                  padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 600,
                  background: slot.isActive ? '#f0f9ff' : '#f9fafb',
                  color: slot.isActive ? '#0369a1' : '#9ca3af',
                  border: `1px solid ${slot.isActive ? '#bae6fd' : '#e5e7eb'}`,
                }}>
                  {slot.isFullDay ? 'Anytime' : `${slot.startTime}–${slot.endTime}`}
                  {slot.isUrgent && <span style={{ marginLeft: 4, color: '#ef4444' }}>⚡</span>}
                  {slot.capacity != null && (
                    <span style={{ marginLeft: 6, color: '#9ca3af' }}>
                      {(slot.capacity - (slot.bookedCount || 0))}/{slot.capacity}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
