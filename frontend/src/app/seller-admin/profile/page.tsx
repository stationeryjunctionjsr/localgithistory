'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';

interface AvailabilityWindow {
  _id: string;
  startAt: string;
  endAt: string;
  reason?: string;
  status: 'scheduled' | 'active' | 'ended' | 'cancelled';
  createdAt: string;
}

export default function SellerProfilePage() {
  const { user, fetchUser } = useAuth();
  const [form, setForm] = useState({ name: '', companyName: '', phone: '', email: '' });
  const [saving, setSaving] = useState(false);

  // Availability state
  const [windows, setWindows] = useState<AvailabilityWindow[]>([]);
  const [avLoading, setAvLoading] = useState(true);
  const [avForm, setAvForm] = useState({ startAt: '', endAt: '', reason: '' });
  const [avSubmitting, setAvSubmitting] = useState(false);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setForm({
        name: user.name || '',
        companyName: user.companyName || '',
        phone: (user as any).phone || '',
        email: user.email || '',
      });
    }
  }, [user]);

  useEffect(() => { fetchWindows(); }, []);

  const fetchWindows = async () => {
    setAvLoading(true);
    try {
      const res = await api.get('/seller-availability/my');
      setWindows(res.data || []);
    } catch { /* silent */ }
    finally { setAvLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/users/${user?._id}`, { name: form.name, companyName: form.companyName, phone: form.phone });
      toast.success('Profile updated');
      await fetchUser();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to update profile');
    } finally { setSaving(false); }
  };

  const handleScheduleOff = async () => {
    if (!avForm.startAt || !avForm.endAt) {
      toast.error('Please set both start and end date/time');
      return;
    }
    setAvSubmitting(true);
    try {
      await api.post('/seller-availability', {
        startAt: new Date(avForm.startAt).toISOString(),
        endAt: new Date(avForm.endAt).toISOString(),
        reason: avForm.reason || undefined,
      });
      toast.success('Store time-off scheduled');
      setAvForm({ startAt: '', endAt: '', reason: '' });
      fetchWindows();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to schedule time-off');
    } finally { setAvSubmitting(false); }
  };

  const handleCancelWindow = async (id: string) => {
    setCancellingId(id);
    try {
      await api.delete(`/seller-availability/${id}`);
      toast.success('Time-off window cancelled');
      fetchWindows();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to cancel');
    } finally { setCancellingId(null); }
  };

  const field = (label: string, key: keyof typeof form, disabled = false) => (
    <div style={{ display: 'flex', flexDirection: 'column' as const, gap: 6 }}>
      <label style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>{label}</label>
      <input
        type="text"
        value={form[key]}
        disabled={disabled}
        onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
        style={{
          padding: '9px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14,
          background: disabled ? '#f9fafb' : '#fff', color: disabled ? '#9ca3af' : '#111827',
          cursor: disabled ? 'not-allowed' : 'text',
        }}
      />
    </div>
  );

  const statusColor = (status: string) => {
    if (status === 'active') return { bg: '#fee2e2', color: '#b91c1c', label: '🔴 Active now' };
    if (status === 'scheduled') return { bg: '#fef9c3', color: '#a16207', label: '🟡 Scheduled' };
    if (status === 'ended') return { bg: '#f0fdf4', color: '#15803d', label: '✅ Ended' };
    return { bg: '#f3f4f6', color: '#6b7280', label: '⚫ Cancelled' };
  };

  const fmtDt = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
    } catch { return iso; }
  };

  const upcoming = windows.filter(w => w.status === 'scheduled' || w.status === 'active');
  const past = windows.filter(w => w.status === 'ended' || w.status === 'cancelled').slice(0, 5);

  return (
    <div style={{ padding: '28px 24px', maxWidth: 600 }}>
      {/* ── Profile Card ── */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#111827', margin: 0 }}>My Profile</h1>
        <p style={{ color: '#6b7280', fontSize: 14, marginTop: 4 }}>Update your seller profile information</p>
      </div>

      <div style={{ background: '#fff', borderRadius: 14, padding: 28, boxShadow: '0 1px 4px rgba(0,0,0,0.07)', display: 'grid', gap: 18, marginBottom: 28 }}>
        {field('Full Name', 'name')}
        {field('Company Name', 'companyName')}
        {field('Phone', 'phone')}
        {field('Email', 'email', true)}

        {/* Permissions banner */}
        <div style={{ background: '#f0f9ff', borderRadius: 10, padding: '14px 16px', border: '1px solid #bae6fd' }}>
          <div style={{ fontWeight: 600, fontSize: 13, color: '#0369a1', marginBottom: 8 }}>Seller Permissions</div>
          <div style={{ display: 'flex', gap: 16 }}>
            <span style={{
              fontSize: 12, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
              background: user?.sellerPermissions?.allowDeliverySlots ? '#dcfce7' : '#f3f4f6',
              color: user?.sellerPermissions?.allowDeliverySlots ? '#15803d' : '#9ca3af',
            }}>
              {user?.sellerPermissions?.allowDeliverySlots ? '✓' : '✗'} Delivery Slots
            </span>
            <span style={{
              fontSize: 12, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
              background: user?.sellerPermissions?.allowUrgentDelivery ? '#dcfce7' : '#f3f4f6',
              color: user?.sellerPermissions?.allowUrgentDelivery ? '#15803d' : '#9ca3af',
            }}>
              {user?.sellerPermissions?.allowUrgentDelivery ? '✓' : '✗'} Urgent Delivery
            </span>
          </div>
          <p style={{ fontSize: 12, color: '#64748b', marginTop: 8, marginBottom: 0 }}>
            Contact the platform admin to change permissions.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            padding: '10px 20px', background: saving ? '#9ca3af' : '#4f46e5', color: '#fff',
            border: 'none', borderRadius: 9, cursor: saving ? 'not-allowed' : 'pointer',
            fontWeight: 600, fontSize: 14, alignSelf: 'start',
          }}
        >
          {saving ? 'Saving…' : 'Save Changes'}
        </button>
      </div>

      {/* ── Store Availability Card ── */}
      <div style={{ background: '#fff', borderRadius: 14, padding: 28, boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: '#111827', margin: '0 0 4px' }}>Store Availability</h2>
        <p style={{ fontSize: 13, color: '#6b7280', marginTop: 0, marginBottom: 20 }}>
          Schedule time off. During unavailability, your products won&apos;t appear for your pincodes.
          Must be set at least <strong>3 hours before</strong> the start time.
        </p>

        {/* Schedule form */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>Start Date &amp; Time</label>
            <input
              type="datetime-local"
              value={avForm.startAt}
              onChange={e => setAvForm(f => ({ ...f, startAt: e.target.value }))}
              style={{ padding: '9px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>End Date &amp; Time</label>
            <input
              type="datetime-local"
              value={avForm.endAt}
              onChange={e => setAvForm(f => ({ ...f, endAt: e.target.value }))}
              style={{ padding: '9px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}
            />
          </div>
        </div>
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Reason (optional)</label>
          <input
            type="text"
            placeholder="e.g. Festival holiday, stock replenishment…"
            value={avForm.reason}
            onChange={e => setAvForm(f => ({ ...f, reason: e.target.value }))}
            style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14, boxSizing: 'border-box' }}
          />
        </div>
        <button
          onClick={handleScheduleOff}
          disabled={avSubmitting}
          style={{
            padding: '9px 20px', background: avSubmitting ? '#9ca3af' : 'linear-gradient(135deg,#f59e0b 0%,#d97706 100%)',
            color: '#fff', border: 'none', borderRadius: 9, cursor: avSubmitting ? 'not-allowed' : 'pointer',
            fontWeight: 600, fontSize: 14,
          }}
        >
          {avSubmitting ? 'Scheduling…' : '⏸ Schedule Time Off'}
        </button>

        {/* Upcoming windows */}
        {avLoading ? (
          <p style={{ color: '#9ca3af', marginTop: 20, fontSize: 13 }}>Loading…</p>
        ) : (
          <>
            {upcoming.length > 0 && (
              <div style={{ marginTop: 24 }}>
                <h3 style={{ fontSize: 13, fontWeight: 700, color: '#374151', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Upcoming / Active</h3>
                {upcoming.map(w => {
                  const sc = statusColor(w.status);
                  return (
                    <div key={w._id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: sc.bg, borderRadius: 10, marginBottom: 8 }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 14, color: '#111827' }}>{fmtDt(w.startAt)} → {fmtDt(w.endAt)}</div>
                        {w.reason && <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{w.reason}</div>}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ background: sc.bg, color: sc.color, fontSize: 12, fontWeight: 700, padding: '2px 10px', borderRadius: 20, border: `1px solid ${sc.color}33` }}>{sc.label}</span>
                        {w.status === 'scheduled' && (
                          <button
                            onClick={() => handleCancelWindow(w._id)}
                            disabled={cancellingId === w._id}
                            style={{ background: '#fee2e2', color: '#b91c1c', border: 'none', borderRadius: 7, padding: '4px 10px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
                          >
                            {cancellingId === w._id ? '…' : 'Cancel'}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {past.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <h3 style={{ fontSize: 13, fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Recent History</h3>
                {past.map(w => {
                  const sc = statusColor(w.status);
                  return (
                    <div key={w._id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 14px', background: '#f9fafb', borderRadius: 8, marginBottom: 6, opacity: 0.8 }}>
                      <div style={{ fontSize: 13, color: '#374151' }}>{fmtDt(w.startAt)} → {fmtDt(w.endAt)}</div>
                      <span style={{ fontSize: 12, color: sc.color, fontWeight: 600 }}>{sc.label}</span>
                    </div>
                  );
                })}
              </div>
            )}

            {upcoming.length === 0 && past.length === 0 && (
              <p style={{ color: '#9ca3af', marginTop: 16, fontSize: 13 }}>No time-off windows scheduled. Your store is always available.</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
