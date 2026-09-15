'use client';
import { logger } from "@/utils/logger";

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/Admin/AdminLayout';
import { toast } from 'react-hot-toast';
import { format, addDays } from 'date-fns';
import api from '@/utils/api';

interface Slot {
  id: string;
  startTime: string;
  endTime: string;
  capacity: number;
  bookedCount: number;
  isActive: boolean;
  isUrgent: boolean;
  isFullDay?: boolean;
  deliveredCount?: number;
  cutoffHours: number | null;
  urgentCutoffHours: number | null;
}

export default function DeliverySlotsPage() {
  const [selectedDates, setSelectedDates] = useState<string[]>([format(new Date(), 'yyyy-MM-dd')]);
  const primaryDate = selectedDates[0];
  const [segment, setSegment] = useState('retail');
  const [selectedZoneIds, setSelectedZoneIds] = useState<string[]>(['default']);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [originalSlots, setOriginalSlots] = useState<Slot[]>([]);
  const [configId, setConfigId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Zones
  const [zones, setZones] = useState<any[]>([]);
  const [loadingZones, setLoadingZones] = useState(false);

  // Urgent delivery charge (global setting stored in default delivery charge)
  const [urgentDeliveryCharge, setUrgentDeliveryCharge] = useState('');
  const [_defaultChargeId, setDefaultChargeId] = useState<string | null>(null);
  const [savingUrgent, setSavingUrgent] = useState(false);

  // Generate next 7 dates
  const next7Days = Array.from({ length: 7 }).map((_, i) =>
    format(addDays(new Date(), i), 'yyyy-MM-dd')
  );

  // The capacity to auto-fill for new slots — based on first selected real zone's defaultCapacity
  const primaryZoneCapacity = (() => {
    const firstRealZone = selectedZoneIds.find(id => id !== 'default');
    if (firstRealZone) {
      const zone = zones.find((z: any) => (z._id || z.id) === firstRealZone);
      return zone?.defaultCapacity ?? 10;
    }
    return 10;
  })();

  useEffect(() => {
    fetchConfig();
  }, [primaryDate, segment]);

  useEffect(() => {
    fetchZones();
    fetchUrgentCharge();
  }, []);

  const fetchZones = async () => {
    setLoadingZones(true);
    try {
      const res = await api.get('/delivery-zones');
      setZones(res.data || []);
    } catch (err) {
      console.error('Failed to fetch zones', err);
      toast.error('Could not load delivery zones');
    } finally {
      setLoadingZones(false);
    }
  };

  const fetchUrgentCharge = async () => {
    try {
      const res = await api.get('/delivery-charges/default');
      setUrgentDeliveryCharge(res.data?.urgentDeliveryCharge?.toString() ?? '');
      setDefaultChargeId(res.data?._id ?? null);
    } catch (e: any) { logger.warn("Background task failed", e); }
  };

  const handleSaveUrgentCharge = async () => {
    setSavingUrgent(true);
    try {
      const res = await api.get('/delivery-charges/default');
      const existing = res.data || {};
      const payload = {
        ...existing,
        urgentDeliveryCharge: urgentDeliveryCharge ? parseFloat(urgentDeliveryCharge) : null,
        tiers: existing.tiers || [],
      };
      await api.post('/delivery-charges/default', payload);
      toast.success('Urgent delivery charge saved');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save urgent delivery charge');
    } finally {
      setSavingUrgent(false);
    }
  };

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/delivery-slots?date=${primaryDate}&segment=${segment}`);
      const data = response.data;
      if (data && data.length > 0) {
        const config = data[0];
        setConfigId(config._id);
        setSelectedZoneIds(config.zoneId ? [config.zoneId] : ['default']);
        setSlots(
          (config.slots || []).map((s: any) => ({
            id: s.id,
            startTime: s.startTime,
            endTime: s.endTime,
            capacity: s.capacity ?? 0,
            bookedCount: s.bookedCount ?? 0,
            isActive: s.isActive !== false,
            isUrgent: s.isUrgent === true,
            cutoffHours: s.cutoffHours ?? null,
            urgentCutoffHours: s.urgentCutoffHours ?? null,
          }))
        );
      } else {
        setConfigId(null);
        setSelectedZoneIds(['default']);
        setSlots([]);
        setOriginalSlots([]);
      }
    } catch (error) {
      console.error('Failed to fetch config', error);
      toast.error('Failed to load delivery slots');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    // 1. Validation: Overlaps
    const fullDaySlots = slots.filter(s => s.isFullDay);
    if (fullDaySlots.length > 1) {
      toast.error('You can only add one Anytime slot per day');
      return;
    }
    
    const urgentSlots = slots.filter(s => s.isUrgent && !s.isFullDay).sort((a,b) => a.startTime.localeCompare(b.startTime));
    for (let i = 0; i < urgentSlots.length - 1; i++) {
      if (urgentSlots[i].endTime > urgentSlots[i+1].startTime) {
        toast.error(`Urgent slots overlap: ${urgentSlots[i].startTime}-${urgentSlots[i].endTime} overlaps with ${urgentSlots[i+1].startTime}-${urgentSlots[i+1].endTime}`);
        return;
      }
    }

    const standardSlots = slots.filter(s => !s.isUrgent && !s.isFullDay).sort((a,b) => a.startTime.localeCompare(b.startTime));
    for (let i = 0; i < standardSlots.length - 1; i++) {
      if (standardSlots[i].endTime > standardSlots[i+1].startTime) {
        toast.error(`Standard slots overlap: ${standardSlots[i].startTime}-${standardSlots[i].endTime} overlaps with ${standardSlots[i+1].startTime}-${standardSlots[i+1].endTime}`);
        return;
      }
    }

    // 2. Validation: Cutoffs for new/modified slots
    const now = new Date();
    for (const dateStr of selectedDates) {
      const [year, month, day] = dateStr.split('-').map(Number);
      
      for (const slot of slots) {
        if (slot.isFullDay) continue;
        
        const originalSlot = originalSlots.find(s => s.id === slot.id);
        const isModified = !originalSlot || 
          originalSlot.startTime !== slot.startTime || 
          originalSlot.endTime !== slot.endTime || 
          originalSlot.cutoffHours !== slot.cutoffHours || 
          originalSlot.urgentCutoffHours !== slot.urgentCutoffHours;
          
        if (isModified) {
          const isUrgent = slot.isUrgent;
          const cutoffHours = isUrgent ? slot.urgentCutoffHours : slot.cutoffHours;
          if (cutoffHours !== null) {
            const anchorTimeStr = isUrgent ? slot.endTime : slot.startTime;
            if (!anchorTimeStr) {
              toast.error('Please set start and end times for all slots');
              return;
            }
            const [hours, minutes] = anchorTimeStr.split(':').map(Number);
            const anchorDate = new Date(year, month - 1, day, hours, minutes, 0, 0);
            const cutoffDate = new Date(anchorDate.getTime() - (cutoffHours * 60 * 60 * 1000));
            
            if (cutoffDate <= now) {
              toast.error(`Cannot save: The cutoff time for the newly added/modified slot ending/starting at ${anchorTimeStr} on ${dateStr} has already passed.`);
              return;
            }
          }
        }
      }
    }

    setSaving(true);
    try {
      const payload = {
        segment,
        date: primaryDate,
        zoneIds: selectedZoneIds,
        slots,
        isActive: true,
      };

      // For multi-date, we send the same zones+slots for each date
      for (const date of selectedDates) {
        await api.post(`/delivery-slots`, { ...payload, date });
      }

      toast.success(selectedDates.length > 1 ? `Saved slots for ${selectedDates.length} dates` : 'Updated delivery slots');
      fetchConfig();
    } catch (error: any) {
      const msg = error?.response?.data?.detail || 'Failed to save delivery slots';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const addSlot = () => {
    setSlots([
      ...slots,
      {
        id: Date.now().toString(),
        startTime: '',
        endTime: '',
        capacity: primaryZoneCapacity,
        bookedCount: 0,
        isActive: true,
        isUrgent: false,
        cutoffHours: null,
        urgentCutoffHours: null,
      },
    ]);
  };

  const addFullDaySlot = () => {
    setSlots([
      ...slots,
      {
        id: Date.now().toString(),
        startTime: '00:00',
        endTime: '23:59',
        capacity: primaryZoneCapacity,
        bookedCount: 0,
        isActive: true,
        isUrgent: false,
        isFullDay: true,
        cutoffHours: null,
        urgentCutoffHours: null,
      },
    ]);
  };

  const addUrgentSlot = () => {
    setSlots([
      ...slots,
      {
        id: Date.now().toString(),
        startTime: '09:00',
        endTime: '22:00',
        capacity: primaryZoneCapacity,
        bookedCount: 0,
        isActive: true,
        isUrgent: true,
        isFullDay: false,
        cutoffHours: null,
        urgentCutoffHours: 1,
      },
    ]);
  };
  const removeSlot = (id: string) => {
    setSlots(slots.filter((s) => s.id !== id));
  };

  const updateSlot = (id: string, field: string, value: string | number | boolean | null) => {
    setSlots(slots.map((s) => (s.id === id ? { ...s, [field]: value } : s)));
  };

    // Slot configuration requires no pincode filtering anymore, purely zoneId driven

  return (
    <AdminLayout>
      <div className="flex h-full flex-col gap-6">
        {/* ── Header ─────────────────────────────────── */}
        <header className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Delivery Slots</h1>
            <p className="mt-1 text-sm text-slate-500">
              Configure time slots for the next 7 days. Only serviceable pincodes are shown.
            </p>
          </div>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </header>

        {/* ── Urgent Delivery Settings ─────────────────── */}
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
          <h2 className="mb-1 text-base font-semibold text-amber-900">⚡ Urgent Delivery Settings</h2>
          <p className="mb-3 text-xs text-amber-700">
            Set the flat surcharge applied when a customer books a slot marked as &quot;Urgent&quot;. This
            charge is applied on top of the standard delivery charge.{' '}
            <strong>These settings apply to {segment === 'retail' ? 'Retail Customers' : 'Business Customers'} globally.</strong>
          </p>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-amber-800">
                Urgent Delivery Charge (₹)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={urgentDeliveryCharge}
                onChange={(e) => setUrgentDeliveryCharge(e.target.value)}
                placeholder="e.g. 99"
                className="w-48 rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>
            <button
              onClick={handleSaveUrgentCharge}
              disabled={savingUrgent}
              className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
            >
              {savingUrgent ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>

        {/* ── Main Grid ────────────────────────────────── */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Left panel — Date / Segment / Pincodes */}
          <div className="lg:col-span-4">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-slate-800">Select Options</h2>

              <div className="space-y-5">
                {/* Date */}
                                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">Select Date(s)</label>
                    <div className="flex flex-wrap gap-2">
                      {next7Days.map((date) => {
                        const isSelected = selectedDates.includes(date);
                        return (
                          <button
                            key={date}
                            onClick={() => {
                              if (isSelected) {
                                if (selectedDates.length > 1) {
                                  setSelectedDates(selectedDates.filter(d => d !== date));
                                } else {
                                  toast.error('At least one date must be selected');
                                }
                              } else {
                                setSelectedDates([...selectedDates, date].sort());
                              }
                            }}
                            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors border ${
                              isSelected 
                                ? 'bg-indigo-600 text-white border-transparent' 
                                : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                            }`}
                          >
                            {format(new Date(date), 'MMM d, yyyy')}
                          </button>
                        );
                      })}
                    </div>
                    {selectedDates.length > 1 && (
                      <p className="mt-2 text-xs text-amber-600 font-medium">
                        You are editing multiple dates at once. Saving will overwrite the slots configuration for all selected dates.
                      </p>
                    )}
                  </div>

                {/* Segment */}
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Customer Segment
                  </label>
                  <p className="mb-2 text-xs text-slate-500">
                    Delivery timings for retail and business customers are managed separately.
                  </p>
                  <div className="flex rounded-md shadow-sm">
                    <button
                      onClick={() => setSegment('retail')}
                      className={`flex-1 rounded-l-md border px-4 py-2 text-sm font-medium ${
                        segment === 'retail'
                          ? 'z-10 border-indigo-500 bg-indigo-50 text-indigo-700'
                          : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      Retail Customer
                    </button>
                    <button
                      onClick={() => setSegment('wholesale')}
                      className={`-ml-px flex-1 rounded-r-md border px-4 py-2 text-sm font-medium ${
                        segment === 'wholesale'
                          ? 'z-10 border-indigo-500 bg-indigo-50 text-indigo-700'
                          : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      Business Customer
                    </button>
                  </div>
                </div>

                {/* Zone picker */}
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Apply to Zones
                  </label>
                  <p className="mb-2 text-xs text-slate-500">
                    Select which zones these slots apply to. Choose <strong>Default</strong> to create a fallback for zones with no specific config that day.
                  </p>

                  {loadingZones ? (
                    <p className="text-sm text-slate-400">Loading zones…</p>
                  ) : (
                    <div className="space-y-1.5 rounded border border-slate-200 bg-white p-2 max-h-52 overflow-y-auto">
                      {/* Default option */}
                      <label className="flex cursor-pointer items-center gap-2 rounded p-1.5 text-sm hover:bg-slate-50">
                        <input
                          type="checkbox"
                          checked={selectedZoneIds.includes('default')}
                          onChange={() => {
                            setSelectedZoneIds(prev =>
                              prev.includes('default') ? prev.filter(id => id !== 'default') : [...prev, 'default']
                            );
                          }}
                          className="h-4 w-4 rounded text-indigo-600"
                        />
                        <span className="font-medium text-slate-700">Default</span>
                        <span className="ml-auto text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">Fallback</span>
                      </label>

                      {/* Real zones */}
                      {zones.map((zone: any) => {
                        const id = zone._id || zone.id;
                        const isSelected = selectedZoneIds.includes(id);
                        return (
                          <label
                            key={id}
                            className="flex cursor-pointer items-center gap-2 rounded p-1.5 text-sm hover:bg-slate-50"
                          >
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => {
                                setSelectedZoneIds(prev =>
                                  prev.includes(id) ? prev.filter(z => z !== id) : [...prev, id]
                                );
                              }}
                              className="h-4 w-4 rounded text-indigo-600"
                            />
                            <span className="text-slate-700">{zone.name}</span>
                            <span className="ml-auto text-[10px] text-slate-400">Cap: {zone.defaultCapacity ?? 10}</span>
                          </label>
                        );
                      })}

                      {zones.length === 0 && (
                        <p className="py-2 text-center text-xs text-slate-400">
                          No zones found. Create zones in Delivery Zones first.
                        </p>
                      )}
                    </div>
                  )}

                  {selectedZoneIds.length > 0 && (
                    <p className="mt-1 text-xs font-medium text-indigo-600">
                      {selectedZoneIds.length} zone(s) selected · default capacity: {primaryZoneCapacity}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right panel — Time Slots */}
          <div className="lg:col-span-8">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-800">
                  Time Slots — {selectedDates.length > 1 ? 'Multiple Dates' : primaryDate} ({segment})
                </h2>
                <button
                  onClick={addSlot}
                  className="flex items-center gap-1 rounded-lg border border-indigo-600 px-3 py-1.5 text-sm font-medium text-indigo-600 transition-colors hover:bg-indigo-50"
                >
                  + Add Slot
                </button>
              </div>

              {loading ? (
                <div className="py-8 text-center text-slate-500">Loading slots…</div>
              ) : slots.length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center">
                  <p className="text-slate-500">
                    No time slots configured for this date and segment.
                  </p>
                  <button
                    onClick={addSlot}
                    className="mt-2 text-sm font-medium text-indigo-600 hover:text-indigo-500"
                  >
                    Add your first slot
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {slots.map((slot) => {
                    const remaining =
                      slot.capacity > 0 ? slot.capacity - (slot.bookedCount || 0) : null;
                    return (
                      <div
                        key={slot.id}
                        className={`relative flex flex-wrap items-end gap-4 rounded-lg border p-4 ${
                          slot.isUrgent
                            ? 'border-amber-300 bg-amber-50'
                            : 'border-slate-200 bg-slate-50'
                        }`}
                      >
                        {/* Start Time */}
                        <div className="min-w-[120px] flex-1">
                          <label className="mb-1 block text-xs font-medium text-slate-500">
                            Start Time
                          </label>
                          <input
                            type="time"
                            value={slot.startTime}
                            onChange={(e) => updateSlot(slot.id, 'startTime', e.target.value)}
                            className="block w-full rounded-md border border-slate-300 p-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          />
                        </div>

                        {/* End Time */}
                        <div className="min-w-[120px] flex-1">
                          <label className="mb-1 block text-xs font-medium text-slate-500">
                            End Time
                          </label>
                          <input
                            type="time"
                            value={slot.endTime}
                            onChange={(e) => updateSlot(slot.id, 'endTime', e.target.value)}
                            className="block w-full rounded-md border border-slate-300 p-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          />
                        </div>

                        {/* Capacity */}
                        <div className="w-28">
                          <label className="mb-1 block text-xs font-medium text-slate-500">
                            Max Bookings
                          </label>
                          <input
                            type="number"
                            min="0"
                            value={slot.capacity}
                            onChange={(e) =>
                              updateSlot(slot.id, 'capacity', parseInt(e.target.value) || 0)
                            }
                            className="block w-full rounded-md border border-slate-300 p-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          />
                          {slot.capacity > 0 && (
                            <p className="mt-0.5 text-xs text-slate-400">
                              {slot.bookedCount || 0} booked
                              {remaining !== null && (
                                <span
                                  className={`ml-1 font-medium ${
                                    remaining === 0 ? 'text-red-500' : 'text-green-600'
                                  }`}
                                >
                                  · {remaining} left
                                </span>
                              )}
                            </p>
                          )}
                        </div>

                        {/* Cutoff Hours */}
                        <div className="w-28">
                          <label className="mb-1 block text-xs font-medium text-slate-500">
                            Cutoff (hrs)
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="48"
                            placeholder="—"
                            value={slot.cutoffHours ?? ''}
                            onChange={(e) =>
                              updateSlot(
                                slot.id,
                                'cutoffHours',
                                e.target.value === '' ? null : parseInt(e.target.value) || 0
                              )
                            }
                            className="block w-full rounded-md border border-slate-300 p-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          />
                          <p className="mt-0.5 text-[10px] leading-tight text-slate-400">
                            {slot.cutoffHours
                              ? `Closes ${slot.cutoffHours}h before start`
                              : 'No cutoff'}
                          </p>
                        </div>

                        {/* Urgent Cutoff Hours — shown only when slot is Urgent */}
                        {slot.isUrgent && (
                          <div className="w-32">
                            <label className="mb-1 block text-xs font-medium text-amber-700">
                              ⚡ Urgent Cutoff (hrs)
                            </label>
                            <input
                              type="number"
                              min="0"
                              max="48"
                              placeholder="—"
                              value={slot.urgentCutoffHours ?? ''}
                              onChange={(e) =>
                                updateSlot(
                                  slot.id,
                                  'urgentCutoffHours',
                                  e.target.value === '' ? null : parseInt(e.target.value) || 0
                                )
                              }
                              className="block w-full rounded-md border border-amber-300 bg-amber-50 p-2 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm"
                            />
                            <p className="mt-0.5 text-[10px] leading-tight text-amber-600">
                              {slot.urgentCutoffHours
                                ? `Closes ${slot.urgentCutoffHours}h before start`
                                : slot.cutoffHours
                                  ? `Fallback: ${slot.cutoffHours}h`
                                  : 'No cutoff'}
                            </p>
                          </div>
                        )}

                        {/* Urgent toggle */}
                        <div className="flex flex-col items-center gap-1">
                          <label className="text-xs font-medium text-slate-500">⚡ Urgent</label>
                          <label className="inline-flex cursor-pointer items-center">
                            <input
                              type="checkbox"
                              checked={slot.isUrgent}
                              onChange={(e) => updateSlot(slot.id, 'isUrgent', e.target.checked)}
                              className="sr-only peer"
                            />
                            <div className="relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-amber-500 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none rtl:peer-checked:after:-translate-x-full" />
                          </label>
                        </div>

                        {/* Active toggle */}
                        <div className="flex flex-col items-center gap-1">
                          <label className="text-xs font-medium text-slate-500">Active</label>
                          <label className="inline-flex cursor-pointer items-center">
                            <input
                              type="checkbox"
                              checked={slot.isActive}
                              onChange={(e) => updateSlot(slot.id, 'isActive', e.target.checked)}
                              className="sr-only peer"
                            />
                            <div className="relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-indigo-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none rtl:peer-checked:after:-translate-x-full" />
                          </label>
                        </div>

                        {/* Urgent badge */}
                        {slot.isUrgent && (
                          <span className="absolute right-10 top-2 rounded-full bg-amber-500 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                            ⚡ Urgent
                          </span>
                        )}

                        {/* Remove button */}
                        <button
                          onClick={() => removeSlot(slot.id)}
                          className="absolute right-2 top-2 text-slate-400 hover:text-red-500"
                          title="Remove slot"
                        >
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
