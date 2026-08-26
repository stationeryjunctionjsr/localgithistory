'use client';

import { useState, useEffect, useMemo } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { logger } from '@/utils/logger';

interface PlatformPincode {
  pincode: string;
  state: string;
  city: string;
  district: string;
  urgentDeliveryAvailable: boolean;
}

interface DeliverySettingsData {
  sellerId: string;
  sellerName: string;
  platformPincodes: PlatformPincode[];
  allowDeliverySlots: boolean;
  allowUrgentDelivery: boolean;
  serviceablePincodes: string[];
  urgentPincodes: string[];
  slotPincodes: string[];
}

export default function SellerDeliverySettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'serviceable' | 'urgent' | 'slots'>('serviceable');

  const [platformPincodes, setPlatformPincodes] = useState<PlatformPincode[]>([]);
  const [allowDeliverySlots, setAllowDeliverySlots] = useState(false);
  const [allowUrgentDelivery, setAllowUrgentDelivery] = useState(false);

  const [serviceablePincodes, setServiceablePincodes] = useState<Set<string>>(new Set());
  const [urgentPincodes, setUrgentPincodes] = useState<Set<string>>(new Set());
  const [slotPincodes, setSlotPincodes] = useState<Set<string>>(new Set());

  const [searchQuery, setSearchQuery] = useState('');
  const [filterState, setFilterState] = useState('ALL');

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await api.get<DeliverySettingsData>('/users/seller-delivery-settings');
      const data = res.data;
      setPlatformPincodes(data.platformPincodes || []);
      setAllowDeliverySlots(!!data.allowDeliverySlots);
      setAllowUrgentDelivery(!!data.allowUrgentDelivery);

      setServiceablePincodes(new Set(data.serviceablePincodes || []));
      setUrgentPincodes(new Set(data.urgentPincodes || []));
      setSlotPincodes(new Set(data.slotPincodes || []));
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

  // Distinct states for filtering
  const distinctStates = useMemo(() => {
    const states = new Set<string>();
    platformPincodes.forEach((p) => {
      if (p.state) states.add(p.state);
    });
    return Array.from(states).sort();
  }, [platformPincodes]);

  // Overall platform serviceable pincodes (filtered by search and state)
  const filteredPlatformPincodes = useMemo(() => {
    return platformPincodes.filter((item) => {
      if (filterState !== 'ALL' && item.state !== filterState) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();
      return (
        item.pincode.toLowerCase().includes(q) ||
        item.city.toLowerCase().includes(q) ||
        item.district.toLowerCase().includes(q) ||
        item.state.toLowerCase().includes(q)
      );
    });
  }, [platformPincodes, filterState, searchQuery]);

  // Urgent eligible pincodes: Must be in serviceablePincodes AND have platform urgentDeliveryAvailable
  const urgentEligiblePincodes = useMemo(() => {
    return platformPincodes.filter(
      (item) => item.urgentDeliveryAvailable && serviceablePincodes.has(item.pincode)
    );
  }, [platformPincodes, serviceablePincodes]);

  const filteredUrgentPincodes = useMemo(() => {
    return urgentEligiblePincodes.filter((item) => {
      if (filterState !== 'ALL' && item.state !== filterState) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();
      return (
        item.pincode.toLowerCase().includes(q) ||
        item.city.toLowerCase().includes(q) ||
        item.district.toLowerCase().includes(q) ||
        item.state.toLowerCase().includes(q)
      );
    });
  }, [urgentEligiblePincodes, filterState, searchQuery]);

  // Slot eligible pincodes: Must be in serviceablePincodes
  const slotEligiblePincodes = useMemo(() => {
    return platformPincodes.filter((item) => serviceablePincodes.has(item.pincode));
  }, [platformPincodes, serviceablePincodes]);

  const filteredSlotPincodes = useMemo(() => {
    return slotEligiblePincodes.filter((item) => {
      if (filterState !== 'ALL' && item.state !== filterState) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();
      return (
        item.pincode.toLowerCase().includes(q) ||
        item.city.toLowerCase().includes(q) ||
        item.district.toLowerCase().includes(q) ||
        item.state.toLowerCase().includes(q)
      );
    });
  }, [slotEligiblePincodes, filterState, searchQuery]);

  // Toggle Handlers
  const handleToggleServiceable = (pincode: string) => {
    setServiceablePincodes((prev) => {
      const next = new Set(prev);
      if (next.has(pincode)) {
        next.delete(pincode);
        // Automatically prune from urgent and slot pincodes if removed from serviceable
        setUrgentPincodes((u) => {
          const nu = new Set(u);
          nu.delete(pincode);
          return nu;
        });
        setSlotPincodes((s) => {
          const ns = new Set(s);
          ns.delete(pincode);
          return ns;
        });
      } else {
        next.add(pincode);
      }
      return next;
    });
  };

  const handleToggleUrgent = (pincode: string) => {
    if (!allowUrgentDelivery) return;
    setUrgentPincodes((prev) => {
      const next = new Set(prev);
      if (next.has(pincode)) next.delete(pincode);
      else next.add(pincode);
      return next;
    });
  };

  const handleToggleSlot = (pincode: string) => {
    if (!allowDeliverySlots) return;
    setSlotPincodes((prev) => {
      const next = new Set(prev);
      if (next.has(pincode)) next.delete(pincode);
      else next.add(pincode);
      return next;
    });
  };

  // Bulk actions for Current Filtered View
  const handleSelectAllServiceable = () => {
    setServiceablePincodes((prev) => {
      const next = new Set(prev);
      filteredPlatformPincodes.forEach((p) => next.add(p.pincode));
      return next;
    });
  };

  const handleDeselectAllServiceable = () => {
    setServiceablePincodes((prev) => {
      const next = new Set(prev);
      filteredPlatformPincodes.forEach((p) => {
        next.delete(p.pincode);
        setUrgentPincodes((u) => {
          const nu = new Set(u);
          nu.delete(p.pincode);
          return nu;
        });
        setSlotPincodes((s) => {
          const ns = new Set(s);
          ns.delete(p.pincode);
          return ns;
        });
      });
      return next;
    });
  };

  const handleSelectAllUrgent = () => {
    if (!allowUrgentDelivery) return;
    setUrgentPincodes((prev) => {
      const next = new Set(prev);
      filteredUrgentPincodes.forEach((p) => next.add(p.pincode));
      return next;
    });
  };

  const handleDeselectAllUrgent = () => {
    setUrgentPincodes((prev) => {
      const next = new Set(prev);
      filteredUrgentPincodes.forEach((p) => next.delete(p.pincode));
      return next;
    });
  };

  const handleSelectAllSlots = () => {
    if (!allowDeliverySlots) return;
    setSlotPincodes((prev) => {
      const next = new Set(prev);
      filteredSlotPincodes.forEach((p) => next.add(p.pincode));
      return next;
    });
  };

  const handleDeselectAllSlots = () => {
    setSlotPincodes((prev) => {
      const next = new Set(prev);
      filteredSlotPincodes.forEach((p) => next.delete(p.pincode));
      return next;
    });
  };

  // Save changes
  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        serviceablePincodes: Array.from(serviceablePincodes),
        urgentPincodes: Array.from(urgentPincodes),
        slotPincodes: Array.from(slotPincodes),
      };
      await api.put('/users/seller-delivery-settings', payload);
      toast.success('Delivery settings saved successfully!');
      fetchSettings();
    } catch (err: any) {
      logger.error(err);
      toast.error(err?.response?.data?.detail || 'Failed to save delivery settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ padding: '28px 24px', maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: 24,
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#0f172a', margin: 0 }}>
            Delivery &amp; Serviceability Settings
          </h1>
          <p style={{ color: '#64748b', fontSize: 14, marginTop: 4, marginBottom: 0 }}>
            Select the pincodes you service and customize where Urgent Delivery and Delivery Slots are offered.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving || loading}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 22px',
            background: saving ? '#94a3b8' : '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 600,
            cursor: saving || loading ? 'not-allowed' : 'pointer',
            boxShadow: '0 2px 6px rgba(37,99,235,0.25)',
            transition: 'background 0.2s',
          }}
        >
          {saving ? (
            <>Saving…</>
          ) : (
            <>
              <svg width={16} height={16} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Save Settings
            </>
          )}
        </button>
      </div>

      {/* Info Notice */}
      <div
        style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: 10,
          padding: '14px 18px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          fontSize: 13,
          color: '#475569',
        }}
      >
        <div style={{ fontSize: 20 }}>ℹ️</div>
        <div>
          <strong>Platform Delivery Charges:</strong> Base delivery charges, free delivery thresholds, and urgent delivery fees are standardized across the platform. You define <em>which</em> locations you fulfill.
        </div>
      </div>

      {/* Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '2px solid #e2e8f0',
          marginBottom: 20,
          gap: 8,
        }}
      >
        <button
          onClick={() => setActiveTab('serviceable')}
          style={{
            padding: '12px 20px',
            border: 'none',
            background: 'transparent',
            borderBottom: activeTab === 'serviceable' ? '3px solid #2563eb' : '3px solid transparent',
            color: activeTab === 'serviceable' ? '#2563eb' : '#64748b',
            fontWeight: activeTab === 'serviceable' ? 700 : 500,
            fontSize: 14,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          📍 Overall Serviceable Pincodes
          <span
            style={{
              fontSize: 12,
              background: activeTab === 'serviceable' ? '#dbeafe' : '#f1f5f9',
              color: activeTab === 'serviceable' ? '#1e40af' : '#64748b',
              padding: '2px 8px',
              borderRadius: 12,
              fontWeight: 600,
            }}
          >
            {serviceablePincodes.size} / {platformPincodes.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('urgent')}
          style={{
            padding: '12px 20px',
            border: 'none',
            background: 'transparent',
            borderBottom: activeTab === 'urgent' ? '3px solid #f59e0b' : '3px solid transparent',
            color: activeTab === 'urgent' ? '#b45309' : '#64748b',
            fontWeight: activeTab === 'urgent' ? 700 : 500,
            fontSize: 14,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          ⚡ Urgent Delivery
          <span
            style={{
              fontSize: 12,
              background: allowUrgentDelivery ? '#fef3c7' : '#f1f5f9',
              color: allowUrgentDelivery ? '#92400e' : '#94a3b8',
              padding: '2px 8px',
              borderRadius: 12,
              fontWeight: 600,
            }}
          >
            {allowUrgentDelivery ? `${urgentPincodes.size} Active` : 'Disabled'}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('slots')}
          style={{
            padding: '12px 20px',
            border: 'none',
            background: 'transparent',
            borderBottom: activeTab === 'slots' ? '3px solid #10b981' : '3px solid transparent',
            color: activeTab === 'slots' ? '#047857' : '#64748b',
            fontWeight: activeTab === 'slots' ? 700 : 500,
            fontSize: 14,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          🕐 Delivery Slots
          <span
            style={{
              fontSize: 12,
              background: allowDeliverySlots ? '#d1fae5' : '#f1f5f9',
              color: allowDeliverySlots ? '#065f46' : '#94a3b8',
              padding: '2px 8px',
              borderRadius: 12,
              fontWeight: 600,
            }}
          >
            {allowDeliverySlots ? `${slotPincodes.size} Active` : 'Disabled'}
          </span>
        </button>
      </div>

      {/* Permission Warning Banners */}
      {activeTab === 'urgent' && !allowUrgentDelivery && (
        <div
          style={{
            background: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: 10,
            padding: 20,
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div style={{ fontSize: 28 }}>🔒</div>
          <div>
            <h3 style={{ margin: '0 0 4px', fontSize: 16, fontWeight: 700, color: '#92400e' }}>
              Urgent Delivery Not Enabled
            </h3>
            <p style={{ margin: 0, fontSize: 13, color: '#78350f' }}>
              Urgent delivery is currently not activated for your seller account. Please contact the platform admin to enable urgent fulfillment permissions.
            </p>
          </div>
        </div>
      )}

      {activeTab === 'slots' && !allowDeliverySlots && (
        <div
          style={{
            background: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: 10,
            padding: 20,
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div style={{ fontSize: 28 }}>🔒</div>
          <div>
            <h3 style={{ margin: '0 0 4px', fontSize: 16, fontWeight: 700, color: '#92400e' }}>
              Delivery Slots Not Enabled
            </h3>
            <p style={{ margin: 0, fontSize: 13, color: '#78350f' }}>
              Delivery slots are currently not activated for your seller account. Please contact the platform admin to enable scheduled slot permissions.
            </p>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          marginBottom: 16,
          flexWrap: 'wrap',
          background: '#ffffff',
          padding: '12px 16px',
          borderRadius: 10,
          border: '1px solid #e2e8f0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: '1 1 300px' }}>
          <input
            type="text"
            placeholder="Search by pincode, city, district, or state…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 14px',
              borderRadius: 6,
              border: '1px solid #cbd5e1',
              fontSize: 13,
              outline: 'none',
            }}
          />
          {distinctStates.length > 1 && (
            <select
              value={filterState}
              onChange={(e) => setFilterState(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: 6,
                border: '1px solid #cbd5e1',
                fontSize: 13,
                outline: 'none',
                background: '#fff',
              }}
            >
              <option value="ALL">All States</option>
              {distinctStates.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {activeTab === 'serviceable' && (
            <>
              <button
                onClick={handleSelectAllServiceable}
                style={{
                  padding: '7px 14px',
                  background: '#eff6ff',
                  color: '#1d4ed8',
                  border: '1px solid #bfdbfe',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Select Filtered
              </button>
              <button
                onClick={handleDeselectAllServiceable}
                style={{
                  padding: '7px 14px',
                  background: '#fef2f2',
                  color: '#b91c1c',
                  border: '1px solid #fecaca',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Deselect Filtered
              </button>
            </>
          )}

          {activeTab === 'urgent' && allowUrgentDelivery && (
            <>
              <button
                onClick={handleSelectAllUrgent}
                style={{
                  padding: '7px 14px',
                  background: '#fef3c7',
                  color: '#92400e',
                  border: '1px solid #fde68a',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Select Filtered Urgent
              </button>
              <button
                onClick={handleDeselectAllUrgent}
                style={{
                  padding: '7px 14px',
                  background: '#fef2f2',
                  color: '#b91c1c',
                  border: '1px solid #fecaca',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Clear Filtered
              </button>
            </>
          )}

          {activeTab === 'slots' && allowDeliverySlots && (
            <>
              <button
                onClick={handleSelectAllSlots}
                style={{
                  padding: '7px 14px',
                  background: '#d1fae5',
                  color: '#065f46',
                  border: '1px solid #a7f3d0',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Select Filtered Slots
              </button>
              <button
                onClick={handleDeselectAllSlots}
                style={{
                  padding: '7px 14px',
                  background: '#fef2f2',
                  color: '#b91c1c',
                  border: '1px solid #fecaca',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Clear Filtered
              </button>
            </>
          )}
        </div>
      </div>

      {/* Grid Content */}
      {loading ? (
        <div style={{ padding: 48, textAlign: 'center', color: '#94a3b8' }}>Loading delivery network…</div>
      ) : (
        <div style={{ background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          {activeTab === 'serviceable' && (
            <div style={{ padding: 16 }}>
              {filteredPlatformPincodes.length === 0 ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>No pincodes match your search.</div>
              ) : (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                    gap: 12,
                  }}
                >
                  {filteredPlatformPincodes.map((item) => {
                    const isChecked = serviceablePincodes.has(item.pincode);
                    return (
                      <label
                        key={item.pincode}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 12,
                          padding: 14,
                          borderRadius: 8,
                          border: isChecked ? '1.5px solid #2563eb' : '1px solid #e2e8f0',
                          background: isChecked ? '#f0f7ff' : '#ffffff',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleServiceable(item.pincode)}
                          style={{ marginTop: 3, cursor: 'pointer' }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{item.pincode}</span>
                            {item.urgentDeliveryAvailable && (
                              <span
                                style={{
                                  fontSize: 10,
                                  fontWeight: 700,
                                  background: '#fef3c7',
                                  color: '#b45309',
                                  padding: '1px 6px',
                                  borderRadius: 4,
                                }}
                              >
                                ⚡ Urgent Ready
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: 12, color: '#475569', marginTop: 3 }}>
                            {item.city}, {item.district}
                          </div>
                          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>{item.state}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {activeTab === 'urgent' && (
            <div style={{ padding: 16 }}>
              {!allowUrgentDelivery ? (
                <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8' }}>
                  Urgent delivery is disabled by platform admin.
                </div>
              ) : filteredUrgentPincodes.length === 0 ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                  {serviceablePincodes.size === 0
                    ? 'Please select overall serviceable pincodes in Tab 1 first.'
                    : 'No serviceable pincodes support urgent delivery under the current filter.'}
                </div>
              ) : (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                    gap: 12,
                  }}
                >
                  {filteredUrgentPincodes.map((item) => {
                    const isChecked = urgentPincodes.has(item.pincode);
                    return (
                      <label
                        key={item.pincode}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 12,
                          padding: 14,
                          borderRadius: 8,
                          border: isChecked ? '1.5px solid #f59e0b' : '1px solid #e2e8f0',
                          background: isChecked ? '#fffbeb' : '#ffffff',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleUrgent(item.pincode)}
                          style={{ marginTop: 3, cursor: 'pointer' }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{item.pincode}</span>
                            <span
                              style={{
                                fontSize: 10,
                                fontWeight: 700,
                                background: isChecked ? '#fef3c7' : '#f1f5f9',
                                color: isChecked ? '#b45309' : '#94a3b8',
                                padding: '1px 6px',
                                borderRadius: 4,
                              }}
                            >
                              {isChecked ? '⚡ Enabled' : 'Disabled'}
                            </span>
                          </div>
                          <div style={{ fontSize: 12, color: '#475569', marginTop: 3 }}>
                            {item.city}, {item.district}
                          </div>
                          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>{item.state}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {activeTab === 'slots' && (
            <div style={{ padding: 16 }}>
              {!allowDeliverySlots ? (
                <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8' }}>
                  Delivery slots are disabled by platform admin.
                </div>
              ) : filteredSlotPincodes.length === 0 ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                  {serviceablePincodes.size === 0
                    ? 'Please select overall serviceable pincodes in Tab 1 first.'
                    : 'No serviceable pincodes match the current filter.'}
                </div>
              ) : (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                    gap: 12,
                  }}
                >
                  {filteredSlotPincodes.map((item) => {
                    const isChecked = slotPincodes.has(item.pincode);
                    return (
                      <label
                        key={item.pincode}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 12,
                          padding: 14,
                          borderRadius: 8,
                          border: isChecked ? '1.5px solid #10b981' : '1px solid #e2e8f0',
                          background: isChecked ? '#f0fdf4' : '#ffffff',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleSlot(item.pincode)}
                          style={{ marginTop: 3, cursor: 'pointer' }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{item.pincode}</span>
                            <span
                              style={{
                                fontSize: 10,
                                fontWeight: 700,
                                background: isChecked ? '#d1fae5' : '#f1f5f9',
                                color: isChecked ? '#047857' : '#94a3b8',
                                padding: '1px 6px',
                                borderRadius: 4,
                              }}
                            >
                              {isChecked ? '🕐 Enabled' : 'Disabled'}
                            </span>
                          </div>
                          <div style={{ fontSize: 12, color: '#475569', marginTop: 3 }}>
                            {item.city}, {item.district}
                          </div>
                          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>{item.state}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Sticky Bottom Save Bar */}
      <div
        style={{
          marginTop: 24,
          padding: '16px 20px',
          background: '#ffffff',
          borderRadius: 10,
          border: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        }}
      >
        <div style={{ fontSize: 13, color: '#64748b' }}>
          <strong>Summary:</strong> {serviceablePincodes.size} Serviceable &bull;{' '}
          {allowUrgentDelivery ? `${urgentPincodes.size} Urgent` : 'Urgent N/A'} &bull;{' '}
          {allowDeliverySlots ? `${slotPincodes.size} Slots` : 'Slots N/A'}
        </div>
        <button
          onClick={handleSave}
          disabled={saving || loading}
          style={{
            padding: '10px 24px',
            background: saving ? '#94a3b8' : '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 600,
            cursor: saving || loading ? 'not-allowed' : 'pointer',
          }}
        >
          {saving ? 'Saving Changes…' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}
