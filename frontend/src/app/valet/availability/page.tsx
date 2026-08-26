'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';

import { useAuth } from '@/context/AuthContext';
import { logger } from '@/utils/logger';

interface Slot {
  id: string;
  startTime: string;
  endTime: string;
  isActive?: boolean;
}

interface AvailabilityDoc {
  _id: string;
  date: string;
  availabilityType: 'full_day' | 'custom';
  slots: string[];
  zones: string[];
}

function formatDate(isoDate: string): string {
  const d = new Date(isoDate + 'T00:00:00');
  return d.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' });
}

function getNextDays(n = 7): string[] {
  const days: string[] = [];
  const today = new Date();
  for (let i = 0; i < n; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    days.push(d.toISOString().split('T')[0]);
  }
  return days;
}

export default function ValetAvailabilityPage() {
  const { user } = useAuth();
  const [dates] = useState<string[]>(getNextDays(7));
  const [selectedDate, setSelectedDate] = useState<string>(getNextDays(7)[0]);
  const [adminSlots, setAdminSlots] = useState<Slot[]>([]);
  const [myAvailability, setMyAvailability] = useState<AvailabilityDoc[]>([]);
  const [allZones, setAllZones] = useState<any[]>([]);
  
  const [availabilityType, setAvailabilityType] = useState<'full_day' | 'custom' | ''>('');
  const [selectedSlots, setSelectedSlots] = useState<string[]>([]);
  const [selectedZones, setSelectedZones] = useState<string[]>([]);
  
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const currentEntry = myAvailability.find((a) => a.date === selectedDate);
  const myPermittedZones = (user as any)?.serviceAreaZones || [];

  const fetchAdminSlots = useCallback(async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await api.get(`/delivery-slots?date=${selectedDate || today}`);
      const configs = res.data || [];
      const allSlots: Slot[] = [];
      configs.forEach((cfg: any) => {
        (cfg.slots || []).forEach((s: any) => {
          if (s.isActive !== false) allSlots.push(s);
        });
      });
      setAdminSlots(allSlots);
    } catch (e) { logger.warn("Silent catch block:", e); /* Silently ignore — slots may not be configured for this date */ }
  }, [selectedDate]);

  const fetchZones = useCallback(async () => {
    try {
      const res = await api.get('/delivery-zones');
      setAllZones(res.data || []);
    } catch (e) { logger.warn("Silent catch block:", e); /* ignore */ }
  }, []);

  const fetchMyAvailability = useCallback(async () => {
    try {
      const res = await api.get('/valet-availability/my');
      setMyAvailability(res.data || []);
    } catch (e) { logger.warn("Silent catch block:", e); /* ignore */ }
  }, []);

  useEffect(() => {
    fetchAdminSlots();
  }, [fetchAdminSlots]);

  useEffect(() => {
    fetchMyAvailability();
    fetchZones();
  }, [fetchMyAvailability, fetchZones]);

  // Sync form to existing entry when date changes
  useEffect(() => {
    if (currentEntry) {
      setAvailabilityType(currentEntry.availabilityType);
      setSelectedSlots(currentEntry.slots || []);
      setSelectedZones(currentEntry.zones || []);
    } else {
      setAvailabilityType('');
      setSelectedSlots([]);
      setSelectedZones(myPermittedZones);
    }
  }, [selectedDate, currentEntry, myPermittedZones]);

  const handleSave = async () => {
    if (!availabilityType) {
      toast.warning('Select Full Day or choose specific slots');
      return;
    }
    if (availabilityType === 'custom' && selectedSlots.length === 0) {
      toast.warning('Select at least one slot');
      return;
    }
    if (selectedZones.length === 0) {
      toast.warning('Select at least one zone');
      return;
    }
    setSaving(true);
    try {
      await api.post('/valet-availability', {
        date: selectedDate,
        availabilityType,
        slots: availabilityType === 'full_day' ? [] : selectedSlots,
        zones: selectedZones,
      });
      toast.success('Availability saved!');
      fetchMyAvailability();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to save availability');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!currentEntry) return;
    setDeleting(true);
    try {
      await api.delete(`/valet-availability/${currentEntry._id}`);
      toast.success('Availability removed');
      setAvailabilityType('');
      setSelectedSlots([]);
      fetchMyAvailability();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to remove');
    } finally {
      setDeleting(false);
    }
  };

  const toggleSlot = (slotId: string) => {
    setSelectedSlots((prev) =>
      prev.includes(slotId) ? prev.filter((s) => s !== slotId) : [...prev, slotId]
    );
  };

  return (
    <div style={{ padding: '24px', maxWidth: 600, margin: '0 auto' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111827', marginBottom: 4 }}>
        📅 My Availability
      </h1>
      <p style={{ color: '#6b7280', fontSize: 13, marginBottom: 24 }}>
        Mark your availability so sellers can assign deliveries to you.
      </p>

      {/* Date tabs */}
      <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4, marginBottom: 24 }}>
        {dates.map((date, i) => {
          const hasEntry = myAvailability.find((a) => a.date === date);
          const isToday = i === 0;
          const isSelected = date === selectedDate;
          return (
            <button
              key={date}
              onClick={() => setSelectedDate(date)}
              style={{
                flexShrink: 0, padding: '10px 14px', borderRadius: 10,
                border: isSelected ? '2px solid #6d28d9' : '2px solid #e5e7eb',
                background: isSelected ? '#f5f3ff' : '#fff',
                cursor: 'pointer', textAlign: 'center', minWidth: 72,
              }}
            >
              <div style={{ fontSize: 11, color: isSelected ? '#6d28d9' : '#6b7280', fontWeight: 600 }}>
                {isToday ? 'Today' : formatDate(date).split(',')[0]}
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: isSelected ? '#4c1d95' : '#111827', marginTop: 2 }}>
                {new Date(date + 'T00:00:00').getDate()}
              </div>
              {hasEntry && (
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#16a34a', margin: '3px auto 0' }} />
              )}
            </button>
          );
        })}
      </div>

      {/* Selected date card */}
      <div style={{
        background: '#fff', borderRadius: 16, padding: 20,
        border: '1px solid #e5e7eb', boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      }}>
        <div style={{ fontWeight: 600, fontSize: 15, color: '#111827', marginBottom: 16 }}>
          {formatDate(selectedDate)}
          {currentEntry && (
            <span style={{
              marginLeft: 10, fontSize: 12, fontWeight: 600,
              padding: '2px 10px', borderRadius: 20,
              background: '#dcfce7', color: '#15803d',
            }}>
              ✓ Marked
            </span>
          )}
        </div>

        {/* Full day toggle */}
        <div
          onClick={() => {
            setAvailabilityType('full_day');
            setSelectedSlots([]);
          }}
          style={{
            display: 'flex', alignItems: 'center', gap: 14,
            padding: '14px 16px', borderRadius: 12, cursor: 'pointer', marginBottom: 10,
            border: availabilityType === 'full_day' ? '2px solid #6d28d9' : '2px solid #e5e7eb',
            background: availabilityType === 'full_day' ? '#f5f3ff' : '#fafafa',
            transition: 'all 0.15s',
          }}
        >
          <div style={{
            width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
            border: availabilityType === 'full_day' ? '6px solid #6d28d9' : '2px solid #d1d5db',
          }} />
          <div>
            <div style={{ fontWeight: 600, color: '#111827', fontSize: 14 }}>Full Day Available</div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>9:00 AM – 7:00 PM · All slots included</div>
          </div>
        </div>

        {/* Custom slots toggle */}
        <div
          onClick={() => setAvailabilityType('custom')}
          style={{
            padding: '14px 16px', borderRadius: 12, cursor: 'pointer', marginBottom: 14,
            border: availabilityType === 'custom' ? '2px solid #6d28d9' : '2px solid #e5e7eb',
            background: availabilityType === 'custom' ? '#f5f3ff' : '#fafafa',
            transition: 'all 0.15s',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
              border: availabilityType === 'custom' ? '6px solid #6d28d9' : '2px solid #d1d5db',
            }} />
            <div>
              <div style={{ fontWeight: 600, color: '#111827', fontSize: 14 }}>Specific Slots Only</div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>Choose the time slots you are available for</div>
            </div>
          </div>

          {availabilityType === 'custom' && (
            <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {adminSlots.length === 0 ? (
                <p style={{ fontSize: 12, color: '#9ca3af', margin: 0 }}>
                  No slots configured for this date by admin.
                </p>
              ) : (
                adminSlots.map((slot) => {
                  const isOn = selectedSlots.includes(slot.id);
                  return (
                    <button
                      key={slot.id}
                      onClick={(e) => { e.stopPropagation(); toggleSlot(slot.id); }}
                      style={{
                        padding: '6px 12px', borderRadius: 8, fontSize: 13, fontWeight: 600,
                        border: isOn ? '2px solid #6d28d9' : '2px solid #d1d5db',
                        background: isOn ? '#ede9fe' : '#fff',
                        color: isOn ? '#4c1d95' : '#374151',
                        cursor: 'pointer', transition: 'all 0.12s',
                      }}
                    >
                      {slot.startTime} – {slot.endTime}
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>
        {/* Zone Selection */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontWeight: 600, color: '#111827', fontSize: 14, marginBottom: 8 }}>Available Zones</div>
          {myPermittedZones.length === 0 ? (
            <p style={{ fontSize: 13, color: '#ef4444', margin: 0 }}>
              You are not assigned to any zones. Contact admin.
            </p>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {myPermittedZones.map((zoneId: string) => {
                const zoneDoc = allZones.find((z) => z._id === zoneId || z.id === zoneId);
                const zoneName = zoneDoc ? zoneDoc.name : zoneId;
                const isOn = selectedZones.includes(zoneId);
                return (
                  <button
                    key={zoneId}
                    onClick={() => {
                      setSelectedZones((prev) =>
                        prev.includes(zoneId) ? prev.filter((z) => z !== zoneId) : [...prev, zoneId]
                      );
                    }}
                    style={{
                      padding: '6px 12px', borderRadius: 8, fontSize: 13, fontWeight: 600,
                      border: isOn ? '2px solid #0ea5e9' : '2px solid #e5e7eb',
                      background: isOn ? '#e0f2fe' : '#fafafa',
                      color: isOn ? '#0369a1' : '#4b5563',
                      cursor: 'pointer', transition: 'all 0.12s',
                    }}
                  >
                    {zoneName}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={handleSave}
            disabled={saving || !availabilityType}
            style={{
              flex: 1, padding: '11px 0', borderRadius: 10, border: 'none',
              background: availabilityType && !saving ? '#6d28d9' : '#c4b5fd',
              color: '#fff', fontWeight: 700, fontSize: 14,
              cursor: availabilityType && !saving ? 'pointer' : 'not-allowed',
              transition: 'background 0.15s',
            }}
          >
            {saving ? 'Saving…' : currentEntry ? '✓ Update' : '✓ Save Availability'}
          </button>
          {currentEntry && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              style={{
                padding: '11px 16px', borderRadius: 10, border: '1px solid #fca5a5',
                background: '#fff', color: '#dc2626', fontWeight: 600, fontSize: 14,
                cursor: deleting ? 'not-allowed' : 'pointer',
              }}
            >
              {deleting ? '…' : '🗑'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
