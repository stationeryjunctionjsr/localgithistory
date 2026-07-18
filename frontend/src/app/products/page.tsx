import ProductsClient from '@/components/ProductsClient';
import { Suspense } from 'react';
import { ProductsPageSkeleton } from '@/components/PageSkeletons';

export const metadata = {
  title: 'All Products | Stationery Junction',
  description: 'Explore our entire collection of premium stationery products at Stationery Junction.',
  alternates: { canonical: 'https://www.stationeryjunction.com/products' },
  openGraph: {
    title: 'All Products | Stationery Junction',
    description: 'Explore our entire collection of premium stationery products at Stationery Junction.',
    url: 'https://www.stationeryjunction.com/products',
    type: 'website',
  },
};

export default function ProductsPage() {
  return (
    <Suspense fallback={<ProductsPageSkeleton />}>
      <ProductsClient />
    </Suspense>
  );
}
