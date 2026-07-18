// Push Notifications Utility for Next.js
import api from './api';

class PushNotificationService {
  private permission: NotificationPermission | null = null;
  private registration: ServiceWorkerRegistration | null = null;
  private subscription: PushSubscription | null = null;

  constructor() {
    this.init();
  }

  async init() {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      try {
        // Register service worker
        // eslint-disable-next-line unused-imports/no-unused-vars
        const registration = await navigator.serviceWorker.register('/service-worker.js');
        this.registration = await navigator.serviceWorker.ready;

        // Request notification permission
        this.permission = await Notification.requestPermission();

        // If permission granted, subscribe to push notifications
        if (this.permission === 'granted') {
          await this.subscribeToPush();
        }
      } catch (error) {
        console.error('Push notification initialization failed:', error);
      }
    }
  }

  async subscribeToPush() {
    try {
      if (!this.registration) {
        console.warn('Service worker not ready');
        return;
      }

      // Get VAPID public key from server
      const response = await api.get('/push-notifications/vapid-public-key');
      const vapidPublicKey = response.data.publicKey;

      if (!vapidPublicKey) {
        console.warn('VAPID public key not available');
        return;
      }

      // Convert VAPID key to Uint8Array
      const applicationServerKey = this.urlBase64ToUint8Array(vapidPublicKey);

      // Subscribe to push notifications
      this.subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey as any,
      });

      // Register device with backend
      await this.registerDevice(this.subscription);
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
    }
  }

  async registerDevice(subscription: PushSubscription) {
    try {
      // Get subscription object in the format expected by backend
      const p256dhKey = subscription.getKey('p256dh');
      const authKey = subscription.getKey('auth');

      const subscriptionData = {
        endpoint: subscription.endpoint,
        keys: {
          p256dh: p256dhKey ? this.arrayBufferToBase64(p256dhKey) : '',
          auth: authKey ? this.arrayBufferToBase64(authKey) : '',
        },
      };

      // Register device (userId will be extracted from token on backend if authenticated)
      await api.post('/push-notifications/register-device', {
        subscription: subscriptionData,
      });
    } catch (error) {
      console.error('Failed to register device:', error);
    }
  }

  urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  async requestPermission() {
    if (!('Notification' in window)) {
      return { granted: false, error: 'Notifications not supported' };
    }

    if (this.permission === 'granted') {
      // If already granted, ensure subscription
      if (!this.subscription) {
        await this.subscribeToPush();
      }
      return { granted: true };
    }

    this.permission = await Notification.requestPermission();

    if (this.permission === 'granted') {
      await this.subscribeToPush();
    }

    return { granted: this.permission === 'granted' };
  }

  showNotification(title: string, options: NotificationOptions = {}) {
    if (this.permission !== 'granted') {
      console.warn('Notification permission not granted');
      return;
    }

    const notificationOptions: NotificationOptions = {
      body: options.body || '',
      icon: options.icon || '/favicon.svg',
      badge: options.badge || '/favicon.svg',
      tag: options.tag || 'default',
      requireInteraction: options.requireInteraction || false,
      silent: options.silent || false,
      ...options,
    };

    if (this.registration) {
      this.registration.showNotification(title, notificationOptions);
    } else {
      new Notification(title, notificationOptions);
    }
  }
}

// Create singleton instance
const pushNotificationService = new PushNotificationService();

export default pushNotificationService;
