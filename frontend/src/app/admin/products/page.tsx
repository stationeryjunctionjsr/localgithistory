'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import { formatDateIST } from '@/utils/dateUtils';
import SearchableSelect from '@/components/SearchableSelect';
import RefreshButton from '@/components/Admin/RefreshButton';

// interface QuantityDiscount {
//   quantity: number;
//   discount: number;
// }

interface Product {
  _id?: string;
  name: string;
  description?: string;
  sku?: string;
  productIdFormatted?: string;
  category: string;
  subCategory?: string; // Sub-category support
  brand?: string;
  mrp: number; // MRP per unit (retail; business when selling by unit)
  mrpPerCase?: number | null; // MRP per case (business only)
  quantityPerCase?: number | null; // Units per case
  stock?: number; // Total units (reduced by units or by cases × quantityPerCase)
  images?: string[]; // Array of image URLs
  videos?: string[]; // Array of video URLs
  // quantityDiscounts?: QuantityDiscount[]; // [{quantity: number, discount: number}]
  isActive?: boolean;
  variations?: any[]; // Product variations
  variantAttributes?: string[];
  variantCombinations?: any[];
  details?: any; // Additional product details
  searchTags?: string[]; // Resolved search tags from association rules
}

// Per-product search tag override component
function SearchTagManager({ productId, onUpdate }: { productId: string; onUpdate: () => void }) {
  const [resolvedTags, setResolvedTags] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<{ _id: string; name: string; type: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    fetchProductTags();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId]);

  const fetchProductTags = async () => {
    try {
      const response = await api.get(`/products/${productId}/search-tags`);
      setResolvedTags(response.data.resolvedTags || []);
      setAllTags(response.data.allTags || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch product search tags:', error);
      setLoading(false);
    }
  };

  const handleAddTag = async (tagId: string) => {
    try {
      await api.post(`/products/${productId}/search-tags`, { searchTagId: tagId });
      toast.success('Search tag added to product');
      fetchProductTags();
      onUpdate();
      setShowDropdown(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add tag');
    }
  };

  const handleRemoveTag = async (tagName: string) => {
    // Find the tag ID by name
    const tag = allTags.find((t) => t.name === tagName);
    if (!tag) {
      toast.error('Tag not found');
      return;
    }
    try {
      await api.delete(`/products/${productId}/search-tags/${tag._id}`);
      toast.success('Search tag removed from product');
      fetchProductTags();
      onUpdate();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to remove tag');
    }
  };

  // Tags available to add (not already resolved on the product)
  const availableToAdd = allTags.filter((t) => !resolvedTags.includes(t.name));

  if (loading) return <div className="text-sm text-gray-400">Loading tags...</div>;

  return (
    <div className="mt-4 border-t pt-4">
      <h4 className="mb-2 text-sm font-semibold">Search Tags</h4>
      <p className="mb-3 text-xs text-gray-500">
        Tags resolved from association rules. You can add or remove tags for this product
        individually.
      </p>
      <div className="mb-3 flex flex-wrap gap-2">
        {resolvedTags.length > 0 ? (
          resolvedTags.map((tagName, idx) => (
            <span
              key={idx}
              className="flex items-center gap-1 rounded-full bg-purple-100 px-2.5 py-1 text-xs text-purple-800"
            >
              {tagName}
              <button
                type="button"
                onClick={() => handleRemoveTag(tagName)}
                className="ml-0.5 font-bold hover:text-purple-600"
                title="Remove this tag from product"
              >
                &times;
              </button>
            </span>
          ))
        ) : (
          <span className="text-xs text-gray-400">No search tags</span>
        )}
      </div>
      <div className="relative inline-block">
        <button
          type="button"
          onClick={() => setShowDropdown(!showDropdown)}
          className="rounded border border-purple-300 px-3 py-1 text-sm text-purple-600 hover:bg-purple-50"
        >
          + Add Tag
        </button>
        {showDropdown && availableToAdd.length > 0 && (
          <div className="absolute z-20 mt-1 max-h-48 min-w-[200px] overflow-y-auto rounded border bg-white shadow-lg">
            {availableToAdd.map((tag) => (
              <button
                key={tag._id}
                type="button"
                onClick={() => handleAddTag(tag._id)}
                className="w-full border-b px-3 py-2 text-left text-sm last:border-b-0 hover:bg-gray-100"
              >
                <span className="font-medium">{tag.name}</span>
                <span
                  className={`ml-2 rounded px-1.5 py-0.5 text-xs ${
                    tag.type === 'Occasion'
                      ? 'bg-blue-100 text-blue-700'
                      : tag.type === 'Intent'
                        ? 'bg-purple-100 text-purple-700'
                        : 'bg-pink-100 text-pink-700'
                  }`}
                >
                  {tag.type}
                </span>
              </button>
            ))}
          </div>
        )}
        {showDropdown && availableToAdd.length === 0 && (
          <div className="absolute z-20 mt-1 min-w-[200px] rounded border bg-white px-3 py-2 text-sm text-gray-500 shadow-lg">
            All tags already assigned
          </div>
        )}
      </div>
    </div>
  );
}

export default function ProductManagement() {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [searchTagsModalProductId, setSearchTagsModalProductId] = useState<string | null>(null);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [newAttributeName, setNewAttributeName] = useState('');
  const [attributeValues, setAttributeValues] = useState<Record<string, string[]>>({});
  const [newValueForAttr, setNewValueForAttr] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState<Product>({
    name: '',
    description: '',
    category: '',
    subCategory: '',
    brand: '',
    mrp: 0,
    mrpPerCase: undefined,
    quantityPerCase: undefined,
    stock: 0,
    images: [],
    videos: [],
    // quantityDiscounts: [],
    variantAttributes: [],
    variantCombinations: [],
  });
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [uploadingImages, setUploadingImages] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);
  const [managedBrands, setManagedBrands] = useState<{ _id: string; name: string }[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 50;

  const getPageNumbers = () => {
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

  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });
  const [coupons, setCoupons] = useState<any[]>([]);
  const [collections, setCollections] = useState<any[]>([]);
  const [discountModal, setDiscountModal] = useState<{
    isOpen: boolean;
    product: any | null;
    type: 'retail' | 'business';
  }>({
    isOpen: false,
    product: null,
    type: 'retail',
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      if (debouncedSearch !== searchTerm) {
        setDebouncedSearch(searchTerm);
        setCurrentPage(1);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm, debouncedSearch]);

  useEffect(() => {
    setCurrentPage(1);
  }, [categoryFilter, statusFilter]);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchCategories();
      fetchManagedBrands();
      fetchPageInfo();
      fetchCoupons();
      fetchCollections();
    }
  }, [user]);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchProducts();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, currentPage, debouncedSearch, categoryFilter, statusFilter]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/product-management');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchManagedBrands = async () => {
    try {
      const res = await api.get('/brands/public');
      setManagedBrands(Array.isArray(res.data) ? res.data : res.data?.brands || []);
    } catch (e) {
      console.error('Failed to fetch brands', e);
      setManagedBrands([]);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories/public');
      setCategories(response.data || []);
    } catch (error) {
      console.error('Failed to fetch categories', error);
      // If category API fails, fall back to extracting from products
      // This will be handled in the form rendering
    }
  };

  const fetchProducts = async () => {
    try {
      const params = new URLSearchParams();
      params.append('page', currentPage.toString());
      params.append('limit', '50');
      if (debouncedSearch) params.append('search', debouncedSearch);
      if (categoryFilter !== 'all') params.append('category', categoryFilter);
      if (statusFilter !== 'all') params.append('status', statusFilter);

      const response = await api.get(`/products?${params.toString()}`);
      setProducts(response.data.products || response.data || []);
      const count = response.data.totalCount || response.data.length || 0;
      setTotalItems(count);
      setTotalPages(Math.ceil(count / 50) || 1);
      setLoading(false);
    } catch (_error: any) {
      toast.error('Failed to fetch products');
      setLoading(false);
    }
  };

  const fetchCoupons = async () => {
    try {
      const response = await api.get('/coupons');
      setCoupons(response.data || []);
    } catch (error) {
      console.error('Failed to fetch coupons', error);
    }
  };

  const fetchCollections = async () => {
    try {
      const response = await api.get('/collections');
      setCollections(response.data || []);
    } catch (error) {
      console.error('Failed to fetch collections', error);
    }
  };

  const getApplicableDiscounts = (product: Product, type: 'retail' | 'business') => {
    return coupons.filter((coupon) => {
      // Basic checks
      if (!coupon.isActive) return false;

      // Role-based filtering to match DiscountManagement
      if (type === 'retail') {
        if (
          !(
            coupon.applicableRoles?.includes('customer') ||
            (!coupon.applicableRoles?.includes('wholesaler') &&
              !coupon.applicableRoles?.includes('customer'))
          )
        )
          return false;
      } else {
        if (!coupon.applicableRoles?.includes('wholesaler')) return false;
      }

      const now = new Date();
      if (coupon.validFrom && new Date(coupon.validFrom) > now) return false;
      if (coupon.validUntil && new Date(coupon.validUntil) < now) return false;

      // Applies to logic
      const { appliesToType, appliesToValueIds } = coupon;
      if (appliesToType === 'all') return true;
      if (!appliesToValueIds || appliesToValueIds.length === 0) return appliesToType === 'all';

      if (appliesToType === 'categories') {
        return (appliesToValueIds || []).some((id: string) => {
          const cat = categories.find((c) => c._id === id);
          return cat && cat.name === product.category;
        });
      }
      if (appliesToType === 'subCategories') {
        return (appliesToValueIds || []).includes(product.subCategory);
      }
      if (appliesToType === 'brands') {
        return (appliesToValueIds || []).some((id: string) => {
          const brand = managedBrands.find((b) => b._id === id);
          return brand && brand.name === product.brand;
        });
      }
      if (appliesToType === 'products') {
        return (appliesToValueIds || []).includes(product._id);
      }
      if (appliesToType === 'collections') {
        return (appliesToValueIds || []).some((id: string) => {
          const col = collections.find((c) => c._id === id);
          if (!col || !col.productIds) return false;
          return col.productIds.some((pid: any) => String(pid) === String(product._id));
        });
      }
      return false;
    });
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]:
        name === 'mrp' || name === 'mrpPerCase' || name === 'stock' || name === 'quantityPerCase'
          ? value === ''
            ? name === 'mrpPerCase' || name === 'quantityPerCase'
              ? undefined
              : 0
            : name === 'quantityPerCase'
              ? parseInt(value, 10)
              : parseFloat(value)
          : value,
    });
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setUploadingImages(true);
    try {
      const formDataUpload = new FormData();
      files.forEach((file) => {
        formDataUpload.append('images', file);
      });

      const response = await api.post('/products/upload-images', formDataUpload, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const newImageUrls = response.data.images || [];
      setImageFiles([...imageFiles, ...files]);
      setFormData({
        ...formData,
        images: [...(formData.images || []), ...newImageUrls],
      });
    } catch (error: any) {
      toast.error('Failed to upload images: ' + (error.response?.data?.message || error.message));
    } finally {
      setUploadingImages(false);
      e.target.value = '';
    }
  };

  const removeProductImage = (index: number) => {
    const newImages = formData.images?.filter((_, i) => i !== index) || [];
    setFormData({
      ...formData,
      images: newImages,
    });
  };

  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setVideoFiles(files);
    const videoUrls = files.map((file) => URL.createObjectURL(file));
    setFormData({ ...formData, videos: [...(formData.videos || []), ...videoUrls] });
  };

  // const handleQuantityDiscountChange = (index: number, field: string, value: string) => {
  //   const newDiscounts = [...(formData.quantityDiscounts || [])];
  //   if (!newDiscounts[index]) {
  //     newDiscounts[index] = { quantity: 0, discount: 0 };
  //   }
  //   newDiscounts[index] = {
  //     ...newDiscounts[index],
  //     [field]: parseFloat(value) || 0,
  //   };
  //   setFormData({ ...formData, quantityDiscounts: newDiscounts });
  // };

  // const addQuantityDiscount = () => {
  //   setFormData({
  //     ...formData,
  //     quantityDiscounts: [...(formData.quantityDiscounts || []), { quantity: 0, discount: 0 }],
  //   });
  // };

  // const removeQuantityDiscount = (index: number) => {
  //   const newDiscounts = (formData.quantityDiscounts || []).filter((_, i) => i !== index);
  //   setFormData({ ...formData, quantityDiscounts: newDiscounts });
  // };

  // Variant Management Functions
  const addVariantAttribute = () => {
    if (newAttributeName && !formData.variantAttributes?.includes(newAttributeName)) {
      setFormData({
        ...formData,
        variantAttributes: [...(formData.variantAttributes || []), newAttributeName],
      });
      setAttributeValues({ ...attributeValues, [newAttributeName]: [] });
      setNewValueForAttr({ ...newValueForAttr, [newAttributeName]: '' });
      setNewAttributeName('');
    }
  };

  const addAttributeValue = (attr: string) => {
    const value = newValueForAttr[attr]?.trim();
    if (value && !attributeValues[attr]?.includes(value)) {
      setAttributeValues({
        ...attributeValues,
        [attr]: [...(attributeValues[attr] || []), value],
      });
      setNewValueForAttr({ ...newValueForAttr, [attr]: '' });
    }
  };

  const removeAttributeValue = (attr: string, valToRemove: string) => {
    setAttributeValues({
      ...attributeValues,
      [attr]: attributeValues[attr].filter((v) => v !== valToRemove),
    });
  };

  const removeVariantAttribute = (attr: string) => {
    setFormData({
      ...formData,
      variantAttributes: formData.variantAttributes?.filter((a) => a !== attr) || [],
      variantCombinations: [], // Reset combinations as they depend on attributes
    });
  };

  const generateCombinations = () => {
    const attrs = formData.variantAttributes || [];
    if (attrs.length === 0) return;

    const attrValues = attrs.map((attr) => attributeValues[attr] || []);

    if (attrValues.some((vals) => vals.length === 0)) {
      toast.error('Please enter values for all attributes');
      return;
    }

    const combinations: any[] = [];
    const helper = (idx: number, current: any) => {
      if (idx === attrs.length) {
        combinations.push({
          attributes: current,
          price: formData.mrp,
          pricePerCase: formData.mrpPerCase || 0,
          stock: 0,
          sku: `NEW-${Object.values(current).join('-').replace(/\s+/g, '')}`,
        });
        return;
      }
      for (const val of attrValues[idx]) {
        helper(idx + 1, { ...current, [attrs[idx]]: val });
      }
    };

    helper(0, {});
    setFormData({ ...formData, variantCombinations: combinations, stock: 0 });
  };

  const updateVariant = (index: number, field: string, value: any) => {
    const newCombos = [...(formData.variantCombinations || [])];
    newCombos[index] = { ...newCombos[index], [field]: value };

    // Update total stock if stock was changed
    let updatedStock = formData.stock;
    if (field === 'stock') {
      updatedStock = newCombos.reduce((sum, combo) => sum + (parseInt(combo.stock) || 0), 0);
    }

    setFormData({
      ...formData,
      variantCombinations: newCombos,
      stock: updatedStock,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const submitData = {
        ...formData,
        mrp: parseFloat(formData.mrp.toString()) || 0,
        mrpPerCase: formData.mrpPerCase != null ? parseFloat(formData.mrpPerCase.toString()) : null,
        quantityPerCase:
          formData.quantityPerCase != null
            ? parseInt(formData.quantityPerCase.toString(), 10)
            : null,
        stock: formData.stock != null ? parseInt(formData.stock.toString()) : 0,
        isActive: formData.isActive !== undefined ? formData.isActive : true,
      };

      if (editingProduct?._id) {
        await api.put(`/products/${editingProduct._id}`, submitData);
        toast.success('Product updated successfully');
      } else {
        await api.post('/products', submitData);
        toast.success('Product created successfully');
      }
      setShowModal(false);
      setEditingProduct(null);
      resetForm();
      fetchProducts();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed');
    }
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name,
      description: product.description || '',
      category: product.category,
      subCategory: product.subCategory || '',
      brand: product.brand || '',
      mrp: product.mrp || 0,
      mrpPerCase: product.mrpPerCase ?? undefined,
      quantityPerCase: product.quantityPerCase ?? undefined,
      stock: product.stock,
      images: product.images || [],
      videos: product.videos || [],
      // quantityDiscounts: product.quantityDiscounts || [],
      isActive: product.isActive !== undefined ? product.isActive : true,
      variantAttributes: product.variantAttributes || [],
      variantCombinations: product.variantCombinations || [],
    });

    const valuesMap: Record<string, string[]> = {};
    const inputMap: Record<string, string> = {};
    if (product.variantAttributes && product.variantCombinations) {
      product.variantAttributes.forEach((attr) => {
        const values = new Set<string>();
        product.variantCombinations?.forEach((combo) => {
          if (combo.attributes[attr]) values.add(combo.attributes[attr]);
        });
        valuesMap[attr] = Array.from(values);
        inputMap[attr] = '';
      });
    }
    setAttributeValues(valuesMap);
    setNewValueForAttr(inputMap);

    setImageFiles([]);
    setVideoFiles([]);
    setShowModal(true);
  };

  // Removed handleDelete - products should not be deleted, only disabled
  const _handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this product?')) return;
    try {
      await api.delete(`/products/${id}`);
      toast.success('Product deleted successfully');
      fetchProducts();
    } catch (_error: any) {
      toast.error('Failed to delete product');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: '',
      subCategory: '',
      brand: '',
      mrp: 0,
      mrpPerCase: undefined,
      quantityPerCase: undefined,
      stock: 0,
      images: [],
      videos: [],
      // quantityDiscounts: [],
      variantAttributes: [],
      variantCombinations: [],
    });
    setAttributeValues({});
    setImageFiles([]);
    setVideoFiles([]);
  };

  const handleCsvFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setCsvFile(file);
      } else {
        toast.error('Please select a CSV file');
        e.target.value = '';
      }
    }
  };

  const handleCsvUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) {
      toast.error('Please select a CSV file');
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', csvFile);

      const response = await api.post('/products/upload-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResult(response.data);
      toast.success(
        `CSV upload completed! ${response.data.success} products processed, ${response.data.errors} errors`
      );

      if (response.data.errors > 0 && response.data.errors) {
        console.error('Upload errors:', response.data.errors);
      }

      setCsvFile(null);
      setShowCsvModal(false);
      fetchProducts();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to upload CSV file');
      setUploadResult(null);
    } finally {
      setUploading(false);
    }
  };

  const downloadCsv = async () => {
    try {
      const response = await api.get('/products/export-csv', {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', 'products.csv');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Failed to download CSV:', error);
      toast.error('Failed to download CSV');
    }
  };

  // Get sub-categories for the selected category
  const availableSubCategories = formData.category
    ? categories.find((cat: any) => cat.name === formData.category)?.subCategories || []
    : [];

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading)
    return (
      <div className="min-h-screen">
        <div>Loading...</div>
      </div>
    );



  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow h-full flex flex-col min-h-0">
          <div className="mb-6 flex flex-shrink-0 items-center justify-between gap-4">
            <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
              <InfoButton
                info={
                  user?.role === 'super_admin' && pageInfo.page?.description
                    ? pageInfo.page.description
                    : undefined
                }
              >
                Product Management
              </InfoButton>
              <RefreshButton onRefresh={fetchProducts} />
            </h1>
            <div className="flex flex-nowrap gap-2">
              <button
                onClick={() => {
                  setShowCsvModal(true);
                  setUploadResult(null);
                }}
                className="rounded bg-gray-600 px-6 py-2 text-white hover:bg-gray-700"
              >
                Upload CSV
              </button>
              <button
                onClick={() => {
                  setShowModal(true);
                  setEditingProduct(null);
                  resetForm();
                }}
                className="rounded px-6 py-2 text-white"
                style={{
                  background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
                }}
              >
                Add Product
              </button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3 flex-shrink-0">
            <div>
              <input
                type="text"
                placeholder="Search by name, SKU, brand, or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="all">All Categories</option>
                {categories.map((cat: any) => (
                  <option key={cat.name} value={cat.name}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="all">All Status</option>
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
            <table className="w-full border-collapse min-w-[1000px]">
              <thead className="sticky top-0 z-10 bg-gray-50 shadow-sm">
                <tr className="bg-gray-50">
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.sku
                            ? pageInfo.columns.sku
                            : undefined
                        }
                      >
                        Product ID
                      </InfoButton>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.name
                            ? pageInfo.columns.name
                            : undefined
                        }
                      >
                        Name
                      </InfoButton>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span>Category</span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span>Subcategory</span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span>Brand</span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.description
                            ? pageInfo.columns.description
                            : undefined
                        }
                      >
                        Description
                      </InfoButton>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span>Search Tags</span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span>Applicable Discounts</span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.mrp
                            ? pageInfo.columns.mrp
                            : undefined
                        }
                      >
                        MRP per unit
                      </InfoButton>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.mrpPerCase
                            ? pageInfo.columns.mrpPerCase
                            : undefined
                        }
                      >
                        MRP per case
                      </InfoButton>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.quantityPerCase
                            ? pageInfo.columns.quantityPerCase
                            : undefined
                        }
                      >
                        Qty per case
                      </InfoButton>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.stock
                            ? pageInfo.columns.stock
                            : undefined
                        }
                      >
                        Stock
                      </InfoButton>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.status
                            ? pageInfo.columns.status
                            : undefined
                        }
                      >
                        Status
                      </InfoButton>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.actions
                            ? pageInfo.columns.actions
                            : undefined
                        }
                      >
                        Actions
                      </InfoButton>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product._id} className="hover:bg-gray-50">
                    <td className="border border-gray-200 p-2">
                      {product.productIdFormatted || product.sku}
                    </td>
                    <td className="border border-gray-200 p-2">{product.name}</td>
                    <td className="border border-gray-200 p-2">{product.category}</td>
                    <td className="border border-gray-200 p-2">{product.subCategory || '-'}</td>
                    <td className="border border-gray-200 p-2">{product.brand || '-'}</td>
                    <td className="border border-gray-200 p-2">
                      <div
                        className="max-w-[150px] truncate text-xs text-gray-500"
                        title={product.description}
                      >
                        {product.description || '-'}
                      </div>
                    </td>
                    <td className="border border-gray-200 p-2">
                      <button
                        onClick={() => {
                          if (product._id) setSearchTagsModalProductId(product._id);
                        }}
                        className="inline-flex items-center gap-1.5 whitespace-nowrap rounded bg-purple-100 px-3 py-1.5 text-xs font-medium text-purple-800 transition-colors hover:bg-purple-200"
                      >
                        Search tags
                      </button>
                    </td>
                    <td className="border border-gray-200 p-2">
                      <div className="flex flex-col gap-2">
                        <button
                          onClick={() =>
                            setDiscountModal({ isOpen: true, product, type: 'retail' })
                          }
                          className="whitespace-nowrap rounded bg-blue-100 px-2 py-1 text-[10px] font-bold uppercase text-blue-800 transition-colors hover:bg-blue-200"
                        >
                          Retail{' '}
                          {getApplicableDiscounts(product, 'retail').length > 0 &&
                            `(${getApplicableDiscounts(product, 'retail').length})`}
                        </button>
                        <button
                          onClick={() =>
                            setDiscountModal({ isOpen: true, product, type: 'business' })
                          }
                          className="whitespace-nowrap rounded bg-green-100 px-2 py-1 text-[10px] font-bold uppercase text-green-800 transition-colors hover:bg-green-200"
                        >
                          Business{' '}
                          {getApplicableDiscounts(product, 'business').length > 0 &&
                            `(${getApplicableDiscounts(product, 'business').length})`}
                        </button>
                      </div>
                    </td>
                    <td className="border border-gray-200 p-2">₹{product.mrp ?? 0}</td>
                    <td className="border border-gray-200 p-2">
                      {product.mrpPerCase != null ? `₹${product.mrpPerCase}` : '–'}
                    </td>
                    <td className="border border-gray-200 p-2">
                      {product.quantityPerCase ?? '–'}
                    </td>
                    <td className="border border-gray-200 p-2">{product.stock}</td>
                    <td className="border border-gray-200 p-2">
                      <div className="flex flex-col gap-1">
                        <span
                          className={`rounded px-2 py-1 text-xs ${product.isActive !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                        >
                          {product.isActive !== false ? 'Active' : 'Inactive'}
                        </span>
                        {product.stock === 0 && (
                          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-800">
                            Stock Out
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="border border-gray-200 p-2">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEdit(product)}
                          className="whitespace-nowrap rounded px-3 py-1 text-sm text-white"
                          style={{
                            background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                          }}
                        >
                          Edit
                        </button>
                        <button
                          onClick={async () => {
                            if (!product._id) return;
                            try {
                              await api.put(`/products/${product._id}`, { stock: 0 });
                              toast.success('Product marked as stock out');
                              fetchProducts();
                            } catch (_error: any) {
                              toast.error('Failed to update stock');
                            }
                          }}
                          className="whitespace-nowrap rounded bg-gray-600 px-3 py-1 text-sm text-white hover:bg-gray-700"
                        >
                          Stock Out
                        </button>
                        <button
                          onClick={async () => {
                            if (!product._id) return;
                            try {
                              await api.put(`/products/${product._id}`, {
                                isActive: product.isActive === false,
                              });
                              toast.success(
                                `Product ${product.isActive === false ? 'enabled' : 'disabled'}`
                              );
                              fetchProducts();
                            } catch (_error: any) {
                              toast.error('Failed to update product status');
                            }
                          }}
                          className="whitespace-nowrap rounded px-3 py-1 text-sm text-white"
                          style={{
                            background:
                              product.isActive !== false
                                ? 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)'
                                : 'linear-gradient(135deg, #28A745 0%, #218838 100%)',
                          }}
                        >
                          {product.isActive !== false ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Premium Pagination Controls */}
          {products.length > 0 && (
            <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
              <div className="text-sm text-gray-700">
                Showing <span className="font-semibold">{totalItems === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1}</span> to{' '}
                <span className="font-semibold">{Math.min(currentPage * itemsPerPage, totalItems)}</span> of{' '}
                <span className="font-semibold">{totalItems}</span> products
              </div>
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <span>Show</span>
                  <select
                    disabled
                    value={itemsPerPage}
                    className="rounded border px-2 py-1 bg-gray-100 cursor-not-allowed focus:outline-none"
                  >
                    <option value={50}>50</option>
                  </select>
                  <span>entries</span>
                </div>
                <nav className="inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                    disabled={currentPage === 1 || loading}
                    className="inline-flex items-center rounded-l-md border border-gray-300 bg-white px-2 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Previous</span>
                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                  {getPageNumbers().map((page, index) => {
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
                        disabled={loading}
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
                    disabled={currentPage === totalPages || loading}
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

        {/* Add/Edit Product Modal */}
        {showModal && (
          <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50">
            <div className="mx-4 max-h-[95vh] w-full max-w-5xl overflow-y-auto rounded-lg bg-white p-8 shadow-md">
              <h2 className="mb-4 text-2xl font-semibold">
                {editingProduct ? 'Edit Product' : 'Add Product'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.name
                            ? pageInfo.columns.name
                            : undefined
                        }
                      >
                        Name *
                      </InfoButton>
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      className="w-full rounded border px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.category
                            ? pageInfo.columns.category
                            : undefined
                        }
                      >
                        Category *
                      </InfoButton>
                    </label>
                    <SearchableSelect
                      options={categories
                        .filter((cat: any) => cat.isActive !== false)
                        .map((cat: any) => cat.name)}
                      value={formData.category}
                      onChange={(val) => {
                        setFormData({ ...formData, category: val, subCategory: '' });
                      }}
                      placeholder="Select a category"
                      required
                    />
                    <small className="mt-1 block text-xs text-gray-500">
                      Categories are managed in the Categories section. If a category doesn&apos;t
                      exist, create it there first.
                    </small>
                  </div>
                  {formData.category && availableSubCategories.length > 0 && (
                    <div>
                      <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.subCategory
                              ? pageInfo.columns.subCategory
                              : undefined
                          }
                        >
                          Sub-Category
                        </InfoButton>
                      </label>
                      <SearchableSelect
                        options={availableSubCategories}
                        value={formData.subCategory || ''}
                        onChange={(val) => setFormData({ ...formData, subCategory: val })}
                        placeholder="Select a sub-category (optional)"
                      />
                      <small className="mt-1 block text-xs text-gray-500">
                        Sub-categories are managed in the Categories section.
                      </small>
                    </div>
                  )}
                  <div>
                    <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.brand
                            ? pageInfo.columns.brand
                            : undefined
                        }
                      >
                        Brand
                      </InfoButton>
                    </label>
                    <SearchableSelect
                      options={Array.from(
                        new Set([
                          ...(formData.brand &&
                          !managedBrands.some((b) => b.name === formData.brand)
                            ? [formData.brand]
                            : []),
                          ...managedBrands.map((b) => b.name),
                        ])
                      )}
                      value={formData.brand || ''}
                      onChange={(val) => setFormData({ ...formData, brand: val })}
                      placeholder="Select a brand (optional)"
                    />
                    <small className="mt-1 block text-xs text-gray-500">
                      Add or edit brands from the Brands menu in the sidebar.
                    </small>
                  </div>
                </div>
                <div className="mt-2 border-t border-gray-100 pt-6 md:col-span-2">
                  <h4 className="mb-4 text-lg font-bold uppercase tracking-wider text-gray-800">
                    Pricing
                  </h4>
                </div>
                <div className="space-y-6 md:col-span-2">
                  <div className="rounded-2xl border-2 border-gray-100 bg-white p-6 shadow-sm transition-all hover:border-blue-100">
                    <div className="mb-4 flex items-center gap-2">
                      <div className="h-4 w-1.5 rounded-full bg-blue-500"></div>
                      <p className="text-xs font-black uppercase tracking-[0.2em] text-gray-500">
                        Pricing Details
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-1.5">
                        <label className="block inline-flex items-baseline gap-1 text-xs font-bold uppercase tracking-wider text-gray-700">
                          <InfoButton
                            info={
                              user?.role === 'super_admin' && pageInfo.columns?.mrp
                                ? pageInfo.columns.mrp
                                : undefined
                            }
                          >
                            MRP per unit *
                          </InfoButton>
                        </label>
                        <input
                          type="number"
                          name="mrp"
                          value={formData.mrp}
                          onChange={handleChange}
                          step="0.01"
                          min="0"
                          required
                          className="w-full rounded-xl border-2 border-gray-100 px-4 py-3 text-sm font-semibold outline-none transition-all focus:border-blue-500 focus:ring-0"
                        />
                        <p className="text-[10px] font-medium text-gray-400">
                          Retail price for a single unit.
                        </p>
                      </div>
                      <div className="space-y-1.5">
                        <label className="block inline-flex items-baseline gap-1 text-xs font-bold uppercase tracking-wider text-gray-700">
                          <InfoButton
                            info={
                              user?.role === 'super_admin' && pageInfo.columns?.mrpPerCase
                                ? pageInfo.columns.mrpPerCase
                                : undefined
                            }
                          >
                            MRP per case
                          </InfoButton>
                        </label>
                        <input
                          type="number"
                          name="mrpPerCase"
                          value={formData.mrpPerCase ?? ''}
                          onChange={handleChange}
                          step="0.01"
                          min="0"
                          placeholder="Business only"
                          className="w-full rounded-xl border-2 border-gray-100 px-4 py-3 text-sm font-semibold outline-none transition-all focus:border-blue-500 focus:ring-0"
                        />
                        <p className="text-[10px] font-medium text-gray-400">
                          Price for bulk case (optional).
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border-2 border-gray-100 bg-white p-6 shadow-sm transition-all hover:border-green-100">
                    <div className="mb-4 flex items-center gap-2">
                      <div className="h-4 w-1.5 rounded-full bg-green-500"></div>
                      <p className="text-xs font-black uppercase tracking-[0.2em] text-gray-500">
                        Inventory Status
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-1.5">
                        <label className="block inline-flex items-baseline gap-1 text-xs font-bold uppercase tracking-wider text-gray-700">
                          <InfoButton
                            info={
                              user?.role === 'super_admin' && pageInfo.columns?.quantityPerCase
                                ? pageInfo.columns.quantityPerCase
                                : undefined
                            }
                          >
                            Quantity per case
                          </InfoButton>
                        </label>
                        <input
                          type="number"
                          name="quantityPerCase"
                          value={formData.quantityPerCase ?? ''}
                          onChange={handleChange}
                          min="1"
                          placeholder="Units per case"
                          className="w-full rounded-xl border-2 border-gray-100 px-4 py-3 text-sm font-semibold outline-none transition-all focus:border-green-500 focus:ring-0"
                        />
                        <p className="text-[10px] font-medium text-gray-400">
                          Individual units inside one case.
                        </p>
                      </div>
                      <div className="space-y-1.5">
                        <label className="block inline-flex items-baseline gap-1 text-xs font-bold uppercase tracking-wider text-gray-700">
                          <InfoButton
                            info={
                              user?.role === 'super_admin' && pageInfo.columns?.stock
                                ? pageInfo.columns.stock
                                : undefined
                            }
                          >
                            Total Stock *
                          </InfoButton>
                        </label>
                        <input
                          type="number"
                          name="stock"
                          value={formData.stock}
                          onChange={handleChange}
                          min="0"
                          required
                          disabled={
                            formData.variantCombinations && formData.variantCombinations.length > 0
                          }
                          className={`w-full rounded-xl border-2 border-gray-100 px-4 py-3 text-sm font-semibold outline-none transition-all focus:border-green-500 focus:ring-0 ${formData.variantCombinations && formData.variantCombinations.length > 0 ? 'cursor-not-allowed bg-gray-50 text-gray-400 opacity-60' : ''}`}
                        />
                        {formData.variantCombinations && formData.variantCombinations.length > 0 ? (
                          <p className="mt-1 animate-pulse text-[10px] font-bold text-blue-600">
                            Syncing automatically with variants...
                          </p>
                        ) : (
                          <p className="text-[10px] font-medium text-gray-400">
                            Available unit quantity in warehouse.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <label className="flex cursor-pointer items-center gap-1">
                    <input
                      type="checkbox"
                      name="isActive"
                      checked={formData.isActive !== false}
                      onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                      className="mr-2"
                    />
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.status
                          ? pageInfo.columns.status
                          : undefined
                      }
                    >
                      Active
                    </InfoButton>
                  </label>
                </div>
                <div className="mt-6 border-t border-gray-100 pt-6 md:col-span-2">
                  <div className="mb-4 flex flex-col gap-4">
                    <h4 className="inline-flex items-baseline gap-2 text-lg font-bold uppercase tracking-wider text-gray-800">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.variantAttributes
                            ? pageInfo.columns.variantAttributes
                            : undefined
                        }
                      >
                        Variant Attributes
                      </InfoButton>
                    </h4>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Attribute name (e.g., Color)"
                        value={newAttributeName}
                        onChange={(e) => setNewAttributeName(e.target.value)}
                        className="flex-1 rounded border px-3 py-2 text-sm"
                      />
                      <button
                        type="button"
                        onClick={addVariantAttribute}
                        className="rounded bg-blue-600 px-4 py-2 text-xs font-bold uppercase text-white transition-colors hover:bg-blue-700"
                      >
                        + Add Attribute
                      </button>
                    </div>

                    {formData.variantAttributes && formData.variantAttributes.length > 0 && (
                      <div className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
                        <p className="mb-2 text-xs font-bold uppercase tracking-widest text-gray-500">
                          Attribute Values
                        </p>
                        {formData.variantAttributes.map((attr) => (
                          <div key={attr} className="flex items-center gap-3">
                            <div className="w-24 shrink-0">
                              <span className="text-[11px] font-black uppercase tracking-wider text-gray-700">
                                {attr}
                              </span>
                            </div>
                            <div className="flex flex-1 flex-col gap-2">
                              <div className="flex flex-wrap gap-1">
                                {(attributeValues[attr] || []).map((val) => (
                                  <span
                                    key={val}
                                    className="inline-flex items-center rounded border border-blue-200 bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-800 shadow-sm"
                                  >
                                    {val}
                                    <button
                                      type="button"
                                      onClick={() => removeAttributeValue(attr, val)}
                                      className="ml-1.5 font-bold text-blue-500 hover:text-blue-700"
                                    >
                                      ×
                                    </button>
                                  </span>
                                ))}
                                {(!attributeValues[attr] || attributeValues[attr].length === 0) && (
                                  <span className="text-[10px] italic text-gray-400">
                                    No values added
                                  </span>
                                )}
                              </div>
                              <div className="flex gap-2">
                                <input
                                  type="text"
                                  placeholder={`Add value for ${attr}...`}
                                  value={newValueForAttr[attr] || ''}
                                  onChange={(e) =>
                                    setNewValueForAttr({
                                      ...newValueForAttr,
                                      [attr]: e.target.value,
                                    })
                                  }
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                      e.preventDefault();
                                      addAttributeValue(attr);
                                    }
                                  }}
                                  className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-xs outline-none placeholder:text-gray-300 focus:ring-1 focus:ring-blue-500"
                                />
                                <button
                                  type="button"
                                  onClick={() => addAttributeValue(attr)}
                                  className="rounded bg-blue-600 px-3 py-1.5 text-[10px] font-black uppercase text-white transition-colors hover:bg-blue-700"
                                >
                                  Add
                                </button>
                              </div>
                            </div>
                            <button
                              type="button"
                              onClick={() => removeVariantAttribute(attr)}
                              className="px-2 text-xl font-bold text-red-300 transition-colors hover:text-red-500"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={generateCombinations}
                          className="mt-2 w-full rounded bg-green-600 px-4 py-2 text-xs font-bold uppercase text-white shadow-sm transition-colors hover:bg-green-700"
                        >
                          Generate All Combinations
                        </button>
                      </div>
                    )}
                  </div>

                  {formData.variantCombinations && formData.variantCombinations.length > 0 && (
                    <div className="mb-8 overflow-hidden rounded-xl border border-gray-200 shadow-sm">
                      <table className="w-full text-left">
                        <thead className="border-b border-gray-200 bg-gray-50">
                          <tr>
                            <th className="w-1/4 px-4 py-3 text-[10px] font-black uppercase tracking-widest text-gray-500">
                              Combination
                            </th>
                            <th className="w-1/4 px-4 py-3 text-[10px] font-black uppercase tracking-widest text-gray-500">
                              SKU
                            </th>
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-gray-500">
                              Price (Unit)
                            </th>
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-gray-500">
                              Price (Case)
                            </th>
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-gray-500">
                              Stock
                            </th>
                            <th className="px-4 py-3"></th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {formData.variantCombinations.map((combo, idx) => (
                            <tr key={idx} className="transition-colors hover:bg-gray-50/50">
                              <td className="px-4 py-3">
                                <div className="text-[11px] font-black uppercase text-gray-900">
                                  {Object.entries(combo.attributes).map(([k, v]: [any, any]) => (
                                    <span
                                      key={k}
                                      className="mr-2 inline-block rounded border bg-white px-2 py-0.5 shadow-sm last:mr-0"
                                    >
                                      {k}: <span className="text-blue-600">{v}</span>
                                    </span>
                                  ))}
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <input
                                  type="text"
                                  value={combo.sku}
                                  onChange={(e) => updateVariant(idx, 'sku', e.target.value)}
                                  className="w-full rounded-lg border border-gray-200 px-4 py-2 text-[11px] font-black shadow-sm outline-none transition-all focus:ring-2 focus:ring-blue-500"
                                  placeholder="Variation SKU"
                                />
                              </td>
                              <td className="px-4 py-3">
                                <input
                                  type="number"
                                  value={combo.price}
                                  onChange={(e) =>
                                    updateVariant(idx, 'price', parseFloat(e.target.value))
                                  }
                                  className="w-24 rounded border border-gray-200 px-3 py-1.5 text-[11px] font-bold outline-none focus:ring-2 focus:ring-blue-500"
                                />
                              </td>
                              <td className="px-4 py-3">
                                <input
                                  type="number"
                                  value={combo.pricePerCase}
                                  onChange={(e) =>
                                    updateVariant(idx, 'pricePerCase', parseFloat(e.target.value))
                                  }
                                  className="w-24 rounded border border-gray-200 px-3 py-1.5 text-[11px] font-bold outline-none focus:ring-2 focus:ring-blue-500"
                                />
                              </td>
                              <td className="px-4 py-3">
                                <input
                                  type="number"
                                  value={combo.stock}
                                  onChange={(e) =>
                                    updateVariant(idx, 'stock', parseInt(e.target.value))
                                  }
                                  className="w-20 rounded border border-gray-200 px-3 py-1.5 text-[11px] font-bold outline-none focus:ring-2 focus:ring-blue-500"
                                />
                              </td>
                              <td className="px-4 py-3 text-right">
                                <button
                                  type="button"
                                  onClick={() => {
                                    const newCombos = formData.variantCombinations?.filter(
                                      (_, i) => i !== idx
                                    );
                                    setFormData({ ...formData, variantCombinations: newCombos });
                                  }}
                                  className="text-[10px] font-bold uppercase tracking-widest text-red-500 hover:text-red-700"
                                >
                                  Delete
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.images
                          ? pageInfo.columns.images
                          : undefined
                      }
                    >
                      Product Images
                    </InfoButton>
                  </label>
                  {formData.images && formData.images.length > 0 && (
                    <div className="mb-4 flex flex-wrap gap-2">
                      {formData.images.map((imageUrl, index) => {
                        let src = imageUrl;
                        if (
                          imageUrl &&
                          !imageUrl.startsWith('http') &&
                          !imageUrl.startsWith('/') &&
                          !imageUrl.startsWith('blob:')
                        ) {
                          // Use Python backend URL for Next.js frontend
                          const backendUrl =
                            process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || '';
                          src = `${backendUrl}${imageUrl}`;
                        } else if (imageUrl && imageUrl.startsWith('/uploads')) {
                          // If it's a relative path starting with /uploads, prepend backend URL
                          const backendUrl =
                            process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || '';
                          src = `${backendUrl}${imageUrl}`;
                        }
                        return (
                          <div key={index} className="relative inline-block">
                            <img
                              src={src}
                              alt={`Product ${index + 1}`}
                              className="h-24 w-24 rounded border border-gray-300 object-cover"
                              onError={(e: any) => {
                                e.target.style.display = 'none';
                              }}
                            />
                            <button
                              type="button"
                              onClick={() => removeProductImage(index)}
                              className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-xs text-white hover:bg-red-700"
                            >
                              ×
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  <div>
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={handleImageUpload}
                      disabled={uploadingImages}
                      style={{ display: 'none' }}
                      id="product-image-upload"
                    />
                    <label
                      htmlFor="product-image-upload"
                      className={`inline-block cursor-pointer rounded bg-gray-600 px-4 py-2 text-sm text-white hover:bg-gray-700 ${uploadingImages ? 'cursor-not-allowed opacity-60' : ''}`}
                    >
                      {uploadingImages ? 'Uploading...' : 'Add Image'}
                    </label>
                  </div>
                  <small className="mt-2 block text-xs text-gray-500">
                    Click &quot;Add Image&quot; to upload one or more product images. You can add
                    multiple images by clicking &quot;Add Image&quot; again.
                  </small>
                </div>
                <div className="md:col-span-2">
                  <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.videos
                          ? pageInfo.columns.videos
                          : undefined
                      }
                    >
                      Videos
                    </InfoButton>
                  </label>
                  <input
                    type="file"
                    accept="video/*"
                    multiple
                    onChange={handleVideoChange}
                    className="w-full rounded border px-3 py-2"
                  />
                  {formData.videos && formData.videos.length > 0 && (
                    <div className="mt-2">
                      {formData.videos.map((vid, idx) => (
                        <span key={idx} className="mr-2">
                          Video {idx + 1}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
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
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={3}
                    className="w-full rounded border px-3 py-2"
                  />
                </div>
                {/* Search Tags Management (only when editing) */}
                {editingProduct?._id && (
                  <SearchTagManager productId={editingProduct._id} onUpdate={fetchProducts} />
                )}

                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      setEditingProduct(null);
                      resetForm();
                    }}
                    className="rounded bg-gray-300 px-6 py-2 text-gray-700 hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="rounded px-6 py-2 text-white"
                    style={{
                      background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
                    }}
                  >
                    {editingProduct ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* CSV Upload Modal */}
        {showCsvModal && (
          <div
            className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-24"
            onClick={() => {
              setShowCsvModal(false);
              setCsvFile(null);
              setUploadResult(null);
            }}
          >
            <div
              className="mx-4 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-md"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-left text-2xl font-semibold">Upload Products via CSV</h3>
              <div className="mb-4 rounded bg-gray-100 p-4 text-left">
                <p className="mb-2 font-bold">CSV Format Requirements:</p>
                <ul className="mb-2 list-inside list-disc space-y-1 text-sm">
                  <li>
                    <strong>Standard Product:</strong> Fill out `name`, `category`, and `mrp`. Leave
                    variant columns blank.
                  </li>
                  <li>
                    <strong>Product with Variants:</strong> Use <strong>One Row per Variant</strong>
                    . The first row defines the main product details (Category, Description, Brand,
                    etc.). For each variant, add a new row with the <em>same Product Name</em> but
                    different `Attribute` / `Variant` values, and its specific `mrp` and `stock`.
                  </li>
                  <li>
                    <strong>Columns:</strong> `Attribute 1`, `Variant 1` (e.g. Color, Red). You can
                    add `Attribute 2`, `Variant 2` as needed.
                  </li>
                  <li>
                    <strong>Updates:</strong> Include a `productId` (e.g. PDT-1) to update an
                    existing product instead of creating a new one.
                  </li>
                </ul>
                <button
                  type="button"
                  onClick={downloadCsv}
                  className="mt-2 rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
                >
                  Download CSV
                </button>
              </div>

              <form onSubmit={handleCsvUpload}>
                <div className="mb-4 text-left">
                  <label className="mb-1 block text-sm font-medium">Select CSV File *</label>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleCsvFileChange}
                    required
                    disabled={uploading}
                    className="w-full rounded border px-3 py-2"
                  />
                  {csvFile && (
                    <p className="mt-2 text-green-600">
                      Selected: {csvFile.name} ({(csvFile.size / 1024).toFixed(2)} KB)
                    </p>
                  )}
                </div>

                {uploadResult && (
                  <div
                    className={`mb-4 rounded p-3 text-left ${uploadResult.errors > 0 ? 'border border-yellow-300 bg-yellow-50' : 'border border-green-300 bg-green-50'}`}
                  >
                    <p className="font-bold">
                      Upload Results: {uploadResult.success} successful, {uploadResult.errors}{' '}
                      errors
                    </p>
                    {uploadResult.errors > 0 && uploadResult.errors && (
                      <div className="mt-2 text-left">
                        <p className="mb-1 font-bold">Errors:</p>
                        <ul className="list-inside list-disc text-sm">
                          {uploadResult.errors.slice(0, 10).map((error: any, idx: number) => (
                            <li key={idx}>
                              Row {error.row}: {error.error}
                            </li>
                          ))}
                          {uploadResult.errors.length > 10 && (
                            <li>... and {uploadResult.errors.length - 10} more errors</li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCsvModal(false);
                      setCsvFile(null);
                      setUploadResult(null);
                    }}
                    disabled={uploading}
                    className="rounded bg-gray-300 px-6 py-2 text-gray-700 hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!csvFile || uploading}
                    className="rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {uploading ? 'Uploading...' : 'Upload CSV'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Search Tags Modal */}
        {searchTagsModalProductId && (
          <div
            className="fixed inset-0 z-[120] flex items-center justify-center bg-black bg-opacity-50"
            onClick={() => setSearchTagsModalProductId(null)}
          >
            <div
              className="mx-4 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-6 shadow-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-xl font-semibold">Product Search Tags</h3>
                <button
                  onClick={() => setSearchTagsModalProductId(null)}
                  className="text-gray-400 hover:text-gray-600 focus:outline-none"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <SearchTagManager productId={searchTagsModalProductId} onUpdate={fetchProducts} />
            </div>
          </div>
        )}

        {/* Applicable Discounts Modal */}
        {discountModal.isOpen && discountModal.product && (
          <div
            className="fixed inset-0 z-[130] flex items-center justify-center bg-black bg-opacity-50"
            onClick={() => setDiscountModal({ ...discountModal, isOpen: false })}
          >
            <div
              className="mx-4 flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-white p-6 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    {discountModal.type === 'retail' ? 'Retail' : 'Business'} Discounts
                  </h3>
                  <p className="text-sm font-medium text-gray-500">
                    Applicable for:{' '}
                    <span className="font-bold text-blue-600">{discountModal.product.name}</span>
                  </p>
                </div>
                <button
                  onClick={() => setDiscountModal({ ...discountModal, isOpen: false })}
                  className="text-gray-400 transition-colors hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>

              <div className="custom-scrollbar flex-1 overflow-y-auto pr-2">
                {getApplicableDiscounts(discountModal.product, discountModal.type).length > 0 ? (
                  <div className="space-y-4">
                    {getApplicableDiscounts(discountModal.product, discountModal.type).map(
                      (discount) => (
                        <div
                          key={discount._id}
                          className="rounded-xl border-2 border-gray-100 bg-gray-50/30 p-4 transition-all hover:border-blue-100"
                        >
                          <div className="mb-2 flex items-start justify-between">
                            <div className="flex flex-col gap-1">
                              <div className="inline-block rounded-lg border-2 border-dashed border-blue-200 bg-white px-3 py-1">
                                <span className="text-sm font-black tracking-wider text-blue-700">
                                  {discount.method === 'automatic'
                                    ? 'AUTOMATIC APPLIED'
                                    : discount.code || 'NO CODE'}
                                </span>
                              </div>
                              {discount.displayId && (
                                <span className="text-[10px] font-bold text-gray-400">
                                  ID: {discount.displayId}
                                </span>
                              )}
                            </div>
                            <div className="text-right">
                              <span className="text-lg font-black text-gray-900">
                                {discount.discountType === 'percentage'
                                  ? `${discount.discountValue}% OFF`
                                  : `₹${discount.discountValue} OFF`}
                              </span>
                              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                                {discount.typeOfDiscount?.replace(/_/g, ' ')}
                              </p>
                            </div>
                          </div>

                          <div className="mt-4 grid grid-cols-2 gap-4 text-[11px]">
                            <div>
                              <p className="mb-1 font-bold uppercase tracking-tighter text-gray-400">
                                Requirement
                              </p>
                              <p className="font-semibold text-gray-700">
                                {discount.minRequirementType === 'min_amount'
                                  ? `Min. ₹${discount.minPurchaseAmount}`
                                  : discount.minRequirementType === 'min_quantity'
                                    ? `Min. ${discount.minQuantityOfEligibleItems} items`
                                    : 'No minimum'}
                              </p>
                            </div>
                            <div>
                              <p className="mb-1 font-bold uppercase tracking-tighter text-gray-400">
                                Valid Until
                              </p>
                              <p className="font-semibold text-gray-700">
                                {formatDateIST(discount.validUntil)}
                              </p>
                            </div>
                          </div>

                          {discount.appliesToType !== 'all' && (
                            <div className="mt-3 border-t border-gray-100 pt-3">
                              <p className="mb-1 mr-2 inline-block text-[10px] font-bold uppercase tracking-tighter text-gray-400">
                                Inherited from:
                              </p>
                              <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-black uppercase text-blue-700">
                                {discount.appliesToType}
                              </span>
                            </div>
                          )}
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50 py-12 text-gray-400">
                    <svg
                      className="mb-3 h-12 w-12 opacity-20"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1}
                        d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"
                      />
                    </svg>
                    <p className="font-bold">No {discountModal.type} discounts found</p>
                    <p className="text-sm">No inherited discounts apply to this product.</p>
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end border-t border-gray-100 pt-4">
                <button
                  onClick={() => setDiscountModal({ ...discountModal, isOpen: false })}
                  className="rounded-xl bg-gray-100 px-6 py-2 text-sm font-bold text-gray-600 transition-all hover:bg-gray-200"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
