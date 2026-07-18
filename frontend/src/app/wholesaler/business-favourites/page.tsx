import { Suspense } from 'react';
import { Metadata } from 'next';
import FavouritesPageClient from '@/components/FavouritesPageClient';

export const metadata: Metadata = {
  title: 'Business Favourites | Stationery Junction Wholesale',
  description: 'Top products ordered by wholesalers, ranked by sales volume. Filter by category, brand, city, and more.',
};

export default function BusinessFavouritesPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50 text-xs uppercase tracking-widest text-[#1a4d33]">
          Loading...
        </div>
      }
    >
      <FavouritesPageClient type="business" />
    </Suspense>
  );
}
