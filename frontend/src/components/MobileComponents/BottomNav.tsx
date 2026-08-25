'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

export default function BottomNav() {
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useAuth();
  const { theme } = useTheme();
  const MOBILE_ACCENT = theme.primary;
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    const fetchCartCount = async () => {
      if (!user) {
        const { getGuestCart } = await import('@/utils/guestStore');
        setCartCount(getGuestCart().length);
        return;
      }
      try {
        const res = await api.get('/cart');
        const items = res.data?.items || res.data || [];
        setCartCount(items.length);
      // eslint-disable-next-line unused-imports/no-unused-vars
      } catch (e) { logger.warn("Silent catch block:", e); /* Silent fail */ }
    };
    fetchCartCount();
  }, [user]);

  const getHomePath = () => {
    if (!user) return '/';
    if (user.role === 'customer') return '/customer';
    if (user.role === 'wholesaler') return '/wholesaler';
    return '/';
  };

  const getUserBasePath = () => {
    if (!user) return '/customer';
    if (user.role === 'customer') return '/customer';
    if (user.role === 'wholesaler') return '/wholesaler';
    return '/customer';
  };

  const basePath = getUserBasePath();

  // Check if path is active
  const isActive = (path: string) => {
    if (
      path === getHomePath() &&
      (pathname === getHomePath() || pathname === '/' || pathname === '/')
    )
      return true;
    if (path !== getHomePath() && pathname?.startsWith(path)) return true;
    return false;
  };

  const navItems = [
    {
      label: 'Home',
      path: getHomePath(),
      icon: (active: boolean) => (
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill={active ? 'currentColor' : 'none'}
          stroke="currentColor"
          strokeWidth={active ? '0' : '1.8'}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          {!active && <polyline points="9 22 9 12 15 12 15 22"></polyline>}
        </svg>
      ),
    },
    {
      label: 'Categories',
      path: '/categories',
      icon: (active: boolean) => (
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill={active ? 'currentColor' : 'none'}
          stroke={active ? 'none' : 'currentColor'}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect x="3" y="3" width="7" height="7" rx="1"></rect>
          <rect x="14" y="3" width="7" height="7" rx="1"></rect>
          <rect x="14" y="14" width="7" height="7" rx="1"></rect>
          <rect x="3" y="14" width="7" height="7" rx="1"></rect>
        </svg>
      ),
    },
    {
      label: 'Brands',
      path: '/brands',
      icon: (active: boolean) => (
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill={active ? 'currentColor' : 'none'}
          stroke="currentColor"
          strokeWidth={active ? '0' : '1.8'}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59z"></path>
          <line x1="7" y1="7" x2="7.01" y2="7"></line>
        </svg>
      ),
    },
    {
      label: 'Cart',
      path: `${basePath}/cart`,
      badge: cartCount,
      icon: (active: boolean) => (
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill={active ? 'currentColor' : 'none'}
          stroke={active ? 'none' : 'currentColor'}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"></path>
          <line x1="3" y1="6" x2="21" y2="6" stroke="currentColor" strokeWidth="1.8"></line>
          <path
            d="M16 10a4 4 0 0 1-8 0"
            stroke={active ? 'white' : 'currentColor'}
            strokeWidth="1.8"
            fill="none"
          ></path>
        </svg>
      ),
    },
    {
      label: 'Profile',
      path: user ? `${basePath}/profile` : '/login',
      icon: (active: boolean) => (
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill={active ? 'currentColor' : 'none'}
          stroke={active ? 'none' : 'currentColor'}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
      ),
    },
  ];

  // Hide on admin pages
  if (pathname?.includes('/admin')) return null;

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-100 bg-white md:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="flex h-16 items-center justify-around px-2">
        {navItems.map((item) => {
          const active = isActive(item.path);
          return (
            <button
              key={item.label}
              onClick={() => router.push(item.path)}
              className={`relative flex h-full flex-1 flex-col items-center justify-center transition-all duration-200 ${active ? 'scale-105' : ''}`}
            >
              {/* Active Indicator Pill */}
              {active && (
                <div
                  className="absolute top-1 h-1 w-10 rounded-full"
                  style={{ backgroundColor: MOBILE_ACCENT, animation: 'scaleIn 0.2s ease-out' }}
                />
              )}

              {/* Icon */}
              <div
                className={`relative transition-colors duration-200 ${active ? '' : 'text-gray-400'}`}
                style={active ? { color: MOBILE_ACCENT } : undefined}
              >
                {item.icon(active)}

                {/* Badge */}
                {item.badge && item.badge > 0 && (
                  <span
                    className="absolute -right-2 -top-1 flex h-4 min-w-[16px] items-center justify-center rounded-full px-1 text-[9px] font-bold text-white"
                    style={{ backgroundColor: MOBILE_ACCENT }}
                  >
                    {item.badge > 99 ? '99+' : item.badge}
                  </span>
                )}
              </div>

              {/* Label */}
              <span
                className={`mt-1 text-[10px] font-medium transition-colors duration-200 ${active ? '' : 'text-gray-400'}`}
                style={active ? { color: MOBILE_ACCENT } : undefined}
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </div>

      <style jsx>{`
        @keyframes scaleIn {
          from {
            transform: scaleX(0);
          }
          to {
            transform: scaleX(1);
          }
        }
      `}</style>
    </nav>
  );
}
