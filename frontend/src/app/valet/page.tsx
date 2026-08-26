'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateTimeIST } from '@/utils/dateUtils';

interface Order {
  _id: string;
  orderNumber?: string;
  user?: {
    _id: string;
    name: string;
    email: string;
    phone?: string;
    userId?: number;
  };
  shippingAddress?: {
    street?: string;
    city?: string;
    state?: string;
    zipCode?: string;
    country?: string;
    addressLine2?: string;
    landmark?: string;
    name?: string;
  };
  items?: Array<{
    product?: {
      name: string;
    };
    quantity: number;
    price: number;
  }>;
  paymentMethod?: string;
  total: number;
  assignedValet?: string;
  status?: string;
  createdAt?: string;
}

export default function ValetDashboard() {
  const { user, logout, loading: authLoading } = useAuth();
  const { theme } = useTheme();
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [returns, setReturns] = useState<any[]>([]);
  const [pendingAssignments, setPendingAssignments] = useState<Order[]>([]);
  const [pendingReturns, setPendingReturns] = useState<any[]>([]);
  const [respondingOrderId, setRespondingOrderId] = useState<string | null>(null);
  const [respondingReturnId, setRespondingReturnId] = useState<string | null>(null);
  const [declineReason, setDeclineReason] = useState('');
  const [showDeclineInput, setShowDeclineInput] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<Record<string, number>>({});
  const [returnCountdown, setReturnCountdown] = useState<Record<string, number>>({});
  const [loadingReturns, setLoadingReturns] = useState(false);
  const [expandedReturns, setExpandedReturns] = useState<Set<string>>(new Set());
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [expandedOrders, setExpandedOrders] = useState<Set<string>>(new Set());
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  const [valetLocation, setValetLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    if (authLoading) return;
    const userRole = user?.effectiveRole || user?.role;
    if (userRole !== 'valet') {
      router.replace('/');
      return;
    }
    fetchOrders();
    fetchReturns();
    // Get valet's current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setValetLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          });
        },
        (error) => {
          console.error('Error getting location:', error);
        }
      );
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, router, startDate, endDate]);

  // Poll for pending assignments every 15 s
  useEffect(() => {
    fetchPendingAssignments();
    fetchPendingReturns();
    const interval = setInterval(() => {
      fetchPendingAssignments();
      fetchPendingReturns();
    }, 15000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Live countdown timers for pending forward delivery assignments
  useEffect(() => {
    const tick = setInterval(() => {
      setCountdown((_prev) => {
        const next: Record<string, number> = {};
        pendingAssignments.forEach((o) => {
          const assignedAt = (o as any).valetAssignedAt;
          if (!assignedAt) return;
          const isUrgent = (o as any).isUrgentDelivery;
          const timeoutMs = (isUrgent ? 5 : 20) * 60 * 1000;
          const elapsed = Date.now() - new Date(assignedAt).getTime();
          const remaining = Math.max(0, Math.round((timeoutMs - elapsed) / 1000));
          next[o._id] = remaining;
        });
        return next;
      });

      // Live countdown timers for pending return pickups (strictly 20 minutes)
      setReturnCountdown((_prev) => {
        const next: Record<string, number> = {};
        pendingReturns.forEach((r) => {
          const assignedAt = r.valetAssignedAt;
          if (!assignedAt) return;
          const timeoutMs = 20 * 60 * 1000;
          const elapsed = Date.now() - new Date(assignedAt).getTime();
          const remaining = Math.max(0, Math.round((timeoutMs - elapsed) / 1000));
          next[r._id || r.id] = remaining;
        });
        return next;
      });
    }, 1000);
    return () => clearInterval(tick);
  }, [pendingAssignments, pendingReturns]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;

      const response = await api.get('/orders', { params });
      // Filter orders assigned to this valet
      const assignedOrders = (response.data || []).filter(
        (order: Order) =>
          order.assignedValet === user?._id || (order as any).assignedValet?._id === user?._id
      );
      // Sort by date descending (newest first)
      assignedOrders.sort(
        (a: Order, b: Order) =>
          new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime()
      );
      setOrders(assignedOrders);
    } catch (error: any) {
      console.error('Failed to fetch orders', error);
      toast.error('Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingAssignments = async () => {
    try {
      const res = await fetch('/api/orders/valet/pending', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPendingAssignments(data);
      }
    } catch (e) {
      console.error('Error fetching pending assignments:', e);
    }
  };

  const fetchPendingReturns = async () => {
    try {
      const res = await fetch('/api/returns/valet/pending', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPendingReturns(data);
      }
    } catch (e) {
      console.error('Error fetching pending returns:', e);
    }
  };

  const fetchReturns = async () => {
    try {
      setLoadingReturns(true);
      const res = await api.get('/returns/valet/assigned');
      setReturns(res.data || []);
    } catch (e) {
      console.error('Error responding to assignment:', e);
      alert('Failed to respond to assignment');
    } finally {
      setRespondingOrderId(null);
      setLoadingReturns(false);
    }
  };

  const handleReturnRespond = async (returnId: string, accept: boolean) => {
    if (!accept && !declineReason) {
      setShowDeclineInput(returnId);
      return;
    }
    try {
      setRespondingReturnId(returnId);
      const res = await fetch(`/api/returns/valet/${returnId}/response`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ accept, declineReason: accept ? undefined : declineReason }),
      });
      if (res.ok) {
        setDeclineReason('');
        setShowDeclineInput(null);
        await Promise.all([fetchPendingReturns(), fetchReturns()]);
      } else {
        const err = await res.json();
        alert(err.detail || 'Failed to respond to return pickup');
      }
    } catch (e) {
      console.error('Error responding to return:', e);
      alert('Failed to respond to return pickup');
    } finally {
      setRespondingReturnId(null);
    }
  };

  const handleMarkCollected = async (returnId: string) => {
    try {
      await api.put(`/returns/valet/${returnId}/collect`);
      toast.success('Return marked as collected');
      fetchReturns();
    } catch (error: any) {
      console.error('Failed to mark return as collected', error);
      toast.error(error.response?.data?.message || 'Failed to mark return as collected');
    }
  };

  const handleMarkDelivered = async (orderId: string) => {
    try {
      await api.put(`/orders/${orderId}/status`, { status: 'delivered' });
      toast.success('Order marked as delivered');
      fetchOrders();
      setShowOrderModal(false);
      setSelectedOrder(null);
    } catch (error: any) {
      console.error('Failed to mark order as delivered', error);
      toast.error(error.response?.data?.message || 'Failed to mark order as delivered');
    }
  };

  const getTotalToCollect = (order: Order) => {
    if (order.paymentMethod === 'upi') {
      return 0;
    } else if (order.paymentMethod === 'credit') {
      return 0;
    } else if (order.paymentMethod === 'cod') {
      return order.total || 0;
    }
    return 0;
  };

  const formatAddress = (address?: Order['shippingAddress']) => {
    if (!address) return 'N/A';
    const parts: string[] = [];
    if (address.name) parts.push(`Name: ${address.name}`);
    if (address.street) parts.push(address.street);
    if (address.addressLine2) parts.push(address.addressLine2);
    if (address.landmark) parts.push(`Landmark: ${address.landmark}`);
    if (address.city && address.state) {
      parts.push(`${address.city}, ${address.state}`);
    } else if (address.city) parts.push(address.city);
    if (address.zipCode) parts.push(`PIN: ${address.zipCode}`);
    if (address.country) parts.push(address.country);
    return parts.length > 0 ? parts.join(', ') : 'N/A';
  };

  const handleViewOrder = (order: Order) => {
    setSelectedOrder(order);
    setShowOrderModal(true);
  };

  const toggleOrderExpand = (orderId: string) => {
    setExpandedOrders((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(orderId)) {
        newSet.delete(orderId);
      } else {
        newSet.add(orderId);
      }
      return newSet;
    });
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const clearDateFilters = () => {
    setStartDate('');
    setEndDate('');
    setStatusFilter('all');
  };

  const filteredOrders = orders.filter((order) => {
    // Status filter
    if (statusFilter !== 'all') {
      if (statusFilter === 'pending') {
        // Pending means shipped but not delivered
        if (order.status === 'delivered' || order.status === 'cancelled') {
          return false;
        }
      } else if (order.status !== statusFilter) {
        return false;
      }
    }
    return true;
  });

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading orders...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gradient-to-r from-red-600 to-red-700 text-white shadow-md">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1
              className="cursor-pointer text-2xl font-bold"
              onClick={() => router.push('/valet')}
              style={{ color: theme.primary }}
            >
              Stationery Junction
            </h1>
            <div className="flex items-center gap-4">
              <div className="relative">
                <button
                  onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                  className="flex items-center gap-2 rounded bg-white px-4 py-2 text-red-600 hover:bg-gray-100"
                >
                  👤 {user?.name}
                </button>
                {showProfileDropdown && (
                  <div className="absolute right-0 z-10 mt-2 min-w-[150px] rounded bg-white p-2 shadow-lg">
                    <button
                      onClick={() => {
                        router.push('/valet');
                        setShowProfileDropdown(false);
                      }}
                      className="block w-full px-4 py-2 text-left text-black hover:bg-gray-100"
                    >
                      My Dashboard
                    </button>
                    <button
                      onClick={() => {
                        handleLogout();
                        setShowProfileDropdown(false);
                      }}
                      className="block w-full px-4 py-2 text-left text-black hover:bg-gray-100"
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="mb-6 grid grid-cols-3 gap-2 md:gap-4">
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg bg-white p-2 text-center shadow-md md:flex-row md:justify-start md:gap-4 md:p-4 md:text-left">
            <div className="text-2xl md:text-4xl">📦</div>
            <div>
              <div className="text-xs uppercase text-gray-500">Total Orders</div>
              <div className="text-lg font-bold md:text-2xl">{orders.length}</div>
            </div>
          </div>
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg bg-white p-2 text-center shadow-md md:flex-row md:justify-start md:gap-4 md:p-4 md:text-left">
            <div className="text-2xl md:text-4xl">🚚</div>
            <div>
              <div className="text-xs uppercase text-gray-500">Pending Deliveries</div>
              <div className="text-lg font-bold md:text-2xl">
                {orders.filter((o) => o.status !== 'delivered' && o.status !== 'cancelled').length}
              </div>
            </div>
          </div>
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg bg-white p-2 text-center shadow-md md:flex-row md:justify-start md:gap-4 md:p-4 md:text-left">
            <div className="text-2xl md:text-4xl">💰</div>
            <div>
              <div className="text-xs uppercase text-gray-500">Total to Collect</div>
              <div className="text-lg font-bold md:text-2xl">
                ₹
                {orders
                  .filter((o) => o.status !== 'delivered')
                  .reduce((sum, order) => sum + getTotalToCollect(order), 0)
                  .toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-md">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold">Assigned Orders</h2>
            <div className="flex flex-wrap items-center gap-4">
              {/* 
                Map View temporarily hidden from UI per request.
                To re-enable, uncomment or add the toggle buttons back here.
              */}
              <div>
                <label className="mr-2 text-sm font-medium">Status:</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="all">All</option>
                  <option value="pending">Pending</option>
                  <option value="delivered">Delivered</option>
                </select>
              </div>
              <div>
                <label className="mr-2 text-sm font-medium">Start Date:</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="rounded border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mr-2 text-sm font-medium">End Date:</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="rounded border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              {(startDate || endDate || statusFilter !== 'all') && (
                <button
                  onClick={clearDateFilters}
                  className="rounded bg-gray-500 px-4 py-2 text-sm text-white hover:bg-gray-600"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {filteredOrders.length === 0 ? (
            <div className="py-12 text-center text-gray-500">
              <p>No orders match your filters.</p>
            </div>
          ) : viewMode === 'map' ? (
            <div className="mt-6">
              <div className="mb-5 h-[600px] w-full overflow-hidden rounded-lg border border-gray-300">
                {valetLocation ? (
                  <iframe
                    width="100%"
                    height="100%"
                    frameBorder="0"
                    style={{ border: 0 }}
                    // NOTE: API key is currently optional for development
                    // TODO: Make API key mandatory in production migration
                    // Set NEXT_PUBLIC_GOOGLE_MAPS_API_KEY in production environment
                    src={`https://www.google.com/maps/embed/v1/view?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || ''}&center=${valetLocation.lat},${valetLocation.lng}&zoom=12`}
                    allowFullScreen
                  />
                ) : (
                  <div className="flex h-full items-center justify-center bg-gray-100">
                    <div className="text-center">
                      <p className="text-gray-600">📍 Requesting location permission...</p>
                      <p className="mt-2 text-xs text-gray-500">
                        Please allow location access to view map
                      </p>
                    </div>
                  </div>
                )}
              </div>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="mb-4">
                  <p className="mb-1 text-sm font-semibold">📍 You are here</p>
                  <p className="text-xs text-gray-600">
                    {valetLocation
                      ? `Lat: ${valetLocation.lat.toFixed(6)}, Lng: ${valetLocation.lng.toFixed(6)}`
                      : 'Location not available'}
                  </p>
                </div>
                <div className="mb-3">
                  <p className="text-sm font-semibold">
                    🏠 Undelivered Orders (
                    {
                      filteredOrders.filter(
                        (o) => o.status !== 'delivered' && o.status !== 'cancelled'
                      ).length
                    }
                    )
                  </p>
                </div>
                <div className="max-h-[300px] space-y-2 overflow-y-auto">
                  {filteredOrders
                    .filter((o) => o.status !== 'delivered' && o.status !== 'cancelled')
                    .map((order) => (
                      <div key={order._id} className="rounded border border-gray-200 bg-white p-3">
                        <div className="mb-2 flex items-start justify-between">
                          <strong className="text-sm">
                            🏠 Order {order.orderNumber || order._id}
                          </strong>
                          <span className="text-xs text-gray-600">
                            {(order.user as any)?.name || 'N/A'}
                          </span>
                        </div>
                        <div className="mb-2 text-xs text-gray-600">
                          {formatAddress(order.shippingAddress)}
                        </div>
                        <div className="mt-2">
                          <a
                            href={(order.user as any)?.locationLink || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(formatAddress(order.shippingAddress))}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                          >
                            🗺️ Open in Google Maps
                          </a>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredOrders.map((order) => {
                const isExpanded = expandedOrders.has(order._id);
                return (
                  <div
                    key={order._id}
                    className="rounded-lg border border-gray-200 bg-white shadow-sm"
                  >
                    <div
                      className="flex cursor-pointer items-center justify-between border-b border-gray-200 p-4 hover:bg-gray-50"
                      onClick={() => toggleOrderExpand(order._id)}
                    >
                      <div>
                        <div className="mb-1 text-xs uppercase text-gray-500">Order Number</div>
                        <div className="text-lg font-bold">{order.orderNumber || order._id}</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span
                          className={`rounded px-3 py-1 text-sm font-semibold ${
                            order.status === 'delivered'
                              ? 'bg-green-100 text-green-800'
                              : order.status === 'shipped'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {order.status === 'shipped'
                            ? '🚚 Shipped'
                            : order.status === 'delivered'
                              ? '✅ Delivered'
                              : order.status || 'pending'}
                        </span>
                        <span className="text-xl text-gray-500">{isExpanded ? '▼' : '▶'}</span>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="space-y-4 p-4">
                        <div className="grid gap-4 md:grid-cols-3">
                          <div>
                            <div className="mb-1 text-xs uppercase text-gray-500">
                              Customer Name
                            </div>
                            <div className="font-semibold">{order.user?.name || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="mb-1 text-xs uppercase text-gray-500">Date</div>
                            <div>{order.createdAt ? formatDateTimeIST(order.createdAt) : '-'}</div>
                          </div>
                          <div>
                            <div className="mb-1 text-xs uppercase text-gray-500">
                              Total to Collect
                            </div>
                            <div
                              className={`text-lg font-bold ${getTotalToCollect(order) > 0 ? 'text-red-600' : 'text-gray-600'}`}
                            >
                              ₹{getTotalToCollect(order).toFixed(2)}
                            </div>
                          </div>
                        </div>

                        <div>
                          <div className="mb-1 text-xs uppercase text-gray-500">
                            📍 Delivery Address
                          </div>
                          <div className="text-sm">{formatAddress(order.shippingAddress)}</div>
                          <div className="mt-2">
                            <a
                              href={(order.user as any)?.locationLink || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(formatAddress(order.shippingAddress))}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
                            >
                              🗺️ Open in Google Maps
                            </a>
                          </div>
                        </div>

                        <div>
                          <div className="mb-1 text-xs uppercase text-gray-500">Items</div>
                          <div className="space-y-1">
                            {order.items?.map((item, idx) => (
                              <div key={idx} className="text-sm">
                                {item.product?.name || 'Product'} - Qty: {item.quantity || 0}
                              </div>
                            )) || 'N/A'}
                          </div>
                        </div>

                        <div className="flex gap-2 border-t pt-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewOrder(order);
                            }}
                            className="rounded bg-gradient-to-r from-cyan-500 to-cyan-600 px-4 py-2 text-sm text-white hover:from-cyan-600 hover:to-cyan-700"
                          >
                            View Details
                          </button>
                          {order.status !== 'delivered' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMarkDelivered(order._id);
                              }}
                              className="rounded bg-gradient-to-r from-green-500 to-green-600 px-4 py-2 text-sm text-white hover:from-green-600 hover:to-green-700"
                            >
                              Mark Delivered
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Assigned Returns Section */}
        <div className="mt-8 rounded-lg bg-white p-6 shadow-md">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold">Assigned Return Collections</h2>
            <button
              onClick={fetchReturns}
              className="rounded bg-gradient-to-r from-purple-500 to-purple-650 px-4 py-2 text-sm text-white hover:from-purple-600 hover:to-purple-700"
            >
              Refresh Returns
            </button>
          </div>

          {loadingReturns ? (
            <div className="py-6 text-center text-gray-500">Loading returns...</div>
          ) : returns.length === 0 ? (
            <div className="py-12 text-center text-gray-500">
              <p>No return pickup requests currently assigned to you.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {returns.map((ret) => {
                const isExpanded = expandedReturns.has(ret._id);
                return (
                  <div key={ret._id} className="rounded-lg border border-gray-200 bg-white shadow-sm">
                    <div
                      className="flex cursor-pointer items-center justify-between border-b border-gray-200 p-4 hover:bg-gray-50"
                      onClick={() => {
                        const newSet = new Set(expandedReturns);
                        if (newSet.has(ret._id)) newSet.delete(ret._id);
                        else newSet.add(ret._id);
                        setExpandedReturns(newSet);
                      }}
                    >
                      <div>
                        <div className="mb-1 text-xs uppercase text-gray-500">Return request id</div>
                        <div className="text-lg font-bold">#{ret._id?.slice(-8)}</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="rounded bg-purple-100 text-purple-800 px-3 py-1 text-sm font-semibold">
                          🔄 {ret.status}
                        </span>
                        <span className="text-xl text-gray-500">{isExpanded ? '▼' : '▶'}</span>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="space-y-4 p-4">
                        <div className="grid gap-4 md:grid-cols-3">
                          <div>
                            <div className="mb-1 text-xs uppercase text-gray-500">Customer Name</div>
                            <div className="font-semibold">{ret.user?.name || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="mb-1 text-xs uppercase text-gray-500">Customer Phone</div>
                            <div className="font-semibold">{ret.user?.phone || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="mb-1 text-xs uppercase text-gray-500">Payment method to collect</div>
                            <div className="font-semibold text-purple-750 uppercase">
                              ₹{ret.deliveryCharge || 0} ({ret.paymentMethod})
                            </div>
                          </div>
                        </div>

                        {ret.deliverySlot && (
                          <div className="mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1.5 rounded-lg border border-purple-200 font-medium inline-block">
                            📅 Scheduled Pickup Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime} ({ret.deliverySlot.date})
                          </div>
                        )}

                        {ret.deliverySlot && (
                          <div className="mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1.5 rounded-lg border border-purple-200 font-medium inline-block">
                            📅 Scheduled Pickup Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime} ({ret.deliverySlot.date})
                          </div>
                        )}

                        {ret.deliverySlot && (
                          <div className="mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1.5 rounded-lg border border-purple-200 font-medium inline-block">
                            📅 Scheduled Pickup Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime} ({ret.deliverySlot.date})
                          </div>
                        )}

                        {ret.deliverySlot && (
                          <div className="mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1.5 rounded-lg border border-purple-200 font-medium inline-block">
                            📅 Scheduled Pickup Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime} ({ret.deliverySlot.date})
                          </div>
                        )}

                        {ret.deliverySlot && (
                          <div className="mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1.5 rounded-lg border border-purple-200 font-medium inline-block">
                            📅 Scheduled Pickup Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime} ({ret.deliverySlot.date})
                          </div>
                        )}

                        {ret.deliverySlot && (
                          <div className="mb-3 text-xs bg-purple-50 text-purple-800 px-3 py-1.5 rounded-lg border border-purple-200 font-medium inline-block">
                            📅 Scheduled Pickup Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime} ({ret.deliverySlot.date})
                          </div>
                        )}

                        <div>
                          <div className="mb-1 text-xs uppercase text-gray-500">📍 Pickup Address</div>
                          <div className="text-sm">
                            {ret.user?.address ? formatAddress({
                              street: ret.user.address.street,
                              city: ret.user.address.city,
                              state: ret.user.address.state,
                              zipCode: ret.user.address.pincode,
                              country: ret.user.address.country,
                            }) : (ret.shippingAddress ? formatAddress(ret.shippingAddress) : 'N/A')}
                          </div>
                        </div>

                        <div>
                          <div className="mb-1 text-xs uppercase text-gray-500">Items to Collect</div>
                          <div className="space-y-1">
                            {ret.items?.map((item: any, idx: number) => (
                              <div key={idx} className="text-sm">
                                {item.product?.name || 'Product'} - Qty: {item.quantity || 0}
                                <div className="text-xs text-red-500 italic mt-0.5">Reason: {item.reason}</div>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="border-t pt-2">
                          <button
                            onClick={() => handleMarkCollected(ret._id)}
                            className="rounded bg-gradient-to-r from-purple-500 to-purple-650 px-4 py-2 text-sm text-white hover:from-purple-600 hover:to-purple-700"
                          >
                            Mark as Collected
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {showOrderModal && selectedOrder && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          onClick={() => {
            setShowOrderModal(false);
            setSelectedOrder(null);
          }}
        >
          <div
            className="mx-4 max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b p-6">
              <h3 className="text-xl font-bold">
                Order Details - {selectedOrder.orderNumber || selectedOrder._id}
              </h3>
              <button
                className="text-2xl text-gray-500 hover:text-gray-700"
                onClick={() => {
                  setShowOrderModal(false);
                  setSelectedOrder(null);
                }}
              >
                ×
              </button>
            </div>
            <div className="space-y-6 p-6">
              <div>
                <h4 className="mb-3 border-b-2 border-red-600 pb-2 text-lg font-semibold">
                  Customer Information
                </h4>
                <p>
                  <strong>Name:</strong> {selectedOrder.user?.name || 'N/A'}
                </p>
                <p>
                  <strong>Email:</strong> {selectedOrder.user?.email || 'N/A'}
                </p>
                <p>
                  <strong>Phone:</strong> {selectedOrder.user?.phone || 'N/A'}
                </p>
              </div>

              <div>
                <h4 className="mb-3 border-b-2 border-red-600 pb-2 text-lg font-semibold">
                  Delivery Address
                </h4>
                <p>{formatAddress(selectedOrder.shippingAddress)}</p>
                <div className="mt-2">
                  <a
                    href={(selectedOrder.user as any)?.locationLink || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(formatAddress(selectedOrder.shippingAddress))}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-blue-600 hover:underline"
                  >
                    🗺️ Open in Google Maps
                  </a>
                </div>
              </div>

              <div>
                <h4 className="mb-3 border-b-2 border-red-600 pb-2 text-lg font-semibold">
                  Order Items
                </h4>
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border p-2 text-left">Product</th>
                      <th className="border p-2 text-left">Quantity</th>
                      <th className="border p-2 text-left">Price</th>
                      <th className="border p-2 text-left">Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedOrder.items?.map((item, idx) => (
                      <tr key={idx}>
                        <td className="border p-2">{item.product?.name || 'Product'}</td>
                        <td className="border p-2">{item.quantity || 0}</td>
                        <td className="border p-2">₹{item.price?.toFixed(2) || '0.00'}</td>
                        <td className="border p-2">
                          ₹{((item.price || 0) * (item.quantity || 0)).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div>
                <h4 className="mb-3 border-b-2 border-red-600 pb-2 text-lg font-semibold">
                  Payment Information
                </h4>
                <p>
                  <strong>Payment Method:</strong>{' '}
                  {selectedOrder.paymentMethod?.toUpperCase() || 'N/A'}
                </p>
                <p>
                  <strong>Subtotal:</strong> ₹{(selectedOrder as any).subtotal?.toFixed(2) || '0.00'}
                </p>
                <p>
                  <strong>Tax:</strong> ₹{(selectedOrder as any).tax?.toFixed(2) || '0.00'}
                </p>
                <p>
                  <strong>Delivery Charge:</strong> ₹{(selectedOrder as any).shipping?.toFixed(2) || '0.00'}
                </p>
                {(selectedOrder as any).deliveryGst > 0 && (
                  <p>
                    <strong>Delivery GST:</strong> ₹{(selectedOrder as any).deliveryGst?.toFixed(2) || '0.00'}
                  </p>
                )}
                {(selectedOrder as any).discount > 0 && (
                  <p>
                    <strong>Discount:</strong> -₹{(selectedOrder as any).discount?.toFixed(2) || '0.00'}
                  </p>
                )}
                <p>
                  <strong>Total Amount:</strong> ₹{selectedOrder.total?.toFixed(2) || '0.00'}
                </p>
                <p>
                  <strong>Amount to Collect:</strong>
                  <span
                    className={`ml-2 text-xl ${getTotalToCollect(selectedOrder) > 0 ? 'text-red-600' : 'text-gray-600'}`}
                  >
                    ₹{getTotalToCollect(selectedOrder).toFixed(2)}
                  </span>
                </p>
              </div>
            </div>
            <div className="border-t p-6">
              {selectedOrder.status !== 'delivered' && (
                <button
                  onClick={() => handleMarkDelivered(selectedOrder._id)}
                  className="w-full rounded bg-gradient-to-r from-green-500 to-green-600 px-4 py-2 text-white hover:from-green-600 hover:to-green-700"
                >
                  Mark as Delivered
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
