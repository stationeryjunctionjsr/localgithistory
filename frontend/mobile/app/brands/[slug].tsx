import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import ProductsList from '../products';
import api from '../../src/api/client';
import { useAuth } from '../../src/hooks/useAuth';
import { ProductsListSkeleton } from '../../src/components/SkeletonLoader';

interface BrandInfo {
  _id?: string;
  name: string;
  logoUrl?: string;
  logo?: string;
}

export default function BrandDetailPage() {
  const params = useLocalSearchParams();
  const { user } = useAuth();
  const slug =
    typeof params.slug === 'string'
      ? params.slug
      : Array.isArray(params.slug)
        ? params.slug[0]
        : '';

  const [brandInfo, setBrandInfo] = useState<BrandInfo | null>(null);
  const [banners, setBanners] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadBrand = async () => {
      if (!slug) {
        setLoading(false);
        return;
      }
      try {
        const [brandRes, bannerRes] = await Promise.all([
          api.get('/brands/public'),
          api
            .get('/banners/public', {
              params: {
                pageType: 'Brand',
                pageId: slug,
                userRole: user?.role || 'guest',
              },
            })
            .catch(() => ({ data: [] })),
        ]);

        const list = Array.isArray(brandRes.data)
          ? brandRes.data
          : brandRes.data?.brands || brandRes.data?.data || [];
        const match = list.find((b: any) => (b?.name || '').toLowerCase() === slug.toLowerCase());
        if (match) {
          setBrandInfo({
            _id: match._id,
            name: match.name || slug,
            logoUrl: match.logoUrl,
            logo: match.logo,
          });
        } else {
          setBrandInfo({ name: slug });
        }

        const activeBanners = (bannerRes.data || []).filter((b: any) => b.isActive);
        setBanners(activeBanners);
      } catch {
        setBrandInfo({ name: slug });
      } finally {
        setLoading(false);
      }
    };
    loadBrand();
  }, [slug, user?.role]);

  if (loading) {
    return (
      <SafeAreaView className="flex-1 bg-neutral-50">
        <ProductsListSkeleton />
      </SafeAreaView>
    );
  }

  const brandName = brandInfo?.name || slug;
  const brandImage = brandInfo?.logoUrl || brandInfo?.logo;

  return (
    <View className="flex-1 bg-neutral-50">
      <ProductsList
        brand={brandName}
        pageMode="brand"
        title={brandName}
        headerImage={brandImage}
        banners={banners}
      />
    </View>
  );
}
