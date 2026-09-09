'use client';

import { useState, useEffect, useMemo } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { logger } from '@/utils/logger';

// ── Types ───────────────────────────────────────────────────────────────────────

interface Zone {
  id: string;
  name: string;
  pincodes: string[];
  defaultCapacity: number;
  urgentDeliveryAvailable: boolean;
  customerType: 'retail' | 'business' | 'both';
}

interface SettingsData {
  sellerId: string;
  sellerName: string;
  serviceableZoneIds: string[];
  availableZones: Zone[];
}

// ── Component ───────────────────────────────────────────────────────────────────

export default function SellerDeliverySettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<SettingsData | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  // ── Data fetching ─────────────────────────────────────────────────────────────

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await api.get<SettingsData>('/users/seller-delivery-settings');
      setData(res.data);
      setSelectedIds(new Set(res.data.serviceableZoneIds || []));
    } catch (err: any) {
      logger.error(err);
      toast.error(err?.response?.data?.detail || 'Failed to load delivery settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  // ── Derived values ────────────────────────────────────────────────────────────

  const filteredZones = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    if (!q) return data.availableZones;
    return data.availableZones.filter(
      (z) =>
        z.name.toLowerCase().includes(q) ||
        z.pincodes.some((p) => p.includes(q))
    );
  }, [data, search]);

  const selectedZones = useMemo(
    () => (data?.availableZones || []).filter((z) => selectedIds.has(z.id)),
    [data, selectedIds]
  );

  const totalPincodes = useMemo(
    () => selectedZones.reduce((sum, z) => sum + z.pincodes.length, 0),
    [selectedZones]
  );

  // ── Handlers ──────────────────────────────────────────────────────────────────

  const toggleZone = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/users/seller-delivery-settings', {
        serviceableZoneIds: Array.from(selectedIds),
      });
      toast.success('Delivery zones saved!');
      fetchSettings();
    } catch (err: any) {
      logger.error(err);
      toast.error(err?.response?.data?.detail || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
        Loading delivery settings…
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#ef4444' }}>
        Failed to load settings. Please refresh.
      </div>
    );
  }

  return (
    <div style={{ padding: '28px 24px', maxWidth: 960, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111827', margin: 0 }}>
            Delivery Zone Settings
          </h1>
          <p style={{ fontSize: 14, color: '#6b7280', marginTop: 4 }}>
            Select which zones you serve. Customers in these zones will see your products.
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            background: saving ? '#9ca3af' : '#3b82f6',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            padding: '10px 22px',
            fontWeight: 600,
            fontSize: 14,
            cursor: saving ? 'not-allowed' : 'pointer',
          }}
        >
          {saving ? 'Saving…' : 'Save Changes'}
        </button>
      </div>

      {/* Search */}
      <input
        type="text"
        placeholder="Search zones or pincodes…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{
          width: '100%',
          padding: '10px 14px',
          border: '1px solid #d1d5db',
          borderRadius: 8,
          fontSize: 14,
          marginBottom: 20,
          boxSizing: 'border-box',
          outline: 'none',
        }}
      />

      {/* Zone list */}
      {filteredZones.length === 0 ? (
        <div
          style={{
            padding: 40,
            textAlign: 'center',
            background: '#f9fafb',
            borderRadius: 12,
            color: '#6b7280',
          }}
        >
          {data.availableZones.length === 0
            ? 'No delivery zones have been created yet. Ask your administrator to set up zones.'
            : 'No zones match your search.'}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filteredZones.map((zone) => {
            const isSelected = selectedIds.has(zone.id);
            const isExpanded = expandedId === zone.id;

            return (
              <div
                key={zone.id}
                style={{
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderLeft: `4px solid ${isSelected ? '#3b82f6' : '#e5e7eb'}`,
                  borderRadius: 10,
                  padding: '16px 18px',
                  backgroundColor: isSelected ? '#eff6ff' : '#fff',
                  transition: 'background 0.15s, border-color 0.15s',
                }}
              >
                {/* Card header row */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleZone(zone.id)}
                    style={{ width: 18, height: 18, cursor: 'pointer', accentColor: '#3b82f6' }}
                  />

                  {/* Zone name + badges */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 600, fontSize: 15, color: '#111827' }}>
                        {zone.name}
                      </span>

                      {/* Pincode count */}
                      <span
                        style={{
                          background: '#e0f2fe',
                          color: '#0369a1',
                          fontSize: 11,
                          fontWeight: 600,
                          padding: '2px 8px',
                          borderRadius: 20,
                        }}
                      >
                        {zone.pincodes.length} pincode{zone.pincodes.length !== 1 ? 's' : ''}
                      </span>

                      {/* Urgent badge */}
                      {zone.urgentDeliveryAvailable && (
                        <span
                          style={{
                            background: '#dcfce7',
                            color: '#166534',
                            fontSize: 11,
                            fontWeight: 600,
                            padding: '2px 8px',
                            borderRadius: 20,
                          }}
                        >
                          ⚡ Urgent
                        </span>
                      )}

                      {/* Customer type */}
                      <span
                        style={{
                          background: '#f3e8ff',
                          color: '#6b21a8',
                          fontSize: 11,
                          fontWeight: 600,
                          padding: '2px 8px',
                          borderRadius: 20,
                          textTransform: 'capitalize',
                        }}
                      >
                        {zone.customerType}
                      </span>

                      {/* Capacity */}
                      <span
                        style={{
                          background: '#f3f4f6',
                          color: '#6b7280',
                          fontSize: 11,
                          padding: '2px 8px',
                          borderRadius: 20,
                        }}
                      >
                        {zone.defaultCapacity} slots/day
                      </span>
                    </div>
                  </div>

                  {/* Expand/collapse toggle */}
                  {zone.pincodes.length > 0 && (
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : zone.id)}
                      style={{
                        background: 'none',
                        border: '1px solid #d1d5db',
                        borderRadius: 6,
                        padding: '4px 10px',
                        fontSize: 12,
                        color: '#6b7280',
                        cursor: 'pointer',
                      }}
                    >
                      {isExpanded ? 'Hide pincodes ▲' : 'Show pincodes ▼'}
                    </button>
                  )}
                </div>

                {/* Expanded pincode list */}
                {isExpanded && (
                  <div
                    style={{
                      marginTop: 14,
                      background: '#f9fafb',
                      borderRadius: 8,
                      padding: '12px 14px',
                    }}
                  >
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {zone.pincodes.map((pc) => (
                        <span
                          key={pc}
                          style={{
                            background: '#e5e7eb',
                            color: '#374151',
                            fontSize: 12,
                            padding: '3px 10px',
                            borderRadius: 20,
                            fontFamily: 'monospace',
                          }}
                        >
                          {pc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Summary footer */}
      <div
        style={{
          marginTop: 24,
          padding: '14px 18px',
          background: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: 10,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 14,
          color: '#374151',
        }}
      >
        <span>
          <strong>{selectedIds.size}</strong> zone{selectedIds.size !== 1 ? 's' : ''} selected
          {' · '}
          <strong>{totalPincodes}</strong> total pincode{totalPincodes !== 1 ? 's' : ''} covered
        </span>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            background: saving ? '#9ca3af' : '#3b82f6',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            padding: '8px 18px',
            fontWeight: 600,
            fontSize: 13,
            cursor: saving ? 'not-allowed' : 'pointer',
          }}
        >
          {saving ? 'Saving…' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}

