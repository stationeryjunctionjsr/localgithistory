'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';
import InfoButton from '@/components/InfoButton';

interface BundleItem {
  productId: string;
  quantity: number;
  product?: {
    _id: string;
    name: string;
    sku: string;
    mrp: number;
    images?: string[];
    stock?: number;
  };
  lineMrp?: number;
}

interface Bundle {
  _id?: string;
  name: string;
  description?: string;
  price: number;
  items: BundleItem[];
  imageUrl?: string;
  images?: string[];
  displayImage?: string;
  category?: string;
  subCategory?: string;
  brand?: string;
  searchTags?: string[];
  isActive: boolean;
  totalMrp?: number;
  savings?: number;
  savingsPercent?: number;
  isAvailable?: boolean;
  createdAt?: string;
}

interface Product {
  _id: string;
  name: string;
  sku: string;
  mrp: number;
  images?: string[];
  stock?: number;
}

const emptyForm = (): Omit<Bundle, '_id'> => ({
  name: '',
  description: '',
  price: 0,
  items: [],
  imageUrl: '',
  displayImage: '',
  category: '',
  subCategory: '',
  brand: '',
  searchTags: [],
  isActive: true,
});

export default function BundlesManagement() {
  const { user } = useAuth();
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBundle, setEditingBundle] = useState<Bundle | null>(null);
  const [formData, setFormData] = useState<Omit<Bundle, '_id'>>(emptyForm());
  const [productSearch, setProductSearch] = useState('');
  const [saving, setSaving] = useState(false);
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
      fetchBundles();
      fetchProducts();
    }
  }, [user]);

  const fetchBundles = async () => {
    try {
      const res = await api.get('/bundles/admin/all');
      setBundles(res.data.bundles || []);
    } catch {
      toast.error('Failed to fetch bundles');
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const res = await api.get('/products');
      setProducts(res.data.products || res.data || []);
    } catch {
      toast.error('Failed to fetch products');
    }
  };

  const resetForm = () => {
    setFormData(emptyForm());
    setEditingBundle(null);
    setProductSearch('');
  };

  const openCreate = () => {
    resetForm();
    setShowModal(true);
  };

  const openEdit = (bundle: Bundle) => {
    setEditingBundle(bundle);
    setFormData({
      name: bundle.name,
      description: bundle.description || '',
      price: bundle.price,
      items: bundle.items.map((i) => ({ productId: i.productId, quantity: i.quantity })),
      imageUrl: bundle.imageUrl || '',
      isActive: bundle.isActive,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.items.length) {
      toast.error('Add at least one product to the bundle');
      return;
    }
    if (formData.price <= 0) {
      toast.error('Bundle price must be greater than zero');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...formData,
        searchTags: typeof formData.searchTags === 'string' 
          ? (formData.searchTags as string).split(',').map(t => t.trim()).filter(Boolean)
          : formData.searchTags
      };
      
      if (editingBundle?._id) {
        await api.put(`/bundles/admin/${editingBundle._id}`, payload);
        toast.success('Bundle updated');
      } else {
        await api.post('/bundles/admin', payload);
        toast.success('Bundle created');
      }
      setShowModal(false);
      fetchBundles();
      resetForm();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Operation failed');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleStatus = async (bundle: Bundle) => {
    try {
      await api.put(`/bundles/admin/${bundle._id}`, { isActive: !bundle.isActive });
      toast.success(`Bundle ${bundle.isActive ? 'deactivated' : 'activated'}`);
      fetchBundles();
    } catch {
      toast.error('Failed to update status');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this bundle permanently?')) return;
    try {
      await api.delete(`/bundles/admin/${id}`);
      toast.success('Bundle deleted');
      fetchBundles();
    } catch {
      toast.error('Failed to delete bundle');
    }
  };

  // ── bundle item helpers ────────────────────────────────────────────────────
  const addProductToBundle = (product: Product) => {
    const already = formData.items.find((i) => i.productId === product._id);
    if (already) {
      toast.info(`${product.name} is already in this bundle`);
      return;
    }
    setFormData({
      ...formData,
      items: [...formData.items, { productId: product._id, quantity: 1 }],
    });
  };

  const removeItemFromBundle = (productId: string) => {
    setFormData({
      ...formData,
      items: formData.items.filter((i) => i.productId !== productId),
    });
  };

  const updateItemQty = (productId: string, qty: number) => {
    setFormData({
      ...formData,
      items: formData.items.map((i) => (i.productId === productId ? { ...i, quantity: Math.max(1, qty) } : i)),
    });
  };

  // ── derived helpers ────────────────────────────────────────────────────────
  const getProductById = (id: string) => products.find((p) => p._id === id);

  const computedTotalMrp = formData.items.reduce((sum, item) => {
    const p = getProductById(item.productId);
    return sum + (p?.mrp ?? 0) * item.quantity;
  }, 0);

  const filteredProducts = products.filter(
    (p) =>
      !formData.items.find((i) => i.productId === p._id) &&
      (p.name.toLowerCase().includes(productSearch.toLowerCase()) ||
        (p.sku || '').toLowerCase().includes(productSearch.toLowerCase()))
  );

  const imgSrc = (url?: string) =>
    url
      ? url.startsWith('http')
        ? url
        : `${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '')}${url}`
      : null;

  if (loading) return <div className="p-8 text-center text-slate-500">Loading bundles…</div>;

  const totalItems = bundles.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedBundles = bundles.slice(startIndex, endIndex);


  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow h-full flex flex-col min-h-0">
          <div className="mb-6 flex flex-shrink-0 items-center justify-between gap-4">
            <div>
              <h1 className="inline-flex items-center gap-3 text-3xl font-bold text-slate-800">
                Product Bundles <RefreshButton onRefresh={fetchBundles} />
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Create curated product sets at a special bundle price. Stock is tracked per individual item.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={openCreate}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-white transition-colors hover:bg-indigo-700"
              >
                <span className="text-xl">+</span> New Bundle
              </button>
            </div>
          </div>

          <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
            <table className="w-full border-collapse text-left">
              <thead className="sticky top-0 z-10 bg-gray-50 shadow-sm">
                <tr className="bg-gray-50">
                  <th className="border border-gray-200 p-2 text-left"><InfoButton info="The bundle name, description, and cover image">Bundle</InfoButton></th>
                  <th className="border border-gray-200 p-2 text-left"><InfoButton info="Number of individual products included in this bundle">Items</InfoButton></th>
                  <th className="border border-gray-200 p-2 text-left"><InfoButton info="Sum of the MRP of all individual products at their standard quantities">MRP Total</InfoButton></th>
                  <th className="border border-gray-200 p-2 text-left"><InfoButton info="The discounted price at which the entire bundle is sold">Bundle Price</InfoButton></th>
                  <th className="border border-gray-200 p-2 text-left"><InfoButton info="The saving amount and percentage discount compared to buying items individually at MRP">Savings</InfoButton></th>
                  <th className="border border-gray-200 p-2 text-left"><InfoButton info="Whether this bundle is currently active and visible to customers">Status</InfoButton></th>
                  <th className="border border-gray-200 p-2 text-left"><InfoButton info="Edit, activate/deactivate, or delete this bundle">Actions</InfoButton></th>
                </tr>
              </thead>
              <tbody>
                {paginatedBundles.map((bundle) => (
                  <tr key={bundle._id} className="hover:bg-gray-50">
                    <td className="border border-gray-200 p-2">
                      <div className="flex items-center gap-3">
                        {bundle.displayImage || bundle.imageUrl ? (
                          <img
                            src={imgSrc(bundle.displayImage || bundle.imageUrl || '') || ''}
                            className="h-10 w-10 rounded-lg border border-slate-200 object-cover"
                            alt=""
                          />
                        ) : (
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-violet-100 to-indigo-100 text-lg">
                            🎁
                          </div>
                        )}
                        <div>
                          <div className="font-semibold text-slate-800">{bundle.name}</div>
                          <div className="max-w-xs truncate text-xs text-slate-500">{bundle.description}</div>
                        </div>
                      </div>
                    </td>
                    <td className="border border-gray-200 p-2">
                      <span className="rounded-full border border-indigo-100 bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700">
                        {bundle.items.length} item{bundle.items.length !== 1 ? 's' : ''}
                      </span>
                    </td>
                    <td className="border border-gray-200 p-2 text-slate-600">
                      ₹{bundle.totalMrp?.toFixed(2) ?? '—'}
                    </td>
                    <td className="border border-gray-200 p-2 font-semibold text-slate-800">
                      ₹{bundle.price.toFixed(2)}
                    </td>
                    <td className="border border-gray-200 p-2">
                      {bundle.savings != null && bundle.savings > 0 ? (
                        <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                          ₹{bundle.savings.toFixed(2)} ({bundle.savingsPercent}% off)
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">No savings</span>
                      )}
                    </td>
                    <td className="border border-gray-200 p-2">
                      <span
                        className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
                          bundle.isActive
                            ? 'border-emerald-100 bg-emerald-50 text-emerald-700'
                            : 'border-slate-200 bg-slate-100 text-slate-600'
                        }`}
                      >
                        {bundle.isActive ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="border border-gray-200 p-2">
                      <div className="flex gap-2">
                        <button
                          onClick={() => openEdit(bundle)}
                          className="px-2 py-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleToggleStatus(bundle)}
                          className={`px-2 py-1 text-sm font-medium ${
                            bundle.isActive
                              ? 'text-amber-600 hover:text-amber-800'
                              : 'text-emerald-600 hover:text-emerald-800'
                          }`}
                        >
                          {bundle.isActive ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          onClick={() => handleDelete(bundle._id!)}
                          className="px-2 py-1 text-sm font-medium text-rose-600 hover:text-rose-800"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {totalItems === 0 && (
                  <tr>
                    <td colSpan={7} className="border border-gray-200 p-4 text-center text-slate-400">
                      No bundles yet. Create your first bundle!
                    </td>
                  </tr>
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


      {/* Create / Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl">
            {/* Modal header */}
            <div className="flex items-center justify-between border-b border-slate-200 p-6">
              <h2 className="text-xl font-bold text-slate-800">
                {editingBundle ? 'Edit Bundle' : 'Create New Bundle'}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-2xl text-slate-400 hover:text-slate-600"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
              <div className="grid grid-cols-1 gap-0 md:grid-cols-2">
                {/* Left: bundle details */}
                <div className="space-y-5 border-r border-slate-100 p-6">
                  <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <h4 className="text-sm font-bold text-slate-700">Bundle Details</h4>

                    <div>
                      <label className="mb-1 block text-sm font-semibold text-slate-700">Name *</label>
                      <input
                        required
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        placeholder="e.g. Back to School Starter Pack"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-sm font-semibold text-slate-700">Description</label>
                      <textarea
                        rows={2}
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        placeholder="Describe the bundle…"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-sm font-semibold text-slate-700">
                        Bundle Price (₹) *
                      </label>
                      <input
                        required
                        type="number"
                        min={0.01}
                        step={0.01}
                        value={formData.price || ''}
                        onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
                        className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        placeholder="299.00"
                      />
                      {computedTotalMrp > 0 && (
                        <div className="mt-1.5 flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-1.5 text-xs text-emerald-700">
                          <span>Sum of MRPs:</span>
                          <span className="font-semibold">₹{computedTotalMrp.toFixed(2)}</span>
                          {formData.price > 0 && formData.price < computedTotalMrp && (
                            <>
                              <span className="text-slate-400">•</span>
                              <span className="font-semibold text-emerald-700">
                                Save ₹{(computedTotalMrp - formData.price).toFixed(2)} (
                                {((computedTotalMrp - formData.price) / computedTotalMrp * 100).toFixed(1)}% off)
                              </span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div>
                      <label className="mb-1 block text-sm font-semibold text-slate-700">Display Image URL <span className="font-normal text-slate-400">(optional)</span></label>
                      <input
                        type="text"
                        value={formData.displayImage}
                        onChange={(e) => setFormData({ ...formData, displayImage: e.target.value })}
                        className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        placeholder="https://... (defaults to first product image if left blank)"
                      />
                    </div>
                    
                    <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <h4 className="text-sm font-bold text-slate-700">Catalog Classification <span className="font-normal text-slate-400">(optional)</span></h4>
                      <p className="text-xs text-slate-500">Set to control where this bundle appears in category/brand pages and recommendations. If left blank, the bundle inherits the categories and brands of its component products.</p>
                      
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-slate-600">Category</label>
                          <input
                            type="text"
                            value={formData.category}
                            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                            className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                            placeholder="e.g. Notebooks"
                          />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-slate-600">Sub-category</label>
                          <input
                            type="text"
                            value={formData.subCategory}
                            onChange={(e) => setFormData({ ...formData, subCategory: e.target.value })}
                            className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                            placeholder="e.g. Spiral Notebooks"
                          />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-slate-600">Brand</label>
                          <input
                            type="text"
                            value={formData.brand}
                            onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                            className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                            placeholder="e.g. Classmate"
                          />
                        </div>
                      </div>

                      <div className="mt-3">
                        <label className="mb-1 block text-xs font-semibold text-slate-600">Search Tags <span className="font-normal text-slate-400">(comma-separated)</span></label>
                        <input
                          type="text"
                          value={Array.isArray(formData.searchTags) ? formData.searchTags.join(', ') : formData.searchTags || ''}
                          onChange={(e) => setFormData({ ...formData, searchTags: (e.target.value as any) })}
                          className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                          placeholder="e.g. school-kit, starter-pack, summer-sale"
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        id="bundleActive"
                        checked={formData.isActive}
                        onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                        className="h-4 w-4 rounded border-slate-300 text-indigo-600"
                      />
                      <label htmlFor="bundleActive" className="cursor-pointer text-sm text-slate-700">
                        Active (visible to customers)
                      </label>
                    </div>
                  </div>

                  {/* Selected items */}
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <h4 className="mb-3 text-sm font-bold text-slate-700">
                      Bundle Items ({formData.items.length})
                    </h4>
                    {formData.items.length === 0 ? (
                      <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-xs text-slate-400">
                        Search and add products from the right panel →
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {formData.items.map((item) => {
                          const p = getProductById(item.productId);
                          return (
                            <div
                              key={item.productId}
                              className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-2"
                            >
                              <div className="h-9 w-9 flex-shrink-0 overflow-hidden rounded border border-slate-200 bg-slate-100">
                                {p?.images?.[0] && (
                                  <img
                                    src={imgSrc(p.images[0]) || ''}
                                    className="h-full w-full object-cover"
                                    alt=""
                                  />
                                )}
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="truncate text-xs font-semibold text-slate-800">
                                  {p?.name ?? item.productId}
                                </div>
                                <div className="text-[10px] text-slate-500">
                                  MRP ₹{p?.mrp ?? '?'} × {item.quantity} = ₹
                                  {((p?.mrp ?? 0) * item.quantity).toFixed(2)}
                                </div>
                              </div>
                              <input
                                type="number"
                                min={1}
                                value={item.quantity}
                                onChange={(e) => updateItemQty(item.productId, parseInt(e.target.value) || 1)}
                                className="w-14 rounded border border-slate-200 px-2 py-1 text-center text-xs"
                              />
                              <button
                                type="button"
                                onClick={() => removeItemFromBundle(item.productId)}
                                className="ml-1 text-rose-400 hover:text-rose-600"
                              >
                                ✕
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* Right: product picker */}
                <div className="flex h-full max-h-[480px] flex-col overflow-hidden p-6">
                  <h4 className="mb-2 text-sm font-bold text-slate-700">Add Products</h4>
                  <input
                    type="text"
                    placeholder="Search by name or SKU…"
                    value={productSearch}
                    onChange={(e) => setProductSearch(e.target.value)}
                    className="mb-3 w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
                  />
                  <div className="flex-1 space-y-1.5 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-2">
                    {filteredProducts.map((p) => (
                      <div
                        key={p._id}
                        onClick={() => addProductToBundle(p)}
                        className="flex cursor-pointer items-center gap-3 rounded-lg border border-transparent bg-white p-2 transition-colors hover:border-indigo-200 hover:bg-indigo-50"
                      >
                        <div className="h-8 w-8 flex-shrink-0 overflow-hidden rounded border border-slate-200 bg-slate-100">
                          {p.images?.[0] && (
                            <img src={imgSrc(p.images[0]) || ''} className="h-full w-full object-cover" alt="" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-xs font-semibold text-slate-800">{p.name}</div>
                          <div className="text-[10px] uppercase tracking-tight text-slate-500">
                            {p.sku} • ₹{p.mrp}
                          </div>
                        </div>
                        <span className="text-xs font-medium text-indigo-600">+ Add</span>
                      </div>
                    ))}
                    {filteredProducts.length === 0 && (
                      <div className="py-8 text-center text-xs text-slate-400">
                        {productSearch ? 'No matching products' : 'All products already added'}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex justify-end gap-3 border-t border-slate-200 p-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-200 px-6 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-indigo-600 px-8 py-2 text-sm font-semibold text-white shadow-md transition-colors hover:bg-indigo-700 disabled:opacity-60"
                >
                  {saving ? 'Saving…' : editingBundle ? 'Save Changes' : 'Create Bundle'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
        </div>
      </div>
    </div>
  );
}
