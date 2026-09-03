import '../global.css';
import { Stack, useRouter, ErrorBoundaryProps } from 'expo-router';
import { ReanimatedLogLevel, configureReanimatedLogger } from 'react-native-reanimated';
import { SafeAreaProvider } from 'react-native-safe-area-context';

// Enable reanimated strict mode to ensure animations are optimized and render-safe.
configureReanimatedLogger({
  level: ReanimatedLogLevel.warn,
  strict: true,
});
import { useEffect, useRef } from 'react';
import { Platform, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { SessionRevokedModal } from '../src/components/SessionRevokedModal';
import ForceUpdateGate from '../src/components/ForceUpdateGate';
import MaintenanceGate from '../src/components/MaintenanceGate';
import { useAuth } from '../src/hooks/useAuth';
import SessionAnalytics from '../src/components/SessionAnalytics';
import api from '../src/api/client';
import Toast from 'react-native-toast-message';
import * as Linking from 'expo-linking';
import { storeDeepLinkAttribution } from '../src/utils/mobileAnalytics';

import { CoachMarkProvider } from '../src/context/CoachMarkContext';
import { PincodeProvider } from '../src/context/PincodeContext';
import { PincodeModal } from '../src/components/PincodeModal';
import { LanguageProvider } from '../src/context/LanguageContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache data for 5 minutes — navigating back shows instant content, not skeleton
      staleTime: 5 * 60 * 1000,
      // Keep unused data in cache for 10 minutes
      gcTime: 10 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
    },
  },
});

// Show alerts even when the app is foregrounded
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    // Expo SDK 54+ specific fields
    shouldShowBanner: true,
    shouldShowList: true,
    priority: Notifications.AndroidNotificationPriority.HIGH,
  }),
});

async function registerForPushNotifications() {
  if (!Device.isDevice) return; // skip simulators / emulators

  // Android: create the channel BEFORE requesting the token
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'General',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#1a4d33',
    });
  }

  const { status: existing } = await Notifications.getPermissionsAsync();
  const finalStatus =
    existing === 'granted'
      ? existing
      : (await Notifications.requestPermissionsAsync()).status;

  if (finalStatus !== 'granted') return;

  // projectId is required in SDK 49+; read from app config if available
  const projectId =
    Constants.expoConfig?.extra?.eas?.projectId ??
    Constants.easConfig?.projectId;

  try {
    const tokenData = projectId
      ? await Notifications.getExpoPushTokenAsync({ projectId })
      : await Notifications.getExpoPushTokenAsync();

    await api.post('/push-notifications/register-device', {
      expoToken: tokenData.data,
    });
  } catch {
    // non-critical — will retry on next launch
  }
}

/** Resolve a notification link to an in-app route or external URL. */
function resolveNotificationUrl(url?: string | null): string | null {
  if (!url) return '/notifications';
  // Internal routes start with '/'
  if (url.startsWith('/')) return url;
  // External URLs — return as-is for Linking
  return null;
}

// ─── Root error boundary ─────────────────────────────────────────────────────
// Expo Router 6 picks this up automatically from the root _layout.
// Shown whenever an unhandled error is thrown inside any screen.
export function ErrorBoundary({ error, retry }: ErrorBoundaryProps) {
  const { SafeAreaView } = require('react-native-safe-area-context');
  return (
    <SafeAreaView style={eb.container} edges={['top', 'bottom']}>
      <View style={eb.content}>
        <View style={eb.iconCircle}>
          <Text style={eb.iconText}>⚠️</Text>
        </View>
        <Text style={eb.title}>Something went wrong</Text>
        <Text style={eb.message}>
          Our team has been notified. You can try again or restart the app.
        </Text>
        {__DEV__ && error?.message ? (
          <View style={eb.devBox}>
            <Text style={eb.devText} numberOfLines={6}>
              {error.message}
            </Text>
          </View>
        ) : null}
        <TouchableOpacity style={eb.button} onPress={retry} activeOpacity={0.8}>
          <Text style={eb.buttonText}>Try again</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const eb = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32, gap: 12 },
  iconCircle: { width: 72, height: 72, borderRadius: 36, backgroundColor: '#FEE2E2', alignItems: 'center', justifyContent: 'center', marginBottom: 8 },
  iconText: { fontSize: 32 },
  title: { fontSize: 20, fontWeight: '700', color: '#111827', textAlign: 'center' },
  message: { fontSize: 14, color: '#6B7280', textAlign: 'center', lineHeight: 20 },
  devBox: { marginTop: 8, padding: 12, backgroundColor: '#FFF1F2', borderRadius: 10, borderWidth: 1, borderColor: '#FECACA', width: '100%' },
  devText: { fontSize: 12, color: '#DC2626', fontFamily: 'monospace' },
  button: { marginTop: 16, backgroundColor: '#2563EB', paddingHorizontal: 32, paddingVertical: 14, borderRadius: 12, minWidth: 160, alignItems: 'center' },
  buttonText: { color: '#FFF', fontSize: 15, fontWeight: '600' },
});
// ─────────────────────────────────────────────────────────────────────────────

export default function RootLayout() {
  const { sessionRevokedDetail, clearSessionRevoked, user, loading } = useAuth();
  const router = useRouter();
  const responseListenerRef = useRef<Notifications.Subscription | null>(null);

  useEffect(() => {
    // Defer push notification registration to keep startup lightweight and fast
    const notificationTimer = setTimeout(() => {
      registerForPushNotifications();
    }, 2000);

    // Capture UTM / gclid / fbclid attribution from the initial deep-link URL
    Linking.getInitialURL().then((url) => {
      if (url) storeDeepLinkAttribution(url);
    });
    const linkingSub = Linking.addEventListener('url', ({ url }) => {
      if (url) storeDeepLinkAttribution(url);
    });

    // Handle notification taps (app in background or killed state)
    responseListenerRef.current = Notifications.addNotificationResponseReceivedListener(
      (response) => {
        const data = response.notification.request.content.data as {
          url?: string;
          notificationId?: string;
        };
        const internalRoute = resolveNotificationUrl(data?.url);
        if (internalRoute) {
          // Navigate after a short delay so the navigator is fully mounted
          setTimeout(() => router.push(internalRoute as any), 300);
        }
      }
    );

    return () => {
      clearTimeout(notificationTimer);
      responseListenerRef.current?.remove();
      linkingSub.remove();
    };
  }, [router]);

  // Redirect valet users to their dedicated dashboard
  useEffect(() => {
    if (!loading && user && (user.role === 'valet' || (user as any).effectiveRole === 'valet')) {
      router.replace('/valet');
    }
  }, [user, loading, router]);


  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <SafeAreaProvider>
          <PincodeProvider>
            <CoachMarkProvider>
              <Stack screenOptions={{ headerShown: false }} />
              <PincodeModal />
              <MaintenanceGate />
              <ForceUpdateGate />
              <SessionAnalytics />
              <SessionRevokedModal
                detail={sessionRevokedDetail}
                onCancel={() => clearSessionRevoked()}
                onSignIn={() => clearSessionRevoked('login')}
              />
              <Toast />
            </CoachMarkProvider>
          </PincodeProvider>
        </SafeAreaProvider>
      </LanguageProvider>
    </QueryClientProvider>
  );
}
