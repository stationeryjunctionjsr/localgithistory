'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateTimeIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';

interface AvailabilityRequest {
  _id: string;
  productId: string;
  productName: string;
  pincode: string;
  userId?: string;
  userName?: string;
  userEmail?: string;
  status: 'pending' | 'fulfilled';
  createdAt: string;
  fulfilledAt?: string;
}

export default function AdminRequests() {
  const { user: currentUser } = useAuth();
  const [requests, setRequests] = useState<AvailabilityRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [fulfilling, setFulfilling] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterPincode, setFilterPincode] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (currentUser?.role === 'super_admin') {
      fetchRequests();
    }
  }, [currentUser]);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const res = await api.get('/availability-requests/');
      setRequests(res.data?.requests || []);
    } catch {
      toast.error('Failed to fetch availability requests');
    } finally {
      setLoading(false);
    }
  };

  const handleFulfill = async (id: string) => {
    try {
      setFulfilling(id);
      const res = await api.post(`/availability-requests/${id}/fulfill`);
      toast.success(res.data?.message || 'Request fulfilled and user notified!');
      setRequests((prev) =>
        prev.map((r) => (r._id === id ? { ...r, status: 'fulfilled', fulfilledAt: new Date().toISOString() } : r))
      );
    } catch {
      toast.error('Failed to fulfill request');
    } finally {
      setFulfilling(null);
    }
  };

  const filtered = useMemo(() => {
    return requests.filter((r) => {
      if (filterStatus !== 'all' && r.status !== filterStatus) return false;
      if (filterPincode && !r.pincode.includes(filterPincode)) return false;
      if (searchTerm) {
        const q = searchTerm.toLowerCase();
        return (
          r.productName.toLowerCase().includes(q) ||
          (r.userName || '').toLowerCase().includes(q) ||
          (r.userEmail || '').toLowerCase().includes(q) ||
          r.pincode.includes(q)
        );
      }
      return true;
    });
  }, [requests, filterStatus, filterPincode, searchTerm]);

  const pending = requests.filter((r) => r.status === 'pending').length;

  if (!currentUser || currentUser.role !== 'super_admin') return null;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Product Availability Requests</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Users requesting products to be made available at their pincode
          </p>
        </div>
        <div className="flex items-center gap-3">
          {pending > 0 && (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
              {pending} pending
            </span>
          )}
          <RefreshButton onRefresh={fetchRequests} />
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <input
          type="text"
          placeholder="Search product, user, email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 w-64"
        />
        <input
          type="text"
          placeholder="Filter by pincode"
          value={filterPincode}
          onChange={(e) => setFilterPincode(e.target.value)}
          className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 w-36"
        />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="fulfilled">Fulfilled</option>
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-400">No requests found.</div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Product</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Pincode</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">User</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Requested</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Status</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {filtered.map((req) => (
                <tr key={req._id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3">
                    <a
                      href={`/admin/products?search=${encodeURIComponent(req.productName || '')}`}
                      className="text-emerald-700 dark:text-emerald-400 hover:underline font-medium"
                    >
                      {req.productName}
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-gray-700 dark:text-gray-200">{req.pincode}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                    <div>{req.userName || '—'}</div>
                    {req.userEmail && (
                      <div className="text-xs text-gray-400">{req.userEmail}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                    {formatDateTimeIST(req.createdAt)}
                  </td>
                  <td className="px-4 py-3">
                    {req.status === 'fulfilled' ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                        ✓ Fulfilled
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400">
                        ⏳ Pending
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {req.status === 'pending' && (
                      <button
                        onClick={() => handleFulfill(req._id)}
                        disabled={fulfilling === req._id}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition"
                      >
                        {fulfilling === req._id ? 'Notifying...' : 'Mark Fulfilled'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
