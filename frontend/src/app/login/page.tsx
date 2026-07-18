'use client';

/**
 * /login route — redirect coordinator only.
 *
 * Login and registration happen via the AuthModal on /landingpage.
 * This route exists to handle:
 *  - Session-expiry redirects from the API client (onUnauthorized)
 *  - Any external links pointing to /login
 *
 * All visitors are redirected to their appropriate destination.
 */

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

function LoginRedirect() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (authLoading) return;

    if (user) {
      const role = user.effectiveRole || user.role;
      switch (role) {
        case 'super_admin': router.replace('/admin'); break;
        case 'wholesaler':  router.replace('/wholesaler'); break;
        case 'customer':    router.replace('/customer'); break;
        case 'valet':       router.replace('/valet'); break;
        default:            router.replace('/');
      }
    } else {
      // Not logged in — go to landing page where the auth modal lives.
      // Preserve any mode param so the landing page can open the right tab.
      const mode = searchParams?.get('mode');
      const dest = mode ? `/?openAuth=true&mode=${mode}` : '/';
      router.replace(dest);
    }
  }, [user, authLoading, router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center gap-3 text-gray-500">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600" />
        <p className="text-sm">Redirecting…</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600" />
        </div>
      }
    >
      <LoginRedirect />
    </Suspense>
  );
}
