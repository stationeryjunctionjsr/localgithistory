/**
 * Shared domain types used by both the web app and mobile app.
 * Import from '@sj/api-client' in either platform.
 */

// ── Auth ──────────────────────────────────────────────────────────────────────

export type UserRole = 'super_admin' | 'wholesaler' | 'customer' | 'valet';

export interface User {
  _id: string;
  name?: string | null;
  email?: string | null;
  phone?: string;
  role: UserRole;
  effectiveRole?: UserRole;
  companyName?: string;
  gstin?: string;
  locationLink?: string;
  approvalStatus?: string;
  address?: any;
  savedAddresses?: any[];
  creditLimit?: number;
  creditUsed?: number;
  logoUrl?: string;
  referralCode?: string;
}

// ── Cart ──────────────────────────────────────────────────────────────────────

export interface CartProduct {
  _id: string;
  name: string;
  price: number;
  mrp?: number;
  images?: string[];
  quantityPerCase?: number;
  mrpPerCase?: number;
  [key: string]: any;
}

export interface CartItem {
  _id: string;
  product: CartProduct;
  price: number;
  quantity: number;
  sellAsCase?: boolean;
}

export interface Cart {
  items: CartItem[];
  subtotal: number;
}

// ── Wishlist ──────────────────────────────────────────────────────────────────

export interface WishlistItem {
  _id: string;
  product: {
    _id: string;
    name: string;
    price: number;
    images: string[];
  };
  addedAt: string;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export type AnalyticsEventType =
  | 'session_start'
  | 'session_end'
  | 'page_view'
  | 'product_click'
  | 'product_view'
  | 'product_add'
  | 'search'
  | 'cart_remove'
  | 'category_click'
  | 'brand_click'
  | 'tag_click'
  | 'list_click'
  | 'add_to_wishlist'
  | 'remove_from_wishlist'
  | 'recommendation_product_click'
  | 'recommendation_add_to_cart';

export interface AnalyticsDeviceInfo {
  type?: string;
  os?: string;
  osVersion?: string;
  model?: string;
  appVersion?: string;
}

export interface AnalyticsEvent {
  type: AnalyticsEventType;
  page?: string;
  referrer?: string;
  sessionId?: string | null;
  userId?: string | null;
  device?: AnalyticsDeviceInfo;
  payload?: Record<string, any>;
  timestamp?: string;
  reason?: string;
}
