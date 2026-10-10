'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';
import Link from 'next/link';

interface SuperCategory {
  _id?: string;
  id?: string;
  name: string;
}

interface CategoryTag {
  _id?: string;
  id?: string;
  name: string;
  description?: string;
  isActive?: boolean;
  divisionId?: number;
  divisionName?: string;
  categoryHeadId?: number;
  categoryHeadName?: string;
  categoryCount?: number;
  createdAt?: string;
  updatedAt?: string;
}

export default function CategoryTagsManagement() {
  const { user } = useAuth();
  const [tags, setTags] = useState<CategoryTag[]>([]);
  const [superCategories, setSuperCategories] = useState<SuperCategory[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [editingTag, setEditingTag] = useState<CategoryTag | null>(null);
  const [formData, setFormData] = useState<{
    name: string;
    description: string;
    isActive: boolean;
    divisionId: number | null;
  }>({
    name: '',
    description: '',
    isActive: true,
    divisionId: null,
  });

  // Categories viewer modal
  const [showCategoriesModal, setShowCategoriesModal] = useState(false);
  const [viewingTag, setViewingTag] = useState<CategoryTag | null>(null);
  const [tagCategories, setTagCategories] = useState<any[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [superCategoryFilter, setSuperCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchTags();
      fetchSuperCategories();
    }
  }, [user]);

  const fetchTags = async () => {
    try {
      setLoading(true);
      const res = await api.get('/category-tags');
      setTags(res.data || []);
    } catch {
      toast.error('Failed to fetch category tags');
    } finally {
      setLoading(false);
    }
  };

  const fetchSuperCategories = async () => {
    try {
      const res = await api.get('/divisions');
      setSuperCategories(res.data || []);
    } catch {
      // Non-blocking
    }
  };

  const handleOpenAddModal = () => {
    setEditingTag(null);
    setFormData({
      name: '',
      description: '',
      isActive: true,
      divisionId: superCategories.length > 0 ? Number(superCategories[0].id || superCategories[0]._id) : null,
    });
    setShowModal(true);
  };

  const handleOpenEditModal = (tag: CategoryTag) => {
    setEditingTag(tag);
    const targetDid = tag.divisionId || tag.categoryHeadId;
    setFormData({
      name: tag.name,
      description: tag.description || '',
      isActive: tag.isActive !== false,
      divisionId: targetDid ? Number(targetDid) : null,
    });
    setShowModal(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Category tag name is required');
      return;
    }

    try {
      const payload = {
        name: formData.name.trim(),
        description: formData.description,
        isActive: formData.isActive,
        divisionId: formData.divisionId,
        categoryHeadId: formData.divisionId,
      };

      if (editingTag) {
        const id = editingTag.id || editingTag._id;
        await api.put(`/category-tags/${id}`, payload);
        toast.success('Category tag updated successfully');
      } else {
        await api.post('/category-tags', payload);
        toast.success('Category tag created successfully');
      }
      setShowModal(false);
      fetchTags();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to save category tag';
      toast.error(msg);
    }
  };

  const handleToggleStatus = async (tag: CategoryTag) => {
    const id = tag.id || tag._id;
    const newStatus = !tag.isActive;
    const action = newStatus ? 'unhide' : 'hide';
    if (!confirm(`Are you sure you want to ${action} category tag "${tag.name}"?`)) return;

    try {
      await api.put(`/category-tags/${id}`, { isActive: newStatus });
      toast.success(`Category tag ${newStatus ? 'unhidden' : 'hidden'} successfully`);
      fetchTags();
    } catch {
      toast.error(`Failed to ${action} category tag`);
    }
  };

  const handleDelete = async (tag: CategoryTag) => {
    const id = tag.id || tag._id;
    if (!confirm(`Are you sure you want to delete category tag "${tag.name}"? This action cannot be undone.`))
      return;

    try {
      await api.delete(`/category-tags/${id}`);
      toast.success('Category tag deleted successfully');
      fetchTags();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to delete category tag');
    }
  };

  const handleViewCategories = async (tag: CategoryTag) => {
    setViewingTag(tag);
    setShowCategoriesModal(true);
    setLoadingCategories(true);
    try {
      const id = tag.id || tag._id;
      const res = await api.get(`/category-tags/${id}/categories`);
      setTagCategories(res.data || []);
    } catch {
      toast.error('Failed to load categories for tag');
    } finally {
      setLoadingCategories(false);
    }
  };

  // Filtered tags
  const filteredTags = tags.filter((tag) => {
    const matchesSearch =
      tag.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (tag.description || '').toLowerCase().includes(searchTerm.toLowerCase());

    const tagDid = String(tag.divisionId || tag.categoryHeadId || '');
    const matchesSuperCategory =
      superCategoryFilter === 'all' ||
      (superCategoryFilter === 'unassigned' && !tag.divisionId && !tag.categoryHeadId) ||
      tagDid === superCategoryFilter;

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && tag.isActive !== false) ||
      (statusFilter === 'inactive' && tag.isActive === false);

    return matchesSearch && matchesSuperCategory && matchesStatus;
  });

  const totalPages = Math.ceil(filteredTags.length / itemsPerPage) || 1;
  const paginatedTags = filteredTags.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const totalAssignedTags = tags.filter((t) => t.divisionId || t.categoryHeadId).length;
  const totalCategoriesCount = tags.reduce((acc, t) => acc + (t.categoryCount || 0), 0);

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Category Tags</h1>
          <p className="mt-1 text-sm text-gray-500">
            Middle-level taxonomy. Each Category Tag belongs to a Super Category and contains multiple Categories.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <RefreshButton onRefresh={fetchTags} />
          <button
            onClick={handleOpenAddModal}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
          >
            + Add Category Tag
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Tags</p>
          <p className="mt-2 text-2xl font-bold text-gray-900">{tags.length}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Active Tags</p>
          <p className="mt-2 text-2xl font-bold text-green-600">
            {tags.filter((t) => t.isActive !== false).length}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Assigned to Super Category</p>
          <p className="mt-2 text-2xl font-bold text-indigo-600">{totalAssignedTags}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Categories</p>
          <p className="mt-2 text-2xl font-bold text-amber-600">{totalCategoriesCount}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-xl bg-white p-4 shadow-sm border border-gray-200">
        <div className="flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search category tags..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={superCategoryFilter}
            onChange={(e) => {
              setSuperCategoryFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          >
            <option value="all">All Super Categories</option>
            {superCategories.map((s) => (
              <option key={s.id || s._id} value={String(s.id || s._id)}>
                {s.name}
              </option>
            ))}
            <option value="unassigned">Unassigned Tags</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as any);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          >
            <option value="all">All Status</option>
            <option value="active">Active Only</option>
            <option value="inactive">Hidden Only</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-gray-500">Loading category tags...</div>
        ) : paginatedTags.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No category tags found. Click &quot;+ Add Category Tag&quot; to create one.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-600 uppercase">
                <tr>
                  <th className="px-6 py-3">Tag Name</th>
                  <th className="px-6 py-3">Super Category</th>
                  <th className="px-6 py-3">Description</th>
                  <th className="px-6 py-3">Contained Categories</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedTags.map((tag) => {
                  const superCatName = tag.divisionName || tag.categoryHeadName;
                  return (
                    <tr key={tag.id || tag._id} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4 font-semibold text-gray-900 whitespace-nowrap">
                        {tag.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {superCatName ? (
                          <span className="inline-flex items-center rounded-md bg-purple-50 px-2.5 py-1 text-xs font-medium text-purple-700 border border-purple-200">
                            🏛️ {superCatName}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400 italic">None</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-gray-600 max-w-xs truncate">
                        {tag.description || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleViewCategories(tag)}
                          className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800 border border-amber-200 hover:bg-amber-100 transition"
                        >
                          📁 {tag.categoryCount || 0} categories
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                            tag.isActive !== false
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {tag.isActive !== false ? 'Active' : 'Hidden'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleOpenEditModal(tag)}
                            className="rounded px-2.5 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleToggleStatus(tag)}
                            className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                              tag.isActive !== false
                                ? 'text-amber-600 hover:bg-amber-50'
                                : 'text-green-600 hover:bg-green-50'
                            }`}
                          >
                            {tag.isActive !== false ? 'Hide' : 'Unhide'}
                          </button>
                          <button
                            onClick={() => handleDelete(tag)}
                            className="rounded px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50 transition"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        {filteredTags.length > 0 && (
          <div className="flex items-center justify-between border-t border-gray-200 bg-white px-6 py-3 text-sm">
            <span className="text-gray-500">
              Showing {(currentPage - 1) * itemsPerPage + 1} to{' '}
              {Math.min(currentPage * itemsPerPage, filteredTags.length)} of {filteredTags.length} tags
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={currentPage === 1}
                className="rounded border border-gray-300 px-3 py-1 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-gray-700">
                {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="rounded border border-gray-300 px-3 py-1 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add / Edit Tag Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-bold text-gray-900">
              {editingTag ? 'Edit Category Tag' : 'Add Category Tag'}
            </h2>
            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-gray-700 mb-1">
                  Tag Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. School, Writing Instruments, Staples"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-700 mb-1">
                  Belongs to Super Category
                </label>
                <select
                  value={formData.divisionId ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      divisionId: e.target.value ? Number(e.target.value) : null,
                    })
                  }
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">-- None (Unassigned) --</option>
                  {superCategories.map((s) => (
                    <option key={s.id || s._id} value={String(s.id || s._id)}>
                      {s.name}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  Select which Super Category (e.g. Stationery, Grocery, Toys) this tag belongs to.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Optional description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.isActive}
                    onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                    className="h-4 w-4 rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  Active (visible to users)
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700"
                >
                  {editingTag ? 'Save Changes' : 'Create Tag'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Contained Categories Modal */}
      {showCategoriesModal && viewingTag && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b pb-3 mb-4">
              <div>
                <h3 className="font-bold text-gray-900 text-lg">
                  Categories under &quot;{viewingTag.name}&quot;
                </h3>
                <p className="text-xs text-gray-500">
                  Level 3 categories grouped under this Level 2 tag.
                </p>
              </div>
              <button
                onClick={() => setShowCategoriesModal(false)}
                className="text-gray-400 hover:text-gray-600 text-xl font-bold"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {loadingCategories ? (
                <div className="py-8 text-center text-gray-500">Loading categories...</div>
              ) : tagCategories.length === 0 ? (
                <div className="py-8 text-center text-gray-500">
                  <p>No categories linked to this tag yet.</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Assign this tag when creating or editing categories in Category Management.
                  </p>
                </div>
              ) : (
                tagCategories.map((c: any) => (
                  <div
                    key={c.id || c._id}
                    className="flex items-center justify-between p-3 rounded-lg border border-gray-100 bg-gray-50/50 hover:bg-gray-50 transition"
                  >
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{c.name}</p>
                      {c.description && (
                        <p className="text-xs text-gray-500 line-clamp-1">{c.description}</p>
                      )}
                    </div>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        c.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {c.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                ))
              )}
            </div>

            <div className="border-t pt-4 mt-4 flex items-center justify-between">
              <Link
                href="/admin/categories"
                className="text-xs text-indigo-600 font-semibold hover:underline"
              >
                Open Category Management &rarr;
              </Link>
              <button
                onClick={() => setShowCategoriesModal(false)}
                className="rounded-lg bg-gray-800 px-4 py-2 text-xs font-semibold text-white hover:bg-black transition"
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
