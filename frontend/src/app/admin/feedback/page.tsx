'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';
import InfoButton from '@/components/InfoButton';

interface Feedback {
  _id: string;
  orderId: string;
  userId: string;
  user?: {
    name: string;
    email: string;
  };
  rating: number;
  comment: string;
  deliveryRating?: number;
  deliveryComment?: string;
  createdAt: string;
}

export default function AdminFeedback() {
  const { user } = useAuth();
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);

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
      fetchFeedbacks();
    }
  }, [user]);

  const fetchFeedbacks = async () => {
    try {
      setLoading(true);
      const response = await api.get('/order-feedback/');
      setFeedbacks(response.data);
      setCurrentPage(1);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch feedback');
    } finally {
      setLoading(false);
    }
  };

  const totalItems = feedbacks.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedFeedbacks = feedbacks.slice(startIndex, endIndex);

  if (user?.role !== 'super_admin') {
    return <div className="p-8">Access Denied</div>;
  }

  const renderStars = (rating: number) => {
    return (
      <div className="flex">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`h-4 w-4 ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
    );
  };

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/50 p-6">
        <div>
          <h2 className="inline-flex items-center gap-3 text-xl font-bold text-gray-800">
            Customer Feedback <RefreshButton onRefresh={fetchFeedbacks} />
          </h2>
          <p className="mt-1 text-sm text-gray-500">View feedback from customers per order</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-500">
          <thead className="border-b bg-gray-50 text-xs uppercase text-gray-700">
            <tr>
              <th className="px-6 py-4 font-semibold"><InfoButton info="The date and time this feedback was submitted">Date</InfoButton></th>
              <th className="px-6 py-4 font-semibold"><InfoButton info="The customer who submitted this feedback">User</InfoButton></th>
              <th className="px-6 py-4 font-semibold"><InfoButton info="Whether this is general feedback or feedback tied to a specific order">Type</InfoButton></th>
              <th className="px-6 py-4 font-semibold"><InfoButton info="The order ID associated with this feedback, if applicable">Order ID</InfoButton></th>
              <th className="px-6 py-4 font-semibold"><InfoButton info="Star rating (1–5) given by the customer for product quality">Product Rating</InfoButton></th>
              <th className="px-6 py-4 font-semibold"><InfoButton info="Written comment from the customer about the product">Product Comment</InfoButton></th>
              <th className="px-6 py-4 font-semibold"><InfoButton info="Star rating (1–5) given by the customer for the delivery experience">Delivery Rating</InfoButton></th>
              <th className="px-6 py-4 font-semibold"><InfoButton info="Written comment from the customer about the delivery experience">Delivery Comment</InfoButton></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                  <div className="flex items-center justify-center gap-2">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
                    Loading feedback...
                  </div>
                </td>
              </tr>
            ) : feedbacks.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  className="m-4 rounded-lg bg-gray-50/50 px-6 py-8 text-center text-gray-500"
                >
                  No feedback received yet
                </td>
              </tr>
            ) : (
              paginatedFeedbacks.map((item) => (
                <tr
                  key={item._id}
                  className="border-b bg-white transition-colors hover:bg-gray-50/50"
                >
                  <td className="whitespace-nowrap px-6 py-4">{formatDateIST(item.createdAt)}</td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">
                      {item.user?.name || 'Unknown User'}
                    </div>
                    <div className="text-xs text-gray-500">{item.user?.email || item.userId}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-semibold ${
                        (item as any).feedbackType === 'general'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-green-100 text-green-700'
                      }`}
                    >
                      {(item as any).feedbackType === 'general' ? 'General' : 'Order'}
                    </span>
                  </td>
                  <td className="max-w-[120px] truncate px-6 py-4 font-mono text-xs">
                    {item.orderId || '-'}
                  </td>
                  <td className="px-6 py-4">{renderStars(item.rating)}</td>
                  <td className="max-w-[200px] px-6 py-4">
                    <p className="line-clamp-2 text-sm text-gray-600" title={item.comment}>
                      {item.comment || '-'}
                    </p>
                  </td>
                  <td className="px-6 py-4">
                    {item.deliveryRating ? renderStars(item.deliveryRating) : '-'}
                  </td>
                  <td className="max-w-[200px] px-6 py-4">
                    <p className="line-clamp-2 text-sm text-gray-600" title={item.deliveryComment}>
                      {item.deliveryComment || '-'}
                    </p>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Premium Pagination Controls */}
      {feedbacks.length > 0 && (
        <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row px-6 pb-6">
          <div className="text-sm text-gray-700">
            Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
            <span className="font-semibold">{endIndex}</span> of{' '}
            <span className="font-semibold">{totalItems}</span> feedbacks
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
  );
}
