'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { formatDateIST } from '@/utils/dateUtils';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

// ─── Types ────────────────────────────────────────────────────────────────────

interface PayoutSettings {
  deliveryChargePerOrder: number;
  returnPickupChargePerOrder: number;
  updatedAt?: string;
}

interface Valet {
  _id: string;
  userId?: number;
  userIdFormatted?: string;
  name: string;
  email: string;
  phone?: string;
  isActive: boolean;
}

interface Order {
  _id: string;
  orderNumber?: string;
  status?: string;
  total?: number;
  createdAt?: string;
  deliveredAt?: string;
}

// Note: return pickups are tracked via the returns collection.
// For now we count delivered orders as deliveries.
interface ValetPayout {
  valet: Valet;
  deliveredOrders: Order[];
  deliveredCount: number;
  payoutAmount: number;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function ValetPayoutPage() {
  const { user } = useAuth();

  // Settings
  const [settings, setSettings] = useState<PayoutSettings>({
    deliveryChargePerOrder: 0,
    returnPickupChargePerOrder: 0,
  });
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [editingSettings, setEditingSettings] = useState(false);
  const [draftDelivery, setDraftDelivery] = useState('0');
  const [draftReturn, setDraftReturn] = useState('0');
  const [savingSettings, setSavingSettings] = useState(false);

  // Payout table
  const [payouts, setPayouts] = useState<ValetPayout[]>([]);
  const [payoutsLoading, setPayoutsLoading] = useState(true);

  // Date filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Search
  const [searchTerm, setSearchTerm] = useState('');

  // Detail modal
  const [detailValet, setDetailValet] = useState<ValetPayout | null>(null);

  // ── Fetch settings ──
  const fetchSettings = useCallback(async () => {
    setSettingsLoading(true);
    try {
      const res = await api.get('/valet-payout/settings');
      setSettings(res.data);
      setDraftDelivery(String(res.data.deliveryChargePerOrder ?? 0));
      setDraftReturn(String(res.data.returnPickupChargePerOrder ?? 0));
    } catch {
      toast.error('Failed to load payout settings');
    } finally {
      setSettingsLoading(false);
    }
  }, []);

  // ── Fetch valets + their delivered orders ──
  const fetchPayouts = useCallback(async () => {
    setPayoutsLoading(true);
    try {
      const valetsRes = await api.get('/users', { params: { role: 'valet' } });
      const valets: Valet[] = valetsRes.data || [];

      const results = await Promise.all(
        valets.map(async (v) => {
          try {
            const params: Record<string, any> = {
              assignedValet: v._id,
              status: 'delivered',
            };
            if (startDate) params.startDate = startDate;
            if (endDate) params.endDate = endDate;
            const ordersRes = await api.get('/orders', { params });
            const delivered: Order[] = Array.isArray(ordersRes.data)
              ? ordersRes.data
              : ordersRes.data?.orders ?? [];
            return {
              valet: v,
              deliveredOrders: delivered,
              deliveredCount: delivered.length,
              payoutAmount: 0, // will be recalculated when settings are loaded
            } as ValetPayout;
          } catch {
            return { valet: v, deliveredOrders: [], deliveredCount: 0, payoutAmount: 0 };
          }
        })
      );
      setPayouts(results);
    } catch {
      toast.error('Failed to load valet data');
    } finally {
      setPayoutsLoading(false);
    }
  }, [startDate, endDate]);

  // ── Recalculate payout amounts whenever settings or data changes ──
  const payoutsWithAmount = useMemo<ValetPayout[]>(() => {
    const rate = settings.deliveryChargePerOrder ?? 0;
    return payouts.map((p) => ({
      ...p,
      payoutAmount: p.deliveredCount * rate,
    }));
  }, [payouts, settings]);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchSettings();
      fetchPayouts();
    }
  }, [user, fetchSettings, fetchPayouts]);

  // ── Save settings ──
  const saveSettings = async () => {
    const delivery = parseFloat(draftDelivery);
    const ret = parseFloat(draftReturn);
    if (isNaN(delivery) || delivery < 0 || isNaN(ret) || ret < 0) {
      toast.error('Please enter valid positive amounts');
      return;
    }
    setSavingSettings(true);
    try {
      const res = await api.put('/valet-payout/settings', {
        deliveryChargePerOrder: delivery,
        returnPickupChargePerOrder: ret,
      });
      setSettings(res.data);
      setEditingSettings(false);
      toast.success('Payout settings saved');
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setSavingSettings(false);
    }
  };

  // ── Filtered list ──
  const filtered = useMemo(() => {
    const q = searchTerm.toLowerCase();
    return payoutsWithAmount.filter(
      (p) =>
        !q ||
        p.valet.name?.toLowerCase().includes(q) ||
        p.valet.email?.toLowerCase().includes(q) ||
        p.valet.phone?.includes(q)
    );
  }, [payoutsWithAmount, searchTerm]);

  // ── Stats ──
  const totalPayout = filtered.reduce((s, p) => s + p.payoutAmount, 0);
  const totalDeliveries = filtered.reduce((s, p) => s + p.deliveredCount, 0);

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;

  return (
    <div className="h-full overflow-y-auto">
      <div className="space-y-6 p-6">

        {/* Header */}
        <div className="flex items-center gap-3">
          <svg className="w-8 h-8 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h1 className="text-3xl font-bold text-gray-900">Valet Payout</h1>
          <RefreshButton onRefresh={() => { fetchSettings(); fetchPayouts(); }} />
        </div>

        {/* ════════════════════════════════════════
            GLOBAL CHARGE SETTINGS
        ════════════════════════════════════════ */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Global Charge Settings</h2>
              <p className="text-sm text-gray-500 mt-0.5">
                Fixed amounts paid to each valet per completed delivery or return pickup.
                {settings.updatedAt && (
                  <span className="ml-2 text-xs text-gray-400">Last updated: {formatDateIST(settings.updatedAt)}</span>
                )}
              </p>
            </div>
            {!editingSettings && !settingsLoading && (
              <button
                onClick={() => setEditingSettings(true)}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
              >
                Edit Charges
              </button>
            )}
          </div>

          {settingsLoading ? (
            <div className="text-sm text-gray-400">Loading settings…</div>
          ) : editingSettings ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Per Delivery (₹)
                  </label>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">₹</span>
                    <input
                      type="number"
                      min={0}
                      step={0.5}
                      value={draftDelivery}
                      onChange={(e) => setDraftDelivery(e.target.value)}
                      className="w-36 rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                      placeholder="e.g. 50"
                    />
                    <span className="text-xs text-gray-400">per delivered order</span>
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Per Return Pickup (₹)
                  </label>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">₹</span>
                    <input
                      type="number"
                      min={0}
                      step={0.5}
                      value={draftReturn}
                      onChange={(e) => setDraftReturn(e.target.value)}
                      className="w-36 rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                      placeholder="e.g. 30"
                    />
                    <span className="text-xs text-gray-400">per return pickup</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={saveSettings}
                  disabled={savingSettings}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
                >
                  {savingSettings ? 'Saving…' : 'Save Settings'}
                </button>
                <button
                  onClick={() => {
                    setEditingSettings(false);
                    setDraftDelivery(String(settings.deliveryChargePerOrder));
                    setDraftReturn(String(settings.returnPickupChargePerOrder));
                  }}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex items-center gap-3 rounded-lg border border-indigo-100 bg-indigo-50 p-4">
                <svg className="w-8 h-8 text-indigo-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
                </svg>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-indigo-500">Per Delivery</p>
                  <p className="text-2xl font-bold text-indigo-800">₹{settings.deliveryChargePerOrder.toFixed(2)}</p>
                  <p className="text-xs text-indigo-400">per delivered order</p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-orange-100 bg-orange-50 p-4">
                <svg className="w-8 h-8 text-orange-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                </svg>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-orange-500">Per Return Pickup</p>
                  <p className="text-2xl font-bold text-orange-800">₹{settings.returnPickupChargePerOrder.toFixed(2)}</p>
                  <p className="text-xs text-orange-400">per return collected</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ════════════════════════════════════════
            PAYOUT SUMMARY STATS
        ════════════════════════════════════════ */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-green-100 bg-green-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-green-600">Total Payout Due</p>
            <p className="mt-1 text-2xl font-bold text-green-700">
              ₹{payoutsLoading ? '…' : totalPayout.toFixed(2)}
            </p>
          </div>
          <div className="rounded-lg border border-blue-100 bg-blue-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-blue-600">Total Deliveries</p>
            <p className="mt-1 text-2xl font-bold text-blue-700">
              {payoutsLoading ? '…' : totalDeliveries}
            </p>
          </div>
          <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Active Valets</p>
            <p className="mt-1 text-2xl font-bold text-gray-700">
              {payoutsLoading ? '…' : filtered.filter((p) => p.valet.isActive).length}
            </p>
          </div>
        </div>

        {/* ════════════════════════════════════════
            DATE FILTER + SEARCH + PAYOUT TABLE
        ════════════════════════════════════════ */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Per-Valet Payout Breakdown</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Calculated as: Deliveries × ₹{settings.deliveryChargePerOrder.toFixed(2)} per delivery.
            </p>
          </div>

          {/* Filters bar */}
          <div className="flex flex-wrap items-center gap-3 bg-gray-50 border-b border-gray-100 px-6 py-3">
            <input
              type="text"
              placeholder="Search valet…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500">From</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500">To</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            {(startDate || endDate) && (
              <button
                onClick={() => { setStartDate(''); setEndDate(''); }}
                className="rounded border border-gray-200 px-3 py-1.5 text-xs text-gray-600 hover:bg-white"
              >
                Clear dates
              </button>
            )}
          </div>

          {/* Table */}
          {payoutsLoading ? (
            <div className="flex h-32 items-center justify-center text-gray-500 text-sm">
              Loading payout data…
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-gray-400 text-sm">
              No valets found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {['Valet', 'Email', 'Phone', 'Deliveries', 'Rate', 'Payout Due', 'Status', 'Actions'].map((h) => (
                      <th key={h} className="border border-gray-200 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((p) => (
                    <tr key={p.valet._id} className="hover:bg-indigo-50/20">
                      <td className="border border-gray-200 px-4 py-3">
                        <div className="font-medium text-gray-900">{p.valet.name}</div>
                        <div className="text-xs text-gray-400">
                          {p.valet.userIdFormatted || (p.valet.userId ? `USER-${p.valet.userId}` : '')}
                        </div>
                      </td>
                      <td className="border border-gray-200 px-4 py-3 text-gray-700">{p.valet.email}</td>
                      <td className="border border-gray-200 px-4 py-3 text-gray-700">{p.valet.phone || '-'}</td>
                      <td className="border border-gray-200 px-4 py-3 text-center">
                        <span className="inline-flex items-center justify-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
                          {p.deliveredCount}
                        </span>
                      </td>
                      <td className="border border-gray-200 px-4 py-3 text-gray-600 text-sm">
                        ₹{settings.deliveryChargePerOrder.toFixed(2)}/delivery
                      </td>
                      <td className="border border-gray-200 px-4 py-3 font-bold text-indigo-700 text-base">
                        ₹{p.payoutAmount.toFixed(2)}
                      </td>
                      <td className="border border-gray-200 px-4 py-3">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${p.valet.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {p.valet.isActive ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="border border-gray-200 px-4 py-3">
                        <button
                          onClick={() => setDetailValet(p)}
                          className="inline-flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-colors"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                          Orders
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                {/* Totals footer */}
                <tfoot className="bg-gray-50">
                  <tr>
                    <td colSpan={3} className="border border-gray-200 px-4 py-3 text-right text-sm font-semibold text-gray-600">
                      Totals ({filtered.length} valets)
                    </td>
                    <td className="border border-gray-200 px-4 py-3 text-center font-bold text-gray-800">
                      {totalDeliveries}
                    </td>
                    <td className="border border-gray-200 px-4 py-3" />
                    <td className="border border-gray-200 px-4 py-3 font-bold text-indigo-800 text-base">
                      ₹{totalPayout.toFixed(2)}
                    </td>
                    <td colSpan={2} className="border border-gray-200 px-4 py-3" />
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </div>

      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          DETAIL MODAL – Delivered orders for a valet
      ══════════════════════════════════════════════════════════════════════ */}
      {detailValet && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 p-4">
          <div className="flex w-full max-w-3xl flex-col rounded-xl bg-white shadow-2xl" style={{ maxHeight: '88vh' }}>
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 flex-shrink-0">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Delivered Orders — {detailValet.valet.name}</h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  {detailValet.deliveredCount} deliveries · Payout: <span className="font-semibold text-indigo-700">₹{detailValet.payoutAmount.toFixed(2)}</span>
                </p>
              </div>
              <button onClick={() => setDetailValet(null)} className="rounded p-1 text-gray-400 hover:bg-gray-100">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4 min-h-0">
              {detailValet.deliveredOrders.length === 0 ? (
                <div className="flex h-24 items-center justify-center text-sm text-gray-400">No delivered orders in this period.</div>
              ) : (
                <table className="w-full border-collapse text-sm">
                  <thead className="sticky top-0 bg-gray-50 z-10">
                    <tr>
                      {['#', 'Order No.', 'Delivered On', 'Order Total', 'Payout'].map((h) => (
                        <th key={h} className="border border-gray-200 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {detailValet.deliveredOrders.map((o, idx) => (
                      <tr key={o._id} className="hover:bg-gray-50">
                        <td className="border border-gray-200 px-3 py-2 text-xs text-gray-400">{idx + 1}</td>
                        <td className="border border-gray-200 px-3 py-2 font-mono text-xs text-gray-800">
                          {o.orderNumber || o._id.slice(-8).toUpperCase()}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 text-gray-600 whitespace-nowrap">
                          {o.deliveredAt ? formatDateIST(o.deliveredAt) : (o.createdAt ? formatDateIST(o.createdAt) : '-')}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 font-medium text-gray-900">
                          ₹{(o.total ?? 0).toFixed(2)}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 font-semibold text-indigo-700">
                          ₹{settings.deliveryChargePerOrder.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr>
                      <td colSpan={4} className="border border-gray-200 px-3 py-2 text-right text-sm font-semibold text-gray-700">
                        Total Payout
                      </td>
                      <td className="border border-gray-200 px-3 py-2 font-bold text-indigo-800">
                        ₹{detailValet.payoutAmount.toFixed(2)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              )}
            </div>

            <div className="flex justify-end border-t border-gray-200 px-6 py-3 flex-shrink-0">
              <button onClick={() => setDetailValet(null)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
