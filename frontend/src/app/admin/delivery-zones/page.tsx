'use client';

import { useState, useEffect, useCallback } from 'react';
import AdminLayout from '@/components/Admin/AdminLayout';
import { toast } from 'react-hot-toast';
import api from '@/utils/api';

// ── Types ──────────────────────────────────────────────────────────────────────

interface Zone {
  _id: string;
  name: string;
  description?: string;
  pincodes: string[];
  defaultCapacity: number;
  urgentDeliveryAvailable: boolean;
  isActive: boolean;
  createdAt?: string;
}

interface ZoneFormData {
  name: string;
  description: string;
  pincodes: string[];
  defaultCapacity: number;
  urgentDeliveryAvailable: boolean;
  isActive: boolean;
}

const EMPTY_FORM: ZoneFormData = {
  name: '',
  description: '',
  pincodes: [],
  defaultCapacity: 10,
  urgentDeliveryAvailable: false,
  isActive: true,
};

// ── Component ──────────────────────────────────────────────────────────────────

export default function DeliveryZonesPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingZone, setEditingZone] = useState<Zone | null>(null);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Serviceable pincodes list (from delivery charges)
  const [serviceablePincodes, setServiceablePincodes] = useState<string[]>([]);
  const [loadingPincodes, setLoadingPincodes] = useState(false);
  const [pincodeSearch, setPincodeSearch] = useState('');

  const [form, setForm] = useState<ZoneFormData>(EMPTY_FORM);

  // ── Fetch ────────────────────────────────────────────────────────────────────

  const fetchZones = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/delivery-zones');
      setZones(res.data || []);
    } catch {
      toast.error('Failed to load delivery zones');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchServiceablePincodes = useCallback(async () => {
    setLoadingPincodes(true);
    try {
      const res = await api.get('/delivery-charges/serviceable-pincodes');
      setServiceablePincodes(res.data || []);
    } catch {
      toast.error('Could not load serviceable pincodes');
    } finally {
      setLoadingPincodes(false);
    }
  }, []);

  useEffect(() => {
    fetchZones();
    fetchServiceablePincodes();
  }, [fetchZones, fetchServiceablePincodes]);

  // ── Build set of pincodes already claimed by OTHER zones ─────────────────────

  const claimedPincodes = new Set<string>(
    zones
      .filter((z) => !editingZone || z._id !== editingZone._id)
      .flatMap((z) => z.pincodes || [])
  );

  // ── Modal helpers ────────────────────────────────────────────────────────────

  const openCreate = () => {
    setEditingZone(null);
    setForm(EMPTY_FORM);
    setPincodeSearch('');
    setShowModal(true);
  };

  const openEdit = (zone: Zone) => {
    setEditingZone(zone);
    setForm({
      name: zone.name,
      description: zone.description || '',
      pincodes: zone.pincodes || [],
      defaultCapacity: zone.defaultCapacity ?? 10,
      urgentDeliveryAvailable: zone.urgentDeliveryAvailable ?? false,
      isActive: zone.isActive !== false,
    });
    setPincodeSearch('');
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingZone(null);
    setForm(EMPTY_FORM);
  };

  // ── Save ─────────────────────────────────────────────────────────────────────

  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.error('Zone name is required');
      return;
    }
    if (form.defaultCapacity < 1) {
      toast.error('Default capacity must be at least 1');
      return;
    }

    setSaving(true);
    try {
      if (editingZone) {
        await api.put(`/delivery-zones/${editingZone._id}`, form);
        toast.success('Zone updated');
      } else {
        await api.post('/delivery-zones', form);
        toast.success('Zone created');
      }
      closeModal();
      fetchZones();
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Failed to save zone';
      toast.error(detail);
    } finally {
      setSaving(false);
    }
  };

  // ── Delete ───────────────────────────────────────────────────────────────────

  const handleDelete = async (zone: Zone) => {
    if (!confirm(`Delete zone "${zone.name}"? This cannot be undone.`)) return;
    setDeletingId(zone._id);
    try {
      await api.delete(`/delivery-zones/${zone._id}`);
      toast.success('Zone deleted');
      fetchZones();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to delete zone');
    } finally {
      setDeletingId(null);
    }
  };

  // ── Pincode toggle ───────────────────────────────────────────────────────────

  const togglePincode = (pc: string) => {
    setForm((prev) => ({
      ...prev,
      pincodes: prev.pincodes.includes(pc)
        ? prev.pincodes.filter((p) => p !== pc)
        : [...prev.pincodes, pc],
    }));
  };

  const filteredPincodes = serviceablePincodes.filter((pc) =>
    pc.includes(pincodeSearch.trim())
  );

  const allFilteredSelected =
    filteredPincodes.length > 0 &&
    filteredPincodes.every((pc) => form.pincodes.includes(pc));

  const toggleAllFiltered = () => {
    if (allFilteredSelected) {
      setForm((prev) => ({
        ...prev,
        pincodes: prev.pincodes.filter((p) => !filteredPincodes.includes(p)),
      }));
    } else {
      setForm((prev) => ({
        ...prev,
        pincodes: Array.from(new Set([...prev.pincodes, ...filteredPincodes.filter((pc) => !claimedPincodes.has(pc))])),
      }));
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <AdminLayout>
      <div className="flex h-full flex-col gap-6">
        {/* Header */}
        <header className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Delivery Zones</h1>
            <p className="mt-1 text-sm text-slate-500">
              Group pincodes into zones. Slot capacity is set per zone. Pincodes can belong
              to only one zone at a time.
            </p>
          </div>
          <button
            onClick={openCreate}
            className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white shadow-sm transition-colors hover:bg-indigo-700"
          >
            + Create Zone
          </button>
        </header>

        {/* Zone List */}
        {loading ? (
          <div className="py-12 text-center text-slate-400">Loading zones…</div>
        ) : zones.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 py-16 text-center">
            <p className="text-slate-500">No zones yet. Create your first zone to get started.</p>
            <button
              onClick={openCreate}
              className="mt-3 text-sm font-medium text-indigo-600 hover:text-indigo-500"
            >
              Create Zone →
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {zones.map((zone) => (
              <div
                key={zone._id}
                className={`rounded-xl border bg-white p-5 shadow-sm transition-opacity ${
                  !zone.isActive ? 'opacity-60' : ''
                }`}
              >
                {/* Zone header */}
                <div className="mb-3 flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-slate-800">{zone.name}</h3>
                    {zone.description && (
                      <p className="mt-0.5 text-xs text-slate-500">{zone.description}</p>
                    )}
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <button
                      onClick={() => openEdit(zone)}
                      className="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(zone)}
                      disabled={deletingId === zone._id}
                      className="rounded px-2 py-1 text-xs font-medium text-red-500 hover:bg-red-50 disabled:opacity-40"
                    >
                      {deletingId === zone._id ? '…' : 'Delete'}
                    </button>
                  </div>
                </div>

                {/* Stats row */}
                <div className="flex flex-wrap gap-3 text-sm">
                  <span className="flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-slate-600">
                    📍 {(zone.pincodes || []).length} pincodes
                  </span>
                  <span className="flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-0.5 text-indigo-700">
                    🪣 Default cap: {zone.defaultCapacity ?? 10}
                  </span>
                  {zone.urgentDeliveryAvailable && (
                    <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-amber-700">
                      ⚡ Urgent
                    </span>
                  )}
                  {!zone.isActive && (
                    <span className="rounded-full bg-slate-200 px-2.5 py-0.5 text-slate-500">
                      Inactive
                    </span>
                  )}
                </div>

                {/* Pincode chips (collapsed) */}
                {zone.pincodes && zone.pincodes.length > 0 && (
                  <details className="mt-3">
                    <summary className="cursor-pointer text-xs text-slate-400 hover:text-slate-600">
                      Show pincodes
                    </summary>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {zone.pincodes.map((pc) => (
                        <span
                          key={pc}
                          className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-600"
                        >
                          {pc}
                        </span>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Create / Edit Modal ──────────────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-2xl">
            {/* Modal header */}
            <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-6 py-4">
              <h2 className="text-lg font-semibold text-slate-800">
                {editingZone ? 'Edit Zone' : 'Create Zone'}
              </h2>
              <button
                onClick={closeModal}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-5 px-6 py-5">
              {/* Name */}
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Zone Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. North Zone, City Centre"
                  value={form.name}
                  onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              {/* Description */}
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Description (optional)
                </label>
                <input
                  type="text"
                  placeholder="Brief description of the zone coverage"
                  value={form.description}
                  onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              {/* Default Capacity */}
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Default Capacity per Slot
                </label>
                <p className="mb-2 text-xs text-slate-500">
                  This number is pre-filled when creating delivery slots for this zone.
                  It can be overridden per day in the Delivery Slots page.
                </p>
                <input
                  type="number"
                  min="1"
                  value={form.defaultCapacity}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, defaultCapacity: parseInt(e.target.value) || 1 }))
                  }
                  className="w-32 rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              {/* Toggles */}
              <div className="flex flex-wrap gap-6">
                {/* Urgent Delivery */}
                <label className="flex cursor-pointer items-center gap-3">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={form.urgentDeliveryAvailable}
                      onChange={(e) =>
                        setForm((p) => ({ ...p, urgentDeliveryAvailable: e.target.checked }))
                      }
                      className="sr-only peer"
                    />
                    <div className="h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-amber-500 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none rtl:peer-checked:after:-translate-x-full" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">⚡ Urgent Delivery</p>
                    <p className="text-xs text-slate-400">Customers in this zone can book urgent slots</p>
                  </div>
                </label>

                {/* Active */}
                <label className="flex cursor-pointer items-center gap-3">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={form.isActive}
                      onChange={(e) =>
                        setForm((p) => ({ ...p, isActive: e.target.checked }))
                      }
                      className="sr-only peer"
                    />
                    <div className="h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-indigo-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none rtl:peer-checked:after:-translate-x-full" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Active</p>
                    <p className="text-xs text-slate-400">Inactive zones are excluded from checkout</p>
                  </div>
                </label>
              </div>

              {/* Pincode Picker */}
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Pincodes
                </label>
                <p className="mb-2 text-xs text-slate-500">
                  Only serviceable pincodes are shown. Greyed-out pincodes belong to another zone.
                </p>

                {loadingPincodes ? (
                  <p className="text-sm text-slate-400">Loading pincodes…</p>
                ) : serviceablePincodes.length === 0 ? (
                  <p className="rounded-lg border border-dashed border-slate-300 p-3 text-center text-sm text-slate-400">
                    No serviceable pincodes found. Add pincodes in Delivery Charges first.
                  </p>
                ) : (
                  <>
                    <div className="mb-2 flex gap-2">
                      <input
                        type="text"
                        placeholder="Search pincodes…"
                        value={pincodeSearch}
                        onChange={(e) => setPincodeSearch(e.target.value)}
                        className="flex-1 rounded border border-slate-300 px-2 py-1 text-sm"
                      />
                      <button
                        type="button"
                        onClick={toggleAllFiltered}
                        className="whitespace-nowrap rounded px-3 py-1 text-xs font-medium text-white"
                        style={{
                          background: allFilteredSelected
                            ? 'linear-gradient(135deg,#DC3545 0%,#C82333 100%)'
                            : 'linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
                        }}
                      >
                        {allFilteredSelected ? 'Deselect All' : 'Select Available'}
                      </button>
                    </div>

                    <div className="grid max-h-52 grid-cols-2 gap-1 overflow-y-auto rounded border border-slate-200 bg-white p-2">
                      {filteredPincodes.map((pc) => {
                        const isClaimed = claimedPincodes.has(pc);
                        const isSelected = form.pincodes.includes(pc);
                        return (
                          <label
                            key={pc}
                            className={`flex cursor-pointer items-center gap-1.5 rounded p-1 text-sm ${
                              isClaimed
                                ? 'cursor-not-allowed opacity-40'
                                : 'hover:bg-slate-50'
                            }`}
                            title={isClaimed ? 'Already assigned to another zone' : undefined}
                          >
                            <input
                              type="checkbox"
                              checked={isSelected}
                              disabled={isClaimed}
                              onChange={() => !isClaimed && togglePincode(pc)}
                              className="h-4 w-4 rounded text-indigo-600"
                            />
                            <span>{pc}</span>
                          </label>
                        );
                      })}
                      {filteredPincodes.length === 0 && (
                        <p className="col-span-2 py-2 text-center text-xs text-slate-400">
                          No pincodes match
                        </p>
                      )}
                    </div>

                    {form.pincodes.length > 0 && (
                      <p className="mt-1 text-xs font-medium text-indigo-600">
                        {form.pincodes.length} pincode(s) selected
                      </p>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Modal footer */}
            <div className="sticky bottom-0 flex justify-end gap-3 border-t bg-white px-6 py-4">
              <button
                onClick={closeModal}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {saving ? 'Saving…' : editingZone ? 'Save Changes' : 'Create Zone'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
