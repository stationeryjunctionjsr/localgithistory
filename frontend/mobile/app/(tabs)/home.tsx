import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { HomeScreenSkeleton } from '../../src/components/SkeletonLoader';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  FlatList,
  Modal,
  Pressable,
  Image,
  Animated,
  Dimensions,
  TextInput,
  StatusBar,
  StyleSheet,
  Linking,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
// import { CoachMark, useCoachMarks } from '../../src/components/CoachMark'; // Coach marks deferred — uncomment to re-enable
import api, { getImageUrl } from '../../src/api/client';
import { useRouter } from 'expo-router';
import { colors, shadows, borderRadius } from '../../src/theme';
import { useAuth } from '../../src/hooks/useAuth';
import { usePincode } from '../../src/context/PincodeContext';
import { SearchOverlay } from '../../src/components/SearchOverlay';
import { LaunchPopup } from '../../src/components/LaunchPopup';
import { BannerCarousel } from '../../src/components/BannerCarousel';
import WholesalerHomeScreen from '../../src/components/WholesalerHomeScreen';
import UnserviceableLocationCard from '../../src/components/UnserviceableLocationCard';
import { trackRecommendationEvent } from '../../src/utils/analytics';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface Product {
  _id?: string;
  name?: string;
  category?: any;
  brand?: string;
  price?: number;
  mrp?: number;
  displayImage?: string;
  images?: string[];
  salesCount?: number;
  isExclusive?: boolean;
  discountPercentage?: number;
  isNew?: boolean;
  bestSeller?: boolean;
  previouslyBought?: boolean;
}

interface Brand {
  _id?: string;
  name?: string;
  logoUrl?: string;
  showInMobileHomepage?: boolean;
}

interface CategoryTag {
  _id?: string;
  name?: string;
}

interface Collection {
  _id?: string;
  name?: string;
  description?: string;
  imageUrl?: string;
  image?: string;
  showOnMobile?: boolean;
}

interface Category {
  _id?: string;
  name?: string;
  slug?: string;
  categoryTags?: string[];
  showInMobileHomepage?: boolean;
  images?: string[];
  subCategories?: string[];
}

interface Banner {
  _id?: string;
  title?: string;
  imageUrl?: string;
  image?: string;
  linkUrl?: string;
  link?: string;
  isActive?: boolean;
}

interface PromoStrip {
  _id: string;
  text: string;
  isActive: boolean;
}

// const COACH_MARK_IDS = ['home_product', 'home_menu']; // Coach marks deferred

