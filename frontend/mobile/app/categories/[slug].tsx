import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import ProductsList from '../products';
import api from '../../src/api/client';
import { useAuth } from '../../src/hooks/useAuth';
import { ProductsListSkeleton } from '../../src/components/SkeletonLoader';

interface CategoryInfo {
  _id?: string;
  name: string;
  slug?: string;
  images?: string[];
  subCategories?: string[];
}

export default function CategoryDetailPage() {
  const params = useLocalSearchParams();
  const { user } = useAuth();
  const slug =
    typeof params.slug === 'string'
      ? params.slug
      : Array.isArray(params.slug)
        ? params.slug[0]
        : '';
  const initialSubCategory = typeof params.subCategory === 'string' ? params.subCategory : '';

  const [categoryInfo, setCategoryInfo] = useState<CategoryInfo | null>(null);
  const [banners, setBanners] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCategory = async () => {
      if (!slug) {
        setLoading(false);
        return;
      }
      try {
        const [catRes, bannerRes] = await Promise.all([
          api.get('/categories/public'),
          api
            .get('/banners/public', {
              params: {
                pageType: 'Category',
                pageId: slug,
                userRole: user?.role || 'guest',
              },
            })
            .catch(() => ({ data: [] })),
        ]);

        const list = Array.isArray(catRes.data)
          ? catRes.data
          : catRes.data?.data || catRes.data?.categories || [];
        const match =
          list.find((c: any) => (c?.slug || c?.name || '').toLowerCase() === slug.toLowerCase()) ||
          list.find((c: any) => (c?.name || '').toLowerCase() === slug.toLowerCase());
        if (match) {
          setCategoryInfo({
            _id: match._id,
            name: match.name || slug,
            slug: match.slug,
            images: match.images || [],
            subCategories: match.subCategories || [],
          });
        } else {
          setCategoryInfo({ name: slug });
        }

        const activeBanners = (bannerRes.data || []).filter((b: any) => b.isActive);
        setBanners(activeBanners);
      } catch {
        setCategoryInfo({ name: slug });
      } finally {
        setLoading(false);
      }
    };
    loadCategory();
  }, [slug, user?.role]);

  if (loading) {
    return (
      <SafeAreaView className="flex-1 bg-neutral-50">
        <ProductsListSkeleton />
      </SafeAreaView>
    );
  }

  const categoryName = categoryInfo?.name || slug;

  return (
    <View className="flex-1 bg-neutral-50">
      <ProductsList
        category={categoryName}
        subCategory={initialSubCategory}
        pageMode="category"
        title={categoryName}
        headerImage={categoryInfo?.images?.[0]}
        banners={banners}
      />
    </View>
  );
}
