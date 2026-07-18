'use client';

import React, { useState, useRef, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { useWishlist } from '@/context/WishlistContext';
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

const ProfileIcon: React.FC = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-gray-600">
    <path
      d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21"
      stroke="currentColor"
      strokeWidth="2"
    />
    <path
      d="M12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);
import ThemeSwitcher from './ThemeSwitcher';
import GeneralFeedbackModal from './GeneralFeedbackModal';
import AccessibilityPanel from './AccessibilityPanel';
import api from '@/utils/api';
import styles from './MobileNavBar.module.css';

interface MobileNavBarProps {
  basePath?: string;
}

export default function MobileNavBar({ basePath = '/' }: MobileNavBarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme } = useTheme();
  const { items: wishlistItems } = useWishlist();
  const [cartCount, setCartCount] = useState(0);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
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
    const interval = setInterval(fetchCartCount, 5000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      console.error('Error fetching cart count:', error);
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
      {/* Mobile Navigation Bar */}
      <div className={styles.mobileNavBar}>
        <div className={styles.navContent}>
          {/* Logo */}
          <div className={styles.logo} onClick={() => router.push(userBasePath)}>
            <h1 style={{ color: theme.primary }}>Stationery Junction</h1>
          </div>

          {/* Right Icons */}
          <div className={styles.navIcons}>
            {/* Theme Switcher */}
            <div className={styles.themeSwitcherWrapper}>
              <ThemeSwitcher />
            </div>

            {/* Cart */}
            <button
              className={styles.iconButton}
              onClick={() => router.push(`${userBasePath}/cart`)}
              aria-label={`Shopping cart${cartCount > 0 ? `, ${cartCount} item${cartCount !== 1 ? 's' : ''}` : ''}`}
            >
              <MyCartIcon cartCount={cartCount} />
            </button>

            {/* Wishlist */}
            <button
              className={styles.iconButton}
              onClick={() => router.push(`${userBasePath}/wishlist`)}
              aria-label={`Wishlist${wishlistItems.length > 0 ? `, ${wishlistItems.length} item${wishlistItems.length !== 1 ? 's' : ''}` : ''}`}
            >
              <WishlistIcon count={wishlistItems.length} />
            </button>

            {/* Profile */}
            <div className={styles.profileWrapper} ref={profileDropdownRef}>
              <button
                className={styles.iconButton}
                onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                aria-label={user ? `Profile menu for ${user.name?.split(' ')[0] || 'User'}` : 'Profile menu'}
                aria-expanded={showProfileDropdown}
                aria-haspopup="true"
              >
                <ProfileIcon />
              </button>

              {showProfileDropdown && (
                <div className={styles.profileDropdown}>
                  {user ? (
                    <>
                      <div className={styles.userInfo}>
                        <span className={styles.userName}>{user.name}</span>
                        <span className={styles.userEmail}>{user.email}</span>
                      </div>
                      <div className={styles.dropdownDivider} />
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push(`${userBasePath}/profile`);
                        }}
                      >
                        My Profile
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push(`${userBasePath}/wishlist`);
                        }}
                      >
                        Wishlist
                      </button>
                      {user?.role !== 'valet' && (
                        <button
                          className={styles.dropdownItem}
                          onClick={() => {
                            setShowProfileDropdown(false);
                            router.push(`${userBasePath}/orders`);
                          }}
                        >
                          My Orders
                        </button>
                      )}
                      {user?.role === 'valet' && (
                        <button
                          className={styles.dropdownItem}
                          onClick={() => {
                            setShowProfileDropdown(false);
                            router.push(userBasePath);
                          }}
                        >
                          Dashboard
                        </button>
                      )}
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          setShowFeedbackModal(true);
                        }}
                      >
                        Give Feedback
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/support');
                        }}
                      >
                        Support
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/faq');
                        }}
                      >
                        FAQ
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/about');
                        }}
                      >
                        About Us
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/privacy-policy');
                        }}
                      >
                        Privacy Policy
                      </button>
                      {user?.role === 'super_admin' && (
                        <button
                          className={styles.dropdownItem}
                          onClick={() => {
                            setShowProfileDropdown(false);
                            router.push('/admin');
                          }}
                        >
                          Admin Panel
                        </button>
                      )}
                      <div className={styles.dropdownDivider} />
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          handleLogout();
                        }}
                      >
                        Logout
                      </button>
                      <AccessibilityPanel />
                    </>
                  ) : (
                    <>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/login');
                        }}
                      >
                        Login
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/customer/wishlist');
                        }}
                      >
                        Wishlist
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/register');
                        }}
                      >
                        Register
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/support');
                        }}
                      >
                        Support
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/faq');
                        }}
                      >
                        FAQ
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/about');
                        }}
                      >
                        About Us
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/privacy-policy');
                        }}
                      >
                        Privacy Policy
                      </button>
                      <AccessibilityPanel />
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Mobile Menu Toggle */}
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

      {/* Mobile Menu Overlay */}
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
    </>
  );
}
