'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { IMAGE_PLACEHOLDER_DATA_URI } from '@/utils/imageUrl';
import VisibilityControls from '@/components/Admin/VisibilityControls';
import InfoButton from '@/components/InfoButton';
import RefreshButton from '@/components/Admin/RefreshButton';

interface Banner {
  _id?: string;
  title: string;
  description?: string;
  imageUrl?: string;
  image?: string;
  position: string;
  targetAudience: string;
  isActive?: boolean;
  isPublished?: boolean;
  startDate?: string;
  endDate?: string;
  userSegments?: string[];
  visibilityRules?: any[];
  linkUrl?: string;
}

const getImageUrl = (imageUrl?: string) => {
  if (!imageUrl) return '';
  if (imageUrl.startsWith('http')) return imageUrl;
  const backendUrl =
    process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || '';
  return `${backendUrl}${imageUrl.startsWith('/') ? imageUrl : '/' + imageUrl}`;
};

export default function BannerManagement() {
  const { user } = useAuth();
  const [banners, setBanners] = useState<Banner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBanner, setEditingBanner] = useState<Banner | null>(null);
  const [formData, setFormData] = useState<Partial<Banner>>({
    title: '',
    description: '',
    imageUrl: '',
    position: 'homepage',
    targetAudience: 'all',
    isActive: true,
    isPublished: false,
    startDate: new Date().toISOString().split('T')[0],
    endDate: '',
    userSegments: ['all'],
    visibilityRules: [],
    linkUrl: '',
  });
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [imageDimensions, setImageDimensions] = useState<{ width: number; height: number } | null>(
    null
  );
  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });

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
      fetchBanners();
      fetchPageInfo();
    }
  }, [user]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/banner-management');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchBanners = async () => {
    try {
      const response = await api.get('/banners');
      setBanners(response.data || []);
      setLoading(false);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch banners');
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

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Get image dimensions
    const img = new Image();
    img.onload = () => {
      setImageDimensions({ width: img.width, height: img.height });
    };
    img.src = URL.createObjectURL(file);

    setUploadingImage(true);
    try {
      const formDataUpload = new FormData();
      formDataUpload.append('image', file);

      try {
        const response = await api.post('/banners/upload-image', formDataUpload, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        setFormData({
          ...formData,
          imageUrl: response.data.imageUrl || response.data.image,
        });
      // eslint-disable-next-line unused-imports/no-unused-vars
      } catch (error: any) {
        const formDataUpload2 = new FormData();
        formDataUpload2.append('images', file);
        const response = await api.post('/products/upload-images', formDataUpload2, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        const imageUrls = response.data.images || [];
        if (imageUrls.length > 0) {
          setFormData({
            ...formData,
            imageUrl: imageUrls[0],
          });
        }
      }
      setImageFile(file);
    } catch (error: any) {
      toast.error('Failed to upload image: ' + (error.response?.data?.message || error.message));
    } finally {
      setUploadingImage(false);
      e.target.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const submitData = {
        ...formData,
        imageUrl: formData.imageUrl || formData.image,
      };

      if (editingBanner?._id) {
        await api.put(`/banners/${editingBanner._id}`, submitData);
        toast.success('Banner updated successfully');
      } else {
        await api.post('/banners', submitData);
        toast.success('Banner created successfully');
      }
      setShowModal(false);
      setEditingBanner(null);
      setFormData({
        title: '',
        description: '',
        imageUrl: '',
        position: 'homepage',
        targetAudience: 'all',
        isActive: true,
        isPublished: false,
        startDate: '',
        endDate: '',
        userSegments: ['all'],
        visibilityRules: [],
        linkUrl: '',
      });
      setImageDimensions(null);
      setImageFile(null);
      fetchBanners();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed');
    }
  };

  const handleEdit = (banner: Banner) => {
    setEditingBanner(banner);
    setFormData({
      title: banner.title || '',
      description: banner.description || '',
      imageUrl: banner.imageUrl || banner.image || '',
      position: banner.position || 'homepage',
      targetAudience: banner.targetAudience || 'all',
      isActive: banner.isActive !== false,
      isPublished: banner.isPublished || false,
      startDate: banner.startDate ? banner.startDate.split('T')[0] : '',
      endDate: banner.endDate ? banner.endDate.split('T')[0] : '',
      userSegments: banner.userSegments || ['all'],
      visibilityRules: banner.visibilityRules || [],
      linkUrl: banner.linkUrl || '',
    });
    setImageFile(null);
    setImageDimensions(null);
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this banner?')) return;
    try {
      await api.delete(`/banners/${id}`);
      toast.success('Banner deleted successfully');
      fetchBanners();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to delete banner');
    }
  };

  const handleTogglePublish = async (banner: Banner) => {
    if (!banner._id) return;
    try {
      await api.put(`/banners/${banner._id}`, { isPublished: !banner.isPublished });
      toast.success(`Banner ${!banner.isPublished ? 'published' : 'unpublished'} successfully`);
      fetchBanners();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to update banner status');
    }
  };

  const filteredBanners = banners.filter(
    (b) =>
      (b.title?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (b.description?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (b.position?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  const totalItems = filteredBanners.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedBanners = filteredBanners.slice(startIndex, endIndex);


  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="rounded-lg bg-white p-6 shadow-md">
      <div className="mb-6 flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
        <h2 className="inline-flex items-center gap-3 text-3xl font-bold">
          <InfoButton
            info={
              user?.role === 'super_admin' && pageInfo.page?.description
                ? pageInfo.page.description
                : undefined
            }
          >
            Banner Management
          </InfoButton>
          <RefreshButton onRefresh={fetchBanners} />
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setShowModal(true);
              setEditingBanner(null);
              setFormData({
                title: '',
                description: '',
                imageUrl: '',
                position: 'homepage',
                targetAudience: 'all',
                isActive: true,
                isPublished: false,
                startDate: new Date().toISOString().split('T')[0],
                endDate: '',
                userSegments: ['all'],
                visibilityRules: [],
                linkUrl: '',
              });
              setImageDimensions(null);
            }}
            className="whitespace-nowrap rounded px-4 py-2 text-white"
            style={{
              background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
            }}
          >
            Add Banner
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div className="min-w-[300px] flex-1">
          <input
            type="text"
            placeholder="Search banners..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full rounded-lg border border-gray-300 px-4 py-2"
          />
        </div>
      </div>


      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.title
                      ? pageInfo.columns.title
                      : undefined
                  }
                >
                  Title
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.position
                      ? pageInfo.columns.position
                      : undefined
                  }
                >
                  Position
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.audience
                      ? pageInfo.columns.audience
                      : undefined
                  }
                >
                  Target Audience
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
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
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
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
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.published
                      ? pageInfo.columns.published
                      : undefined
                  }
                >
                  Published
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
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
          <tbody className="divide-y divide-gray-200 bg-white">
            {paginatedBanners.length > 0 ? (
              paginatedBanners.map((banner) => (
                <tr key={banner._id}>
                  <td className="whitespace-nowrap px-6 py-4">{banner.title || 'Untitled'}</td>
                  <td className="whitespace-nowrap px-6 py-4">{banner.position}</td>
                  <td className="whitespace-nowrap px-6 py-4">{banner.targetAudience}</td>
                  <td className="whitespace-nowrap px-6 py-4">
                    {banner.imageUrl || banner.image ? (
                      <img
                        src={getImageUrl(banner.imageUrl || banner.image)}
                        alt={banner.title}
                        className="h-12 w-24 rounded object-cover"
                        onError={(e: any) => {
                          e.target.src = IMAGE_PLACEHOLDER_DATA_URI;
                        }}
                      />
                    ) : (
                      'No image'
                    )}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span
                      className={`rounded px-2 py-1 text-xs ${banner.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {banner.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span
                      className={`rounded px-2 py-1 text-xs ${banner.isPublished ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}
                    >
                      {banner.isPublished ? 'Published' : 'Draft'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(banner)}
                        className="rounded bg-amber-400 px-3 py-1 text-sm text-white"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleTogglePublish(banner)}
                        className={`rounded px-3 py-1 text-sm text-white ${banner.isPublished ? 'bg-orange-500' : 'bg-green-500'}`}
                      >
                        {banner.isPublished ? 'Unpublish' : 'Publish'}
                      </button>
                      <button
                        onClick={() => banner._id && handleDelete(banner._id)}
                        className="rounded bg-red-500 px-3 py-1 text-sm text-white"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                  No banners found
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


      {showModal && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={() => {
            setShowModal(false);
            setImageFile(null);
          }}
        >
          <div
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">
              {editingBanner ? 'Edit Banner' : 'Add Banner'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                <h4 className="text-sm font-bold text-slate-700">General Information</h4>
                <div className="space-y-4">
                  <div>
                    <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium text-slate-600">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.title
                            ? pageInfo.columns.title
                            : undefined
                        }
                      >
                        Title
                      </InfoButton>
                    </label>
                    <input
                      type="text"
                      name="title"
                      value={formData.title}
                      onChange={handleChange}
                      placeholder="Optional title"
                      className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium text-slate-600">
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
                      className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                <h4 className="text-sm font-bold text-slate-700">Media Assets</h4>
                <div className="space-y-4">
                  <label className="mb-1 block text-sm font-medium text-slate-600">
                    Upload Image *
                  </label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    disabled={uploadingImage}
                    className="w-full rounded border bg-white px-3 py-2 text-sm"
                  />
                  {uploadingImage && (
                    <p className="mt-1 animate-pulse text-sm text-gray-600">Uploading...</p>
                  )}
                  {formData.imageUrl && (
                    <div className="mt-2 space-y-2">
                      <img
                        src={getImageUrl(formData.imageUrl)}
                        alt="Banner preview"
                        className="max-h-48 max-w-full rounded border-2 border-slate-200 shadow-sm"
                      />
                      {imageDimensions && (
                        <div className="flex items-center gap-2 rounded-lg border border-green-100 bg-green-50 p-2 italic">
                          <p className="text-xs text-green-700">
                            📏 <strong>Current Size:</strong> {imageDimensions.width} x{' '}
                            {imageDimensions.height} px
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-sm font-bold text-slate-700">Display Settings & Redirection</h4>
                <VisibilityControls
                  userSegments={formData.userSegments || ['all']}
                  visibilityRules={formData.visibilityRules || []}
                  linkUrl={formData.linkUrl}
                  onLinkChange={(url) => setFormData({ ...formData, linkUrl: url })}
                  onChange={(data) => setFormData({ ...formData, ...data })}
                />
              </div>

              <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
                <h4 className="text-sm font-bold text-slate-700">Schedule & Status</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium text-slate-600">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.dates
                            ? pageInfo.columns.dates
                            : undefined
                        }
                      >
                        Start Date
                      </InfoButton>
                    </label>
                    <input
                      type="date"
                      name="startDate"
                      value={formData.startDate}
                      onChange={handleChange}
                      className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-600">
                      End Date
                    </label>
                    <input
                      type="date"
                      name="endDate"
                      value={formData.endDate}
                      onChange={handleChange}
                      className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                    />
                  </div>
                </div>
                <div className="flex gap-6 pt-2">
                  <label className="flex cursor-pointer items-center text-sm font-medium text-slate-600">
                    <input
                      type="checkbox"
                      name="isActive"
                      checked={formData.isActive}
                      onChange={handleChange}
                      className="mr-2 h-4 w-4 rounded text-green-600 focus:ring-green-500"
                    />
                    Active
                  </label>
                  <label className="flex cursor-pointer items-center text-sm font-medium text-slate-600">
                    <input
                      type="checkbox"
                      name="isPublished"
                      checked={formData.isPublished}
                      onChange={handleChange}
                      className="mr-2 h-4 w-4 rounded text-green-600 focus:ring-green-500"
                    />
                    Published
                  </label>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setImageFile(null);
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
                  {editingBanner ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