function HomeInner() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { user } = useAuth();
  const { pincode, city, isServiceable, openModal } = usePincode();

  // State
  const [showMenu, setShowMenu] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [currentPromoIndex, setCurrentPromoIndex] = useState(0);

  const queryClient = useQueryClient();

  // ── React Query: Phase 1 critical data (banners, products, categories) ──
  const { data: phase1Data, isLoading: phase1Loading, refetch: refetchPhase1 } = useQuery({
    queryKey: ['home-phase1', user?.role || 'guest'],
    queryFn: async () => {
      const [b, p, catsRes] = await Promise.all([
        api.get('/banners/public', {
          params: { position: 'homepage_mobile', pageType: 'Home', userRole: user?.role || 'guest' },
        }).catch(() => ({ data: [] })),
        api.get('/products/public', {
          params: { includeFacets: false, skinny: true },
        }).catch(() => ({ data: { products: [] } })),
        api.get('/categories/public').catch(() => ({ data: [] })),
      ]);

      const activeBanners = (b.data || []).filter((item: Banner) => item.isActive);
      const allProducts: Product[] = p.data?.products || p.data || [];
      const catData = Array.isArray(catsRes.data) ? catsRes.data : catsRes.data?.data || [];
      const allCategories: Category[] = catData.filter((c: any) => c && c.name);

      return { activeBanners, allProducts, allCategories };
    },
  });

  // ── React Query: Phase 2 deferred data (brands, tags, promo, collections, rating) ──
  const { data: phase2Data, refetch: refetchPhase2 } = useQuery({
    queryKey: ['home-phase2'],
    queryFn: async () => {
      const [brandsRes, tagsRes, promoRes, collRes, ratingRes] = await Promise.all([
        api.get('/brands/public').catch(() => ({ data: [] })),
        api.get('/category-tags/active').catch(() => ({ data: [] })),
        api.get('/promo-strips/active').catch(() => ({ data: [] })),
        api.get('/collections/public', { params: { visiblePage: 'Home', pageType: 'Home' } }).catch(() => ({ data: [] })),
        api.get('/google-reviews/rating').catch(() => ({ data: { rating: 0, reviewCount: '0' } })),
      ]);

      const ratingData = ratingRes?.data || { rating: 0, reviewCount: '0' };
      const strips: PromoStrip[] = promoRes.data || [];
      const brandData = Array.isArray(brandsRes.data)
        ? brandsRes.data
        : brandsRes.data?.brands || brandsRes.data?.data || [];
      const mobileBrands = brandData.filter(
        (item: any) => item?.showInMobileHomepage === true || item?.showInMobileHomepage === 'true'
      );
      const brands: Brand[] = mobileBrands.length > 0 ? mobileBrands : brandData.slice(0, 9);
      const tagData = Array.isArray(tagsRes.data) ? tagsRes.data : tagsRes.data?.data || [];
      const categoryTags: CategoryTag[] = tagData.filter((t: any) => t && t.name);
      const collList = Array.isArray(collRes?.data) ? collRes.data : collRes?.data?.data || [];
      const collections: Collection[] = collList.filter((c: any) => c && c.showOnMobile !== false).slice(0, 4);

      return { ratingData, strips, brands, categoryTags, collections };
    },
  });

  const { data: recommendationsData } = useQuery({
    queryKey: ['home-recommendations'],
    queryFn: async () => {
      try {
        const res = await api.get('/recommendations');
        const data = res.data || {};
        const filterActive = (arr: any[]) =>
          (arr || []).filter((p: any) => p && p.isActive !== false && p.stock > 0);
          
        return {
          newArrivals: filterActive(data.newArrivals),
          customerFavourites: filterActive(data.customerFavourites),
          trendingNow: filterActive(data.trendingNow),
          explore: filterActive(data.explore),
          sectionOrder: data.sectionOrder,
        };
      } catch (err) {
        return null;
      }
    },
  });

  // Derived state from React Query results
  const loading = phase1Loading;
  const banners = phase1Data?.activeBanners || [];
  const products = phase1Data?.allProducts || [];
  const allCategories = phase1Data?.allCategories || [];
  const categories = allCategories;
  const homeCategories = allCategories.filter((c: any) => c.showInMobileHomepage).slice(0, 6);
  const newlyAdded = products.slice(0, 10);
  const exclusive = products.filter((item: any) => item.isExclusive).slice(0, 10);
  const bestSelling = [...products].sort((a: any, b: any) => (b.salesCount || 0) - (a.salesCount || 0)).slice(0, 10);

  const recNewArrivals = recommendationsData?.newArrivals || [];
  const recCustomerFavourites = recommendationsData?.customerFavourites || [];
  const recTrendingNow = recommendationsData?.trendingNow || [];
  const recExplore = recommendationsData?.explore || [];
  const sectionOrder = recommendationsData?.sectionOrder || ["new_arrivals", "customer_favourites", "trending_now", "explore"];

  const brands = phase2Data?.brands || [];
  const categoryTags = phase2Data?.categoryTags || [];
  const promoStrips = phase2Data?.strips || [];
  const collections = phase2Data?.collections || [];
  const googleRating = phase2Data?.ratingData || { rating: 0, reviewCount: '0' };

  const [expandedTag, setExpandedTag] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [unreadNotifCount, setUnreadNotifCount] = useState(0);
  const [retryCount, setRetryCount] = useState(0);

  // Animations
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const drawerAnim = useRef(new Animated.Value(-SCREEN_WIDTH * 0.85)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;
  const searchExpandAnim = useRef(new Animated.Value(0)).current;

  const [isMenuVisible, setIsMenuVisible] = useState(false);
  // const coachMarks = useCoachMarks(COACH_MARK_IDS); // Coach marks deferred

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    products.forEach((p) => {
      const catName = typeof p.category === 'object' ? p.category?.name : p.category;
      if (catName) counts[catName] = (counts[catName] || 0) + 1;
    });
    return counts;
  }, [products]);

  // Premium Drawer Animation
  useEffect(() => {
    if (showMenu) {
      setIsMenuVisible(true);
      Animated.parallel([
        Animated.spring(drawerAnim, {
          toValue: 0,
          friction: 15,
          tension: 50,
          useNativeDriver: true,
        }),
        Animated.timing(backdropAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(drawerAnim, {
          toValue: -SCREEN_WIDTH * 0.85,
          duration: 280,
          useNativeDriver: true,
        }),
        Animated.timing(backdropAnim, {
          toValue: 0,
          duration: 280,
          useNativeDriver: true,
        }),
      ]).start(({ finished }) => {
        if (finished) setIsMenuVisible(false);
      });
    }
  }, [showMenu]);

  // Search expand animation
  useEffect(() => {
    Animated.timing(searchExpandAnim, {
      toValue: showSearch ? 1 : 0,
      duration: 280,
      useNativeDriver: false,
    }).start();
  }, [showSearch]);

  // Notification badge: count how many published notifications the user hasn't read yet
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [response, raw] = await Promise.all([
          api.get<any[]>('/push-notifications/inbox'),
          AsyncStorage.getItem('sj_read_notification_ids'),
        ]);
        if (cancelled) return;
        const readIds: string[] = raw ? JSON.parse(raw) : [];
        const notifs = response.data || [];
        setUnreadNotifCount(notifs.filter((n: any) => !readIds.includes(n._id)).length);
      } catch (e: any) { console.warn('Background task failed', e); }
    })();
    return () => { cancelled = true; };
  }, []);

  // Initial fade in
  useEffect(() => {
    Animated.spring(fadeAnim, {
      toValue: 1,
      friction: 10,
      tension: 40,
      useNativeDriver: true,
    }).start();
    // Coach tour is not auto-started here (was intrusive on every cold load). Call coachMarks.startTour() from a help entry point if needed.
  }, [loading]);

  // Promo strip animation
  useEffect(() => {
    if (promoStrips.length > 1) {
      const interval = setInterval(() => {
        setCurrentPromoIndex((prev) => (prev + 1) % promoStrips.length);
      }, 4000);
      return () => clearInterval(interval);
    }
  }, [promoStrips]);

  // retryCount triggers manual refetch via React Query invalidation
  useEffect(() => {
    if (retryCount > 0) {
      refetchPhase1();
      refetchPhase2();
    }
  }, [retryCount]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([refetchPhase1(), refetchPhase2()]);
    setRefreshing(false);
  }, [refetchPhase1, refetchPhase2]);

  const toggleTag = (id?: string) => {
    if (!id) return;
    setExpandedTag(expandedTag === id ? null : id);
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      setShowSearch(false);
      router.push({ pathname: '/products', params: { search: searchQuery.trim() } });
    }
  };

  // Premium Product Card
  const ProductCard = ({ item, _index, slot, strategy }: { item: Product; _index?: number; slot?: string; strategy?: string }) => {
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
            if (slot) {
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
            } else {
              router.push({ pathname: '/products/[id]', params: { id: pid } });
            }
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
              <Ionicons name="image-outline" size={28} color={colors.neutral[300]} />
            </View>
          )}

          {/* Discount badge */}
          {discountPct > 0 && (
            <View style={styles.discountBadge}>
              <Text style={styles.discountText}>{discountPct}% OFF</Text>
            </View>
          )}

          {/* Exclusive badge */}
          {item.isExclusive && (
            <View style={styles.exclusiveBadge}>
              <Ionicons name="star" size={10} color={colors.accent} />
            </View>
          )}

          {/* Dynamic Badges */}
          <View style={{ position: 'absolute', bottom: 4, left: 4, flexDirection: 'row', flexWrap: 'wrap', gap: 4, paddingRight: 4 }}>
            {item.isNew && (
              <View style={{ backgroundColor: colors.info, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: colors.surface }}>NEW</Text>
              </View>
            )}
            {item.bestSeller && (
              <View style={{ backgroundColor: colors.warning, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: colors.surface }}>BESTSELLER</Text>
              </View>
            )}
            {item.previouslyBought && (
              <View style={{ backgroundColor: '#8B5CF6', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: colors.surface }}>BOUGHT BEFORE</Text>
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
            {hasDiscount && <Text style={styles.productMrp}>₹{item.mrp}</Text>}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  // Section Component
  const Section = ({
    title,
    data,
    onViewAll,
    renderCard,
  }: {
    title: string;
    data: any[];
    onViewAll?: () => void;
    renderCard: (item: any, index: number) => React.ReactElement;
  }) => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {onViewAll && (
          <TouchableOpacity onPress={onViewAll} activeOpacity={0.7} style={styles.viewAllButton}>
            <Text style={styles.viewAllText}>View all</Text>
            <Ionicons name="chevron-forward" size={14} color={colors.primary} />
          </TouchableOpacity>
        )}
      </View>
      <FlatList
        data={data}
        keyExtractor={(item, idx) => `${item?._id || idx}`}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16 }}
        renderItem={({ item, index }) => renderCard(item, index)}
      />
    </View>
  );

  const RecommendationSection = ({
    title,
    data,
    slot,
    strategy,
  }: {
    title: string;
    data: any[];
    slot: string;
    strategy: string;
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
      <Section
        title={title}
        data={data}
        renderCard={(item, index) => (
          <ProductCard
            key={item._id}
            item={item}
            _index={index}
            slot={slot}
            strategy={strategy}
          />
        )}
      />
    );
  };

  const renderRecommendationSection = (sectionKey: string) => {
    let title = '';
    let data: any[] = [];
    let slot = '';
    let strategy = '';

    switch (sectionKey) {
      case 'new_arrivals':
        title = 'New Arrivals';
        data = recNewArrivals.length > 0 ? recNewArrivals : newlyAdded;
        slot = 'new_arrivals';
        strategy = 'new_arrivals';
        break;
      case 'customer_favourites':
        title = 'Customer Favourites';
        data = recCustomerFavourites.length > 0 ? recCustomerFavourites : bestSelling;
        slot = 'customer_favourites';
        strategy = 'customer_favourites';
        break;
      case 'trending_now':
        title = 'Trending Now';
        data = recTrendingNow.length > 0 ? recTrendingNow : exclusive;
        slot = 'trending_now';
        strategy = 'trending_now';
        break;
      case 'explore':
        title = 'Explore More';
        data = recExplore;
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
      />
    );
  };

  const renderStars = (rating: number) => {
    const stars = [];
    const floorRating = Math.floor(rating);
    const hasHalf = rating - floorRating >= 0.5;

    for (let i = 1; i <= 5; i++) {
      if (i <= floorRating) {
        stars.push(
          <Ionicons key={i} name="star" size={14} color="#fbbf24" style={{ marginRight: 2 }} />
        );
      } else if (i === floorRating + 1 && hasHalf) {
        stars.push(
          <Ionicons key={i} name="star-half" size={14} color="#fbbf24" style={{ marginRight: 2 }} />
        );
      } else {
        stars.push(
          <Ionicons key={i} name="star-outline" size={14} color="#fbbf24" style={{ marginRight: 2 }} />
        );
      }
    }
    return stars;
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />

      {/* Premium Header */}
      <View style={styles.header}>
        {/* Promo Strip */}
        {promoStrips.length > 0 && (
          <View style={styles.promoStrip}>
            <Text style={styles.promoText} numberOfLines={1}>
              {promoStrips[currentPromoIndex]?.text}
            </Text>
          </View>
        )}

        {/* Main Header Row */}
        <View style={styles.headerRow}>
          <TouchableOpacity onPress={() => setShowMenu(true)} style={styles.menuButton}>
            <Ionicons name="menu-outline" size={26} color={colors.primary} />
          </TouchableOpacity>

          <Text style={styles.logo}>Stationery Junction</Text>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            {/* Search */}
            <TouchableOpacity
              onPress={() => setShowSearch(!showSearch)}
              style={[styles.searchButton, showSearch && styles.searchButtonActive]}
            >
              <Ionicons
                name="search-outline"
                size={22}
                color={showSearch ? colors.surface : colors.primary}
              />
            </TouchableOpacity>

            {/* Notification Bell — rightmost */}
            <TouchableOpacity
              onPress={() => router.push('/notifications')}
              style={{ padding: 6 }}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="notifications-outline" size={22} color={colors.primary} />
              {unreadNotifCount > 0 && (
                <View
                  style={{
                    position: 'absolute',
                    top: 2,
                    right: 2,
                    minWidth: 16,
                    height: 16,
                    borderRadius: 8,
                    backgroundColor: colors.error,
                    alignItems: 'center',
                    justifyContent: 'center',
                    paddingHorizontal: 3,
                  }}
                >
                  <Text style={{ color: colors.surface, fontSize: 9, fontWeight: '700' }}>
                    {unreadNotifCount > 9 ? '9+' : unreadNotifCount}
                  </Text>
                </View>
              )}
            </TouchableOpacity>
          </View>
        </View>

        {/* Hyperlocal Delivery Location Bar */}
        <TouchableOpacity
          onPress={() => openModal(false)}
          style={styles.locationBar}
          activeOpacity={0.8}
        >
          <Ionicons name="location" size={14} color={colors.primary} />
          <Text style={styles.locationText} numberOfLines={1}>
            Deliver to: <Text style={styles.locationBold}>{pincode || 'Select Pincode'}</Text>
            {city ? ` (${city})` : ''}
          </Text>
          <Ionicons name="chevron-down" size={12} color={colors.primary} />
        </TouchableOpacity>

        {/* Expandable Search Bar */}
        <Animated.View
          style={[
            styles.expandableSearch,
            {
              maxHeight: searchExpandAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0, 60],
              }),
              opacity: searchExpandAnim,
              marginTop: searchExpandAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0, 12],
              }),
            },
          ]}
        >
          <View style={styles.searchInputContainer}>
            <Ionicons name="search-outline" size={18} color={colors.neutral[400]} />
            <TextInput
              placeholder="Search for journals, pens..."
              placeholderTextColor={colors.neutral[400]}
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={handleSearch}
              returnKeyType="search"
              style={styles.searchInput}
              autoFocus={showSearch}
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <Ionicons name="close-circle" size={18} color={colors.neutral[400]} />
              </TouchableOpacity>
            )}
          </View>
        </Animated.View>
      </View>

      {/* Main Content */}
      {loading ? (
        <HomeScreenSkeleton />
      ) : products.length === 0 && categories.length === 0 && banners.length === 0 ? (
        <View style={styles.errorContainer}>
          <Ionicons name="wifi-outline" size={48} color={colors.neutral[400]} />
          <Text style={styles.errorText}>Failed to load content. Please check your connection.</Text>
          <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <Animated.ScrollView
          style={{ opacity: fadeAnim }}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={colors.primary}
              colors={[colors.primary]}
            />
          }
        >
          {isServiceable === false ? (
            <UnserviceableLocationCard />
          ) : (
            <>
              {/* Premium Banner Carousel */}
              <BannerCarousel banners={banners} />

          {/* Stats Counter */}
          {(products.length > 0 || brands.length > 0) && (
            <View style={styles.statsContainer}>
              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{products.length}+</Text>
                  <Text style={styles.statLabel}>PREMIUM PRODUCTS</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{brands.length}+</Text>
                  <Text style={styles.statLabel}>TRUSTED BRANDS</Text>
                </View>
              </View>
            </View>
          )}

          {/* Product Sections */}
          {sectionOrder.map((sectionKey: string) => renderRecommendationSection(sectionKey))}

          {/* Collections */}
          {collections.length > 0 && (
            <View style={styles.collectionsSection}>
              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>Featured Collections</Text>
              </View>
              <View style={styles.collectionsGrid}>
                {collections.map((col) => (
                  <TouchableOpacity
                    key={col._id}
                    style={[styles.collectionCard, shadows.sm]}
                    activeOpacity={0.9}
                    onPress={() =>
                      router.push({
                        pathname: '/collections/[slug]',
                        params: { slug: col._id || '' },
                      })
                    }
                  >
                    <Image
                      source={{ uri: getImageUrl(col.imageUrl || col.image || '') }}
                      style={styles.collectionImage}
                      resizeMode="cover"
                    />
                    <View
                      style={[styles.collectionGradient, { backgroundColor: 'rgba(0,0,0,0.3)' }]}
                    />
                    <View style={styles.collectionContent}>
                      <Text style={styles.collectionName} numberOfLines={2}>
                        {col.name}
                      </Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* Shop by Category */}
          {homeCategories.length > 0 && (
            <View style={styles.categoriesSection}>
              <View style={styles.categoriesHeader}>
                <Text style={styles.categoriesTitle}>Shop by Category</Text>
                <Text style={styles.categoriesSubtitle}>Explore our premium collection</Text>
              </View>
              <View style={styles.categoriesGrid}>
                {homeCategories.map((item, idx) => (
                  <TouchableOpacity
                    key={item._id || item.name}
                    style={[styles.categoryCard, shadows.sm]}
                    activeOpacity={0.85}
                    onPress={() =>
                      router.push({
                        pathname: '/categories/[slug]',
                        params: { slug: item.slug || item.name || '' },
                      })
                    }
                  >
                    <View
                      style={[
                        styles.categoryImageContainer,
                        {
                          backgroundColor:
                            idx % 3 === 0 ? '#f4e4e1' : idx % 3 === 1 ? '#e8ebf4' : '#e8f4e8',
                        },
                      ]}
                    >
                      {item.images?.length ? (
                        <Image
                          source={{ uri: getImageUrl(item.images[0]) }}
                          style={styles.categoryImage}
                          resizeMode="cover"
                        />
                      ) : (
                        <Ionicons name="layers-outline" size={24} color={colors.primary} />
                      )}
                    </View>
                    <Text style={styles.categoryName} numberOfLines={1}>
                      {item.name}
                    </Text>
                    <Text style={styles.categoryCount}>
                      {categoryCounts[item.name || ''] || 0} items
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* Brands */}
          {brands.length > 0 && (
            <View style={styles.brandsSection}>
              <View style={styles.sectionHeader}>
                <View>
                  <Text style={styles.sectionTitle}>Featured Brands</Text>
                  <Text style={styles.sectionSubtitle}>The finest stationery makers</Text>
                </View>
                <TouchableOpacity
                  onPress={() => router.push('/(tabs)/brands')}
                  style={styles.viewAllButton}
                >
                  <Text style={styles.viewAllText}>View all</Text>
                  <Ionicons name="chevron-forward" size={14} color={colors.primary} />
                </TouchableOpacity>
              </View>
              <View style={styles.brandsGrid}>
                {brands.map((item) => (
                  <TouchableOpacity
                    key={item._id}
                    style={[styles.brandCard, shadows.xs]}
                    activeOpacity={0.85}
                    onPress={() =>
                      router.push({ pathname: '/brands/[slug]', params: { slug: item.name || '' } })
                    }
                  >
                    {item.logoUrl ? (
                      <Image
                        source={{ uri: getImageUrl(item.logoUrl) }}
                        style={styles.brandLogo}
                        resizeMode="contain"
                      />
                    ) : (
                      <Text style={styles.brandName} numberOfLines={2}>
                        {item.name}
                      </Text>
                    )}
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* Google Reviews — links to real Google review page */}
          <TouchableOpacity
            style={[styles.reviewsCard, shadows.sm]}
            activeOpacity={0.8}
            onPress={() => Linking.openURL('https://share.google/6nwo4Mqy2qMRtztbF')}
          >
            <View style={styles.reviewsContent}>
              <View style={styles.googleIcon}>
                <Ionicons name="logo-google" size={24} color="white" />
              </View>
              <View style={styles.reviewsInfo}>
                {googleRating.rating > 0 ? (
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <Text style={styles.ratingValueText}>{googleRating.rating.toFixed(1)}</Text>
                    <View style={[styles.starsRow, { marginLeft: 6, marginRight: 6 }]}>
                      {renderStars(googleRating.rating)}
                    </View>
                    <Text style={styles.ratingCountText}>({googleRating.reviewCount} reviews)</Text>
                  </View>
                ) : (
                  <Text style={styles.ratingText}>Rate us on Google</Text>
                )}
                <Text style={styles.reviewsSubtext}>Tap to write a review</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.neutral[400]} />
          </TouchableOpacity>
            </>
          )}

          <View style={{ height: 32 }} />
        </Animated.ScrollView>
      )}

      {/* Premium Drawer Modal */}
      <Modal
        visible={isMenuVisible}
        animationType="none"
        transparent
        onRequestClose={() => setShowMenu(false)}
      >
        <View style={styles.drawerOverlay}>
          {/* Backdrop */}
          <Animated.View style={[styles.drawerBackdrop, { opacity: backdropAnim }]} pointerEvents="none" />
          <Pressable
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              right: 0,
              width: SCREEN_WIDTH * 0.15,
            }}
            onPress={() => setShowMenu(false)}
          />

          {/* Drawer Content */}
          <Animated.View
            style={[
              styles.drawerContainer,
              {
                transform: [{ translateX: drawerAnim }],
                paddingTop: insets.top,
                paddingBottom: insets.bottom,
              },
            ]}
          >
            {/* Drawer Header */}
            <View style={styles.drawerHeader}>
              <View style={styles.drawerBrandRow}>
                <View style={styles.drawerLogoContainer}>
                  <Text style={styles.drawerLogoText}>SJ</Text>
                </View>
                <View>
                  <Text style={styles.drawerBrandName}>Stationery Junction</Text>
                  <Text style={styles.drawerBrandTagline}>Premium Stationery</Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setShowMenu(false)} style={styles.drawerCloseButton}>
                <Ionicons name="close-outline" size={26} color={colors.neutral[600]} />
              </TouchableOpacity>
            </View>

            {/* Drawer Menu */}
            <ScrollView style={styles.drawerScroll} showsVerticalScrollIndicator={false}>
              {categoryTags.map((tag) => {
                const tagId = tag._id || (tag as any).id || '';
                return (
                  <View key={tagId || tag.name} style={styles.drawerSection}>
                    <TouchableOpacity
                      style={styles.drawerSectionHeader}
                      onPress={() => toggleTag(tagId)}
                    >
                      <Text style={styles.drawerSectionTitle}>{tag.name}</Text>
                      <Ionicons
                        name={expandedTag === tagId ? 'chevron-up' : 'chevron-down'}
                        size={18}
                        color={colors.neutral[400]}
                      />
                    </TouchableOpacity>

                    {expandedTag === tagId && (
                      <View style={styles.drawerSubMenu}>
                        {categories
                          .filter((c) =>
                            (c.categoryTags || []).some((t) => {
                              if (typeof t !== 'string') return false;
                              return t.toLowerCase() === (tag.name || '').toLowerCase();
                            })
                          )
                          .map((cat) => {
                            const catId = cat._id || (cat as any).id || '';
                            return (
                              <View key={catId}>
                                <View style={styles.drawerSubItemRow}>
                                  <TouchableOpacity
                                    style={styles.drawerSubItemTextButton}
                                    onPress={() => {
                                      setShowMenu(false);
                                      router.push({
                                        pathname: '/categories/[slug]',
                                        params: { slug: cat.slug || cat.name || '' },
                                      });
                                    }}
                                  >
                                    <Text style={styles.drawerSubItemText}>{cat.name}</Text>
                                  </TouchableOpacity>

                                  {cat.subCategories && cat.subCategories.length > 0 ? (
                                    <TouchableOpacity
                                      style={styles.drawerChevronButton}
                                      onPress={() => {
                                        setExpandedCategory(
                                          expandedCategory === catId ? null : catId
                                        );
                                      }}
                                    >
                                      <Ionicons
                                        name={
                                          expandedCategory === catId ? 'chevron-up' : 'chevron-down'
                                        }
                                        size={18}
                                        color={colors.neutral[400]}
                                      />
                                    </TouchableOpacity>
                                  ) : (
                                    <View style={styles.drawerChevronPlaceholder}>
                                      <Ionicons
                                        name="chevron-forward"
                                        size={14}
                                        color={colors.neutral[300]}
                                      />
                                    </View>
                                  )}
                                </View>

                                {/* Sub Categories Expansion */}
                                {expandedCategory === catId && cat.subCategories && (
                                  <View
                                    style={{
                                      paddingLeft: 16,
                                      borderLeftWidth: 1,
                                      borderLeftColor: colors.border,
                                      marginLeft: 8,
                                    }}
                                  >
                                    {cat.subCategories.map((sub) => (
                                      <TouchableOpacity
                                        key={sub}
                                        style={styles.drawerSubItem}
                                        onPress={() => {
                                          setShowMenu(false);
                                          router.push({
                                            pathname: '/categories/[slug]',
                                            params: {
                                              slug: cat.slug || cat.name || '',
                                              subCategory: sub,
                                            },
                                          });
                                        }}
                                      >
                                        <Text style={styles.drawerSubItemText}>{sub}</Text>
                                      </TouchableOpacity>
                                    ))}
                                  </View>
                                )}
                              </View>
                            );
                          })}
                      </View>
                    )}
                  </View>
                );
              })}

              {/* Quick Links */}
              <View style={styles.drawerQuickLinks}>
                <TouchableOpacity
                  style={styles.drawerQuickLink}
                  onPress={() => {
                    setShowMenu(false);
                    router.push({ pathname: '/products', params: {} });
                  }}
                >
                  <Ionicons name="grid-outline" size={20} color={colors.primary} />
                  <Text style={styles.drawerQuickLinkText}>All Products</Text>
                </TouchableOpacity>
              </View>

              {/* Footer */}
              <View style={styles.drawerFooter}>
                <Text style={styles.drawerFooterText}>Elegance in Stationery</Text>
                <Text style={styles.drawerVersionText}>V 1.0.0</Text>
              </View>
            </ScrollView>
          </Animated.View>
        </View>
      </Modal>

      {/* Coach Marks — deferred; uncomment import + useCoachMarks above and remove these comments to re-enable
      {coachMarks.isActive && coachMarks.currentMarkId === 'home_product' && (
        <CoachMark id="home_product" title="Browse Products" description="Tap on any product to see details."
          onDismiss={coachMarks.dismiss} onNext={coachMarks.next} isLast={coachMarks.currentIndex === coachMarks.totalMarks - 1} />
      )}
      {coachMarks.isActive && coachMarks.currentMarkId === 'home_menu' && (
        <CoachMark id="home_menu" title="Browse Categories" description="Tap the menu icon to browse."
          onDismiss={coachMarks.dismiss} onNext={coachMarks.next} isLast={coachMarks.currentIndex === coachMarks.totalMarks - 1} />
      )}
      */}

      {/* Global Overlays */}
      <SearchOverlay
        visible={showSearch}
        onClose={() => setShowSearch(false)}
        onSearch={(q) => router.push({ pathname: '/products', params: { search: q } })}
        initialQuery={searchQuery}
      />

      <LaunchPopup />
    </SafeAreaView>
  );
}

export default function Home() {
  const { user } = useAuth();
  if (user?.role === 'wholesaler') {
    return <WholesalerHomeScreen />;
  }
  return <HomeInner />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundAlt,
  },
  header: {
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  promoStrip: {
    backgroundColor: colors.primary,
    marginHorizontal: -16,
    marginTop: -4,
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  promoText: {
    color: colors.surface,
    fontSize: 12,
    fontWeight: '500',
    textAlign: 'center',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  locationBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#E8F5E9',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    marginTop: 8,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#C8E6C9',
  },
  locationText: {
    fontSize: 12,
    color: colors.primary,
    maxWidth: SCREEN_WIDTH - 80,
  },
  locationBold: {
    fontWeight: '700',
    color: colors.primary,
  },
  menuButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: -0.3,
  },
  searchButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
  },
  searchButtonActive: {
    backgroundColor: colors.primary,
  },
  expandableSearch: {
    overflow: 'hidden',
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.backgroundAlt,
    borderRadius: borderRadius.lg,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  searchInput: {
    flex: 1,
    marginLeft: 10,
    fontSize: 15,
    color: colors.textPrimary,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    paddingTop: 16,
    paddingBottom: 40,
  },
  // Category styles
  categoriesSection: {
    marginBottom: 32,
    paddingHorizontal: 16,
  },
  categoriesHeader: {
    alignItems: 'center',
    marginBottom: 20,
  },
  categoriesTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: -0.3,
  },
  categoriesSubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  categoryCard: {
    width: '31%',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: 12,
    marginBottom: 12,
    alignItems: 'center',
  },
  categoryImageContainer: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
    overflow: 'hidden',
  },
  categoryImage: {
    width: '100%',
    height: '100%',
  },
  categoryName: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.primary,
    textAlign: 'center',
  },
  categoryCount: {
    fontSize: 9,
    color: colors.textMuted,
    marginTop: 2,
  },
  // Section styles
  section: {
    marginBottom: 28,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: -0.3,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  viewAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewAllText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
    marginRight: 2,
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
    backgroundColor: colors.backgroundAlt,
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
  exclusiveBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.accentLight,
    alignItems: 'center',
    justifyContent: 'center',
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
  // Collections styles
  collectionsSection: {
    marginBottom: 28,
    paddingHorizontal: 16,
  },
  collectionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  collectionCard: {
    width: '48%',
    height: 120,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    marginBottom: 12,
  },
  collectionImage: {
    width: '100%',
    height: '100%',
  },
  collectionGradient: {
    ...StyleSheet.absoluteFillObject,
  },
  collectionContent: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 10,
  },
  collectionName: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.surface,
  },
  // Stats counter
  statsContainer: {
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
    marginBottom: 20,
    opacity: 0.8,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  statItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  statLabel: {
    fontSize: 9,
    fontWeight: '700',
    textTransform: 'uppercase',
    color: '#6b7280',
    letterSpacing: 0.5,
  },
  statDivider: {
    width: 1,
    height: 20,
    backgroundColor: '#e5e7eb',
    marginHorizontal: 16,
  },
  // Brands styles
  brandsSection: {
    marginBottom: 28,
    paddingHorizontal: 16,
  },
  brandsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  brandCard: {
    width: '31%',
    height: 64,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  brandLogo: {
    width: '100%',
    height: 36,
  },
  brandName: {
    fontSize: 10,
    fontWeight: '500',
    color: colors.primary,
    textAlign: 'center',
  },
  // Reviews card
  reviewsCard: {
    marginHorizontal: 16,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  reviewsContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  googleIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#4285F4',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  reviewsInfo: {},
  starsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
    marginLeft: 6,
  },
  ratingValueText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.primary,
  },
  ratingCountText: {
    fontSize: 12,
    color: colors.textSecondary || colors.textMuted,
    fontWeight: '500',
  },
  reviewsSubtext: {
    fontSize: 10,
    color: colors.textMuted,
    marginTop: 2,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  reviewButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: borderRadius.full,
  },
  reviewButtonText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.surface,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  // Drawer styles
  drawerOverlay: {
    flex: 1,
    flexDirection: 'row',
  },
  drawerBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  drawerContainer: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: SCREEN_WIDTH * 0.85,
    backgroundColor: colors.surface,
    ...shadows.xl,
  },
  drawerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  drawerBrandRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  drawerLogoContainer: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  drawerLogoText: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.surface,
  },
  drawerBrandName: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.primary,
  },
  drawerBrandTagline: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 1,
  },
  drawerCloseButton: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  drawerScroll: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  drawerSection: {
    marginBottom: 8,
  },
  drawerSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
  },
  drawerSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primary,
  },
  drawerSubMenu: {
    paddingLeft: 12,
    paddingBottom: 12,
    borderLeftWidth: 2,
    borderLeftColor: colors.border,
    marginLeft: 4,
  },
  drawerSubItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
  },
  drawerSubItemText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  drawerSubItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  drawerSubItemTextButton: {
    flex: 1,
    paddingVertical: 10,
  },
  drawerChevronButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  drawerChevronPlaceholder: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  drawerQuickLinks: {
    marginTop: 24,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  drawerQuickLink: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
  },
  drawerQuickLinkText: {
    fontSize: 15,
    fontWeight: '500',
    color: colors.primary,
    marginLeft: 14,
  },
  drawerFooter: {
    marginTop: 32,
    paddingVertical: 24,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  drawerFooterText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.neutral[300],
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  drawerVersionText: {
    fontSize: 9,
    color: colors.neutral[200],
    marginTop: 4,
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 30,
    marginTop: 80,
  },
  errorText: {
    fontSize: 15,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 20,
    fontWeight: '500',
  },
  retryButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: colors.surface,
    fontWeight: '600',
    fontSize: 14,
  },
});
