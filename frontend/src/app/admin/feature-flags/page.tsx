'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';
import InfoButton from '@/components/InfoButton';

interface FeatureFlag {
  _id?: string;
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  category: string;
  createdAt?: string;
  updatedAt?: string;
}

export default function FeatureFlagManagement() {
  const { user } = useAuth();
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingFlag, setEditingFlag] = useState<FeatureFlag | null>(null);
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    description: '',
    enabled: false,
    category: 'features',
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

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
      fetchFlags();
    }
  }, [user]);

  const fetchFlags = async () => {
    try {
      const response = await api.get('/feature-flags');
      setFlags(response.data || []);
      setLoading(false);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch feature flags');
      setLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingFlag) {
        await api.put(`/feature-flags/${editingFlag.id}`, formData);
        toast.success('Feature flag updated successfully');
      } else {
        await api.post('/feature-flags', formData);
        toast.success('Feature flag created successfully');
      }
      setShowModal(false);
      setEditingFlag(null);
      setFormData({
        id: '',
        name: '',
        description: '',
        enabled: false,
        category: 'features',
      });
      fetchFlags();
    } catch (error: any) {
      toast.error(
        error.response?.data?.message || error.response?.data?.detail || 'Operation failed'
      );
    }
  };

  const handleEdit = (flag: FeatureFlag) => {
    setEditingFlag(flag);
    setFormData({
      id: flag.id,
      name: flag.name,
      description: flag.description || '',
      enabled: flag.enabled,
      category: flag.category || 'features',
    });
    setShowModal(true);
  };

  const handleDelete = async (flag: FeatureFlag) => {
    if (window.confirm(`Are you sure you want to delete "${flag.name}"?`)) {
      try {
        await api.delete(`/feature-flags/${flag.id}`);
        toast.success('Feature flag deleted successfully');
        fetchFlags();
      } catch (error: any) {
        toast.error(
          error.response?.data?.message ||
            error.response?.data?.detail ||
            'Failed to delete feature flag'
        );
      }
    }
  };

  const handleToggle = async (flag: FeatureFlag) => {
    try {
      await api.patch(`/feature-flags/${flag.id}/toggle`);
      toast.success(`Feature flag ${!flag.enabled ? 'enabled' : 'disabled'} successfully`);
      fetchFlags();
    } catch (error: any) {
      toast.error(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to toggle feature flag'
      );
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingFlag(null);
    setFormData({
      id: '',
      name: '',
      description: '',
      enabled: false,
      category: 'features',
    });
  };

  const categories = ['all', 'features', 'ui', 'analytics', 'payment', 'delivery'];
  const filteredFlags = flags.filter((flag) => {
    const matchesSearch =
      flag.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      flag.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (flag.description && flag.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = categoryFilter === 'all' || flag.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const totalItems = filteredFlags.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedFlags = filteredFlags.slice(startIndex, endIndex);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
          Feature Flags Management <RefreshButton onRefresh={fetchFlags} />
        </h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowModal(true)}
            className="rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
          >
            + Add Feature Flag
          </button>
        </div>
      </div>

      <div className="mb-6 flex flex-wrap gap-4">
        <div className="min-w-[300px] flex-1">
          <input
            type="text"
            placeholder="Search flags..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full rounded-lg border border-gray-300 px-4 py-2"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            setCurrentPage(1);
          }}
          className="rounded-lg border border-gray-300 px-4 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
        >
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat === 'all' ? 'All Categories' : cat.charAt(0).toUpperCase() + cat.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-hidden rounded-lg bg-white shadow border border-gray-200">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wider text-gray-500 border-b border-gray-200">
            <tr>
              <th className="px-6 py-4"><InfoButton info="The unique machine-readable identifier for this feature flag, used in code">ID</InfoButton></th>
              <th className="px-6 py-4"><InfoButton info="The human-readable display name for this feature flag">Name</InfoButton></th>
              <th className="px-6 py-4"><InfoButton info="A description of what this feature flag controls or enables">Description</InfoButton></th>
              <th className="px-6 py-4"><InfoButton info="The functional category this flag belongs to (e.g. features, ui, payment, delivery)">Category</InfoButton></th>
              <th className="px-6 py-4"><InfoButton info="Whether this feature flag is currently enabled or disabled">Status</InfoButton></th>
              <th className="px-6 py-4"><InfoButton info="Edit, enable/disable, or delete this feature flag">Actions</InfoButton></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {totalItems === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                  No feature flags found
                </td>
              </tr>
            ) : (
              paginatedFlags.map((flag) => (
                <tr key={flag._id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-mono text-gray-900">
                    <code className="rounded bg-gray-100 px-2 py-1 text-xs">{flag.id}</code>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{flag.name}</td>
                  <td className="px-6 py-4 text-gray-500">{flag.description || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    <span className="rounded bg-gray-200 px-2 py-1 text-xs">
                      {flag.category || 'features'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    <span
                      className={`rounded px-2 py-1 text-xs ${flag.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {flag.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(flag)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleToggle(flag)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background: flag.enabled
                            ? 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)'
                            : 'linear-gradient(135deg, #28A745 0%, #218838 100%)',
                        }}
                      >
                        {flag.enabled ? 'Disable' : 'Enable'}
                      </button>
                      <button
                        onClick={() => handleDelete(flag)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background: 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)',
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Premium Pagination Controls */}
      {totalItems > 0 && (
        <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-slate-200 pt-4 sm:flex-row px-6 pb-6">
          <div className="text-sm text-gray-700">
            Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
            <span className="font-semibold">{endIndex}</span> of{' '}
            <span className="font-semibold">{totalItems}</span> entries
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-700">
              <span>Show</span>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
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
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={currentPage === 1}
                className="inline-flex items-center rounded-l-md border border-gray-300 bg-white px-2 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="sr-only">Previous</span>
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </button>
              {getPageNumbers(currentPage, totalPages).map((page, index) => {
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
                    onClick={() => setCurrentPage(page as number)}
                    className={`inline-flex items-center border px-4 py-2 text-sm font-medium transition-colors ${
                      currentPage === page
                        ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600 font-semibold'
                        : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                );
              })}
              <button
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                disabled={currentPage === totalPages}
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

      {showModal && (
        <div
          className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-24"
          onClick={handleCloseModal}
        >
          <div
            className="w-full max-w-md rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-bold">
                {editingFlag ? 'Edit Feature Flag' : 'Add Feature Flag'}
              </h3>
              <button onClick={handleCloseModal} className="text-2xl">
                &times;
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block">Flag ID *</label>
                <input
                  type="text"
                  name="id"
                  value={formData.id}
                  onChange={handleChange}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  required
                  disabled={!!editingFlag}
                  placeholder="e.g., enable_new_feature"
                />
                <small className="text-sm text-gray-600">
                  Unique identifier (cannot be changed after creation)
                </small>
              </div>
              <div>
                <label className="mb-1 block">Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  required
                  placeholder="e.g., New Feature"
                />
              </div>
              <div>
                <label className="mb-1 block">Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  rows={3}
                  placeholder="Describe what this feature flag controls"
                />
              </div>
              <div>
                <label className="mb-1 block">Category</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                >
                  <option value="features">Features</option>
                  <option value="ui">UI</option>
                  <option value="analytics">Analytics</option>
                  <option value="payment">Payment</option>
                  <option value="delivery">Delivery</option>
                </select>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="enabled"
                    checked={formData.enabled}
                    onChange={handleChange}
                    className="mr-2"
                  />
                  Enabled
                </label>
              </div>
              <div className="flex justify-end gap-4">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                >
                  {editingFlag ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
