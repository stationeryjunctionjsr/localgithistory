import type { Metadata } from 'next';
import AdminLayout from '@/components/Admin/AdminLayout';

export const metadata: Metadata = {
  title: 'Admin | Stationery Junction',
  robots: { index: false, follow: false },
};

export default function AdminRootLayout({ children }: { children: React.ReactNode }) {
  return <AdminLayout>{children}</AdminLayout>;
}
