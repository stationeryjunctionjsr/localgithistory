/**
 * Recommendation engagement tracking for the backend.
 * Events are stored in activities so you can measure:
 * - Section views (did users see the recommendation block?)
 * - Product views (did they click a recommended product?)
 * - Add to cart (did they add a recommended product?)
 * Use this to tune the recommendation algorithm.
 */
import api from '@/utils/api';
import Cookies from 'js-cookie';
import { logger } from '@/utils/logger';

const RECOMMENDATION_SLOT = 'home_recommendations';

export type RecommendationEventType = 'section_view' | 'product_view' | 'add_to_cart';

/** Strategy (arm) for Multi-Armed Bandit: trending | user_favorites | explore */
export type RecommendationStrategy = 'trending' | 'user_favorites' | 'explore';

export interface RecommendationEventMeta {
  slot: string;
  productId?: string;
  productName?: string;
  /** Set when product came from GET /recommendations (for bandit reward update) */
  strategy?: RecommendationStrategy;
}

export async function trackRecommendationEventBackend(
  eventType: RecommendationEventType,
  meta: RecommendationEventMeta
) {
  const sessionId =
    (typeof window !== 'undefined' ? localStorage.getItem('sessionId') : null) ||
    Cookies.get('sessionId');
  if (!sessionId) return;
  try {
    const body: Record<string, unknown> = {
      eventType,
      slot: meta.slot,
      productId: meta.productId,
      productName: meta.productName,
    };
    if (meta.strategy) body.strategy = meta.strategy;
    await api.post('/recommendations/events', body, {
      headers: { 'X-Session-Id': sessionId },
    });
  } catch (e) { logger.warn("Silent catch block:", e); /* Non-blocking; avoid breaking UX */ }
}

export const DEFAULT_RECOMMENDATION_SLOT = RECOMMENDATION_SLOT;
