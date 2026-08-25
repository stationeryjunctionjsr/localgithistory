'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import SearchableSelect from '@/components/SearchableSelect';
import RefreshButton from './RefreshButton';
import { logger } from '@/utils/logger';

interface Segment {
  _id?: string;
  name: string;
  type: string;
  userIds: string[];
  filters?: any;
  createdAt?: string;
  isActive?: boolean;
  lastRefreshedAt?: string;
  isSystem?: boolean;
}

interface UserOption {
  _id: string;
  id?: string;
  name?: string;
  phone?: string;
  email?: string;
}

interface CustomerSegmentsProps {
  segmentType: 'retail' | 'business';
}

const PRE_EXISTING_BEHAVIORS = [
  { id: 'registered_no_order', name: 'Registered but did not order' },
  { id: 'registered_one_order', name: 'Registered and ordered once' },
  { id: 'regular_registered', name: 'Regular Registered (Avg >= 4 orders/month)' },
  {
    id: 'registered_irregular',
    name: 'Registered and irregular (>1 order and <=3 orders per month)',
  },
  { id: 'downloaded_no_order', name: 'Downloaded but did not order' },
  { id: 'downloaded_one_order', name: 'Downloaded and ordered once' },
  { id: 'regular_app_user', name: 'Regular App User (Avg >= 4 orders/month)' },
  {
    id: 'downloaded_irregular',
    name: 'Downloaded and irregular (>1 order and <=3 orders per month)',
  },
];

