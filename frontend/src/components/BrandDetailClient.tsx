'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import api from '@/utils/api';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import ProductCatalog from '@/components/ProductCatalog';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { useAuth } from '@/context/AuthContext';
import { logger } from '@/utils/logger';

interface BrandInfo {
  _id?: string;
  name: string;
  logoUrl?: string;
  logo?: string;
  description?: string;
}

export interface BrandDetailClientProps {
  initialBrandInfo?: BrandInfo | null;
  initialBanners?: any[];
}

export default function BrandDetailClient({
  initialBrandInfo,
  initialBanners,
}: BrandDetailClientProps) {
  const params = useParams();
  const slug =
    typeof params.slug === 'string'
      ? params.slug
      : Array.isArray(params.slug)
        ? params.slug[0]
        : '';
  const [brandInfo, setBrandInfo] = useState<BrandInfo | null>(initialBrandInfo || null);
  const [banners, setBanners] = useState<any[]>(initialBanners || []);
  const { user } = useAuth();

  const effectiveRole = user?.effectiveRole || user?.role || 'guest';
  const basePath = user?.role === 'wholesaler' ? '/wholesaler' : '/customer';

  useEffect(() => {
    const loadBrand = async () => {
      if (!slug) return;
      if (initialBrandInfo) return; // Initial Data provided by SSR

      try {
        const res = await api.get('/brands/public');
        const list = Array.isArray(res.data) ? res.data : res.data?.brands || res.data?.data || [];
        const decoded = decodeURIComponent(slug);
        const match = list.find(
          (b: any) => (b?.name || '').toLowerCase() === decoded.toLowerCase()
        );
        if (match) {
          setBrandInfo({
            _id: match._id,
            name: match.name || decoded,
            logoUrl: match.logoUrl,
            logo: match.logo,
            description: match.description,
          });
        } else {
          setBrandInfo({ name: decoded });
        }
      } catch {
        setBrandInfo({ name: decodeURIComponent(slug) });
      }
    };
    loadBrand();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  // Fetch banners for this brand
  useEffect(() => {
    const fetchBanners = async () => {
      if (initialBanners && initialBanners.length > 0) return; // Overwrite Client-Fetching
      const brandName = brandInfo?.name || decodeURIComponent(slug);
      if (!brandName) return;
      try {
        const res = await api.get('/banners/public', {
          params: {
            pageType: 'Brand',
            pageId: brandName,
            userRole: effectiveRole,
          },
        });
        const activeBanners = (res.data || []).filter((b: any) => b.isActive);
        setBanners(activeBanners);
      } catch (error) {
        logger.error('Failed to fetch brand banners', error);
      }
    };
    if (brandInfo?.name || slug) fetchBanners();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brandInfo?.name, slug, effectiveRole]);

  const brandName = brandInfo?.name || decodeURIComponent(slug);
  const brandLogo = brandInfo?.logoUrl || brandInfo?.logo;

  const breadcrumbs = [
    { label: 'Home', href: user ? basePath : '/' },
    { label: 'Brands', href: '/brands' },
    { label: brandName },
  ];

  // Banner URL
  // eslint-disable-next-line unused-imports/no-unused-vars
  const heroBannerUrl =
    banners.length > 0
      ? getImageUrlWithFallback(banners[0]?.imageUrl || banners[0]?.image)
      : undefined;
  // eslint-disable-next-line unused-imports/no-unused-vars
  const heroBannerLink = banners.length > 0 && banners[0]?.link ? banners[0].link : undefined;

  return (
    <div className="font-inter min-h-screen bg-white pb-20 md:pb-0">
      <Header />

      <div>
        {/* Hero Section */}
        <div className="w-full">
          <HeroBanner
            banners={banners}
            thumbnailUrl={brandLogo ? getImageUrlWithFallback(brandLogo) : undefined}
            title={brandName}
            subtitle={brandInfo?.description || `Browse all products by ${brandName}`}
            breadcrumbs={breadcrumbs}
            fallbackInitial={brandName?.charAt(0)?.toUpperCase() || 'B'}
          />
        </div>

        {/* Product Catalog */}
        <div className="mt-4">
          <ProductCatalog
            brand={brandName}
            showFilters={true}
            pageMode="brand"
            basePath={basePath}
            hideHeader={true}
          />
        </div>
      </div>
    </div>
  );
}
