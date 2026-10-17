import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Use | Stationery Junction',
  description:
    'Review the Terms of Use governing your access to and use of the Stationery Junction platform.',
  alternates: { canonical: 'https://www.stationeryjunction.com/terms-of-use' },
  openGraph: {
    title: 'Terms of Use | Stationery Junction',
    description:
      'Review the Terms of Use governing your access to and use of the Stationery Junction platform.',
    url: 'https://www.stationeryjunction.com/terms-of-use',
    siteName: 'Stationery Junction',
    type: 'website',
  },
};

export default function TermsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
