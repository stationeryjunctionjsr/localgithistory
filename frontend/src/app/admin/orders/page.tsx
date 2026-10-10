'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import Modal from '@/components/Modal';
import { formatDateIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';

interface Order {
  _id: string;
  orderNumber: string;
  user?: {
    _id: string;
    name: string;
    email: string;
    role?: string;
  };
  orderType?: string;
  total: number;
  paymentMethod?: string;
  status: string;
  paymentStatus?: string;
  createdAt: string;
  declineReason?: string;
  shipping?: number;
  subtotal?: number;
  tax?: number;
  deliveryGst?: number;
  discount?: number;
  invoicePath?: string;
  paymentEntries?: any[];
  turnaroundHours?: number;
  isUrgentDelivery?: boolean;
  deliverySlot?: {
    slotId?: string;
    date?: string;
    startTime?: string;
    endTime?: string;
    isUrgent?: boolean;
  } | null;
  shippingAddress?: {
    street?: string;
    city?: string;
    state?: string;
    district?: string;
    zipCode?: string;
    country?: string;
    addressLine2?: string;
    landmark?: string;
    name?: string;
  };
  valet?: {
    _id: string;
    userId?: number;
    userIdFormatted?: string;
    name: string;
    email: string;
  };
}

interface Valet {
  _id: string;
  name: string;
  email: string;
}

const ActionIconButton = ({
  onClick,
  icon,
  tooltip,
  variant,
}: {
  onClick: () => void;
  icon: React.ReactNode;
  tooltip: string;
  variant: string;
}) => (
  <div className="relative group flex items-center justify-center">
    <button
      onClick={onClick}
      className={`rounded-lg p-2 text-white shadow-sm transition-all hover:scale-105 duration-150 ${variant}`}
    >
      {icon}
    </button>
    <div className="absolute bottom-full left-1/2 z-30 mb-2 -translate-x-1/2 scale-75 opacity-0 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-bottom pointer-events-none whitespace-nowrap rounded bg-gray-950 px-2.5 py-1 text-[11px] font-medium text-white shadow-lg">
      {tooltip}
      <div className="absolute top-full left-1/2 -mt-1 -translate-x-1/2 border-4 border-transparent border-t-gray-950" />
    </div>
  </div>
);

export default function OrderManagement() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [orderTypeFilter, setOrderTypeFilter] = useState('all');
  const [orderCategoryTab, setOrderCategoryTab] = useState('all');
  const [dateFilter, setDateFilter] = useState('all'); // 'all', 'day', 'week', 'month', 'year', 'custom'
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [valets, setValets] = useState<Valet[]>([]);
  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });

  // Modal states
  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [showDispatchModal, setShowDispatchModal] = useState(false);
  const [showProductsModal, setShowProductsModal] = useState(false);
  const [showDeliveryChargeModal, setShowDeliveryChargeModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [declineReason, setDeclineReason] = useState('');
  const [selectedValetId, setSelectedValetId] = useState('');
  const [courierPartner, setCourierPartner] = useState('');
  const [courierAwb, setCourierAwb] = useState('');
  const [courierTrackingId, setCourierTrackingId] = useState('');
  const [courierEta, setCourierEta] = useState('');
  const [newDeliveryCharge, setNewDeliveryCharge] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Payment history modal state
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentDetails, setPaymentDetails] = useState<any[]>([]);
  const [paymentLoading, setPaymentLoading] = useState(false);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchOrders();
      fetchValets();
      fetchPageInfo();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, dateFilter, customStartDate, customEndDate]);

  const getDateRange = () => {
    const now = new Date();
    let startDate: Date,
      endDate: Date = new Date(now);

    switch (dateFilter) {
      case 'day':
        startDate = new Date(now);
        startDate.setHours(0, 0, 0, 0);
        break;
      case 'week':
        startDate = new Date(now);
        startDate.setDate(now.getDate() - 7);
        startDate.setHours(0, 0, 0, 0);
        break;
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'year':
        startDate = new Date(now.getFullYear(), 0, 1);
        break;
      case 'custom':
        if (customStartDate && customEndDate) {
          startDate = new Date(customStartDate);
          endDate = new Date(customEndDate);
          endDate.setHours(23, 59, 59, 999);
        } else {
          return null;
        }
        break;
      default:
        return null;
    }

    return {
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
    };
  };

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/order-management');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const dateRange = getDateRange();
      const params: any = {};
      if (dateRange) {
        params.startDate = dateRange.startDate;
        params.endDate = dateRange.endDate;
      }
      const response = await api.get('/orders', { params });
      setOrders(response.data || []);
      setLoading(false);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch orders');
      setLoading(false);
    }
  };

  const fetchValets = async () => {
    try {
      const response = await api.get('/users?role=valet');
      setValets(response.data || []);
    } catch (error) {
      console.error('Failed to fetch valets', error);
    }
  };

  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      const matchesSearch =
        order.orderNumber?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.user?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.user?.email?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
      const matchesOrderType = orderTypeFilter === 'all' || order.orderType === orderTypeFilter;

      let matchesCategory = true;
      if (orderCategoryTab === 'regular') {
        matchesCategory = !order.isUrgentDelivery && !order.deliverySlot;
      } else if (orderCategoryTab === 'urgent_slot') {
        matchesCategory = !!order.isUrgentDelivery || !!order.deliverySlot;
      } else if (orderCategoryTab === 'hyperlocal') {
        matchesCategory = (order as any).fulfillment_type !== 'courier';
      } else if (orderCategoryTab === 'courier') {
        matchesCategory = (order as any).fulfillment_type === 'courier';
      }

      return matchesSearch && matchesStatus && matchesOrderType && matchesCategory;
    });
  }, [orders, searchTerm, statusFilter, orderTypeFilter, orderCategoryTab]);

  const totalItems = filteredOrders.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);

  const paginatedOrders = useMemo(() => {
    return filteredOrders.slice(startIndex, endIndex);
  }, [filteredOrders, startIndex, endIndex]);

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

  const handleAccept = async (orderId: string) => {
    try {
      await api.put(`/orders/${orderId}/accept`);
      toast.success('Order accepted successfully');
      fetchOrders();
    } catch (error: any) {
      toast.error(
        error.response?.data?.message || error.response?.data?.detail || 'Failed to accept order'
      );
    }
  };

  const handleDecline = async () => {
    if (!declineReason.trim()) {
      toast.error('Please provide a reason for declining');
      return;
    }
    try {
      await api.put(`/orders/${selectedOrder?._id}/decline`, { reason: declineReason });
      toast.success('Order declined successfully');
      setShowDeclineModal(false);
      setSelectedOrder(null);
      setDeclineReason('');
      fetchOrders();
    } catch (error: any) {
      toast.error(
        error.response?.data?.message || error.response?.data?.detail || 'Failed to decline order'
      );
    }
  };

  const handleGenerateInvoice = async (orderId: string) => {
    try {
      await api.post(`/orders/${orderId}/generate-invoice`);
      toast.success('Invoice generated successfully');
      fetchOrders(); // Refresh orders to show invoice link
    } catch (error: any) {
      toast.error(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to generate invoice'
      );
    }
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

  const openPaymentModal = async (order: Order) => {
    try {
      setPaymentLoading(true);
      setSelectedOrder(order);
      setShowPaymentModal(true);
      const response = await api.get(`/payments?orderId=${order._id}`);
      setPaymentDetails(response.data || []);
      setPaymentLoading(false);
    } catch (error) {
      console.error('Failed to fetch payment history:', error);
      toast.error('Failed to fetch payment history');
      setPaymentLoading(false);
    }
  };

  const handleVerifyPayment = async (paymentId: string, entryId: number, verified: boolean) => {
    try {
      await api.put(`/payments/${paymentId}/verify-entry/${entryId}`, { verified });
      toast.success(`Payment entry ${verified ? 'verified' : 'unverified'} successfully`);

      // Refresh payment modal details
      if (selectedOrder) {
        const response = await api.get(`/payments?orderId=${selectedOrder._id}`);
        setPaymentDetails(response.data || []);

        // Also refresh the main orders list to update the "Accept" button state
        fetchOrders();
      }
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to verify payment entry');
    }
  };

  const handleDispatch = async () => {
    const isCourier = (selectedOrder as any)?.fulfillment_type === 'courier';
    if (isCourier) {
      if (!courierPartner) {
        toast.error('Please select a courier partner');
        return;
      }
      if (!courierAwb) {
        toast.error('Please enter the AWB / waybill number');
        return;
      }
      try {
        await api.put(`/orders/${selectedOrder?._id}/dispatch-courier`, {
          courier_partner: courierPartner,
          awb_code: courierAwb,
          tracking_id: courierTrackingId || courierAwb,
          estimated_delivery_date: courierEta || undefined,
        });
        toast.success('Order dispatched via courier successfully');
        setShowDispatchModal(false);
        setSelectedOrder(null);
        setCourierPartner('');
        setCourierAwb('');
        setCourierTrackingId('');
        setCourierEta('');
        fetchOrders();
      } catch (error: any) {
        toast.error(
          error.response?.data?.message || error.response?.data?.detail || 'Failed to dispatch courier order'
        );
      }
    } else {
      if (!selectedValetId) {
        toast.error('Please select a delivery valet');
        return;
      }
      try {
        await api.put(`/orders/${selectedOrder?._id}/dispatch`, { valetId: selectedValetId });
        toast.success('Order dispatched successfully');
        setShowDispatchModal(false);
        setSelectedOrder(null);
        setSelectedValetId('');
        fetchOrders();
      } catch (error: any) {
        toast.error(
          error.response?.data?.message || error.response?.data?.detail || 'Failed to dispatch order'
        );
      }
    }
  };

  const openDeclineModal = (order: Order) => {
    if (order.paymentMethod === 'upi') {
      toast.error('UPI orders cannot be declined');
      return;
    }
    if (order.paymentMethod !== 'cod' && order.paymentMethod !== 'credit') {
      toast.error('Only COD and Credit orders can be declined');
      return;
    }
    setSelectedOrder(order);
    setShowDeclineModal(true);
  };

  const openDispatchModal = (order: Order) => {
    setSelectedOrder(order);
    // Reset courier fields
    setCourierPartner('');
    setCourierAwb('');
    setCourierTrackingId('');
    setCourierEta('');
    setSelectedValetId('');
    setShowDispatchModal(true);
  };

  const handleUpdateDeliveryCharge = async () => {
    if (!newDeliveryCharge || parseFloat(newDeliveryCharge) < 0) {
      toast.error('Please enter a valid delivery charge');
      return;
    }

    try {
      const response = await api.put(`/orders/${selectedOrder?._id}/delivery-charge`, {
        newDeliveryCharge: parseFloat(newDeliveryCharge),
      });
      toast.success(response.data.message || 'Delivery charge updated successfully');
      setShowDeliveryChargeModal(false);
      setNewDeliveryCharge('');
      setSelectedOrder(null);
      fetchOrders();
    } catch (error: any) {
      toast.error(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to update delivery charge'
      );
    }
  };

  const openDeliveryChargeModal = (order: Order) => {
    // Only allow for wholesaler orders
    const userRole = (order.user as any)?.role;
    if (!userRole || userRole !== 'wholesaler') {
      toast.error('Can only update delivery charge for business/retail customer orders');
      return;
    }
    // Only allow before dispatch
    if (!['pending', 'confirmed', 'processing'].includes(order.status)) {
      toast.error('Can only update delivery charge before order is dispatched');
      return;
    }
    setSelectedOrder(order);
    setNewDeliveryCharge(((order as any).shipping || 0).toString());
    setShowDeliveryChargeModal(true);
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'shipped':
        return 'bg-blue-100 text-blue-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'declined':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPaymentStatusBadgeClass = (paymentStatus?: string) => {
    switch (paymentStatus) {
      case 'paid':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPaymentMethodDisplay = (method?: string) => {
    const methodMap: Record<string, string> = {
      cod: 'COD',
      upi: 'UPI',
      credit: 'Credit',
    };
    return methodMap[method || ''] || method?.toUpperCase() || 'N/A';
  };

  const canAccept = (order: Order) => {
    if (order.paymentMethod === 'upi') {
      const entries = (order as any).paymentEntries || [];
      const anyVerified = entries.some((e: any) => e.verified);
      return order.status === 'pending' && anyVerified;
    }
    return order.status === 'pending';
  };

  const canDecline = (order: Order) => {
    return (
      order.status === 'pending' &&
      order.paymentMethod !== 'upi' &&
      (order.paymentMethod === 'cod' || order.paymentMethod === 'credit')
    );
  };

  const canDispatch = (order: Order) => {
    return order.status === 'processing';
  };

  const isActionDisabled = (order: Order) => {
    return (
      order.status === 'cancelled' ||
      order.status === 'declined' ||
      order.status === 'shipped' ||
      order.status === 'delivered'
    );
  };

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading) return <div>Loading...</div>;

  return (
    <>
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow-md h-full flex flex-col min-h-0">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
              <InfoButton
                info={
                  user?.role === 'super_admin' && pageInfo.page?.description
                    ? pageInfo.page.description
                    : undefined
                }
              >
                Order Management
              </InfoButton>
              <RefreshButton onRefresh={fetchOrders} />
            </h1>
          </div>

          {/* Tabs */}
          <div className="mb-6 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {['all', 'regular', 'urgent_slot', 'hyperlocal', 'courier'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => {
                    setOrderCategoryTab(tab);
                    setCurrentPage(1);
                  }}
                  className={`
                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200
                    ${orderCategoryTab === tab
                      ? 'border-primary-green text-primary-green'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                  `}
                >
                  {tab === 'all' ? 'All'
                    : tab === 'regular' ? 'Regular'
                    : tab === 'urgent_slot' ? 'Urgent/Slot'
                    : tab === 'hyperlocal' ? '🟢 Hyperlocal'
                    : '📦 Courier (3PL)'}
                </button>
              ))}
            </nav>
          </div>

          {/* Search and Filters */}
          <div className="mb-6 flex flex-wrap gap-4">
            <div className="min-w-[300px] flex-1">
              <input
                type="text"
                placeholder="Search by order number, customer name, or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2"
              />
            </div>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-4 py-2"
            >
              <option value="all">All Time</option>
              <option value="day">Today</option>
              <option value="week">Last 7 Days</option>
              <option value="month">This Month</option>
              <option value="year">This Year</option>
              <option value="custom">Custom Range</option>
            </select>
            {dateFilter === 'custom' && (
              <>
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  className="rounded-lg border border-gray-300 px-4 py-2"
                  placeholder="Start Date"
                />
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  className="rounded-lg border border-gray-300 px-4 py-2"
                  placeholder="End Date"
                />
              </>
            )}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-4 py-2"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="shipped">Shipped</option>
              <option value="delivered">Delivered</option>
              <option value="declined">Declined</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <select
              value={orderTypeFilter}
              onChange={(e) => setOrderTypeFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-4 py-2"
            >
              <option value="all">All Types</option>
              <option value="b2c">B2C</option>
              <option value="b2b">B2B</option>
            </select>
          </div>

          {/* Orders Table */}
          <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
            <table className="w-full border-collapse">
              <thead className="sticky top-0 z-10 bg-gray-100 shadow-sm">
                <tr className="bg-gray-100">
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.orderNumber
                          ? pageInfo.columns.orderNumber
                          : undefined
                      }
                    >
                      Order Number
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.customerId
                          ? pageInfo.columns.customerId
                          : undefined
                      }
                    >
                      Customer ID
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.customer
                          ? pageInfo.columns.customer
                          : undefined
                      }
                    >
                      Customer
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.deliveryAddress
                          ? pageInfo.columns.deliveryAddress
                          : undefined
                      }
                    >
                      Delivery Address
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.orderType
                          ? pageInfo.columns.orderType
                          : undefined
                      }
                    >
                      Type
                    </InfoButton>
                  </th>
                  {user?.role === 'super_admin' && (
                    <th className="border p-3 text-left">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.turnaround
                            ? pageInfo.columns.turnaround
                            : undefined
                        }
                      >
                        Turnaround (hrs)
                      </InfoButton>
                    </th>
                  )}
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.total
                          ? pageInfo.columns.total
                          : undefined
                      }
                    >
                      Total
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.paymentMethod
                          ? pageInfo.columns.paymentMethod
                          : undefined
                      }
                    >
                      Payment Method
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">
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
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.paymentStatus
                          ? pageInfo.columns.paymentStatus
                          : undefined
                      }
                    >
                      Payment Status
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.date
                          ? pageInfo.columns.date
                          : undefined
                      }
                    >
                      Date
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">Type</th>
                  <th className="border p-3 text-left">Delivery</th>
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin'
                          ? 'The valet assigned to deliver this order'
                          : undefined
                      }
                    >
                      Fulfilled by
                    </InfoButton>
                  </th>
                  <th className="border p-3 text-left">
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
                  <th className="border p-3 text-left">
                    <InfoButton
                      info={
                        user?.role === 'super_admin'
                          ? 'Accept, decline, or dispatch the order'
                          : undefined
                      }
                    >
                      Order Action
                    </InfoButton>
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedOrders.length > 0 ? (
                  paginatedOrders.map((order) => (
                    <tr key={order._id} className="hover:bg-gray-50">
                      <td className="border p-3">{order.orderNumber}</td>
                      <td className="border p-3">
                        {(order.user as any)?.userIdFormatted ||
                          (order.user as any)?.userId ||
                          order.user?._id ||
                          'N/A'}
                      </td>
                      <td className="border p-3">
                        {order.user?.name || order.user?.email || 'N/A'}
                      </td>
                      <td className="border p-3">
                        {order.shippingAddress ? (
                          <div className="text-sm leading-relaxed">
                            {order.shippingAddress.name && (
                              <div className="font-semibold">{order.shippingAddress.name}</div>
                            )}
                            {order.shippingAddress.street && (
                              <div>{order.shippingAddress.street}</div>
                            )}
                            {order.shippingAddress.addressLine2 && (
                              <div>{order.shippingAddress.addressLine2}</div>
                            )}
                            {order.shippingAddress.landmark && (
                              <div>Landmark: {order.shippingAddress.landmark}</div>
                            )}
                            {order.shippingAddress.city && order.shippingAddress.state && (
                              <div>
                                {order.shippingAddress.city}, {order.shippingAddress.state}
                              </div>
                            )}
                            {order.shippingAddress.zipCode && (
                              <div>PIN: {order.shippingAddress.zipCode}</div>
                            )}
                            {order.shippingAddress.country && (
                              <div>{order.shippingAddress.country}</div>
                            )}
                            {!order.shippingAddress.street && !order.shippingAddress.city && (
                              <div className="text-gray-400">N/A</div>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="border p-3">
                        <span className="rounded bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-800">
                          {order.orderType?.toUpperCase() || 'N/A'}
                        </span>
                      </td>
                      {user?.role === 'super_admin' && (
                        <td className="border p-3">
                          {order.turnaroundHours != null ? Math.round(order.turnaroundHours) : '-'}
                        </td>
                      )}
                      <td className="border p-3">₹{order.total?.toFixed(2) || '0.00'}</td>
                      <td className="border p-3">{getPaymentMethodDisplay(order.paymentMethod)}</td>
                      <td className="border p-3">
                        <span
                          className={`rounded px-2 py-1 text-xs font-semibold ${getStatusBadgeClass(order.status)}`}
                        >
                          {order.status}
                        </span>
                      </td>
                      <td className="border p-3">
                        <span
                          className={`rounded px-2 py-1 text-xs font-semibold ${getPaymentStatusBadgeClass(order.paymentStatus)}`}
                        >
                          {order.paymentStatus || 'N/A'}
                        </span>
                      </td>
                      <td className="border p-3">
                        {order.createdAt ? formatDateIST(order.createdAt) : '-'}
                      </td>
                      <td className="border p-3">
                        {(order as any).fulfillment_type === 'courier' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700">
                            📦 Courier (3PL)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                            🟢 Hyperlocal
                          </span>
                        )}
                      </td>
                      <td className="border p-3">
                        {order.deliverySlot?.isUrgent || order.isUrgentDelivery ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                            ⚡ Urgent
                            {order.deliverySlot?.startTime && (
                              <span className="font-normal">
                                {' '}{order.deliverySlot.startTime}–{order.deliverySlot.endTime}
                              </span>
                            )}
                          </span>
                        ) : order.deliverySlot?.slotId ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-800">
                            🕐 Slot
                            {order.deliverySlot?.startTime && (
                              <span className="font-normal">
                                {' '}{order.deliverySlot.startTime}–{order.deliverySlot.endTime}
                              </span>
                            )}
                          </span>
                        ) : (
                          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">Standard</span>
                        )}
                      </td>

                      <td className="border p-3">
                        {order.valet ? (
                          <div className="text-sm">
                            <div className="font-bold">{order.valet.name}</div>
                            <div className="text-xs text-gray-500">
                              {order.valet.userIdFormatted || order.valet.userId || 'N/A'}
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-400">Not assigned</span>
                        )}
                      </td>
                      <td className="border p-3">
                        <div className="flex items-center gap-1.5 flex-nowrap">
                          {/* Show Products */}
                          <ActionIconButton
                            onClick={() => {
                              setSelectedOrder(order);
                              setShowProductsModal(true);
                            }}
                            tooltip="Show Products"
                            variant="bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700"
                            icon={
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-4 h-4">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                            }
                          />

                          {/* Payment History */}
                          <ActionIconButton
                            onClick={() => openPaymentModal(order)}
                            tooltip="Payment History"
                            variant="bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700"
                            icon={
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-4 h-4">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.5 8.5h19M2.5 12h19M2.5 15.5h19M4 5.5h16a1.5 1.5 0 011.5 1.5v10a1.5 1.5 0 01-1.5 1.5H4a1.5 1.5 0 01-1.5-1.5V7A1.5 1.5 0 014 5.5z" />
                              </svg>
                            }
                          />

                          {/* Generate / Download Invoice */}
                          {(() => {
                            const isWholesaler = (order.user as any)?.role === 'wholesaler';
                            if (order.invoicePath) {
                              // Invoice exists → always allow download (for both retail & wholesale)
                              return (
                                <ActionIconButton
                                  onClick={() => handleDownloadInvoice(order._id)}
                                  tooltip="Download Invoice"
                                  variant="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
                                  icon={
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-4 h-4">
                                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                                    </svg>
                                  }
                                />
                              );
                            }
                            if (isWholesaler) {
                              // Wholesale: super admin can generate invoice at any time before/after dispatch
                              return (
                                <ActionIconButton
                                  onClick={() => handleGenerateInvoice(order._id)}
                                  tooltip="Generate Invoice"
                                  variant="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
                                  icon={
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-4 h-4">
                                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                                    </svg>
                                  }
                                />
                              );
                            }
                            // Retail: invoice auto-generates on delivery — no manual generate button
                            return null;
                          })()}

                          {/* Update Delivery Charge */}
                          {(order.user as any)?.role === 'wholesaler' &&
                            ['pending', 'confirmed', 'processing'].includes(order.status) && (
                              <ActionIconButton
                                onClick={() => openDeliveryChargeModal(order)}
                                tooltip="Update Delivery"
                                variant="bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700"
                                icon={
                                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                                  </svg>
                                }
                              />
                            )}

                          {/* Reason for decline */}
                          {order.status === 'declined' && order.declineReason && (
                            <div className="relative group flex items-center justify-center">
                              <span className="cursor-help rounded-lg bg-red-100 p-2 text-red-600 hover:bg-red-200 transition-colors">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-4 h-4">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                                </svg>
                              </span>
                              <div className="absolute bottom-full left-1/2 z-30 mb-2 -translate-x-1/2 scale-75 opacity-0 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-bottom pointer-events-none whitespace-normal w-48 rounded bg-gray-950 px-2.5 py-1.5 text-[11px] font-medium text-white shadow-lg text-center leading-relaxed">
                                <strong>Decline Reason:</strong> {order.declineReason}
                                <div className="absolute top-full left-1/2 -mt-1 -translate-x-1/2 border-4 border-transparent border-t-gray-950" />
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="border p-3">
                        {isActionDisabled(order) ? (
                          <select
                            disabled
                            className="w-full rounded border border-gray-300 bg-gray-50 px-2 py-1.5 text-xs text-gray-500 opacity-60 cursor-not-allowed min-w-[130px]"
                          >
                            <option>Actions Disabled</option>
                          </select>
                        ) : (
                          <select
                            className="w-full rounded border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900 cursor-pointer hover:border-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 min-w-[130px]"
                            onChange={(e) => {
                              const action = e.target.value;
                              if (action === 'accept' && canAccept(order)) {
                                handleAccept(order._id);
                              } else if (action === 'decline' && canDecline(order)) {
                                openDeclineModal(order);
                              } else if (action === 'dispatch' && canDispatch(order)) {
                                openDispatchModal(order);
                              }
                              e.target.value = '';
                            }}
                            defaultValue=""
                          >
                            <option value="" disabled>
                              Select Action
                            </option>
                            {canAccept(order) && <option value="accept">Accept</option>}
                            {canDecline(order) && <option value="decline">Decline</option>}
                            {canDispatch(order) && <option value="dispatch">Dispatch</option>}
                          </select>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={14} className="border p-3 text-center">
                      No orders found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Premium Pagination Controls */}
          {filteredOrders.length > 0 && (
            <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
              <div className="text-sm text-gray-700">
                Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
                <span className="font-semibold">{endIndex}</span> of{' '}
                <span className="font-semibold">{totalItems}</span> orders
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
        </div>

        {/* Decline Modal */}
        {showDeclineModal && selectedOrder && (
          <div
            className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-24"
            onClick={() => {
              setShowDeclineModal(false);
              setDeclineReason('');
              setSelectedOrder(null);
            }}
          >
            <div
              className="m-4 w-full max-w-md rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-xl font-bold">Decline Order</h3>
              <p>
                <strong>Order Number:</strong> {selectedOrder.orderNumber}
              </p>
              <p className="mb-4">
                <strong>Customer:</strong> {selectedOrder.user?.name || selectedOrder.user?.email}
              </p>
              <div className="mb-4">
                <label className="mb-1 block inline-flex items-baseline gap-1">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.declineReason
                        ? pageInfo.columns.declineReason
                        : undefined
                    }
                  >
                    Reason for Decline <span className="text-red-600">*</span>
                  </InfoButton>
                </label>
                <textarea
                  value={declineReason}
                  onChange={(e) => setDeclineReason(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  rows={4}
                  placeholder="Enter reason for declining this order..."
                  required
                />
              </div>
              <div className="flex justify-end gap-4">
                <button
                  className="rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
                  onClick={() => {
                    setShowDeclineModal(false);
                    setDeclineReason('');
                    setSelectedOrder(null);
                  }}
                >
                  Cancel
                </button>
                <button
                  className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
                  onClick={handleDecline}
                >
                  Decline Order
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Products Modal */}
        {showProductsModal && selectedOrder && (
          <div
            className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-24"
            onClick={() => {
              setShowProductsModal(false);
              setSelectedOrder(null);
            }}
          >
            <div
              className="m-4 max-h-[80vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-xl font-bold">
                Order Products - {selectedOrder.orderNumber}
              </h3>
              <p>
                <strong>Customer:</strong> {selectedOrder.user?.name || selectedOrder.user?.email}
              </p>
              <p className="mb-4">
                <strong>Total:</strong> ₹{selectedOrder.total?.toFixed(2) || '0.00'}
              </p>
              <div className="mt-4">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border p-3 text-left">Product</th>
                      <th className="border p-3 text-left">Quantity</th>
                      <th className="border p-3 text-left">Price</th>
                      <th className="border p-3 text-left">Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selectedOrder as any).items && (selectedOrder as any).items.length > 0 ? (
                      (selectedOrder as any).items.map((item: any, index: number) => (
                        <tr key={index}>
                          <td className="border p-3">
                            {item.product?.name || item.productName || 'Unknown Product'}
                          </td>
                          <td className="border p-3">{item.quantity || 0}</td>
                          <td className="border p-3">₹{(item.price || 0).toFixed(2)}</td>
                          <td className="border p-3">
                            ₹{((item.price || 0) * (item.quantity || 0)).toFixed(2)}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="border p-3 text-center">
                          No products found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="border-t-2 border-gray-300 pt-4 mt-4">
                <div className="mb-2 flex justify-between">
                  <strong>Subtotal:</strong>
                  <span>₹{selectedOrder.subtotal?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="mb-2 flex justify-between">
                  <strong>Tax:</strong>
                  <span>₹{selectedOrder.tax?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="mb-2 flex justify-between">
                  <strong>Delivery Charge:</strong>
                  <span>₹{selectedOrder.shipping?.toFixed(2) || '0.00'}</span>
                </div>
                {(selectedOrder.deliveryGst || 0) > 0 && (
                  <div className="mb-2 flex justify-between">
                    <strong>Delivery GST:</strong>
                    <span>₹{selectedOrder.deliveryGst?.toFixed(2) || '0.00'}</span>
                  </div>
                )}
                {(selectedOrder.discount || 0) > 0 && (
                  <div className="mb-2 flex justify-between">
                    <strong>Discount:</strong>
                    <span>-₹{selectedOrder.discount?.toFixed(2) || '0.00'}</span>
                  </div>
                )}
                <div className="mt-4 flex justify-between border-t-2 border-gray-800 pt-4 text-lg font-bold">
                  <strong>Total:</strong>
                  <span>₹{selectedOrder.total?.toFixed(2) || '0.00'}</span>
                </div>
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  className="rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
                  onClick={() => {
                    setShowProductsModal(false);
                    setSelectedOrder(null);
                  }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Dispatch Modal */}
        {showDispatchModal && selectedOrder && (
          <div
            className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-24"
            onClick={() => {
              setShowDispatchModal(false);
              setSelectedValetId('');
              setSelectedOrder(null);
            }}
          >
            <div
              className="m-4 w-full max-w-md rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-1 text-xl font-bold">
                {(selectedOrder as any).fulfillment_type === 'courier'
                  ? '📦 Dispatch via Courier'
                  : '🟢 Dispatch to Valet'}
              </h3>
              <p className="mb-0.5 text-sm text-gray-500">
                <strong>Order:</strong> {selectedOrder.orderNumber}
              </p>
              <p className="mb-5 text-sm text-gray-500">
                <strong>Customer:</strong> {selectedOrder.user?.name || selectedOrder.user?.email}
              </p>

              {(selectedOrder as any).fulfillment_type === 'courier' ? (
                /* ── Courier dispatch fields ── */
                <div className="space-y-4">
                  <div>
                    <label className="mb-1 block text-sm font-semibold">
                      Courier Partner <span className="text-red-600">*</span>
                    </label>
                    <select
                      value={courierPartner}
                      onChange={(e) => setCourierPartner(e.target.value)}
                      className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                      required
                    >
                      <option value="">Select courier partner…</option>
                      <option value="delhivery">Delhivery</option>
                      <option value="shiprocket">Shiprocket</option>
                      <option value="blue_dart">Blue Dart</option>
                      <option value="dtdc">DTDC</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-semibold">
                      AWB / Waybill Number <span className="text-red-600">*</span>
                    </label>
                    <input
                      type="text"
                      value={courierAwb}
                      onChange={(e) => setCourierAwb(e.target.value)}
                      placeholder="e.g. 1234567890"
                      className="w-full rounded border border-gray-300 px-3 py-2 text-sm font-mono"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-semibold">
                      Tracking ID <span className="text-xs font-normal text-gray-400">(leave blank to use AWB)</span>
                    </label>
                    <input
                      type="text"
                      value={courierTrackingId}
                      onChange={(e) => setCourierTrackingId(e.target.value)}
                      placeholder="Same as AWB by default"
                      className="w-full rounded border border-gray-300 px-3 py-2 text-sm font-mono"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-semibold">
                      Estimated Delivery Date
                    </label>
                    <input
                      type="date"
                      value={courierEta}
                      onChange={(e) => setCourierEta(e.target.value)}
                      className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              ) : (
                /* ── Hyperlocal valet dispatch fields ── */
                <div>
                  <div className="mb-4">
                    <label className="mb-1 block inline-flex items-baseline gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.valet
                            ? pageInfo.columns.valet
                            : undefined
                        }
                      >
                        Assign Delivery Valet <span className="text-red-600">*</span>
                      </InfoButton>
                    </label>
                    <select
                      value={selectedValetId}
                      onChange={(e) => setSelectedValetId(e.target.value)}
                      className="w-full rounded border border-gray-300 px-3 py-2"
                      required
                    >
                      <option value="">Select a delivery valet...</option>
                      {valets.map((valet) => (
                        <option key={valet._id} value={valet._id}>
                          {valet.name} ({valet.email})
                        </option>
                      ))}
                    </select>
                  </div>
                  {valets.length === 0 && (
                    <p className="mb-4 text-sm text-red-600">
                      No delivery valets available. Please create valet users first.
                    </p>
                  )}
                </div>
              )}

              <div className="mt-6 flex justify-end gap-4">
                <button
                  className="rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
                  onClick={() => {
                    setShowDispatchModal(false);
                    setSelectedValetId('');
                    setSelectedOrder(null);
                  }}
                >
                  Cancel
                </button>
                <button
                  className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
                  onClick={handleDispatch}
                  disabled={
                    (selectedOrder as any).fulfillment_type === 'courier'
                      ? !courierPartner || !courierAwb
                      : !selectedValetId || valets.length === 0
                  }
                >
                  Dispatch Order
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Update Delivery Charge Modal */}
        {showDeliveryChargeModal && selectedOrder && (
          <div
            className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-24"
            onClick={() => {
              setShowDeliveryChargeModal(false);
              setNewDeliveryCharge('');
              setSelectedOrder(null);
            }}
          >
            <div
              className="m-4 w-full max-w-md rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-xl font-bold">Update Delivery Charge</h3>
              <p className="mb-2">
                <strong>Order Number:</strong> {selectedOrder.orderNumber}
              </p>
              <p className="mb-2">
                <strong>Customer:</strong> {selectedOrder.user?.name || selectedOrder.user?.email}
              </p>
              <p className="mb-4">
                <strong>Role:</strong>{' '}
                <span className="capitalize">{(selectedOrder.user as any)?.role}</span>
              </p>

              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium">Current Delivery Charge</label>
                <input
                  type="text"
                  value={`₹${(selectedOrder as any).shipping || 0}`}
                  className="w-full rounded border border-gray-300 bg-gray-50 px-3 py-2"
                  disabled
                />
              </div>

              <div className="mb-4">
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  <InfoButton
                    info={
                      user?.role === 'super_admin' && pageInfo.columns?.deliveryCharge
                        ? pageInfo.columns.deliveryCharge
                        : undefined
                    }
                  >
                    New Delivery Charge <span className="text-red-500">*</span>
                  </InfoButton>
                </label>
                <input
                  type="number"
                  value={newDeliveryCharge}
                  onChange={(e) => setNewDeliveryCharge(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  placeholder="Enter new delivery charge"
                  step="0.01"
                  min="0"
                  required
                />
              </div>

              <div className="mb-4 rounded border border-yellow-200 bg-yellow-50 p-3">
                <strong className="text-yellow-800">📌 Note:</strong>
                <ul className="ml-5 mt-2 list-disc space-y-1 text-sm text-yellow-800">
                  <li>
                    <strong>UPI payments:</strong> Amount difference will be settled during delivery
                    as COD
                  </li>
                  <li>
                    <strong>Credit/COD:</strong> Amount difference will be added to remaining amount
                  </li>
                  <li>Can only update before order is dispatched</li>
                </ul>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  className="rounded bg-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-400"
                  onClick={() => {
                    setShowDeliveryChargeModal(false);
                    setNewDeliveryCharge('');
                    setSelectedOrder(null);
                  }}
                >
                  Cancel
                </button>
                <button
                  className="rounded bg-gradient-to-r from-teal-500 to-teal-600 px-4 py-2 text-white hover:from-teal-600 hover:to-teal-700"
                  onClick={handleUpdateDeliveryCharge}
                >
                  Update Delivery Charge
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Payment History Modal */}
      <Modal
        isOpen={showPaymentModal}
        onClose={() => {
          setShowPaymentModal(false);
          setSelectedOrder(null);
          setPaymentDetails([]);
        }}
        title="Payment history"
      >
        {paymentLoading ? (
          <div>Loading...</div>
        ) : (
          <div className="space-y-4">
            {paymentDetails.length === 0 && <div>No payments found.</div>}
            {paymentDetails.map((payment) => (
              <details key={payment._id} className="rounded border">
                <summary className="flex cursor-pointer items-center justify-between p-3">
                  <span>
                    Payment {payment.paymentId || payment._id} — ₹{payment.totalAmount}
                  </span>
                  <span className="text-sm text-gray-600">
                    Method: {payment.paymentMethod?.toUpperCase()}
                  </span>
                </summary>
                <div className="space-y-2 p-3">
                  <div>Amount Paid: ₹{payment.amountPaid}</div>
                  <div>Amount Remaining: ₹{payment.amountRemaining}</div>
                  <div className="space-y-2">
                    <div className="font-semibold">Entries</div>
                    {(payment.paymentEntries || []).map((entry: any) => (
                      <div
                        key={entry.entryId}
                        className="flex items-center justify-between rounded border p-2"
                      >
                        <div>
                          <div>
                            Entry #{entry.entryId} — ₹{entry.amount}
                          </div>
                          <div className="text-sm text-gray-600">
                            Method:{' '}
                            {entry.paymentMethod?.toUpperCase() ||
                              payment.paymentMethod?.toUpperCase()}
                          </div>
                          {entry.notes && (
                            <div className="text-sm text-gray-500">{entry.notes}</div>
                          )}
                          {entry.image && (
                            <div className="mt-2">
                              <p className="mb-1 text-xs font-semibold text-gray-500">
                                Screenshot:
                              </p>
                              <img
                                src={
                                  entry.image.startsWith('/')
                                    ? `${process.env.NEXT_PUBLIC_API_URL || ''}${entry.image}`
                                    : entry.image
                                }
                                alt="Payment Screenshot"
                                className="max-h-[200px] max-w-[200px] cursor-pointer rounded border object-contain"
                                onClick={() =>
                                  window.open(
                                    entry.image.startsWith('/')
                                      ? `${process.env.NEXT_PUBLIC_API_URL || ''}${entry.image}`
                                      : entry.image,
                                    '_blank'
                                  )
                                }
                              />
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <span
                            className={`rounded px-2 py-1 text-xs ${entry.verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}
                          >
                            {entry.verified ? 'Verified' : 'Pending'}
                          </span>
                          <button
                            className="rounded bg-blue-600 px-2 py-1 text-xs text-white"
                            onClick={() =>
                              handleVerifyPayment(payment._id, entry.entryId, !entry.verified)
                            }
                          >
                            Mark {entry.verified ? 'Unverified' : 'Verified'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </details>
            ))}
          </div>
        )}
      </Modal>
    </>
  );
}
