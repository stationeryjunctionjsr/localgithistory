import React, { useCallback, useRef, useState, useEffect } from 'react';
import { trackRecommendationEvent } from '../utils/analytics';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  FlatList,
  Image,
  StyleSheet,
  Animated,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import api, { getImageUrl } from '../api/client';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';
import { usePincode } from '../context/PincodeContext';
import { BannerCarousel, BannerItem } from './BannerCarousel';
import UnserviceableLocationCard from './UnserviceableLocationCard';
import { colors, spacing, borderRadius, shadows, typography } from '../theme';
import { formatDateIST } from '../utils/dateUtils';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface Scheme {
  _id: string;
  name: string;
  description?: string;
  discountType: string;
  discountValue: number;
  minOrderValue?: number;
  validUntil?: string;
  code?: string;
}

interface Collection {
  _id?: string;
  name?: string;
  imageUrl?: string;
  image?: string;
  slug?: string;
}

interface Brand {
  _id?: string;
  name?: string;
  logoUrl?: string;
}

interface Category {
  _id?: string;
  name?: string;
  slug?: string;
  images?: string[];
}

const BRAND_LOGO_SIZE = 72;
const COLLECTION_CARD_W = SCREEN_WIDTH * 0.55;

export default function WholesalerHomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { user } = useAuth();
  // Start at 1 so cached content is instantly visible; animate from 0 only on fresh load
  const fadeAnim = useRef(new Animated.Value(1)).current;

  const { data, isLoading: loading, refetch } = useQuery({
    queryKey: ['wholesaler-home', user?.role],
    queryFn: async () => {
      const role = user?.role;
      const [bannersRes, schemesRes, collectionsRes, brandsRes, categoriesRes] = await Promise.all([
        api
          .get('/banners/public', {
            params: { position: 'wholesaler', pageType: 'wholesaler', userRole: role },
          })
          .catch(() => ({ data: [] })),
        api.get('/schemes').catch(() => ({ data: [] })),
        api
          .get('/collections/public', { params: { visiblePage: 'Home', pageType: 'Home' } })
          .catch(() => ({ data: [] })),
        api.get('/brands/public').catch(() => ({ data: [] })),
        api
          .get('/categories/public', { params: { forHomepage: true } })
          .catch(() => ({ data: [] })),
      ]);

      const rawBanners: any[] = Array.isArray(bannersRes.data) ? bannersRes.data : [];
      let activeBanners = rawBanners.filter(
        (b) =>
          b.isActive !== false &&
          b.isPublished !== false &&
          (b.targetAudience === 'wholesaler' || b.targetAudience === 'all')
      );
      if (activeBanners.length === 0) {
        try {
          const fallback = await api.get('/banners/public', {
            params: { position: 'homepage', targetAudience: 'all' },
          });
          const fb: any[] = Array.isArray(fallback.data) ? fallback.data : [];
          activeBanners = fb.filter((b) => b.isActive !== false && b.isPublished !== false);
        } catch {
          activeBanners = [];
        }
      }

      const schemes = (Array.isArray(schemesRes.data) ? schemesRes.data : []).slice(0, 3);
      const cols = collectionsRes.data?.data || collectionsRes.data || [];
      const collections = Array.isArray(cols) ? cols : [];
      const rawBrands = Array.isArray(brandsRes.data) ? brandsRes.data : brandsRes.data?.brands || [];
      const brands = rawBrands.filter((b: Brand) => b.logoUrl);
      const rawCats = categoriesRes.data?.data || categoriesRes.data || [];
      const categories: Category[] = (Array.isArray(rawCats) ? rawCats : [])
        .filter((c: any) => c.isActive !== false)
        .slice(0, 8);

      return { banners: activeBanners, schemes, collections, brands, categories };
    },
  });

  const { data: recommendationsData } = useQuery({
    queryKey: ['wholesaler-recommendations'],
    queryFn: async () => {
      try {
        const res = await api.get('/recommendations');
        return res.data;
      } catch (err) {
        return null;
      }
    },
  });

  const banners = data?.banners || [];
  const schemes = data?.schemes || [];
  const collections = data?.collections || [];
  const brands = data?.brands || [];
  const categories = data?.categories || [];

  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  // Import useEffect for the animation trigger
  React.useEffect(() => {
    if (!loading) {
      Animated.spring(fadeAnim, { toValue: 1, friction: 10, useNativeDriver: true }).start();
    }
  }, [loading]);

  const { pincode, city, isServiceable, openModal } = usePincode();
  const companyName = user?.companyName || user?.name || 'Business Partner';
  const firstName = (user?.name || '').split(' ')[0] || 'there';

  // ─── Section: Header ──────────────────────────────────────────────────────
  const renderHeader = () => (
    <LinearGradient
      colors={['#0f3322', '#1a4d33', '#2d7a52']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.header, { paddingTop: insets.top + 12 }]}
    >
      <View style={styles.headerContent}>
        <View>
          <Text style={styles.headerGreeting}>Welcome back, {firstName}</Text>
          <Text style={styles.headerCompany} numberOfLines={1}>
            {companyName}
          </Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.headerIconBtn}
            onPress={() => router.push('/orders')}
          >
            <Ionicons name="receipt-outline" size={22} color="#fff" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.headerIconBtn}
            onPress={() => router.push('/wishlist')}
          >
            <Ionicons name="heart-outline" size={22} color="#fff" />
          </TouchableOpacity>
        </View>
      </View>
      {/* Badges row: Wholesale badge & Delivery Location */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <View style={styles.wholesaleBadge}>
          <Ionicons name="business-outline" size={12} color={colors.accent} />
          <Text style={styles.wholesaleBadgeText}>Business Account</Text>
        </View>

        <TouchableOpacity
          onPress={() => openModal(false)}
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 4,
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            paddingVertical: 4,
            paddingHorizontal: 10,
            borderRadius: 20,
            borderWidth: 1,
            borderColor: 'rgba(255, 255, 255, 0.25)',
          }}
          activeOpacity={0.8}
        >
          <Ionicons name="location-outline" size={12} color="#fff" />
          <Text style={{ color: '#fff', fontSize: 11, fontWeight: '600' }} numberOfLines={1}>
            Deliver to: {pincode || 'Select Pincode'}{city ? ` (${city})` : ''}
          </Text>
          <Ionicons name="chevron-down" size={10} color="#fff" />
        </TouchableOpacity>
      </View>
    </LinearGradient>
  );

  // ─── Section: Quick Actions ───────────────────────────────────────────────
  const quickActions = [
    {
      icon: 'storefront-outline' as const,
      label: 'Browse\nProducts',
      onPress: () => router.push('/products'),
      color: '#1a4d33',
    },
    {
      icon: 'pricetags-outline' as const,
      label: 'My\nSchemes',
      onPress: () => router.push('/schemes'),
      color: '#D4AF37',
    },
    {
      icon: 'receipt-outline' as const,
      label: 'My\nOrders',
      onPress: () => router.push('/orders'),
      color: '#4A90D9',
    },
    {
      icon: 'person-outline' as const,
      label: 'My\nProfile',
      onPress: () => router.push('/edit-profile'),
      color: '#E67E22',
    },
  ];

  const renderQuickActions = () => (
    <View style={styles.quickActionsRow}>
      {quickActions.map((action) => (
        <TouchableOpacity
          key={action.label}
          style={styles.quickActionCard}
          onPress={action.onPress}
          activeOpacity={0.75}
        >
          <View style={[styles.quickActionIcon, { backgroundColor: action.color + '18' }]}>
            <Ionicons name={action.icon} size={26} color={action.color} />
          </View>
          <Text style={styles.quickActionLabel}>{action.label}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  // ─── Section: Schemes preview ─────────────────────────────────────────────
  const renderSchemePreview = (scheme: Scheme) => (
    <View key={scheme._id} style={styles.schemeCard}>
      <View style={styles.schemeCardLeft}>
        <Text style={styles.schemeName} numberOfLines={1}>
          {scheme.name}
        </Text>
        {scheme.description ? (
          <Text style={styles.schemeDesc} numberOfLines={1}>
            {scheme.description}
          </Text>
        ) : null}
        {scheme.validUntil ? (
          <Text style={styles.schemeMeta}>Until {formatDateIST(scheme.validUntil)}</Text>
        ) : null}
      </View>
      <View style={styles.schemeBadge}>
        <Text style={styles.schemeBadgeText}>
          {scheme.discountType === 'percentage'
            ? `${scheme.discountValue}%`
            : `₹${scheme.discountValue}`}
        </Text>
        <Text style={styles.schemeBadgeOff}>off</Text>
      </View>
    </View>
  );

  // ─── Section: Brand logo carousel ─────────────────────────────────────────
  const renderBrandItem = ({ item }: { item: Brand }) => (
    <TouchableOpacity
      style={styles.brandCard}
      onPress={() => item.name && router.push(`/brands/${encodeURIComponent(item.name)}`)}
      activeOpacity={0.75}
    >
      <Image
        source={{ uri: getImageUrl(item.logoUrl || '') }}
        style={styles.brandLogo}
        resizeMode="contain"
      />
    </TouchableOpacity>
  );

  // ─── Section: Collection card ─────────────────────────────────────────────
  const renderCollectionItem = ({ item }: { item: Collection }) => (
    <TouchableOpacity
      style={styles.collectionCard}
      onPress={() =>
        router.push(
          item.slug
            ? `/collections/${item.slug}`
            : `/collections/${encodeURIComponent(item.name || '')}`
        )
      }
      activeOpacity={0.8}
    >
      <Image
        source={{ uri: getImageUrl(item.imageUrl || item.image || '') }}
        style={styles.collectionImage}
        resizeMode="cover"
      />
      <LinearGradient
        colors={['transparent', 'rgba(0,0,0,0.65)']}
        style={StyleSheet.absoluteFill}
      />
      <Text style={styles.collectionName} numberOfLines={2}>
        {item.name}
      </Text>
    </TouchableOpacity>
  );

  // ─── Section: Category chip ───────────────────────────────────────────────
  const renderCategoryChip = ({ item }: { item: Category }) => (
    <TouchableOpacity
      style={styles.categoryChip}
      onPress={() =>
        router.push(
          item.slug
            ? `/categories/${item.slug}`
            : `/categories/${encodeURIComponent(item.name || '')}`
        )
      }
      activeOpacity={0.75}
    >
      {item.images?.[0] ? (
        <Image
          source={{ uri: getImageUrl(item.images[0]) }}
          style={styles.categoryChipImage}
          resizeMode="cover"
        />
      ) : (
        <View style={[styles.categoryChipImage, { backgroundColor: colors.neutral[100] }]} />
      )}
      <Text style={styles.categoryChipName} numberOfLines={1}>
        {item.name}
      </Text>
    </TouchableOpacity>
  );

  interface Product {
    _id?: string;
    name?: string;
    category?: any;
    brand?: string;
    price?: number;
    mrp?: number;
    displayImage?: string;
    images?: string[];
    isExclusive?: boolean;
    discountPercentage?: number;
    isNew?: boolean;
    bestSeller?: boolean;
    previouslyBought?: boolean;
  }

  const ProductCard = ({ item, slot, strategy }: { item: Product; slot: string; strategy: string }) => {
    const img = item.displayImage || (item.images?.length ? item.images[0] : null);
    const hasDiscount = item.mrp && item.price && item.mrp > item.price;
    const discountPct =
      item.discountPercentage ||
      (hasDiscount ? Math.round(((item.mrp! - item.price!) / item.mrp!) * 100) : 0);

    return (
      <TouchableOpacity
        style={[styles.productCard, shadows.card]}
        activeOpacity={0.9}
        onPress={async () => {
          const pid = item._id || (item as any).id;
          if (pid) {
            await trackRecommendationEvent({
              eventType: 'product_view',
              slot: slot,
              productId: pid,
              productName: item.name,
              strategy: strategy,
            });
            router.push({
              pathname: '/products/[id]',
              params: { id: pid, refSlot: slot, refStrategy: strategy },
            });
          }
        }}
      >
        <View style={styles.productImageContainer}>
          {img ? (
            <Image
              source={{ uri: getImageUrl(img) }}
              style={styles.productImage}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.productImagePlaceholder}>
              <Ionicons name="image-outline" size={24} color={colors.neutral[300]} />
            </View>
          )}

          {discountPct > 0 && (
            <View style={styles.discountBadge}>
              <Text style={styles.discountText}>{discountPct}% OFF</Text>
            </View>
          )}

          {/* Dynamic Badges */}
          <View style={{ position: 'absolute', bottom: 4, left: 4, flexDirection: 'row', flexWrap: 'wrap', gap: 4, paddingRight: 4 }}>
            {item.isNew && (
              <View style={{ backgroundColor: '#3B82F6', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: '#fff' }}>NEW</Text>
              </View>
            )}
            {item.bestSeller && (
              <View style={{ backgroundColor: '#F59E0B', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: '#fff' }}>BESTSELLER</Text>
              </View>
            )}
            {item.previouslyBought && (
              <View style={{ backgroundColor: '#8B5CF6', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: '#fff' }}>BOUGHT BEFORE</Text>
              </View>
            )}
          </View>
        </View>

        <View style={styles.productInfo}>
          {item.brand && (
            <Text style={styles.productBrand} numberOfLines={1}>
              {item.brand}
            </Text>
          )}
          <Text style={styles.productName} numberOfLines={2}>
            {item.name}
          </Text>
          <View style={styles.priceRow}>
            <Text style={styles.productPrice}>₹{item.price}</Text>
            {hasDiscount && (
              <Text style={styles.productMrp}>₹{item.mrp}</Text>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  const RecommendationSection = ({
    title,
    data,
    slot,
    strategy,
    onSeeAll,
  }: {
    title: string;
    data: any[];
    slot: string;
    strategy: string;
    onSeeAll?: () => void;
  }) => {
    useEffect(() => {
      if (data && data.length > 0) {
        trackRecommendationEvent({
          eventType: 'section_view',
          slot: slot,
          strategy: strategy,
        });
      }
    }, [data, slot, strategy]);

    if (!data || data.length === 0) return null;

    return (
      <View style={styles.section}>
        <SectionHeader title={title} onSeeAll={onSeeAll} />
        <FlatList
          data={data}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(item, idx) => item._id || String(idx)}
          renderItem={({ item }) => (
            <ProductCard
              item={item}
              slot={slot}
              strategy={strategy}
            />
          )}
          contentContainerStyle={{ paddingHorizontal: spacing.lg }}
        />
      </View>
    );
  };

  const renderRecommendationSection = (sectionKey: string) => {
    let title = '';
    let data: any[] = [];
    let slot = '';
    let strategy = '';
    let onSeeAll: (() => void) | undefined = undefined;

    const cityName = recommendationsData?.cityName || '';

    switch (sectionKey) {
      case 'business_favourites':
        title = cityName ? `Business Favourites in ${cityName}` : 'Business Favourites';
        data = recommendationsData?.businessFavourites || [];
        slot = 'business_favourites';
        strategy = 'business_favourites';
        onSeeAll = () => router.push('/wholesaler/business-favourites');
        break;
      case 'customer_favourites':
        title = cityName ? `Customer Favourites in ${cityName}` : 'Customer Favourites';
        data = recommendationsData?.customerFavourites || [];
        slot = 'customer_favourites';
        strategy = 'customer_favourites';
        onSeeAll = () => router.push('/wholesaler/customer-favourites');
        break;
      case 'trending_now':
        title = 'Trending Now';
        data = recommendationsData?.trendingNow || [];
        slot = 'trending_now';
        strategy = 'trending_now';
        break;
      case 'new_arrivals':
        title = 'New Arrivals';
        data = recommendationsData?.newArrivals || [];
        slot = 'new_arrivals';
        strategy = 'new_arrivals';
        break;
      case 'explore':
        title = 'Explore More';
        data = recommendationsData?.explore || [];
        slot = 'explore';
        strategy = 'explore';
        break;
      default:
        return null;
    }

    if (!data || data.length === 0) return null;

    return (
      <RecommendationSection
        key={sectionKey}
        title={title}
        data={data}
        slot={slot}
        strategy={strategy}
        onSeeAll={onSeeAll}
      />
    );
  };

  // ─── Section title helper ──────────────────────────────────────────────────
  const SectionHeader = ({
    title,
    onSeeAll,
  }: {
    title: string;
    onSeeAll?: () => void;
  }) => (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {onSeeAll && (
        <TouchableOpacity onPress={onSeeAll}>
          <Text style={styles.seeAll}>See all</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.loadingContainer} edges={['top']}>
        {renderHeader()}
        <View style={styles.loadingBody}>
          <Animated.View style={{ opacity: fadeAnim }}>
            <View style={styles.skeletonBanner} />
            <View style={styles.skeletonRow}>
              {[0, 1, 2, 3].map((i) => (
                <View key={i} style={styles.skeletonAction} />
              ))}
            </View>
          </Animated.View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <Animated.View style={[{ flex: 1, opacity: fadeAnim }]}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={{ paddingBottom: 32 + insets.bottom }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
      >
        {/* Header */}
        {renderHeader()}

        {isServiceable === false ? (
          <UnserviceableLocationCard />
        ) : (
          <>
            {/* Wholesaler Banners */}
            {banners.length > 0 && (
              <View style={styles.section}>
                <BannerCarousel banners={banners} height={200} />
              </View>
            )}

            {/* Quick Actions */}
            <View style={styles.section}>
              {renderQuickActions()}
            </View>

        {/* Active Schemes Preview */}
        {schemes.length > 0 && (
          <View style={styles.section}>
            <SectionHeader
              title="Active Schemes"
              onSeeAll={() => router.push('/schemes')}
            />
            {schemes.map(renderSchemePreview)}
          </View>
        )}

        {/* Featured Collections */}
        {collections.length > 0 && (
          <View style={styles.section}>
            <SectionHeader title="Collections" />
            <FlatList
              data={collections}
              horizontal
              showsHorizontalScrollIndicator={false}
              keyExtractor={(item, idx) => item._id || String(idx)}
              renderItem={renderCollectionItem}
              contentContainerStyle={{ paddingHorizontal: spacing.lg, gap: spacing.sm }}
              scrollEnabled
            />
          </View>
        )}

        {/* Brand Carousel */}
        {brands.length > 0 && (
          <View style={styles.section}>
            <SectionHeader title="Brands" onSeeAll={() => router.push('/brands')} />
            <FlatList
              data={brands}
              horizontal
              showsHorizontalScrollIndicator={false}
              keyExtractor={(item, idx) => item._id || String(idx)}
              renderItem={renderBrandItem}
              contentContainerStyle={{ paddingHorizontal: spacing.lg, gap: spacing.sm }}
            />
          </View>
        )}

        {/* Categories */}
        {categories.length > 0 && (
          <View style={styles.section}>
            <SectionHeader title="Categories" onSeeAll={() => router.push('/categories')} />
            <FlatList
              data={categories}
              horizontal
              showsHorizontalScrollIndicator={false}
              keyExtractor={(item, idx) => item._id || String(idx)}
              renderItem={renderCategoryChip}
              contentContainerStyle={{ paddingHorizontal: spacing.lg, gap: spacing.sm }}
            />
          </View>
        )}

        {/* Dynamic Recommendations */}
        {recommendationsData?.sectionOrder?.map((sectionKey: string) => renderRecommendationSection(sectionKey))}

        {/* Browse Products CTA */}
        <View style={[styles.section, { paddingHorizontal: spacing.lg }]}>
          <TouchableOpacity
            style={styles.ctaButton}
            onPress={() => router.push('/products')}
            activeOpacity={0.85}
          >
            <LinearGradient
              colors={['#1a4d33', '#2d7a52']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.ctaGradient}
            >
              <Ionicons name="storefront-outline" size={20} color="#fff" />
              <Text style={styles.ctaText}>Browse All Products</Text>
              <Ionicons name="arrow-forward" size={18} color="#fff" />
            </LinearGradient>
          </TouchableOpacity>
        </View>
          </>
        )}
      </ScrollView>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingBody: {
    padding: spacing.lg,
  },
  skeletonBanner: {
    height: 200,
    backgroundColor: colors.neutral[100],
    borderRadius: borderRadius.xl,
    marginBottom: spacing.lg,
  },
  skeletonRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  skeletonAction: {
    flex: 1,
    height: 80,
    backgroundColor: colors.neutral[100],
    borderRadius: borderRadius.md,
  },

  // Header
  header: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerGreeting: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.75)',
    fontWeight: '400',
    marginBottom: 2,
  },
  headerCompany: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    maxWidth: SCREEN_WIDTH * 0.55,
  },
  headerActions: {
    flexDirection: 'row',
    gap: spacing.xs,
  },
  headerIconBtn: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  wholesaleBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 4,
    marginTop: spacing.sm,
    backgroundColor: 'rgba(212,175,55,0.18)',
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: 'rgba(212,175,55,0.35)',
  },
  wholesaleBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.accent,
    letterSpacing: 0.3,
  },

  // Sections
  section: {
    marginTop: spacing.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  seeAll: {
    ...typography.bodySmall,
    color: colors.primary,
    fontWeight: '600',
  },

  // Quick actions
  quickActionsRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing.lg,
    gap: spacing.sm,
  },
  quickActionCard: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    paddingVertical: spacing.md,
    paddingHorizontal: 4,
    ...shadows.sm,
  },
  quickActionIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xs,
  },
  quickActionLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.textPrimary,
    textAlign: 'center',
    lineHeight: 14,
  },

  // Schemes
  schemeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.sm,
    padding: spacing.md,
    ...shadows.sm,
  },
  schemeCardLeft: {
    flex: 1,
    marginRight: spacing.sm,
  },
  schemeName: {
    ...typography.bodySmall,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  schemeDesc: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  schemeMeta: {
    ...typography.caption,
    color: colors.textMuted,
    marginTop: 2,
  },
  schemeBadge: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    alignItems: 'center',
    minWidth: 52,
  },
  schemeBadgeText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#fff',
    lineHeight: 18,
  },
  schemeBadgeOff: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.75)',
  },

  // Collections
  collectionCard: {
    width: COLLECTION_CARD_W,
    height: 140,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    justifyContent: 'flex-end',
    ...shadows.sm,
  },
  collectionImage: {
    ...StyleSheet.absoluteFillObject,
  },
  collectionName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#fff',
    padding: spacing.sm,
    lineHeight: 18,
  },

  // Brands
  brandCard: {
    width: BRAND_LOGO_SIZE + 16,
    height: BRAND_LOGO_SIZE + 16,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    ...shadows.xs,
  },
  brandLogo: {
    width: BRAND_LOGO_SIZE,
    height: BRAND_LOGO_SIZE,
  },

  // Categories
  categoryChip: {
    alignItems: 'center',
    width: 80,
  },
  categoryChipImage: {
    width: 64,
    height: 64,
    borderRadius: 32,
    marginBottom: 6,
    backgroundColor: colors.neutral[100],
    overflow: 'hidden',
  },
  categoryChipName: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textPrimary,
    textAlign: 'center',
    lineHeight: 14,
  },

  // CTA
  ctaButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
  },
  ctaGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.md + 2,
    paddingHorizontal: spacing.lg,
  },
  ctaText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
    flex: 1,
    textAlign: 'center',
  },
  // Product card styles
  productCard: {
    width: 150,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    marginRight: 12,
    overflow: 'hidden',
  },
  productImageContainer: {
    height: 140,
    backgroundColor: colors.background,
    position: 'relative',
  },
  productImage: {
    width: '100%',
    height: '100%',
  },
  productImagePlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  discountBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: colors.success,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  discountText: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.surface,
  },
  productInfo: {
    padding: 10,
  },
  productBrand: {
    fontSize: 9,
    fontWeight: '600',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  productName: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.textPrimary,
    lineHeight: 16,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
  },
  productPrice: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
  },
  productMrp: {
    fontSize: 11,
    color: colors.textMuted,
    textDecorationLine: 'line-through',
    marginLeft: 6,
  },
});
