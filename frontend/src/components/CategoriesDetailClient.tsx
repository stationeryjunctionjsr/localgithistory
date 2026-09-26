'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import api from '@/utils/api';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import ProductCatalog from '@/components/ProductCatalog';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { useAuth } from '@/context/AuthContext';
import { logger } from '@/utils/logger';

interface CategoryInfo {
  id?: string;
  name: string;
  slug?: string;
  images?: string[];
  subCategories?: string[];
  isReturnable?: boolean;
}

export interface CategoriesDetailClientProps {
  initialCategoryInfo?: CategoryInfo | null;
  initialBanners?: any[];
}

export default function CategoriesDetailClient({
  initialCategoryInfo,
  initialBanners,
}: CategoriesDetailClientProps) {
  const params = useParams();
  const searchParams = useSearchParams();
  const slugParam =
    typeof params.slug === 'string'
      ? params.slug
      : Array.isArray(params.slug)
        ? params.slug[0]
        : '';
  const slug = decodeURIComponent(slugParam);
  const initialSub = searchParams.get('subCategory') || '';
  const [categoryInfo, setCategoryInfo] = useState<CategoryInfo | null>(
    initialCategoryInfo || null
  );
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [subCategory, setSubCategory] = useState(initialSub);
  const { user } = useAuth();

  useEffect(() => {
    const loadCategory = async () => {
      if (!slug) return;
      if (initialCategoryInfo) return; // SSR data provided
      try {
        const res = await api.get('/categories/public');
        const list = Array.isArray(res.data)
          ? res.data
          : res.data?.data || res.data?.categories || [];
        const match =
          list.find((c: any) => (c?.slug || c?.name || '').toLowerCase() === slug.toLowerCase()) ||
          list.find((c: any) => (c?.name || '').toLowerCase() === slug.toLowerCase());
        if (match) {
          setCategoryInfo({
            id: match.id,
            name: match.name || slug,
            slug: match.slug,
            images: match.images || [],
            subCategories: match.subCategories || [],
            isReturnable: match.isReturnable || false,
          });
        } else {
          setCategoryInfo({ name: slug });
        }
      } catch {
        setCategoryInfo({ name: slug });
      }
    };
    loadCategory();
  }, [slug, initialCategoryInfo]);

  // eslint-disable-next-line unused-imports/no-unused-vars
  const subCategories = useMemo(() => categoryInfo?.subCategories || [], [categoryInfo]);
  const basePath = user?.role === 'wholesaler' ? '/wholesaler' : '/customer';
  const [banners, setBanners] = useState<any[]>(initialBanners || []);

  useEffect(() => {
    const fetchBanners = async () => {
      if (initialBanners && initialBanners.length > 0) return;
      try {
        const res = await api.get('/banners/public', {
          params: {
            pageType: 'Category',
            pageId: slug,
            userRole: user?.role || 'customer',
          },
        });
        setBanners(res.data || []);
      } catch (err) {
        logger.error('Banner fetch error:', err);
      }
    };
    fetchBanners();
  }, [slug, user?.role, initialBanners]);

  const breadcrumbs = [
    { label: 'Home', href: user ? basePath : '/' },
    { label: 'Categories', href: '/categories' },
    { label: categoryInfo?.name || slug },
  ];

  return (
    <div className="font-inter min-h-screen bg-white pb-20 md:pb-0">
      <Header />

      <div>
        {/* Hero Section */}
        <HeroBanner
          banners={banners}
          thumbnailUrl={
            categoryInfo?.images && categoryInfo.images.length > 0
              ? getImageUrlWithFallback(categoryInfo.images[0])
              : undefined
          }
          title={categoryInfo?.name || slug}
          subtitle={categoryInfo?.name ? 'Browse products in this category' : ''}
          breadcrumbs={breadcrumbs}
          fallbackInitial={categoryInfo?.name?.charAt(0)?.toUpperCase() || 'C'}
        />

        {/* Product Catalog */}
        <div className="mt-4">
          <ProductCatalog
            category={categoryInfo?.slug || categoryInfo?.name || slug}
            subCategory={subCategory}
            showFilters={true}
            hideSubCategoryFilters={true}
            pageMode="category"
            basePath={basePath}
            hideHeader={true}
          />
        </div>
      </div>
    </div>
  );
}
