import { createApiClient, ApiAdapter } from '@sj/api-client';
import * as SecureStore from 'expo-secure-store';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

const TOKEN_KEY = 'token';
const REFRESH_KEY = 'refreshToken';
const SESSION_KEY = 'sessionId';

export async function storeTokens(tokens: {
  token?: string | null;
  refreshToken?: string | null;
  sessionId?: string | null;
}) {
  if (tokens.token) await SecureStore.setItemAsync(TOKEN_KEY, tokens.token);
  if (tokens.refreshToken) await SecureStore.setItemAsync(REFRESH_KEY, tokens.refreshToken);
  if (tokens.sessionId) await SecureStore.setItemAsync(SESSION_KEY, tokens.sessionId);
}

const mobileApiTimeoutMs = (() => {
  const raw = process.env.EXPO_PUBLIC_API_TIMEOUT_MS;
  if (raw !== undefined && raw !== '') {
    const n = Number(raw);
    if (Number.isFinite(n) && n > 0) return n;
  }
  // Keep failures fast enough for UX; can be overridden in env when needed.
  return 30_000;
})();

const mobileAdapter: ApiAdapter = {
  getAccessToken: async () => {
    return (await SecureStore.getItemAsync(TOKEN_KEY)) || null;
  },
  getSessionId: async () => {
    return (await SecureStore.getItemAsync(SESSION_KEY)) || null;
  },
  clearTokens: async () => {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_KEY);
    await SecureStore.deleteItemAsync(SESSION_KEY);
  },
  getRefreshToken: async () => {
    return (await SecureStore.getItemAsync(REFRESH_KEY)) || null;
  },
  setTokens: async (data: { token: string; refreshToken?: string; sessionId?: string }) => {
    if (data.token) await SecureStore.setItemAsync(TOKEN_KEY, data.token);
    if (data.refreshToken) await SecureStore.setItemAsync(REFRESH_KEY, data.refreshToken);
    if (data.sessionId) await SecureStore.setItemAsync(SESSION_KEY, data.sessionId);
  },
  onUnauthorized: () => {
    // Clear user state in store when unauthorized and refresh fails
    // Note: redirect is typically handled by components reacting to user === null
    const { useAuthStore } = require('../store/authStore');
    useAuthStore.getState().setUser(null);
  },
  getDeviceHeaders: () => {
    const appVersion = Constants.expoConfig?.version || Constants.manifest?.version || 'mobile';
    const os = Device.osName || 'mobile';
    const osVersion = Device.osVersion?.toString() || '';
    const model = Device.modelName || '';
    return {
      'X-App-Version': appVersion,
      'X-Device-OS': os,
      'X-Device-OS-Version': osVersion,
      'X-Device-Type': 'app',
      'X-Device-Model': model,
    };
  },
};

// RN uses Bearer tokens only — skip cookie credentials. Long default timeout for LAN + slow DB.
const api = createApiClient(mobileAdapter, {
  timeout: mobileApiTimeoutMs,
  withCredentials: false,
});

const extra = (Constants.expoConfig?.extra || (Constants as any).manifest?.extra || {}) as {
  apiUrl?: string;
};

const configuredApiUrl = (process.env.EXPO_PUBLIC_API_URL || extra.apiUrl || '').trim();

const isLocalApiUrl = (url: string) =>
  /^https?:\/\/(?:localhost|127\.0\.0\.1|10\.0\.2\.2)(?::\d+)?(?:\/|$)/i.test(url);

const normalizeApiBaseUrl = (url: string) => {
  const trimmed = url.replace(/\/+$/, '');
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
};

/** host:port from Expo; bracket form [::1]:8081 supported */
const parseDebuggerHost = (hostUri: string | undefined): string | null => {
  if (!hostUri || !hostUri.trim()) return null;
  const h = hostUri.trim();
  if (h.startsWith('[')) {
    const end = h.indexOf(']:');
    if (end !== -1) return h.slice(1, end);
    return null;
  }
  const lastColon = h.lastIndexOf(':');
  if (lastColon <= 0) return h;
  return h.slice(0, lastColon);
};

const isTunnelStyleHost = (host: string) =>
  /\.exp\.direct$/i.test(host) ||
  /\.exp\.host$/i.test(host) ||
  /\.expo\.dev$/i.test(host) ||
  /\.ngrok(?:-free)?\.app$/i.test(host);

// Resolve baseURL for mobile development (Expo Go / Development builds).
// Uses the Expo debugger host so the app automatically connects to whichever
// machine is running Metro — no hardcoded IPs needed.
if (__DEV__) {
  if (configuredApiUrl && !isLocalApiUrl(configuredApiUrl)) {
    api.defaults.baseURL = normalizeApiBaseUrl(configuredApiUrl);
  } else {
    const debuggerHost = Constants.expoConfig?.hostUri || (Constants as any).manifest?.hostUri;
    const fromHostUri = parseDebuggerHost(debuggerHost);
    const devHostOverride = (process.env.EXPO_PUBLIC_DEV_HOST || '').trim();

    let address: string | null = devHostOverride || null;
    if (!address && fromHostUri) {
      if (!isTunnelStyleHost(fromHostUri)) {
        address = fromHostUri;
      }
    }
    if (!address) {
      address = '10.0.2.2'; // Android emulator → host loopback when hostUri is missing
    }

    if (fromHostUri && isTunnelStyleHost(fromHostUri) && !devHostOverride && !configuredApiUrl) {
      console.warn(
        '[dev] Expo tunnel host cannot reach your API. Set EXPO_PUBLIC_API_URL (e.g. http://YOUR_LAN_IP:8000/api) or EXPO_PUBLIC_DEV_HOST=YOUR_LAN_IP, or use Expo LAN (npx expo start --lan).'
      );
    }

    const port = process.env.EXPO_PUBLIC_API_PORT || '8000';
    api.defaults.baseURL = `http://${address}:${port}/api`;
  }
  console.log('[dev] Mobile API BaseURL:', api.defaults.baseURL);
} else {
  if (!configuredApiUrl || isLocalApiUrl(configuredApiUrl)) {
    throw new Error(
      'Mobile API base URL is not configured for production. Set EXPO_PUBLIC_API_URL to the deployed backend URL.'
    );
  }
  api.defaults.baseURL = normalizeApiBaseUrl(configuredApiUrl);
}

/**
 * Resolves a potentially relative image path to an absolute URL
 * using the current API base URL.
 */
export const getImageUrl = (path: string) => {
  if (!path) return '';
  if (path.startsWith('http')) return path;

  const baseUrl = api.defaults.baseURL || '';
  const host = baseUrl.split('/api')[0];
  const cleanPath = path.startsWith('/') ? path : `/${path}`;

  return `${host}${cleanPath}`;
};

export default api;
export { TOKEN_KEY, REFRESH_KEY, SESSION_KEY };
