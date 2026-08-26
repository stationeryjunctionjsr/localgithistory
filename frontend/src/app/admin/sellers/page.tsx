'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Seller {
  id: string;
  name: string;
  email: string;
  phone?: string;
  companyName?: string;
  isActive: boolean;
  commissionOverridePct: number | null;
  effectiveCommissionType: 'override' | 'tiers';
  effectiveTiersSummary: string;
  createdAt: string;
}

interface CommissionTier {
  id?: string;
  minOrderValue: number;
  maxOrderValue: number | null;
  commissionPct: number;
}

interface CommissionSettings {
  tiers: CommissionTier[];
  defaultCommissionPct: number;
}

// ─── Small UI helpers ─────────────────────────────────────────────────────────

const inputStyle: React.CSSProperties = {
  padding: '8px 12px',
  borderRadius: 8,
  border: '1px solid #e5e7eb',
  fontSize: 14,
  width: '100%',
  outline: 'none',
  background: '#fff',
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  fontWeight: 600,
  color: '#6b7280',
  marginBottom: 4,
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
};

const btnPrimary: React.CSSProperties = {
  padding: '8px 18px',
  borderRadius: 8,
  border: 'none',
  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
  color: '#fff',
  fontSize: 14,
  fontWeight: 600,
  cursor: 'pointer',
};

const btnSecondary: React.CSSProperties = {
  padding: '8px 18px',
  borderRadius: 8,
  border: '1px solid #e5e7eb',
  background: '#fff',
  color: '#374151',
  fontSize: 14,
  fontWeight: 500,
  cursor: 'pointer',
};

const btnDanger: React.CSSProperties = {
  padding: '6px 12px',
  borderRadius: 6,
  border: '1px solid #fecaca',
  background: '#fff5f5',
  color: '#dc2626',
  fontSize: 12,
  fontWeight: 600,
  cursor: 'pointer',
};

// ─── Overlap validation ───────────────────────────────────────────────────────

function validateTiers(tiers: CommissionTier[]): string | null {
  const sorted = [...tiers].sort((a, b) => a.minOrderValue - b.minOrderValue);
  for (let i = 0; i < sorted.length - 1; i++) {
    const curr = sorted[i];
    const next = sorted[i + 1];
    if (curr.maxOrderValue === null) {
      return `Tier ${i + 1} has no upper limit but is not the last tier.`;
    }
    if (curr.maxOrderValue >= next.minOrderValue) {
      return `Tiers overlap: a tier ending at ₹${curr.maxOrderValue} overlaps with the next starting at ₹${next.minOrderValue}.`;
    }
  }
  return null;
}

// ─── Sellers Tab ──────────────────────────────────────────────────────────────

