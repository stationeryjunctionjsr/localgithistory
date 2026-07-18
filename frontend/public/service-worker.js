// Service Worker for Push Notifications (Next.js)
const CACHE_NAME = 'stationery-junction-v1';

// Install event - cache resources
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event);

  let notificationData = {
    title: 'New Notification',
    body: 'You have a new notification',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: 'default',
    data: {},
  };

  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = {
        title: data.title || notificationData.title,
        body: data.message || data.body || notificationData.body,
        icon: data.image || data.icon || notificationData.icon,
        badge: data.badge || notificationData.badge,
        tag: data.tag || data.notificationId || notificationData.tag,
        data: {
          link: data.link,
          notificationId: data.notificationId || data._id,
        },
      };
    } catch (e) {
      console.error('Error parsing push data:', e);
      notificationData.body = event.data.text() || notificationData.body;
    }
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      tag: notificationData.tag,
      data: notificationData.data,
      requireInteraction: false,
      silent: false,
    })
  );
});

// Notification click event - handle user clicking on notification
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);

  event.notification.close();

  const notificationData = event.notification.data || {};
  const link = notificationData.link;

  // Mark notification as read
  if (notificationData.notificationId) {
    fetch(`/api/push-notifications/${notificationData.notificationId}/mark-read`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }).catch((err) => console.error('Failed to mark notification as read:', err));
  }

  // Navigate to link if provided
  if (link) {
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
        // Check if there's already a window/tab open with the target URL
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (client.url === link && 'focus' in client) {
            return client.focus();
          }
        }

        // If no matching window, open a new one
        if (clients.openWindow) {
          // Handle relative and absolute URLs
          const url = link.startsWith('http')
            ? link
            : `${self.location.origin}${link.startsWith('/') ? link : '/' + link}`;
          return clients.openWindow(url);
        }
      })
    );
  }
});

// Message event - handle messages from the main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker received message:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
