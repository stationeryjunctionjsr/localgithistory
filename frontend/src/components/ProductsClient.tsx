'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import ProductCatalog from '@/components/ProductCatalog';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

export default function ProductsClient() {
  // eslint-disable-next-line unused-imports/no-unused-vars
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const [banners, setBanners] = useState<any[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [loading, setLoading] = useState(true);

  const effectiveRole = user?.effectiveRole || user?.role || 'customer';
  const basePath = user?.role === 'wholesaler' ? '/wholesaler' : '/customer';

  useEffect(() => {
    const loadBanners = async () => {
      try {
        const bannerRes = await api.get('/banners/public/', {
          params: {
            position: 'products',
            pageType: 'all_products',
            userRole: effectiveRole,
          },
        });
        const activeBanners = (bannerRes.data || []).filter(
          (b: any) =>
            b.isActive && (b.targetAudience === 'all' || b.targetAudience === effectiveRole)
        );
        setBanners(activeBanners);
      } catch (e) {
        logger.error('Failed to fetch product banners', e);
      } finally {
        setLoading(false);
      }
    };
    loadBanners();
  }, [effectiveRole]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Hero Section */}
      <HeroBanner
        banners={banners}
        title="All Products"
        subtitle="Explore our entire collection of premium stationery"
        stat="Quality you can trust"
        breadcrumbs={[{ label: 'Home', href: user ? basePath : '/' }, { label: 'Products' }]}
        hideThumbnail={true}
      />

      {/* Main Content */}
      <main className="pb-20">
        <div className="w-full">
          <ProductCatalog
            showFilters={true}
            pageMode="general"
            hideHeader={false}
            searchTerm={searchParams.get('searchTerm') || ''}
            category={searchParams.get('category') || ''}
            brand={searchParams.get('brand') || ''}
            hideBreadcrumbs={true}
          />
        </div>
      </main>
    </div>
  );
}
