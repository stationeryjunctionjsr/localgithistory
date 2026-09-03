'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { logger } from '@/utils/logger';

interface SellerAdminLayoutProps {
  children?: React.ReactNode;
}

const SIDEBAR_EXPANDED = 240;
const SIDEBAR_COLLAPSED = 64;
const HEADER_H = 56;

/* ─── SVG icons ─────────────────────────────────────────────────── */
const Icon = ({ d, d2 }: { d: string; d2?: string }) => (
  <svg
    width={18}
    height={18}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    viewBox="0 0 24 24"
    style={{ flexShrink: 0 }}
  >
    <path d={d} />
    {d2 && <path d={d2} />}
  </svg>
);

const icons: Record<string, React.ReactNode> = {
  dashboard: <Icon d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />,
  products: <Icon d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />,
  categories: <Icon d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />,
  tags: <Icon d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />,
  orders: <Icon d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />,
  delivery: <Icon d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />,
  profile: <Icon d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />,
  collapse: <Icon d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />,
  logout: <Icon d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />,
  menu: <Icon d="M4 6h16M4 12h16M4 18h16" />,
  discount: <Icon d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />,
  support: <Icon d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />,
};

/* ─── Styles ─────────────────────────────────────────────────────── */
const s = {
  root: {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100vh',
    overflow: 'hidden',
    fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
    background: '#f1f5f9',
  },
  header: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    height: HEADER_H,
    background: '#ffffff',
    borderBottom: '1px solid #e2e8f0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 20px',
    zIndex: 100,
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: 12 },
  headerRight: { display: 'flex', alignItems: 'center', gap: 12 },
  brandText: {
    fontWeight: 700,
    fontSize: 16,
    color: '#1e293b',
    letterSpacing: '-0.3px',
  },
  brandBadge: {
    fontSize: 10,
    fontWeight: 600,
    background: '#6366f1',
    color: '#fff',
    padding: '2px 7px',
    borderRadius: 20,
    letterSpacing: '0.5px',
    textTransform: 'uppercase' as const,
  },
  userChip: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 12px',
    borderRadius: 8,
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    fontSize: 13,
    fontWeight: 500,
    color: '#475569',
  },
  avatarCircle: {
    width: 28,
    height: 28,
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #6366f1, #818cf8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 12,
    fontWeight: 700,
    color: '#fff',
  },
  iconBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '7px 12px',
    borderRadius: 8,
    border: '1px solid #e2e8f0',
    background: '#f8fafc',
    cursor: 'pointer' as const,
    fontSize: 13,
    fontWeight: 500,
    color: '#64748b',
    transition: 'all 0.15s',
  },
  sidebar: (collapsed: boolean) => ({
    position: 'fixed' as const,
    top: HEADER_H,
    left: 0,
    width: collapsed ? SIDEBAR_COLLAPSED : SIDEBAR_EXPANDED,
    height: `calc(100vh - ${HEADER_H}px)`,
    background: '#1a1d27',
    borderRight: '1px solid #252836',
    display: 'flex',
    flexDirection: 'column' as const,
    transition: 'width 0.22s cubic-bezier(0.4,0,0.2,1)',
    zIndex: 90,
    overflowX: 'hidden' as const,
    overflowY: 'auto' as const,
  }),
  sidebarTop: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    padding: '10px 8px 6px',
    borderBottom: '1px solid #252836',
  },
  collapseBtn: {
    width: 32,
    height: 32,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    border: 'none',
    background: 'transparent',
    color: '#64748b',
    cursor: 'pointer' as const,
    transition: 'background 0.15s, color 0.15s',
  },
  navArea: { flex: 1, padding: '8px 8px 16px', overflowY: 'auto' as const },
  navItem: (active: boolean, collapsed: boolean) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: collapsed ? '10px 0' : '9px 12px',
    justifyContent: collapsed ? 'center' : 'flex-start',
    borderRadius: 8,
    marginBottom: 2,
    cursor: 'pointer' as const,
    transition: 'background 0.15s, color 0.15s',
    background: active ? 'rgba(99,102,241,0.18)' : 'transparent',
    color: active ? '#a5b4fc' : '#94a3b8',
    fontWeight: active ? 600 : 400,
    fontSize: 13,
    border: 'none',
    width: '100%',
    textAlign: 'left' as const,
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden' as const,
    textOverflow: 'ellipsis' as const,
    position: 'relative' as const,
  }),
  navLabel: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const },
  activeBar: {
    position: 'absolute' as const,
    left: 0,
    top: '50%',
    transform: 'translateY(-50%)',
    width: 3,
    height: '60%',
    borderRadius: '0 3px 3px 0',
    background: '#6366f1',
  },
  content: (collapsed: boolean) => ({
    marginLeft: collapsed ? SIDEBAR_COLLAPSED : SIDEBAR_EXPANDED,
    marginTop: HEADER_H,
    height: `calc(100vh - ${HEADER_H}px)`,
    overflowY: 'auto' as const,
    transition: 'margin-left 0.22s cubic-bezier(0.4,0,0.2,1)',
    background: '#f1f5f9',
  }),
  mobileOverlay: {
    position: 'fixed' as const,
    inset: 0,
    top: HEADER_H,
    background: 'rgba(0,0,0,0.5)',
    zIndex: 89,
  },
  hamburger: {
    display: 'none' as const,
    alignItems: 'center',
    justifyContent: 'center',
    width: 36,
    height: 36,
    borderRadius: 8,
    border: 'none',
    background: '#f1f5f9',
    cursor: 'pointer' as const,
    color: '#475569',
  },
};

