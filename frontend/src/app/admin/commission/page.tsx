'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { formatDateIST } from '@/utils/dateUtils';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

// ─── Types ────────────────────────────────────────────────────────────────────

interface SubOrder {
  _id: string;
  subOrderNumber?: string;
  parentOrderNumber?: string;
  sellerId?: string | null;
  sellerName?: string;
  total?: number;
  commissionPct?: number | null;
  commissionAmount?: number | null;
  commissionStatus?: 'unrealized' | 'realized' | null;
  status?: string;
  createdAt?: string;
  deliveredAt?: string;
}

interface SellerSummary {
  sellerId: string;
  sellerName: string;
  totalSubOrders: number;
  realizedAmount: number;
  unrealizedAmount: number;
  realizedCount: number;
  unrealizedCount: number;
  subOrders: SubOrder[];
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function CommissionPage() {
  const { user } = useAuth();

  // Global tiers state (kept here, seller overrides are in Sellers page)
  const [defaultPct, setDefaultPct] = useState<number>(5);
  const [tiersLoading, setTiersLoading] = useState(true);

  // Sub-orders / commission data
  const [subOrders, setSubOrders] = useState<SubOrder[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [_total, setTotal] = useState(0);
  const [_page, _setPage] = useState(1);
  const LIMIT = 500; // fetch a large batch for aggregation; date filter narrows this

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sellerFilter, _setSellerFilter] = useState('');

  // Detail modal
  const [detailSeller, setDetailSeller] = useState<SellerSummary | null>(null);
  const [detailStatusFilter, setDetailStatusFilter] = useState<'all' | 'realized' | 'unrealized'>('all');
  const [detailSearch, setDetailSearch] = useState('');

  // Preview calculator
  const [previewValue, setPreviewValue] = useState('');
  const [previewResult, setPreviewResult] = useState<{ commissionPct: number; commissionAmount: number } | null>(null);
  const [previewing, setPreviewing] = useState(false);

  // ── Fetch tiers (just for default % display) ──
  const fetchTiers = useCallback(async () => {
    setTiersLoading(true);
    try {
      const res = await api.get('/commission/tiers');
      setDefaultPct(res.data?.defaultCommissionPct ?? 5);
    } catch { /* silent */ }
    finally { setTiersLoading(false); }
  }, []);

  // ── Fetch sub-orders with optional date / seller filter ──
  const fetchSubOrders = useCallback(async () => {
    setOrdersLoading(true);
    try {
      const params: Record<string, any> = { page: 1, limit: LIMIT };
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;
      if (sellerFilter) params.sellerId = sellerFilter;

      const res = await api.get('/orders/admin/sub-orders', { params });
      const list: SubOrder[] = res.data?.subOrders ?? [];
      setSubOrders(list.filter((o) => o.sellerId)); // only seller sub-orders have commission
      setTotal(res.data?.totalCount ?? 0);
    } catch {
      toast.error('Failed to load commission data');
    } finally {
      setOrdersLoading(false);
    }
  }, [startDate, endDate, sellerFilter]);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchTiers();
      fetchSubOrders();
    }
  }, [user, fetchTiers, fetchSubOrders]);

  // ── Aggregate per-seller ──
  const sellerSummaries = useMemo<SellerSummary[]>(() => {
    const map = new Map<string, SellerSummary>();
    for (const so of subOrders) {
      if (!so.sellerId) continue;
      if (!map.has(so.sellerId)) {
        map.set(so.sellerId, {
          sellerId: so.sellerId,
          sellerName: so.sellerName || 'Unknown Seller',
          totalSubOrders: 0,
          realizedAmount: 0,
          unrealizedAmount: 0,
          realizedCount: 0,
          unrealizedCount: 0,
          subOrders: [],
        });
      }
      const entry = map.get(so.sellerId)!;
      entry.totalSubOrders += 1;
      entry.subOrders.push(so);
      if (so.commissionStatus === 'realized') {
        entry.realizedAmount += so.commissionAmount ?? 0;
        entry.realizedCount += 1;
      } else if (so.commissionStatus === 'unrealized') {
        entry.unrealizedAmount += so.commissionAmount ?? 0;
        entry.unrealizedCount += 1;
      }
    }
    return Array.from(map.values()).sort((a, b) =>
      (b.realizedAmount + b.unrealizedAmount) - (a.realizedAmount + a.unrealizedAmount)
    );
  }, [subOrders]);

  // ── Overall stats ──
  const totalRealized = sellerSummaries.reduce((s, v) => s + v.realizedAmount, 0);
  const totalUnrealized = sellerSummaries.reduce((s, v) => s + v.unrealizedAmount, 0);
  const realizedCount = sellerSummaries.reduce((s, v) => s + v.realizedCount, 0);
  const unrealizedCount = sellerSummaries.reduce((s, v) => s + v.unrealizedCount, 0);

  // ── Detail modal filtered orders ──
  const detailOrders = useMemo(() => {
    if (!detailSeller) return [];
    return detailSeller.subOrders.filter((so) => {
      const matchesStatus =
        detailStatusFilter === 'all' ||
        so.commissionStatus === detailStatusFilter;
      const q = detailSearch.toLowerCase();
      const matchesSearch =
        !q ||
        so.subOrderNumber?.toLowerCase().includes(q) ||
        so.parentOrderNumber?.toLowerCase().includes(q);
      return matchesStatus && matchesSearch;
    });
  }, [detailSeller, detailStatusFilter, detailSearch]);

  // ── Preview ──
  const handlePreview = async () => {
    if (!previewValue) return;
    setPreviewing(true);
    setPreviewResult(null);
    try {
      const res = await api.get('/commission/calculate', {
        params: { order_value: parseFloat(previewValue) },
      });
      setPreviewResult(res.data);
    } catch {
      toast.error('Failed to calculate');
    } finally {
      setPreviewing(false);
    }
  };

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;

  return (
    <div className="h-full overflow-y-auto">
      <div className="space-y-6 p-6">

        {/* Header */}
        <div className="flex items-center gap-3">
          <svg className="w-8 h-8 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
          </svg>
          <h1 className="text-3xl font-bold text-gray-900">Commission</h1>
          <RefreshButton onRefresh={() => { fetchTiers(); fetchSubOrders(); }} />
        </div>

        {/* ── Stats row ── */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-green-100 bg-green-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-green-600">Realized</p>
            <p className="mt-1 text-2xl font-bold text-green-700">₹{totalRealized.toFixed(2)}</p>
            <p className="text-xs text-green-500 mt-0.5">{realizedCount} sub-orders</p>
          </div>
          <div className="rounded-lg border border-yellow-100 bg-yellow-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-yellow-600">Unrealized</p>
            <p className="mt-1 text-2xl font-bold text-yellow-700">₹{totalUnrealized.toFixed(2)}</p>
            <p className="text-xs text-yellow-500 mt-0.5">{unrealizedCount} sub-orders</p>
          </div>
          <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-indigo-600">Total Commission</p>
            <p className="mt-1 text-2xl font-bold text-indigo-700">₹{(totalRealized + totalUnrealized).toFixed(2)}</p>
            <p className="text-xs text-indigo-500 mt-0.5">{realizedCount + unrealizedCount} sub-orders</p>
          </div>
          <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Default Rate</p>
            <p className="mt-1 text-2xl font-bold text-gray-700">{tiersLoading ? '…' : `${defaultPct}%`}</p>
            <p className="text-xs text-gray-400 mt-0.5">Overrides managed in Sellers</p>
          </div>
        </div>

        {/* ── Filters ── */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="mb-3 text-sm font-medium text-gray-700">Filter by Date Range</p>
          <div className="flex flex-wrap items-center gap-3">
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
                className="rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
              >
                Clear
              </button>
            )}
            <span className="text-xs text-gray-400">
              {ordersLoading ? 'Loading…' : `${subOrders.length} sub-orders loaded`}
            </span>
          </div>
        </div>

        {/* ── Per-Seller Commission Table ── */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Commission by Seller</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Click a row to view individual sub-orders. Seller-level overrides are managed in Users → Sellers.
            </p>
          </div>

          {ordersLoading ? (
            <div className="flex h-32 items-center justify-center text-gray-500 text-sm">
              Loading commission data…
            </div>
          ) : sellerSummaries.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-gray-400 text-sm">
              No commission data found for the selected period.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {['Seller', 'Sub-Orders', 'Realized', 'Unrealized', 'Total Commission', 'Details'].map((h) => (
                      <th key={h} className="border border-gray-200 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sellerSummaries.map((s) => (
                    <tr key={s.sellerId} className="hover:bg-indigo-50/30 cursor-pointer" onClick={() => { setDetailSeller(s); setDetailStatusFilter('all'); setDetailSearch(''); }}>
                      <td className="border border-gray-200 px-4 py-3">
                        <div className="font-medium text-gray-900">{s.sellerName}</div>
                        <div className="text-xs text-gray-400 font-mono">{s.sellerId.slice(-8)}</div>
                      </td>
                      <td className="border border-gray-200 px-4 py-3 text-center">
                        <span className="inline-flex items-center justify-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-semibold text-gray-700">
                          {s.totalSubOrders}
                        </span>
                      </td>
                      <td className="border border-gray-200 px-4 py-3">
                        <div className="font-semibold text-green-700">₹{s.realizedAmount.toFixed(2)}</div>
                        <div className="text-xs text-gray-400">{s.realizedCount} orders</div>
                      </td>
                      <td className="border border-gray-200 px-4 py-3">
                        <div className="font-semibold text-yellow-700">₹{s.unrealizedAmount.toFixed(2)}</div>
                        <div className="text-xs text-gray-400">{s.unrealizedCount} orders</div>
                      </td>
                      <td className="border border-gray-200 px-4 py-3 font-bold text-indigo-700">
                        ₹{(s.realizedAmount + s.unrealizedAmount).toFixed(2)}
                      </td>
                      <td className="border border-gray-200 px-4 py-3">
                        <button
                          onClick={(e) => { e.stopPropagation(); setDetailSeller(s); setDetailStatusFilter('all'); setDetailSearch(''); }}
                          className="inline-flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-colors"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ── Preview Calculator ── */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-1 text-lg font-semibold text-gray-900">Commission Preview Calculator</h2>
          <p className="mb-4 text-sm text-gray-500">Enter an order value to preview the applicable commission rate.</p>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1">
              <span className="text-sm text-gray-600">₹</span>
              <input
                type="number"
                min={0}
                placeholder="Order value"
                value={previewValue}
                onChange={(e) => { setPreviewValue(e.target.value); setPreviewResult(null); }}
                className="w-36 rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <button
              onClick={handlePreview}
              disabled={!previewValue || previewing}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
            >
              {previewing ? 'Calculating…' : 'Calculate'}
            </button>
          </div>
          {previewResult && (
            <div className="mt-4 inline-flex items-center gap-5 rounded-lg border border-indigo-100 bg-indigo-50 px-5 py-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-indigo-500">Rate</p>
                <p className="text-xl font-bold text-indigo-800">{previewResult.commissionPct}%</p>
              </div>
              <div className="h-8 w-px bg-indigo-200" />
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-indigo-500">Amount</p>
                <p className="text-xl font-bold text-indigo-800">₹{previewResult.commissionAmount.toFixed(2)}</p>
              </div>
            </div>
          )}
        </div>

      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          DETAIL MODAL – Sub-orders for a seller
      ══════════════════════════════════════════════════════════════════════ */}
      {detailSeller && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 p-4">
          <div className="flex w-full max-w-4xl flex-col rounded-xl bg-white shadow-2xl" style={{ maxHeight: '90vh' }}>
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 flex-shrink-0">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Commission — {detailSeller.sellerName}</h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  {detailSeller.totalSubOrders} sub-orders ·{' '}
                  Realized <span className="font-semibold text-green-700">₹{detailSeller.realizedAmount.toFixed(2)}</span> ·{' '}
                  Unrealized <span className="font-semibold text-yellow-700">₹{detailSeller.unrealizedAmount.toFixed(2)}</span>
                </p>
              </div>
              <button onClick={() => setDetailSeller(null)} className="rounded p-1 text-gray-400 hover:bg-gray-100">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-3 border-b border-gray-100 bg-gray-50 px-6 py-3 flex-shrink-0">
              <input
                type="text"
                placeholder="Search sub-order or parent order no."
                value={detailSearch}
                onChange={(e) => setDetailSearch(e.target.value)}
                className="rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <select
                value={detailStatusFilter}
                onChange={(e) => setDetailStatusFilter(e.target.value as any)}
                className="rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              >
                <option value="all">All</option>
                <option value="realized">Realized only</option>
                <option value="unrealized">Unrealized only</option>
              </select>
              <span className="text-xs text-gray-400">{detailOrders.length} shown</span>
            </div>

            {/* Table */}
            <div className="flex-1 overflow-y-auto px-6 pb-6 pt-4 min-h-0">
              {detailOrders.length === 0 ? (
                <div className="flex h-24 items-center justify-center text-sm text-gray-400">No matching sub-orders.</div>
              ) : (
                <table className="w-full border-collapse text-sm">
                  <thead className="sticky top-0 bg-gray-50 z-10">
                    <tr>
                      {['Sub-Order No.', 'Parent Order', 'Date', 'Order Total', 'Commission %', 'Commission ₹', 'Status'].map((h) => (
                        <th key={h} className="border border-gray-200 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {detailOrders.map((so) => (
                      <tr key={so._id} className="hover:bg-gray-50">
                        <td className="border border-gray-200 px-3 py-2 font-mono text-xs text-gray-800">{so.subOrderNumber || so._id.slice(-8)}</td>
                        <td className="border border-gray-200 px-3 py-2 font-mono text-xs text-gray-600">{so.parentOrderNumber || '-'}</td>
                        <td className="border border-gray-200 px-3 py-2 text-gray-600 whitespace-nowrap">
                          {so.createdAt ? formatDateIST(so.createdAt) : '-'}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 font-medium text-gray-900">
                          ₹{(so.total ?? 0).toFixed(2)}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 text-gray-700">
                          {so.commissionPct != null ? `${so.commissionPct}%` : '—'}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 font-semibold text-indigo-700">
                          {so.commissionAmount != null ? `₹${so.commissionAmount.toFixed(2)}` : '—'}
                        </td>
                        <td className="border border-gray-200 px-3 py-2">
                          {so.commissionStatus === 'realized' ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                              ✓ Realized
                            </span>
                          ) : so.commissionStatus === 'unrealized' ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
                              ⏳ Unrealized
                            </span>
                          ) : (
                            <span className="text-gray-400 text-xs">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="flex justify-end border-t border-gray-200 px-6 py-3 flex-shrink-0">
              <button onClick={() => setDetailSeller(null)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
