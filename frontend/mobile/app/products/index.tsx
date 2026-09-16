import React, { useEffect, useState, useMemo, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Image,
  Dimensions,
  Alert,
  Modal,
  ScrollView,
  StatusBar,
  Animated,
  NativeSyntheticEvent,
  NativeScrollEvent,
  RefreshControl,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons, Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import Slider from '@react-native-community/slider';
import MultiSlider from '@ptomasroos/react-native-multi-slider';
import api, { getImageUrl, SESSION_KEY } from '../../src/api/client';
import * as SecureStore from 'expo-secure-store';
import { useAuth } from '../../src/hooks/useAuth';
import { addGuestCartItem } from '../../src/services/guestStore';
import { BannerCarousel } from '../../src/components/BannerCarousel';
import { ProductsListSkeleton } from '../../src/components/SkeletonLoader';
import { colors } from '../../src/theme';
import { useInfiniteQuery, keepPreviousData } from '@tanstack/react-query';

import { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import { default as ReAnimated } from 'react-native-reanimated';

// ── Types ──

interface Product {
  _id?: string;
  name?: string;
  category?: string;
  brand?: string;
  type?: string;
  value?: string;
  tags?: string[];
  price?: number;
  mrp?: number;
  discountPercentage?: number;
  displayImage?: string;
  images?: string[];
  subCategory?: string;
  stock?: number;
  createdAt?: string;
  collection?: string;
  salesCount?: number;
  isNew?: boolean;
  bestSeller?: boolean;
  previouslyBought?: boolean;
}

type PageMode = 'category' | 'brand' | 'collection' | 'general';

interface ProductsListProps {
  category?: string;
  subCategory?: string;
  brand?: string;
  collection?: string;
  pageMode?: PageMode;
  hideHeader?: boolean;
  hideSubCategoryChips?: boolean;
  title?: string;
  headerImage?: string;
  banners?: any[];
}

// ── Constants ──
const { width: SCREEN_WIDTH } = Dimensions.get('window');
const COLUMN_count = 2;
const GRID_SPACING = 12;
const ITEM_WIDTH = (SCREEN_WIDTH - GRID_SPACING * (COLUMN_count + 1)) / COLUMN_count;

const AddButton = ({
  productId,
  busyId,
  item,
  addToCart,
}: {
  productId: string;
  busyId: string | null;
  item: any;
  addToCart: (id: string) => void;
}) => {
  const scale = useSharedValue(1);
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <ReAnimated.View style={[animatedStyle, { position: 'absolute', bottom: 12, right: 12 }]}>
      <TouchableOpacity
        className="h-9 w-9 items-center justify-center rounded-full bg-white shadow-md"
        activeOpacity={0.9}
        onPressIn={() => (scale.value = withSpring(0.9, { damping: 10, stiffness: 200 }))}
        onPressOut={() => (scale.value = withSpring(1))}
        onPress={() => addToCart(productId)}
        disabled={busyId === item._id}
      >
        {busyId === item._id ? (
          <ActivityIndicator size="small" color={colors.textPrimary} />
        ) : (
          <Ionicons name="add" size={24} color={colors.textPrimary} />
        )}
      </TouchableOpacity>
    </ReAnimated.View>
  );
};

export default function ProductsList(props: ProductsListProps = {}) {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const params = useLocalSearchParams();
  const { user } = useAuth();

  // Refs
  const flatListRef = useRef<FlatList>(null);

  // Scroll Animation Values
  const scrollY = useRef(new Animated.Value(0)).current;
  const [showBackToTop, setShowBackToTop] = useState(false);
  const lastScrollY = useRef(0);
  const isScrollingDown = useRef(false);

  // ── Initialization ──
  const initialCategory =
    props.category ??
    (typeof params.category === 'string'
      ? params.category
      : typeof params.slug === 'string'
        ? params.slug
        : '');
  const initialBrand = props.brand ?? (typeof params.brand === 'string' ? params.brand : '');
  const initialSubCategory =
    props.subCategory ?? (typeof params.subCategory === 'string' ? params.subCategory : '');
  const initialCollection =
    props.collection ?? (typeof params.collection === 'string' ? params.collection : '');
  const initialSearch =
    typeof params.search === 'string' ? params.search : typeof params.searchTerm === 'string' ? params.searchTerm : '';
  const pageMode: PageMode =
    props.pageMode ??
    (initialCollection
      ? 'collection'
      : initialBrand && !initialCategory
        ? 'brand'
        : initialCategory
          ? 'category'
          : 'general');

  // ── State ──
  const [busyId, setBusyId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Header Info
  const [categoryInfo, setCategoryInfo] = useState<{
    name: string;
    image?: string;
    subCategories?: string[];
  } | null>(null);

  // Filters
  const [search, setSearch] = useState(initialSearch);
  const [debouncedSearch, setDebouncedSearch] = useState(initialSearch);
  const [category, setCategory] = useState(pageMode === 'category' ? initialCategory : '');
  const [fixedCategory] = useState(pageMode === 'category' ? initialCategory : '');
  const [fixedBrand] = useState(pageMode === 'brand' ? initialBrand : '');
  // Note: subCategory might change via chips
  const [subCategory, setSubCategory] = useState(initialSubCategory);

  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [selectedCollections, setSelectedCollections] = useState<string[]>([]);
  const [allCollectionsNames, setAllCollectionsNames] = useState<Record<string, string>>({});
  const [fullCollections, setFullCollections] = useState<any[]>([]);
  const [backendCollections, setBackendCollections] = useState<string[]>([]);
  const [backendBrands, setBackendBrands] = useState<string[]>([]);
  const [backendSubCategories, setBackendSubCategories] = useState<string[]>([]);

  // Price Range
  const [globalMinPrice, setGlobalMinPrice] = useState(0);
  const [globalMaxPrice, setGlobalMaxPrice] = useState(50000);
  const [priceRange, setPriceRange] = useState<number[]>([0, 50000]); // [min, max]
  // Tracks when the user explicitly applies a price filter (not API-driven init)
  const [priceFilterVersion, setPriceFilterVersion] = useState(0);

  // Discount
  const [minDiscount, setMinDiscount] = useState<number>(0);

  const [popularity, setPopularity] = useState('');
  const [sort, setSort] = useState<'recommended' | 'newest' | 'price_asc' | 'price_desc'>(
    'recommended'
  );

  // UI State
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [showSortModal, setShowSortModal] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Banners (self-fetched for standalone/general mode)
  const [selfBanners, setSelfBanners] = useState<any[]>([]);
  const effectiveBanners = props.banners || selfBanners;

  // ── Derived Header Info ──
  const headerTitle =
    props.title ||
    categoryInfo?.name ||
    fixedBrand ||
    (initialCollection ? 'Collection' : 'Products');
  const headerImage = props.headerImage || categoryInfo?.image;

  // ── Fetch Banners (standalone/general mode only) ──
  useEffect(() => {
    if (props.banners || fixedCategory || fixedBrand || initialCollection) return;
    api
      .get('/banners/public', {
        params: {
          position: 'products_mobile',
          pageType: 'all_products',
          userRole: user?.role || 'guest',
        },
      })
      .then((res) => {
        const active = (res.data || []).filter((b: any) => b.isActive);
        setSelfBanners(active);
      })
      .catch((err) => {
        if (__DEV__) console.warn('[products] banner fetch failed', err);
      });
  }, [props.banners, fixedCategory, fixedBrand, initialCollection, user?.role]);

  // ── Fetch Data ──
  useEffect(() => {
    // Fetch collections map
    api
      .get('/collections/public')
      .then((res) => {
        const list = Array.isArray(res.data) ? res.data : res.data?.data || [];
        setFullCollections(list);
        const map: Record<string, string> = {};
        list.forEach((c: any) => {
          if (c._id) map[c._id] = c.name;
        });
        setAllCollectionsNames(map);
      })
      .catch((e) => {
        if (__DEV__) console.error(e);
      });
  }, []);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 500);
    return () => clearTimeout(timer);
  }, [search]);

  // React Query useInfiniteQuery configuration
  const queryKey = useMemo(() => [
    'products',
    {
      debouncedSearch,
      category,
      subCategory,
      selectedBrands,
      selectedCollections,
      // priceFilterVersion (not priceRange) in queryKey: only bumped when user
      // explicitly applies a price filter via the modal. This avoids the infinite
      // refetch loop where the API response sets globalMin/MaxPrice -> priceRange
      // changes -> new queryKey -> new fetch -> repeat.
      priceFilterVersion,
      minDiscount,
      popularity,
      sort,
      retryCount,
      initialCollection,
      fixedBrand,
      fixedCategory,
    }
  ], [
    debouncedSearch,
    category,
    subCategory,
    selectedBrands,
    selectedCollections,
    priceFilterVersion,
    minDiscount,
    popularity,
    sort,
    retryCount,
    initialCollection,
    fixedBrand,
    fixedCategory,
  ]);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
    refetch,
    isError,
    isLoading,
  } = useInfiniteQuery({
    queryKey,
    queryFn: async ({ pageParam = 1 }) => {
      const apiParams: Record<string, any> = {
        page: pageParam,
        limit: 20,
      };
      if (initialCollection) apiParams.collection = initialCollection;
      if (fixedBrand) apiParams.brand = fixedBrand;
      if (fixedCategory) apiParams.category = fixedCategory;
      if (debouncedSearch) apiParams.search = debouncedSearch;
      if (category) apiParams.category = category;
      if (subCategory) apiParams.subCategory = subCategory;
      if (selectedBrands.length > 0) apiParams.brand = selectedBrands.join(',');
      if (selectedCollections.length > 0) apiParams.collection = selectedCollections.join(',');
      if (priceRange[0] > globalMinPrice) apiParams.minPrice = priceRange[0];
      if (priceRange[1] < globalMaxPrice) apiParams.maxPrice = priceRange[1];
      if (minDiscount > 0) apiParams.minDiscount = minDiscount;
      if (popularity) apiParams.popularity = popularity;
      if (sort !== 'recommended') apiParams.sort = sort;
      apiParams.includeFacets = pageParam === 1;
      apiParams.skinny = true;

      const res = await api.get('/products/public', { params: apiParams });
      return res.data;
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage, allPages) => {
      const totalCount = lastPage.totalCount || 0;
      const loadedCount = allPages.length * 20;
      return loadedCount < totalCount ? allPages.length + 1 : undefined;
    },
    placeholderData: keepPreviousData,
  });

  const products = useMemo(() => {
    if (!data?.pages) return [];
    return data.pages.flatMap((page) => page.products || page || []);
  }, [data]);

  const firstPage = data?.pages?.[0];
  useEffect(() => {
    if (firstPage) {
      if (firstPage.brands) setBackendBrands(firstPage.brands);
      if (firstPage.collections) setBackendCollections(firstPage.collections);
      if (firstPage.subCategories) setBackendSubCategories(firstPage.subCategories);

      const fetchedProducts = firstPage.products || firstPage || [];
      if (fetchedProducts.length > 0 && globalMinPrice === 0 && globalMaxPrice === 50000) {
        const prices = fetchedProducts.map((p: Product) => p.price || 0);
        const min = Math.floor(Math.min(...prices) / 100) * 100;
        const max = Math.ceil(Math.max(...prices) / 100) * 100;
        const validMin = min;
        const validMax = max === min ? max + 100 : max;
        setGlobalMinPrice(validMin);
        setGlobalMaxPrice(validMax);
        setPriceRange([validMin, validMax]);
      }
    }
  }, [firstPage, globalMinPrice, globalMaxPrice]);

  const handleRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  // Load category info
  useEffect(() => {
    if (pageMode !== 'category' || !fixedCategory) {
      setCategoryInfo(null);
      return;
    }
    const load = async () => {
      try {
        const res = await api.get('/categories/public');
        const list = Array.isArray(res.data) ? res.data : res.data?.data || [];
        const match =
          list.find(
            (c: any) => (c?.slug || c?.name || '').toLowerCase() === fixedCategory.toLowerCase()
          ) || list.find((c: any) => (c?.name || '').toLowerCase() === fixedCategory.toLowerCase());
        if (match) {
          setCategoryInfo({
            name: match.name || fixedCategory,
            image: match.images?.[0],
            subCategories: match.subCategories || [],
          });
        } else {
          setCategoryInfo({ name: fixedCategory });
        }
      } catch (e) {
        if (__DEV__) console.warn('[products] category info fetch failed', e);
        setCategoryInfo({ name: fixedCategory });
      }
    };
    load();
  }, [pageMode, fixedCategory]);

  // ── Derived Data & filtering ──

  // Subcategories
  const derivedSubCategories = useMemo(() => {
    if (categoryInfo?.subCategories && categoryInfo.subCategories.length > 0)
      return categoryInfo.subCategories;
    if (!fixedCategory && !category) return [];
    return backendSubCategories;
  }, [backendSubCategories, fixedCategory, category, categoryInfo]);

  const chipItems = useMemo(() => {
    if (pageMode === 'category') return derivedSubCategories;
    return backendSubCategories; // Actually on brand pages, chipItems are usually subcategories or categories.
  }, [pageMode, backendSubCategories, derivedSubCategories]);

  const chipValue = pageMode === 'category' ? subCategory : category;

  const onChipSelect = (val: string) => {
    if (pageMode === 'category') {
      setSubCategory(chipValue === val ? '' : val);
    } else {
      setCategory(chipValue === val ? '' : val);
      setSubCategory('');
    }
  };

  // Available Filter Options - From backend
  const availableBrands = useMemo(() => {
    if (pageMode === 'brand') return [];
    return backendBrands;
  }, [pageMode, backendBrands]);

  const availableCollections = useMemo(() => {
    if (pageMode === 'collection') return [];
    return backendCollections;
  }, [pageMode, backendCollections]);

  const availableSubCategories = useMemo(() => {
    if (pageMode === 'category') return [];
    return backendSubCategories;
  }, [pageMode, backendSubCategories]);

  // ── Handlers ──

  const clearFilters = () => {
    setSearch('');
    if (pageMode === 'category') {
      setSubCategory('');
    } else {
      setCategory('');
      setSubCategory('');
    }
    setSelectedBrands([]);
    setSelectedCollections([]);
    setPriceRange([globalMinPrice, globalMaxPrice]);
    setMinDiscount(0);
    setPopularity('');
    setSort('recommended');
    setShowFilterModal(false);
  };

  const addToCart = async (productId: string) => {
    setBusyId(productId);
    try {
      if (user) {
        const sessionId = await SecureStore.getItemAsync(SESSION_KEY);
        await api.post('/cart', { productId, quantity: 1, sessionId });
      } else {
        const prod = products.find((p) => (p._id || (p as any).id) === productId);
        await addGuestCartItem(productId, 1, prod || undefined);
      }
    } catch (err: any) {
      Alert.alert('Error', 'Could not add to cart.');
    }
    setBusyId(null);
  };

  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const currentOffset = event.nativeEvent.contentOffset.y;

    // Determine direction
    // If currentOffset > lastScrollY, we are scrolling DOWN (higher Y value)
    // If currentOffset < lastScrollY, we are scrolling UP (lower Y value)
    if (currentOffset > lastScrollY.current) {
      isScrollingDown.current = true;
    } else if (currentOffset < lastScrollY.current) {
      isScrollingDown.current = false;
    }

    // Show if scrolling down OR if offset is substantial (user deep in page)
    // User asked: "Do not show it when user is scrolling upwards"
    // So ONLY show if isScrollingDown AND offset > threshold?
    // Or show if offset > threshold AND isScrollingDown?
    // Let's implement literally: Show only if isScrollingDown is true?
    // AND offset > 500

    if (isScrollingDown.current && currentOffset > 300) {
      setShowBackToTop(true);
    } else {
      setShowBackToTop(false);
    }

    lastScrollY.current = currentOffset;
  };

  const handleLoadMore = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  const renderFooter = () => {
    if (!isFetchingNextPage) return <View style={{ height: 40 }} />;
    return (
      <View className="py-4 items-center justify-center">
        <ActivityIndicator size="small" color={colors.primary} />
      </View>
    );
  };

  // ── Render Components ──

  const renderProductItem = ({ item }: { item: Product }) => {
    const img = item.displayImage || (item.images?.length ? item.images[0] : null);
    const imgUrl = img ? getImageUrl(img) : null;
    const productId = item._id || (item as any).id;
    const effectivePrice = item.price || 0;
    const hasDiscount = item.mrp && item.mrp > effectivePrice;
    const discount =
      item.discountPercentage ||
      (hasDiscount ? Math.round(((item.mrp! - effectivePrice) / item.mrp!) * 100) : 0);
    const isOutOfStock = (item.stock || 0) <= 0;

    return (
      <TouchableOpacity
        style={{ width: ITEM_WIDTH, marginBottom: 24 }}
        activeOpacity={0.8}
        onPress={() =>
          productId && router.push({ pathname: '/products/[id]', params: { id: productId } })
        }
      >
        {/* Image Card */}
        <View className="relative mb-3 aspect-[3/4] w-full overflow-hidden rounded-2xl bg-gray-100 shadow-sm">
          {imgUrl ? (
            <Image source={{ uri: imgUrl }} className="h-full w-full" resizeMode="cover" />
          ) : (
            <View className="h-full w-full items-center justify-center">
              <Ionicons name="image-outline" size={32} color={colors.textMuted} />
            </View>
          )}

          {/* Badges */}
          {hasDiscount && discount > 0 && (
            <View className="absolute left-2 top-2 rounded-md bg-red-500 px-2 py-1">
              <Text className="text-[10px] font-bold text-white">{discount}% OFF</Text>
            </View>
          )}
          {isOutOfStock && (
            <View className="absolute inset-0 items-center justify-center bg-white/60 z-10">
              <View className="rounded-full bg-neutral-900 px-3 py-1">
                <Text className="text-xs font-bold text-white">Out of Stock</Text>
              </View>
            </View>
          )}

          {/* Dynamic Badges */}
          <View className="absolute bottom-2 left-1 flex-row flex-wrap gap-1 pr-1">
            {item.isNew && (
              <View className="rounded bg-blue-500 px-1.5 py-0.5">
                <Text className="text-[9px] font-bold text-white">NEW</Text>
              </View>
            )}
            {item.bestSeller && (
              <View className="rounded bg-amber-500 px-1.5 py-0.5">
                <Text className="text-[9px] font-bold text-white">BESTSELLER</Text>
              </View>
            )}
            {item.previouslyBought && (
              <View className="rounded bg-violet-500 px-1.5 py-0.5">
                <Text className="text-[9px] font-bold text-white">BOUGHT BEFORE</Text>
              </View>
            )}
          </View>


          {/* Add Button Overlay (visible on card) */}
          {!isOutOfStock && (
            <AddButton productId={productId!} busyId={busyId} item={item} addToCart={addToCart} />
          )}
        </View>

        {/* Info */}
        <View className="px-1">
          <Text
            className="mb-1 text-xs font-bold uppercase tracking-wider text-gray-400"
            numberOfLines={1}
          >
            {item.brand || 'Stationery'}
          </Text>
          <Text className="mb-1 text-sm font-medium leading-tight text-gray-900" numberOfLines={2}>
            {item.name}
          </Text>
          <View className="flex-row items-baseline gap-2">
            <Text className="text-base font-bold text-gray-900">
              ₹{effectivePrice.toLocaleString()}
            </Text>
            {hasDiscount && (
              <Text className="text-xs text-gray-400 line-through">
                ₹{item.mrp?.toLocaleString()}
              </Text>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  // ── Header Component (Scrollable: Content + Search) ──
  const renderScrollableHeader = () => {
    const heroHeight = 260;
    return (
      <View className="mb-2 bg-white">
        {effectiveBanners.length > 0 && !props.hideHeader ? (
          <View className="px-4 pb-2 pt-24">
            <Text className="mb-1 font-serif text-3xl font-bold text-gray-900">{headerTitle}</Text>
            <Text className="mb-4 text-sm text-gray-500">
              {products.length} Premium Products
            </Text>
            <BannerCarousel banners={effectiveBanners} height={180} />
          </View>
        ) : headerImage && !props.hideHeader ? (
          <View className="relative mb-4 w-full" style={{ height: heroHeight }}>
            <Image
              source={{ uri: getImageUrl(headerImage) }}
              className="absolute inset-0 h-full w-full"
              resizeMode="cover"
            />
            <LinearGradient
              colors={['rgba(0,0,0,0.3)', 'transparent', 'rgba(0,0,0,0.8)']}
              className="absolute inset-0"
            />

            <View className="absolute bottom-6 left-6 right-6">
              <Text className="text-shadow font-serif text-4xl font-bold tracking-tight text-white shadow-sm">
                {headerTitle}
              </Text>
              <Text className="mt-2 self-start rounded-full bg-black/20 px-3 py-1 text-sm font-medium text-white/90 backdrop-blur-sm">
                {products.length} Premium Products
              </Text>
            </View>
          </View>
        ) : (
          <View className="px-4 pb-4 pt-24">
            <Text className="mb-1 font-serif text-3xl font-bold text-gray-900">{headerTitle}</Text>
            <Text className="text-sm text-gray-500">{products.length} Premium Products</Text>
          </View>
        )}

        {/* Search & Chips Section - Scrolls with content */}
        <View className="px-4 pb-2">
          {/* Search Input */}
          <View className="mb-4 flex-row items-center rounded-xl border border-gray-200 bg-gray-100 px-4 py-3">
            <Feather name="search" size={18} color="#6B7280" />
            <TextInput
              placeholder="Search products..."
              value={search}
              onChangeText={setSearch}
              className="ml-3 flex-1 font-medium text-gray-900"
              placeholderTextColor={colors.textMuted}
            />
            {search.length > 0 && (
              <TouchableOpacity onPress={() => setSearch('')}>
                <Ionicons name="close-circle" size={18} color="#6B7280" />
              </TouchableOpacity>
            )}
          </View>

          {/* Horizontal Chips (Categories/Subcategories) */}
          {chipItems.length > 0 && (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              className="mb-4"
              contentContainerStyle={{ paddingRight: 20 }}
            >
              <TouchableOpacity
                onPress={() => onChipSelect('')}
                className={`mr-2 rounded-full border px-5 py-2.5 shadow-sm ${!chipValue ? 'border-neutral-900 bg-neutral-900' : 'border-gray-200 bg-white'}`}
              >
                <Text
                  className={`text-sm font-bold ${!chipValue ? 'text-white' : 'text-gray-700'}`}
                >
                  All
                </Text>
              </TouchableOpacity>
              {chipItems.map((item) => (
                <TouchableOpacity
                  key={item}
                  onPress={() => onChipSelect(item)}
                  className={`mr-2 rounded-full border px-5 py-2.5 shadow-sm ${chipValue === item ? 'border-neutral-900 bg-neutral-900' : 'border-gray-200 bg-white'}`}
                >
                  <Text
                    className={`text-sm font-bold ${chipValue === item ? 'text-white' : 'text-gray-700'}`}
                  >
                    {item}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          )}

          {/* Sort & Filter Indicator */}
          <View className="mt-2 flex-row items-center justify-between border-t border-gray-100 py-2">
            <Text className="text-xs font-bold uppercase tracking-widest text-gray-500">
              {products.length} Items Found
            </Text>
            <TouchableOpacity
              onPress={() => setShowSortModal(true)}
              className="flex-row items-center space-x-1 rounded-lg px-3 py-1 active:bg-gray-50"
            >
              <Text className="text-sm font-bold text-gray-900">
                {sort === 'recommended'
                  ? 'Recommended'
                  : sort === 'newest'
                    ? 'Newest'
                    : sort === 'price_asc'
                      ? 'Lowest Price'
                      : 'Highest Price'}
              </Text>
              <Ionicons name="chevron-down" size={16} color={colors.textPrimary} />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  };

  // ── Fixed Header (Back & Filter Only) ──
  // This sits ON TOP of everything
  const renderFixedHeader = () => {
    // Dynamic Background Opacity: 0 at top, 1 after 150px
    const bgOpacity = scrollY.interpolate({
      inputRange: [50, 200],
      outputRange: [0, 1],
      extrapolate: 'clamp',
    });

    // Dynamic Text Opacity (Title): 0 at top, 1 after 200px
    const textOpacity = scrollY.interpolate({
      inputRange: [150, 250],
      outputRange: [0, 1],
      extrapolate: 'clamp',
    });

    // Icon Color: White at top (if image), Black after scroll
    // Note: Interpolating colors on text/icons in RN requires Animated.Text / Animated.createAnimatedComponent
    // Since we can't easily animate icon props directly without wrapper, we'll swap colors based on threshold or use a wrapper

    // Simplified approach for reliability:
    // Use 2 layers of icons? Or just a white background that fades in + black icons?
    // If we have a white background fading in, we want black icons eventually.
    // If we are over the image, we want white icons.

    // Let's use a "threshold" state for icon color for simplicity, or just assume dark icons if bg becomes white?
    // React Native Animated interpolation doesn't perfectly swap native props like 'color' without specific animated components.
    // But we can overlay two headers? No, that's heavy.

    // We will use a "background" view that fades in (White).
    // And for icons, we will use a "circle" background that is always semi-transparent light/dark, so it works on both.
    // The User requested "fixed on product listing".

    // Best design:
    // Icons are always in a glassmorphism circle (semi-transparent white/black).
    // The main header bar background fades in to Solid White.

    return (
      <View className="absolute left-0 right-0 top-0 z-50">
        <Animated.View
          className="absolute inset-0 border-b border-gray-200 bg-white"
          style={{ opacity: bgOpacity }}
        />
        <SafeAreaView edges={['top']} className="px-4 py-2">
          <View className="h-12 flex-row items-center justify-between">
            <TouchableOpacity
              onPress={() => router.back()}
              className="h-10 w-10 items-center justify-center rounded-full bg-white/50 shadow-sm backdrop-blur-md"
            >
              <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
            </TouchableOpacity>

            {/* Fixed Center Title (Fades in on scroll) */}
            <Animated.Text
              className="bg-transparent text-lg font-bold text-black"
              style={{ opacity: textOpacity }}
              numberOfLines={1}
            >
              {headerTitle}
            </Animated.Text>

            <TouchableOpacity
              onPress={() => setShowFilterModal(true)}
              className="h-10 w-10 items-center justify-center rounded-full bg-white/50 shadow-sm backdrop-blur-md"
            >
              <Ionicons name="options-outline" size={20} color={colors.textPrimary} />
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </View>
    );
  };

  return (
    <View className="flex-1 bg-white">
      <StatusBar barStyle="dark-content" translucent backgroundColor="transparent" />

      {/* 1. Fixed Header Layer */}
      {renderFixedHeader()}

      {/* 2. Scrollable Content */}
      <Animated.FlatList
        ref={flatListRef}
        data={products}
        keyExtractor={(item, index) => item._id || `product-${index}`}
        renderItem={renderProductItem}
        numColumns={COLUMN_count}
        contentContainerStyle={{
          paddingHorizontal: GRID_SPACING,
          paddingBottom: insets.bottom + 80,
        }}
        columnWrapperStyle={{ justifyContent: 'space-between' }}
        ListHeaderComponent={renderScrollableHeader} // Hero + Search + Filters
        ListFooterComponent={renderFooter}
        showsVerticalScrollIndicator={false}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        onScroll={Animated.event([{ nativeEvent: { contentOffset: { y: scrollY } } }], {
          useNativeDriver: false,
          listener: handleScroll,
        })}
        scrollEventThrottle={16}
        ListEmptyComponent={
          isLoading ? (
            <ProductsListSkeleton />
          ) : isError ? (
            <View className="flex-1 items-center justify-center px-10 py-20">
              <View className="mb-6 h-20 w-20 items-center justify-center rounded-full bg-red-50">
                <Feather name="wifi-off" size={32} color={colors.error} />
              </View>
              <Text className="mb-2 text-center text-xl font-bold text-gray-900">
                Could not load products
              </Text>
              <Text className="mb-6 text-center text-gray-500">
                Check your connection and try again.
              </Text>
              <TouchableOpacity
                onPress={() => setRetryCount((c) => c + 1)}
                className="rounded-full bg-neutral-900 px-8 py-3"
              >
                <Text className="font-bold text-white">Retry</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View className="flex-1 items-center justify-center px-10 py-20">
              <View className="mb-6 h-20 w-20 items-center justify-center rounded-full bg-gray-50">
                <Feather name="search" size={32} color={colors.textMuted} />
              </View>
              <Text className="mb-2 text-center text-xl font-bold text-gray-900">
                No products found
              </Text>
              <Text className="mb-6 text-center text-gray-500">
                Try adjusting your filters or search query.
              </Text>
              <TouchableOpacity
                onPress={clearFilters}
                className="rounded-full bg-neutral-900 px-8 py-3"
              >
                <Text className="font-bold text-white">Clear All Filters</Text>
              </TouchableOpacity>
            </View>
          )
        }
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
      />

      {/* Back To Top Button */}
      {showBackToTop && (
        <TouchableOpacity
          className="absolute right-5 z-50 h-12 w-12 items-center justify-center rounded-full border border-white/20 bg-neutral-900/90 shadow-2xl"
          style={{ bottom: insets.bottom + 20 }}
          onPress={() => flatListRef.current?.scrollToOffset({ offset: 0, animated: true })}
          activeOpacity={0.8}
        >
          <Ionicons name="arrow-up" size={24} color={colors.surface} />
        </TouchableOpacity>
      )}

      {/* ── Filter Modal ── */}
      <Modal visible={showFilterModal} animationType="slide" presentationStyle="pageSheet">
        <View className="flex-1 bg-white">
          <View className="flex-row items-center justify-between border-b border-gray-100 px-6 py-4">
            <Text className="text-xl font-bold text-gray-900">Filters</Text>
            <TouchableOpacity
              onPress={() => setShowFilterModal(false)}
              className="h-8 w-8 items-center justify-center rounded-full bg-gray-100"
            >
              <Ionicons name="close" size={20} color={colors.textPrimary} />
            </TouchableOpacity>
          </View>

          <ScrollView className="flex-1 px-6">
            {/* Price Range */}
            <View className="border-b border-gray-100 py-6">
              <View className="mb-8 flex-row items-center justify-between">
                <Text className="text-sm font-bold text-gray-900">PRICE RANGE</Text>
                <Text className="text-sm font-bold text-blue-600">
                  ₹{priceRange[0]} - ₹{priceRange[1]}
                </Text>
              </View>
              <View className="items-center px-4">
                <MultiSlider
                  values={priceRange}
                  min={globalMinPrice}
                  max={globalMaxPrice}
                  step={100}
                  sliderLength={SCREEN_WIDTH - 80}
                  onValuesChange={(vals) => setPriceRange(vals)}
                  selectedStyle={{ backgroundColor: colors.primary }}
                  unselectedStyle={{ backgroundColor: '#E5E7EB' }}
                  markerStyle={{
                    backgroundColor: colors.surface,
                    height: 24,
                    width: 24,
                    borderWidth: 2,
                    borderColor: colors.primary,
                    shadowOpacity: 0.1,
                    shadowRadius: 3,
                  }}
                  trackStyle={{ height: 4 }}
                  // Allow overlap?
                  allowOverlap={false}
                  minMarkerOverlapDistance={10}
                />
              </View>
              <View className="mt-2 flex-row justify-between">
                <Text className="text-xs text-gray-400">₹{globalMinPrice}</Text>
                <Text className="text-xs text-gray-400">₹{globalMaxPrice}</Text>
              </View>
            </View>

            {/* Discount */}
            <View className="border-b border-gray-100 py-6">
              <View className="mb-4 flex-row items-center justify-between">
                <Text className="text-sm font-bold text-gray-900">MIN DISCOUNT</Text>
                <Text className="text-sm font-bold text-green-600">
                  {Math.round(minDiscount)}% +
                </Text>
              </View>
              <Slider
                style={{ width: '100%', height: 40 }}
                minimumValue={0}
                maximumValue={100}
                step={5}
                value={minDiscount}
                onValueChange={setMinDiscount}
                minimumTrackTintColor={colors.primary}
                maximumTrackTintColor="#E5E7EB"
                thumbTintColor={colors.primary}
              />
              <View className="mt-1 flex-row justify-between">
                <Text className="text-xs text-gray-400">0%</Text>
                <Text className="text-xs text-gray-400">100%</Text>
              </View>
            </View>

            {/* Popularity */}
            <View className="border-b border-gray-100 py-6">
              <Text className="mb-4 text-sm font-bold text-gray-900">POPULARITY</Text>
              <View className="flex-row flex-wrap gap-2">
                {[
                  { label: 'Exclusive', value: 'exclusive' },
                  { label: 'New Arrivals', value: 'new' },
                  { label: 'Best Sellers', value: 'best_selling' },
                  { label: 'Trending', value: 'trending' },
                ].map((item) => (
                  <TouchableOpacity
                    key={item.value}
                    onPress={() => setPopularity(popularity === item.value ? '' : item.value)}
                    className={`rounded-lg border px-4 py-2 ${popularity === item.value ? 'border-neutral-900 bg-neutral-900' : 'border-gray-200 bg-white'}`}
                  >
                    <Text
                      className={`text-sm font-medium ${popularity === item.value ? 'text-white' : 'text-gray-700'}`}
                    >
                      {item.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Sub Categories (if available) */}
            {availableSubCategories.length > 0 && (
              <View className="border-b border-gray-100 py-6">
                <Text className="mb-4 text-sm font-bold text-gray-900">SUB CATEGORIES</Text>
                <View className="flex-row flex-wrap gap-2">
                  {availableSubCategories.map((sub) => (
                    <TouchableOpacity
                      key={sub}
                      onPress={() => {
                        setSubCategory(subCategory === sub ? '' : sub);
                        setShowFilterModal(false); // Often users want to see results immediately
                      }}
                      className={`rounded-lg border px-4 py-2 ${subCategory === sub ? 'border-neutral-900 bg-neutral-900' : 'border-gray-200 bg-white'}`}
                    >
                      <Text
                        className={`text-sm font-medium ${subCategory === sub ? 'text-white' : 'text-gray-700'}`}
                      >
                        {sub}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}

            {/* Brands */}
            {availableBrands.length > 0 && (
              <View className="border-b border-gray-100 py-6">
                <Text className="mb-4 text-sm font-bold text-gray-900">BRANDS</Text>
                <View className="flex-row flex-wrap gap-2">
                  {availableBrands.map((b) => (
                    <TouchableOpacity
                      key={b}
                      onPress={() =>
                        setSelectedBrands(
                          selectedBrands.includes(b)
                            ? selectedBrands.filter((x) => x !== b)
                            : [...selectedBrands, b]
                        )
                      }
                      className={`rounded-lg border px-4 py-2 ${selectedBrands.includes(b) ? 'border-neutral-900 bg-neutral-900' : 'border-gray-200 bg-white'}`}
                    >
                      <Text
                        className={`text-sm font-medium ${selectedBrands.includes(b) ? 'text-white' : 'text-gray-700'}`}
                      >
                        {b}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}

            {/* Collections */}
            {availableCollections.length > 0 && (
              <View className="border-b border-gray-100 py-6">
                <Text className="mb-4 text-sm font-bold text-gray-900">COLLECTIONS</Text>
                <View className="flex-row flex-wrap gap-2">
                  {availableCollections.map((cId) => (
                    <TouchableOpacity
                      key={cId}
                      onPress={() =>
                        setSelectedCollections(
                          selectedCollections.includes(cId)
                            ? selectedCollections.filter((x) => x !== cId)
                            : [...selectedCollections, cId]
                        )
                      }
                      className={`rounded-lg border px-4 py-2 ${selectedCollections.includes(cId) ? 'border-neutral-900 bg-neutral-900' : 'border-gray-200 bg-white'}`}
                    >
                      <Text
                        className={`text-sm font-medium ${selectedCollections.includes(cId) ? 'text-white' : 'text-gray-700'}`}
                      >
                        {allCollectionsNames[cId] || 'Collection'}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}
          </ScrollView>

          <View className="border-t border-gray-100 bg-white p-6">
            <TouchableOpacity
              onPress={() => {
                setPriceFilterVersion((v) => v + 1);
                setShowFilterModal(false);
              }}
              className="w-full items-center rounded-full bg-neutral-900 py-4"
            >
              <Text className="text-base font-bold text-white">Show Results</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={clearFilters} className="mt-4 items-center">
              <Text className="font-semibold text-gray-500">Clear All Filters</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* ── Sort Modal ── */}
      <Modal visible={showSortModal} transparent animationType="fade">
        <TouchableOpacity
          className="flex-1 justify-end bg-black/50"
          activeOpacity={1}
          onPress={() => setShowSortModal(false)}
        >
          <View className="rounded-t-3xl bg-white p-6 pb-12">
            <View className="mb-6 flex-row items-center justify-between">
              <Text className="text-lg font-bold text-gray-900">Sort By</Text>
              <TouchableOpacity onPress={() => setShowSortModal(false)}>
                <Ionicons name="close" size={24} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>
            {[
              { label: 'Recommended', value: 'recommended' },
              { label: 'Newest Arrivals', value: 'newest' },
              { label: 'Price: Low to High', value: 'price_asc' },
              { label: 'Price: High to Low', value: 'price_desc' },
            ].map((opt) => (
              <TouchableOpacity
                key={opt.value}
                className="flex-row items-center justify-between border-b border-gray-100 py-4"
                onPress={() => {
                  setSort(opt.value as any);
                  setShowSortModal(false);
                }}
              >
                <Text
                  className={`text-base ${sort === opt.value ? 'font-bold text-neutral-900' : 'font-medium text-gray-600'}`}
                >
                  {opt.label}
                </Text>
                {sort === opt.value && <Ionicons name="checkmark" size={20} color={colors.textPrimary} />}
              </TouchableOpacity>
            ))}
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}
