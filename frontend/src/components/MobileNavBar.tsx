'use client';

import React, { useState, useRef, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
// import { useWishlist } from '@/context/WishlistContext';
import { useWishlistStore } from '@/store/wishlistStore';
import { getGuestCartCount } from '@/utils/guestStore';

// Temporary placeholder components
const MyCartIcon: React.FC<{ cartCount: number }> = ({ cartCount }) => (
  <div className="relative">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-gray-600">
      <path
        d="M9 22C9.55228 22 10 21.5523 10 21C10 20.4477 9.55228 20 9 20C8.44772 20 8 20.4477 8 21C8 21.5523 8.44772 22 9 22Z"
        fill="currentColor"
      />
      <path
        d="M20 22C20.5523 22 21 21.5523 21 21C21 20.4477 20.5523 20 20 20C19.4477 20 19 20.4477 19 21C19 21.5523 19.4477 22 20 22Z"
        fill="currentColor"
      />
      <path
        d="M1 1H5L7.68 14.39C7.77 14.85 8.17 15.18 8.64 15.18H19.32C19.79 15.18 20.19 14.85 20.28 14.39L22 6H6"
        stroke="currentColor"
        strokeWidth="2"
      />
    </svg>
    {cartCount > 0 && (
      <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
        {cartCount > 99 ? '99+' : cartCount}
      </span>
    )}
  </div>
);

const WishlistIcon: React.FC<{ count: number }> = ({ count }) => (
  <div className="relative">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-gray-600">
      <path
        d="M20.84 4.61C20.3292 4.099 19.7229 3.69365 19.0554 3.41708C18.3879 3.14052 17.673 2.99817 16.95 2.99817C16.227 2.99817 15.5121 3.14052 14.8446 3.41708C14.1771 3.69365 13.5708 4.099 13.06 4.61L12 5.67L10.94 4.61C9.9083 3.57831 8.50903 2.99871 7.05 2.99871C5.59096 2.99871 4.19169 3.57831 3.16 4.61C2.12831 5.64169 1.54871 7.04097 1.54871 8.5C1.54871 9.95903 2.12831 11.3583 3.16 12.39L4.22 13.45L12 21.23L19.78 13.45L20.84 12.39C21.351 11.8792 21.7564 11.2729 22.0329 10.6054C22.3095 9.93789 22.4518 9.22295 22.4518 8.5C22.4518 7.77704 22.3095 7.06211 22.0329 6.3946C21.7564 5.7271 21.351 5.12079 20.84 4.61Z"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
    </svg>
    {count > 0 && (
      <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
        {count > 99 ? '99+' : count}
      </span>
    )}
  </div>
);

import ThemeSwitcher from './ThemeSwitcher';
import GeneralFeedbackModal from './GeneralFeedbackModal';
import AccessibilityModal from './AccessibilityModal';
import CustomerNotificationsModal from './CustomerNotificationsModal';
import api from '@/utils/api';
import styles from './MobileNavBar.module.css';
import { logger } from '@/utils/logger';
import ModeSwitchToggle from './ModeSwitchToggle';
import { usePincode } from '@/context/PincodeContext';

interface MobileNavBarProps {
  basePath?: string;
}

export default function MobileNavBar({ basePath = '/' }: MobileNavBarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme } = useTheme();
  // const { items: wishlistItems } = useWishlist();
  const wishlistItems = useWishlistStore((s) => s.items);
  const { availableModes } = usePincode();
  const [cartCount, setCartCount] = useState(0);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [showNotificationsModal, setShowNotificationsModal] = useState(false);
  const [unreadNotifCount, setUnreadNotifCount] = useState(0);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showAccessibilityModal, setShowAccessibilityModal] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const profileDropdownRef = useRef<HTMLDivElement>(null);

  // Get user-specific base path
  const getBasePath = () => {
    if (basePath && basePath !== '/') return basePath;
    if (!user) return '/';
    if (user.role === 'customer') return '/customer';
    if (user.role === 'wholesaler') return '/wholesaler';
    if (user.role === 'valet') return '/valet';
    return '/';
  };

  const userBasePath = getBasePath();

  useEffect(() => {
    fetchCartCount();
    let interval: ReturnType<typeof setInterval> | null = setInterval(fetchCartCount, 60_000);

    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (interval) { clearInterval(interval); interval = null; }
      } else {
        fetchCartCount();
        interval = setInterval(fetchCartCount, 60_000);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (interval) clearInterval(interval);
    };
  }, [user]);

  useEffect(() => {
    if (user) {
      const fetchUnreadCount = async () => {
        try {
          const res = await api.get('/push-notifications/inbox');
          const data = res.data || [];
          setUnreadNotifCount(data.filter((n: any) => !n.isRead).length);
        } catch (e) { logger.warn("Silent catch block:", e);  }
      };
      fetchUnreadCount();
    }
  }, [user]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        profileDropdownRef.current &&
        !profileDropdownRef.current.contains(event.target as Node)
      ) {
        setShowProfileDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsMenuOpen(false);
        setShowProfileDropdown(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const fetchCartCount = async () => {
    try {
      if (user) {
        const response = await api.get('/cart');
        const cartItems = response.data.items || [];
        const totalQuantity = cartItems.reduce(
          (sum: number, item: any) => sum + (item.quantity || 0),
          0
        );
        setCartCount(totalQuantity);
      } else {
        setCartCount(getGuestCartCount());
      }
    } catch (error) {
      logger.error('Error fetching cart count:', error);
      setCartCount(0);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
    setShowProfileDropdown(false);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  let navItems = [];

  if (user?.role === 'valet') {
    navItems = [
      { label: 'Orders', href: userBasePath, icon: '📋' },
      { label: 'Profile', href: `${userBasePath}/profile`, icon: '👤' },
    ];
  } else {
    navItems = [
      { label: 'Home', href: userBasePath, icon: '🏠' },
      { label: 'Products', href: '/products', icon: '📦' },
      { label: 'Categories', href: '/categories', icon: '🏷️' },
      { label: 'Brands', href: '/brands', icon: '🏢' },
      { label: 'Orders', href: `${userBasePath}/orders`, icon: '📋' },
    ];
    if (user?.role === 'wholesaler' || user?.effectiveRole === 'wholesaler') {
      navItems.push({ label: 'Schemes', href: `${userBasePath}/schemes`, icon: '🎁' });
    }
    navItems.push({ label: 'Profile', href: `${userBasePath}/profile`, icon: '👤' });
  }

  if (user?.role === 'super_admin') {
    navItems.push({ label: 'Admin', href: '/admin', icon: '⚙️' });
  }

  return (
    <>
      <div className={styles.mobileNavBar}>
        <div className={styles.navContent}>
          <div className={styles.logo} onClick={() => router.push(userBasePath)}>
            <h1 style={{ color: theme.primary }}>Stationery Junction</h1>
          </div>

          {/* Mode switch pill - only shown when both modes are available */}
          {availableModes.length === 2 && (
            <div className="flex items-center">
              <ModeSwitchToggle />
            </div>
          )}

          <div className={styles.navIcons}>
            <div className={styles.themeSwitcherWrapper}>
              <ThemeSwitcher />
            </div>

            <button
              className={styles.iconButton}
              onClick={() => router.push(`${userBasePath}/cart`)}
              aria-label={`Shopping cart${cartCount > 0 ? `, ${cartCount} item${cartCount !== 1 ? 's' : ''}` : ''}`}
            >
              <MyCartIcon cartCount={cartCount} />
            </button>

            <button
              className={styles.iconButton}
              onClick={() => router.push(`${userBasePath}/wishlist`)}
              aria-label={`Wishlist${wishlistItems.length > 0 ? `, ${wishlistItems.length} item${wishlistItems.length !== 1 ? 's' : ''}` : ''}`}
            >
              <WishlistIcon count={wishlistItems.length} />
            </button>

            <button className={styles.menuToggle} onClick={toggleMenu} aria-label="Toggle menu">
              <span className={`${styles.hamburger} ${isMenuOpen ? styles.open : ''}`}>
                <span></span>
                <span></span>
                <span></span>
              </span>
            </button>
          </div>
        </div>
      </div>

      {isMenuOpen && (
        <>
          <div className={styles.menuOverlay} onClick={closeMenu} />
          <div className={`${styles.mobileMenu} ${isMenuOpen ? styles.open : ''}`}>
            <div className={styles.menuHeader}>
              <h3>Menu</h3>
              <button className={styles.closeMenu} onClick={closeMenu}>
                ×
              </button>
            </div>
            <nav className={styles.menuNav}>
              {navItems.map((item) => (
                <button
                  key={item.href}
                  className={`${styles.menuItem} ${pathname === item.href ? styles.active : ''}`}
                  aria-current={pathname === item.href ? 'page' : undefined}
                  onClick={() => {
                    router.push(item.href);
                    closeMenu();
                  }}
                >
                  <span className={styles.menuIcon}>{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </>
      )}
      <GeneralFeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
      />
      <CustomerNotificationsModal
        isOpen={showNotificationsModal}
        onClose={() => setShowNotificationsModal(false)}
        onUnreadCountChange={setUnreadNotifCount}
      />
      <AccessibilityModal
        isOpen={showAccessibilityModal}
        onClose={() => setShowAccessibilityModal(false)}
      />
    </>
  );
}
