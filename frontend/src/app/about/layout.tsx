import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'About Us | Stationery Junction',
  description:
    'Learn about Stationery Junction — our story, mission, and commitment to delivering premium stationery and art supplies across India.',
  alternates: { canonical: 'https://www.stationeryjunction.com/about' },
  openGraph: {
    title: 'About Us | Stationery Junction',
    description:
      'Learn about Stationery Junction — our story, mission, and commitment to delivering premium stationery and art supplies across India.',
    url: 'https://www.stationeryjunction.com/about',
    siteName: 'Stationery Junction',
    type: 'website',
  },
};

export default function AboutLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
