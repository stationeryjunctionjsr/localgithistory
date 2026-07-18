/**
 * mobileAnalytics.ts
 *
 * Mirrors the GTM/GA4/Meta-pixel events that run on web, for the Expo mobile app.
 * Since native apps cannot run browser scripts, we:
 *   1. Send structured events to our own backend (/analytics/events) which feeds GA4
 *      via Measurement Protocol when NEXT_PUBLIC_GA_ID + GA4_API_SECRET are set.
 *   2. Optionally forward purchase/lead events to Meta CAPI (server-side pixel).
 *   3. Track ad-click attribution via UTM params stored on deep-link open.
 */

import { Platform } from 'react-native';
import * as Device from 'expo-device';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../api/client';

// ── Types ─────────────────────────────────────────────────────────────────────

export type MobileEventType =
  | 'session_start'
  | 'session_end'
  | 'page_view'
  | 'product_view'
  | 'product_click'
  | 'add_to_cart'
  | 'remove_from_cart'
  | 'begin_checkout'
  | 'purchase'
  | 'search'
  | 'login'
  | 'sign_up'
  | 'share'
  | 'add_to_wishlist'
  | 'ad_impression'
  | 'ad_click'
  | 'ad_conversion';

export interface MobileAnalyticsEvent {
  type: MobileEventType;
  page?: string;
  sessionId?: string | null;
  userId?: string | null;
  payload?: Record<string, any>;
  timestamp?: string;
  /** UTM attribution stored from last deep-link open */
  attribution?: AttributionData | null;
}

export interface AttributionData {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  gclid?: string;   // Google click ID
  fbclid?: string;  // Meta click ID
  ad_id?: string;   // Our internal ad ID
}

// ── Attribution store (persisted) ────────────────────────────────────────────

const ATTRIBUTION_KEY = '@sj_attribution';

/**
 * Call this from _layout.tsx when the app opens via a deep link.
 * Parses UTM / gclid / fbclid / ad_id from the URL query string.
 */
export async function storeDeepLinkAttribution(url: string): Promise<void> {
  try {
    const urlObj = new URL(url);
    const params = urlObj.searchParams;
    const data: AttributionData = {};
    if (params.get('utm_source')) data.utm_source = params.get('utm_source')!;
    if (params.get('utm_medium')) data.utm_medium = params.get('utm_medium')!;
    if (params.get('utm_campaign')) data.utm_campaign = params.get('utm_campaign')!;
    if (params.get('utm_content')) data.utm_content = params.get('utm_content')!;
    if (params.get('utm_term')) data.utm_term = params.get('utm_term')!;
    if (params.get('gclid')) data.gclid = params.get('gclid')!;
    if (params.get('fbclid')) data.fbclid = params.get('fbclid')!;
    if (params.get('ad_id')) data.ad_id = params.get('ad_id')!;

    if (Object.keys(data).length > 0) {
      await AsyncStorage.setItem(ATTRIBUTION_KEY, JSON.stringify(data));
    }
  } catch {
    // Non-critical
  }
}

export async function getStoredAttribution(): Promise<AttributionData | null> {
  try {
    const raw = await AsyncStorage.getItem(ATTRIBUTION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export async function clearAttribution(): Promise<void> {
  try {
    await AsyncStorage.removeItem(ATTRIBUTION_KEY);
  } catch {}
}

// ── Device info ───────────────────────────────────────────────────────────────

const getDevice = () => ({
  type: 'app',
  os: Device.osName || Platform.OS,
  osVersion: Device.osVersion?.toString() || '',
  model: Device.modelName || '',
  appVersion: Device.osBuildId || 'mobile',
});

// ── Core event sender ─────────────────────────────────────────────────────────

/**
 * Send a structured analytics event to the backend.
 * The backend GA4 Measurement Protocol integration will forward this to GA4.
 */
export async function trackEvent(event: MobileAnalyticsEvent): Promise<void> {
  try {
    const attribution = event.attribution !== undefined
      ? event.attribution
      : await getStoredAttribution();

    const payload = {
      ...event,
      device: getDevice(),
      attribution,
      timestamp: event.timestamp || new Date().toISOString(),
    };

    await api.post('/analytics/events', payload);
  } catch {
    // Analytics failures are non-critical; silently ignore
  }
}

// ── Convenience wrappers (mirrors web GTM dataLayer pushes) ──────────────────

export const trackPageView = (page: string, sessionId?: string | null) =>
  trackEvent({ type: 'page_view', page, sessionId });

export const trackProductView = (
  productId: string,
  productName: string,
  price?: number,
  sessionId?: string | null
) =>
  trackEvent({
    type: 'product_view',
    sessionId,
    payload: { productId, productName, price },
  });

export const trackAddToCart = (
  productId: string,
  productName: string,
  quantity: number,
  price: number,
  sessionId?: string | null
) =>
  trackEvent({
    type: 'add_to_cart',
    sessionId,
    payload: { productId, productName, quantity, price, value: quantity * price },
  });

export const trackPurchase = (
  orderId: string,
  value: number,
  currency = 'INR',
  items: Array<{ productId: string; productName: string; quantity: number; price: number }>,
  sessionId?: string | null
) =>
  trackEvent({
    type: 'purchase',
    sessionId,
    payload: { orderId, value, currency, items },
  });

export const trackSearch = (query: string, resultsCount: number, sessionId?: string | null) =>
  trackEvent({ type: 'search', sessionId, payload: { query, resultsCount } });

export const trackLogin = (method: string, userId?: string) =>
  trackEvent({ type: 'login', userId, payload: { method } });

export const trackSignUp = (method: string, userId?: string) =>
  trackEvent({ type: 'sign_up', userId, payload: { method } });

export const trackAddToWishlist = (productId: string, productName: string, sessionId?: string | null) =>
  trackEvent({ type: 'add_to_wishlist', sessionId, payload: { productId, productName } });

/** Record that a paid-ad deep link was clicked (stores attribution + fires event) */
export const trackAdClick = async (adId: string, url: string, platform: string) => {
  await storeDeepLinkAttribution(url);
  await trackEvent({
    type: 'ad_click',
    payload: { adId, platform, url },
  });
  // Also record against the ad in our ads system
  try {
    await api.post('/ads/events/record', {
      ad_id: adId,
      event_type: 'click',
      platform,
    });
  } catch {}
};

export const trackAdConversion = async (
  adId: string,
  platform: string,
  value: number,
  currency = 'INR'
) => {
  await trackEvent({
    type: 'ad_conversion',
    payload: { adId, platform, value, currency },
  });
  try {
    await api.post('/ads/events/record', {
      ad_id: adId,
      event_type: 'purchase',
      platform,
      value,
      currency,
    });
  } catch {}
};
