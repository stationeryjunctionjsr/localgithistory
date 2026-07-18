'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';
import InfoButton from '@/components/InfoButton';

interface SearchTag {
  _id?: string;
  tagId?: string;
  name: string;
  type: string;
  isActive?: boolean;
  categories?: string[];
  subCategories?: string[];
  brands?: string[];
  collections?: string[];
  productIds?: string[];
  excludedProductIds?: string[];
  createdAt?: string;
  updatedAt?: string;
}

interface Category {
  _id: string;
  name: string;
  subCategories?: string[];
  isActive?: boolean;
}

interface Brand {
  _id: string;
  name: string;
  isActive?: boolean;
}

interface Collection {
  _id: string;
  name: string;
  isActive?: boolean;
}

interface Product {
  _id: string;
  name: string;
  sku: string;
  category?: string;
}

const emptyFormData = {
  name: '',
  type: 'Occasion',
  isActive: true,
  categories: [] as string[],
  subCategories: [] as string[],
  brands: [] as string[],
  collections: [] as string[],
  productIds: [] as string[],
};

export default function SearchTagsManagement() {
  const { user } = useAuth();
  const [tags, setTags] = useState<SearchTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTag, setEditingTag] = useState<SearchTag | null>(null);
  const [formData, setFormData] = useState({ ...emptyFormData });

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const getPageNumbers = (totalPages: number) => {
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

  // Association data
  const [allCategories, setAllCategories] = useState<Category[]>([]);
  const [allBrands, setAllBrands] = useState<Brand[]>([]);
  const [allCollections, setAllCollections] = useState<Collection[]>([]);
  const [productSearch, setProductSearch] = useState('');
  const [productResults, setProductResults] = useState<Product[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([]);
  const [searchingProducts, setSearchingProducts] = useState(false);

  // Available subcategories based on selected categories
  const availableSubCategories = allCategories
    .filter((c) => formData.categories.includes(c.name))
    .flatMap((c) => c.subCategories || []);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchTags();
      fetchAssociationData();
    }
  }, [user]);

  const fetchTags = async () => {
    try {
      const response = await api.get('/search-tags');
      setTags(response.data || []);
      setLoading(false);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch search tags');
      setLoading(false);
    }
  };

  const fetchAssociationData = async () => {
    try {
      const [catRes, brandRes, colRes] = await Promise.all([
        api.get('/categories/public'),
        api.get('/brands/public'),
        api.get('/collections/public'),
      ]);
      setAllCategories(catRes.data || []);
      setAllBrands(brandRes.data || []);
      setAllCollections(colRes.data || []);
    } catch (error) {
      console.error('Failed to fetch association data:', error);
    }
  };

  const searchProducts = useCallback(
    async (query: string) => {
      if (query.length < 2) {
        setProductResults([]);
        return;
      }
      setSearchingProducts(true);
      try {
        const response = await api.get(`/products?search=${encodeURIComponent(query)}&limit=10`);
        const products = response.data?.products || response.data || [];
        // Filter out already selected products
        setProductResults(products.filter((p: Product) => !formData.productIds.includes(p._id)));
      } catch (error) {
        console.error('Product search failed:', error);
      } finally {
        setSearchingProducts(false);
      }
    },
    [formData.productIds]
  );

  // Debounced product search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (productSearch) searchProducts(productSearch);
    }, 300);
    return () => clearTimeout(timer);
  }, [productSearch, searchProducts]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        categories: formData.categories,
        subCategories: formData.subCategories,
        brands: formData.brands,
        collections: formData.collections,
        productIds: formData.productIds,
      };
      if (editingTag?._id) {
        await api.put(`/search-tags/${editingTag._id}`, payload);
        toast.success('Tag updated successfully');
      } else {
        await api.post('/search-tags', payload);
        toast.success('Tag created successfully');
      }
      closeModal();
      fetchTags();
    } catch (error: any) {
      const errMsg =
        error.response?.data?.detail?.[0]?.msg ||
        error.response?.data?.message ||
        error.response?.data?.detail ||
        'Operation failed';
      toast.error(errMsg);
    }
  };

  const handleEdit = (tag: SearchTag) => {
    if (!tag._id) {
      toast.error('Cannot edit tag: Missing ID');
      return;
    }
    setEditingTag(tag);
    setFormData({
      name: tag.name,
      type: tag.type,
      isActive: tag.isActive !== false,
      categories: tag.categories || [],
      subCategories: tag.subCategories || [],
      brands: tag.brands || [],
      collections: tag.collections || [],
      productIds: tag.productIds || [],
    });
    // Load selected products info for display
    if (tag.productIds && tag.productIds.length > 0) {
      loadSelectedProducts(tag.productIds);
    } else {
      setSelectedProducts([]);
    }
    setShowModal(true);
  };

  const loadSelectedProducts = async (productIds: string[]) => {
    try {
      const response = await api.get('/products?limit=9999');
      const allProducts = response.data?.products || response.data || [];
      setSelectedProducts(allProducts.filter((p: Product) => productIds.includes(p._id)));
    } catch (error) {
      console.error('Failed to load selected products:', error);
    }
  };

  const handleToggleStatus = async (tag: SearchTag) => {
    if (!tag._id) {
      toast.error('Failed to update status: Missing ID');
      return;
    }
    try {
      await api.put(`/search-tags/${tag._id}`, { isActive: !tag.isActive });
      toast.success(`Tag ${tag.isActive ? 'disabled' : 'enabled'} successfully`);
      fetchTags();
    } catch (error: any) {
      const errMsg =
        error.response?.data?.detail?.[0]?.msg ||
        error.response?.data?.message ||
        error.response?.data?.detail ||
        'Failed to update tag status';
      toast.error(errMsg);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingTag(null);
    setFormData({ ...emptyFormData });
    setSelectedProducts([]);
    setProductSearch('');
    setProductResults([]);
  };

  const addProduct = (product: Product) => {
    setFormData((prev) => ({ ...prev, productIds: [...prev.productIds, product._id] }));
    setSelectedProducts((prev) => [...prev, product]);
    setProductResults((prev) => prev.filter((p) => p._id !== product._id));
    setProductSearch('');
  };

  const removeProduct = (productId: string) => {
    setFormData((prev) => ({
      ...prev,
      productIds: prev.productIds.filter((id) => id !== productId),
    }));
    setSelectedProducts((prev) => prev.filter((p) => p._id !== productId));
  };

  const toggleArrayItem = (
    field: 'categories' | 'subCategories' | 'brands' | 'collections',
    value: string
  ) => {
    setFormData((prev) => {
      const arr = prev[field];
      const updated = arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value];
      // If removing a category, also remove its subcategories
      if (field === 'categories' && arr.includes(value)) {
        const cat = allCategories.find((c) => c.name === value);
        const subsToRemove = cat?.subCategories || [];
        return {
          ...prev,
          [field]: updated,
          subCategories: prev.subCategories.filter((s) => !subsToRemove.includes(s)),
        };
      }
      return { ...prev, [field]: updated };
    });
  };

  // Helper to count associations for a tag
  const getAssociationSummary = (tag: SearchTag): string => {
    const parts: string[] = [];
    if (tag.categories?.length) parts.push(`${tag.categories.length} cat`);
    if (tag.subCategories?.length) parts.push(`${tag.subCategories.length} subcat`);
    if (tag.brands?.length) parts.push(`${tag.brands.length} brand`);
    if (tag.collections?.length) parts.push(`${tag.collections.length} coll`);
    if (tag.productIds?.length) parts.push(`${tag.productIds.length} prod`);
    return parts.length > 0 ? parts.join(', ') : 'None';
  };

  const totalItems = tags.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedTags = tags.slice(startIndex, endIndex);

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow h-full flex flex-col min-h-0">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
              Search Tags Management <RefreshButton onRefresh={fetchTags} />
            </h1>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  closeModal();
                  setShowModal(true);
                }}
                className="rounded px-4 py-2 text-white"
                style={{
                  background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
                }}
              >
                Add Search Tag
              </button>
            </div>
          </div>

          <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
            <table className="w-full border-collapse">
              <thead className="sticky top-0 z-10 bg-gray-50 shadow-sm">
                <tr className="bg-gray-50">
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton info="The unique system-generated identifier for this search tag">Tag ID</InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton info="The display name of the search tag shown to customers">Name</InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton info="The category of the search tag: Occasion (e.g. Birthday), Intent (e.g. Gift), or Recipient (e.g. For Him)">Type</InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton info="Summary of how many categories, brands, collections, and products this tag is associated with">Associations</InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton info="Whether this search tag is currently active and visible to customers">Status</InfoButton>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <InfoButton info="Edit or enable/disable this search tag">Actions</InfoButton>
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedTags.length > 0 ? (
                  paginatedTags.map((tag) => (
                    <tr key={tag._id} className="hover:bg-gray-50">
                      <td className="border border-gray-200 p-2 text-sm font-bold text-blue-600">
                        {tag.tagId || 'N/A'}
                      </td>
                      <td className="border border-gray-200 p-2 font-medium text-gray-900">
                        {tag.name}
                      </td>
                      <td className="border border-gray-200 p-2">
                        <span
                          className={`rounded px-2 py-1 text-xs uppercase ${
                            tag.type === 'Occasion'
                              ? 'bg-blue-100 text-blue-800'
                              : tag.type === 'Intent'
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-pink-100 text-pink-800'
                          }`}
                        >
                          {tag.type}
                        </span>
                      </td>
                      <td className="border border-gray-200 p-2 text-sm text-gray-600">{getAssociationSummary(tag)}</td>
                      <td className="border border-gray-200 p-2">
                        <span
                          className={`rounded px-2 py-1 text-xs ${tag.isActive !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                        >
                          {tag.isActive !== false ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="border border-gray-200 p-2">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEdit(tag)}
                            className="rounded px-3 py-1 text-sm text-white"
                            style={{
                              background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                            }}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleToggleStatus(tag)}
                            className="rounded px-3 py-1 text-sm text-white"
                            style={{
                              background:
                                tag.isActive !== false
                                  ? 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)'
                                  : 'linear-gradient(135deg, #28A745 0%, #218838 100%)',
                            }}
                          >
                            {tag.isActive !== false ? 'Disable' : 'Enable'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="border border-gray-200 p-4 text-center text-gray-500">
                      No search tags found
                    </td>
                  </tr>
                )}
              </tbody>
        </table>
      </div>

      {/* Premium Pagination Controls */}
      {tags.length > 0 && (
        <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
          <div className="text-sm text-gray-700">
            Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
            <span className="font-semibold">{endIndex}</span> of{' '}
            <span className="font-semibold">{totalItems}</span> search tags
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
              {getPageNumbers(totalPages).map((page, index) => {
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

      {/* Create/Edit Modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          onClick={closeModal}
        >
          <div
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">{editingTag ? 'Edit Tag' : 'Add Tag'}</h3>
            <form onSubmit={handleSubmit}>
              {/* Basic Info */}
              <div className="mb-4 grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm font-medium">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    className="w-full rounded border px-3 py-2"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">Type *</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    className="w-full rounded border bg-white px-3 py-2"
                  >
                    <option value="Occasion">Occasion</option>
                    <option value="Intent">Intent</option>
                    <option value="Recipient">Recipient</option>
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.isActive}
                    onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                    className="mr-2"
                  />
                  Active
                </label>
              </div>

              {/* Associations Section */}
              <div className="mt-4 border-t pt-4">
                <h4 className="mb-3 text-lg font-semibold">Associations</h4>
                <p className="mb-4 text-sm text-gray-500">
                  Select which categories, subcategories, brands, collections, or products this tag
                  should be applied to. Products matching any of these associations will be tagged.
                </p>

                {/* Categories */}
                <div className="mb-4">
                  <label className="mb-2 block text-sm font-medium">Categories</label>
                  <div className="max-h-40 overflow-y-auto rounded border p-3">
                    {allCategories.length > 0 ? (
                      allCategories.map((cat) => (
                        <label
                          key={cat._id}
                          className="mb-1 flex cursor-pointer items-center rounded px-1 hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={formData.categories.includes(cat.name)}
                            onChange={() => toggleArrayItem('categories', cat.name)}
                            className="mr-2"
                          />
                          <span className="text-sm">{cat.name}</span>
                        </label>
                      ))
                    ) : (
                      <p className="text-sm text-gray-400">No categories available</p>
                    )}
                  </div>
                  {formData.categories.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {formData.categories.map((c) => (
                        <span
                          key={c}
                          className="flex items-center gap-1 rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800"
                        >
                          {c}
                          <button
                            type="button"
                            onClick={() => toggleArrayItem('categories', c)}
                            className="hover:text-blue-600"
                          >
                            &times;
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Sub-categories (shown only when categories are selected) */}
                {formData.categories.length > 0 && availableSubCategories.length > 0 && (
                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium">Sub-categories</label>
                    <div className="max-h-40 overflow-y-auto rounded border p-3">
                      {availableSubCategories.map((sub) => (
                        <label
                          key={sub}
                          className="mb-1 flex cursor-pointer items-center rounded px-1 hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={formData.subCategories.includes(sub)}
                            onChange={() => toggleArrayItem('subCategories', sub)}
                            className="mr-2"
                          />
                          <span className="text-sm">{sub}</span>
                        </label>
                      ))}
                    </div>
                    {formData.subCategories.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {formData.subCategories.map((s) => (
                          <span
                            key={s}
                            className="flex items-center gap-1 rounded-full bg-indigo-100 px-2 py-1 text-xs text-indigo-800"
                          >
                            {s}
                            <button
                              type="button"
                              onClick={() => toggleArrayItem('subCategories', s)}
                              className="hover:text-indigo-600"
                            >
                              &times;
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Brands */}
                <div className="mb-4">
                  <label className="mb-2 block text-sm font-medium">Brands</label>
                  <div className="max-h-40 overflow-y-auto rounded border p-3">
                    {allBrands.length > 0 ? (
                      allBrands.map((brand) => (
                        <label
                          key={brand._id}
                          className="mb-1 flex cursor-pointer items-center rounded px-1 hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={formData.brands.includes(brand.name)}
                            onChange={() => toggleArrayItem('brands', brand.name)}
                            className="mr-2"
                          />
                          <span className="text-sm">{brand.name}</span>
                        </label>
                      ))
                    ) : (
                      <p className="text-sm text-gray-400">No brands available</p>
                    )}
                  </div>
                  {formData.brands.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {formData.brands.map((b) => (
                        <span
                          key={b}
                          className="flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-xs text-green-800"
                        >
                          {b}
                          <button
                            type="button"
                            onClick={() => toggleArrayItem('brands', b)}
                            className="hover:text-green-600"
                          >
                            &times;
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Collections */}
                <div className="mb-4">
                  <label className="mb-2 block text-sm font-medium">Collections</label>
                  <div className="max-h-40 overflow-y-auto rounded border p-3">
                    {allCollections.length > 0 ? (
                      allCollections.map((col) => (
                        <label
                          key={col._id}
                          className="mb-1 flex cursor-pointer items-center rounded px-1 hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={formData.collections.includes(col._id)}
                            onChange={() => toggleArrayItem('collections', col._id)}
                            className="mr-2"
                          />
                          <span className="text-sm">{col.name}</span>
                        </label>
                      ))
                    ) : (
                      <p className="text-sm text-gray-400">No collections available</p>
                    )}
                  </div>
                  {formData.collections.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {formData.collections.map((colId) => {
                        const col = allCollections.find((c) => c._id === colId);
                        return (
                          <span
                            key={colId}
                            className="flex items-center gap-1 rounded-full bg-orange-100 px-2 py-1 text-xs text-orange-800"
                          >
                            {col?.name || colId}
                            <button
                              type="button"
                              onClick={() => toggleArrayItem('collections', colId)}
                              className="hover:text-orange-600"
                            >
                              &times;
                            </button>
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Products (searchable) */}
                <div className="mb-4">
                  <label className="mb-2 block text-sm font-medium">Individual Products</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={productSearch}
                      onChange={(e) => setProductSearch(e.target.value)}
                      placeholder="Search products by name or SKU..."
                      className="w-full rounded border px-3 py-2"
                    />
                    {searchingProducts && (
                      <div className="absolute right-3 top-2.5 text-sm text-gray-400">
                        Searching...
                      </div>
                    )}
                    {productResults.length > 0 && (
                      <div className="absolute z-10 max-h-48 w-full overflow-y-auto rounded-b border bg-white shadow-lg">
                        {productResults.map((product) => (
                          <button
                            key={product._id}
                            type="button"
                            onClick={() => addProduct(product)}
                            className="w-full border-b px-3 py-2 text-left text-sm last:border-b-0 hover:bg-gray-100"
                          >
                            <span className="font-medium">{product.name}</span>
                            <span className="ml-2 text-gray-500">({product.sku})</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {selectedProducts.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {selectedProducts.map((p) => (
                        <span
                          key={p._id}
                          className="flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-1 text-xs text-yellow-800"
                        >
                          {p.name} ({p.sku})
                          <button
                            type="button"
                            onClick={() => removeProduct(p._id)}
                            className="hover:text-yellow-600"
                          >
                            &times;
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-end gap-2 border-t pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded bg-gray-500 px-4 py-2 text-white hover:bg-gray-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded px-4 py-2 text-white"
                  style={{
                    background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
                  }}
                >
                  {editingTag ? 'Update' : 'Create'}
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
