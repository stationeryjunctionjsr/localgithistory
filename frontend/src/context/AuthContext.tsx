'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import api, { setSessionRevokedHandler } from '@/utils/api';
import Cookies from 'js-cookie';
import { toast } from 'react-toastify';
import { logActivity, promoteGuestActivities } from '@/utils/activity';
import { syncGuestDataToBackend } from '@/utils/syncCartWishlist';


interface User {
  _id: string;
  name?: string | null;
  email?: string | null;
  phone?: string;
  role: 'super_admin' | 'wholesaler' | 'customer' | 'valet';
  effectiveRole?: 'super_admin' | 'wholesaler' | 'customer' | 'valet';
  companyName?: string;
  approvalStatus?: string;
  address?: any;
  savedAddresses?: any[];
  creditLimit?: number;
  creditUsed?: number;
  logoUrl?: string;
  referralCode?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  loginWithTokens: (data: {
    token: string;
    refreshToken?: string;
    sessionId?: string;
    user?: any;
  }) => Promise<User>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  sessionRevokedDetail: any;
}

interface RegisterData {
  name?: string;
  email?: string;
  password: string;
  role: 'wholesaler' | 'customer';
  phone?: string;
  companyName?: string;
  address?: any;
  msg91Token?: string;
  otp?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionRevokedDetail, setSessionRevokedDetail] = useState<any>(null);

  useEffect(() => {
    checkAuth();
    setSessionRevokedHandler((detail) => {
      setSessionRevokedDetail(detail);
      setUser(null);
    });
    return () => setSessionRevokedHandler(null);
  }, []);

  const checkAuth = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch {
      setUser(null);
    }
    setLoading(false);
  };

  const login = async (emailOrPhone: string, password: string) => {
    try {
      const isEmail = emailOrPhone.includes('@');
      const loginData = isEmail
        ? { email: emailOrPhone.toLowerCase(), password }
        : { phone: emailOrPhone.replace(/\D/g, ''), password };

      const response = await api.post('/auth/login', loginData);
      const { sessionId, user: userData, message } = response.data;

      if (!userData) {
        toast.error('Invalid response from server');
        throw new Error('Invalid response from server');
      }

      if (typeof window !== 'undefined') {
        if (sessionId) {
          window.localStorage.setItem('sessionId', sessionId);
        } else {
          window.localStorage.removeItem('sessionId');
        }
      }
      setUser(userData);
      // promote guest activities if we had a guest session id
      const guestSessionId = Cookies.get('guestSessionId');
      if (guestSessionId && sessionId) {
        promoteGuestActivities(guestSessionId, userData._id).catch(() => {});
      }
      logActivity({
        type: 'login',
        detail: { method: isEmail ? 'email' : 'phone' },
        sessionId,
      }).catch(() => {});
      // Sync guest cart/wishlist to backend (fire-and-forget — don't block login)
      syncGuestDataToBackend().catch(() => {});

      if (message) {
        toast.info(message);
      } else {
        toast.success('Login successful');
      }

      return userData;
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Login failed');
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      const response = await api.post('/auth/register', data);
      const { sessionId, user: userData, message } = response.data;

      if (typeof window !== 'undefined') {
        if (sessionId) {
          window.localStorage.setItem('sessionId', sessionId);
        } else {
          window.localStorage.removeItem('sessionId');
        }
      }
      setUser(userData);
      logActivity({ type: 'register', detail: { role: data.role }, sessionId }).catch(() => {});
      // Sync guest cart/wishlist to backend (fire-and-forget — don't block registration)
      syncGuestDataToBackend().catch(() => {});

      if (message) {
        toast.info(message);
      } else {
        toast.success('Registration successful');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Registration failed');
      throw error;
    }
  };

  /** Store tokens from an external auth flow (e.g. inline checkout registration) */
  const loginWithTokens = async (data: {
    token: string;
    refreshToken?: string;
    sessionId?: string;
    user?: any;
  }) => {
    if (typeof window !== 'undefined') {
      if (data.sessionId) {
        window.localStorage.setItem('sessionId', data.sessionId);
      } else {
        window.localStorage.removeItem('sessionId');
      }
    }
    const userData = data.user;
    if (userData) setUser(userData);
    // Sync guest cart/wishlist to backend (fire-and-forget)
    syncGuestDataToBackend().catch(() => {});
    return userData;
  };

  const logout = () => {
    api.post('/auth/logout', {}).catch(() => {});
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('sessionId');
    }
    setUser(null);
    logActivity({ type: 'logout' }).catch(() => {});
  };

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        loginWithTokens,
        register,
        logout,
        fetchUser,
        sessionRevokedDetail,
      }}
    >
      {children}
      {sessionRevokedDetail && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.45)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000,
          }}
        >
          <div
            style={{
              background: '#fff',
              padding: '24px',
              borderRadius: '12px',
              maxWidth: '420px',
              width: '90%',
              boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
            }}
          >
            <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Session ended</h3>
            <p style={{ marginBottom: '16px' }}>
              Your account is active in another device. Do you wish to sign in here?
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSessionRevokedDetail(null)}
                style={{
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: '1px solid #ccc',
                  background: '#f5f5f5',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setSessionRevokedDetail(null);
                  window.location.href = '/login';
                }}
                style={{
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: 'none',
                  background: '#111827',
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      )}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
