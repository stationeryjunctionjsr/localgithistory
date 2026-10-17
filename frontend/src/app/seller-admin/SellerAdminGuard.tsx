'use client';

import { useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import SellerAdminLayout from '@/components/SellerAdmin/SellerAdminLayout';

/**
 * Client-side auth guard for the seller-admin segment.
 * Extracted from layout.tsx so that layout.tsx can remain a Server Component
 * and export `metadata` (including noindex).
 */
export default function SellerAdminGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (
      !loading &&
      (!user ||
        ((user.role as string) !== 'seller' &&
          !(user.role === 'wholesaler' && (user as any).isSellerAdmin)))
    ) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: '#f8fafc',
        }}
      >
        <div
          style={{
            width: 44,
            height: 44,
            border: '4px solid #e2e8f0',
            borderTopColor: '#6366f1',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (
    !user ||
    ((user.role as string) !== 'seller' &&
      !(user.role === 'wholesaler' && (user as any).isSellerAdmin))
  ) {
    return null;
  }

  return <SellerAdminLayout>{children}</SellerAdminLayout>;
}
