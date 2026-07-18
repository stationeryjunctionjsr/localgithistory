import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import api from '../api/client';

// Configure how notifications are displayed when the app is in the foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

/**
 * Registers the device with the backend using an Expo Push Token.
 * This should be called after the user logs in (or on app startup if already logged in).
 */
export async function registerExpoPushToken(): Promise<void> {
  try {
    // Push tokens only work on physical devices
    if (!Device.isDevice) {
      if (__DEV__) console.log('[PushNotifications] Skipping: must run on a physical device');
      return;
    }

    // Request permissions
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      if (__DEV__) console.log('[PushNotifications] Permission not granted');
      return;
    }

    // Android requires a notification channel
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'Default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#1a4d33',
        sound: 'default',
      });
    }

    // Get the Expo push token
    const tokenData = await Notifications.getExpoPushTokenAsync();
    const expoToken = tokenData.data;
    if (__DEV__) console.log('[PushNotifications] Expo Push Token:', expoToken);

    // Register the token with our backend
    await api.post('/push-notifications/register-device', {
      expoToken,
    });

    if (__DEV__) console.log('[PushNotifications] Device registered successfully');
  } catch (error) {
    if (__DEV__) console.error('[PushNotifications] Registration failed:', error);
  }
}

/**
 * Add a listener for notifications received while the app is in the foreground.
 * Returns the subscription (call .remove() to clean up).
 */
export function addForegroundNotificationListener(
  handler: (notification: Notifications.Notification) => void
) {
  return Notifications.addNotificationReceivedListener(handler);
}

/**
 * Add a listener for when the user taps a notification (foreground or background).
 * Returns the subscription (call .remove() to clean up).
 */
export function addNotificationResponseListener(
  handler: (response: Notifications.NotificationResponse) => void
) {
  return Notifications.addNotificationResponseReceivedListener(handler);
}
