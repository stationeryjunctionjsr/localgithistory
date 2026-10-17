import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'FAQ | Stationery Junction',
  description:
    'Frequently asked questions about orders, delivery, returns, and payments at Stationery Junction.',
  alternates: { canonical: 'https://www.stationeryjunction.com/faq' },
  openGraph: {
    title: 'FAQ | Stationery Junction',
    description:
      'Frequently asked questions about orders, delivery, returns, and payments at Stationery Junction.',
    url: 'https://www.stationeryjunction.com/faq',
    siteName: 'Stationery Junction',
    type: 'website',
  },
};

export default function FAQLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
