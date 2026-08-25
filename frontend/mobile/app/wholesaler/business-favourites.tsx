import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Image,
  Dimensions,
  Modal,
  ScrollView,
  StyleSheet,
  TextInput,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api, { getImageUrl } from '../../src/api/client';
import { useAuth } from '../../src/hooks/useAuth';
import { colors, spacing, borderRadius, shadows, typography } from '../../src/theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const COLUMN_COUNT = 2;
const GRID_SPACING = 12;
const ITEM_WIDTH = (SCREEN_WIDTH - GRID_SPACING * (COLUMN_COUNT + 1)) / COLUMN_COUNT;

interface Product {
  _id?: string;
  name?: string;
  category?: string;
  brand?: string;
  price?: number;
  mrp?: number;
  discountPercentage?: number;
  displayImage?: string;
  images?: string[];
  stock?: number;
}

interface Filters {
  categories: string[];
  subCategories: string[];
  brands: string[];
  states: string[];
  cities: string[];
}

export default function BusinessFavouritesScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { user, loading: authLoading } = useAuth();

  // Filters State
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubCategory, setSelectedSubCategory] = useState('');
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedAvailable, setSelectedAvailable] = useState<'' | 'true' | 'false'>('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');

  // Temp Filters State (for Modal)
  const [tempCategory, setTempCategory] = useState('');
  const [tempSubCategory, setTempSubCategory] = useState('');
  const [tempBrand, setTempBrand] = useState('');
  const [tempAvailable, setTempAvailable] = useState<'' | 'true' | 'false'>('');
  const [tempMinPrice, setTempMinPrice] = useState('');
  const [tempMaxPrice, setTempMaxPrice] = useState('');

  // Data State
  const [products, setProducts] = useState<Product[]>([]);
  const [filters, setFilters] = useState<Filters>({
    categories: [],
    subCategories: [],
    brands: [],
    states: [],
    cities: [],
  });
  const [cityName, setCityName] = useState('');
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showFilterModal, setShowFilterModal] = useState(false);

  const isWholesaler = user?.role === 'wholesaler';

  // Redirect non-wholesalers — render nothing while auth is still loading
  // to prevent a flash of protected content before the redirect fires
  useEffect(() => {
    if (!authLoading && !isWholesaler) {
      router.replace('/(tabs)/home');
    }
  }, [isWholesaler, authLoading]);

  // While auth is resolving or if not a wholesaler, show nothing
  if (authLoading || !isWholesaler) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  const fetchProducts = useCallback(async () => {
    if (!isWholesaler) return;
    setLoading(true);
    try {
      const params: Record<string, string> = { type: 'business' };
      if (selectedCategory) params.category = selectedCategory;
      if (selectedSubCategory) params.sub_category = selectedSubCategory;
      if (selectedBrand) params.brand = selectedBrand;
      if (selectedAvailable) params.available = selectedAvailable;
      if (minPrice) params.min_price = minPrice;
      if (maxPrice) params.max_price = maxPrice;

      const res = await api.get('/recommendations/favourites', { params });
      const data = res.data || {};
      setProducts(data.products || []);
      setTotal(data.total || 0);
      setCityName(data.cityName || '');
      if (data.filters) {
        setFilters(data.filters);
      }
    } catch (err) {
      if (__DEV__) console.warn('Failed to fetch business favourites', err);
    } finally {
      setLoading(false);
    }
  }, [
    isWholesaler,
    selectedCategory,
    selectedSubCategory,
    selectedBrand,
    selectedAvailable,
    minPrice,
    maxPrice,
  ]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const openFilters = () => {
    setTempCategory(selectedCategory);
    setTempSubCategory(selectedSubCategory);
    setTempBrand(selectedBrand);
    setTempAvailable(selectedAvailable);
    setTempMinPrice(minPrice);
    setTempMaxPrice(maxPrice);
    setShowFilterModal(true);
  };

  const applyFilters = () => {
    setSelectedCategory(tempCategory);
    setSelectedSubCategory(tempSubCategory);
    setSelectedBrand(tempBrand);
    setSelectedAvailable(tempAvailable);
    setMinPrice(tempMinPrice);
    setMaxPrice(tempMaxPrice);
    setShowFilterModal(false);
  };

  const clearFilters = () => {
    setTempCategory('');
    setTempSubCategory('');
    setTempBrand('');
    setTempAvailable('');
    setTempMinPrice('');
    setTempMaxPrice('');
  };

  const hasActiveFilters =
    selectedCategory ||
    selectedSubCategory ||
    selectedBrand ||
    selectedAvailable ||
    minPrice ||
    maxPrice;

  const renderProductItem = ({ item }: { item: Product }) => {
    const img = item.displayImage || (item.images?.length ? item.images[0] : null);
    const imgUrl = img ? getImageUrl(img) : null;
    const hasDiscount = item.mrp && item.price && item.mrp > item.price;
    const discount =
      item.discountPercentage ||
      (hasDiscount ? Math.round(((item.mrp! - item.price!) / item.mrp!) * 100) : 0);
    const isOutOfStock = (item.stock || 0) <= 0;

    return (
      <TouchableOpacity
        style={{ width: ITEM_WIDTH, marginBottom: 20 }}
        activeOpacity={0.8}
        onPress={() => item._id && router.push(`/products/${item._id}`)}
      >
        <View style={styles.imageCard}>
          {imgUrl ? (
            <Image source={{ uri: imgUrl }} style={styles.productImage} resizeMode="cover" />
          ) : (
            <View style={styles.placeholderContainer}>
              <Ionicons name="image-outline" size={32} color={colors.neutral[300]} />
            </View>
          )}

          {hasDiscount && discount > 0 && (
            <View style={styles.discountBadge}>
              <Text style={styles.discountText}>{discount}% OFF</Text>
            </View>
          )}

          {isOutOfStock && (
            <View style={styles.outOfStockOverlay}>
              <View style={styles.outOfStockBadge}>
                <Text style={styles.outOfStockText}>Out of Stock</Text>
              </View>
            </View>
          )}
        </View>

        <View style={{ paddingHorizontal: 4 }}>
          <Text style={styles.brandText} numberOfLines={1}>
            {item.brand || 'Stationery'}
          </Text>
          <Text style={styles.nameText} numberOfLines={2}>
            {item.name}
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }}>
            <Text style={styles.priceText}>₹{item.price?.toLocaleString()}</Text>
            {hasDiscount && (
              <Text style={styles.mrpText}>₹{item.mrp?.toLocaleString()}</Text>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
        </TouchableOpacity>
        <View style={styles.titleContainer}>
          <Text style={styles.headerTitle}>Business Favourites</Text>
          {cityName ? (
            <View style={styles.cityBadge}>
              <Text style={styles.cityBadgeText}>📍 {cityName}</Text>
            </View>
          ) : null}
        </View>
        <TouchableOpacity onPress={openFilters} style={styles.filterButton}>
          <Ionicons name="options-outline" size={22} color="#FFFFFF" />
          {hasActiveFilters && <View style={styles.activeFilterDot} />}
        </TouchableOpacity>
      </View>

      {/* Subtitle */}
      <View style={styles.subtitleContainer}>
        <Text style={styles.subtitleText}>
          Top products by wholesaler order volume, ranked highest to lowest.
        </Text>
      </View>

      {/* Products Grid */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : products.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="file-tray-outline" size={48} color={colors.neutral[300]} />
          <Text style={styles.emptyText}>No products found</Text>
          {hasActiveFilters && (
            <TouchableOpacity onPress={clearFilters} style={styles.clearFiltersBtn}>
              <Text style={styles.clearFiltersBtnText}>Reset Filters</Text>
            </TouchableOpacity>
          )}
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => item._id || ''}
          renderItem={renderProductItem}
          numColumns={2}
          contentContainerStyle={{ padding: GRID_SPACING }}
          columnWrapperStyle={{ justifyContent: 'space-between' }}
        />
      )}

      {/* Filters Modal */}
      <Modal visible={showFilterModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalHeaderTitle}>Filters</Text>
              <TouchableOpacity onPress={() => setShowFilterModal(false)}>
                <Ionicons name="close" size={24} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalForm} contentContainerStyle={{ paddingBottom: 40 }}>
              {/* Category */}
              <Text style={styles.filterLabel}>Category</Text>
              <View style={styles.pickerContainer}>
                {filters.categories.map((c) => (
                  <TouchableOpacity
                    key={c}
                    style={[
                      styles.chip,
                      tempCategory === c && styles.activeChip,
                    ]}
                    onPress={() => setTempCategory(tempCategory === c ? '' : c)}
                  >
                    <Text
                      style={[
                        styles.chipText,
                        tempCategory === c && styles.activeChipText,
                      ]}
                    >
                      {c}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Sub-Category */}
              {filters.subCategories.length > 0 && (
                <>
                  <Text style={styles.filterLabel}>Sub-Category</Text>
                  <View style={styles.pickerContainer}>
                    {filters.subCategories.map((sc) => (
                      <TouchableOpacity
                        key={sc}
                        style={[
                          styles.chip,
                          tempSubCategory === sc && styles.activeChip,
                        ]}
                        onPress={() => setTempSubCategory(tempSubCategory === sc ? '' : sc)}
                      >
                        <Text
                          style={[
                            styles.chipText,
                            tempSubCategory === sc && styles.activeChipText,
                          ]}
                        >
                          {sc}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </>
              )}

              {/* Brand */}
              {filters.brands.length > 0 && (
                <>
                  <Text style={styles.filterLabel}>Brand</Text>
                  <View style={styles.pickerContainer}>
                    {filters.brands.map((b) => (
                      <TouchableOpacity
                        key={b}
                        style={[
                          styles.chip,
                          tempBrand === b && styles.activeChip,
                        ]}
                        onPress={() => setTempBrand(tempBrand === b ? '' : b)}
                      >
                        <Text
                          style={[
                            styles.chipText,
                            tempBrand === b && styles.activeChipText,
                          ]}
                        >
                          {b}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </>
              )}

              {/* Availability */}
              <Text style={styles.filterLabel}>Availability</Text>
              <View style={{ flexDirection: 'row', gap: 10 }}>
                {([
                  { label: 'All', value: '' },
                  { label: 'In Stock', value: 'true' },
                  { label: 'Out of Stock', value: 'false' },
                ] as const).map((opt) => (
                  <TouchableOpacity
                    key={opt.value}
                    style={[
                      styles.availBtn,
                      tempAvailable === opt.value && styles.activeAvailBtn,
                    ]}
                    onPress={() => setTempAvailable(opt.value)}
                  >
                    <Text
                      style={[
                        styles.availBtnText,
                        tempAvailable === opt.value && styles.activeAvailBtnText,
                      ]}
                    >
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Price Range */}
              <Text style={styles.filterLabel}>Price Range (₹)</Text>
              <View style={styles.priceInputRow}>
                <TextInput
                  placeholder="Min"
                  value={tempMinPrice}
                  onChangeText={setTempMinPrice}
                  keyboardType="numeric"
                  style={styles.priceInput}
                  placeholderTextColor={colors.neutral[400]}
                />
                <Text style={styles.priceInputSeparator}>–</Text>
                <TextInput
                  placeholder="Max"
                  value={tempMaxPrice}
                  onChangeText={setTempMaxPrice}
                  keyboardType="numeric"
                  style={styles.priceInput}
                  placeholderTextColor={colors.neutral[400]}
                />
              </View>
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity onPress={clearFilters} style={styles.clearBtn}>
                <Text style={styles.clearBtnText}>Clear All</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={applyFilters} style={styles.applyBtn}>
                <Text style={styles.applyBtnText}>Apply</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    backgroundColor: '#0f3322',
  },
  backButton: {
    padding: 4,
  },
  titleContainer: {
    flex: 1,
    marginLeft: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  cityBadge: {
    backgroundColor: 'rgba(255,255,255,0.15)',
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  cityBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  filterButton: {
    padding: 6,
    position: 'relative',
  },
  activeFilterDot: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.accent,
  },
  subtitleContainer: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    backgroundColor: '#1a4d33',
  },
  subtitleText: {
    fontSize: 13,
    color: '#E0F2FE',
    lineHeight: 18,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  clearFiltersBtn: {
    marginTop: spacing.lg,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    backgroundColor: '#1a4d33',
    borderRadius: borderRadius.full,
  },
  clearFiltersBtnText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  imageCard: {
    position: 'relative',
    aspectRatio: 3 / 4,
    width: '100%',
    borderRadius: borderRadius.lg,
    backgroundColor: colors.neutral[100],
    overflow: 'hidden',
    marginBottom: spacing.xs,
    ...shadows.sm,
  },
  productImage: {
    width: '100%',
    height: '100%',
  },
  placeholderContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  discountBadge: {
    position: 'absolute',
    top: 6,
    left: 6,
    backgroundColor: colors.success,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: borderRadius.xs,
  },
  discountText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  outOfStockOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.6)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  outOfStockBadge: {
    backgroundColor: colors.neutral[900],
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: borderRadius.full,
  },
  outOfStockText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  brandText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.textMuted,
    textTransform: 'uppercase',
  },
  nameText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textPrimary,
    lineHeight: 18,
    marginTop: 2,
  },
  priceText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
  },
  mrpText: {
    fontSize: 11,
    color: colors.textMuted,
    textDecorationLine: 'line-through',
    marginLeft: 6,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    height: '80%',
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    overflow: 'hidden',
  },
  modalHeader: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalHeaderTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  modalForm: {
    flex: 1,
    padding: spacing.lg,
  },
  filterLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  pickerContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: spacing.xs,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: '#FFFFFF',
  },
  activeChip: {
    borderColor: '#1a4d33',
    backgroundColor: '#E6F4EA',
  },
  chipText: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  activeChipText: {
    color: '#1a4d33',
    fontWeight: '600',
  },
  availBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  activeAvailBtn: {
    borderColor: '#1a4d33',
    backgroundColor: '#1a4d33',
  },
  availBtnText: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  activeAvailBtnText: {
    color: '#FFFFFF',
  },
  priceInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  priceInput: {
    flex: 1,
    height: 44,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    fontSize: 14,
    color: colors.textPrimary,
  },
  priceInputSeparator: {
    color: colors.textMuted,
  },
  modalFooter: {
    flexDirection: 'row',
    padding: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    gap: 12,
    backgroundColor: '#FFFFFF',
  },
  clearBtn: {
    flex: 1,
    height: 48,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clearBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  applyBtn: {
    flex: 2,
    height: 48,
    borderRadius: borderRadius.md,
    backgroundColor: '#1a4d33',
    alignItems: 'center',
    justifyContent: 'center',
  },
  applyBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
