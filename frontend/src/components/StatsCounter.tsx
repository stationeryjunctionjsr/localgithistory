'use client';

import React from 'react';

/*
// Original implementation that fetched the entire product and brand catalog:
// This was changed to accept counts as props because fetching thousands of records
// just to display a count was a major performance bottleneck.
//
// import React, { useEffect, useState } from 'react';
// import api from '@/utils/api';
//
// export default function StatsCounter() {
//   const [stats, setStats] = useState({ products: 0, brands: 0 });
//
//   useEffect(() => {
//     const fetchStats = async () => {
//       try {
//         const [prodRes, brandRes] = await Promise.all([
//           api.get('/products/public'),
//           api.get('/brands/public'),
//         ]);
//
//         const products = prodRes.data.products || prodRes.data || [];
//         const brands = brandRes.data.brands || brandRes.data || [];
//
//         setStats({
//           products: products.length,
//           brands: brands.length,
//         });
//       } catch (error) {
//         console.error('Failed to fetch stats', error);
//       }
//     };
//     fetchStats();
//   }, []);
//
//   return (
//     ...
//   );
// }
*/

interface StatsCounterProps {
  productCount?: number;
  brandCount?: number;
}

export default function StatsCounter({ productCount = 0, brandCount = 0 }: StatsCounterProps) {
  return (
    <div className="w-full border-b border-gray-100 bg-white py-3">
      <div className="mx-auto flex max-w-[1200px] items-center justify-center gap-12 px-4 opacity-60 md:gap-24">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-gray-900 md:text-xl">{productCount}+</span>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500 md:text-xs">
            Premium Products
          </span>
        </div>
        <div className="h-6 w-px bg-gray-200" />
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-gray-900 md:text-xl">{brandCount}+</span>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500 md:text-xs">
            Trusted Brands
          </span>
        </div>
      </div>
    </div>
  );
}
