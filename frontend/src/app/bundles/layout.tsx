import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Bundles | Stationery Junction',
  description:
    'Explore curated stationery bundles and combo packs at Stationery Junction — great value deals on premium art and writing supplies.',
  alternates: { canonical: 'https://www.stationeryjunction.com/bundles' },
  openGraph: {
    title: 'Bundles | Stationery Junction',
    description:
      'Explore curated stationery bundles and combo packs at Stationery Junction — great value deals on premium art and writing supplies.',
    url: 'https://www.stationeryjunction.com/bundles',
    siteName: 'Stationery Junction',
    type: 'website',
  },
};

export default function BundlesLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
