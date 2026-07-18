import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  StyleSheet,
  Dimensions,
  ViewStyle,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { getImageUrl } from '../api/client';
import { colors, borderRadius } from '../theme';
import { LinearGradient } from 'expo-linear-gradient';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export interface BannerItem {
  _id?: string;
  title?: string;
  imageUrl?: string;
  image?: string;
  linkUrl?: string;
  link?: string;
  isActive?: boolean;
}

interface BannerCarouselProps {
  banners: BannerItem[];
  height?: number;
  autoPlayInterval?: number;
  horizontalPadding?: number;
  style?: ViewStyle;
}

export const BannerCarousel: React.FC<BannerCarouselProps> = ({
  banners,
  height = 180,
  autoPlayInterval = 4000,
  horizontalPadding = 16,
  style,
}) => {
  const router = useRouter();
  const flatListRef = useRef<FlatList>(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  const bannerWidth = SCREEN_WIDTH - horizontalPadding * 2;
  const snapInterval = bannerWidth + 12;

  const handleBannerPress = useCallback(
    (banner: BannerItem) => {
      const url = banner.linkUrl || banner.link;
      if (url) {
        if (url.startsWith('http://') || url.startsWith('https://')) {
          Linking.openURL(url);
        } else {
          router.push(url as any);
        }
      }
    },
    [router]
  );

  useEffect(() => {
    if (banners.length <= 1 || !autoPlayInterval) return;
    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        const next = (prev + 1) % banners.length;
        flatListRef.current?.scrollToIndex({ index: next, animated: true });
        return next;
      });
    }, autoPlayInterval);
    return () => clearInterval(interval);
  }, [banners.length, autoPlayInterval]);

  if (!banners || banners.length === 0) {
    return (
      <View style={[styles.container, style, { paddingHorizontal: horizontalPadding }]}>
        <View style={[styles.bannerItem, { width: SCREEN_WIDTH - horizontalPadding * 2, height: 220 }]}>
          <LinearGradient
            colors={['#1f2937', '#111827', '#000000']}
            style={StyleSheet.absoluteFillObject}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          />
          <View style={styles.fallbackContent}>
            <Text style={styles.fallbackTagline}>PREMIUM STATIONERY</Text>
            <Text style={styles.fallbackTitle}>Elevate Your</Text>
            <Text style={styles.fallbackTitleHighlight}>Workspace</Text>
            <Text style={styles.fallbackSubtitle}>
              Discover our curated collection of premium stationery designed to inspire creativity and productivity.
            </Text>
            <View style={styles.fallbackActions}>
              <TouchableOpacity
                onPress={() => router.push('/products')}
                style={styles.fallbackButtonPrimary}
              >
                <Text style={styles.fallbackButtonPrimaryText}>VISIT SHOP</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => router.push('/(tabs)/brands')}
                style={styles.fallbackButtonSecondary}
              >
                <Text style={styles.fallbackButtonSecondaryText}>BRANDS</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </View>
    );
  }

  const renderItem = ({ item }: { item: BannerItem }) => (
    <TouchableOpacity
      activeOpacity={0.95}
      onPress={() => handleBannerPress(item)}
      style={[styles.bannerItem, { width: bannerWidth, height }]}
    >
      <Image
        source={{ uri: getImageUrl(item.imageUrl || item.image || '') }}
        style={styles.bannerImage}
        resizeMode="cover"
      />
      <View style={styles.bannerOverlay} />
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, style]}>
      <FlatList
        ref={flatListRef}
        data={banners}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        keyExtractor={(item, idx) => item._id || String(idx)}
        contentContainerStyle={{ paddingHorizontal: horizontalPadding }}
        snapToInterval={snapInterval}
        decelerationRate="fast"
        onScroll={(e) => {
          const idx = Math.round(e.nativeEvent.contentOffset.x / snapInterval);
          setCurrentIndex(idx);
        }}
        scrollEventThrottle={16}
        renderItem={renderItem}
        onScrollToIndexFailed={() => {}}
      />
      {banners.length > 1 && (
        <View style={styles.dots}>
          {banners.map((_, idx) => (
            <View
              key={idx}
              style={[styles.dot, idx === currentIndex ? styles.dotActive : styles.dotInactive]}
            />
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 24,
  },
  bannerItem: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    marginRight: 12,
  },
  bannerImage: {
    width: '100%',
    height: '100%',
  },
  bannerOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.1)',
  },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 12,
  },
  dot: {
    height: 4,
    borderRadius: 2,
    marginHorizontal: 3,
  },
  dotActive: {
    backgroundColor: colors.primary,
    width: 20,
  },
  dotInactive: {
    backgroundColor: colors.neutral[200],
    width: 8,
  },
  fallbackContent: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  fallbackTagline: {
    color: '#fb7185',
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  fallbackTitle: {
    color: '#ffffff',
    fontSize: 26,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  fallbackTitleHighlight: {
    color: '#f43f5e',
    fontSize: 26,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  fallbackSubtitle: {
    color: '#9ca3af',
    fontSize: 12,
    textAlign: 'center',
    marginBottom: 16,
    paddingHorizontal: 10,
    lineHeight: 18,
  },
  fallbackActions: {
    flexDirection: 'row',
    gap: 12,
  },
  fallbackButtonPrimary: {
    backgroundColor: '#f43f5e',
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 24,
  },
  fallbackButtonPrimaryText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  fallbackButtonSecondary: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 24,
  },
  fallbackButtonSecondaryText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
});
