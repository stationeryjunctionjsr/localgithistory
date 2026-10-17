import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Customer Support | Stationery Junction',
  description:
    'Contact Stationery Junction support for help with your orders, returns, payments, or any other queries.',
  alternates: { canonical: 'https://www.stationeryjunction.com/support' },
  openGraph: {
    title: 'Customer Support | Stationery Junction',
    description:
      'Contact Stationery Junction support for help with your orders, returns, payments, or any other queries.',
    url: 'https://www.stationeryjunction.com/support',
    siteName: 'Stationery Junction',
    type: 'website',
  },
};

export default function SupportLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
