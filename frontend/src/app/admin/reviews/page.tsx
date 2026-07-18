'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateTimeIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';
import InfoButton from '@/components/InfoButton';

interface Review {
  _id: string;
  productId: string;
  userId: string;
  userName: string;
  rating: number;
  comment: string;
  classification: string;
  status: 'pending' | 'approved' | 'removed';
  createdAt?: string;
}

interface Classification {
  _id: string;
  name: string;
  isActive: boolean;
}

export default function ReviewManagement() {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [classifications, setClassifications] = useState<Classification[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'approved' | 'removed' | 'classifications'>('pending');
  const [showClassModal, setShowClassModal] = useState(false);
  const [editingClass, setEditingClass] = useState<Classification | null>(null);
  const [classFormName, setClassFormName] = useState('');
  const [submittingClass, setSubmittingClass] = useState(false);

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

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchData();
    }
    setCurrentPage(1);
  }, [user, activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'classifications') {
        const classRes = await api.get('/reviews/admin/classifications');
        setClassifications(classRes.data || []);
      } else {
        const reviewRes = await api.get('/reviews/admin/list', {
          params: { status_filter: activeTab }
        });
        setReviews(reviewRes.data || []);
      }
      setLoading(false);
    } catch (err: any) {
      console.error('Failed to fetch data', err);
      toast.error('Failed to load data from server.');
      setLoading(false);
    }
  };

  const handleApproveReview = async (reviewId: string) => {
    try {
      await api.post(`/reviews/admin/${reviewId}/approve`);
      toast.success('Review approved successfully');
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to approve review');
    }
  };

  const handleRejectReview = async (reviewId: string) => {
    try {
      await api.post(`/reviews/admin/${reviewId}/remove`);
      toast.success('Review hidden/removed');
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to remove review');
    }
  };

  const handleClassSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = classFormName.trim();
    if (!name) {
      toast.error('Name cannot be empty');
      return;
    }

    setSubmittingClass(true);
    try {
      if (editingClass) {
        await api.put(`/reviews/admin/classifications/${editingClass._id}`, { name });
        toast.success('Classification updated successfully');
      } else {
        await api.post('/reviews/admin/classifications', { name });
        toast.success('Classification created successfully');
      }
      setShowClassModal(false);
      setEditingClass(null);
      setClassFormName('');
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || 'Failed to save classification');
    } finally {
      setSubmittingClass(false);
    }
  };

  const handleToggleClassActive = async (cls: Classification) => {
    try {
      await api.put(`/reviews/admin/classifications/${cls._id}`, { isActive: !cls.isActive });
      toast.success(`Classification ${cls.isActive ? 'deactivated' : 'activated'} successfully`);
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to update classification status');
    }
  };

  const totalItems = reviews.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedReviews = reviews.slice(startIndex, endIndex);

  if (user?.role !== 'super_admin') {
    return (
      <div className="flex min-h-[50vh] items-center justify-center bg-gray-50 rounded-lg p-8 text-center text-red-500 font-semibold border border-red-100">
        Access Denied: Admin role required.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="inline-flex items-center gap-3 text-2xl font-bold text-gray-900">
            Review & Rating Moderation <RefreshButton onRefresh={fetchData} />
          </h1>
          <p className="text-sm text-gray-500 mt-1">Manage customer product reviews and review classifications</p>
        </div>
        <div className="flex gap-2">
          {activeTab === 'classifications' && (
            <button
              onClick={() => {
                setEditingClass(null);
                setClassFormName('');
                setShowClassModal(true);
              }}
              className="rounded-lg bg-[#28A745] hover:bg-[#218838] px-4 py-2 text-sm font-bold text-white transition-all shadow-sm"
            >
              Add Classification
            </button>
          )}
        </div>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-gray-100 mb-6 flex-wrap">
        {[
          { id: 'pending', label: 'Pending Moderation' },
          { id: 'approved', label: 'Approved Reviews' },
          { id: 'removed', label: 'Hidden / Rejected' },
          { id: 'classifications', label: 'Manage Classifications' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`border-b-2 px-5 py-3 text-sm font-bold transition-all ${
              activeTab === tab.id
                ? 'border-[#ff3f6c] text-[#ff3f6c]'
                : 'border-transparent text-gray-500 hover:text-gray-900 hover:border-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex min-h-[300px] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-[#ff3f6c]" />
        </div>
      ) : activeTab === 'classifications' ? (
        /* Classifications view */
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="The name of this review classification (e.g. Quality, Price)">Name</InfoButton></th>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="Whether this classification is currently active and available for customers to select">Status</InfoButton></th>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="Edit or enable/disable this classification">Actions</InfoButton></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {classifications.length > 0 ? (
                classifications.map((cls) => (
                  <tr key={cls._id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{cls.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                          cls.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {cls.isActive ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setEditingClass(cls);
                            setClassFormName(cls.name);
                            setShowClassModal(true);
                          }}
                          className="rounded bg-yellow-50 px-2.5 py-1 text-xs font-bold text-yellow-700 hover:bg-yellow-100 border border-yellow-200"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleToggleClassActive(cls)}
                          className={`rounded px-2.5 py-1 text-xs font-bold text-white border ${
                            cls.isActive
                              ? 'bg-red-500 hover:bg-red-600 border-red-600'
                              : 'bg-green-500 hover:bg-green-600 border-green-600'
                          }`}
                        >
                          {cls.isActive ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="px-6 py-8 text-center text-gray-500">
                    No classifications found. Click &quot;Add Classification&quot; to create one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        /* Reviews list view */
        <div className="overflow-x-auto">
          <table className="w-full min-w-[800px] divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="The customer who wrote this review">Customer</InfoButton></th>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="The internal product ID that this review was written for">Product ID</InfoButton></th>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="The star rating (1–5) given by the customer">Rating</InfoButton></th>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="The written review text left by the customer">Comment</InfoButton></th>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="The review classification or category selected by the customer (e.g. Quality, Price)">Category</InfoButton></th>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="The date and time this review was submitted">Submitted On</InfoButton></th>
                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500"><InfoButton info="Approve or reject/hide this review">Actions</InfoButton></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {paginatedReviews.length > 0 ? (
                paginatedReviews.map((review) => (
                  <tr key={review._id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-semibold text-gray-900">{review.userName || 'Verified Buyer'}</div>
                      <div className="text-xs text-gray-400">ID: {review.userId?.slice(-6)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                      {review.productId}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-0.5 text-yellow-400">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <svg
                            key={i}
                            className={`h-4 w-4 ${i < review.rating ? 'fill-current' : 'text-gray-200'}`}
                            viewBox="0 0 24 24"
                          >
                            <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                          </svg>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 max-w-[250px] truncate" title={review.comment}>
                      {review.comment}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center rounded-full bg-pink-50 px-2.5 py-0.5 text-xs font-semibold text-pink-700">
                        {review.classification}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 font-medium">
                      {formatDateTimeIST(review.createdAt)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold">
                      <div className="flex gap-2">
                        {review.status !== 'approved' && (
                          <button
                            onClick={() => handleApproveReview(review._id)}
                            className="rounded bg-green-50 px-3 py-1 text-xs font-bold text-green-700 hover:bg-green-100 border border-green-200"
                          >
                            Approve
                          </button>
                        )}
                        {review.status !== 'removed' && (
                          <button
                            onClick={() => handleRejectReview(review._id)}
                            className="rounded bg-red-50 px-3 py-1 text-xs font-bold text-red-700 hover:bg-red-100 border border-red-200"
                          >
                            Reject/Hide
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    No reviews in this category.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Premium Pagination Controls */}
          {reviews.length > 0 && (
            <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
              <div className="text-sm text-gray-700">
                Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
                <span className="font-semibold">{endIndex}</span> of{' '}
                <span className="font-semibold">{totalItems}</span> reviews
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
        </div>
      )}

      {/* Classification Create/Edit Modal */}
      {showClassModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          onClick={() => {
            setShowClassModal(false);
            setEditingClass(null);
            setClassFormName('');
          }}
        >
          <div
            className="mx-4 w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-lg font-bold text-gray-900">
              {editingClass ? 'Edit Review Classification' : 'Add Review Classification'}
            </h3>
            <form onSubmit={handleClassSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  value={classFormName}
                  onChange={(e) => setClassFormName(e.target.value)}
                  placeholder="e.g. Quality, Price, Return Experience"
                  required
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-800 focus:border-[#ff3f6c]"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowClassModal(false);
                    setEditingClass(null);
                    setClassFormName('');
                  }}
                  className="rounded bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingClass}
                  className="rounded bg-green-600 px-5 py-2 text-sm font-bold text-white hover:bg-green-700 transition-all disabled:opacity-50"
                >
                  {submittingClass ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
