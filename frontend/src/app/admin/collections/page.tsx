'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import CollectionVisibilityControls from '@/components/Admin/CollectionVisibilityControls';
import RefreshButton from '@/components/Admin/RefreshButton';

interface Collection {
  _id?: string;
  name: string;
  description?: string;
  imageUrl?: string;
  isActive: boolean;
  displayOrder: number;
  productIds: string[];
  visiblePages: string[];
  userSegments: string[];
  visibilityRules: any[];
}

interface Product {
  _id: string;
  name: string;
  sku: string;
  category: string;
  mrp: number;
  images?: string[];
}

export default function CollectionsManagement() {
  const { user } = useAuth();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null);

  const [formData, setFormData] = useState<Collection>({
    name: '',
    description: '',
    imageUrl: '',
    isActive: true,
    displayOrder: 0,
    productIds: [],
    visiblePages: ['Home'],
    userSegments: ['all'],
    visibilityRules: [],
  });

  // eslint-disable-next-line unused-imports/no-unused-vars
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
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

  const [categoryFilter, setCategoryFilter] = useState('all');

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchCollections();
      fetchProducts();
      fetchCategories();
      fetchPageInfo();
    }
  }, [user]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/collection-management');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchCollections = async () => {
    try {
      const response = await api.get('/collections');
      setCollections(response.data || []);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      toast.error('Failed to fetch collections');
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await api.get('/products');
      setProducts(response.data.products || response.data || []);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      toast.error('Failed to fetch products');
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories/public');
      setCategories(response.data || []);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      console.error('Failed to fetch categories');
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingImage(true);
    try {
      const formDataUpload = new FormData();
      formDataUpload.append('image', file);

      const response = await api.post('/collections/upload-image', formDataUpload, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setFormData({ ...formData, imageUrl: response.data.imageUrl });
      toast.success('Image uploaded successfully');
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to upload image');
    } finally {
      setUploadingImage(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingCollection?._id) {
        await api.put(`/collections/${editingCollection._id}`, formData);
        toast.success('Collection updated successfully');
      } else {
        await api.post('/collections', formData);
        toast.success('Collection created successfully');
      }
      setShowModal(false);
      fetchCollections();
      resetForm();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleEdit = (collection: Collection) => {
    setEditingCollection(collection);
    setFormData({
      name: collection.name,
      description: collection.description || '',
      imageUrl: collection.imageUrl || '',
      isActive: collection.isActive,
      displayOrder: collection.displayOrder || 0,
      productIds: collection.productIds || [],
      visiblePages: collection.visiblePages || [],
      userSegments: collection.userSegments || ['all'],
      visibilityRules: collection.visibilityRules || [],
    });
    setShowModal(true);
  };

  const handleToggleStatus = async (collection: Collection) => {
    const newStatus = !collection.isActive;
    if (!confirm(`Are you sure you want to ${newStatus ? 'unhide' : 'hide'} this collection?`))
      return;
    try {
      await api.put(`/collections/${collection._id}`, { isActive: newStatus });
      toast.success(`Collection ${newStatus ? 'unhidden' : 'hidden'} successfully`);
      fetchCollections();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      toast.error(`Failed to ${newStatus ? 'unhide' : 'hide'} collection`);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this collection permanently?')) return;
    try {
      await api.delete(`/collections/${id}`);
      toast.success('Collection deleted successfully');
      fetchCollections();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      toast.error('Failed to delete collection');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      imageUrl: '',
      isActive: true,
      displayOrder: 0,
      productIds: [],
      visiblePages: ['Home'],
      userSegments: ['all'],
      visibilityRules: [],
    });
    setEditingCollection(null);
    setImageFile(null);
  };

  const toggleProductInCollection = (productId: string) => {
    const currentIds = [...formData.productIds];
    const index = currentIds.indexOf(productId);
    if (index === -1) {
      currentIds.push(productId);
    } else {
      currentIds.splice(index, 1);
    }
    setFormData({ ...formData, productIds: currentIds });
  };

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.sku || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || p.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  const totalItems = collections.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedCollections = collections.slice(startIndex, endIndex);


  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow h-full flex flex-col min-h-0">
          <div className="mb-6 flex flex-shrink-0 items-center justify-between gap-4">
            <div>
              <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.page?.description
                      ? pageInfo.page.description
                      : undefined
                  }
                >
                  Collections Management
                </InfoButton>
                <RefreshButton onRefresh={fetchCollections} />
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Create and manage curated product collections
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  resetForm();
                  setShowModal(true);
                }}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-white transition-colors hover:bg-indigo-700"
              >
                <span className="text-xl">+</span> Add Collection
              </button>
            </div>
          </div>

          <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
            <table className="w-full border-collapse text-left">
              <thead className="sticky top-0 z-10 bg-gray-50 shadow-sm">
                <tr className="bg-gray-50">
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.image
                          ? pageInfo.columns.image
                          : undefined
                      }
                    >
                      Image
                    </InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.name
                          ? pageInfo.columns.name
                          : undefined
                      }
                    >
                      Name
                    </InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.products
                          ? pageInfo.columns.products
                          : undefined
                      }
                    >
                      Products
                    </InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.order
                          ? pageInfo.columns.order
                          : undefined
                      }
                    >
                      Order
                    </InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.visibility
                          ? pageInfo.columns.visibility
                          : undefined
                      }
                    >
                      Visibility
                    </InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.status
                          ? pageInfo.columns.status
                          : undefined
                      }
                    >
                      Status
                    </InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.actions
                          ? pageInfo.columns.actions
                          : undefined
                      }
                    >
                      Actions
                    </InfoButton>
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedCollections.map((collection) => (
                  <tr key={collection._id} className="hover:bg-gray-50">
                    <td className="border border-gray-200 p-2">
                      {collection.imageUrl ? (
                        <img
                          src={
                            collection.imageUrl.startsWith('http')
                              ? collection.imageUrl
                              : `${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '')}${collection.imageUrl}`
                          }
                          className="h-12 w-12 rounded border border-slate-200 object-cover"
                          alt=""
                        />
                      ) : (
                        <div className="flex h-12 w-12 items-center justify-center rounded bg-slate-100 text-xs text-slate-400">
                          No Image
                        </div>
                      )}
                    </td>
                    <td className="border border-gray-200 p-2">
                      <div className="font-medium text-slate-800">{collection.name}</div>
                      <div className="max-w-xs truncate text-xs text-slate-500">
                        {collection.description}
                      </div>
                    </td>
                    <td className="border border-gray-200 p-2">
                      <span className="rounded-full border border-indigo-100 bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700">
                        {collection.productIds?.length || 0} Products
                      </span>
                    </td>
                    <td className="border border-gray-200 p-2 text-slate-600">{collection.displayOrder}</td>
                    <td className="border border-gray-200 p-2">
                      <div className="flex flex-col gap-1">
                        <div className="flex flex-wrap gap-1">
                          {(collection.visiblePages || []).map((page) => (
                            <span
                              key={page}
                              className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600"
                            >
                              {page}
                            </span>
                          ))}
                        </div>
                        {collection.visibilityRules && collection.visibilityRules.length > 0 && (
                          <div className="border-tl-2 mt-1 flex flex-col gap-0.5 border-slate-100 pl-1 pt-1">
                            {collection.visibilityRules.map((rule: any, idx: number) => (
                              <div key={idx} className="font-mono text-[9px] text-slate-500">
                                • {rule.pageType}:{' '}
                                {rule.pageIds?.length > 0 ? rule.pageIds.join(', ') : 'All'}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="border border-gray-200 p-2">
                      <span
                        className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
                          collection.isActive
                            ? 'border-emerald-100 bg-emerald-50 text-emerald-700'
                            : 'border-slate-200 bg-slate-100 text-slate-600'
                        }`}
                      >
                        {collection.isActive ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="border border-gray-200 p-2">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(collection)}
                          className="px-2 py-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
                        >
                          Edit
                        </button>
                        {collection.isActive ? (
                          <button
                            onClick={() => handleToggleStatus(collection)}
                            className="px-2 py-1 text-sm font-medium text-amber-600 hover:text-amber-800"
                          >
                            Hide
                          </button>
                        ) : (
                          <button
                            onClick={() => handleToggleStatus(collection)}
                            className="px-2 py-1 text-sm font-medium text-emerald-600 hover:text-emerald-800"
                          >
                            Unhide
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(collection._id!)}
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
                      No collections found. Create your first collection!
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

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="animate-in fade-in zoom-in flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl duration-200">
            <div className="flex items-center justify-between border-b border-slate-200 bg-white p-6">
              <h2 className="text-xl font-bold text-slate-800">
                {editingCollection ? 'Edit Collection' : 'New Collection'}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-2xl text-slate-400 hover:text-slate-600"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex-1 space-y-6 overflow-y-auto p-6">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div className="space-y-6">
                  <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                    <h4 className="text-sm font-bold text-slate-700">General Information</h4>
                    <div className="space-y-4">
                      <div>
                        <label className="mb-1.5 block inline-flex items-baseline gap-1 text-sm font-semibold text-slate-700">
                          <InfoButton
                            info={
                              user?.role === 'super_admin' && pageInfo.columns?.name
                                ? pageInfo.columns.name
                                : undefined
                            }
                          >
                            Collection Name *
                          </InfoButton>
                        </label>
                        <input
                          type="text"
                          required
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                          className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
                          placeholder="e.g. Summer Specials"
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block inline-flex items-baseline gap-1 text-sm font-semibold text-slate-700">
                          <InfoButton
                            info={
                              user?.role === 'super_admin' && pageInfo.columns?.description
                                ? pageInfo.columns.description
                                : undefined
                            }
                          >
                            Description
                          </InfoButton>
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) =>
                            setFormData({ ...formData, description: e.target.value })
                          }
                          className="h-24 w-full rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
                          placeholder="Describe this collection..."
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                    <h4 className="text-sm font-bold text-slate-700">Display Settings</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="mb-1.5 block inline-flex items-baseline gap-1 text-sm font-semibold text-slate-600 text-slate-700">
                          <InfoButton
                            info={
                              user?.role === 'super_admin' && pageInfo.columns?.order
                                ? pageInfo.columns.order
                                : undefined
                            }
                          >
                            Display Order
                          </InfoButton>
                        </label>
                        <input
                          type="number"
                          value={formData.displayOrder}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              displayOrder: parseInt(e.target.value) || 0,
                            })
                          }
                          className="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block text-sm font-semibold text-slate-600 text-slate-700">
                          Status
                        </label>
                        <div className="mt-2 flex h-[42px] items-center gap-3">
                          <input
                            type="checkbox"
                            id="isActiveCol"
                            checked={formData.isActive}
                            onChange={(e) =>
                              setFormData({ ...formData, isActive: e.target.checked })
                            }
                            className="h-4 w-4 cursor-pointer rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <label
                            htmlFor="isActiveCol"
                            className="cursor-pointer text-sm text-slate-600"
                          >
                            Active Collection
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-sm font-bold text-slate-700">Visibility Targeting</h4>
                    <CollectionVisibilityControls
                      userSegments={formData.userSegments}
                      visibilityRules={formData.visibilityRules}
                      onChange={(data) => setFormData({ ...formData, ...data })}
                    />
                  </div>

                  <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                    <h4 className="text-sm font-bold text-slate-700">Cover Image</h4>
                    <div className="flex items-center gap-4">
                      {formData.imageUrl && (
                        <div className="group relative h-20 w-20 flex-shrink-0 overflow-hidden rounded-lg border border-slate-200 bg-white">
                          <img
                            src={
                              formData.imageUrl.startsWith('http')
                                ? formData.imageUrl
                                : `${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '')}${formData.imageUrl}`
                            }
                            className="h-full w-full object-cover"
                            alt=""
                          />
                        </div>
                      )}
                      <div className="flex-1">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageUpload}
                          className="hidden"
                          id="colImgUpload"
                          disabled={uploadingImage}
                        />
                        <label
                          htmlFor="colImgUpload"
                          className={`inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition-all hover:border-indigo-300 hover:bg-white ${uploadingImage ? 'cursor-not-allowed opacity-50' : ''}`}
                        >
                          {uploadingImage ? 'Uploading...' : 'Click to Upload Image'}
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex h-full flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
                  <div className="border-b border-slate-200 bg-white p-4">
                    <label className="mb-2 block text-sm font-semibold text-slate-700">
                      Select Products ({formData.productIds.length} chosen)
                    </label>
                    <div className="space-y-2">
                      <input
                        type="text"
                        placeholder="Search products..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm"
                      />
                      <select
                        value={categoryFilter}
                        onChange={(e) => setCategoryFilter(e.target.value)}
                        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm"
                      >
                        <option value="all">All Categories</option>
                        {categories.map((c) => (
                          <option key={c.name} value={c.name}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div
                    className="flex-1 space-y-1 overflow-y-auto bg-slate-50 p-2"
                    style={{ maxHeight: '400px' }}
                  >
                    {filteredProducts.map((p) => (
                      <div
                        key={p._id}
                        onClick={() => toggleProductInCollection(p._id)}
                        className={`flex cursor-pointer items-center gap-3 rounded-lg border p-2 transition-colors ${
                          formData.productIds.includes(p._id)
                            ? 'border-indigo-200 bg-indigo-50 hover:bg-indigo-100'
                            : 'border-transparent bg-white hover:border-slate-300 hover:bg-white'
                        }`}
                      >
                        <div className="h-8 w-8 flex-shrink-0 overflow-hidden rounded border border-slate-200 bg-slate-200">
                          {p.images?.[0] && (
                            <img
                              src={
                                p.images[0].startsWith('http')
                                  ? p.images[0]
                                  : `${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '')}${p.images[0]}`
                              }
                              className="h-full w-full object-cover"
                              alt=""
                            />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-xs font-semibold text-slate-800">
                            {p.name}
                          </div>
                          <div className="text-[10px] uppercase tracking-tight text-slate-500">
                            {p.sku} | ₹{p.mrp}
                          </div>
                        </div>
                        <div
                          className={`flex h-5 w-5 items-center justify-center rounded-full border ${
                            formData.productIds.includes(p._id)
                              ? 'border-indigo-600 bg-indigo-600 text-white'
                              : 'border-slate-300'
                          }`}
                        >
                          {formData.productIds.includes(p._id) && (
                            <span className="text-[10px]">✓</span>
                          )}
                        </div>
                      </div>
                    ))}
                    {filteredProducts.length === 0 && (
                      <div className="py-8 text-center text-xs text-slate-400">
                        No products found for this filter.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 border-t border-slate-200 pt-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-200 px-6 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-8 py-2 text-sm font-semibold text-white shadow-md transition-colors hover:bg-indigo-700"
                >
                  {editingCollection ? 'Save Changes' : 'Create Collection'}
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