export default function SellerAdminLayout({ children }: SellerAdminLayoutProps) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('seller-sidebar-collapsed');
      if (saved !== null) setCollapsed(saved === 'true');
    } catch (e) { logger.warn("Silent catch block:", e);  }
  }, []);

  const toggleCollapse = () =>
    setCollapsed((c) => {
      try { localStorage.setItem('seller-sidebar-collapsed', String(!c)); } catch (e) { logger.warn("Silent catch block:", e);  }
      return !c;
    });

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const navTo = (path: string) => {
    router.push(path);
    setMobileOpen(false);
  };

  const isActive = (path: string) =>
    path === '/seller-admin'
      ? pathname === '/seller-admin' || pathname === '/seller-admin/'
      : pathname.startsWith(path);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', path: '/seller-admin', icon: icons.dashboard },
    { id: 'products', label: 'Products', path: '/seller-admin/products', icon: icons.products },
    { id: 'categories', label: 'Categories', path: '/seller-admin/categories', icon: icons.categories },
    { id: 'category-tags', label: 'Category Tags', path: '/seller-admin/category-tags', icon: icons.tags },
    { id: 'orders', label: 'Orders', path: '/seller-admin/orders', icon: icons.orders },
    { id: 'sla', label: 'SLA', path: '/seller-admin/sla', icon: icons.delivery },
    { id: 'delivery-settings', label: 'Delivery Settings', path: '/seller-admin/delivery-settings', icon: icons.delivery },
    { id: 'reports', label: 'Reports', path: '/seller-admin/reports', icon: icons['business-stats'] || icons.orders },
    { id: 'analytics', label: 'Analytics', path: '/seller-admin/analytics', icon: <Icon d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /> },
    ...(user?.sellerPermissions?.allowDeliverySlots
      ? [{ id: 'delivery-slots', label: 'Delivery Slots', path: '/seller-admin/delivery-slots', icon: icons.delivery }]
      : []),
    { id: 'valet-scheduler', label: 'Valet Scheduler', path: '/seller-admin/valet-scheduler', icon: icons.delivery },
    { id: 'discounts', label: 'Discounts', path: '/seller-admin/discounts', icon: icons.discount },
    { id: 'requests', label: 'Raise Request', path: '/seller-admin/requests', icon: icons.support },
    { id: 'profile', label: 'Profile', path: '/seller-admin/profile', icon: icons.profile },
  ];

  const initials = (user?.name || 'S')
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();

  return (
    <div style={s.root}>
      {/* ─── Header ──────────────────────────────────────── */}
      <header style={s.header}>
        <div style={s.headerLeft}>
          <button
            style={{ ...s.hamburger, display: 'flex' }}
            className="seller-hamburger"
            onClick={() => setMobileOpen((o) => !o)}
            aria-label="Toggle sidebar"
          >
            {icons.menu}
          </button>
          <span style={s.brandText}>Seller Portal</span>
          <span style={s.brandBadge}>Admin</span>
        </div>
        <div style={s.headerRight}>
          <div style={s.userChip}>
            <div style={s.avatarCircle}>{initials}</div>
            <span className="seller-username">{user?.name || 'Seller'}</span>
          </div>
          <button style={s.iconBtn} onClick={handleLogout} title="Logout">
            {icons.logout}
            <span className="seller-logout-label">Logout</span>
          </button>
        </div>
      </header>

      {/* ─── Sidebar ─────────────────────────────────────── */}
      <aside style={s.sidebar(collapsed)} className={mobileOpen ? 'seller-sidebar-open' : ''}>
        <div style={s.sidebarTop}>
          <button
            style={{ ...s.collapseBtn, transform: collapsed ? 'rotate(180deg)' : 'none' }}
            onClick={toggleCollapse}
            title={collapsed ? 'Expand' : 'Collapse'}
          >
            {icons.collapse}
          </button>
        </div>
        <nav style={s.navArea}>
          {navItems.map((item) => {
            const active = isActive(item.path);
            return (
              <button
                key={item.id}
                style={s.navItem(active, collapsed)}
                onClick={() => navTo(item.path)}
                title={collapsed ? item.label : undefined}
              >
                {active && <span style={s.activeBar} />}
                {item.icon}
                {!collapsed && <span style={s.navLabel}>{item.label}</span>}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div style={s.mobileOverlay} onClick={() => setMobileOpen(false)} aria-hidden />
      )}

      {/* ─── Main content ────────────────────────────────── */}
      <main style={s.content(collapsed)}>{children}</main>

      <style>{`
        @media (max-width: 768px) {
          .seller-hamburger { display: flex !important; }
          .seller-username { display: none; }
          .seller-logout-label { display: none; }
          aside[style] {
            transform: translateX(-100%);
            width: ${SIDEBAR_EXPANDED}px !important;
            transition: transform 0.22s ease, width 0.22s ease !important;
          }
          aside.seller-sidebar-open {
            transform: translateX(0) !important;
          }
          main[style] {
            margin-left: 0 !important;
          }
        }
        @media (min-width: 769px) {
          .seller-hamburger { display: none !important; }
        }
        aside::-webkit-scrollbar { width: 4px; }
        aside::-webkit-scrollbar-track { background: transparent; }
        aside::-webkit-scrollbar-thumb { background: #2d3148; border-radius: 4px; }
      `}</style>
    </div>
  );
}
