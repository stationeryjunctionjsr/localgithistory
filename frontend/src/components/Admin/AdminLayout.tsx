'use client';

import { useState, useEffect, useRef, Fragment } from 'react';
import { createPortal } from 'react-dom';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import Notifications from '@/components/Notifications';
import DashboardStats from './DashboardStats';

const HEADER_HEIGHT = 56;

interface AdminLayoutProps {
  children?: React.ReactNode;
}

const iconClass = 'w-5 h-5 flex-shrink-0';

const menuIcons: Record<string, React.ReactNode> = {
  dashboard: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
      />
    </svg>
  ),
  users: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  ),
  categories: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
      />
    </svg>
  ),
  brands: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
      />
    </svg>
  ),
  products: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
      />
    </svg>
  ),
  orders: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
      />
    </svg>
  ),
  payments: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
      />
    </svg>
  ),
  reports: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  ),
  delivery: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1h-1m-1-1V8a1 1 0 011-1h2a1 1 0 011 1v8a1 1 0 01-1 1h-1m-1-1z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6" />
    </svg>
  ),
  'delivery-charges': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  'delivery-slots': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  ),
  discounts: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"
      />
    </svg>
  ),
  promotions: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
      />
    </svg>
  ),
  ads: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
    </svg>
  ),
  banners: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
      />
    </svg>
  ),
  contacts: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
      />
    </svg>
  ),
  analytics: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  ),
  'push-notifications': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 00-6-6 6 6 0 00-6 6v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
      />
    </svg>
  ),
  'search-tags': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  ),
  'promo-strip': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 6h16M4 12h16M4 18h16"
      />
    </svg>
  ),
  collections: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V5a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2m14 0V5a2 2 0 012-2h2a2 2 0 012 2v6a2 2 0 01-2 2z"
      />
    </svg>
  ),
  bundles: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
      />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11v6" />
    </svg>
  ),
  support: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  ),
  feedback: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
      />
    </svg>
  ),
  'feedback-support': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  ),
  'reports-analytics': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  ),
  catalog: (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
      />
    </svg>
  ),
  'content-pages': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
    </svg>
  ),
  'faq-management': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  'about-management': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  'privacy-management': (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
};

type MenuItem = { id: string; label: string; children?: { id: string; label: string }[] };

const menuItems: MenuItem[] = [
  { id: 'dashboard', label: 'Dashboard' },
  {
    id: 'users',
    label: 'Users',
    children: [
      { id: 'users', label: 'Individual Users' },
      { id: 'retail-customer-segments', label: 'Retail Customer Segments' },
      { id: 'business-customer-segments', label: 'Business Customer Segments' },
    ],
  },
  {
    id: 'catalog',
    label: 'Catalog',
    children: [
      { id: 'categories', label: 'Categories' },
      { id: 'brands', label: 'Brands' },
      { id: 'products', label: 'Products' },
      { id: 'search-tags', label: 'Search Tags' },
      { id: 'collections', label: 'Collections' },
      { id: 'bundles', label: 'Bundles' },
    ],
  },
  {
    id: 'discounts',
    label: 'Discounts',
    children: [
      { id: 'retail-discounts', label: 'Retail Discounts' },
      { id: 'business-discounts', label: 'Business Discounts' },
    ],
  },
  {
    id: 'delivery',
    label: 'Delivery',
    children: [
      { id: 'delivery-charges', label: 'Delivery Charges' },
      { id: 'delivery-slots', label: 'Delivery Slots' },
    ],
  },
  { id: 'orders', label: 'Orders' },
  { id: 'payments', label: 'Payments' },
  {
    id: 'promotions',
    label: 'Promotions',
    children: [
      { id: 'banners', label: 'Banners' },
      { id: 'promo-strip', label: 'Promo Strip' },
      { id: 'push-notifications', label: 'Push Notifications' },
      { id: 'ads', label: 'Ad Campaigns' },
    ],
  },
  {
    id: 'reports-analytics',
    label: 'Reports & Analytics',
    children: [
      { id: 'reports', label: 'Reports' },
      { id: 'analytics', label: 'Analytics' },
    ],
  },
  { id: 'contacts', label: 'Contacts' },
  {
    id: 'content-pages',
    label: 'Content Pages',
    children: [
      { id: 'faq-management', label: 'FAQ' },
      { id: 'about-management', label: 'About Us' },
      { id: 'privacy-management', label: 'Privacy Policy' },
    ],
  },
  {
    id: 'feedback-support',
    label: 'Feedback & Support',
    children: [
      { id: 'feedback', label: 'Feedback' },
      { id: 'reviews', label: 'Product Reviews' },
      { id: 'google-reviews', label: 'Google Reviews' },
      { id: 'support', label: 'Support' },
    ],
  },
];

