import api, { SESSION_KEY } from '../api/client';
import { Platform } from 'react-native';
import * as Device from 'expo-device';
import * as SecureStore from 'expo-secure-store';
import type { AnalyticsEventType, AnalyticsEvent } from '@sj/api-client';

// Re-export so existing imports of these types from this file keep working
export type { AnalyticsEventType, AnalyticsEvent };


const getDeviceData = () => {
  return {
    os: Device.osName || Platform.OS,
    browser: 'MobileApp',
    campaign: undefined, // Campaign attribution usually handled via deep links in mobile
  };
};

const buildDevice = () => {
  return {
    type: 'app',
    os: Device.osName || Platform.OS,
    osVersion: Device.osVersion?.toString() || '',
    model: Device.modelName || '',
    appVersion: Device.osBuildId || 'mobile',
  };
};

export const recordEvent = async (event: AnalyticsEvent) => {
  try {
    const payload: AnalyticsEvent = {
      ...event,
      device: event.device || buildDevice(),
      ...getDeviceData(),
    };
    await api.post('/analytics/events', payload);
  } catch (e: any) { console.warn("Background task failed", e); }
};

export const trackError = async (error: {
  message: string;
  stack?: string;
  url?: string;
  line?: number;
  col?: number;
}) => {
  try {
    await api.post('/tracking/error', {
      ...error,
      // sessionId management might be different on mobile, but for now we look in SecureStore if needed
      // but let's just send the message for now
    });
  } catch (e: any) { console.warn("Background task failed", e); }
};

export interface RecommendationEventPayload {
  eventType: 'section_view' | 'product_view' | 'add_to_cart';
  slot: string;
  productId?: string;
  productName?: string;
  strategy?: string;
}

export const trackRecommendationEvent = async (payload: RecommendationEventPayload) => {
  try {
    const sessionId = await SecureStore.getItemAsync(SESSION_KEY);
    if (!sessionId) return;
    await api.post('/recommendations/events', payload, {
      headers: { 'X-Session-Id': sessionId },
    });
  } catch (err) {
    if (__DEV__) {
      console.warn('Failed to track recommendation event:', err);
    }
  }
};

