'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function CustomerSupportRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/support');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="animate-pulse font-bold text-emerald-600">Redirecting to Support...</div>
    </div>
  );
}
