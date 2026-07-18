'use client';

import { usePathname } from 'next/navigation';
import MobileHeader from '@/components/MobileComponents/MobileHeader';
import AndroidAppBanner from '@/components/AndroidAppBanner';
import BottomNav from '@/components/MobileComponents/BottomNav';

export default function AppChrome() {
  const pathname = usePathname();
  const isAdmin = pathname?.startsWith('/admin');

  if (isAdmin) {
    return null;
  }

  return (
    <>
      <MobileHeader />
      <AndroidAppBanner />
      <BottomNav />
    </>
  );
}
