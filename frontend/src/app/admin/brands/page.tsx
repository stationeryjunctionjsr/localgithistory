'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { getImageUrl } from '@/utils/imageUrl';
import InfoButton from '@/components/InfoButton';
import RefreshButton from '@/components/Admin/RefreshButton';

interface Brand {
  _id?: string;
  name: string;
  logoUrl?: string;
  isActive?: boolean;
  showInMobileHomepage?: boolean;
}

export default function BrandManagement() {
  const { user } = useAuth();
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBrand, setEditingBrand] = useState<Brand | null>(null);
  const [formData, setFormData] = useState<Brand>({
    name: '',
    logoUrl: '',
    showInMobileHomepage: false,
  });
  const [uploadingImage, setUploadingImage] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [sortColumn, setSortColumn] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
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
      fetchBrands();
      fetchPageInfo();
    } else {
      setLoading(false);
    }
  }, [user]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/brand-management');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchBrands = async () => {
    try {
      const response = await api.get('/brands');
      setBrands(response.data || []);
    } catch (error: any) {
      const msg = error.response?.data?.message || error.response?.statusText || error.message;
      toast.error(msg || 'Failed to fetch brands');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingImage(true);
    try {
      const fd = new FormData();
      fd.append('image', file);
      const res = await api.post('/brands/upload-logo', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const url = (res.data?.logoUrl ?? res.data?.imageUrl) || '';
      if (!url) {
        toast.error('Upload succeeded but no logo URL returned');
        return;
      }
      setFormData((prev) => ({ ...prev, logoUrl: url }));
      toast.success('Logo uploaded');
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Failed to upload logo');
    } finally {
      setUploadingImage(false);
      e.target.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name?.trim()) {
      toast.error('Name is required');
      return;
    }
    try {
      const payload = {
        name: formData.name.trim(),
        logoUrl: formData.logoUrl ?? '',
        showInMobileHomepage: formData.showInMobileHomepage || false,
      };
      if (editingBrand?._id) {
        await api.put(`/brands/${editingBrand._id}`, payload);
        toast.success('Brand updated successfully');
      } else {
        await api.post('/brands', payload);
        toast.success('Brand created successfully');
      }
      setShowModal(false);
      setEditingBrand(null);
      setFormData({ name: '', logoUrl: '' });
      fetchBrands();
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Operation failed');
    }
  };

  const handleEdit = (b: Brand) => {
    setEditingBrand(b);
    setFormData({
      name: b.name || '',
      logoUrl: b.logoUrl || '',
      showInMobileHomepage: b.showInMobileHomepage || false,
    });
    setShowModal(true);
  };

  const handleToggleActive = async (brand: Brand) => {
    try {
      await api.put(`/brands/${brand._id}`, { isActive: !brand.isActive });
      toast.success(`Brand ${brand.isActive ? 'disabled' : 'enabled'} successfully`);
      fetchBrands();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (err: any) {
      toast.error('Failed to update brand status');
    }
  };

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }
  if (loading) return <div>Loading...</div>;

  const filteredBrands = brands.filter((brand) => {
    const matchesSearch = brand.name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && brand.isActive !== false) ||
      (statusFilter === 'inactive' && brand.isActive === false);

    return matchesSearch && matchesStatus;
  });

  const sortedBrands = [...filteredBrands].sort((a, b) => {
    if (!sortColumn) return 0;

    let valA: any = a[sortColumn as keyof Brand] ?? '';
    let valB: any = b[sortColumn as keyof Brand] ?? '';

    // Handle custom sorting fields
    if (sortColumn === 'status' || sortColumn === 'isActive') {
      valA = a.isActive !== false ? 'Active' : 'Inactive';
      valB = b.isActive !== false ? 'Active' : 'Inactive';
    }

    if (typeof valA === 'string' && typeof valB === 'string') {
      return sortDirection === 'asc'
        ? valA.localeCompare(valB)
        : valB.localeCompare(valA);
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

  const totalItems = filteredBrands.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedBrands = sortedBrands.slice(startIndex, endIndex);
  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow h-full flex flex-col min-h-0">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
              <InfoButton
                info={
                  user?.role === 'super_admin' && pageInfo.page?.description
                    ? pageInfo.page.description
                    : undefined
                }
              >
                Brand Management
              </InfoButton>
              <RefreshButton onRefresh={fetchBrands} />
            </h1>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowModal(true);
                  setEditingBrand(null);
                  setFormData({ name: '', logoUrl: '', showInMobileHomepage: false });
                }}
                className="rounded px-4 py-2 text-white"
                style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
              >
                Add Brand
              </button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3 flex-shrink-0">
            <div>
              <input
                type="text"
                placeholder="Search by brand name..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full rounded border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as any);
                  setCurrentPage(1);
                }}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="all">All Status</option>
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
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
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.logo
                            ? pageInfo.columns.logo
                            : undefined
                        }
                      >
                        Logo
                      </InfoButton>
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
                  <th className="border border-gray-200 p-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <span
                        onClick={() => handleSort('showInMobileHomepage')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.showInHomepage
                              ? pageInfo.columns.showInHomepage
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
                {paginatedBrands.length > 0 ? (
                  paginatedBrands.map((b) => (
                    <tr key={b._id} className="hover:bg-gray-50">
                      <td className="border border-gray-200 p-2">{b.name || '-'}</td>
                      <td className="border border-gray-200 p-2">
                        {b.logoUrl ? (
                          <img
                            src={getImageUrl(b.logoUrl) || ''}
                            alt={b.name}
                            className="h-12 w-12 object-contain"
                            onError={(e: any) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        ) : (
                          <span className="text-gray-400">No logo</span>
                        )}
                      </td>
                      <td className="border border-gray-200 p-2">
                        <span
                          className={`rounded px-2 py-1 text-xs ${b.isActive !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                        >
                          {b.isActive !== false ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="border border-gray-200 p-2 text-center">
                        <input
                          type="checkbox"
                          checked={b.showInMobileHomepage || false}
                          onChange={async () => {
                            try {
                              await api.put(`/brands/${b._id}`, {
                                showInMobileHomepage: !b.showInMobileHomepage,
                              });
                              toast.success('Homepage visibility updated');
                              fetchBrands();
                            // eslint-disable-next-line unused-imports/no-unused-vars
                            } catch (err) {
                              toast.error('Failed to update mobile visibility');
                            }
                          }}
                          className="h-4 w-4 cursor-pointer"
                        />
                      </td>
                      <td className="border border-gray-200 p-2">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleEdit(b)}
                            className="rounded px-3 py-1 text-sm text-white"
                            style={{
                              background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                            }}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleToggleActive(b)}
                            className="rounded px-3 py-1 text-sm text-white"
                            style={{
                              background:
                                b.isActive !== false
                                  ? 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)'
                                  : 'linear-gradient(135deg, #28A745 0%, #218838 100%)',
                            }}
                          >
                            {b.isActive !== false ? 'Disable' : 'Enable'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="border border-gray-200 p-4 text-center text-gray-500">
                      No brands found. Add a brand to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Premium Pagination Controls */}
          {totalItems > 0 && (
            <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-slate-200 pt-4 sm:flex-row">
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
          className="fixed inset-0 z-[110] flex items-start justify-center bg-black/50 pt-24"
          onClick={() => {
            setShowModal(false);
            setEditingBrand(null);
            setFormData({ name: '', logoUrl: '', showInMobileHomepage: false });
          }}
        >
          <div
            className="mx-4 max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">{editingBrand ? 'Edit Brand' : 'Add Brand'}</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
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
                  placeholder="e.g. Flair, Doms"
                  className="w-full rounded border px-3 py-2"
                />
              </div>
              <div>
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.logo
                        ? pageInfo.columns.logo
                        : undefined
                    }
                  >
                    Logo
                  </InfoButton>
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleLogoUpload}
                  disabled={uploadingImage}
                  className="w-full rounded border px-3 py-2"
                />
                {uploadingImage && <p className="mt-1 text-sm text-gray-500">Uploading...</p>}
                {formData.logoUrl && (
                  <div className="mt-2">
                    <img
                      src={getImageUrl(formData.logoUrl) || ''}
                      alt="Logo"
                      className="max-h-20 max-w-[120px] rounded border object-contain"
                      onError={(e: any) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="showInMobileHomepage"
                  name="showInMobileHomepage"
                  checked={formData.showInMobileHomepage}
                  onChange={(e) =>
                    setFormData({ ...formData, showInMobileHomepage: e.target.checked })
                  }
                  className="h-4 w-4 cursor-pointer"
                />
                <label
                  htmlFor="showInMobileHomepage"
                  className="inline-flex cursor-pointer items-center gap-1 text-sm font-medium"
                >
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.showInHomepage
                        ? pageInfo.columns.showInHomepage
                        : undefined
                    }
                  >
                    Display in homepage (web & mobile)
                  </InfoButton>
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingBrand(null);
                    setFormData({ name: '', logoUrl: '', showInMobileHomepage: false });
                  }}
                  className="rounded bg-gray-200 px-4 py-2"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded px-4 py-2 text-white"
                  style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
                >
                  {editingBrand ? 'Update' : 'Create'}
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
