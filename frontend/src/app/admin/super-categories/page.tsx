'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

interface SuperCategory {
  _id?: string;
  id?: string;
  name: string;
  description?: string;
  imageUrl?: string;
  displayOrder?: number;
  isActive?: boolean;
  categoryTagIds?: number[];
  categoryTags?: any[];
  categoryTagNames?: string[];
  categoryCount?: number;
  createdAt?: string;
  updatedAt?: string;
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
}

export default function SuperCategoriesManagement() {
  const { user } = useAuth();
  const [categories, setCategories] = useState<SuperCategory[]>([]);
  const [allTags, setAllTags] = useState<CategoryTag[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<SuperCategory | null>(null);
  const [formData, setFormData] = useState<{
    name: string;
    description: string;
    displayOrder: number;
    isActive: boolean;
    categoryTagIds: number[];
  }>({
    name: '',
    description: '',
    displayOrder: 0,
    isActive: true,
    categoryTagIds: [],
  });

  // Hierarchy View Modal
  const [showHierarchyModal, setShowHierarchyModal] = useState(false);
  const [viewingCategory, setViewingCategory] = useState<SuperCategory | null>(null);
  const [hierarchyTags, setHierarchyTags] = useState<any[]>([]);
  const [loadingHierarchy, setLoadingHierarchy] = useState(false);

  // Filter and Search states
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [tagSearchInModal, setTagSearchInModal] = useState('');

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchSuperCategories();
      fetchAllTags();
    }
  }, [user]);

  const fetchSuperCategories = async () => {
    try {
      setLoading(true);
      const res = await api.get('/divisions');
      setCategories(res.data || []);
    } catch (err) {
      toast.error('Failed to fetch super categories');
    } finally {
      setLoading(false);
    }
  };

  const fetchAllTags = async () => {
    try {
      const res = await api.get('/category-tags');
      setAllTags(res.data || []);
    } catch (err) {
      // Non-blocking
    }
  };

  const handleOpenAddModal = () => {
    setEditingCategory(null);
    setFormData({
      name: '',
      description: '',
      displayOrder: categories.length + 1,
      isActive: true,
      categoryTagIds: [],
    });
    setTagSearchInModal('');
    setShowModal(true);
  };

  const handleOpenEditModal = (cat: SuperCategory) => {
    setEditingCategory(cat);
    const tagIds = cat.categoryTagIds || (cat.categoryTags ? cat.categoryTags.map((t) => Number(t.id || t._id)) : []);
    setFormData({
      name: cat.name || '',
      description: cat.description || '',
      displayOrder: cat.displayOrder ?? 0,
      isActive: cat.isActive !== false,
      categoryTagIds: tagIds,
    });
    setTagSearchInModal('');
    setShowModal(true);
  };

  const handleToggleTagSelection = (tagId: number) => {
    setFormData((prev) => {
      const exists = prev.categoryTagIds.includes(tagId);
      return {
        ...prev,
        categoryTagIds: exists
          ? prev.categoryTagIds.filter((id) => id !== tagId)
          : [...prev.categoryTagIds, tagId],
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Super category name is required');
      return;
    }

    try {
      const payload = {
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        displayOrder: Number(formData.displayOrder) || 0,
        isActive: formData.isActive,
        categoryTagIds: formData.categoryTagIds,
      };

      if (editingCategory) {
        const catId = editingCategory.id || editingCategory._id;
        await api.put(`/divisions/${catId}`, payload);
        toast.success('Super Category updated successfully');
      } else {
        await api.post('/divisions', payload);
        toast.success('Super Category created successfully');
      }

      setShowModal(false);
      fetchSuperCategories();
      fetchAllTags();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleToggleStatus = async (cat: SuperCategory) => {
    const catId = cat.id || cat._id;
    try {
      await api.put(`/divisions/${catId}`, {
        isActive: !cat.isActive,
      });
      toast.success(`Super Category ${cat.isActive ? 'disabled' : 'enabled'} successfully`);
      fetchSuperCategories();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleDelete = async (cat: SuperCategory) => {
    const catId = cat.id || cat._id;
    if (!confirm(`Are you sure you want to delete "${cat.name}"? This will unlink its associated category tags.`)) {
      return;
    }
    try {
      await api.delete(`/divisions/${catId}`);
      toast.success('Super Category deleted successfully');
      fetchSuperCategories();
      fetchAllTags();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to delete super category');
    }
  };

  const handleOpenHierarchy = async (cat: SuperCategory) => {
    setViewingCategory(cat);
    setShowHierarchyModal(true);
    setLoadingHierarchy(true);
    try {
      const catId = cat.id || cat._id;
      const res = await api.get(`/divisions/${catId}/tags`);
      const tagsWithCategories = await Promise.all(
        (res.data || []).map(async (t: any) => {
          try {
            const catRes = await api.get(`/category-tags/${t.id || t._id}/categories`);
            return { ...t, categories: catRes.data || [] };
          } catch {
            return { ...t, categories: [] };
          }
        })
      );
      setHierarchyTags(tagsWithCategories);
    } catch (err) {
      toast.error('Failed to load hierarchy');
    } finally {
      setLoadingHierarchy(false);
    }
  };

  // Filter and search
  const filteredCategories = categories.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.description || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && c.isActive !== false) ||
      (statusFilter === 'inactive' && c.isActive === false);
    return matchesSearch && matchesStatus;
  });

  const totalItems = filteredCategories.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedCategories = filteredCategories.slice(startIndex, startIndex + itemsPerPage);

  if (user?.role !== 'super_admin') {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-gray-500">Access denied. Super Admin role required.</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Super Categories</h1>
          <p className="mt-1 text-sm text-gray-500">
            Top-level catalog divisions (e.g. Stationery, Grocery, Toys, Electronics). Each Super Category contains multiple Category Tags, and each Tag contains multiple Categories.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <RefreshButton onRefresh={fetchSuperCategories} />
          <button
            onClick={handleOpenAddModal}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
          >
            + Add Super Category
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Total Super Categories</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{categories.length}</p>
          <p className="mt-1 text-xs text-gray-400">
            {categories.filter((c) => c.isActive !== false).length} Active &bull; {categories.filter((c) => c.isActive === false).length} Inactive
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Total Category Tags</p>
          <p className="mt-2 text-3xl font-bold text-indigo-600">{allTags.length}</p>
          <p className="mt-1 text-xs text-gray-400">
            Organised under Super Categories
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Catalog Structure</p>
          <div className="mt-2 flex items-center gap-1.5 text-xs font-bold text-gray-700">
            <span className="rounded bg-indigo-100 px-2 py-0.5 text-indigo-800">Super Category</span>
            <span>&rarr;</span>
            <span className="rounded bg-blue-100 px-2 py-0.5 text-blue-800">Tag</span>
            <span>&rarr;</span>
            <span className="rounded bg-emerald-100 px-2 py-0.5 text-emerald-800">Category</span>
          </div>
          <p className="mt-1.5 text-xs text-gray-400">Strict relational 3-level taxonomy</p>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="mb-6 flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-2">
          <div className="relative flex-1 max-w-md">
            <input
              type="text"
              placeholder="Search super categories..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full rounded-lg border border-gray-300 py-2 pl-3 pr-8 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-2.5 top-2.5 text-xs text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            )}
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as any);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wider text-gray-600 border-b border-gray-200">
              <tr>
                <th className="py-3.5 pl-6 pr-3">Order</th>
                <th className="px-3 py-3.5">Super Category</th>
                <th className="px-3 py-3.5">Description</th>
                <th className="px-3 py-3.5">Category Tags</th>
                <th className="px-3 py-3.5">Total Categories</th>
                <th className="px-3 py-3.5">Status</th>
                <th className="py-3.5 pl-3 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-500">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent"></div>
                    <p className="mt-2">Loading super categories...</p>
                  </td>
                </tr>
              ) : paginatedCategories.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-500">
                    No super categories found matching criteria.
                  </td>
                </tr>
              ) : (
                paginatedCategories.map((cat) => (
                  <tr key={cat.id || cat._id} className="hover:bg-gray-50/75 transition-colors">
                    <td className="py-4 pl-6 pr-3 font-mono text-xs text-gray-400">
                      {cat.displayOrder ?? 0}
                    </td>
                    <td className="px-3 py-4">
                      <div className="font-semibold text-gray-900">{cat.name}</div>
                      <div className="text-xs text-gray-400">ID: {cat.id || cat._id}</div>
                    </td>
                    <td className="px-3 py-4 max-w-xs text-gray-600">
                      {cat.description ? (
                        <span className="line-clamp-2">{cat.description}</span>
                      ) : (
                        <span className="italic text-gray-400">No description</span>
                      )}
                    </td>
                    <td className="px-3 py-4">
                      <div className="flex flex-wrap items-center gap-1.5 max-w-xs">
                        {cat.categoryTags && cat.categoryTags.length > 0 ? (
                          cat.categoryTags.slice(0, 3).map((tag: any, idx: number) => (
                            <span
                              key={idx}
                              className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-200"
                            >
                              {tag.name || tag}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-gray-400 italic">No tags linked</span>
                        )}
                        {cat.categoryTags && cat.categoryTags.length > 3 && (
                          <span className="text-xs font-semibold text-gray-400">
                            +{cat.categoryTags.length - 3} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-4">
                      <span className="inline-flex items-center rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-200">
                        {cat.categoryCount ?? 0} Categories
                      </span>
                    </td>
                    <td className="px-3 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                          cat.isActive !== false
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {cat.isActive !== false ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="py-4 pl-3 pr-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenHierarchy(cat)}
                          title="Explore complete 3-tier hierarchy"
                          className="rounded p-1.5 text-gray-500 hover:bg-gray-100 hover:text-indigo-600 transition"
                        >
                          🌳 Explore Tree
                        </button>
                        <button
                          onClick={() => handleOpenEditModal(cat)}
                          className="rounded p-1.5 text-gray-500 hover:bg-gray-100 hover:text-blue-600 transition"
                          title="Edit"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleToggleStatus(cat)}
                          className={`rounded p-1.5 text-xs font-medium transition ${
                            cat.isActive !== false
                              ? 'text-amber-600 hover:bg-amber-50'
                              : 'text-green-600 hover:bg-green-50'
                          }`}
                        >
                          {cat.isActive !== false ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          onClick={() => handleDelete(cat)}
                          className="rounded p-1.5 text-red-600 hover:bg-red-50 transition"
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-6 py-3 text-sm">
          <div className="text-gray-500">
            Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
            <span className="font-semibold">{Math.min(startIndex + itemsPerPage, totalItems)}</span> of{' '}
            <span className="font-semibold">{totalItems}</span> super categories
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              disabled={currentPage === 1}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="px-2 text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Add / Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl max-h-[90vh] flex flex-col">
            <div className="mb-4 flex items-center justify-between border-b pb-3">
              <h2 className="text-lg font-bold text-gray-900">
                {editingCategory ? 'Edit Super Category' : 'Create Super Category'}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 text-xl font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto pr-1 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1">
                  Super Category Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Stationery, Grocery, Toys, Electronics"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Optional overview of what products belong in this super category..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1">
                    Display Order
                  </label>
                  <input
                    type="number"
                    value={formData.displayOrder}
                    onChange={(e) => setFormData({ ...formData, displayOrder: parseInt(e.target.value) || 0 })}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
                <div className="flex items-center pt-6">
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.isActive}
                      onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                      className="h-4 w-4 rounded text-indigo-600 focus:ring-indigo-500"
                    />
                    Active in catalog
                  </label>
                </div>
              </div>

              {/* Tag Selector */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
                    Assign Category Tags ({formData.categoryTagIds.length} selected)
                  </label>
                </div>
                <input
                  type="text"
                  placeholder="Search tags to assign..."
                  value={tagSearchInModal}
                  onChange={(e) => setTagSearchInModal(e.target.value)}
                  className="mb-2 w-full rounded-md border border-gray-200 px-3 py-1.5 text-xs focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <div className="max-h-48 overflow-y-auto rounded-lg border border-gray-200 p-2 space-y-1 bg-gray-50/50">
                  {allTags.filter((t) =>
                    t.name.toLowerCase().includes(tagSearchInModal.toLowerCase())
                  ).length === 0 ? (
                    <p className="p-3 text-center text-xs text-gray-400">No category tags found</p>
                  ) : (
                    allTags
                      .filter((t) => t.name.toLowerCase().includes(tagSearchInModal.toLowerCase()))
                      .map((t) => {
                        const tid = Number(t.id || t._id);
                        const isSelected = formData.categoryTagIds.includes(tid);
                        return (
                          <div
                            key={tid}
                            onClick={() => handleToggleTagSelection(tid)}
                            className={`flex items-center justify-between p-2 rounded-md cursor-pointer transition text-xs ${
                              isSelected
                                ? 'bg-indigo-50 border border-indigo-200 text-indigo-900 font-semibold'
                                : 'hover:bg-gray-100 border border-transparent text-gray-700'
                            }`}
                          >
                            <span className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => {}} // handled by parent div
                                className="h-3.5 w-3.5 rounded text-indigo-600 focus:ring-indigo-500"
                              />
                              {t.name}
                            </span>
                            {t.divisionName && t.divisionName !== formData.name && (
                              <span className="text-[10px] text-gray-400">Currently in {t.divisionName}</span>
                            )}
                          </div>
                        );
                      })
                  )}
                </div>
                <p className="mt-1 text-[11px] text-gray-400">
                  Category tags assigned here will belong to this Super Category and appear in its hierarchy.
                </p>
              </div>

              <div className="mt-4 flex items-center justify-end gap-3 border-t pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
                >
                  {editingCategory ? 'Save Changes' : 'Create Super Category'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 3-Tier Hierarchy Explorer Modal */}
      {showHierarchyModal && viewingCategory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b pb-4 mb-4">
              <div>
                <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-bold text-indigo-800">
                  Level 1: Super Category
                </span>
                <h2 className="text-xl font-bold text-gray-900 mt-1">{viewingCategory.name} Hierarchy</h2>
                <p className="text-xs text-gray-500">
                  Showing all Category Tags (Level 2) and member Categories (Level 3) under this Super Category.
                </p>
              </div>
              <button
                onClick={() => setShowHierarchyModal(false)}
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {loadingHierarchy ? (
                <div className="py-12 text-center text-gray-500">
                  <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent"></div>
                  <p className="mt-2 text-sm">Building 3-level taxonomy view...</p>
                </div>
              ) : hierarchyTags.length === 0 ? (
                <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center">
                  <p className="text-sm font-medium text-gray-600">No Category Tags assigned to {viewingCategory.name}.</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Edit this Super Category to assign category tags like School Notebooks, Writing Instruments, etc.
                  </p>
                </div>
              ) : (
                hierarchyTags.map((tag: any) => (
                  <div key={tag.id || tag._id} className="rounded-xl border border-gray-200 bg-gray-50/60 p-4">
                    <div className="flex items-center justify-between border-b border-gray-200/80 pb-2 mb-3">
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-blue-100 px-2 py-0.5 text-[11px] font-bold text-blue-800">
                          Level 2: Tag
                        </span>
                        <h3 className="font-semibold text-gray-900 text-sm">{tag.name}</h3>
                      </div>
                      <span className="text-xs font-semibold text-gray-500">
                        {tag.categories?.length || 0} Categories
                      </span>
                    </div>

                    {/* Member Categories */}
                    <div className="pl-4">
                      {tag.categories && tag.categories.length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                          {tag.categories.map((cat: any) => (
                            <div
                              key={cat.id || cat._id}
                              className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-2 text-xs shadow-2xs hover:border-indigo-300 transition"
                            >
                              <span className="font-medium text-gray-800 truncate" title={cat.name}>
                                {cat.name}
                              </span>
                              <span
                                className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                                  cat.isActive ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
                                }`}
                              >
                                {cat.isActive ? 'Active' : 'Off'}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400 italic">No categories assigned to this tag yet.</p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="border-t pt-4 mt-4 flex justify-end">
              <button
                onClick={() => setShowHierarchyModal(false)}
                className="rounded-lg bg-gray-900 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-black transition"
              >
                Close Explorer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
