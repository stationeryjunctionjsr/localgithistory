import { useCallback, useEffect, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import Toast from 'react-native-toast-message';
import api, { TOKEN_KEY, REFRESH_KEY, SESSION_KEY } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { setSessionRevokedHandler } from '@sj/api-client';
import { syncGuestDataToBackend } from '../services/syncCartWishlist';
import { registerExpoPushToken } from '../utils/expoPushNotifications';

let isInitialCheckDone = false;

interface AuthResponse {
  token: string;
  refreshToken?: string;
  sessionId?: string;
  user?: any;
}

export function useAuth() {
  const { user, setUser, sessionRevokedDetail, setSessionRevokedDetail } = useAuthStore();

  const fetchUser = useCallback(async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      return res.data;
    } catch {
      return null;
    }
  }, [setUser]);
  const [loading, setLoading] = useState(!isInitialCheckDone);

  useEffect(() => {
    setSessionRevokedHandler((detail: any) => {
      setSessionRevokedDetail(detail);
      setUser(null);
    });

    if (isInitialCheckDone) {
      return () => setSessionRevokedHandler(null);
    }

    (async () => {
      const token = await SecureStore.getItemAsync(TOKEN_KEY);
      if (token && !user) {
        try {
          // Startup auth check should fail fast to avoid an endless loading screen.
          const res = await api.get('/auth/me', { timeout: 8000 });
          setUser(res.data);
          // Register push token on app startup (token already stored)
          registerExpoPushToken().catch(() => {});
        } catch (err) {
          const status = (err as any)?.response?.status;
          if (status === 401 || status === 403) {
            await clearTokens();
            setUser(null);
          }
        }
      }
      isInitialCheckDone = true;
      setLoading(false);
    })();
    return () => setSessionRevokedHandler(null);
  }, [setSessionRevokedDetail, user]);

  const clearTokens = useCallback(async () => {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_KEY);
    await SecureStore.deleteItemAsync(SESSION_KEY);
  }, []);

  /** Store tokens, set user, and sync guest cart/wishlist to backend */
  const storeTokensAndSetUser = useCallback(
    async (token: string, refreshToken?: string, sessionId?: string, userData?: any) => {
      if (token) await SecureStore.setItemAsync(TOKEN_KEY, token);
      if (refreshToken) await SecureStore.setItemAsync(REFRESH_KEY, refreshToken);
      if (sessionId) await SecureStore.setItemAsync(SESSION_KEY, sessionId);
      if (userData) setUser(userData);
      // Sync guest cart/wishlist to backend after login
      syncGuestDataToBackend().catch(() => {
        Toast.show({
          type: 'error',
          text1: 'Cart not restored',
          text2: "We couldn't restore your cart. Please add your items again.",
          visibilityTime: 4000,
        });
      });
      // Register Expo push token after login
      registerExpoPushToken().catch(() => {});
      return userData;
    },
    []
  );

  const login = useCallback(
    async (emailOrPhone: string, password: string) => {
      // Determine if input is email or phone
      const isEmail = emailOrPhone.includes('@');
      const loginData = isEmail
        ? { email: emailOrPhone.trim().toLowerCase(), password }
        : { phone: emailOrPhone.replace(/\D/g, ''), password };

      const res = await api.post<AuthResponse>('/auth/login', loginData);
      const { token, refreshToken, sessionId, user: userData } = res.data;
      return storeTokensAndSetUser(token, refreshToken, sessionId, userData);
    },
    [storeTokensAndSetUser]
  );

  /** Login using tokens returned from checkout registration */
  const loginWithTokens = useCallback(
    async (data: { token: string; refreshToken?: string; sessionId?: string; user?: any }) => {
      return storeTokensAndSetUser(data.token, data.refreshToken, data.sessionId, data.user);
    },
    [storeTokensAndSetUser]
  );

  const refresh = useCallback(async () => {
    const refreshToken = await SecureStore.getItemAsync(REFRESH_KEY);
    const sessionId = await SecureStore.getItemAsync(SESSION_KEY);
    if (!refreshToken || !sessionId) throw new Error('No refresh token');
    const res = await api.post<AuthResponse>('/auth/refresh', { refreshToken }, {
      sessionId,
      skipAccessToken: true,
    } as any);
    const {
      token: newToken,
      refreshToken: newRefresh,
      sessionId: newSessionId,
      user: userData,
    } = res.data || {};
    if (newToken) await SecureStore.setItemAsync(TOKEN_KEY, newToken);
    if (newRefresh) await SecureStore.setItemAsync(REFRESH_KEY, newRefresh);
    if (newSessionId) await SecureStore.setItemAsync(SESSION_KEY, newSessionId);
    if (userData) setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(async () => {
    await clearTokens();
    setUser(null);
  }, [clearTokens]);

  const clearSessionRevoked = useCallback(
    (action?: 'login') => {
      setSessionRevokedDetail(null);
      if (action === 'login') {
        // navigation handled by caller
      }
    },
    [setSessionRevokedDetail]
  );

  return {
    user,
    loading,
    login,
    loginWithTokens,
    refresh,
    logout,
    fetchUser,
    sessionRevokedDetail,
    clearSessionRevoked,
  };
}
