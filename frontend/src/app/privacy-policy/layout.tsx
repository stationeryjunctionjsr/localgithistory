import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy | Stationery Junction',
  description:
    'Read our Privacy Policy to understand how Stationery Junction collects, uses, and protects your personal information.',
  alternates: { canonical: 'https://www.stationeryjunction.com/privacy-policy' },
  openGraph: {
    title: 'Privacy Policy | Stationery Junction',
    description:
      'Read our Privacy Policy to understand how Stationery Junction collects, uses, and protects your personal information.',
    url: 'https://www.stationeryjunction.com/privacy-policy',
    siteName: 'Stationery Junction',
    type: 'website',
  },
};

export default function PrivacyPolicyLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
