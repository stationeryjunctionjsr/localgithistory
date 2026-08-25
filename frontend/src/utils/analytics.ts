/**
 * Unified Analytics Utility
 * Handles events for GTM DataLayer and Google Analytics GTag.
 */
import { trackRecommendationEventBackend } from '@/utils/recommendationTracking';
import api from '@/utils/api';
import Cookies from 'js-cookie';
import { logger } from '@/utils/logger';

export const GTM_ID = process.env.NEXT_PUBLIC_GTM_ID || '';
export const GA_ID = process.env.NEXT_PUBLIC_GA_ID || '';

// --- Backend Tracking Helpers ---

export const getSessionId = () => {
  if (typeof window !== 'undefined') {
    return (
      localStorage.getItem('sessionId') ||
      Cookies.get('sessionId') ||
      localStorage.getItem('guestSessionId') ||
      Cookies.get('guestSessionId') ||
      undefined
    );
  }
  return undefined;
};

export const trackBackendCartAdd = async (productId: string, quantity: number) => {
  try {
    await api.post('/tracking/cart-add', {
      productId,
      quantity,
      sessionId: getSessionId(),
    });
  } catch (e) {
    logger.error('Tracking error', e);
  }
};

export const trackBackendCartRemove = async (productId: string, quantity: number) => {
  try {
    await api.post('/tracking/cart-remove', {
      productId,
      quantity,
      sessionId: getSessionId(),
    });
  } catch (e) {
    logger.error('Tracking error', e);
  }
};

export const trackBackendProductClick = async (
  productId: string,
  productName: string,
  source: string
) => {
  try {
    await api.post('/tracking/click', {
      productId,
      productName,
      source,
      sessionId: getSessionId(),
    });
  } catch (e) {
    logger.error('Tracking error', e);
  }
};

export const trackBackendProductView = async (productId: string, productName: string) => {
  try {
    await api.post('/tracking/view', {
      productId,
      productName,
      sessionId: getSessionId(),
    });
  } catch (e) {
    logger.error('Tracking error', e);
  }
};

export const trackBackendFilterClick = async (filterType: string, filterValue: string) => {
  try {
    await api.post('/tracking/filter-click', {
      filterType,
      filterValue,
      sessionId: getSessionId(),
    });
  } catch (e) {
    logger.error('Tracking error', e);
  }
};

// --------------------------------

// Add GTM to window object
declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
  }
}

/**
 * Push an event to GTM DataLayer
 */
export const pushToDataLayer = (event: string, data: Record<string, any> = {}) => {
  if (typeof window !== 'undefined' && window.dataLayer) {
    window.dataLayer.push({
      event,
      ...data,
    });
  }
};

/**
 * Backward compatible recordEvent for existing code
 */
export const recordEvent = ({
  type,
  page,
  payload,
}: {
  type: string;
  page?: string;
  payload?: any;
}) => {
  pushToDataLayer(type, {
    page: page || (typeof window !== 'undefined' ? window.location.pathname : ''),
    ...payload,
  });
};

/**
 * Track an E-commerce event
 * Supports both GA4 GTag and GTM DataLayer conventions
 */
export const trackEcommerceEvent = (
  event: 'view_item' | 'add_to_cart' | 'purchase' | 'begin_checkout' | 'view_item_list',
  data: any
) => {
  if (typeof window === 'undefined') return;

  // Standardize the event for DataLayer
  const payload = {
    event,
    ecommerce: {
      currency: 'INR',
      value: data.value || 0,
      items: data.items || [],
    },
  };

  // Push to GTM
  pushToDataLayer(event, payload);

  // Push to GA4 Directly if gtag is available
  if (window.gtag) {
    window.gtag('event', event, data);
  }
};

/**
 * Track Page View
 */
export const trackPageView = (url: string) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('config', GA_ID, {
      page_path: url,
    });
  }
};

/**
 * Record a Beacon (Reliable tracking on tab close)
 */
export const recordBeacon = (data: Record<string, any>) => {
  if (typeof window !== 'undefined' && typeof navigator !== 'undefined') {
    const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
    navigator.sendBeacon(
      `${process.env.NEXT_PUBLIC_API_URL}/tracking/beacon`,
      blob
    );
    // Also push to DataLayer for GTM consistency
    pushToDataLayer('beacon_event', data);
  }
};

/**
 * Track Frontend Errors (Critical)
 */
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
      sessionId: getSessionId(),
    });
  } catch (e) {
    // Fail silently to avoid infinite error loops
    logger.error('Error reporting failed', e);
  }
};

