// Shared domain types — importable by both web and mobile
export type {
  User,
  UserRole,
  Cart,
  CartItem,
  CartProduct,
  WishlistItem,
  AnalyticsEventType,
  AnalyticsEvent,
  AnalyticsDeviceInfo,
} from './types';

import axios, {
  AxiosInstance,
  InternalAxiosRequestConfig,
  AxiosRequestHeaders,
  AxiosHeaders,
} from 'axios';

export interface ApiAdapter {
  getAccessToken: () => Promise<string | null> | string | null;
  getRefreshToken?: () => Promise<string | null> | string | null;
  getSessionId?: () => Promise<string | null> | string | null;
  clearTokens: () => Promise<void> | void;
  setTokens?: (data: {
    token: string;
    refreshToken?: string;
    sessionId?: string;
  }) => Promise<void> | void;
  onUnauthorized?: () => void;
  onSessionRevoked?: (detail: any) => void;
  getDeviceHeaders?: () => Promise<Record<string, string>> | Record<string, string>;
  getPincode?: () => Promise<string | null> | string | null;
}

let webSessionRevokedHandler: ((detail: any) => void) | null = null;
export const setSessionRevokedHandler = (handler: ((detail: any) => void) | null) => {
  webSessionRevokedHandler = handler;
};

export type CreateApiClientOptions = {
  /** ms; omit or 0 for axios default (no request timeout). */
  timeout?: number;
  withCredentials?: boolean;
};

export const createApiClient = (adapter: ApiAdapter, options?: CreateApiClientOptions): AxiosInstance => {
  const timeoutMs =
    typeof options?.timeout === 'number' && options.timeout > 0 ? options.timeout : undefined;
  const instance = axios.create({
    baseURL: typeof window !== 'undefined' ? '/api' : process.env.NEXT_PUBLIC_API_URL,
    headers: { 'Content-Type': 'application/json' },
    withCredentials: options?.withCredentials ?? true,
    ...(timeoutMs !== undefined ? { timeout: timeoutMs } : {}),
  });

  instance.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
    // Ensure trailing slash for root resource requests to avoid CORS-breaking redirects
    if (config.url) {
      const [path, query] = config.url.split('?');
      const normalizedPath = path.startsWith('/') ? path : '/' + path;
      const rootEndpoints = [
        '/products',
        '/coupons',
        '/collections',
        '/cart',
        '/wishlist',
        '/banners',
        '/brands',
        '/categories',
        '/category-tags',
        '/notifications',
        '/orders',
        '/support-tickets',
        '/users',
        '/payments',
        '/feature-flags',
        '/reviews',
        '/promo-strips',
        '/push-notifications',
        '/search-tags',
        '/analytics',
        '/activity',
        '/pincodes',
        '/customer-segments',
        '/referrals',
        '/returns',
        '/bundles',
        '/ads'
      ];
      if (rootEndpoints.includes(normalizedPath)) {
        config.url = path + '/' + (query ? '?' + query : '');
      }
    }

    const headers: AxiosRequestHeaders = (config.headers = config.headers
      ? new AxiosHeaders(config.headers)
      : new AxiosHeaders());

    const skipAccessToken = (config as any).skipAccessToken;
    if (!skipAccessToken) {
      const token = await Promise.resolve(adapter.getAccessToken());
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
    }

    // Device headers
    const deviceHeaders = (await Promise.resolve(adapter.getDeviceHeaders?.())) || {};
    Object.entries(deviceHeaders).forEach(([k, v]) => {
      headers[k] = v as any;
    });

    // Session Id passthrough (explicit or via adapter)
    const explicitSessionId = (config as any).sessionId;
    const adapterSessionId = adapter.getSessionId
      ? await Promise.resolve(adapter.getSessionId())
      : null;
    const finalSessionId = explicitSessionId || adapterSessionId;
    if (finalSessionId) {
      headers['X-Session-Id'] = finalSessionId as any;
    }

    // Pincode header and query passthrough (explicit or via adapter)
    const explicitPincode = (config as any).pincode || (config.params && config.params.pincode);
    const adapterPincode = adapter.getPincode
      ? await Promise.resolve(adapter.getPincode())
      : null;
    const finalPincode = explicitPincode || adapterPincode;
    if (finalPincode) {
      headers['X-Pincode'] = finalPincode as any;
      if (config.params && typeof config.params === 'object' && !config.params.pincode) {
        config.params.pincode = finalPincode;
      }
    }

    // For FormData, allow browser to set boundary
    if (config.data instanceof FormData) {
      delete headers['Content-Type'];
    }

    return config;
  });

  instance.interceptors.response.use(
    (response: any) => response,
    async (error: any) => {
      const status = error.response?.status;
      const detail = error.response?.data;
      if (status === 401 && detail?.code === 'SESSION_REVOKED') {
        await Promise.resolve(adapter.clearTokens());
        if (adapter.onSessionRevoked) adapter.onSessionRevoked(detail);
        if (webSessionRevokedHandler) webSessionRevokedHandler(detail);
        return Promise.reject(error);
      }
      if (status === 401) {
        const url = error.config?.url || '';
        const isRefreshRequest = url.includes('/auth/refresh');
        const isLoginRequest = url.includes('/auth/login');

        // If it's a login request, don't try to refresh or redirect; let the caller handle it.
        if (isLoginRequest) {
          return Promise.reject(error);
        }

        const refreshToken = adapter.getRefreshToken
          ? await Promise.resolve(adapter.getRefreshToken())
          : null;
        if (!isRefreshRequest && adapter.setTokens) {
          try {
            const refreshBaseURL =
              instance.defaults.baseURL ||
              process.env.NEXT_PUBLIC_API_URL ||
              '';
            const refreshUrl = refreshBaseURL
              ? (refreshBaseURL.endsWith('/') ? refreshBaseURL : refreshBaseURL + '/') +
                'auth/refresh'.replace(/^\//, '')
              : '/auth/refresh';
            const refreshTimeoutMs =
              typeof instance.defaults.timeout === 'number' && instance.defaults.timeout > 0
                ? instance.defaults.timeout
                : 60000;
            const res = await axios.post(refreshUrl, refreshToken ? { refreshToken } : {}, {
              headers: { 'Content-Type': 'application/json' },
              timeout: refreshTimeoutMs,
              withCredentials: instance.defaults.withCredentials ?? true,
            });
            const data = res.data;
            if (data?.token) {
              await Promise.resolve(
                adapter.setTokens({
                  token: data.token,
                  refreshToken: data.refreshToken,
                  sessionId: data.sessionId,
                })
              );
              if (error.config) {
                error.config.headers = error.config.headers || {};
                error.config.headers.Authorization = `Bearer ${data.token}`;
                return instance.request(error.config);
              }
            }
          } catch (_) {
            /* refresh failed, fall through to clear and redirect */
          }
        }
        await Promise.resolve(adapter.clearTokens());
        if (adapter.onUnauthorized) adapter.onUnauthorized();
      }
      return Promise.reject(error);
    }
  );

  return instance;
};

