'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import { formatDateTimeIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';
import { logger } from '@/utils/logger';

interface PushNotification {
  _id: string;
  title: string;
  message: string;
  link?: string;
  image?: string;
  status: 'published' | 'scheduled';
  scheduledFor?: string;
  deliveredCount: number;
  readCount: number;
  userSegment: string;
  userBehavior: string;
  createdAt: string;
  updatedAt: string;
}

interface Analytics {
  totalDevices: number;
  deliveredCount: number;
  readCount: number;
  deliveryRate: number;
  readRate: number;
}

export default function PushNotificationManagement() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<PushNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showBehaviorPopover, setShowBehaviorPopover] = useState(false);
  const [behaviorSearch, setBehaviorSearch] = useState('');
  const [editingNotification, setEditingNotification] = useState<PushNotification | null>(null);
  const behaviorRef = useRef<HTMLDivElement>(null);
  const [formData, setFormData] = useState({
    title: '',
    message: '',
    link: '',
    image: null as File | null,
    imagePreview: null as string | null,
    scheduledFor: '',
    publishNow: true,
    userSegment: 'all',
    userBehavior: 'none',
  });
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedNotification, setSelectedNotification] = useState<PushNotification | null>(null);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [customSegments, setCustomSegments] = useState<any[]>([]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (behaviorRef.current && !behaviorRef.current.contains(event.target as Node)) {
        setShowBehaviorPopover(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchNotifications();
      fetchPageInfo();
      api
        .get('/customer-segments')
        .then((r) => setCustomSegments(r.data || []))
        .catch((e) => {
          logger.error('Failed to load customer segments', e);
          toast.warning('Could not load customer segments');
        });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, statusFilter]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/push-notifications');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await api.get('/push-notifications', { params });
      setNotifications(response.data || []);
    } catch (error: any) {
      console.error('Error fetching notifications:', error);
      toast.error('Failed to fetch push notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const target = e.target as HTMLInputElement;

    if (type === 'file') {
      const file = target.files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onloadend = () => {
          setFormData((prev) => ({
            ...prev,
            image: file,
            imagePreview: reader.result as string,
          }));
        };
        reader.readAsDataURL(file);
      }
    } else if (type === 'checkbox') {
      setFormData((prev) => ({
        ...prev,
        [name]: target.checked,
        scheduledFor: target.checked ? '' : prev.scheduledFor,
      }));
    } else {
      setFormData((prev) => {
        const updated = { ...prev, [name]: value };
        if (name === 'userSegment') {
          updated.userBehavior = 'none';
        }
        return updated;
      });
    }
  };

  const getSegmentLabel = (segment: string) => {
    switch (segment) {
      case 'all':
        return 'All';
      case 'customers':
        return 'Retail Customers';
      case 'wholesalers':
        return 'Business Customers';
      default:
        return segment;
    }
  };

  const getBehaviorLabel = (behavior: string) => {
    if (!behavior || behavior === 'none') return 'All';
    return behavior
      .split(',')
      .map((b) => b.trim())
      .map((part) => {
        if (part.startsWith('segment_')) {
          const segId = part.replace('segment_', '');
          const seg = customSegments.find((s) => s._id === segId || s.id === segId);
          return seg ? seg.name : part;
        }
        switch (part) {
          case 'none':
            return 'All';
          case 'behavior1':
            return 'Downloaded but no order';
          case 'behavior2':
            return 'Ordered once';
          case 'behavior3':
            return 'Regular (Avg >= 4/month)';
          case 'behavior4':
            return 'Downloaded and irregular (>1 order and <=3 orders per month)';
          default:
            return part;
        }
      })
      .join(', ');
  };

  const getSelectedBehaviors = () => {
    if (!formData.userBehavior || formData.userBehavior === 'none') {
      return ['none'];
    }
    return formData.userBehavior.split(',').map((s) => s.trim()).filter(Boolean);
  };

  const handleToggleBehavior = (val: string) => {
    let newBehaviors: string[];
    if (val === 'none') {
      newBehaviors = ['none'];
    } else {
      const current = getSelectedBehaviors().filter((x) => x !== 'none');
      if (current.includes(val)) {
        newBehaviors = current.filter((x) => x !== val);
        if (newBehaviors.length === 0) {
          newBehaviors = ['none'];
        }
      } else {
        newBehaviors = [...current, val];
      }
    }
    setFormData({
      ...formData,
      userBehavior: newBehaviors.join(','),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title || !formData.message) {
      toast.error('Title and message are required');
      return;
    }

    try {
      const submitData = new FormData();
      submitData.append('title', formData.title);
      submitData.append('message', formData.message);
      submitData.append('link', formData.link || '');
      submitData.append('publishNow', formData.publishNow.toString());

      if (!formData.publishNow && formData.scheduledFor) {
        submitData.append('scheduledFor', formData.scheduledFor);
      }

      if (formData.image) {
        submitData.append('image', formData.image);
      }

      submitData.append('userSegment', formData.userSegment);
      submitData.append('userBehavior', formData.userBehavior);

      if (editingNotification?._id) {
        await api.put(`/push-notifications/${editingNotification._id}`, submitData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        toast.success('Push notification updated successfully');
      } else {
        await api.post('/push-notifications', submitData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        toast.success('Push notification created successfully');
      }

      setShowModal(false);
      setEditingNotification(null);
      setFormData({
        title: '',
        message: '',
        link: '',
        image: null,
        imagePreview: null,
        scheduledFor: '',
        publishNow: true,
        userSegment: 'all',
        userBehavior: 'none',
      });
      fetchNotifications();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed');
    }
  };

  const handleEdit = (notification: PushNotification) => {
    setEditingNotification(notification);
    setFormData({
      title: notification.title || '',
      message: notification.message || '',
      link: notification.link || '',
      image: null,
      imagePreview: notification.image || null,
      scheduledFor: notification.scheduledFor || '',
      publishNow: notification.status === 'published',
      userSegment: notification.userSegment || 'all',
      userBehavior: notification.userBehavior || 'none',
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this notification?')) return;
    try {
      await api.delete(`/push-notifications/${id}`);
      toast.success('Notification deleted successfully');
      fetchNotifications();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to delete notification');
    }
  };

  const handleViewAnalytics = async (notification: PushNotification) => {
    try {
      const response = await api.get(`/push-notifications/${notification._id}/analytics`);
      setAnalytics(response.data);
      setSelectedNotification(notification);
      setShowAnalyticsModal(true);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch analytics');
    }
  };

  const filteredNotifications = notifications.filter((n) => {
    if (statusFilter === 'all') return true;
    return n.status === statusFilter;
  });

  const totalItems = filteredNotifications.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedNotifications = filteredNotifications.slice(startIndex, endIndex);

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

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="rounded-lg bg-white p-6 shadow-md">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h2 className="inline-flex items-center gap-3 text-2xl font-bold">
          <InfoButton
            info={
              user?.role === 'super_admin' && pageInfo.page?.description
                ? pageInfo.page.description
                : undefined
            }
          >
            Push Notification Management
          </InfoButton>
          <RefreshButton onRefresh={fetchNotifications} />
        </h2>
        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border px-3 py-2"
          >
            <option value="all">All Status</option>
            <option value="published">Published</option>
            <option value="scheduled">Scheduled</option>
          </select>
          <button
            onClick={() => {
              setShowModal(true);
              setEditingNotification(null);
              setFormData({
                title: '',
                message: '',
                link: '',
                image: null,
                imagePreview: null,
                scheduledFor: '',
                publishNow: true,
                userSegment: 'all',
                userBehavior: 'none',
              });
            }}
            className="rounded px-4 py-2 text-white"
            style={{
              background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
            }}
          >
            + Create Notification
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px]">
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
                    user?.role === 'super_admin' && pageInfo.columns?.message
                      ? pageInfo.columns.message
                      : undefined
                  }
                >
                  Message
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
                    user?.role === 'super_admin' && pageInfo.columns?.segments
                      ? pageInfo.columns.segments
                      : undefined
                  }
                >
                  Segments
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.behavior
                      ? pageInfo.columns.behavior
                      : undefined
                  }
                >
                  Behavior
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.scheduledFor
                      ? pageInfo.columns.scheduledFor
                      : undefined
                  }
                >
                  Scheduled For
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.delivered
                      ? pageInfo.columns.delivered
                      : undefined
                  }
                >
                  Delivered
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.read
                      ? pageInfo.columns.read
                      : undefined
                  }
                >
                  Read
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
            {paginatedNotifications.length > 0 ? (
              paginatedNotifications.map((notification) => (
                <tr key={notification._id}>
                  <td className="whitespace-nowrap px-6 py-4">{notification.title}</td>
                  <td className="px-6 py-4">{notification.message.substring(0, 50)}...</td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span
                      className={`rounded px-2 py-1 text-xs ${
                        notification.status === 'published'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {notification.status}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {getSegmentLabel(notification.userSegment)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {getBehaviorLabel(notification.userBehavior)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    {notification.scheduledFor ? formatDateTimeIST(notification.scheduledFor) : '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">{notification.deliveredCount}</td>
                  <td className="whitespace-nowrap px-6 py-4">{notification.readCount}</td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewAnalytics(notification)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background: 'linear-gradient(135deg, #17A2B8 0%, #117A8B 100%)',
                        }}
                      >
                        Analytics
                      </button>
                      <button
                        onClick={() => handleEdit(notification)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(notification._id)}
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
            ) : (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                  No notifications found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Premium Pagination Controls */}
      {filteredNotifications.length > 0 && (
        <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
          <div className="text-sm text-gray-700">
            Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
            <span className="font-semibold">{endIndex}</span> of{' '}
            <span className="font-semibold">{totalItems}</span> notifications
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

      {/* Create/Edit Modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={() => setShowModal(false)}
        >
          <div
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">
              {editingNotification ? 'Edit Push Notification' : 'Create Push Notification'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.title
                        ? pageInfo.columns.title
                        : undefined
                    }
                  >
                    Title *
                  </InfoButton>
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded border px-3 py-2"
                />
              </div>
              <div>
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.message
                        ? pageInfo.columns.message
                        : undefined
                    }
                  >
                    Message *
                  </InfoButton>
                </label>
                <textarea
                  name="message"
                  value={formData.message}
                  onChange={handleInputChange}
                  required
                  rows={4}
                  className="w-full rounded border px-3 py-2"
                />
              </div>
              <div>
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.link
                        ? pageInfo.columns.link
                        : undefined
                    }
                  >
                    Link (Optional)
                  </InfoButton>
                </label>
                <input
                  type="text"
                  name="link"
                  value={formData.link}
                  onChange={handleInputChange}
                  placeholder="/products/123 or https://example.com"
                  className="w-full rounded border px-3 py-2"
                />
                <small className="text-xs text-gray-500">Can be a relative path or full URL</small>
              </div>
              <div>
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.image
                        ? pageInfo.columns.image
                        : undefined
                    }
                  >
                    Image (Optional)
                  </InfoButton>
                </label>
                <input
                  type="file"
                  name="image"
                  accept="image/*"
                  onChange={handleInputChange}
                  className="w-full rounded border px-3 py-2"
                />
                {formData.imagePreview && (
                  <img
                    src={formData.imagePreview}
                    alt="Preview"
                    className="mt-2 max-h-48 max-w-xs object-contain"
                  />
                )}
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.segments
                          ? pageInfo.columns.segments
                          : undefined
                      }
                    >
                      User Segments
                    </InfoButton>
                  </label>
                  <select
                    name="userSegment"
                    value={formData.userSegment}
                    onChange={handleInputChange as any}
                    className="w-full rounded border bg-white px-3 py-2"
                  >
                    <option value="all">All</option>
                    <option value="customers">Retail Customers</option>
                    <option value="wholesalers">Business Customers</option>
                  </select>
                </div>
                <div className="flex flex-col gap-2 relative" ref={behaviorRef}>
                  <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.behavior
                          ? pageInfo.columns.behavior
                          : undefined
                      }
                    >
                      User Behaviour
                    </InfoButton>
                  </label>
                  <div className="relative">
                    {/* Input field trigger */}
                    <div
                      onClick={() => setShowBehaviorPopover(!showBehaviorPopover)}
                      className="w-full min-h-[42px] cursor-pointer rounded border bg-white px-3 py-2 pr-10 text-sm text-gray-700 flex flex-wrap gap-1.5 items-center transition-all duration-200 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 hover:border-gray-400 shadow-sm"
                    >
                      {getSelectedBehaviors().length === 0 || getSelectedBehaviors().includes('none') ? (
                        <span className="text-gray-400">All Users</span>
                      ) : (
                        getSelectedBehaviors().map((val) => {
                          let label = 'All';
                          if (val.startsWith('segment_')) {
                            const segId = val.substring('segment_'.length);
                            const seg = customSegments.find((s) => (s._id || s.id) === segId);
                            label = seg ? seg.name : 'Custom Segment';
                          } else {
                            switch (val) {
                              case 'behavior1':
                                label = 'Downloaded but no order';
                                break;
                              case 'behavior2':
                                label = 'Ordered once';
                                break;
                              case 'behavior3':
                                label = 'Regular (Avg >= 4/month)';
                                break;
                              case 'behavior4':
                                label = 'Downloaded and irregular (>1 order and <=3 orders per month)';
                                break;
                              default:
                                label = 'All';
                            }
                          }
                          return (
                            <span
                              key={val}
                              className="inline-flex items-center gap-1 rounded bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-700 border border-indigo-200"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {label}
                              {val !== 'none' && (
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleToggleBehavior(val);
                                  }}
                                  className="text-indigo-500 hover:text-indigo-800 font-bold ml-0.5 focus:outline-none"
                                >
                                  &times;
                                </button>
                              )}
                            </span>
                          );
                        })
                      )}
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                        <svg className={`h-4 w-4 transition-transform duration-200 ${showBehaviorPopover ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>

                    {/* Popover Dropdown */}
                    {showBehaviorPopover && (
                      <div className="absolute left-0 right-0 z-[150] mt-1.5 max-h-[350px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl flex flex-col">
                        {/* Search Box */}
                        <div className="p-2.5 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                          <svg className="h-4 w-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                          <input
                            type="text"
                            placeholder="Search segments..."
                            value={behaviorSearch}
                            onChange={(e) => setBehaviorSearch(e.target.value)}
                            className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 outline-none"
                            onClick={(e) => e.stopPropagation()}
                          />
                          {behaviorSearch && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setBehaviorSearch('');
                              }}
                              className="text-slate-400 hover:text-slate-600 text-xs font-semibold"
                            >
                              Clear
                            </button>
                          )}
                        </div>

                        {/* Options List */}
                        <div className="flex-1 overflow-y-auto p-2.5 space-y-3">
                          {(() => {
                            const searchLower = behaviorSearch.toLowerCase();
                            
                            const showAllOption = 'all users'.includes(searchLower) || 'all'.includes(searchLower);
                            
                            const defaultBehaviors = [
                              { value: 'behavior1', title: 'Downloaded but no order', desc: 'Users who registered but have never placed an order.' },
                              { value: 'behavior2', title: 'Ordered once', desc: 'Users who have placed exactly one order.' },
                              { value: 'behavior3', title: 'Regular (Avg >= 4/month)', desc: 'Users with average of 4 or more orders per month (last 90 days).' },
                              { value: 'behavior4', title: 'Downloaded and irregular (>1 order and <=3 orders per month)', desc: 'Users with more than 1 and up to 3 orders per month (last 90 days).' }
                            ].filter(b => b.title.toLowerCase().includes(searchLower) || b.desc.toLowerCase().includes(searchLower));

                            const filteredSegments = (formData.userSegment === 'customers'
                              ? customSegments.filter((s) => s.type === 'retail')
                              : formData.userSegment === 'wholesalers'
                                ? customSegments.filter((s) => s.type === 'business')
                                : customSegments
                            ).filter(s => s.name.toLowerCase().includes(searchLower));

                            const noResults = !showAllOption && defaultBehaviors.length === 0 && filteredSegments.length === 0;

                            if (noResults) {
                              return (
                                <div className="py-6 text-center text-sm text-gray-400 italic">
                                  No segments found
                                </div>
                              );
                            }

                            return (
                              <>
                                {/* General Section */}
                                {showAllOption && (
                                  <div className="space-y-0.5">
                                    <h4 className="px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">General</h4>
                                    <label
                                      onClick={(e) => e.stopPropagation()}
                                      className="flex items-center gap-3 p-1 rounded hover:bg-indigo-50/55 cursor-pointer transition-colors"
                                    >
                                      <input
                                        type="checkbox"
                                        checked={getSelectedBehaviors().includes('none')}
                                        onChange={() => handleToggleBehavior('none')}
                                        className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                      />
                                      <span className="text-sm text-gray-800">All Users</span>
                                    </label>
                                  </div>
                                )}

                                {/* Default Behaviors Section */}
                                {defaultBehaviors.length > 0 && (
                                  <div className="space-y-0.5">
                                    <h4 className="px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">Default Behaviors</h4>
                                    {defaultBehaviors.map((beh) => (
                                      <label
                                        key={beh.value}
                                        onClick={(e) => e.stopPropagation()}
                                        className="flex items-center gap-3 p-1 rounded hover:bg-indigo-50/55 cursor-pointer transition-colors"
                                      >
                                        <input
                                          type="checkbox"
                                          checked={getSelectedBehaviors().includes(beh.value)}
                                          onChange={() => handleToggleBehavior(beh.value)}
                                          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                        />
                                        <span className="text-sm text-gray-800">{beh.title}</span>
                                      </label>
                                    ))}
                                  </div>
                                )}

                                {/* Custom Segments Section */}
                                {filteredSegments.length > 0 && (
                                  <div className="space-y-0.5">
                                    <h4 className="px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">Custom Segments</h4>
                                    {filteredSegments.map((seg) => {
                                      const val = `segment_${seg._id || seg.id}`;
                                      return (
                                        <label
                                          key={val}
                                          onClick={(e) => e.stopPropagation()}
                                          className="flex items-center gap-3 p-1 rounded hover:bg-indigo-50/55 cursor-pointer transition-colors"
                                        >
                                          <input
                                            type="checkbox"
                                            checked={getSelectedBehaviors().includes(val)}
                                            onChange={() => handleToggleBehavior(val)}
                                            className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                          />
                                          <span className="text-sm text-gray-800">
                                            {seg.name} ({seg.userIds?.length || 0} users)
                                          </span>
                                        </label>
                                      );
                                    })}
                                  </div>
                                )}
                              </>
                            );
                          })()}
                        </div>

                        {/* Footer */}
                        <div className="px-3.5 py-2.5 border-t border-slate-100 bg-slate-50 flex justify-between items-center">
                          <span className="text-xs font-semibold text-gray-500">
                            {getSelectedBehaviors().includes('none') 
                              ? 'All Selected' 
                              : `${getSelectedBehaviors().length} selected`}
                          </span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowBehaviorPopover(false);
                            }}
                            className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-xs font-bold transition-colors shadow-sm"
                          >
                            Done
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="publishNow"
                    checked={formData.publishNow}
                    onChange={handleInputChange}
                    className="mr-2"
                  />
                  Publish Now
                </label>
              </div>
              {!formData.publishNow && (
                <div>
                  <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.scheduledFor
                          ? pageInfo.columns.scheduledFor
                          : undefined
                      }
                    >
                      Schedule For
                    </InfoButton>
                  </label>
                  <input
                    type="datetime-local"
                    name="scheduledFor"
                    value={formData.scheduledFor}
                    onChange={handleInputChange}
                    required={!formData.publishNow}
                    className="w-full rounded border px-3 py-2"
                  />
                </div>
              )}
              <div className="mt-6 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded bg-gray-100 px-4 py-2 text-gray-600 hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded bg-green-500 px-4 py-2 text-white hover:bg-green-600"
                >
                  {editingNotification ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAnalyticsModal && analytics && selectedNotification && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={() => setShowAnalyticsModal(false)}
        >
          <div
            className="w-full max-w-md rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">Analytics: {selectedNotification.title}</h3>
            <div className="space-y-4">
              <div>
                <strong>Total Devices:</strong> {analytics.totalDevices}
              </div>
              <div>
                <strong>Delivered:</strong> {analytics.deliveredCount} (
                {analytics.deliveryRate.toFixed(1)}%)
              </div>
              <div>
                <strong>Read:</strong> {analytics.readCount} ({analytics.readRate.toFixed(1)}%)
              </div>
            </div>
            <button
              onClick={() => setShowAnalyticsModal(false)}
              className="mt-6 w-full rounded bg-gray-900 px-4 py-2 text-white hover:bg-gray-800"
            >
              Close
            </button>
          </div>
        </div>
      )}


    </div>
  );
}
