'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import api from '@/utils/api';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import ProductCatalog from '@/components/ProductCatalog';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { useAuth } from '@/context/AuthContext';

interface CollectionInfo {
  _id?: string;
  name: string;
  description?: string;
  imageUrl?: string;
  image?: string;
}

export interface CollectionDetailClientProps {
  initialCollectionInfo?: CollectionInfo | null;
  initialBanners?: any[];
}

export default function CollectionDetailClient({
  initialCollectionInfo,
  initialBanners,
}: CollectionDetailClientProps) {
  const params = useParams();
  const slug =
    typeof params.slug === 'string'
      ? params.slug
      : Array.isArray(params.slug)
        ? params.slug[0]
        : '';
  const [collectionInfo, setCollectionInfo] = useState<CollectionInfo | null>(
    initialCollectionInfo || null
  );
  const [banners, setBanners] = useState<any[]>(initialBanners || []);
  const { user } = useAuth();

  useEffect(() => {
    const loadCollection = async () => {
      if (!slug) return;
      if (initialCollectionInfo) return; // Initial Data provided by SSR

      try {
        const res = await api.get('/collections/public');
        const list = Array.isArray(res.data) ? res.data : res.data?.data || [];
        const decoded = decodeURIComponent(slug);
        const match = list.find(
          (c: any) => c?._id === decoded || (c?.name || '').toLowerCase() === decoded.toLowerCase()
        );
        if (match) {
          setCollectionInfo({
            _id: match._id,
            name: match.name || decoded,
            description: match.description,
            imageUrl: match.imageUrl,
            image: match.image,
          });
        } else {
          setCollectionInfo({ name: decoded });
        }
      } catch {
        setCollectionInfo({ name: decodeURIComponent(slug) });
      }
    };
    loadCollection();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  useEffect(() => {
    const fetchBanners = async () => {
      if (initialBanners && initialBanners.length > 0) return; // Overwrite Client-Fetching
      try {
        const res = await api.get('/banners/public', {
          params: {
            pageType: 'Collection',
            pageId: slug,
            userRole: user?.role || 'customer',
          },
        });
        setBanners(res.data || []);
      } catch {
        // No banners available
      }
    };
    fetchBanners();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, user?.role]);

  const collectionName = collectionInfo?.name || decodeURIComponent(slug);
  const collectionImage = collectionInfo?.imageUrl || collectionInfo?.image;
  const collectionId = collectionInfo?._id || slug;
  const basePath = user?.role === 'wholesaler' ? '/wholesaler' : '/customer';

  const breadcrumbs = [
    { label: 'Home', href: user ? basePath : '/' },
    { label: collectionName },
  ];

  return (
    <div className="font-inter min-h-screen bg-white pb-20 md:pb-0">
      <Header />

      <div>
        {/* Hero Section */}
        <HeroBanner
          banners={banners}
          thumbnailUrl={collectionImage ? getImageUrlWithFallback(collectionImage) : undefined}
          title={collectionName}
          subtitle={collectionInfo?.description || 'Curated collection'}
          breadcrumbs={breadcrumbs}
          fallbackInitial={collectionName?.charAt(0)?.toUpperCase() || 'C'}
        />

        {/* Product Catalog */}
        <div className="mt-4">
          <ProductCatalog
            collection={collectionId}
            showFilters={true}
            pageMode="collection"
            hideHeader={true}
          />
        </div>
      </div>
    </div>
  );
}
