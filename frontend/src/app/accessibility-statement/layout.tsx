import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Accessibility Statement | Stationery Junction',
  description:
    'Stationery Junction is committed to digital accessibility. Read our accessibility statement and learn how we meet WCAG 2.1 standards.',
  alternates: { canonical: 'https://www.stationeryjunction.com/accessibility-statement' },
  openGraph: {
    title: 'Accessibility Statement | Stationery Junction',
    description:
      'Stationery Junction is committed to digital accessibility for all users.',
    url: 'https://www.stationeryjunction.com/accessibility-statement',
    siteName: 'Stationery Junction',
    type: 'website',
  },
};

export default function AccessibilityLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
