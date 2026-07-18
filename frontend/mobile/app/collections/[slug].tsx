import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import ProductsList from '../products';
import api from '../../src/api/client';
import { useAuth } from '../../src/hooks/useAuth';
import { ProductsListSkeleton } from '../../src/components/SkeletonLoader';

interface CollectionInfo {
  _id?: string;
  name: string;
  imageUrl?: string;
  image?: string;
}

export default function CollectionDetailPage() {
  const params = useLocalSearchParams();
  const { user } = useAuth();
  const slug =
    typeof params.slug === 'string'
      ? params.slug
      : Array.isArray(params.slug)
        ? params.slug[0]
        : '';

  const [collectionInfo, setCollectionInfo] = useState<CollectionInfo | null>(null);
  const [banners, setBanners] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCollection = async () => {
      if (!slug) {
        setLoading(false);
        return;
      }
      try {
        const [colRes, bannerRes] = await Promise.all([
          api.get('/collections/public'),
          api
            .get('/banners/public', {
              params: {
                pageType: 'Collection',
                pageId: slug,
                userRole: user?.role || 'guest',
              },
            })
            .catch(() => ({ data: [] })),
        ]);

        const list = Array.isArray(colRes.data) ? colRes.data : colRes.data?.data || [];
        const match = list.find(
          (c: any) => c?._id === slug || (c?.name || '').toLowerCase() === slug.toLowerCase()
        );
        if (match) {
          setCollectionInfo({
            _id: match._id,
            name: match.name || slug,
            imageUrl: match.imageUrl,
            image: match.image,
          });
        } else {
          setCollectionInfo({ name: slug });
        }

        const activeBanners = (bannerRes.data || []).filter((b: any) => b.isActive);
        setBanners(activeBanners);
      } catch {
        setCollectionInfo({ name: slug });
      } finally {
        setLoading(false);
      }
    };
    loadCollection();
  }, [slug, user?.role]);

  if (loading) {
    return (
      <SafeAreaView className="flex-1 bg-neutral-50">
        <ProductsListSkeleton />
      </SafeAreaView>
    );
  }

  const collectionName = collectionInfo?.name || slug;
  const collectionImage = collectionInfo?.imageUrl || collectionInfo?.image;
  const collectionId = collectionInfo?._id || slug;

  return (
    <View className="flex-1 bg-neutral-50">
      <ProductsList
        collection={collectionId}
        pageMode="collection"
        title={collectionName}
        headerImage={collectionImage}
        banners={banners}
      />
    </View>
  );
}