/** Source page/context when adding or removing from wishlist */
export type WishlistSource =
  | 'catalog'
  | 'product_detail'
  | 'cart'
  | 'wishlist_page'
  | 'product_card';

/**
 * Track add to wishlist with source (page/context where the action happened)
 */
export const trackAddToWishlist = (payload: {
  productId: string;
  productName?: string;
  source: WishlistSource;
}) => {
  recordEvent({
    type: 'add_to_wishlist',
    payload: {
      productId: payload.productId,
      productName: payload.productName,
      source: payload.source,
    },
  });
};

/**
 * Track remove from wishlist with source
 */
export const trackRemoveFromWishlist = (payload: {
  productId: string;
  productName?: string;
  source: WishlistSource;
}) => {
  recordEvent({
    type: 'remove_from_wishlist',
    payload: {
      productId: payload.productId,
      productName: payload.productName,
      source: payload.source,
    },
  });
};

/**
 * Section/slot where the product was shown (e.g. cart sections).
 * Valid recommendation slots will be defined later; use string for now.
 */
export type RecommendationSlot = string;

/**
 * Track when the user reaches the recommendation section (e.g. scrolls it into view).
 * Backend stores this so you can measure: section views vs product clicks vs add-to-cart.
 */
export const trackRecommendationSectionView = (recommendationSlot: RecommendationSlot) => {
  recordEvent({
    type: 'recommendation_section_view',
    payload: { recommendationSlot },
  });
  trackRecommendationEventBackend('section_view', { slot: recommendationSlot }).catch((e) => logger.warn("Background task failed", e));
};

/**
 * Track product view/click from a recommendation/section block.
 * strategy: use when product came from GET /recommendations (for Multi-Armed Bandit reward).
 */
export const trackRecommendationProductClick = (payload: {
  productId: string;
  productName?: string;
  recommendationSlot: RecommendationSlot;
  strategy?: string;
}) => {
  recordEvent({
    type: 'recommendation_product_click',
    payload: {
      productId: payload.productId,
      productName: payload.productName,
      recommendationSlot: payload.recommendationSlot,
      strategy: payload.strategy,
    },
  });
  trackRecommendationEventBackend('product_view', {
    slot: payload.recommendationSlot,
    productId: payload.productId,
    productName: payload.productName,
    strategy: payload.strategy as 'trending' | 'user_favorites' | 'explore' | undefined,
  }).catch((e) => logger.warn("Background task failed", e));
};

/**
 * Track add to cart from a recommendation/section block.
 * strategy: use when product came from GET /recommendations (for Multi-Armed Bandit reward).
 */
export const trackRecommendationAddToCart = (payload: {
  productId: string;
  productName?: string;
  recommendationSlot: RecommendationSlot;
  strategy?: string;
}) => {
  recordEvent({
    type: 'recommendation_add_to_cart',
    payload: {
      productId: payload.productId,
      productName: payload.productName,
      recommendationSlot: payload.recommendationSlot,
      strategy: payload.strategy,
    },
  });
  // Also send GA4 add_to_cart with section context
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'add_to_cart', {
      ...payload,
      recommendation_slot: payload.recommendationSlot,
    });
  }
  trackRecommendationEventBackend('add_to_cart', {
    slot: payload.recommendationSlot,
    productId: payload.productId,
    productName: payload.productName,
    strategy: payload.strategy as 'trending' | 'user_favorites' | 'explore' | undefined,
  }).catch((e) => logger.warn("Background task failed", e));
};

// --- Ad Management Tracking ---

export const trackWebAdClick = async (adId: string, url: string, platform: string) => {
  try {
    recordEvent({
      type: 'ad_click',
      payload: { adId, platform, url },
    });
    await api.post('/ads/events/record', {
      ad_id: adId,
      event_type: 'click',
      platform,
      session_id: getSessionId(),
    });
  } catch (e) {
    logger.error('Failed to track ad click', e);
  }
};

export const trackWebAdConversion = async (
  adId: string,
  platform: string,
  value: number,
  currency = 'INR'
) => {
  try {
    recordEvent({
      type: 'ad_conversion',
      payload: { adId, platform, value, currency },
    });
    await api.post('/ads/events/record', {
      ad_id: adId,
      event_type: 'purchase',
      platform,
      value,
      currency,
      session_id: getSessionId(),
    });
  } catch (e) {
    logger.error('Failed to track ad conversion', e);
  }
};
