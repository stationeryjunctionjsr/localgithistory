'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';

interface Valet {
  id: string;
  name: string;
  phone?: string;
  vehicleType?: string;
  city?: string;
  activeOrderCount: number;
  maxConcurrentOrders: number;
}

interface DispatchValetModalProps {
  orderId: string;
  orderNumber?: string;
  sellerPincode: string;
  deliverySlotId?: string;
  isUrgent?: boolean;
  onSuccess: () => void;
  onClose: () => void;
}

const VEHICLE_ICONS: Record<string, string> = {
  bicycle: '🚲',
  bike: '🏍️',
  auto: '🛺',
  van: '🚐',
};

export default function DispatchValetModal({
  orderId,
  orderNumber,
  sellerPincode,
  deliverySlotId,
  isUrgent = false,
  onSuccess,
  onClose,
}: DispatchValetModalProps) {
  const [valets, setValets] = useState<Valet[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedValetId, setSelectedValetId] = useState<string>('');
  const [dispatching, setDispatching] = useState(false);

  const fetchAvailableValets = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ pincode: sellerPincode });
      if (deliverySlotId) params.set('slotId', deliverySlotId);
      const res = await api.get(`/users/valets/available?${params}`);
      setValets(res.data || []);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to load available valets');
    } finally {
      setLoading(false);
    }
  }, [sellerPincode, deliverySlotId]);

  useEffect(() => {
    fetchAvailableValets();
  }, [fetchAvailableValets]);

  const handleDispatch = async () => {
    if (!selectedValetId) {
      toast.warning('Please select a valet');
      return;
    }
    setDispatching(true);
    try {
      await api.put(`/orders/${orderId}/dispatch`, { valetId: selectedValetId });
      toast.success('Order dispatched! Waiting for valet confirmation.');
      onSuccess();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to dispatch order');
    } finally {
      setDispatching(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 16, width: '100%', maxWidth: 520,
        boxShadow: '0 20px 60px rgba(0,0,0,0.2)', overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px 16px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#111827' }}>
              Assign Delivery Valet
            </h2>
            {orderNumber && (
              <p style={{ margin: '2px 0 0', fontSize: 13, color: '#6b7280' }}>
                Order #{orderNumber} · {isUrgent ? '⚡ Urgent — 5 min acceptance' : '🕐 Normal — 20 min acceptance'}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: 20, color: '#9ca3af', lineHeight: 1, padding: 4,
            }}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '16px 24px', maxHeight: 380, overflowY: 'auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#6b7280' }}>
              <div style={{ fontSize: 28, marginBottom: 8 }}>🔍</div>
              <p style={{ margin: 0 }}>Finding available valets…</p>
            </div>
          ) : valets.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <div style={{ fontSize: 36, marginBottom: 10 }}>🚫</div>
              <p style={{ fontWeight: 600, color: '#111827', margin: '0 0 4px' }}>
                No valets available
              </p>
              <p style={{ color: '#6b7280', fontSize: 13, margin: 0 }}>
                No on-duty valets are available for pincode {sellerPincode} right now.
                Ask a valet to go on duty or mark availability.
              </p>
            </div>
          ) : (
            <>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#6b7280' }}>
                {valets.length} valet{valets.length !== 1 ? 's' : ''} available · sorted by workload
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {valets.map((valet) => {
                  const isSelected = selectedValetId === valet.id;
                  const vehicleIcon = VEHICLE_ICONS[valet.vehicleType || ''] || '🛵';
                  return (
                    <button
                      key={valet.id}
                      onClick={() => setSelectedValetId(valet.id)}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '14px 16px', borderRadius: 12, cursor: 'pointer', textAlign: 'left',
                        border: isSelected ? '2px solid #6d28d9' : '2px solid #e5e7eb',
                        background: isSelected ? '#f5f3ff' : '#fafafa',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                          width: 44, height: 44, borderRadius: '50%',
                          background: isSelected ? '#ede9fe' : '#e5e7eb',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 20, flexShrink: 0,
                        }}>
                          {vehicleIcon}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 15, color: '#111827' }}>
                            {valet.name}
                          </div>
                          <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                            {valet.vehicleType ? `${valet.vehicleType.charAt(0).toUpperCase() + valet.vehicleType.slice(1)}` : 'Valet'}
                            {valet.phone ? ` · ${valet.phone}` : ''}
                          </div>
                        </div>
                      </div>
                      <div style={{ textAlign: 'right', flexShrink: 0 }}>
                        <div style={{
                          display: 'inline-flex', alignItems: 'center', gap: 4,
                          padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                          background: valet.activeOrderCount === 0 ? '#dcfce7' : '#fef3c7',
                          color: valet.activeOrderCount === 0 ? '#15803d' : '#92400e',
                        }}>
                          {valet.activeOrderCount === 0 ? '✓ Free' : `${valet.activeOrderCount} active`}
                        </div>
                        <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 3 }}>
                          max {valet.maxConcurrentOrders}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #f0f0f0',
          display: 'flex', gap: 10, justifyContent: 'flex-end',
        }}>
          <button
            onClick={onClose}
            disabled={dispatching}
            style={{
              padding: '10px 20px', borderRadius: 8, border: '1px solid #d1d5db',
              background: '#fff', color: '#374151', fontWeight: 600, cursor: 'pointer',
              fontSize: 14,
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleDispatch}
            disabled={!selectedValetId || dispatching || valets.length === 0}
            style={{
              padding: '10px 22px', borderRadius: 8, border: 'none',
              background: selectedValetId && !dispatching ? '#6d28d9' : '#c4b5fd',
              color: '#fff', fontWeight: 700, cursor: selectedValetId && !dispatching ? 'pointer' : 'not-allowed',
              fontSize: 14, transition: 'background 0.15s ease',
            }}
          >
            {dispatching ? 'Dispatching…' : '🚀 Dispatch Order'}
          </button>
        </div>
      </div>
    </div>
  );
}