export default function CustomerSegments({ segmentType }: CustomerSegmentsProps) {
  const { user } = useAuth();
  const [segments, setSegments] = useState<Segment[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSegment, setEditingSegment] = useState<Segment | null>(null);
  const [showUsersModal, setShowUsersModal] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [availableUsers, setAvailableUsers] = useState<UserOption[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<UserOption[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);

  const [availableStates, setAvailableStates] = useState<string[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [availableDistricts, setAvailableDistricts] = useState<string[]>([]);

  const role = segmentType === 'retail' ? 'customer' : 'wholesaler';

  const [name, setName] = useState('');
  const [filters, setFilters] = useState<any>({
    minAverageOrderValue: '',
    maxAverageOrderValue: '',
    startDate: '',
    endDate: '',
    minOrderFrequency: '',
    maxOrderFrequency: '',
    state: '',
    district: '',
    appUser: 'all', // 'all', 'yes', 'no'
    behavior: 'none',
  });

  // Pagination states
  const [currentSegmentsPage, setCurrentSegmentsPage] = useState(1);
  const [segmentsPerPage, setSegmentsPerPage] = useState(10);

  const [currentPreviewPage, setCurrentPreviewPage] = useState(1);
  const [previewPerPage, setPreviewPerPage] = useState(10);

  const [currentViewUsersPage, setCurrentViewUsersPage] = useState(1);
  const [viewUsersPerPage, setViewUsersPerPage] = useState(10);

  const getPageNumbers = (currentPage: number, totalPages: number) => {
    const delta = 2;
    const range = [];
    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i);
    }
    if (currentPage - delta > 2) {
      range.unshift('...');
    }
    if (currentPage + delta < totalPages - 1) {
      range.push('...');
    }
    range.unshift(1);
    if (totalPages > 1) {
      range.push(totalPages);
    }
    return range;
  };

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchSegments();
      fetchInitialData();
    }
    setCurrentSegmentsPage(1);
    setCurrentPreviewPage(1);
    setCurrentViewUsersPage(1);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, segmentType]);

  const fetchSegments = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/customer-segments?type=${segmentType}`);
      setSegments(res.data || []);
    } catch (e: any) {
      toast.error('Failed to load segments');
    } finally {
      setLoading(false);
    }
  };

  const fetchInitialData = async () => {
    try {
      const [usersRes, statesRes] = await Promise.all([
        api.get(`/users?role=${role}`),
        api.get('/pincodes/states'),
      ]);
      setAvailableUsers(usersRes.data || []);
      setFilteredUsers(usersRes.data || []);
      setAvailableStates(statesRes.data || []);
    } catch (e) {
      logger.error(e);
    }
  };

  const handleFilterChange = async (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    if (key === 'state') {
      if (value) {
        const res = await api.get(`/pincodes/districts?state=${encodeURIComponent(value)}`);
        setAvailableDistricts(res.data || []);
      } else {
        setAvailableDistricts([]);
      }
      setFilters((prev: any) => ({ ...prev, district: '' }));
    }
  };

  const handleApplyFilters = async () => {
    try {
      const payload: any = { role };
      if (filters.minAverageOrderValue)
        payload.minAverageOrderValue = parseFloat(filters.minAverageOrderValue);
      if (filters.maxAverageOrderValue)
        payload.maxAverageOrderValue = parseFloat(filters.maxAverageOrderValue);
      if (filters.startDate) payload.startDate = new Date(filters.startDate).toISOString();
      if (filters.endDate) payload.endDate = new Date(filters.endDate).toISOString();
      if (filters.minOrderFrequency)
        payload.minOrderFrequency = parseInt(filters.minOrderFrequency, 10);
      if (filters.maxOrderFrequency)
        payload.maxOrderFrequency = parseInt(filters.maxOrderFrequency, 10);
      if (filters.state) payload.state = filters.state;
      if (filters.district) payload.district = filters.district;
      if (filters.appUser !== 'all') payload.appUser = filters.appUser === 'yes';
      if (filters.behavior !== 'none') payload.behavior = filters.behavior;

      const res = await api.post('/customer-segments/filter', payload);
      const users = res.data || [];
      setFilteredUsers(users);
      setSelectedUserIds(users.map((u: any) => u._id || u.id));
      setCurrentPreviewPage(1);
      toast.success(`Found ${users.length} users matching criteria`);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (e: any) {
      toast.error('Failed to apply filters');
    }
  };

  const handleSaveSegment = async () => {
    if (!name.trim()) {
      toast.error('Segment name is required');
      return;
    }
    if (selectedUserIds.length === 0) {
      toast.error('Please select at least one user');
      return;
    }

    try {
      const payload = {
        name,
        type: segmentType,
        userIds: selectedUserIds,
        filters,
      };
      if (editingSegment?._id) {
        await api.put(`/customer-segments/${editingSegment._id}`, payload);
        toast.success('Segment updated successfully');
      } else {
        await api.post('/customer-segments', payload);
        toast.success('Segment created successfully');
      }
      setShowModal(false);
      setEditingSegment(null);
      fetchSegments();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (e: any) {
      toast.error(editingSegment?._id ? 'Failed to update segment' : 'Failed to create segment');
    }
  };

  const handleEdit = (seg: Segment) => {
    setEditingSegment(seg);
    setName(seg.name);
    setFilters(
      seg.filters || {
        minAverageOrderValue: '',
        maxAverageOrderValue: '',
        startDate: '',
        endDate: '',
        minOrderFrequency: '',
        maxOrderFrequency: '',
        state: '',
        district: '',
        appUser: 'all',
        behavior: 'none',
      }
    );
    setFilteredUsers(availableUsers);
    setSelectedUserIds(seg.userIds);
    setCurrentPreviewPage(1);
    setShowModal(true);
  };

  const handleToggleActive = async (seg: Segment) => {
    try {
      const newActive = !seg.isActive;
      await api.put(`/customer-segments/${seg._id}`, { isActive: newActive });
      toast.success(`Segment ${newActive ? 'enabled' : 'disabled'}`);
      fetchSegments();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (e) {
      toast.error('Failed to toggle segment status');
    }
  };

  const handleRefreshSegment = async (id: string) => {
    try {
      setRefreshing(true);
      const res = await api.post(`/customer-segments/${id}/refresh`);
      toast.success(`Segment refreshed: Found ${res.data.count} users`);
      fetchSegments();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (e) {
      toast.error('Failed to refresh segment');
    } finally {
      setRefreshing(false);
    }
  };

  const handleToggleUserSelection = (uid: string) => {
    setSelectedUserIds((prev) =>
      prev.includes(uid) ? prev.filter((x) => x !== uid) : [...prev, uid]
    );
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this segment?')) return;
    try {
      await api.delete(`/customer-segments/${id}`);
      toast.success('Segment deleted');
      fetchSegments();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (e) {
      toast.error('Failed to delete segment');
    }
  };

  // Slicing segments
  const sortedSegments = [...segments].sort((a, b) => (b.isSystem ? 1 : 0) - (a.isSystem ? 1 : 0));
  const totalSegments = sortedSegments.length;
  const totalSegmentsPages = Math.ceil(totalSegments / segmentsPerPage);
  const segmentsStartIndex = (currentSegmentsPage - 1) * segmentsPerPage;
  const segmentsEndIndex = Math.min(segmentsStartIndex + segmentsPerPage, totalSegments);
  const paginatedSegments = sortedSegments.slice(segmentsStartIndex, segmentsEndIndex);

  // Slicing preview users
  const totalPreviewItems = filteredUsers.length;
  const totalPreviewPages = Math.ceil(totalPreviewItems / previewPerPage);
  const previewStartIndex = (currentPreviewPage - 1) * previewPerPage;
  const previewEndIndex = Math.min(previewStartIndex + previewPerPage, totalPreviewItems);
  const paginatedPreviewUsers = filteredUsers.slice(previewStartIndex, previewEndIndex);

  // Slicing view users
  const targetSegmentUsers = availableUsers.filter((u) =>
    segments
      .find((s) => s._id === showUsersModal)
      ?.userIds.includes(u._id || (u.id as string))
  );
  const totalViewUsersItems = targetSegmentUsers.length;
  const totalViewUsersPages = Math.ceil(totalViewUsersItems / viewUsersPerPage);
  const viewUsersStartIndex = (currentViewUsersPage - 1) * viewUsersPerPage;
  const viewUsersEndIndex = Math.min(viewUsersStartIndex + viewUsersPerPage, totalViewUsersItems);
  const paginatedViewUsers = targetSegmentUsers.slice(viewUsersStartIndex, viewUsersEndIndex);

  if (user?.role !== 'super_admin')
    return <div className="p-8 text-center text-slate-500">Access Denied</div>;

  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-md">
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 p-6">
          <h2 className="flex items-center gap-3 text-2xl font-bold text-slate-800">
            <InfoButton
              info={`Manage segments for ${segmentType} customers. Create rules to auto-group users.`}
            >
              {segmentType === 'retail' ? 'Retail Segments' : 'Business Segments'}
            </InfoButton>
            <RefreshButton onRefresh={fetchSegments} />
          </h2>
          <div className="flex gap-2">
            <button
              onClick={() => {
                setEditingSegment(null);
                setName('');
                setFilters({
                  minAverageOrderValue: '',
                  maxAverageOrderValue: '',
                  startDate: '',
                  endDate: '',
                  minOrderFrequency: '',
                  maxOrderFrequency: '',
                  state: '',
                  district: '',
                  appUser: 'all',
                  behavior: 'none',
                });
                setFilteredUsers(availableUsers);
                setSelectedUserIds([]);
                setCurrentPreviewPage(1);
                setShowModal(true);
              }}
              className="rounded-lg px-4 py-2 text-white shadow transition"
              style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
            >
              Create Segment
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 font-medium text-slate-500">
              <tr>
                <th className="px-6 py-3">Name</th>
                <th className="px-6 py-3">Users</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Created At</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {paginatedSegments.length > 0 ? (
                paginatedSegments.map((seg) => (
                  <tr
                    key={seg._id}
                    className={`hover:bg-slate-50 ${seg.isSystem ? 'bg-slate-50/30' : ''}`}
                  >
                    <td className="px-6 py-4 font-semibold text-slate-800">{seg.name || seg._id || 'Unnamed'}</td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => {
                          setCurrentViewUsersPage(1);
                          setShowUsersModal(seg._id!);
                        }}
                        className="text-indigo-600 hover:underline"
                      >
                        {seg.userIds?.length || 0} users
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      {seg.isActive !== false ? (
                        <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                          Active
                        </span>
                      ) : (
                        <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {seg.createdAt
                        ? new Date(seg.createdAt).toLocaleDateString()
                        : seg.isSystem
                          ? 'System'
                          : '-'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        {!seg.isSystem && (
                          <button
                            onClick={() => handleEdit(seg)}
                            className="rounded px-3 py-1 text-sm text-white shadow-sm transition"
                            style={{
                              background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                            }}
                          >
                            Edit
                          </button>
                        )}
                        <button
                          onClick={() => handleToggleActive(seg)}
                          className="min-w-[70px] rounded px-3 py-1 text-sm text-white shadow-sm transition"
                          style={{
                            background:
                              seg.isActive !== false
                                ? 'linear-gradient(135deg, #6c757d 0%, #495057 100%)'
                                : 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
                          }}
                        >
                          {seg.isActive !== false ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center italic text-slate-400">
                    No custom segments created yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Premium Pagination Controls */}
        {sortedSegments.length > 0 && (
          <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-slate-200 pt-4 sm:flex-row px-6 pb-6">
            <div className="text-sm text-gray-700">
              Showing <span className="font-semibold">{totalSegments === 0 ? 0 : segmentsStartIndex + 1}</span> to{' '}
              <span className="font-semibold">{segmentsEndIndex}</span> of{' '}
              <span className="font-semibold">{totalSegments}</span> segments
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <span>Show</span>
                <select
                  value={segmentsPerPage}
                  onChange={(e) => {
                    setSegmentsPerPage(Number(e.target.value));
                    setCurrentSegmentsPage(1);
                  }}
                  className="rounded border px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
                <span>entries</span>
              </div>
              <nav className="inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                <button
                  onClick={() => setCurrentSegmentsPage((p) => Math.max(p - 1, 1))}
                  disabled={currentSegmentsPage === 1}
                  className="inline-flex items-center rounded-l-md border border-gray-300 bg-white px-2 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Previous</span>
                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
                {getPageNumbers(currentSegmentsPage, totalSegmentsPages).map((page, index) => {
                  if (page === '...') {
                    return (
                      <span
                        key={`dots-${index}`}
                        className="inline-flex items-center border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-500"
                      >
                        ...
                      </span>
                    );
                  }
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentSegmentsPage(page as number)}
                      className={`inline-flex items-center border px-4 py-2 text-sm font-medium transition-colors ${
                        currentSegmentsPage === page
                          ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600 font-semibold'
                          : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
                <button
                  onClick={() => setCurrentSegmentsPage((p) => Math.min(p + 1, totalSegmentsPages))}
                  disabled={currentSegmentsPage === totalSegmentsPages}
                  className="inline-flex items-center rounded-r-md border border-gray-300 bg-white px-2 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Next</span>
                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
              </nav>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4">
          <div className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 p-6">
              <h3 className="text-xl font-bold text-slate-800">
                {editingSegment ? 'Edit Segment' : 'Create Custom Segment'}
              </h3>
              <button
                onClick={() => {
                  setShowModal(false);
                  setEditingSegment(null);
                }}
                className="text-2xl font-bold text-slate-400 hover:text-slate-600"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 space-y-6 overflow-y-auto bg-slate-50 p-6">
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">
                  Segment Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. High Value Customers"
                  className="w-full rounded-lg border-2 border-slate-200 p-3 shadow-sm outline-none transition focus:border-indigo-500"
                />
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <h4 className="mb-4 flex items-center gap-2 font-bold text-slate-800">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-xs text-indigo-600">
                    1
                  </span>
                  Set Auto-Filtering Rules
                </h4>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-600">
                      Order Date Range
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="date"
                        value={filters.startDate}
                        onChange={(e) => handleFilterChange('startDate', e.target.value)}
                        className="w-full rounded-lg border p-2.5 text-sm text-slate-700"
                      />
                      <input
                        type="date"
                        value={filters.endDate}
                        onChange={(e) => handleFilterChange('endDate', e.target.value)}
                        className="w-full rounded-lg border p-2.5 text-sm text-slate-700"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-600">
                      Avg Order Value (Min - Max)
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        placeholder="Min"
                        value={filters.minAverageOrderValue}
                        onChange={(e) => handleFilterChange('minAverageOrderValue', e.target.value)}
                        className="w-full rounded-lg border p-2.5 text-sm text-slate-700"
                      />
                      <input
                        type="number"
                        placeholder="Max"
                        value={filters.maxAverageOrderValue}
                        onChange={(e) => handleFilterChange('maxAverageOrderValue', e.target.value)}
                        className="w-full rounded-lg border p-2.5 text-sm text-slate-700"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-600">
                      Order Frequency (Min - Max)
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        placeholder="Min"
                        value={filters.minOrderFrequency}
                        onChange={(e) => handleFilterChange('minOrderFrequency', e.target.value)}
                        className="w-full rounded-lg border p-2.5 text-sm text-slate-700"
                      />
                      <input
                        type="number"
                        placeholder="Max"
                        value={filters.maxOrderFrequency}
                        onChange={(e) => handleFilterChange('maxOrderFrequency', e.target.value)}
                        className="w-full rounded-lg border p-2.5 text-sm text-slate-700"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-600">
                      App Used / Platform
                    </label>
                    <select
                      value={filters.appUser}
                      onChange={(e) => handleFilterChange('appUser', e.target.value)}
                      className="w-full rounded-lg border p-2.5 text-sm text-slate-700"
                    >
                      <option value="all">Any Platform</option>
                      <option value="yes">Mobile App User</option>
                      <option value="no">Browser Only User</option>
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-600">
                      Behavior Pattern
                    </label>
                    <select
                      value={filters.behavior}
                      onChange={(e) => handleFilterChange('behavior', e.target.value)}
                      className="w-full rounded-lg border p-2.5 text-sm text-slate-700"
                    >
                      <option value="none">Any Behavior</option>
                      {PRE_EXISTING_BEHAVIORS.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-600">
                      Location (State)
                    </label>
                    <SearchableSelect
                      options={availableStates}
                      value={filters.state}
                      onChange={(v) => handleFilterChange('state', v)}
                      placeholder="Select State"
                    />
                  </div>
                </div>
                <button
                  onClick={handleApplyFilters}
                  className="mt-6 w-full rounded-lg border border-indigo-100 bg-indigo-50 py-2.5 font-bold text-indigo-700 shadow-sm transition hover:bg-indigo-100"
                >
                  Apply Rules & Preview Users
                </button>
              </div>

              <div className="flex flex-1 flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center justify-between">
                  <h4 className="flex items-center gap-2 font-bold text-slate-800">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-xs text-indigo-600">
                      2
                    </span>
                    Finalize User List ({selectedUserIds.length} users)
                  </h4>
                  <div className="rounded-full border bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-500">
                    Showing {filteredUsers.length} potential matches
                  </div>
                </div>

                <div className="max-h-[300px] overflow-y-auto rounded-xl border border-slate-200 bg-slate-50">
                  <table className="w-full text-left text-sm">
                    <thead className="sticky top-0 z-10 border-b border-slate-200 bg-white font-semibold text-slate-500">
                      <tr>
                        <th className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={
                              selectedUserIds.length === filteredUsers.length &&
                              filteredUsers.length > 0
                            }
                            onChange={() => {
                              if (selectedUserIds.length === filteredUsers.length)
                                setSelectedUserIds([]);
                              else setSelectedUserIds(filteredUsers.map((u: any) => u._id || u.id));
                            }}
                          />
                        </th>
                        <th className="px-4 py-3">Name</th>
                        <th className="px-4 py-3">Contact</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {paginatedPreviewUsers.map((u) => (
                        <tr key={u._id || u.id} className="transition hover:bg-indigo-50/30">
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={selectedUserIds.includes(u._id || (u.id as string))}
                              onChange={() => handleToggleUserSelection(u._id || (u.id as string))}
                            />
                          </td>
                          <td className="px-4 py-3 font-medium text-slate-700">
                            {u.name || 'Unnamed'}
                          </td>
                          <td className="px-4 py-3 text-slate-500">{u.phone || u.email || '-'}</td>
                        </tr>
                      ))}
                      {filteredUsers.length === 0 && (
                        <tr>
                          <td colSpan={3} className="p-8 text-center italic text-slate-400">
                            No users match the criteria.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Preview Users Pagination */}
                {filteredUsers.length > 0 && (
                  <div className="mt-4 flex flex-col items-center justify-between gap-4 border-t border-gray-100 pt-4 sm:flex-row">
                    <div className="text-xs text-gray-500">
                      Showing <span className="font-semibold">{previewStartIndex + 1}</span> to{' '}
                      <span className="font-semibold">{previewEndIndex}</span> of{' '}
                      <span className="font-semibold">{totalPreviewItems}</span> users
                    </div>
                    <nav className="inline-flex -space-x-px rounded-md shadow-sm text-xs" aria-label="Pagination">
                      <button
                        type="button"
                        onClick={() => setCurrentPreviewPage((p) => Math.max(p - 1, 1))}
                        disabled={currentPreviewPage === 1}
                        className="inline-flex items-center rounded-l-md border border-gray-300 bg-white px-2 py-1 text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      {getPageNumbers(currentPreviewPage, totalPreviewPages).map((page, index) => {
                        if (page === '...') {
                          return (
                            <span key={`dots-${index}`} className="inline-flex items-center border border-gray-300 bg-white px-2 py-1 text-gray-400">
                              ...
                            </span>
                          );
                        }
                        return (
                          <button
                            type="button"
                            key={page}
                            onClick={() => setCurrentPreviewPage(page as number)}
                            className={`inline-flex items-center border px-2 py-1 transition-colors ${
                              currentPreviewPage === page
                                ? 'bg-indigo-50 border-indigo-500 text-indigo-600 font-semibold'
                                : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'
                            }`}
                          >
                            {page}
                          </button>
                        );
                      })}
                      <button
                        type="button"
                        onClick={() => setCurrentPreviewPage((p) => Math.min(p + 1, totalPreviewPages))}
                        disabled={currentPreviewPage === totalPreviewPages}
                        className="inline-flex items-center rounded-r-md border border-gray-300 bg-white px-2 py-1 text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </nav>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 border-t border-slate-200 bg-white p-4 sm:p-6">
              <button
                onClick={() => {
                  setShowModal(false);
                  setEditingSegment(null);
                }}
                className="rounded-lg px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSegment}
                className="rounded-lg px-5 py-2.5 text-sm font-medium text-white shadow-sm transition"
                style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
              >
                {editingSegment ? 'Update Segment' : 'Save Segment'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Users Modal */}
      {showUsersModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4">
          <div className="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 p-6">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-bold text-slate-800">Segment Users</h3>
                {!segments.find((s) => s._id === showUsersModal)?.isSystem && (
                  <button
                    onClick={() => handleRefreshSegment(showUsersModal!)}
                    disabled={refreshing}
                    className="rounded-full p-1.5 text-indigo-600 transition hover:bg-indigo-50 disabled:opacity-50"
                    title="Refresh User List"
                  >
                    <svg
                      className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                  </button>
                )}
              </div>
              <button
                onClick={() => setShowUsersModal(null)}
                className="text-2xl font-bold text-slate-400 hover:text-slate-600"
              >
                &times;
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <table className="w-full text-left text-sm">
                <thead className="border-b font-semibold text-slate-500">
                  <tr>
                    <th className="pb-3 pr-4">Name</th>
                    <th className="pb-3">Contact</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {paginatedViewUsers.map((u) => (
                    <tr key={u._id || u.id} className="hover:bg-slate-50">
                      <td className="py-3 pr-4 font-medium text-slate-700">
                        {u.name || 'Unnamed'}
                      </td>
                      <td className="py-3 text-slate-500">{u.phone || u.email || '-'}</td>
                    </tr>
                  ))}
                  {totalViewUsersItems === 0 && (
                    <tr>
                      <td colSpan={2} className="py-8 text-center italic text-slate-400">
                        No users in this segment yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>

              {/* View Users Pagination */}
              {totalViewUsersItems > 0 && (
                <div className="mt-4 flex flex-col items-center justify-between gap-4 border-t border-gray-100 pt-4 sm:flex-row">
                  <div className="text-xs text-gray-500">
                    Showing <span className="font-semibold">{viewUsersStartIndex + 1}</span> to{' '}
                    <span className="font-semibold">{viewUsersEndIndex}</span> of{' '}
                    <span className="font-semibold">{totalViewUsersItems}</span> users
                  </div>
                  <nav className="inline-flex -space-x-px rounded-md shadow-sm text-xs" aria-label="Pagination">
                    <button
                      onClick={() => setCurrentViewUsersPage((p) => Math.max(p - 1, 1))}
                      disabled={currentViewUsersPage === 1}
                      className="inline-flex items-center rounded-l-md border border-gray-300 bg-white px-2 py-1 text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    {getPageNumbers(currentViewUsersPage, totalViewUsersPages).map((page, index) => {
                      if (page === '...') {
                        return (
                          <span key={`dots-${index}`} className="inline-flex items-center border border-gray-300 bg-white px-2 py-1 text-gray-400">
                            ...
                          </span>
                        );
                      }
                      return (
                        <button
                          key={page}
                          onClick={() => setCurrentViewUsersPage(page as number)}
                          className={`inline-flex items-center border px-2 py-1 transition-colors ${
                            currentViewUsersPage === page
                              ? 'bg-indigo-50 border-indigo-500 text-indigo-600 font-semibold'
                              : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'
                          }`}
                        >
                          {page}
                        </button>
                      );
                    })}
                    <button
                      onClick={() => setCurrentViewUsersPage((p) => Math.min(p + 1, totalViewUsersPages))}
                      disabled={currentViewUsersPage === totalViewUsersPages}
                      className="inline-flex items-center rounded-r-md border border-gray-300 bg-white px-2 py-1 text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </nav>
                </div>
              )}
            </div>
            <div className="flex justify-end border-t border-slate-100 bg-slate-50/50 p-4">
              <button
                onClick={() => setShowUsersModal(null)}
                className="rounded-lg border border-slate-200 bg-white px-6 py-2 font-semibold text-slate-600 shadow-sm transition hover:bg-slate-100"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
