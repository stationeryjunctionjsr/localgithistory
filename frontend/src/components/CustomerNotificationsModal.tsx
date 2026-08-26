import React, { useEffect, useState } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface Notification {
  _id: string;
  title: string;
  body: string;
  type: string;
  isRead: boolean;
  createdAt: string;
  data?: {
    url?: string;
  };
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onUnreadCountChange?: (count: number) => void;
}

const getIconForType = (type: string) => {
  switch (type) {
    case 'order': return '📦';
    case 'promo': return '🏷️';
    case 'system': return '⚙️';
    default: return '🔔';
  }
};

const formatTimeAgo = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 172800) return 'Yesterday';
  return `${Math.floor(diffInSeconds / 86400)}d ago`;
};

export const CustomerNotificationsModal: React.FC<Props> = ({ isOpen, onClose, onUnreadCountChange }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await api.get('/push-notifications/inbox');
      const data = res.data || [];
      setNotifications(data);
      updateUnreadCount(data);
    } catch (err) {
      logger.error('Error fetching notifications:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const updateUnreadCount = (notifs: Notification[]) => {
    if (onUnreadCountChange) {
      const count = notifs.filter(n => !n.isRead).length;
      onUnreadCountChange(count);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  const handleMarkAsRead = async (id: string) => {
    try {
      await api.put(`/push-notifications/${id}/read`);
      const updated = notifications.map(n => n._id === id ? { ...n, isRead: true } : n);
      setNotifications(updated);
      updateUnreadCount(updated);
    } catch (err) {
      logger.error('Error marking as read:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await api.post('/push-notifications/read-all');
      const updated = notifications.map(n => ({ ...n, isRead: true }));
      setNotifications(updated);
      updateUnreadCount(updated);
    } catch (err) {
      logger.error('Error marking all as read:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center z-[3000] bg-black bg-opacity-50 transition-opacity duration-300"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl w-full max-w-[420px] max-h-[80vh] flex flex-col overflow-hidden m-4"
        onClick={e => e.stopPropagation()}
        style={{ animation: 'fadeIn 0.3s ease-out' }}
      >
        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
          }
          .skeleton-pulse {
            animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
          }
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: .5; }
          }
        `}</style>
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-gray-800">Notifications</h2>
            {notifications.filter(n => !n.isRead).length > 0 && (
              <span className="bg-[#1a4d33] text-white text-xs font-bold px-2 py-0.5 rounded-full">
                {notifications.filter(n => !n.isRead).length}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {notifications.length > 0 && notifications.some(n => !n.isRead) && (
              <button 
                onClick={handleMarkAllAsRead}
                className="text-sm text-[#1a4d33] hover:underline font-medium"
              >
                Mark all as read
              </button>
            )}
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700 p-1">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-0">
          {loading ? (
            <div className="p-4 space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex gap-3">
                  <div className="w-8 h-8 bg-gray-200 rounded-full skeleton-pulse"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4 skeleton-pulse"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2 skeleton-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center p-8 text-center h-48">
              <p className="text-gray-500 mb-4">Failed to load notifications</p>
              <button 
                onClick={fetchNotifications}
                className="px-4 py-2 bg-[#1a4d33] text-white rounded hover:bg-opacity-90"
              >
                Retry
              </button>
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-center h-48 text-gray-500">
              <span className="text-4xl mb-3">🔔</span>
              <p>You&apos;re all caught up!</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {notifications.map(notification => (
                <div 
                  key={notification._id}
                  onClick={() => {
                    if (!notification.isRead) handleMarkAsRead(notification._id);
                    if (notification.data?.url) {
                      window.location.href = notification.data.url;
                    }
                  }}
                  className={`flex gap-3 p-4 cursor-pointer hover:bg-gray-50 transition-colors ${!notification.isRead ? 'bg-blue-50/30' : ''}`}
                >
                  <div className="mt-1 flex items-center justify-center w-2 h-2 rounded-full">
                    <div className={`w-2 h-2 rounded-full ${notification.isRead ? 'bg-gray-300' : 'bg-green-500'}`}></div>
                  </div>
                  <div className="text-xl leading-none pt-1">
                    {getIconForType(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm ${notification.isRead ? 'font-medium text-gray-700' : 'font-bold text-gray-900'}`}>
                      {notification.title}
                    </div>
                    <div className="text-sm text-gray-500 mt-0.5 line-clamp-2">
                      {notification.body}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {formatTimeAgo(notification.createdAt)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CustomerNotificationsModal;
