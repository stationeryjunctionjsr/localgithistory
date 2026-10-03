'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import Link from 'next/link';
import Header from '@/components/Header';
import { toast } from 'react-toastify';
import OrderTimeline from '@/components/OrderTimeline';

const PAGE_SIZE = 10;

export default function MyOrders() {
  const { user, fetchUser } = useAuth();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSettleCreditModal, setShowSettleCreditModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<any>(null);
  const [settleCreditData, setSettleCreditData] = useState({
    amount: '',
    paymentImage: null as string | null,
  });
  const [upiDetails, setUpiDetails] = useState<any>(null);
  const [settlingCredit, setSettlingCredit] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showItemDetailsModal, setShowItemDetailsModal] = useState(false);
  const [selectedOrderForDetails, setSelectedOrderForDetails] = useState<any>(null);
  const [fetchError, setFetchError] = useState(false);
  const [page, setPage] = useState(1);
  const [totalOrders, setTotalOrders] = useState(0);

  const [classifications, setClassifications] = useState<any[]>([]);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewProduct, setReviewProduct] = useState<{ id: string; name: string } | null>(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewClassification, setReviewClassification] = useState('');
  const [reviewComment, setReviewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  // Returns state
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [eligibleItems, setEligibleItems] = useState<any[]>([]);
  const [returnCharge, setReturnCharge] = useState(0);
  const [selectedReturnItems, setSelectedReturnItems] = useState<Record<string, { quantity: number; reason: string }>>({});
  const [returnPaymentMethod, setReturnPaymentMethod] = useState<'cod' | 'upi'>('cod');
  const [returnUpiScreenshot, setReturnUpiScreenshot] = useState<string | null>(null);
  const [returnNotes, setReturnNotes] = useState('');
  const [submittingReturn, setSubmittingReturn] = useState(false);
  const [loadingEligibility, setLoadingEligibility] = useState(false);
  const [currentReturnOrderId, setCurrentReturnOrderId] = useState('');

  useEffect(() => {
    const fetchClassifications = async () => {
      try {
        const response = await api.get('/reviews/classifications');
        setClassifications(response.data || []);
        if (response.data && response.data.length > 0) {
          setReviewClassification(response.data[0].name);
        }
      } catch (err) {
        console.error('Failed to fetch review classifications', err);
      }
    };
    fetchClassifications();
  }, []);

  const handleOpenReviewModal = (productId: string, productName: string) => {
    setReviewProduct({ id: productId, name: productName });
    setReviewRating(5);
    if (classifications.length > 0) {
      setReviewClassification(classifications[0].name);
    } else {
      setReviewClassification('');
    }
    setReviewComment('');
    setShowReviewModal(true);
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewProduct) return;
    
    if (!reviewComment.trim()) {
      toast.error('Please enter a comment.');
      return;
    }
    if (!reviewClassification) {
      toast.error('Please select a classification.');
      return;
    }

    setSubmittingReview(true);
    try {
      await api.post('/reviews/', {
        productId: reviewProduct.id,
        rating: reviewRating,
        comment: reviewComment.trim(),
        classification: reviewClassification,
      });
      toast.success('Review submitted successfully and is pending admin approval.');
      setShowReviewModal(false);
      setReviewProduct(null);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || 'Failed to submit review');
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleOpenReturnModal = async (orderId: string) => {
    setLoadingEligibility(true);
    setCurrentReturnOrderId(orderId);
    setSelectedReturnItems({});
    setReturnPaymentMethod('cod');
    setReturnUpiScreenshot(null);
    setReturnNotes('');
    
    try {
      const res = await api.get(`/returns/order/${orderId}/eligibility`);
      const data = res.data || {};
      if (data.reason) {
        toast.error(data.reason);
        return;
      }
      setEligibleItems(data.eligibleItems || []);
      setReturnCharge(data.returnDeliveryCharge || 0);
      setShowReturnModal(true);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to check return eligibility');
    } finally {
      setLoadingEligibility(false);
    }
  };

  const handleReturnSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const itemsToSubmit = Object.entries(selectedReturnItems)
      .filter(([_, details]) => details.quantity > 0)
      .map(([productId, details]) => ({
        productId,
        quantity: details.quantity,
        reason: details.reason || 'No reason specified',
      }));

    if (itemsToSubmit.length === 0) {
      toast.error('Please select at least one item and quantity to return.');
      return;
    }

    if (returnPaymentMethod === 'upi' && !returnUpiScreenshot) {
      toast.error('Please upload your UPI payment screenshot.');
      return;
    }

    setSubmittingReturn(true);
    try {
      await api.post('/returns/request', {
        orderId: currentReturnOrderId,
        items: itemsToSubmit,
        paymentMethod: returnPaymentMethod,
        upiPaymentScreenshot: returnUpiScreenshot,
        notes: returnNotes,
      });
      toast.success('Return request submitted successfully.');
      setShowReturnModal(false);
      fetchOrders(page);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || 'Failed to request return');
    } finally {
      setSubmittingReturn(false);
    }
  };

  const handleReturnScreenshotChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setReturnUpiScreenshot(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const totalPages = Math.max(1, Math.ceil(totalOrders / PAGE_SIZE));

  useEffect(() => {
    if (user) {
      fetchOrders(1);
      fetchUPIDetails();
    } else {
      setLoading(false);
    }
    // Reset to page 1 whenever filters change
    setPage(1);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, startDate, endDate]);

  const fetchUPIDetails = async () => {
    try {
      const response = await api.get('/upi/details');
      setUpiDetails(response.data);
    } catch (error) {
      console.error('Failed to fetch UPI details', error);
    }
  };

  const fetchOrders = async (pageNum: number = page) => {
    try {
      setFetchError(false);
      setLoading(true);
      const params: any = { page: pageNum, limit: PAGE_SIZE };
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;

      const response = await api.get('/orders', { params });
      const data = response.data;
      const ordersData: any[] = data.orders || data || [];
      setOrders(ordersData);
      setTotalOrders(data.total ?? ordersData.length);
      setPage(pageNum);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch orders', error);
      setFetchError(true);
      setLoading(false);
    }
  };

  const clearDateFilters = () => {
    setStartDate('');
    setEndDate('');
  };

  const handleViewItemDetails = (order: any) => {
    setSelectedOrderForDetails(order);
    setShowItemDetailsModal(true);
  };

  const handleDownloadInvoice = async (orderId: string) => {
    try {
      const response = await api.get(`/orders/${orderId}/invoice`, {
        responseType: 'blob',
      });

      // Create blob and download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${orderId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Invoice downloaded successfully');
    } catch (error: any) {
      toast.error(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to download invoice'
      );
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  const handleSettleCredit = async (order: any) => {
    setSelectedOrder(order);
    setShowSettleCreditModal(true);
    // Fetch payment details for this order to get remaining amount
    try {
      const response = await api.get(`/payments?orderId=${order._id}`);
      if (response.data && response.data.length > 0) {
        const payment = response.data[0];
        setSettleCreditData({
          amount: payment.amountRemaining?.toString() || order.total?.toString() || '0',
          paymentImage: null,
        });
      } else {
        setSettleCreditData({
          amount: order.total?.toString() || '0',
          paymentImage: null,
        });
      }
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      setSettleCreditData({
        amount: order.total?.toString() || '0',
        paymentImage: null,
      });
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSettleCreditData({
          ...settleCreditData,
          paymentImage: reader.result as string,
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSettleCreditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;

    const settleAmount = parseFloat(settleCreditData.amount);
    if (isNaN(settleAmount) || settleAmount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setSettlingCredit(true);
    try {
      await api.post(`/orders/${selectedOrder._id}/settle-credit`, {
        amount: settleAmount,
        paymentImage: settleCreditData.paymentImage,
        upiPaymentScreenshot: settleCreditData.paymentImage,
      });
      toast.success('Credit settled successfully');
      setShowSettleCreditModal(false);
      setSelectedOrder(null);
      setSettleCreditData({ amount: '', paymentImage: null });
      fetchOrders(page);
      if (fetchUser) fetchUser(); // Refresh user data to update credit
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to settle credit');
    } finally {
      setSettlingCredit(false);
    }
  };

  if (loading) {
    return (
      <>
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="mb-6 flex items-center justify-between">
            <div className="h-8 w-40 animate-pulse rounded bg-gray-200"></div>
            <div className="flex gap-4">
              <div className="h-10 w-48 animate-pulse rounded bg-gray-200"></div>
              <div className="h-10 w-48 animate-pulse rounded bg-gray-200"></div>
            </div>
          </div>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex h-24 animate-pulse items-center justify-between rounded-lg bg-gray-100 p-4 shadow-sm">
                <div className="h-4 w-1/4 rounded bg-gray-200"></div>
                <div className="h-4 w-1/6 rounded bg-gray-200"></div>
                <div className="h-4 w-1/6 rounded bg-gray-200"></div>
                <div className="h-4 w-1/12 rounded bg-gray-200"></div>
                <div className="h-8 w-24 rounded bg-gray-200"></div>
              </div>
            ))}
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="container mx-auto px-4 py-8">
        {fetchError && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            Failed to load orders. Please{' '}
            <button onClick={() => fetchOrders(page)} className="font-semibold underline">
              try again
            </button>
            .
          </div>
        )}
        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <h1 className="text-3xl font-bold">My Orders</h1>
          <div className="flex flex-wrap items-end gap-3 md:gap-4">
            <div className="w-full sm:w-auto">
              <label className="mb-1 block text-sm font-medium md:mb-0 md:mr-2 md:inline">Start Date:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm md:w-auto"
              />
            </div>
            <div className="w-full sm:w-auto">
              <label className="mb-1 block text-sm font-medium md:mb-0 md:mr-2 md:inline">End Date:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm md:w-auto"
              />
            </div>
            {(startDate || endDate) && (
              <button
                onClick={clearDateFilters}
                className="w-full rounded bg-gray-500 px-4 py-2 text-sm text-white hover:bg-gray-600 sm:w-auto"
              >
                Clear
              </button>
            )}
          </div>
        </div>
        {orders.length === 0 ? (
          <div className="rounded-lg bg-white p-6 text-center shadow">
            <p className="mb-4 text-gray-600">No orders found</p>
            <Link
              href="/customer"
              className="inline-block rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
            >
              Continue Shopping
            </Link>
          </div>
        ) : (
          <>
            {/* ── Desktop table (md+) ── */}
            <div className="hidden overflow-hidden rounded-lg bg-white shadow md:block">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Order Number</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Total</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Payment Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Payment Method</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {orders.map((order: any) => (
                    <tr key={order._id}>
                      <td className="whitespace-nowrap px-6 py-4">{order.orderNumber || order._id}</td>
                      <td className="whitespace-nowrap px-6 py-4">{formatDate(order.createdAt)}</td>
                      <td className="whitespace-nowrap px-6 py-4">₹{order.total?.toFixed(2) || '0.00'}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span className={`rounded px-2 py-1 text-sm ${order.status === 'delivered' ? 'bg-green-100 text-green-800' : order.status === 'cancelled' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                          {order.status || 'pending'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span className={`rounded px-2 py-1 text-sm ${order.paymentStatus === 'paid' ? 'bg-green-100 text-green-800' : order.paymentStatus === 'failed' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                          {order.paymentStatus || 'pending'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">{order.paymentMethod?.toUpperCase() || '-'}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="flex gap-2">
                          <button className="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600" onClick={() => handleViewItemDetails(order)}>Item Details</button>
                          {/* Invoice download: retail gets it on delivery (auto-generated); wholesale only after delivery */}
                          {order.invoicePath && (user?.role !== 'wholesaler' || order.status === 'delivered') && (
                            <button className="rounded bg-green-500 px-3 py-1 text-sm text-white hover:bg-green-600" onClick={() => handleDownloadInvoice(order._id)}>Download Invoice</button>
                          )}
                          {user?.role === 'wholesaler' && order.paymentMethod === 'credit' && order.paymentStatus !== 'paid' && (
                            <button className="rounded bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-700" onClick={() => handleSettleCredit(order)}>Settle Credit</button>
                          )}
                          {order.status === 'delivered' && user?.role === 'customer' && (
                            <button className="rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600 disabled:opacity-50" disabled={loadingEligibility && currentReturnOrderId === order._id} onClick={() => handleOpenReturnModal(order._id)}>
                              {loadingEligibility && currentReturnOrderId === order._id ? 'Checking...' : 'Return Items'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* ── Mobile card list (< md) ── */}
            <div className="space-y-3 md:hidden">
              {orders.map((order: any) => (
                <div key={order._id} className="rounded-lg bg-white p-4 shadow">
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <span className="text-sm font-semibold text-gray-900 break-all">
                      #{order.orderNumber || order._id?.slice(-8)}
                    </span>
                    <span className="text-xs text-gray-500 shrink-0">{formatDate(order.createdAt)}</span>
                  </div>
                  <div className="mb-3 flex flex-wrap gap-2">
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${order.status === 'delivered' ? 'bg-green-100 text-green-800' : order.status === 'cancelled' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {order.status || 'pending'}
                    </span>
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${order.paymentStatus === 'paid' ? 'bg-green-100 text-green-800' : order.paymentStatus === 'failed' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {order.paymentStatus || 'pending'}
                    </span>
                    <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
                      {order.paymentMethod?.toUpperCase() || '-'}
                    </span>
                  </div>
                  <div className="mb-3 text-base font-bold text-gray-900">
                    ₹{order.total?.toFixed(2) || '0.00'}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button className="rounded bg-blue-500 px-3 py-1.5 text-sm text-white hover:bg-blue-600" onClick={() => handleViewItemDetails(order)}>Item Details</button>
                    {/* Invoice download: retail gets it on delivery (auto-generated); wholesale only after delivery */}
                    {order.invoicePath && (user?.role !== 'wholesaler' || order.status === 'delivered') && (
                      <button className="rounded bg-green-500 px-3 py-1.5 text-sm text-white hover:bg-green-600" onClick={() => handleDownloadInvoice(order._id)}>Download Invoice</button>
                    )}
                    {user?.role === 'wholesaler' && order.paymentMethod === 'credit' && order.paymentStatus !== 'paid' && (
                      <button className="rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700" onClick={() => handleSettleCredit(order)}>Settle Credit</button>
                    )}
                    {order.status === 'delivered' && user?.role === 'customer' && (
                      <button className="rounded bg-red-500 px-3 py-1.5 text-sm text-white hover:bg-red-650 disabled:opacity-50" disabled={loadingEligibility && currentReturnOrderId === order._id} onClick={() => handleOpenReturnModal(order._id)}>
                        {loadingEligibility && currentReturnOrderId === order._id ? 'Checking...' : 'Return Items'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-8 flex flex-col items-center gap-4">
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                onClick={() => fetchOrders(page - 1)}
                disabled={page <= 1 || loading}
                className="rounded border border-gray-300 px-3 py-1 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-40 hover:bg-gray-50"
              >
                Previous
              </button>
              
              <div className="flex flex-wrap items-center justify-center gap-1.5">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                  <button
                    key={p}
                    onClick={() => fetchOrders(p)}
                    disabled={loading}
                    className={`min-w-[32px] rounded border px-3 py-1 text-sm font-medium transition-colors ${
                      p === page
                        ? 'border-blue-600 bg-blue-600 text-white'
                        : 'border-gray-300 hover:bg-gray-50'
                    } disabled:cursor-not-allowed`}
                  >
                    {p}
                  </button>
                ))}
              </div>

              <button
                onClick={() => fetchOrders(page + 1)}
                disabled={page >= totalPages || loading}
                className="rounded border border-gray-300 px-3 py-1 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-40 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
            <span className="text-sm text-gray-500">
              {totalOrders} order{totalOrders !== 1 ? 's' : ''} total
            </span>
          </div>
        )}

        {/* Item Details Modal */}
        {showItemDetailsModal && selectedOrderForDetails && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
            onClick={() => {
              setShowItemDetailsModal(false);
              setSelectedOrderForDetails(null);
            }}
          >
            <div
              className="mx-4 max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-2xl font-bold">Order Details</h3>
              <p className="mb-2">
                <strong>Order Number:</strong> {selectedOrderForDetails.orderNumber}
              </p>
              <p className="mb-4">
                <strong>Order Date:</strong> {formatDate(selectedOrderForDetails.createdAt)}
              </p>

              {/* ── Order Status Timeline ── */}
              <div className="mb-6 rounded-2xl border border-gray-100 bg-gray-50 px-5 py-5">
                <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-gray-500">
                  Order Progress
                </h4>
                <OrderTimeline
                  orderId={selectedOrderForDetails._id || selectedOrderForDetails.id}
                  currentStatus={selectedOrderForDetails.status || 'pending'}
                />
              </div>

              {/* Delivery slot info */}
              {selectedOrderForDetails.deliverySlot?.slotId && (
                <div
                  className={`mb-4 rounded-lg border p-3 ${
                    selectedOrderForDetails.deliverySlot?.isUrgent
                      ? 'border-amber-200 bg-amber-50'
                      : 'border-blue-200 bg-blue-50'
                  }`}
                >
                  <p className="font-semibold">
                    {selectedOrderForDetails.deliverySlot?.isUrgent ? '⚡ Urgent Delivery Slot' : '🕐 Scheduled Delivery Slot'}
                  </p>
                  <p className="mt-1 text-sm text-gray-700">
                    <strong>Date:</strong> {selectedOrderForDetails.deliverySlot?.date}
                  </p>
                  <p className="text-sm text-gray-700">
                    <strong>Time:</strong>{' '}
                    {selectedOrderForDetails.deliverySlot?.startTime} – {selectedOrderForDetails.deliverySlot?.endTime}
                  </p>
                </div>
              )}

              <h4 className="mb-3 mt-6 text-xl font-semibold">Items</h4>

              <div className="overflow-x-auto">
                <table className="mb-6 w-full min-w-[500px]">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-2 text-left">Product</th>
                      <th className="px-4 py-2 text-left">Quantity</th>
                      <th className="px-4 py-2 text-left">Price</th>
                      <th className="px-4 py-2 text-left">Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedOrderForDetails.items?.map((item: any, index: number) => (
                      <tr key={index} className="border-b">
                        <td className="px-4 py-2">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <span>{item.product?.name || 'Product'}</span>
                            {selectedOrderForDetails.status === 'delivered' && (
                              <button
                                onClick={() => handleOpenReviewModal(item.product?._id || item.product, item.product?.name || 'Product')}
                                className="inline-flex self-start items-center rounded bg-[#ff3f6c] px-3 py-1 text-xs font-bold text-white hover:bg-[#e0355f] transition-all"
                              >
                                Review Product
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-2">{item.quantity}</td>
                        <td className="px-4 py-2">₹{item.price?.toFixed(2) || '0.00'}</td>
                        <td className="px-4 py-2">₹{item.subtotal?.toFixed(2) || '0.00'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="border-t-2 border-gray-300 pt-4">
                <div className="mb-2 flex justify-between">
                  <strong>Subtotal:</strong>
                  <span>₹{selectedOrderForDetails.subtotal?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="mb-2 flex justify-between">
                  <strong>Tax:</strong>
                  <span>₹{selectedOrderForDetails.tax?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="mb-2 flex justify-between">
                  <strong>Delivery Charge:</strong>
                  <span>₹{selectedOrderForDetails.shipping?.toFixed(2) || '0.00'}</span>
                </div>
                {selectedOrderForDetails.deliveryGst > 0 && (
                  <div className="mb-2 flex justify-between">
                    <strong>Delivery GST:</strong>
                    <span>₹{selectedOrderForDetails.deliveryGst?.toFixed(2) || '0.00'}</span>
                  </div>
                )}
                {selectedOrderForDetails.discount > 0 && (
                  <div className="mb-2 flex justify-between">
                    <strong>Discount:</strong>
                    <span>-₹{selectedOrderForDetails.discount?.toFixed(2) || '0.00'}</span>
                  </div>
                )}
                <div className="mt-4 flex justify-between border-t-2 border-gray-800 pt-4 text-lg font-bold">
                  <strong>Total:</strong>
                  <span>₹{selectedOrderForDetails.total?.toFixed(2) || '0.00'}</span>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  className="rounded bg-gray-600 px-6 py-2 text-white hover:bg-gray-700"
                  onClick={() => {
                    setShowItemDetailsModal(false);
                    setSelectedOrderForDetails(null);
                  }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Settle Credit Modal */}
        {showSettleCreditModal && selectedOrder && upiDetails && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
            onClick={() => {
              setShowSettleCreditModal(false);
              setSelectedOrder(null);
              setSettleCreditData({ amount: '', paymentImage: null });
            }}
          >
            <div
              className="mx-4 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-xl font-bold">Settle Credit</h3>
              <p className="mb-2">
                <strong>Order ID:</strong> {selectedOrder.orderNumber || selectedOrder._id}
              </p>
              <p className="mb-4">
                <strong>Total Amount:</strong> ₹{selectedOrder.total?.toFixed(2) || '0.00'}
              </p>

              <div className="mb-6 rounded-lg bg-gray-50 p-4 text-center">
                <p className="mb-4">Scan the QR code or use the UPI ID to make payment</p>
                {upiDetails.qrCodeUrl && (
                  <img
                    src={upiDetails.qrCodeUrl}
                    alt="UPI QR Code"
                    className="mx-auto mb-4 max-h-[250px] max-w-[250px] rounded-lg border border-gray-300"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                )}
                <div className="mb-4">
                  <strong>UPI ID:</strong> {upiDetails.upiId}
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(upiDetails.upiId);
                      toast.success('UPI ID copied to clipboard');
                    }}
                    className="ml-2 rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                  >
                    Copy
                  </button>
                </div>
              </div>

              <form onSubmit={handleSettleCreditSubmit}>
                <div className="mb-4">
                  <label className="mb-1 block">Amount to Pay (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={settleCreditData.amount}
                    onChange={(e) =>
                      setSettleCreditData({ ...settleCreditData, amount: e.target.value })
                    }
                    required
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  />
                </div>
                <div className="mb-4">
                  <label className="mb-1 block">Upload Payment Screenshot *</label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    required
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  />
                  {settleCreditData.paymentImage && (
                    <div className="mt-2">
                      <img
                        src={settleCreditData.paymentImage}
                        alt="Payment Screenshot"
                        className="max-h-[200px] max-w-[200px] rounded border border-gray-300"
                      />
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap justify-end gap-3 md:gap-4">
                  <button
                    type="button"
                    className="flex-1 rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700 sm:flex-none"
                    onClick={() => {
                      setShowSettleCreditModal(false);
                      setSelectedOrder(null);
                      setSettleCreditData({ amount: '', paymentImage: null });
                    }}
                    disabled={settlingCredit}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400 sm:flex-none"
                    disabled={
                      settlingCredit || !settleCreditData.amount || !settleCreditData.paymentImage
                    }
                  >
                    {settlingCredit ? 'Processing...' : 'Settle Credit'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Product Review Modal */}
        {showReviewModal && reviewProduct && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
            onClick={() => {
              setShowReviewModal(false);
              setReviewProduct(null);
            }}
          >
            <div
              className="mx-4 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-xl font-bold">Review Product</h3>
              <p className="mb-4 text-sm text-gray-600">
                You are reviewing: <strong>{reviewProduct.name}</strong>
              </p>

              <form onSubmit={handleReviewSubmit} className="space-y-4">
                {/* Star Rating */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
                  <div className="flex items-center gap-1.5">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setReviewRating(star)}
                        className="text-2xl outline-none focus:outline-none transition-transform active:scale-95"
                      >
                        <svg
                          className={`h-8 w-8 ${star <= reviewRating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                          viewBox="0 0 24 24"
                        >
                          <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                        </svg>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Classification Select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Review Category / Classification</label>
                  <select
                    value={reviewClassification}
                    onChange={(e) => setReviewClassification(e.target.value)}
                    required
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-800 bg-white"
                  >
                    {classifications.map((c) => (
                      <option key={c._id} value={c.name}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Comment Textarea */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Your Review</label>
                  <textarea
                    rows={4}
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    required
                    placeholder="Describe your experience with this product..."
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-800 outline-none focus:border-[#ff3f6c]"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowReviewModal(false);
                      setReviewProduct(null);
                    }}
                    className="rounded bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingReview}
                    className="rounded bg-[#ff3f6c] px-5 py-2 text-sm font-bold text-white hover:bg-[#e0355f] transition-all disabled:opacity-50"
                  >
                    {submittingReview ? 'Submitting...' : 'Submit Review'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Return Items Modal */}
        {showReturnModal && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 overflow-y-auto"
            onClick={() => setShowReturnModal(false)}
          >
            <div
              className="mx-4 my-8 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-4 pb-2 border-b">
                <h3 className="text-xl font-bold text-gray-900">Return Request</h3>
                <button
                  onClick={() => setShowReturnModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <form onSubmit={handleReturnSubmit} className="space-y-6">
                <div>
                  <h4 className="font-semibold text-sm text-gray-700 mb-2">Select Items to Return:</h4>
                  <div className="space-y-4 max-h-[40vh] overflow-y-auto border p-3 rounded-lg divide-y divide-gray-100">
                    {eligibleItems.map((item) => {
                      const selection = selectedReturnItems[item.productId] || { quantity: 0, reason: '' };
                      return (
                        <div key={item.productId} className="py-3 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-gray-900">{item.name}</p>
                            <p className="text-xs text-gray-500">Price: ₹{item.price} | Max returnable: {item.maxQuantity}</p>
                          </div>
                          
                          <div className="flex items-center gap-3">
                            <div className="flex items-center border rounded">
                              <button
                                type="button"
                                className="px-2 py-1 text-gray-600 hover:bg-gray-100"
                                onClick={() => {
                                  setSelectedReturnItems({
                                    ...selectedReturnItems,
                                    [item.productId]: {
                                      ...selection,
                                      quantity: Math.max(0, selection.quantity - 1),
                                    },
                                  });
                                }}
                              >
                                -
                              </button>
                              <span className="px-3 text-sm font-medium">{selection.quantity}</span>
                              <button
                                type="button"
                                className="px-2 py-1 text-gray-600 hover:bg-gray-100"
                                onClick={() => {
                                  setSelectedReturnItems({
                                    ...selectedReturnItems,
                                    [item.productId]: {
                                      ...selection,
                                      quantity: Math.min(item.maxQuantity, selection.quantity + 1),
                                    },
                                  });
                                }}
                              >
                                +
                              </button>
                            </div>

                            {selection.quantity > 0 && (
                              <input
                                type="text"
                                placeholder="Reason"
                                value={selection.reason}
                                onChange={(e) => {
                                  setSelectedReturnItems({
                                    ...selectedReturnItems,
                                    [item.productId]: {
                                      ...selection,
                                      reason: e.target.value,
                                    },
                                  });
                                }}
                                required
                                className="border rounded px-2 py-1 text-xs w-32 outline-none focus:border-red-500"
                              />
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="bg-red-50 p-4 rounded-lg flex justify-between items-center">
                  <div>
                    <p className="text-xs text-red-700 font-semibold uppercase tracking-wider">Return Pickup Fee</p>
                    <p className="text-sm text-red-600">A pickup fee will apply to this return request.</p>
                  </div>
                  <span className="text-lg font-bold text-red-700">₹{returnCharge}</span>
                </div>

                {/* Return pickup fee payment method */}
                {returnCharge > 0 && (
                  <div className="space-y-3">
                    <label className="block text-sm font-semibold text-gray-700">Pay Return Pickup Fee Via:</label>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="returnPaymentMethod"
                          value="cod"
                          checked={returnPaymentMethod === 'cod'}
                          onChange={() => setReturnPaymentMethod('cod')}
                        />
                        <span className="text-sm text-gray-700">Pay on Pickup (COD)</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="returnPaymentMethod"
                          value="upi"
                          checked={returnPaymentMethod === 'upi'}
                          onChange={() => setReturnPaymentMethod('upi')}
                        />
                        <span className="text-sm text-gray-700">Pay via UPI Now</span>
                      </label>
                    </div>

                    {returnPaymentMethod === 'upi' && upiDetails && (
                      <div className="mt-3 p-4 bg-gray-50 border rounded-lg space-y-4">
                        <p className="text-xs text-gray-600 font-medium text-center">Scan the QR code or pay to the UPI ID, then upload the screenshot.</p>
                        {upiDetails.qrCodeUrl && (
                          <img
                            src={upiDetails.qrCodeUrl}
                            alt="UPI QR Code"
                            className="mx-auto max-h-[180px] rounded-lg border bg-white"
                          />
                        )}
                        <div className="text-center text-sm">
                          <strong>UPI ID:</strong> {upiDetails.upiId}
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-gray-600 mb-1">Upload Payment Screenshot *</label>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handleReturnScreenshotChange}
                            required
                            className="w-full text-xs"
                          />
                          {returnUpiScreenshot && (
                            <img
                              src={returnUpiScreenshot}
                              alt="Screenshot preview"
                              className="mt-2 max-h-[100px] rounded border"
                            />
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Return notes */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Additional Notes (Optional)</label>
                  <textarea
                    rows={2}
                    value={returnNotes}
                    onChange={(e) => setReturnNotes(e.target.value)}
                    placeholder="Provide any additional details or pickup instructions..."
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-800"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowReturnModal(false)}
                    className="rounded bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingReturn}
                    className="rounded bg-red-650 px-5 py-2 text-sm font-bold text-white hover:bg-red-700 transition-all disabled:opacity-50"
                  >
                    {submittingReturn ? 'Submitting...' : 'Submit Request'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
