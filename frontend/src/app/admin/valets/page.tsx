'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { formatDateIST, formatDateTimeIST } from '@/utils/dateUtils';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Valet {
  _id: string;
  id?: string;
  userId?: number;
  userIdFormatted?: string;
  name: string;
  email: string;
  phone?: string;
  isActive: boolean;
  isDeactivated?: boolean;
  createdAt?: string;
  approvalStatus?: string;
  address?: { street?: string; city?: string; state?: string; zipCode?: string; country?: string };
  maxConcurrentOrders?: number;
}

interface ValetWithStats extends Valet {
  totalOrders: number;
  completedOrders: number;
  pendingOrders: number;
  ordersLoading: boolean;
}

interface Order {
  _id: string;
  orderNumber?: string;
  status?: string;
  total?: number;
  createdAt?: string;
  deliveredAt?: string;
  shippedAt?: string;
  user?: { name?: string; phone?: string };
  shippingAddress?: { street?: string; city?: string; state?: string };
  paymentMethod?: string;
  items?: { product?: { name?: string }; quantity?: number; price?: number }[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const PENDING_STATUSES = ['pending', 'processing', 'shipped', 'out_for_delivery', 'accepted'];
const COMPLETED_STATUSES = ['delivered'];

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  accepted: 'Accepted',
  processing: 'Processing',
  shipped: 'Shipped',
  out_for_delivery: 'Out for Delivery',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  declined: 'Declined',
  returned: 'Returned',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  accepted: 'bg-blue-100 text-blue-800',
  processing: 'bg-indigo-100 text-indigo-800',
  shipped: 'bg-purple-100 text-purple-800',
  out_for_delivery: 'bg-orange-100 text-orange-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
  declined: 'bg-red-100 text-red-800',
  returned: 'bg-gray-100 text-gray-800',
};

// ─── Component ────────────────────────────────────────────────────────────────

export default function ValetsManagement() {
  const { user } = useAuth();

  // Valets list state
  const [valets, setValets] = useState<ValetWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [sortColumn, setSortColumn] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Add-valet modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [allUsers, setAllUsers] = useState<any[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userSearch, setUserSearch] = useState('');
  const [promotingId, setPromotingId] = useState<string | null>(null);

  // Deactivate confirm modal
  const [confirmDeactivateId, setConfirmDeactivateId] = useState<string | null>(null);
  const [deactivating, setDeactivating] = useState(false);

  // Orders modal
  const [ordersModalValet, setOrdersModalValet] = useState<ValetWithStats | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [orderSearch, setOrderSearch] = useState('');
  const [orderStatusFilter, setOrderStatusFilter] = useState('all');
  const [orderStartDate, setOrderStartDate] = useState('');
  const [orderEndDate, setOrderEndDate] = useState('');

  // Global Valet Settings
  const [globalMaxOrders, setGlobalMaxOrders] = useState<number>(1);
  const [globalMaxLoading, setGlobalMaxLoading] = useState(true);

  // ── Sorting ──
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const renderSortIcon = (column: string) => {
    if (sortColumn !== column) return <span className="text-gray-300 ml-1 select-none">⇅</span>;
    return sortDirection === 'asc'
      ? <span className="text-indigo-600 ml-1 select-none">▲</span>
      : <span className="text-indigo-600 ml-1 select-none">▼</span>;
  };

  // ── Fetch orders for a single valet (for stats) ──
  const fetchValetOrders = useCallback(async (valetId: string): Promise<Order[]> => {
    try {
      const res = await api.get('/orders', { params: { assignedValet: valetId } });
      return Array.isArray(res.data) ? res.data : (res.data?.orders ?? []);
    } catch {
      return [];
    }
  }, []);

  // ── Fetch all valets + their order stats ──
  const fetchValets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/users', { params: { role: 'valet' } });
      const rawValets: Valet[] = res.data || [];

      // Initialise with loading indicators
      const withLoading: ValetWithStats[] = rawValets.map((v) => ({
        ...v,
        totalOrders: 0,
        completedOrders: 0,
        pendingOrders: 0,
        ordersLoading: true,
      }));
      setValets(withLoading);
      setLoading(false);

      // Fetch order stats concurrently (one request per valet)
      const statsResults = await Promise.all(
        rawValets.map(async (v) => {
          const valetOrders = await fetchValetOrders(v._id || v.id || '');
          return {
            id: v._id || v.id || '',
            totalOrders: valetOrders.length,
            completedOrders: valetOrders.filter((o) => COMPLETED_STATUSES.includes(o.status || '')).length,
            pendingOrders: valetOrders.filter((o) => PENDING_STATUSES.includes(o.status || '')).length,
          };
        })
      );

      setValets((prev) =>
        prev.map((v) => {
          const stats = statsResults.find((s) => s.id === (v._id || v.id));
          if (!stats) return { ...v, ordersLoading: false };
          return {
            ...v,
            totalOrders: stats.totalOrders,
            completedOrders: stats.completedOrders,
            pendingOrders: stats.pendingOrders,
            ordersLoading: false,
          };
        })
      );
    } catch {
      toast.error('Failed to load valets');
      setLoading(false);
    }
  }, [fetchValetOrders]);

  const fetchGlobalSettings = useCallback(async () => {
    try {
      setGlobalMaxLoading(true);
      const res = await api.get('/system-settings');
      setGlobalMaxOrders(res.data.maxConcurrentOrders || 1);
    } catch {
      toast.error('Failed to load global valet settings');
    } finally {
      setGlobalMaxLoading(false);
    }
  }, []);

  const handleUpdateGlobalMax = async () => {
    try {
      const newLimitStr = window.prompt('Set new Global Default Max Orders:', String(globalMaxOrders));
      if (!newLimitStr) return;
      const newLimit = parseInt(newLimitStr, 10);
      if (isNaN(newLimit) || newLimit < 1) {
        toast.error('Please enter a valid number >= 1');
        return;
      }
      setGlobalMaxLoading(true);
      await api.put('/system-settings', { maxConcurrentOrders: newLimit });
      setGlobalMaxOrders(newLimit);
      toast.success('Global max orders updated successfully');
    } catch {
      toast.error('Failed to update global settings');
    } finally {
      setGlobalMaxLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchValets();
      fetchGlobalSettings();
    }
  }, [user, fetchValets, fetchGlobalSettings]);

  // ── Add-valet modal ──
  const fetchAllUsers = async () => {
    setLoadingUsers(true);
    try {
      const res = await api.get('/users');
      setAllUsers(
        (res.data || []).filter((u: any) => u.role !== 'valet' && u.role !== 'super_admin')
      );
    } catch {
      toast.error('Failed to load users');
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleOpenAddModal = () => {
    setUserSearch('');
    setShowAddModal(true);
    fetchAllUsers();
  };

  const handlePromoteToValet = async (userId: string) => {
    setPromotingId(userId);
    try {
      await api.put(`/users/${userId}/role`, { role: 'valet', approvalStatus: 'approved' });
      toast.success('User promoted to Valet successfully');
      setShowAddModal(false);
      fetchValets();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || 'Failed to promote user');
    } finally {
      setPromotingId(null);
    }
  };

  // ── Deactivate / reactivate ──
  const handleDeactivate = async (valetId: string) => {
    setDeactivating(true);
    try {
      await api.put(`/users/${valetId}/deactivate`);
      toast.success('Valet deactivated');
      setConfirmDeactivateId(null);
      fetchValets();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to deactivate');
    } finally {
      setDeactivating(false);
    }
  };

  const handleReactivate = async (valetId: string) => {
    try {
      await api.put(`/users/${valetId}/reactivate`);
      toast.success('Valet reactivated');
      fetchValets();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to reactivate');
    }
  };

  const handleRemoveValetRole = async (valetId: string) => {
    try {
      await api.put(`/users/${valetId}/role`, { role: 'customer', approvalStatus: 'approved' });
      toast.success('Valet role removed – user is now a Retail Customer');
      fetchValets();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to remove valet role');
    }
  };

  // ── Orders modal ──
  const openOrdersModal = async (valet: ValetWithStats) => {
    setOrdersModalValet(valet);
    setOrderSearch('');
    setOrderStatusFilter('all');
    setOrderStartDate('');
    setOrderEndDate('');
    setOrdersLoading(true);
    setOrders([]);
    try {
      const res = await api.get('/orders', { params: { assignedValet: valet._id || valet.id } });
      const list: Order[] = Array.isArray(res.data) ? res.data : (res.data?.orders ?? []);
      setOrders(list);
    } catch {
      toast.error('Failed to load orders for this valet');
    } finally {
      setOrdersLoading(false);
    }
  };

  const closeOrdersModal = () => {
    setOrdersModalValet(null);
    setOrders([]);
  };

  // ── Filtered orders inside modal ──
  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      const q = orderSearch.toLowerCase();
      const matchesSearch =
        !q ||
        o.orderNumber?.toLowerCase().includes(q) ||
        o.user?.name?.toLowerCase().includes(q) ||
        o.user?.phone?.includes(q) ||
        o.shippingAddress?.city?.toLowerCase().includes(q);

      const matchesStatus = orderStatusFilter === 'all' || o.status === orderStatusFilter;

      let matchesDate = true;
      if (orderStartDate || orderEndDate) {
        const orderDate = o.createdAt ? new Date(o.createdAt) : null;
        if (orderDate) {
          if (orderStartDate) matchesDate = matchesDate && orderDate >= new Date(orderStartDate);
          if (orderEndDate) {
            const end = new Date(orderEndDate);
            end.setHours(23, 59, 59, 999);
            matchesDate = matchesDate && orderDate <= end;
          }
        }
      }

      return matchesSearch && matchesStatus && matchesDate;
    });
  }, [orders, orderSearch, orderStatusFilter, orderStartDate, orderEndDate]);

  // ── Valets list filtering / sorting ──
  const filteredValets = useMemo(() => {
    return valets.filter((v) => {
      const q = searchTerm.toLowerCase();
      const matchesSearch =
        !q ||
        v.name?.toLowerCase().includes(q) ||
        v.email?.toLowerCase().includes(q) ||
        v.phone?.includes(q) ||
        (v.userIdFormatted || `USER-${v.userId}` || v._id || v.id || '')
          .toLowerCase()
          .includes(q);

      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'active' && v.isActive) ||
        (statusFilter === 'inactive' && !v.isActive);

      return matchesSearch && matchesStatus;
    });
  }, [valets, searchTerm, statusFilter]);

  const sortedValets = useMemo(() => {
    if (!sortColumn) return filteredValets;
    return [...filteredValets].sort((a: any, b: any) => {
      let valA: any = a[sortColumn] ?? '';
      let valB: any = b[sortColumn] ?? '';
      if (sortColumn === 'userId') {
        valA = a.userIdFormatted || `USER-${a.userId}` || a._id || '';
        valB = b.userIdFormatted || `USER-${b.userId}` || b._id || '';
      }
      if (typeof valA === 'string' && typeof valB === 'string')
        return sortDirection === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      return sortDirection === 'asc' ? (valA > valB ? 1 : -1) : valA < valB ? 1 : -1;
    });
  }, [filteredValets, sortColumn, sortDirection]);

  const totalItems = filteredValets.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedValets = sortedValets.slice(startIndex, endIndex);

  const getPageNumbers = () => {
    const delta = 2;
    const range: (number | string)[] = [];
    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) range.push(i);
    if (currentPage - delta > 2) range.unshift('...');
    if (currentPage + delta < totalPages - 1) range.push('...');
    range.unshift(1);
    if (totalPages > 1) range.push(totalPages);
    return range;
  };

  const filteredUserSearch = useMemo(() => {
    if (!userSearch.trim()) return allUsers;
    const q = userSearch.toLowerCase();
    return allUsers.filter(
      (u) => u.name?.toLowerCase().includes(q) || u.email?.toLowerCase().includes(q) || u.phone?.includes(q)
    );
  }, [allUsers, userSearch]);

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;

  // ── Aggregate stats ──
  const totalCompleted = valets.reduce((s, v) => s + v.completedOrders, 0);
  const totalPending = valets.reduce((s, v) => s + v.pendingOrders, 0);

  // ─────────────────────────────────────────────────────────────────────────────
  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow h-full flex flex-col min-h-0">

          {/* Header */}
          <div className="mb-6 flex items-center justify-between flex-shrink-0">
            <h1 className="inline-flex items-center gap-3 text-3xl font-bold text-gray-900">
              <svg className="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
              </svg>
              Valets
              <RefreshButton onRefresh={fetchValets} />
            </h1>
            <div className="flex items-center gap-3">
              <button
                onClick={handleUpdateGlobalMax}
                disabled={globalMaxLoading}
                className="inline-flex items-center gap-2 rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm border border-slate-300 hover:bg-slate-200 transition-colors disabled:opacity-50"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Global Max Orders ({globalMaxOrders})
              </button>
              <button
                onClick={handleOpenAddModal}
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Valet
              </button>
            </div>
          </div>

          {/* Stats row */}
          <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4 flex-shrink-0">
            <div className="rounded-lg border border-yellow-100 bg-yellow-50 p-4">
              <p className="text-xs text-yellow-600 font-medium uppercase tracking-wide">Total Valets</p>
              <p className="mt-1 text-2xl font-bold text-yellow-700">{valets.length}</p>
            </div>
            <div className="rounded-lg border border-green-100 bg-green-50 p-4">
              <p className="text-xs text-green-600 font-medium uppercase tracking-wide">Active</p>
              <p className="mt-1 text-2xl font-bold text-green-700">{valets.filter((v) => v.isActive).length}</p>
            </div>
            <div className="rounded-lg border border-blue-100 bg-blue-50 p-4">
              <p className="text-xs text-blue-600 font-medium uppercase tracking-wide">Orders Completed</p>
              <p className="mt-1 text-2xl font-bold text-blue-700">{totalCompleted}</p>
            </div>
            <div className="rounded-lg border border-orange-100 bg-orange-50 p-4">
              <p className="text-xs text-orange-600 font-medium uppercase tracking-wide">Orders Pending</p>
              <p className="mt-1 text-2xl font-bold text-orange-700">{totalPending}</p>
            </div>
          </div>

          {/* Filters */}
          <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2 flex-shrink-0">
            <input
              type="text"
              placeholder="Search by name, email, phone, or ID…"
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex flex-1 items-center justify-center">
              <div className="text-gray-500">Loading valets…</div>
            </div>
          ) : (
            <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
              <table className="w-full border-collapse">
                <thead className="sticky top-0 z-10 bg-gray-50 shadow-sm">
                  <tr>
                    {[
                      ['userId', 'User ID'],
                      ['name', 'Name'],
                      ['email', 'Email'],
                      ['phone', 'Phone'],
                      ['city', 'City'],
                      ['state', 'State'],
                      ['createdAt', 'Added On'],
                      ['isActive', 'Status'],
                    ].map(([col, label]) => (
                      <th
                        key={col}
                        className="border border-gray-200 p-2 text-left cursor-pointer hover:bg-gray-100 select-none text-sm font-semibold text-gray-700"
                        onClick={() => handleSort(col)}
                      >
                        {label} {renderSortIcon(col)}
                      </th>
                    ))}
                    <th className="border border-gray-200 p-2 text-center text-sm font-semibold text-gray-700">
                      Completed
                    </th>
                    <th className="border border-gray-200 p-2 text-center text-sm font-semibold text-gray-700">
                      Pending
                    </th>
                    <th className="border border-gray-200 p-2 text-left text-sm font-semibold text-gray-700">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedValets.length > 0 ? (
                    paginatedValets.map((valet) => (
                      <tr key={valet._id || valet.id} className="hover:bg-gray-50">
                        <td className="border border-gray-200 p-2 text-sm text-gray-700">
                          {valet.userIdFormatted || (valet.userId ? `USER-${valet.userId}` : valet._id || '-')}
                        </td>
                        <td className="border border-gray-200 p-2 text-sm font-medium text-gray-900">
                          {valet.name}
                        </td>
                        <td className="border border-gray-200 p-2 text-sm text-gray-700">{valet.email}</td>
                        <td className="border border-gray-200 p-2 text-sm text-gray-700">{valet.phone || '-'}</td>
                        <td className="border border-gray-200 p-2 text-sm text-gray-700">
                          {valet.address?.city || '-'}
                        </td>
                        <td className="border border-gray-200 p-2 text-sm text-gray-700">
                          {valet.address?.state || '-'}
                        </td>
                        <td className="border border-gray-200 p-2 text-sm text-gray-700">
                          {valet.createdAt ? formatDateIST(valet.createdAt) : '-'}
                        </td>
                        <td className="border border-gray-200 p-2 text-center text-sm font-semibold">
                          {valet.maxConcurrentOrders ?? 1}
                        </td>
                        <td className="border border-gray-200 p-2">
                          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${valet.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {valet.isActive ? 'Active' : 'Inactive'}
                          </span>
                        </td>

                        {/* Completed orders */}
                        <td className="border border-gray-200 p-2 text-center">
                          {valet.ordersLoading ? (
                            <span className="text-xs text-gray-400">…</span>
                          ) : (
                            <span className="inline-flex items-center justify-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
                              {valet.completedOrders}
                            </span>
                          )}
                        </td>

                        {/* Pending orders */}
                        <td className="border border-gray-200 p-2 text-center">
                          {valet.ordersLoading ? (
                            <span className="text-xs text-gray-400">…</span>
                          ) : (
                            <span className={`inline-flex items-center justify-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${valet.pendingOrders > 0 ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-600'}`}>
                              {valet.pendingOrders}
                            </span>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="border border-gray-200 p-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            {/* Orders button */}
                            <button
                              onClick={() => openOrdersModal(valet)}
                              className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-colors"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                              </svg>
                              Orders
                            </button>

                            <button
                              onClick={async () => {
                                const limit = window.prompt(`Set max concurrent orders for ${valet.name}:`, String(valet.maxConcurrentOrders ?? 1));
                                if (limit && !isNaN(Number(limit))) {
                                  try {
                                    await api.put(`/users/${valet._id || valet.id}`, { maxConcurrentOrders: Number(limit) });
                                    toast.success('Max orders updated');
                                    fetchValets();
                                  } catch {
                                    toast.error('Failed to update max orders');
                                  }
                                }
                              }}
                              className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors"
                            >
                              Set Max
                            </button>

                            {valet.isActive ? (
                              <button
                                onClick={() => setConfirmDeactivateId(valet._id || valet.id || '')}
                                className="rounded px-2 py-1 text-xs font-medium bg-red-50 text-red-700 hover:bg-red-100 border border-red-200 transition-colors"
                              >
                                Deactivate
                              </button>
                            ) : (
                              <button
                                onClick={() => handleReactivate(valet._id || valet.id || '')}
                                className="rounded px-2 py-1 text-xs font-medium bg-green-50 text-green-700 hover:bg-green-100 border border-green-200 transition-colors"
                              >
                                Reactivate
                              </button>
                            )}
                            <button
                              onClick={() => handleRemoveValetRole(valet._id || valet.id || '')}
                              className="rounded px-2 py-1 text-xs font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200 transition-colors"
                            >
                              Remove Role
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={11} className="border border-gray-200 p-8 text-center text-gray-500">
                        {searchTerm || statusFilter !== 'all'
                          ? 'No valets match your search/filter.'
                          : 'No valets found. Click "Add Valet" to assign one.'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {!loading && totalItems > 0 && (
            <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
              <div className="text-sm text-gray-700">
                Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
                <span className="font-semibold">{endIndex}</span> of{' '}
                <span className="font-semibold">{totalItems}</span> valets
              </div>
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <span>Show</span>
                  <select
                    value={itemsPerPage}
                    onChange={(e) => { setItemsPerPage(Number(e.target.value)); setCurrentPage(1); }}
                    className="rounded border px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {[5, 10, 25, 50].map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                  <span>entries</span>
                </div>
                <nav className="inline-flex -space-x-px rounded-md shadow-sm">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                    disabled={currentPage === 1}
                    className="inline-flex items-center rounded-l-md border border-gray-300 bg-white px-2 py-2 text-sm text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  </button>
                  {getPageNumbers().map((page, idx) =>
                    page === '...' ? (
                      <span key={`d-${idx}`} className="inline-flex items-center border border-gray-300 bg-white px-4 py-2 text-sm text-gray-500">...</span>
                    ) : (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page as number)}
                        className={`inline-flex items-center border px-4 py-2 text-sm font-medium transition-colors ${currentPage === page ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600' : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'}`}
                      >
                        {page}
                      </button>
                    )
                  )}
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className="inline-flex items-center rounded-r-md border border-gray-300 bg-white px-2 py-2 text-sm text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" /></svg>
                  </button>
                </nav>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          ORDERS MODAL
      ══════════════════════════════════════════════════════════════════════ */}
      {ordersModalValet && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 p-4">
          <div className="flex w-full max-w-4xl flex-col rounded-xl bg-white shadow-2xl" style={{ maxHeight: '90vh' }}>
            {/* Modal header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 flex-shrink-0">
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  Orders — {ordersModalValet.name}
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  {ordersModalValet.email} {ordersModalValet.phone ? `· ${ordersModalValet.phone}` : ''}
                </p>
              </div>
              <button
                onClick={closeOrdersModal}
                className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Summary chips */}
            <div className="flex flex-wrap gap-3 px-6 py-3 border-b border-gray-100 bg-gray-50 flex-shrink-0">
              <span className="inline-flex items-center gap-1 rounded-full bg-gray-200 px-3 py-1 text-xs font-medium text-gray-700">
                Total <strong>{ordersLoading ? '…' : orders.length}</strong>
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800">
                Completed <strong>{ordersLoading ? '…' : orders.filter((o) => COMPLETED_STATUSES.includes(o.status || '')).length}</strong>
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-3 py-1 text-xs font-medium text-orange-800">
                Pending / In-Progress <strong>{ordersLoading ? '…' : orders.filter((o) => PENDING_STATUSES.includes(o.status || '')).length}</strong>
              </span>
            </div>

            {/* Search & filter bar */}
            <div className="grid grid-cols-1 gap-3 px-6 py-4 sm:grid-cols-4 flex-shrink-0">
              <input
                type="text"
                placeholder="Search order no., customer…"
                value={orderSearch}
                onChange={(e) => setOrderSearch(e.target.value)}
                className="col-span-1 sm:col-span-1 rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <select
                value={orderStatusFilter}
                onChange={(e) => setOrderStatusFilter(e.target.value)}
                className="rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              >
                <option value="all">All Statuses</option>
                {Object.entries(STATUS_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>{label}</option>
                ))}
              </select>
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500 whitespace-nowrap">From</label>
                <input
                  type="date"
                  value={orderStartDate}
                  onChange={(e) => setOrderStartDate(e.target.value)}
                  className="flex-1 rounded border border-gray-300 px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500 whitespace-nowrap">To</label>
                <input
                  type="date"
                  value={orderEndDate}
                  onChange={(e) => setOrderEndDate(e.target.value)}
                  className="flex-1 rounded border border-gray-300 px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
              </div>
            </div>

            {/* Orders table */}
            <div className="flex-1 overflow-y-auto px-6 pb-6 min-h-0">
              {ordersLoading ? (
                <div className="flex h-32 items-center justify-center text-gray-500 text-sm">
                  Loading orders…
                </div>
              ) : filteredOrders.length === 0 ? (
                <div className="flex h-32 items-center justify-center text-gray-400 text-sm">
                  {orders.length === 0 ? 'No orders assigned to this valet.' : 'No orders match your filters.'}
                </div>
              ) : (
                <table className="w-full border-collapse text-sm">
                  <thead className="sticky top-0 bg-gray-50 z-10">
                    <tr>
                      {['Order No.', 'Customer', 'City', 'Date', 'Amount', 'Payment', 'Status'].map((h) => (
                        <th key={h} className="border border-gray-200 px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredOrders.map((order) => (
                      <tr key={order._id} className="hover:bg-gray-50">
                        <td className="border border-gray-200 px-3 py-2 font-mono text-xs font-medium text-gray-800">
                          {order.orderNumber || order._id.slice(-8).toUpperCase()}
                        </td>
                        <td className="border border-gray-200 px-3 py-2">
                          <div className="font-medium text-gray-900">{order.user?.name || '-'}</div>
                          {order.user?.phone && (
                            <div className="text-xs text-gray-500">{order.user.phone}</div>
                          )}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 text-gray-700">
                          {order.shippingAddress?.city || '-'}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 text-gray-600 whitespace-nowrap">
                          {order.createdAt ? formatDateTimeIST(order.createdAt) : '-'}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 font-medium text-gray-900">
                          ₹{(order.total ?? 0).toFixed(2)}
                        </td>
                        <td className="border border-gray-200 px-3 py-2 uppercase text-xs text-gray-600">
                          {order.paymentMethod || '-'}
                        </td>
                        <td className="border border-gray-200 px-3 py-2">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[order.status || ''] || 'bg-gray-100 text-gray-700'}`}>
                            {STATUS_LABELS[order.status || ''] || order.status || '-'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Modal footer */}
            <div className="flex items-center justify-between border-t border-gray-200 px-6 py-3 flex-shrink-0">
              <p className="text-xs text-gray-500">
                Showing {filteredOrders.length} of {orders.length} orders
              </p>
              <button
                onClick={closeOrdersModal}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          ADD VALET MODAL
      ══════════════════════════════════════════════════════════════════════ */}
      {showAddModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-xl rounded-xl bg-white shadow-2xl flex flex-col max-h-[80vh]">
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 flex-shrink-0">
              <h2 className="text-lg font-bold text-gray-900">Assign Valet Role to User</h2>
              <button onClick={() => setShowAddModal(false)} className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 flex-shrink-0">
              <p className="mb-4 text-sm text-gray-600">
                Search for an existing user to promote to the <strong>Delivery Valet</strong> role.
              </p>
              <input
                type="text"
                placeholder="Search by name, email, or phone…"
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div className="flex-1 overflow-y-auto px-6 pb-6 min-h-0">
              {loadingUsers ? (
                <div className="text-center text-sm text-gray-500 py-8">Loading users…</div>
              ) : filteredUserSearch.length === 0 ? (
                <div className="text-center text-sm text-gray-500 py-8">
                  {userSearch ? 'No matching users found.' : 'No eligible users available.'}
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredUserSearch.map((u: any) => (
                    <div key={u._id || u.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{u.name}</p>
                        <p className="text-xs text-gray-500">{u.email}</p>
                        {u.phone && <p className="text-xs text-gray-400">{u.phone}</p>}
                        <span className="mt-1 inline-block rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-700">
                          {u.role === 'customer' ? 'Retail Customer' : u.role === 'wholesaler' ? 'Business Customer' : u.role}
                        </span>
                      </div>
                      <button
                        onClick={() => handlePromoteToValet(u._id || u.id)}
                        disabled={promotingId === (u._id || u.id)}
                        className="ml-4 flex-shrink-0 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
                      >
                        {promotingId === (u._id || u.id) ? 'Assigning…' : 'Make Valet'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          DEACTIVATE CONFIRM MODAL
      ══════════════════════════════════════════════════════════════════════ */}
      {confirmDeactivateId && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-xl bg-white shadow-2xl">
            <div className="p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-2">Deactivate Valet</h2>
              <p className="text-sm text-gray-600 mb-6">
                Are you sure you want to deactivate this valet? They will no longer be able to log in.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setConfirmDeactivateId(null)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeactivate(confirmDeactivateId)}
                  disabled={deactivating}
                  className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60 transition-colors"
                >
                  {deactivating ? 'Deactivating…' : 'Deactivate'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
