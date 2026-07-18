'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';

interface Notification {
  _id: string;
  title: string;
  message: string;
  read: boolean;
  showBrowserNotification?: boolean;
  icon?: string;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  permissionGranted: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  showNotification: (
    title: string,
    message: string,
    type?: 'success' | 'error' | 'warning' | 'info',
    options?: { showBrowser?: boolean; icon?: string }
  ) => void;
  requestNotificationPermission: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [permissionGranted, setPermissionGranted] = useState(false);

  useEffect(() => {
    if (user) {
      fetchNotifications();
      requestNotificationPermission();
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setPermissionGranted(permission === 'granted');
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await api.get('/notifications/');
      const allNotifications = response.data || [];
      setNotifications(allNotifications);
      setUnreadCount(allNotifications.filter((n: Notification) => !n.read).length);

      allNotifications
        .filter((n: Notification) => !n.read && n.showBrowserNotification)
        .forEach((notification: Notification) => {
          if (permissionGranted) {
            new Notification(notification.title, {
              body: notification.message,
              tag: notification._id,
              icon: notification.icon,
            });
          }
        });
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await api.put(`/notifications/${notificationId}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n._id === notificationId ? { ...n, read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.put('/notifications/read-all/');
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const showNotification = (
    title: string,
    message: string,
    type: 'success' | 'error' | 'warning' | 'info' = 'info',
    options?: { showBrowser?: boolean; icon?: string }
  ) => {
    if (type === 'success') {
      toast.success(message);
    } else if (type === 'error') {
      toast.error(message);
    } else if (type === 'warning') {
      toast.warning(message);
    } else {
      toast.info(message);
    }

    if (permissionGranted && options?.showBrowser) {
      new Notification(title, {
        body: message,
        icon: options.icon,
      });
    }
  };

  const value: NotificationContextType = {
    notifications,
    unreadCount,
    permissionGranted,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    showNotification,
    requestNotificationPermission,
  };

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
};
