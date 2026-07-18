'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import RefreshButton from '@/components/Admin/RefreshButton';

interface Category {
  _id?: string;
  name: string;
  description?: string;
  images?: string[];
  subCategories?: string[];
  minimumQuantity?: number;
  categoryTag?: string;
  isActive?: boolean;
  showInMobileHomepage?: boolean;
  gst?: number;
  isReturnable?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export default function CategoryManagement() {
  const { user } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [formData, setFormData] = useState<Category>({
    name: '',
    description: '',
    images: [],
    subCategories: [],
    minimumQuantity: 0,
    categoryTag: '',
    isActive: true,
    showInMobileHomepage: false,
    gst: 0,
    isReturnable: false,
  });
  const [subCategoryInput, setSubCategoryInput] = useState('');
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [uploadingImages, setUploadingImages] = useState(false);
  const [showTagModal, setShowTagModal] = useState(false);
  const [categoryTags, setCategoryTags] = useState<any[]>([]);
  const [editingTag, setEditingTag] = useState<any | null>(null);
  const [tagFormData, setTagFormData] = useState({ name: '', description: '', isActive: true });

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [tagFilter, setTagFilter] = useState<string>('all');
  const [sortColumn, setSortColumn] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const [showSubCategoriesDialog, setShowSubCategoriesDialog] = useState(false);
  const [subCategoriesToView, setSubCategoriesToView] = useState<string[]>([]);
  const [viewingCategoryName, setViewingCategoryName] = useState('');

  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const renderSortIcon = (column: string) => {
    if (sortColumn !== column) {
      return <span className="text-gray-300 ml-1 select-none">⇅</span>;
    }
    return sortDirection === 'asc' ? (
      <span className="text-indigo-600 ml-1 select-none">▲</span>
    ) : (
      <span className="text-indigo-600 ml-1 select-none">▼</span>
    );
  };

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchCategories();
      fetchCategoryTags();
      fetchPageInfo();
    }
  }, [user]);

  // Reset pagination to page 1 on filter/search change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter, tagFilter]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/category-management');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories');
      setCategories(response.data || []);
      setLoading(false);
    } catch (_error: any) {
      toast.error('Failed to fetch categories');
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
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

      const response = await api.post('/categories/upload-images', formDataUpload, {
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

  const removeImage = (index: number) => {
    const newImages = formData.images?.filter((_, i) => i !== index) || [];
    setFormData({
      ...formData,
      images: newImages,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const trimmedName = (formData.name || '').trim().toLowerCase();
      if (!trimmedName) {
        toast.error('Category name is required');
        return;
      }
      const nameExists = categories.some((cat) => {
        if (editingCategory && cat._id === editingCategory._id) {
          return false;
        }
        return (cat.name || '').trim().toLowerCase() === trimmedName;
      });

      if (nameExists) {
        toast.error('Category name already exists. Please choose a unique name.');
        return;
      }

      const categoryData = {
        name: formData.name || '',
        description: formData.description || '',
        images: (formData.images || []).filter((url: string) => url.trim() !== ''),
        subCategories: formData.subCategories || [],
        minimumQuantity: formData.minimumQuantity || 0,
        categoryTag: formData.categoryTag || '',
        gst: formData.gst || 0,
        isActive: formData.isActive !== undefined ? formData.isActive : true,
        showInMobileHomepage: formData.showInMobileHomepage || false,
        isReturnable: formData.isReturnable || false,
      };

      if (editingCategory?._id) {
        await api.put(`/categories/${editingCategory._id}`, categoryData);
        toast.success('Category updated successfully');
      } else {
        await api.post('/categories', categoryData);
        toast.success('Category created successfully');
      }
      setShowModal(false);
      setEditingCategory(null);
      setFormData({
        name: '',
        description: '',
        images: [],
        subCategories: [],
        minimumQuantity: 0,
        categoryTag: '',
        gst: 0,
        isActive: true,
        showInMobileHomepage: false,
        isReturnable: false,
      });
      setSubCategoryInput('');
      setImageFiles([]);
      fetchCategories();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed');
    }
  };

  const handleEdit = (category: Category) => {
    setEditingCategory(category);
    const images = category.images || [];
    const subCategories = category.subCategories || [];
    setImageFiles([]); // Reset files on edit
    setFormData({
      name: category.name || '',
      description: category.description || '',
      images: images,
      subCategories: subCategories,
      minimumQuantity: category.minimumQuantity || 0,
      categoryTag: category.categoryTag || (category as any).categoryTags?.[0] || '',
      gst: category.gst || 0,
      isActive: category.isActive !== false,
      showInMobileHomepage: category.showInMobileHomepage || false,
      isReturnable: category.isReturnable || false,
    });
    setSubCategoryInput('');
    fetchCategoryTags(); // Refresh tags when opening edit modal
    setShowModal(true);
  };

  const handleToggleStatus = async (category: Category) => {
    try {
      await api.put(`/categories/${category._id}`, { isActive: !category.isActive });
      toast.success(`Category ${category.isActive ? 'disabled' : 'enabled'} successfully`);
      fetchCategories();
    } catch (_error: any) {
      toast.error('Failed to update category status');
    }
  };

  const fetchCategoryTags = async () => {
    try {
      const response = await api.get('/category-tags');
      setCategoryTags(response.data || []);
    } catch (_error: any) {
      toast.error('Failed to fetch category tags');
    }
  };

  const handleTagSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTag?._id) {
        await api.put(`/category-tags/${editingTag._id}`, tagFormData);
        toast.success('Category tag updated successfully');
      } else {
        await api.post('/category-tags', tagFormData);
        toast.success('Category tag created successfully');
      }
      setShowTagModal(false);
      setEditingTag(null);
      setTagFormData({ name: '', description: '', isActive: true });
      fetchCategoryTags();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed');
    }
  };

  const handleEditTag = (tag: any) => {
    setEditingTag(tag);
    setTagFormData({
      name: tag.name || '',
      description: tag.description || '',
      isActive: tag.isActive !== false,
    });
  };

  const handleToggleTagStatus = async (tag: any) => {
    const newStatus = !tag.isActive;
    if (!confirm(`Are you sure you want to ${newStatus ? 'unhide' : 'hide'} this category tag?`))
      return;
    try {
      await api.put(`/category-tags/${tag._id}`, { isActive: newStatus });
      toast.success(`Category tag ${newStatus ? 'unhidden' : 'hidden'} successfully`);
      fetchCategoryTags();
    } catch (_error: any) {
      toast.error(`Failed to ${newStatus ? 'unhide' : 'hide'} category tag`);
    }
  };

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading) return <div>Loading...</div>;

  const filteredCategories = categories.filter((category) => {
    const matchesSearch =
      category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (category.description || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && category.isActive !== false) ||
      (statusFilter === 'inactive' && category.isActive === false);

    const matchesTag =
      tagFilter === 'all' ||
      category.categoryTag === tagFilter ||
      (Array.isArray((category as any).categoryTags) && (category as any).categoryTags.includes(tagFilter));

    return matchesSearch && matchesStatus && matchesTag;
  });

  const sortedCategories = [...filteredCategories].sort((a, b) => {
    if (!sortColumn) return 0;

    let valA: any = a[sortColumn as keyof Category] ?? '';
    let valB: any = b[sortColumn as keyof Category] ?? '';

    // Handle custom sorting fields
    if (sortColumn === 'status' || sortColumn === 'isActive') {
      valA = a.isActive !== false ? 'Active' : 'Inactive';
      valB = b.isActive !== false ? 'Active' : 'Inactive';
    }

    if (sortColumn === 'subCategories') {
      valA = a.subCategories?.length ?? 0;
      valB = b.subCategories?.length ?? 0;
    }

    if (typeof valA === 'string' && typeof valB === 'string') {
      return sortDirection === 'asc'
        ? valA.localeCompare(valB)
        : valB.localeCompare(valA);
    }

    if (typeof valA === 'number' && typeof valB === 'number') {
      return sortDirection === 'asc' ? valA - valB : valB - valA;
    }

    if (typeof valA === 'boolean' && typeof valB === 'boolean') {
      return sortDirection === 'asc'
        ? (valA === valB ? 0 : valA ? 1 : -1)
        : (valA === valB ? 0 : valA ? -1 : 1);
    }

    return sortDirection === 'asc'
      ? (valA > valB ? 1 : -1)
      : (valA < valB ? 1 : -1);
  });

  const totalItems = filteredCategories.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedCategories = sortedCategories.slice(startIndex, endIndex);

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

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow h-full flex flex-col min-h-0">
          <div className="mb-6 flex flex-shrink-0 items-center justify-between">
            <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
              <InfoButton
                info={
                  user?.role === 'super_admin' && pageInfo.page?.description
                    ? pageInfo.page.description
                    : undefined
                }
              >
                Category Management
              </InfoButton>
              <RefreshButton onRefresh={fetchCategories} />
            </h1>
            <div className="flex gap-2">
              <button
            onClick={() => {
              setShowTagModal(true);
              fetchCategoryTags();
            }}
            className="rounded px-4 py-2 text-white"
            style={{
              background: 'linear-gradient(135deg, #6c757d 0%, #495057 100%)',
            }}
          >
            Manage Category Tags
          </button>
          <button
            onClick={() => {
              fetchCategoryTags(); // Refresh tags when opening add modal
              setShowModal(true);
              setEditingCategory(null);
              setFormData({
                name: '',
                description: '',
                images: [],
                subCategories: [],
                minimumQuantity: 0,
                categoryTag: '',
                gst: 0,
                isActive: true,
                showInMobileHomepage: false,
                isReturnable: false,
              });
              setSubCategoryInput('');
              setImageFiles([]);
            }}
            className="rounded px-4 py-2 text-white"
            style={{
              background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
            }}
          >
            Add Category
          </button>
        </div>
      </div>

          {/* Search and Filters */}
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3 flex-shrink-0">
            <div>
              <input
                type="text"
                placeholder="Search by name or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              />
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
            <div>
              <select
                value={tagFilter}
                onChange={(e) => setTagFilter(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="all">All Category Tags</option>
                {categoryTags.map((tag) => (
                  <option key={tag._id} value={tag.name}>
                    {tag.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

      <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10 bg-gray-50 shadow-sm">
            <tr className="bg-gray-50">
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('_id')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.id
                          ? pageInfo.columns.id
                          : undefined
                      }
                    >
                      ID
                    </InfoButton>
                    {renderSortIcon('_id')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('name')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.name
                          ? pageInfo.columns.name
                          : undefined
                      }
                    >
                      Name
                    </InfoButton>
                    {renderSortIcon('name')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('description')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.description
                          ? pageInfo.columns.description
                          : undefined
                      }
                    >
                      Description
                    </InfoButton>
                    {renderSortIcon('description')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('subCategories')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.subCategories
                          ? pageInfo.columns.subCategories
                          : undefined
                      }
                    >
                      Sub-Categories
                    </InfoButton>
                    {renderSortIcon('subCategories')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('categoryTag')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.categoryTag
                          ? pageInfo.columns.categoryTag
                          : undefined
                      }
                    >
                      Category Tag
                    </InfoButton>
                    {renderSortIcon('categoryTag')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('minimumQuantity')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.minimumQuantity
                          ? pageInfo.columns.minimumQuantity
                          : undefined
                      }
                    >
                      Minimum Quantity
                    </InfoButton>
                    {renderSortIcon('minimumQuantity')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('gst')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.gst
                          ? pageInfo.columns.gst
                          : undefined
                      }
                    >
                      GST %
                    </InfoButton>
                    {renderSortIcon('gst')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('isReturnable')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.isReturnable
                          ? pageInfo.columns.isReturnable
                          : undefined
                      }
                    >
                      Returnable
                    </InfoButton>
                    {renderSortIcon('isReturnable')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('isActive')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.status
                          ? pageInfo.columns.status
                          : undefined
                      }
                    >
                      Status
                    </InfoButton>
                    {renderSortIcon('isActive')}
                  </span>
                </div>
              </th>
              <th className="border border-gray-200 p-2 text-left">
                <div className="flex items-center gap-1">
                  <span
                    onClick={() => handleSort('showInMobileHomepage')}
                    className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                  >
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.showInMobileHomepage
                          ? pageInfo.columns.showInMobileHomepage
                          : undefined
                      }
                    >
                      Display in homepage
                    </InfoButton>
                    {renderSortIcon('showInMobileHomepage')}
                  </span>
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
            {paginatedCategories.length > 0 ? (
              paginatedCategories.map((category) => (
                <tr key={category._id} className="hover:bg-gray-50">
                  <td className="border border-gray-200 p-2">
                    {category._id || '-'}
                  </td>
                  <td className="border border-gray-200 p-2">{category.name}</td>
                  <td className="border border-gray-200 p-2">
                    <div
                      className="max-w-[250px] truncate text-xs text-gray-500"
                      title={category.description}
                    >
                      {category.description || '-'}
                    </div>
                  </td>
                  <td className="border border-gray-200 p-2">
                    {category.subCategories && category.subCategories.length > 0 ? (
                      <button
                        onClick={() => {
                          setSubCategoriesToView(category.subCategories || []);
                          setViewingCategoryName(category.name);
                          setShowSubCategoriesDialog(true);
                        }}
                        className="inline-flex items-center gap-1.5 whitespace-nowrap rounded bg-blue-100 px-3 py-1.5 text-xs font-normal text-blue-800 transition-colors hover:bg-blue-200"
                      >
                        Show subcategories ({category.subCategories.length})
                      </button>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="border border-gray-200 p-2">
                    {category.categoryTag || (category as any).categoryTags?.[0] ? (
                      <span className="rounded bg-green-100 px-2 py-1 text-xs font-normal text-green-800">
                        {category.categoryTag || (category as any).categoryTags?.[0]}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="border border-gray-200 p-2">
                    {category.minimumQuantity !== undefined ? category.minimumQuantity : 0}
                  </td>
                  <td className="border border-gray-200 p-2">{category.gst !== undefined ? category.gst : 0}%</td>
                  <td className="border border-gray-200 p-2 text-center">
                    <input
                      type="checkbox"
                      checked={category.isReturnable || false}
                      onChange={async () => {
                        try {
                          await api.put(`/categories/${category._id}`, {
                            isReturnable: !category.isReturnable,
                          });
                          toast.success('Returnable status updated');
                          fetchCategories();
                        } catch (_err) {
                          toast.error('Failed to update returnable status');
                        }
                      }}
                      className="h-4 w-4 cursor-pointer"
                    />
                  </td>
                  <td className="border border-gray-200 p-2">
                    <span
                      className={`rounded px-2 py-1 text-xs font-normal ${category.isActive !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {category.isActive !== false ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="border border-gray-200 p-2 text-center">
                    <input
                      type="checkbox"
                      checked={category.showInMobileHomepage || false}
                      onChange={async () => {
                        try {
                          await api.put(`/categories/${category._id}`, {
                            showInMobileHomepage: !category.showInMobileHomepage,
                          });
                          toast.success('Homepage visibility updated');
                          fetchCategories();
                        } catch (_err) {
                          toast.error('Failed to update mobile visibility');
                        }
                      }}
                      className="h-4 w-4 cursor-pointer"
                    />
                  </td>
                  <td className="border border-gray-200 p-2">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleEdit(category)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleToggleStatus(category)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background:
                            category.isActive !== false
                              ? 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)'
                              : 'linear-gradient(135deg, #28A745 0%, #218838 100%)',
                        }}
                      >
                        {category.isActive !== false ? 'Disable' : 'Enable'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={11} className="border border-gray-200 p-4 text-center text-gray-500">
                  No categories found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Premium Pagination Controls */}
      {filteredCategories.length > 0 && (
        <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
          <div className="text-sm text-gray-700">
            Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
            <span className="font-semibold">{endIndex}</span> of{' '}
            <span className="font-semibold">{totalItems}</span> categories
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
          className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-4 overflow-y-auto pb-4"
          onClick={() => setShowModal(false)}
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
        >
          <div
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">
              {editingCategory ? 'Edit Category' : 'Add Category'}
            </h3>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.name
                        ? pageInfo.columns.name
                        : undefined
                    }
                  >
                    Category Name *
                  </InfoButton>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  placeholder="e.g., Office Supplies, Writing Instruments"
                  className="w-full rounded border px-3 py-2"
                />
              </div>
              <div className="mb-4">
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
                  placeholder="Optional description of the category"
                  className="w-full rounded border px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.minimumQuantity
                        ? pageInfo.columns.minimumQuantity
                        : undefined
                    }
                  >
                    Minimum Quantity Required *
                  </InfoButton>
                </label>
                <input
                  type="number"
                  name="minimumQuantity"
                  value={formData.minimumQuantity || 0}
                  onChange={handleChange}
                  required
                  min="0"
                  className="w-full rounded border px-3 py-2"
                  placeholder="Minimum quantity for low stock alerts"
                />
                <small className="mt-1 block text-sm text-gray-600">
                  When any product in this category reaches below this quantity, a notification will
                  be sent
                </small>
              </div>
              <div className="mb-4">
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.gst
                        ? pageInfo.columns.gst
                        : undefined
                    }
                  >
                    GST (%) *
                  </InfoButton>
                </label>
                <input
                  type="number"
                  name="gst"
                  value={formData.gst || 0}
                  onChange={handleChange}
                  required
                  min="0"
                  max="100"
                  step="0.1"
                  className="w-full rounded border px-3 py-2"
                  placeholder="GST percentage (e.g., 18)"
                />
              </div>
              <div className="mb-4">
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.categoryTag
                        ? pageInfo.columns.categoryTag
                        : undefined
                    }
                  >
                    Category Tag *
                  </InfoButton>
                </label>
                <div className="mt-1 flex flex-col gap-2">
                  {categoryTags.filter((tag) => tag.isActive !== false).length === 0 ? (
                    <p className="text-sm text-gray-500">
                      No category tags available. Please create tags using &quot;Manage Category
                      Tags&quot; button.
                    </p>
                  ) : (
                    categoryTags
                      .filter((tag) => tag.isActive !== false)
                      .map((tag) => (
                        <label key={tag._id} className="flex cursor-pointer items-center gap-2">
                          <input
                            type="radio"
                            name="categoryTag"
                            value={tag.name}
                            checked={formData.categoryTag === tag.name}
                            onChange={() => setFormData({ ...formData, categoryTag: tag.name })}
                            className="h-4 w-4 cursor-pointer"
                          />
                          <span>{tag.name}</span>
                        </label>
                      ))
                  )}
                </div>
                <small className="mt-1 block text-sm text-gray-600">
                  Select the main category tag this category belongs to (e.g., School)
                </small>
              </div>
              <div className="mb-4">
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.subCategories
                        ? pageInfo.columns.subCategories
                        : undefined
                    }
                  >
                    Sub-Categories
                  </InfoButton>
                </label>
                <div>
                  <div className="mb-2 flex gap-2">
                    <input
                      type="text"
                      value={subCategoryInput}
                      onChange={(e) => setSubCategoryInput(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          if (
                            subCategoryInput.trim() &&
                            !formData.subCategories?.includes(subCategoryInput.trim())
                          ) {
                            setFormData({
                              ...formData,
                              subCategories: [
                                ...(formData.subCategories || []),
                                subCategoryInput.trim(),
                              ],
                            });
                            setSubCategoryInput('');
                          }
                        }
                      }}
                      placeholder="Enter sub-category name and press Enter (e.g., A4, A3, Long)"
                      className="flex-1 rounded border px-3 py-2"
                    />
                    <button
                      type="button"
                      className="rounded bg-gray-200 px-4 py-2 hover:bg-gray-300"
                      onClick={() => {
                        if (
                          subCategoryInput.trim() &&
                          !formData.subCategories?.includes(subCategoryInput.trim())
                        ) {
                          setFormData({
                            ...formData,
                            subCategories: [
                              ...(formData.subCategories || []),
                              subCategoryInput.trim(),
                            ],
                          });
                          setSubCategoryInput('');
                        }
                      }}
                    >
                      Add
                    </button>
                  </div>
                  {formData.subCategories && formData.subCategories.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {formData.subCategories.map((subCat, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center gap-1 rounded bg-blue-100 px-2 py-1 text-xs text-blue-800"
                        >
                          {subCat}
                          <button
                            type="button"
                            onClick={() => {
                              setFormData({
                                ...formData,
                                subCategories:
                                  formData.subCategories?.filter((_, i) => i !== index) || [],
                              });
                            }}
                            className="text-sm text-blue-800 hover:text-blue-600"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                  <small className="mt-1 block text-xs text-gray-500">
                    Add sub-categories for this category (e.g., Notebooks can have A4, A3, Long,
                    Ledger)
                  </small>
                </div>
              </div>
              <div className="mb-4">
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.images
                        ? pageInfo.columns.images
                        : undefined
                    }
                  >
                    Category Images *
                  </InfoButton>
                </label>
                {formData.images && formData.images.length > 0 && (
                  <div className="mb-4 flex flex-wrap gap-2">
                    {formData.images.map((imageUrl, index) => {
                      let src = imageUrl;
                      if (imageUrl && !imageUrl.startsWith('http') && !imageUrl.startsWith('/')) {
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
                            alt={`Category ${index + 1}`}
                            className="h-24 w-24 rounded border border-gray-300 object-cover"
                            onError={(e: any) => {
                              e.target.style.display = 'none';
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => removeImage(index)}
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
                    id="category-image-upload"
                  />
                  <label
                    htmlFor="category-image-upload"
                    className={`inline-block cursor-pointer rounded bg-gray-600 px-4 py-2 text-sm text-white hover:bg-gray-700 ${uploadingImages ? 'cursor-not-allowed opacity-60' : ''}`}
                  >
                    {uploadingImages ? 'Uploading...' : 'Add Image'}
                  </label>
                </div>
                <small className="mt-2 block text-xs text-gray-500">
                  Click &quot;Add Image&quot; to upload one or more images. At least one image is
                  required. These images will be displayed on the retail customer/wholesaler
                  dashboards.
                </small>
              </div>
              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="isActive"
                    checked={formData.isActive}
                    onChange={handleChange}
                    className="mr-2"
                  />
                  Active (visible to users)
                </label>
              </div>
              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="showInMobileHomepage"
                    checked={formData.showInMobileHomepage}
                    onChange={(e) =>
                      setFormData({ ...formData, showInMobileHomepage: e.target.checked })
                    }
                    className="mr-2"
                  />
                  Display in homepage (web & mobile)
                </label>
              </div>
              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="isReturnable"
                    checked={formData.isReturnable || false}
                    onChange={(e) =>
                      setFormData({ ...formData, isReturnable: e.target.checked })
                    }
                    className="mr-2"
                  />
                  Returnable Category (allow returns for products under this category)
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
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
                  {editingCategory ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Category Tags Management Modal */}
      {showTagModal && (
        <div
          className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-4 overflow-y-auto pb-4"
          onClick={() => {
            setShowTagModal(false);
            setEditingTag(null);
            setTagFormData({ name: '', description: '', isActive: true });
          }}
        >
          <div
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">Manage Category Tags</h3>

            {/* Add/Edit Tag Form */}
            <form onSubmit={handleTagSubmit} className="mb-6 border-b pb-4">
              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium">Tag Name *</label>
                <input
                  type="text"
                  value={tagFormData.name}
                  onChange={(e) => setTagFormData({ ...tagFormData, name: e.target.value })}
                  required
                  placeholder="e.g., School, Office"
                  className="w-full rounded border px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium">Description</label>
                <textarea
                  value={tagFormData.description}
                  onChange={(e) => setTagFormData({ ...tagFormData, description: e.target.value })}
                  rows={2}
                  placeholder="Tag description (displayed on desktop)"
                  className="w-full rounded border px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={tagFormData.isActive}
                    onChange={(e) => setTagFormData({ ...tagFormData, isActive: e.target.checked })}
                    className="mr-2"
                  />
                  Active
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowTagModal(false);
                    setEditingTag(null);
                    setTagFormData({ name: '', description: '', isActive: true });
                  }}
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
                  {editingTag ? 'Update Tag' : 'Add Tag'}
                </button>
              </div>
            </form>

            {/* Tags List */}
            <div>
              <h4 className="mb-4 text-lg font-semibold">Existing Category Tags</h4>
              {categoryTags.length === 0 ? (
                <p className="text-gray-600">No category tags found</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 bg-white">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                          Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                          Description
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {categoryTags.map((tag) => (
                        <tr key={tag._id}>
                          <td className="whitespace-nowrap px-6 py-4">{tag.name}</td>
                          <td className="px-6 py-4">{tag.description || '-'}</td>
                          <td className="whitespace-nowrap px-6 py-4">
                            <span
                              className={`rounded px-2 py-1 text-xs ${tag.isActive !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                            >
                              {tag.isActive !== false ? 'Active' : 'Hidden'}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4">
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleEditTag(tag)}
                                className="rounded px-3 py-1 text-sm text-white"
                                style={{
                                  background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                                }}
                              >
                                Edit
                              </button>
                              {tag.isActive !== false ? (
                                <button
                                  onClick={() => handleToggleTagStatus(tag)}
                                  className="rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
                                  style={{
                                    background: 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)',
                                  }}
                                >
                                  Hide
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleToggleTagStatus(tag)}
                                  className="rounded bg-green-500 px-3 py-1 text-sm text-white hover:bg-green-600"
                                  style={{
                                    background: 'linear-gradient(135deg, #28A745 0%, #218838 100%)',
                                  }}
                                >
                                  Unhide
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* View Sub-categories Modal */}
      {showSubCategoriesDialog && (
        <div
          className="animate-in fade-in fixed inset-0 z-[130] flex items-center justify-center bg-black/60 duration-200"
          onClick={() => setShowSubCategoriesDialog(false)}
        >
          <div
            className="animate-in zoom-in-95 mx-4 flex max-h-[92vh] w-full max-w-lg transform flex-col rounded-2xl bg-white p-8 shadow-2xl transition-all duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-6 flex flex-shrink-0 items-center justify-between border-b-2 border-gray-100 pb-2">
              <h3 className="text-xl font-black uppercase tracking-tight text-gray-800">
                Sub-categories for <span className="text-blue-600">{viewingCategoryName}</span>
              </h3>
              <button
                onClick={() => setShowSubCategoriesDialog(false)}
                className="transform text-3xl font-light text-gray-300 transition-colors duration-200 hover:rotate-90 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="flex flex-1 flex-wrap gap-2.5 overflow-y-auto py-4">
              {subCategoriesToView.map((subCat, idx) => (
                <span
                  key={idx}
                  className="cursor-default rounded-xl border-2 border-blue-100 bg-blue-50 px-4 py-2 text-xs font-medium uppercase tracking-widest text-blue-700 shadow-sm transition-all hover:border-blue-200 hover:bg-blue-100"
                >
                  {subCat}
                </span>
              ))}
            </div>
            <div className="mt-8 flex flex-shrink-0 justify-end border-t pt-4">
              <button
                onClick={() => setShowSubCategoriesDialog(false)}
                className="rounded-xl bg-gray-900 px-8 py-3 text-[10px] font-bold uppercase tracking-widest text-white shadow-lg transition-all hover:-translate-y-0.5 hover:bg-black hover:shadow-gray-200 active:translate-y-0"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}
        </div>
      </div>
    </div>
  );
}
