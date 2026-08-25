'use client';

import { useState, useEffect } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateTimeIST } from '@/utils/dateUtils';
import { logger } from '@/utils/logger';

interface Notification {
  _id: string;
  type: 'new_order' | 'new_payment' | 'low_stock';
  title: string;
  message: string;
  data: any;
  isRead: boolean;
  isAcknowledged: boolean;
  createdAt: string;
}

interface Order {
  _id: string;
  orderNumber?: string;
  user?: {
    name: string;
  };
  total: number;
  paymentMethod: string;
  status: string;
  createdAt: string;
  items?: Array<{
    product?: {
      name: string;
    };
    quantity: number;
    price: number;
  }>;
}

interface Payment {
  _id: string;
  paymentId?: string;
  orderNumber?: string;
  orderId: string;
  customerName: string;
  totalAmount: number;
  amountPaid: number;
  amountRemaining: number;
  paymentMethod: string;
  paymentEntries?: Array<{
    entryId: number;
    amount: number;
    image?: string;
    verified: boolean;
  }>;
}

interface Product {
  _id: string;
  sku: string;
  name: string;
  stock: number;
  category?: string;
}

export default function Notifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  const [showNotificationModal, setShowNotificationModal] = useState(false);
  const [viewUnreadOnly, setViewUnreadOnly] = useState(false);
  const [markingAll, setMarkingAll] = useState(false);

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();

    let interval: ReturnType<typeof setInterval> | null = setInterval(() => {
      fetchNotifications();
      fetchUnreadCount();
    }, 30000);

    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (interval) { clearInterval(interval); interval = null; }
      } else {
        fetchNotifications();
        fetchUnreadCount();
        interval = setInterval(() => { fetchNotifications(); fetchUnreadCount(); }, 30000);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (interval) clearInterval(interval);
    };
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await api.get('/notifications/');
      setNotifications(response.data || []);
    } catch (error: any) {
      logger.error('Error fetching notifications:', error);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await api.get('/notifications/unread-count/');
      setUnreadCount(response.data.count || 0);
    } catch (error: any) {
      logger.error('Error fetching unread count:', error);
    }
  };

  const handleAcknowledge = async (notificationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.put(`/notifications/${notificationId}/acknowledge`);
      await fetchNotifications();
      await fetchUnreadCount();
      toast.success('Notification acknowledged');
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to acknowledge notification');
    }
  };

  const handleMarkAllAsRead = async () => {
    setMarkingAll(true);
    try {
      await api.put('/notifications/read-all/');
      await fetchNotifications();
      await fetchUnreadCount();
      toast.success('All notifications marked as read');
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to mark all as read');
    } finally {
      setMarkingAll(false);
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    setSelectedNotification(notification);
    setShowNotificationModal(true);

    if (!notification.isRead) {
      try {
        await api.put(`/notifications/${notification._id}/read`);
        await fetchNotifications();
        await fetchUnreadCount();
      } catch (error: any) {
        logger.error('Error marking notification as read:', error);
      }
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'new_order':
        return '📦';
      case 'new_payment':
        return '💰';
      case 'low_stock':
        return '⚠️';
      default:
        return '🔔';
    }
  };

  const unreadNotifications = notifications.filter((n) => !n.isAcknowledged);
  const readNotifications = notifications.filter((n) => n.isAcknowledged);

  // When "View Unread only" is active, hide the read section
  const showRead = !viewUnreadOnly;

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative p-2 text-2xl"
      >
        🔔
        {unreadCount > 0 && (
          <span className="absolute right-0 top-0 flex h-5 w-5 items-center justify-center rounded-full bg-red-600 text-xs font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {showNotifications && (
        <div className="absolute right-0 top-full z-50 mt-2 max-h-[600px] w-96 overflow-hidden rounded-lg border border-gray-300 bg-white shadow-lg">
          {/* Header */}
          <div className="flex items-center justify-between border-b bg-gray-50 p-4">
            <h3 className="text-lg font-semibold">Notifications</h3>
            <button
              onClick={() => setShowNotifications(false)}
              className="text-2xl text-gray-600 hover:text-gray-800"
            >
              ×
            </button>
          </div>

          {/* Action bar: View Unread only + Mark all as Read */}
          <div className="flex items-center justify-between gap-2 border-b bg-white px-4 py-2">
            <button
              onClick={() => setViewUnreadOnly(!viewUnreadOnly)}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                viewUnreadOnly
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              {viewUnreadOnly ? 'Viewing Unread' : 'View Unread Only'}
            </button>
            <button
              onClick={handleMarkAllAsRead}
              disabled={markingAll || unreadNotifications.length === 0}
              className="flex items-center gap-1.5 rounded-md bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 transition-colors hover:bg-green-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              {markingAll ? 'Marking...' : 'Mark All Read'}
            </button>
          </div>

          <div className="max-h-[460px] overflow-y-auto">
            {unreadNotifications.length === 0 && readNotifications.length === 0 ? (
              <div className="p-10 text-center text-gray-500">No notifications</div>
            ) : viewUnreadOnly && unreadNotifications.length === 0 ? (
              <div className="p-10 text-center text-gray-500">No unread notifications</div>
            ) : (
              <>
                {unreadNotifications.length > 0 && (
                  <div className="p-2">
                    <h4 className="mb-2 text-xs uppercase text-gray-600">
                      Unread ({unreadNotifications.length})
                    </h4>
                    {unreadNotifications.map((notification) => (
                      <div
                        key={notification._id}
                        className={`cursor-pointer border-b p-3 hover:bg-gray-50 ${!notification.isAcknowledged ? 'bg-yellow-50 font-semibold' : ''}`}
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex flex-1 gap-3">
                            <div className="text-2xl">{getNotificationIcon(notification.type)}</div>
                            <div className="flex-1">
                              <div className="text-sm font-semibold">{notification.title}</div>
                              <div className="text-sm text-gray-600">{notification.message}</div>
                              <div className="mt-1 text-xs text-gray-400">
                                {formatDateTimeIST(notification.createdAt)}
                              </div>
                            </div>
                          </div>
                          <button
                            className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-green-600 text-white transition-colors hover:bg-green-700"
                            onClick={(e) => handleAcknowledge(notification._id, e)}
                            title="Mark as read"
                          >
                            <svg
                              width="12"
                              height="12"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="3"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {showRead && readNotifications.length > 0 && (
                  <div className="p-2">
                    <h4 className="mb-2 text-xs uppercase text-gray-600">
                      Read ({readNotifications.length})
                    </h4>
                    {readNotifications.map((notification) => (
                      <div
                        key={notification._id}
                        className="cursor-pointer border-b p-3 hover:bg-gray-50"
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex flex-1 gap-3">
                            <div className="text-2xl">{getNotificationIcon(notification.type)}</div>
                            <div className="flex-1">
                              <div className="text-sm font-semibold">{notification.title}</div>
                              <div className="text-sm text-gray-600">{notification.message}</div>
                              <div className="mt-1 text-xs text-gray-400">
                                {formatDateTimeIST(notification.createdAt)}
                              </div>
                            </div>
                          </div>
                          <div
                            className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-gray-300 text-white"
                            title="Acknowledged"
                          >
                            <svg
                              width="12"
                              height="12"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="3"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {showNotificationModal && selectedNotification && (
        <NotificationDetailModal
          notification={selectedNotification}
          onClose={() => {
            setShowNotificationModal(false);
            setSelectedNotification(null);
          }}
        />
      )}
    </div>
  );
}

function NotificationDetailModal({
  notification,
  onClose,
}: {
  notification: Notification;
  onClose: () => void;
}) {
  const [order, setOrder] = useState<Order | null>(null);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDetails();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notification]);

  const fetchDetails = async () => {
    try {
      setLoading(true);
      if (notification.type === 'new_order') {
        const response = await api.get(`/orders/${notification.data.orderId}`);
        setOrder(response.data);
      } else if (notification.type === 'new_payment') {
        const response = await api.get(`/payments/${notification.data.paymentId}`);
        setPayment(response.data);
      } else if (notification.type === 'low_stock') {
        const response = await api.get(`/products/${notification.data.productId}`);
        setProduct(response.data);
      }
    } catch (error: any) {
      logger.error('Error fetching details:', error);
      toast.error('Failed to load details');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptOrder = async () => {
    try {
      await api.put(`/orders/${order!._id}/accept`);
      toast.success('Order accepted');
      onClose();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to accept order');
    }
  };

  const handleDeclineOrder = async () => {
    const reason = prompt('Please enter reason for decline:');
    if (!reason) return;
    try {
      await api.put(`/orders/${order!._id}/decline`, { reason });
      toast.success('Order declined');
      onClose();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to decline order');
    }
  };

  const handleVerifyPayment = async (paymentId: string, entryId: number, verified: boolean) => {
    try {
      await api.put(`/payments/${paymentId}/verify-entry/${entryId}`, { verified });
      toast.success(`Payment ${verified ? 'verified' : 'unverified'}`);
      fetchDetails();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to update payment verification');
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onClose}
    >
      <div
        className="mx-4 max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between border-b pb-4">
          <h3 className="text-xl font-bold">{notification.title}</h3>
          <button onClick={onClose} className="text-2xl text-gray-600">
            ×
          </button>
        </div>
        <div>
          {loading ? (
            <div>Loading...</div>
          ) : notification.type === 'new_order' && order ? (
            <OrderDetails
              order={order}
              onAccept={handleAcceptOrder}
              onDecline={handleDeclineOrder}
            />
          ) : notification.type === 'new_payment' && payment ? (
            <PaymentDetails payment={payment} onVerify={handleVerifyPayment} />
          ) : notification.type === 'low_stock' && product ? (
            <ProductDetails product={product} notification={notification} />
          ) : (
            <div>{notification.message}</div>
          )}
        </div>
      </div>
    </div>
  );
}

function OrderDetails({
  order,
  onAccept,
  onDecline,
}: {
  order: Order;
  onAccept: () => void;
  onDecline: () => void;
}) {
  return (
    <div>
      <div className="mb-6">
        <h4 className="mb-3 text-lg font-semibold">Order Information</h4>
        <p>
          <strong>Order Number:</strong> {order.orderNumber || order._id}
        </p>
        <p>
          <strong>Customer:</strong> {order.user?.name || 'N/A'}
        </p>
        <p>
          <strong>Total Amount:</strong> ₹{order.total?.toFixed(2) || '0.00'}
        </p>
        <p>
          <strong>Payment Method:</strong> {order.paymentMethod?.toUpperCase() || 'N/A'}
        </p>
        <p>
          <strong>Status:</strong> {order.status || 'N/A'}
        </p>
        <p>
          <strong>Date:</strong> {formatDateTimeIST(order.createdAt)}
        </p>
      </div>
      <div className="mb-6">
        <h4 className="mb-3 text-lg font-semibold">Order Items</h4>
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="border p-2 text-left">Product</th>
              <th className="border p-2 text-left">Quantity</th>
              <th className="border p-2 text-left">Price</th>
              <th className="border p-2 text-left">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {order.items?.map((item, idx) => (
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
      {order.status === 'pending' && (
        <div className="flex gap-4 border-t pt-4">
          <button
            className="rounded bg-green-600 px-6 py-2 text-white hover:bg-green-700"
            onClick={onAccept}
          >
            Accept Order
          </button>
          {order.paymentMethod !== 'upi' && (
            <button
              className="rounded bg-red-600 px-6 py-2 text-white hover:bg-red-700"
              onClick={onDecline}
            >
              Decline Order
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function PaymentDetails({
  payment,
  onVerify,
}: {
  payment: Payment;
  onVerify: (paymentId: string, entryId: number, verified: boolean) => void;
}) {
  return (
    <div>
      <div className="mb-6">
        <h4 className="mb-3 text-lg font-semibold">Payment Information</h4>
        <p>
          <strong>Payment ID:</strong> {payment.paymentId || payment._id}
        </p>
        <p>
          <strong>Order ID:</strong> {payment.orderNumber || payment.orderId}
        </p>
        <p>
          <strong>Customer:</strong> {payment.customerName || 'N/A'}
        </p>
        <p>
          <strong>Total Amount:</strong> ₹{payment.totalAmount?.toFixed(2) || '0.00'}
        </p>
        <p>
          <strong>Amount Paid:</strong> ₹{payment.amountPaid?.toFixed(2) || '0.00'}
        </p>
        <p>
          <strong>Amount Remaining:</strong> ₹{payment.amountRemaining?.toFixed(2) || '0.00'}
        </p>
        <p>
          <strong>Payment Method:</strong> {payment.paymentMethod?.toUpperCase() || 'N/A'}
        </p>
      </div>
      {payment.paymentEntries && payment.paymentEntries.length > 0 && (
        <div className="mb-6">
          <h4 className="mb-3 text-lg font-semibold">Payment Entries</h4>
          {payment.paymentEntries.map((entry, idx) => (
            <div key={idx} className="mb-4 rounded-lg border bg-gray-50 p-4">
              <p>
                <strong>Entry {entry.entryId}:</strong> ₹{entry.amount?.toFixed(2) || '0.00'}
              </p>
              {entry.image && (
                <img src={entry.image} alt="Payment proof" className="mt-2 max-w-xs rounded" />
              )}
              <p>
                <strong>Verified:</strong> {entry.verified ? 'Yes' : 'No'}
              </p>
              <div className="mt-3 flex gap-2">
                <button
                  className="rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50"
                  onClick={() => onVerify(payment._id, entry.entryId, true)}
                  disabled={entry.verified}
                >
                  Verify Yes
                </button>
                <button
                  className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:opacity-50"
                  onClick={() => onVerify(payment._id, entry.entryId, false)}
                  disabled={!entry.verified}
                >
                  Verify No
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ProductDetails({
  product,
  notification,
}: {
  product: Product;
  notification: Notification;
}) {
  return (
    <div>
      <div className="mb-6">
        <h4 className="mb-3 text-lg font-semibold">Product Information</h4>
        <p>
          <strong>SKU:</strong> {product.sku || 'N/A'}
        </p>
        <p>
          <strong>Product Name:</strong> {product.name || 'N/A'}
        </p>
        <p>
          <strong>Current Quantity:</strong> {notification.data.quantity || product.stock || 0}
        </p>
        <p>
          <strong>Category:</strong> {product.category || 'N/A'}
        </p>
        <p>
          <strong>Threshold:</strong> {notification.data.threshold || 2000}
        </p>
      </div>
    </div>
  );
}
