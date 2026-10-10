'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function CategoryHeadsRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/admin/super-categories');
  }, [router]);

  return (
    <div className="flex h-64 items-center justify-center">
      <div className="text-center">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent"></div>
        <p className="mt-2 text-sm text-gray-500">Redirecting to Super Categories...</p>
      </div>
    </div>
  );
}