const AdminLayout = ({ children }: AdminLayoutProps) => {
  const { user, logout } = useAuth();
  const { theme } = useTheme();
  const pathname = usePathname();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    // Disable body and html scrolling when in admin layout to prevent double scrollbars
    const originalBodyOverflow = document.body.style.overflow;
    const originalHtmlOverflow = document.documentElement.style.overflow;

    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = originalBodyOverflow;
      document.documentElement.style.overflow = originalHtmlOverflow;
    };
  }, []);

  const allTabIds = menuItems.flatMap((m) => (m.children ? m.children.map((c) => c.id) : [m.id]));

  const [expandedParents, setExpandedParents] = useState<Record<string, boolean>>({});
  const [collapsedFlyoutId, setCollapsedFlyoutId] = useState<string | null>(null);
  const flyoutTriggerRef = useRef<HTMLButtonElement>(null);
  const [flyoutPosition, setFlyoutPosition] = useState<{ top: number; left: number } | null>(null);

  useEffect(() => {
    const pathSegments = pathname.split('/');
    const currentSegment = pathSegments[pathSegments.length - 1] || 'dashboard';
    const isAdminRoot = pathname === '/admin' || pathname === '/admin/';
    if (isAdminRoot) {
      setActiveTab('dashboard');
      return;
    }
    if (allTabIds.includes(currentSegment)) {
      setActiveTab(currentSegment);
      setExpandedParents((prev) => {
        const next = { ...prev };
        const usersParent = menuItems.find((m) => m.id === 'users');
        const catalogParent = menuItems.find((m) => m.id === 'catalog');
        const reportsParent = menuItems.find((m) => m.id === 'reports-analytics');
        const discountsParent = menuItems.find((m) => m.id === 'discounts');
        const deliveryParent = menuItems.find((m) => m.id === 'delivery');
        const promotionsParent = menuItems.find((m) => m.id === 'promotions');
        const feedbackSupportParent = menuItems.find((m) => m.id === 'feedback-support');
        if (usersParent?.children?.some((c) => c.id === currentSegment)) next.users = true;
        if (catalogParent?.children?.some((c) => c.id === currentSegment)) next.catalog = true;
        if (reportsParent?.children?.some((c) => c.id === currentSegment))
          next['reports-analytics'] = true;
        if (discountsParent?.children?.some((c) => c.id === currentSegment)) next.discounts = true;
        if (deliveryParent?.children?.some((c) => c.id === currentSegment)) next.delivery = true;
        if (promotionsParent?.children?.some((c) => c.id === currentSegment))
          next.promotions = true;
        if (feedbackSupportParent?.children?.some((c) => c.id === currentSegment))
          next['feedback-support'] = true;
        return next;
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const handleTabClick = (tabId: string) => {
    setCollapsedFlyoutId(null);
    setActiveTab(tabId);
    const newPath = tabId === 'dashboard' ? '/admin' : `/admin/${tabId}`;
    router.push(newPath);
    setSidebarOpen(false);
    setSidebarCollapsed(true);
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleLogoClick = () => {
    setActiveTab('dashboard');
    router.push('/admin');
    setSidebarCollapsed(true);
  };

  const toggleSidebarCollapsed = () => {
    setSidebarCollapsed((c) => {
      const next = !c;
      try {
        localStorage.setItem('admin-sidebar-collapsed', String(next));
      } catch {}
      return next;
    });
  };

  useEffect(() => {
    try {
      const saved = localStorage.getItem('admin-sidebar-collapsed') === 'true';
      setSidebarCollapsed(saved);
    } catch {}
  }, []);

  useEffect(() => {
    if (!collapsedFlyoutId || !sidebarCollapsed) {
      setFlyoutPosition(null);
      return;
    }
    const el = flyoutTriggerRef.current;
    if (!el) return;
    const update = () => {
      const rect = el.getBoundingClientRect();
      const openItem = menuItems.find((m) => m.id === collapsedFlyoutId);
      const childCount = openItem?.children?.length || 0;
      // 8px container vertical padding + 40px header + (childCount * 40px per item)
      const estimatedHeight = 48 + childCount * 40;
      const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 800;
      let top = rect.top;
      if (top + estimatedHeight > viewportHeight) {
        top = Math.max(16, viewportHeight - estimatedHeight - 16);
      }
      setFlyoutPosition({ top, left: rect.right + 8 });
    };
    update();
    window.addEventListener('scroll', update, true);
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update, true);
      window.removeEventListener('resize', update);
    };
  }, [collapsedFlyoutId, sidebarCollapsed]);

  useEffect(() => {
    try {
      localStorage.setItem('admin-sidebar-collapsed', String(sidebarCollapsed));
    } catch {}
  }, [sidebarCollapsed]);

  const sidebarWidth = sidebarCollapsed ? 64 : 240;

  const SidebarNav = () => (
    <div className="flex h-full flex-col py-3">
      <button
        onClick={toggleSidebarCollapsed}
        className={`mx-2 mb-2 flex flex-shrink-0 items-center gap-3 rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 ${sidebarCollapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2.5'}`}
        title={sidebarCollapsed ? 'Expand menu' : 'Collapse menu'}
        aria-label={sidebarCollapsed ? 'Expand menu' : 'Collapse menu'}
      >
        <svg
          className="h-5 w-5 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          style={{ transform: sidebarCollapsed ? 'rotate(180deg)' : undefined }}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
          />
        </svg>
      </button>
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-2">
        {menuItems.map((item) => {
          const icon = menuIcons[item.id] ?? menuIcons.dashboard;
          const hasChildren = item.children && item.children.length > 0;
          const isExpanded = hasChildren && expandedParents[item.id];
          const isParentActive = hasChildren && item.children?.some((c) => c.id === activeTab);

          if (hasChildren && item.children) {
            if (sidebarCollapsed) {
              const flyoutOpen = collapsedFlyoutId === item.id;
              return (
                <div key={item.id} className="relative">
                  <button
                    ref={flyoutOpen ? flyoutTriggerRef : undefined}
                    onClick={() => setCollapsedFlyoutId(flyoutOpen ? null : item.id)}
                    className={`flex w-full flex-shrink-0 items-center justify-center gap-3 rounded-lg px-2 py-2.5 text-sm font-medium transition-colors ${isParentActive ? 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200/80' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
                    title={item.label}
                  >
                    {icon}
                  </button>
                </div>
              );
            }
            return (
              <div key={item.id}>
                <button
                  onClick={() => setExpandedParents((p) => ({ ...p, [item.id]: !p[item.id] }))}
                  className={`flex w-full flex-shrink-0 items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-colors ${isParentActive ? 'bg-indigo-50/80 text-indigo-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
                >
                  {icon}
                  <span className="flex-1 truncate">{item.label}</span>
                  <svg
                    className={`h-4 w-4 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                {isExpanded && (
                  <div className="ml-4 mt-0.5 space-y-0.5 border-l border-slate-200 pl-1">
                    {item.children.map((child) => {
                      const childIcon = menuIcons[child.id] ?? icon;
                      const isActive = activeTab === child.id;
                      return (
                        <button
                          key={child.id}
                          onClick={() => handleTabClick(child.id)}
                          className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors ${isActive ? 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200/80' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
                        >
                          {childIcon}
                          <span className="truncate">{child.label}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          }

          const isActive = activeTab === item.id;
          const btn = (
            <button
              key={item.id}
              onClick={() => handleTabClick(item.id)}
              className={`flex w-full flex-shrink-0 items-center gap-3 rounded-lg text-left text-sm font-medium transition-colors ${sidebarCollapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2.5'} ${isActive ? 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200/80' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
              title={sidebarCollapsed ? item.label : undefined}
            >
              {icon}
              {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
            </button>
          );
          return sidebarCollapsed ? (
            <div key={item.id} className="group relative">
              {btn}
              <div className="pointer-events-none absolute left-full top-1/2 z-[100] ml-2 -translate-y-1/2 whitespace-nowrap rounded bg-slate-800 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100">
                {item.label}
              </div>
            </div>
          ) : (
            <Fragment key={item.id}>{btn}</Fragment>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="flex h-screen flex-col bg-slate-50 overflow-hidden">
      {/* Header: full width, fixed at top */}
      <header className="fixed left-0 right-0 top-0 z-[100] h-14 border-b border-slate-200/80 bg-white shadow-sm">
        <div className="flex h-full items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((o) => !o)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
              aria-label="Toggle menu"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <div
              className="flex cursor-pointer items-center rounded-lg px-3 py-2 transition-colors hover:bg-slate-50"
              onClick={handleLogoClick}
            >
              {user?.logoUrl ? (
                <img
                  src={
                    user.logoUrl.startsWith('http')
                      ? user.logoUrl
                      : `${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || ''}${user.logoUrl}`
                  }
                  alt="Stationery Junction"
                  className="h-7 w-auto max-w-[140px] object-contain md:h-8"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                    if (fallback) fallback.style.display = 'block';
                  }}
                />
              ) : null}
              <h2
                className={`text-lg font-bold md:text-xl ${user?.logoUrl ? 'hidden' : 'block'}`}
                style={{ display: user?.logoUrl ? 'none' : 'block', color: theme.primary }}
              >
                Stationery Junction
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2 md:gap-4">
            <Notifications />
            <div className="relative">
              <button
                onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
              >
                <span className="text-lg" aria-hidden>
                  👤
                </span>
                <span className="hidden max-w-[120px] truncate md:block">
                  {user?.name || 'Admin'}
                </span>
              </button>
              {showProfileDropdown && (
                <div className="absolute right-0 z-50 mt-2 w-48 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-lg">
                  <button
                    onClick={() => {
                      setShowProfileDropdown(false);
                      handleTabClick('profile');
                    }}
                    className="block w-full px-4 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50"
                  >
                    My Profile
                  </button>
                  <button
                    onClick={() => {
                      setShowProfileDropdown(false);
                      handleLogout();
                    }}
                    className="block w-full border-t border-slate-100 px-4 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Content area: sidebar (below header) + main */}
      <div className="flex flex-1 mt-14 overflow-hidden" style={{ height: 'calc(100vh - 3.5rem)' }}>
        {/* Left sidebar - starts below header, collapsible on desktop */}
        <aside
          className={`fixed inset-y-0 left-0 z-[90] flex-shrink-0 self-start border-r border-slate-200/80 bg-white shadow-lg transition-[width,transform] duration-200 ease-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
          style={{
            width: sidebarWidth,
            top: HEADER_HEIGHT,
            height: `calc(100vh - ${HEADER_HEIGHT}px)`,
          }}
        >
          <div className="flex h-full flex-col pt-2 lg:pt-2">
            <SidebarNav />
          </div>
        </aside>

        {sidebarOpen && (
          <div
            className="fixed inset-0 z-[80] bg-black/40 lg:hidden"
            style={{ top: HEADER_HEIGHT }}
            onClick={() => setSidebarOpen(false)}
            aria-hidden
          />
        )}

        {/* Desktop backdrop overlay for expanded sidebar */}
        {!sidebarCollapsed && (
          <div
            className="fixed inset-0 z-[80] bg-black/15 transition-opacity duration-200 hidden lg:block"
            style={{ top: HEADER_HEIGHT }}
            onClick={() => setSidebarCollapsed(true)}
            aria-hidden
          />
        )}

        {sidebarCollapsed && collapsedFlyoutId && (
          <div
            className="fixed inset-0 z-[89]"
            onClick={() => setCollapsedFlyoutId(null)}
            aria-hidden
          />
        )}

        {sidebarCollapsed &&
          collapsedFlyoutId &&
          flyoutPosition &&
          typeof document !== 'undefined' &&
          (() => {
            const openItem = menuItems.find((m) => m.id === collapsedFlyoutId && m.children);
            if (!openItem?.children) return null;
            const flyoutEl = (
              <div
                className="fixed z-[100] min-w-[180px] rounded-lg border border-slate-600 bg-slate-800 py-1 text-sm text-white shadow-xl"
                style={{ top: flyoutPosition.top, left: flyoutPosition.left }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className="border-b border-slate-600 px-3 py-2 font-medium">
                  {openItem.label}
                </div>
                {openItem.children.map((child) => (
                  <button
                    key={child.id}
                    onClick={() => {
                      handleTabClick(child.id);
                      setCollapsedFlyoutId(null);
                      setSidebarOpen(false);
                    }}
                    className="block w-full px-3 py-2.5 text-left first:rounded-t-none last:rounded-b hover:bg-slate-700"
                  >
                    {child.label}
                  </button>
                ))}
              </div>
            );
            return createPortal(flyoutEl, document.body);
          })()}

        <main className="min-w-0 flex-1 p-3 sm:p-4 lg:p-6 lg:pl-[88px] overflow-hidden h-full">
          <div className="mx-auto max-w-[1400px] w-full h-full flex flex-col min-h-0 admin-main-container">
            <style
              dangerouslySetInnerHTML={{
                __html: `
                  .admin-main-container {
                    display: flex !important;
                    flex-direction: column !important;
                    height: 100% !important;
                    min-height: 0 !important;
                    overflow: hidden !important;
                  }
                  .admin-main-container > div {
                    display: flex !important;
                    flex-direction: column !important;
                    height: 100% !important;
                    min-height: 0 !important;
                  }
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) {
                    display: flex !important;
                    flex-direction: column !important;
                    height: 100% !important;
                    max-height: 100% !important;
                    min-height: 0 !important;
                    overflow: hidden !important;
                  }
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > h1,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > div:first-of-type,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > div.mb-6,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > .mb-6 {
                    flex-shrink: 0 !important;
                  }
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > .overflow-x-auto,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > div > .overflow-x-auto,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > .overflow-auto,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > div > .overflow-auto,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > .w-full.overflow-x-auto {
                    flex: 1 1 0% !important;
                    overflow: auto !important;
                    min-height: 0 !important;
                    border: 1px solid #e5e7eb !important;
                    border-radius: 0.375rem !important;
                  }
                  .admin-main-container table thead {
                    position: sticky !important;
                    top: 0 !important;
                    z-index: 10 !important;
                    background-color: #f9fafb !important;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
                  }
                  .admin-main-container table thead th {
                    position: sticky !important;
                    top: 0 !important;
                    z-index: 10 !important;
                    background-color: #f9fafb !important;
                  }
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > .mt-4,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > div > .mt-4,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > .mt-6,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > div > .mt-6,
                  .admin-main-container .bg-white.shadow-md:not(.fixed *):not([class*="fixed"] *) > nav {
                    flex-shrink: 0 !important;
                    margin-top: auto !important;
                    padding-top: 1rem !important;
                  }
                `,
              }}
            />
            {children || <DashboardStats />}
          </div>
        </main>
      </div>

      {showProfileDropdown && (
        <div className="fixed inset-0 z-40" onClick={() => setShowProfileDropdown(false)} />
      )}
    </div>
  );
};

export default AdminLayout;
