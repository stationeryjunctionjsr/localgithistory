'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';
import { logger } from '@/utils/logger';

interface PincodeSearchRecord {
  _id: string;
  pincode: string;
  isServiceable: boolean;
  sellerCount: number;
  serviceableSellerIds: string[];
  userRole: string;
  city?: string;
  state?: string;
  district?: string;
  createdAt: string;
}

interface StatsData {
  totalSearches: number;
  serviceableSearches: number;
  unserviceableSearches: number;
  uniquePincodesCount: number;
  topPincodes: {
    pincode: string;
    city?: string;
    state?: string;
    count: number;
    isServiceable: boolean;
  }[];
}

export default function PincodeSearchesPage() {
  const { user } = useAuth();
  const [searches, setSearches] = useState<PincodeSearchRecord[]>([]);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [filterServiceable, setFilterServiceable] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchStats = async () => {
    try {
      const res = await api.get('/admin/pincode-searches/stats');
      setStats(res.data);
    } catch (err: any) {
      logger.error('Failed to fetch stats', err);
    }
  };

  const fetchSearches = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('page', page.toString());
      params.set('limit', limit.toString());
      if (filterServiceable !== 'all') {
        params.set('is_serviceable', filterServiceable);
      }
      if (searchQuery.trim()) {
        params.set('pincode', searchQuery.trim());
      }

      const res = await api.get(`/admin/pincode-searches?${params.toString()}`);
      setSearches(res.data.searches || []);
      setTotalCount(res.data.totalCount || 0);
    } catch (err: any) {
      logger.error('Failed to fetch pincode searches', err);
      toast.error('Failed to load pincode search history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchSearches();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, limit, filterServiceable]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchSearches();
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / limit));

  return (
    <div className="min-h-screen bg-gray-50/50 p-6 lg:p-10">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900 sm:text-3xl">
            Pincode Searches & Hyperlocal Demand
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Track user location queries, demand hotspots, and serviceability performance in real time.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <RefreshButton
            onRefresh={async () => {
              await Promise.all([fetchStats(), fetchSearches()]);
            }}
          />
        </div>
      </div>

      {/* KPI Cards */}
      {stats && (
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Total Searches</span>
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                🔍
              </span>
            </div>
            <p className="mt-3 text-3xl font-black text-gray-900">{stats.totalSearches.toLocaleString('en-IN')}</p>
            <p className="mt-1 text-xs text-gray-500">All customer & wholesaler location checks</p>
          </div>

          <div className="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">Serviceable Demand</span>
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
                ✅
              </span>
            </div>
            <p className="mt-3 text-3xl font-black text-emerald-600">
              {stats.serviceableSearches.toLocaleString('en-IN')}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {stats.totalSearches > 0
                ? `${Math.round((stats.serviceableSearches / stats.totalSearches) * 100)}% of all searches`
                : '0%'}
            </p>
          </div>

          <div className="rounded-2xl border border-amber-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600">Unserviceable Demand</span>
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
                📍
              </span>
            </div>
            <p className="mt-3 text-3xl font-black text-amber-600">
              {stats.unserviceableSearches.toLocaleString('en-IN')}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {stats.totalSearches > 0
                ? `${Math.round((stats.unserviceableSearches / stats.totalSearches) * 100)}% expansion opportunity`
                : '0%'}
            </p>
          </div>

          <div className="rounded-2xl border border-purple-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-600">Unique Pincodes</span>
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
                🗺️
              </span>
            </div>
            <p className="mt-3 text-3xl font-black text-purple-600">
              {stats.uniquePincodesCount.toLocaleString('en-IN')}
            </p>
            <p className="mt-1 text-xs text-gray-500">Distinct geographic localities searched</p>
          </div>
        </div>
      )}

      {/* Top Searched Localities */}
      {stats && stats.topPincodes && stats.topPincodes.length > 0 && (
        <div className="mb-8 rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Top Searched Pincodes & Demand Hotspots</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {stats.topPincodes.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded-xl border border-gray-100 bg-gray-50/50 p-3.5 hover:bg-gray-100/60 transition-colors"
              >
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-gray-900">{item.pincode}</span>
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${
                        item.isServiceable ? 'bg-emerald-500' : 'bg-amber-500'
                      }`}
                    />
                  </div>
                  <div className="text-xs text-gray-500 truncate max-w-[120px]">
                    {item.city || item.state || 'Unknown'}
                  </div>
                </div>
                <div className="text-right">
                  <span className="rounded-lg bg-white px-2.5 py-1 text-xs font-black text-gray-700 shadow-sm border border-gray-100">
                    {item.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search & Filter Controls */}
      <div className="mb-6 rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <input
                type="text"
                placeholder="Search by PIN code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-gray-50/50 py-2.5 pl-10 pr-4 text-sm text-gray-900 outline-none transition-all focus:border-[#1a4d33] focus:bg-white focus:ring-2 focus:ring-[#1a4d33]/10"
              />
              <span className="absolute left-3.5 top-3 text-gray-400">🔍</span>
            </div>
            <button
              type="submit"
              className="rounded-xl bg-[#1a4d33] px-5 py-2.5 text-sm font-bold text-white transition-all hover:bg-[#143e29] active:scale-95"
            >
              Search
            </button>
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('');
                  setPage(1);
                }}
                className="text-sm font-medium text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Status:</span>
            <div className="flex rounded-xl bg-gray-100 p-1">
              <button
                type="button"
                onClick={() => {
                  setFilterServiceable('all');
                  setPage(1);
                }}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
                  filterServiceable === 'all' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => {
                  setFilterServiceable('true');
                  setPage(1);
                }}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
                  filterServiceable === 'true' ? 'bg-emerald-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Serviceable
              </button>
              <button
                type="button"
                onClick={() => {
                  setFilterServiceable('false');
                  setPage(1);
                }}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
                  filterServiceable === 'false' ? 'bg-amber-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Unserviceable
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Search Logs Table */}
      <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-600">
            <thead className="border-b border-gray-100 bg-gray-50/75 text-xs font-bold uppercase tracking-wider text-gray-500">
              <tr>
                <th className="px-6 py-4">PIN Code</th>
                <th className="px-6 py-4">Location</th>
                <th className="px-6 py-4">Serviceability</th>
                <th className="px-6 py-4">Sellers Count</th>
                <th className="px-6 py-4">User Type</th>
                <th className="px-6 py-4">Date & Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-500">
                    <div className="mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-2 border-gray-200 border-t-[#1a4d33]" />
                    Loading searches...
                  </td>
                </tr>
              ) : searches.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-500">
                    No pincode searches found matching your filters.
                  </td>
                </tr>
              ) : (
                searches.map((record) => (
                  <tr key={record._id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-gray-900">{record.pincode}</td>
                    <td className="px-6 py-4">
                      {record.city ? (
                        <div>
                          <span className="font-semibold text-gray-900">{record.city}</span>
                          {record.state && <span className="text-xs text-gray-400">, {record.state}</span>}
                        </div>
                      ) : (
                        <span className="text-gray-400 italic">Not resolved</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {record.isServiceable ? (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 border border-emerald-200/50">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          Serviceable
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-amber-700 border border-amber-200/50">
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                          Not Serviceable
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 font-semibold text-gray-800">
                      {record.sellerCount > 0 ? (
                        <span>{record.sellerCount} {record.sellerCount === 1 ? 'seller' : 'sellers'}</span>
                      ) : (
                        <span className="text-gray-400">0</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="capitalize text-xs font-semibold px-2.5 py-1 rounded-md bg-gray-100 text-gray-700">
                        {record.userRole || 'customer'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500">
                      {record.createdAt ? new Date(record.createdAt).toLocaleString('en-IN') : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-gray-100 bg-gray-50/50 px-6 py-4 text-xs text-gray-500">
          <div>
            Showing <span className="font-bold text-gray-900">{searches.length > 0 ? (page - 1) * limit + 1 : 0}</span> to{' '}
            <span className="font-bold text-gray-900">{Math.min(page * limit, totalCount)}</span> of{' '}
            <span className="font-bold text-gray-900">{totalCount}</span> searches
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 font-bold text-gray-700 shadow-sm transition-all hover:bg-gray-50 disabled:opacity-40"
            >
              Previous
            </button>
            <span className="font-bold text-gray-700">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 font-bold text-gray-700 shadow-sm transition-all hover:bg-gray-50 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
