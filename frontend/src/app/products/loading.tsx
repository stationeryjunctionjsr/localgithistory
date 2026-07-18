import { ProductsPageSkeleton } from '@/components/PageSkeletons';

/** Shown by Next.js App Router during navigation to /products */
export default function Loading() {
  return <ProductsPageSkeleton />;
}
