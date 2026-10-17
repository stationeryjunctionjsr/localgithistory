import type { Metadata } from 'next';
import SellerAdminGuard from './SellerAdminGuard';

export const metadata: Metadata = {
  title: 'Seller Admin | Stationery Junction',
  robots: { index: false, follow: false },
};

export default function SellerAdminRootLayout({ children }: { children: React.ReactNode }) {
  return <SellerAdminGuard>{children}</SellerAdminGuard>;
}