function SellersTab() {
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Override modal state
  const [overrideModal, setOverrideModal] = useState<{ sellerId: string; sellerName: string; current: number | null } | null>(null);
  const [overrideValue, setOverrideValue] = useState('');
  const [savingOverride, setSavingOverride] = useState(false);

  const fetchSellers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/commission/sellers');
      setSellers(res.data);
    } catch {
      toast.error('Failed to load sellers');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchSellers(); }, [fetchSellers]);

  const openOverrideModal = (s: Seller) => {
    setOverrideModal({ sellerId: s.id, sellerName: s.name, current: s.commissionOverridePct });
    setOverrideValue(s.commissionOverridePct != null ? String(s.commissionOverridePct) : '');
  };

  const saveOverride = async () => {
    if (!overrideModal) return;
    const pct = parseFloat(overrideValue);
    if (isNaN(pct) || pct < 0 || pct > 100) {
      toast.error('Enter a valid percentage (0–100)');
      return;
    }
    setSavingOverride(true);
    try {
      await api.put(`/commission/sellers/${overrideModal.sellerId}/override`, {
        commissionOverridePct: pct,
      });
      toast.success('Commission override saved');
      setOverrideModal(null);
      fetchSellers();
    } catch {
      toast.error('Failed to save override');
    } finally {
      setSavingOverride(false);
    }
  };

  const removeOverride = async (sellerId: string, sellerName: string) => {
    if (!confirm(`Remove commission override for ${sellerName}? They will revert to global tiers.`)) return;
    try {
      await api.delete(`/commission/sellers/${sellerId}/override`);
      toast.success('Override removed — seller will use global tiers');
      fetchSellers();
    } catch {
      toast.error('Failed to remove override');
    }
  };

  const filtered = sellers.filter(
    (s) =>
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.companyName || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      {/* Search */}
      <div style={{ marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Search sellers by name, email, or company…"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ ...inputStyle, maxWidth: 400 }}
        />
      </div>

      {/* Table */}
      <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                {['Seller', 'Company', 'Status', 'Commission Rate', 'Source', 'Joined', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#374151', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: '#9ca3af' }}>Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: '#9ca3af' }}>No sellers found</td></tr>
              ) : filtered.map((s) => (
                <tr key={s.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontWeight: 600, color: '#1f2937' }}>{s.name}</div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>{s.email}</div>
                    {s.phone && <div style={{ fontSize: 12, color: '#9ca3af' }}>{s.phone}</div>}
                  </td>
                  <td style={{ padding: '12px 16px', color: '#6b7280' }}>{s.companyName || '—'}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                      background: s.isActive ? '#f0fdf4' : '#fef2f2',
                      color: s.isActive ? '#16a34a' : '#dc2626',
                    }}>
                      {s.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {s.commissionOverridePct != null ? (
                      <span style={{ fontWeight: 700, fontSize: 15, color: '#6366f1' }}>
                        {s.commissionOverridePct}%
                      </span>
                    ) : (
                      <span style={{ color: '#6b7280', fontSize: 13 }}>Uses global tiers</span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                      background: s.effectiveCommissionType === 'override' ? '#ede9fe' : '#f1f5f9',
                      color: s.effectiveCommissionType === 'override' ? '#7c3aed' : '#475569',
                    }}>
                      {s.effectiveCommissionType === 'override' ? '🔒 Override' : '📊 Tiers'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#6b7280', whiteSpace: 'nowrap', fontSize: 13 }}>
                    {s.createdAt ? new Date(s.createdAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <button
                        onClick={() => openOverrideModal(s)}
                        style={{
                          padding: '6px 12px', borderRadius: 6, border: '1px solid #c7d2fe',
                          background: '#eef2ff', color: '#4338ca', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                        }}
                      >
                        {s.commissionOverridePct != null ? 'Edit Override' : 'Set Override'}
                      </button>
                      {s.commissionOverridePct != null && (
                        <button onClick={() => removeOverride(s.id, s.name)} style={btnDanger}>
                          Remove
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Override Modal */}
      {overrideModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
          zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            background: '#fff', borderRadius: 16, padding: 32, width: '100%', maxWidth: 440,
            boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }}>
            <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 4 }}>Set Commission Override</h3>
            <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 24 }}>
              Fixed commission rate for <strong>{overrideModal.sellerName}</strong>.
              This overrides global tiers for all their orders.
            </p>

            <div style={{ marginBottom: 20 }}>
              <label style={labelStyle}>Commission Percentage (%)</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={0.01}
                  value={overrideValue}
                  onChange={(e) => setOverrideValue(e.target.value)}
                  placeholder="e.g. 6.5"
                  style={{ ...inputStyle, paddingRight: 36 }}
                  autoFocus
                />
                <span style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  color: '#9ca3af', fontWeight: 700,
                }}>%</span>
              </div>
              <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 6 }}>
                Enter a fixed percentage. Leave blank to remove the override and revert to tiers.
              </p>
            </div>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button onClick={() => setOverrideModal(null)} style={btnSecondary}>Cancel</button>
              <button onClick={saveOverride} disabled={savingOverride} style={btnPrimary}>
                {savingOverride ? 'Saving…' : 'Save Override'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Commission Tiers Tab ─────────────────────────────────────────────────────

function CommissionTiersTab() {
  const [settings, setSettings] = useState<CommissionSettings>({ tiers: [], defaultCommissionPct: 5 });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewValue, setPreviewValue] = useState('');
  const [previewResult, setPreviewResult] = useState<{ commissionPct: number; commissionAmount: number } | null>(null);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/commission/tiers');
      setSettings(res.data);
    } catch {
      toast.error('Failed to load commission settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  const addTier = () => {
    const lastTier = settings.tiers[settings.tiers.length - 1];
    const newMin = lastTier ? (lastTier.maxOrderValue ?? 0) + 1 : 0;
    setSettings((s) => ({
      ...s,
      tiers: [...s.tiers, { minOrderValue: newMin, maxOrderValue: null, commissionPct: 5 }],
    }));
  };

  const removeTier = (idx: number) => {
    setSettings((s) => ({ ...s, tiers: s.tiers.filter((_, i) => i !== idx) }));
  };

  const updateTier = (idx: number, field: keyof CommissionTier, value: string) => {
    setSettings((s) => {
      const tiers = [...s.tiers];
      const parsed = value === '' ? null : Number(value);
      tiers[idx] = { ...tiers[idx], [field]: parsed };
      return { ...s, tiers };
    });
  };

  const saveTiers = async () => {
    const validationError = validateTiers(settings.tiers);
    if (validationError) {
      toast.error(validationError);
      return;
    }
    setSaving(true);
    try {
      await api.put('/commission/tiers', settings);
      toast.success('Commission tiers saved successfully');
      fetchSettings();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save tiers');
    } finally {
      setSaving(false);
    }
  };

  const previewCommission = async () => {
    const val = parseFloat(previewValue);
    if (isNaN(val) || val < 0) { toast.error('Enter a valid order value'); return; }
    try {
      const res = await api.get(`/commission/calculate?order_value=${val}`);
      setPreviewResult(res.data);
    } catch {
      toast.error('Preview failed');
    }
  };

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: '#9ca3af' }}>Loading commission settings…</div>;

  return (
    <div style={{ maxWidth: 840 }}>
      {/* Info banner */}
      <div style={{
        background: 'linear-gradient(135deg, #ede9fe, #ddd6fe)',
        border: '1px solid #c4b5fd',
        borderRadius: 12, padding: '14px 20px', marginBottom: 28,
        display: 'flex', gap: 12, alignItems: 'flex-start',
      }}>
        <span style={{ fontSize: 20 }}>ℹ️</span>
        <div style={{ fontSize: 14, color: '#5b21b6' }}>
          <strong>How commission tiers work:</strong> When a seller order is delivered, the commission rate is
          determined by the order total against these tiers. If no tier matches, the default rate applies.
          Commission is marked <strong>Unrealized</strong> until the return window elapses, then <strong>Realized</strong>.
          You can also set a fixed override on a per-seller basis in the Sellers tab.
        </div>
      </div>

      {/* Default commission */}
      <div style={{
        background: '#fff', borderRadius: 12, padding: 24,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)', marginBottom: 20,
      }}>
        <h3 style={{ fontWeight: 700, fontSize: 16, marginBottom: 16, color: '#1f2937' }}>
          Default Commission Rate
        </h3>
        <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 12 }}>
          Applied when no tier matches the order total.
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ position: 'relative', width: 160 }}>
            <input
              type="number"
              min={0}
              max={100}
              step={0.01}
              value={settings.defaultCommissionPct}
              onChange={(e) => setSettings((s) => ({ ...s, defaultCommissionPct: parseFloat(e.target.value) || 0 }))}
              style={{ ...inputStyle, paddingRight: 36 }}
            />
            <span style={{
              position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
              color: '#9ca3af', fontWeight: 700,
            }}>%</span>
          </div>
          <span style={{ fontSize: 13, color: '#6b7280' }}>Default fallback rate</span>
        </div>
      </div>

      {/* Tiers */}
      <div style={{
        background: '#fff', borderRadius: 12, padding: 24,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)', marginBottom: 20,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <h3 style={{ fontWeight: 700, fontSize: 16, color: '#1f2937', margin: 0 }}>Commission Tiers</h3>
            <p style={{ fontSize: 13, color: '#6b7280', margin: '4px 0 0' }}>
              Set different commission rates based on order value ranges.
            </p>
          </div>
          <button onClick={addTier} style={{
            ...btnSecondary,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span style={{ fontSize: 16 }}>+</span> Add Tier
          </button>
        </div>

        {settings.tiers.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: '32px 20px',
            background: '#f9fafb', borderRadius: 8, border: '2px dashed #e5e7eb',
            color: '#9ca3af', fontSize: 14,
          }}>
            No tiers configured. Click &quot;Add Tier&quot; to get started, or rely on the default rate only.
          </div>
        ) : (
          <div>
            {/* Header */}
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 40px',
              gap: 12, padding: '0 0 8px',
              borderBottom: '1px solid #e5e7eb', marginBottom: 12,
            }}>
              <span style={labelStyle}>Min Order Value (₹)</span>
              <span style={labelStyle}>Max Order Value (₹)</span>
              <span style={labelStyle}>Commission (%)</span>
              <span />
            </div>

            {settings.tiers.map((tier, idx) => (
              <div
                key={idx}
                style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 40px',
                  gap: 12, marginBottom: 12, alignItems: 'center',
                }}
              >
                <input
                  type="number"
                  min={0}
                  step={1}
                  value={tier.minOrderValue ?? ''}
                  onChange={(e) => updateTier(idx, 'minOrderValue', e.target.value)}
                  style={inputStyle}
                  placeholder="0"
                />
                <div style={{ position: 'relative' }}>
                  <input
                    type="number"
                    min={0}
                    step={1}
                    value={tier.maxOrderValue ?? ''}
                    onChange={(e) => updateTier(idx, 'maxOrderValue', e.target.value)}
                    style={inputStyle}
                    placeholder="Unlimited"
                  />
                  {tier.maxOrderValue === null && (
                    <span style={{
                      position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                      fontSize: 11, color: '#9ca3af',
                    }}>∞</span>
                  )}
                </div>
                <div style={{ position: 'relative' }}>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={0.01}
                    value={tier.commissionPct ?? ''}
                    onChange={(e) => updateTier(idx, 'commissionPct', e.target.value)}
                    style={{ ...inputStyle, paddingRight: 32 }}
                    placeholder="5"
                  />
                  <span style={{
                    position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                    color: '#9ca3af', fontWeight: 700, fontSize: 12,
                  }}>%</span>
                </div>
                <button
                  onClick={() => removeTier(idx)}
                  style={{
                    width: 32, height: 32, borderRadius: 6, border: '1px solid #fecaca',
                    background: '#fff5f5', color: '#dc2626', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 16, fontWeight: 700,
                  }}
                  title="Remove tier"
                >
                  ×
                </button>
              </div>
            ))}

            {/* Visual summary */}
            <div style={{
              marginTop: 16, padding: '12px 16px',
              background: '#f9fafb', borderRadius: 8, border: '1px solid #e5e7eb',
            }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#6b7280', marginBottom: 8 }}>TIER PREVIEW</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {[...settings.tiers]
                  .sort((a, b) => a.minOrderValue - b.minOrderValue)
                  .map((t, i) => (
                    <div key={i} style={{
                      background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8,
                      padding: '6px 12px', fontSize: 13,
                    }}>
                      <span style={{ color: '#6b7280' }}>
                        ₹{t.minOrderValue.toLocaleString('en-IN')}
                        {' – '}
                        {t.maxOrderValue != null ? `₹${t.maxOrderValue.toLocaleString('en-IN')}` : '∞'}
                      </span>
                      <span style={{ fontWeight: 700, color: '#6366f1', marginLeft: 8 }}>
                        {t.commissionPct}%
                      </span>
                    </div>
                  ))}
                <div style={{
                  background: '#fef9c3', border: '1px solid #fde047', borderRadius: 8,
                  padding: '6px 12px', fontSize: 13,
                }}>
                  <span style={{ color: '#713f12' }}>Default: </span>
                  <span style={{ fontWeight: 700, color: '#854d0e' }}>{settings.defaultCommissionPct}%</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Save button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 32 }}>
        <button onClick={saveTiers} disabled={saving} style={{ ...btnPrimary, minWidth: 140 }}>
          {saving ? 'Saving…' : '💾 Save Tiers'}
        </button>
      </div>

      {/* Commission Preview Calculator */}
      <div style={{
        background: '#fff', borderRadius: 12, padding: 24,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      }}>
        <h3 style={{ fontWeight: 700, fontSize: 16, color: '#1f2937', marginBottom: 8 }}>
          Commission Preview Calculator
        </h3>
        <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 16 }}>
          Enter an order value to see what commission would apply using the current global tiers.
        </p>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={labelStyle}>Order Value (₹)</label>
            <div style={{ position: 'relative' }}>
              <span style={{
                position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
                color: '#9ca3af', fontWeight: 600,
              }}>₹</span>
              <input
                type="number"
                min={0}
                step={1}
                value={previewValue}
                onChange={(e) => { setPreviewValue(e.target.value); setPreviewResult(null); }}
                style={{ ...inputStyle, paddingLeft: 28, width: 180 }}
                placeholder="1500"
              />
            </div>
          </div>
          <button onClick={previewCommission} style={btnPrimary}>Calculate</button>
        </div>

        {previewResult && (
          <div style={{
            marginTop: 16, display: 'flex', gap: 24,
            background: 'linear-gradient(135deg, #ede9fe, #f5f3ff)',
            borderRadius: 10, padding: '16px 24px',
            border: '1px solid #ddd6fe',
          }}>
            <div>
              <div style={{ fontSize: 12, color: '#7c3aed', fontWeight: 600, textTransform: 'uppercase' }}>Commission Rate</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: '#6d28d9' }}>{previewResult.commissionPct}%</div>
            </div>
            <div style={{ borderLeft: '1px solid #c4b5fd', paddingLeft: 24 }}>
              <div style={{ fontSize: 12, color: '#7c3aed', fontWeight: 600, textTransform: 'uppercase' }}>Commission Amount</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: '#6d28d9' }}>
                ₹{previewResult.commissionAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function SellersPage() {
  const [activeTab, setActiveTab] = useState<'sellers' | 'commission'>('sellers');

  const TAB_CONFIG = [
    { id: 'sellers' as const, label: '🏪 Sellers', description: 'All marketplace sellers and individual commission overrides' },
    { id: 'commission' as const, label: '📊 Commission Tiers', description: 'Global tier-based commission rates' },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Page header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4, color: '#1f2937' }}>Sellers</h1>
        <p style={{ color: '#6b7280', fontSize: 14 }}>
          Manage marketplace sellers and configure commission rates.
        </p>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: 0, marginBottom: 28,
        borderBottom: '2px solid #e5e7eb',
      }}>
        {TAB_CONFIG.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 24px',
              fontSize: 14,
              fontWeight: 600,
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              color: activeTab === tab.id ? '#6366f1' : '#6b7280',
              borderBottom: activeTab === tab.id ? '2px solid #6366f1' : '2px solid transparent',
              marginBottom: -2,
              transition: 'color 0.15s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'sellers' ? <SellersTab /> : <CommissionTiersTab />}
    </div>
  );
}