// Default web adapter
const webAdapter: ApiAdapter = {
  getAccessToken: () => null,
  getRefreshToken: () => null,
  getSessionId: () => {
    if (typeof window === 'undefined') {
      return null;
    }
    return window.localStorage.getItem('sessionId');
  },
  getPincode: () => {
    if (typeof window === 'undefined') {
      return null;
    }
    return window.localStorage.getItem('sj_user_pincode') || null;
  },
  clearTokens: () => {},
  setTokens: () => {},
  onUnauthorized: () => {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname;
      // Don't redirect away from cart — guest users need to stay here to sign in at checkout
      const noRedirectPaths = ['/', '/landingpage', '/login', '/customer/cart'];
      if (!noRedirectPaths.some((p) => path === p || path.startsWith(p + '?'))) {
        window.location.href = '/';
      }
    }
  },
  onSessionRevoked: (detail) => {
    if (webSessionRevokedHandler) webSessionRevokedHandler(detail);
  },
  getDeviceHeaders: () => {
    const appVersion = process.env.NEXT_PUBLIC_APP_VERSION || 'web';
    const os = typeof navigator !== 'undefined' ? navigator.platform : 'web';
    const osVersion = typeof navigator !== 'undefined' ? navigator.userAgent : '';
    return {
      'X-App-Version': appVersion,
      'X-Device-OS': os,
      'X-Device-OS-Version': osVersion,
      'X-Device-Type': 'web',
      'X-Device-Model': '',
    };
  },
};

const api = createApiClient(webAdapter);

export default api;
