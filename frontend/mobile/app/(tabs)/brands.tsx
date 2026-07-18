import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TextInput,
  Image,
  TouchableOpacity,
  Dimensions,
  StyleSheet,
  StatusBar,
  Modal,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api, { getImageUrl } from '../../src/api/client';
import { useAuth } from '../../src/hooks/useAuth';
import { BannerCarousel } from '../../src/components/BannerCarousel';
import { colors, shadows } from '../../src/theme';
import { BrandsScreenSkeleton } from '../../src/components/SkeletonLoader';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const COLUMNS = 3;
const SPACING = 12;
const ITEM_WIDTH = (SCREEN_WIDTH - SPACING * (COLUMNS + 1)) / COLUMNS;

interface Brand {
  _id?: string;
  name?: string;
  logoUrl?: string;
  logo?: string;
}

interface Category {
  _id: string;
  name: string;
  subCategories?: string[];
}

export default function Brands() {
  const router = useRouter();
  const { user } = useAuth();

  // Data State
  const [allBrands, setAllBrands] = useState<Brand[]>([]);
  const [filteredBrands, setFilteredBrands] = useState<Brand[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [banners, setBanners] = useState<any[]>([]);

  // UI State
  const [loading, setLoading] = useState(true);
  const [loadingFilter, setLoadingFilter] = useState(false);
  const [search, setSearch] = useState('');
  const [showFilterModal, setShowFilterModal] = useState(false);

  // Filter Selection
  const [selectedSubCategory, setSelectedSubCategory] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [fetchError, setFetchError] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Initial Load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [brandsRes, catsRes, bannerRes] = await Promise.all([
          api.get('/brands/public'),
          api.get('/categories/public'),
          api
            .get('/banners/public', {
              params: {
                position: 'all_brands_mobile',
                pageType: 'all_brands',
                userRole: user?.role || 'guest',
              },
            })
            .catch(() => ({ data: [] })),
        ]);

        const brandsList = Array.isArray(brandsRes.data)
          ? brandsRes.data
          : brandsRes.data?.brands || [];
        setAllBrands(brandsList);
        setFilteredBrands(brandsList); // Initially show all

        const catsList = Array.isArray(catsRes.data) ? catsRes.data : catsRes.data?.data || [];
        setCategories(catsList);

        const activeBanners = (bannerRes.data || []).filter((b: any) => b.isActive);
        setBanners(activeBanners);
      } catch (e) {
        if (__DEV__) console.error('Failed to load brands/categories', e);
        setFetchError(true);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    };
    loadData();
  }, [user, retryCount]);

  const handleRefresh = React.useCallback(() => {
    setRefreshing(true);
    setRetryCount((c) => c + 1);
  }, []);

  // Search Logic (Local)
  useEffect(() => {
    if (loadingFilter) return; // Don't override while fetching filter results

    // If no complex filter is active, filter allBrands by search
    if (!selectedCategory) {
      const term = search.trim().toLowerCase();
      if (!term) {
        setFilteredBrands(allBrands);
      } else {
        setFilteredBrands(allBrands.filter((b) => (b.name || '').toLowerCase().includes(term)));
      }
    } else {
      // If complex filter IS active, we filter the *already filtered* list by search
      // (Note: The effect below handles the API fetching for category/subcat)
    }
  }, [search, allBrands, selectedCategory, loadingFilter]);

  // complex Filter Logic (Category/SubCategory)
  useEffect(() => {
    const applyFilters = async () => {
      if (!selectedCategory) {
        // Reset to showing all (respecting search)
        const term = search.trim().toLowerCase();
        setFilteredBrands(
          term ? allBrands.filter((b) => (b.name || '').toLowerCase().includes(term)) : allBrands
        );
        return;
      }

      setLoadingFilter(true);
      try {
        // Fetch products for this category/subcategory to find relevant brands
        const params: any = { category: selectedCategory.name };
        if (selectedSubCategory) params.subCategory = selectedSubCategory;

        const res = await api.get('/products/public', { params });
        const products = res.data.products || res.data || [];

        // Extract unique brand names from products
        const relevantBrandNames = new Set(products.map((p: any) => p.brand).filter(Boolean));

        // Filter the main brands list
        const matchingBrands = allBrands.filter((b) => relevantBrandNames.has(b.name));

        // Apply search on top if exists
        const term = search.trim().toLowerCase();
        const final = term
          ? matchingBrands.filter((b) => (b.name || '').toLowerCase().includes(term))
          : matchingBrands;

        setFilteredBrands(final);
      } catch (e) {
        if (__DEV__) console.error('Filter error', e);
        setFilteredBrands([]);
      } finally {
        setLoadingFilter(false);
      }
    };

    if (selectedCategory) {
      applyFilters();
    }
  }, [selectedCategory, selectedSubCategory, allBrands]); // Search is handled separately/additively in UI but here we re-run if underlying set changes

  const clearFilters = () => {
    setSelectedCategory(null);
    setSelectedSubCategory('');
    setSearch('');
    setShowFilterModal(false);
  };

  const renderBrandItem = ({ item }: { item: Brand }) => {
    const hasLogo = item.logoUrl || item.logo;
    return (
      <TouchableOpacity
        style={[styles.brandCard, { width: ITEM_WIDTH, height: ITEM_WIDTH * 1.1, marginHorizontal: SPACING / 2 }, shadows.card]}
        onPress={() =>
          router.push({ pathname: '/brands/[slug]', params: { slug: item.name || '' } })
        }
        activeOpacity={0.7}
      >
        <View style={styles.brandLogoContainer}>
          {hasLogo ? (
            <Image
              source={{ uri: getImageUrl(item.logoUrl || item.logo || '') }}
              style={styles.brandLogoImage}
              resizeMode="contain"
            />
          ) : (
            <Text style={styles.brandLogoFallback}>
              {(item.name || '?')[0].toUpperCase()}
            </Text>
          )}
        </View>
        <Text style={styles.brandName} numberOfLines={2}>
          {item.name}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />

      {/* Header */}
      <View style={styles.headerBar}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.headerTitle}>Brands</Text>
            <Text style={styles.headerSubtitle}>{filteredBrands.length} brands</Text>
          </View>
          <TouchableOpacity
            onPress={() => setShowFilterModal(true)}
            style={[styles.filterButton, selectedCategory ? styles.filterButtonActive : styles.filterButtonInactive]}
          >
            <Ionicons name="filter" size={20} color={selectedCategory ? colors.surface : colors.textPrimary} />
          </TouchableOpacity>
        </View>

        {/* Search */}
        <View style={styles.searchBar}>
          <Ionicons name="search" size={18} color={colors.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search brands..."
            placeholderTextColor={colors.textMuted}
            value={search}
            onChangeText={setSearch}
          />
        </View>

        {/* Active Filter Chips */}
        {selectedCategory && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipScroll}>
            <TouchableOpacity
              onPress={() => setSelectedCategory(null)}
              style={styles.activeChip}
            >
              <Text style={styles.activeChipText}>{selectedCategory.name}</Text>
              <Ionicons name="close" size={14} color={colors.surface} />
            </TouchableOpacity>
            {selectedSubCategory ? (
              <TouchableOpacity
                onPress={() => setSelectedSubCategory('')}
                style={styles.activeChip}
              >
                <Text style={styles.activeChipText}>{selectedSubCategory}</Text>
                <Ionicons name="close" size={14} color={colors.surface} />
              </TouchableOpacity>
            ) : null}
          </ScrollView>
        )}
      </View>

      {/* Banner Carousel */}
      {banners.length > 0 && !loading && <BannerCarousel banners={banners} height={160} />}

      {/* Content */}
      {loading || loadingFilter ? (
        <BrandsScreenSkeleton />
      ) : fetchError ? (
        <View style={styles.centered}>
          <Ionicons name="cloud-offline-outline" size={48} color={colors.neutral[300]} />
          <Text style={styles.emptyText}>Could not load brands</Text>
          <TouchableOpacity
            onPress={() => setRetryCount((c) => c + 1)}
            style={styles.retryBtn}
          >
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : filteredBrands.length === 0 ? (
        <View style={styles.centered}>
          <Ionicons name="search-outline" size={48} color={colors.neutral[300]} />
          <Text style={styles.emptyText}>No brands found</Text>
          <TouchableOpacity
            onPress={clearFilters}
            style={styles.clearButton}
          >
            <Text style={styles.clearButtonText}>Clear Filters</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={filteredBrands}
          keyExtractor={(item, index) => item._id || item.name || `brand-${index}`}
          renderItem={renderBrandItem}
          numColumns={COLUMNS}
          contentContainerStyle={{ paddingHorizontal: SPACING / 2, paddingTop: SPACING }}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={colors.primary}
              colors={[colors.primary]}
            />
          }
        />
      )}

      {/* Filter Modal */}
      <Modal visible={showFilterModal} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modalContainer}>
          <View style={styles.modalHandle} />
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Filter by Category</Text>
            <TouchableOpacity onPress={() => setShowFilterModal(false)}>
              <Ionicons name="close" size={24} color={colors.textPrimary} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody}>
            <Text style={styles.sectionLabel}>Category</Text>
            <View style={styles.chipGrid}>
              {categories.map((cat) => {
                const isSelected = selectedCategory?._id === cat._id;
                return (
                  <TouchableOpacity
                    key={cat._id}
                    onPress={() => {
                      setSelectedCategory(cat);
                      setSelectedSubCategory('');
                    }}
                    style={[styles.filterChip, isSelected ? styles.filterChipActive : styles.filterChipInactive]}
                  >
                    <Text style={[styles.filterChipText, isSelected ? styles.filterChipTextActive : styles.filterChipTextInactive]}>
                      {cat.name}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            {selectedCategory &&
              selectedCategory.subCategories &&
              selectedCategory.subCategories.length > 0 && (
                <>
                  <Text style={[styles.sectionLabel, { marginTop: 24 }]}>Sub Category</Text>
                  <View style={styles.chipGrid}>
                    {selectedCategory.subCategories.map((sub) => {
                      const isSelected = selectedSubCategory === sub;
                      return (
                        <TouchableOpacity
                          key={sub}
                          onPress={() =>
                            setSelectedSubCategory(selectedSubCategory === sub ? '' : sub)
                          }
                          style={[styles.filterChip, isSelected ? styles.filterChipActive : styles.filterChipInactive]}
                        >
                          <Text style={[styles.filterChipText, isSelected ? styles.filterChipTextActive : styles.filterChipTextInactive]}>
                            {sub}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </>
              )}
          </ScrollView>

          <View style={styles.modalFooter}>
            <TouchableOpacity
              onPress={() => setShowFilterModal(false)}
              style={styles.showResultsButton}
            >
              <Text style={styles.showResultsText}>Show Results</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={clearFilters} style={styles.clearFiltersLink}>
              <Text style={styles.clearFiltersText}>Clear Filters</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  headerBar: {
    backgroundColor: colors.surface,
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 2,
  },
  filterButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
  },
  filterButtonActive: {
    backgroundColor: colors.primary,
  },
  filterButtonInactive: {
    backgroundColor: colors.backgroundAlt,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.backgroundAlt,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  searchInput: {
    flex: 1,
    marginLeft: 12,
    fontSize: 15,
    fontWeight: '500',
    color: colors.textPrimary,
  },
  chipScroll: {
    marginTop: 12,
  },
  activeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
  },
  activeChipText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.surface,
    marginRight: 4,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    marginTop: 16,
    fontSize: 15,
    color: colors.textMuted,
  },
  clearButton: {
    marginTop: 16,
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 20,
  },
  clearButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.surface,
  },
  retryBtn: {
    marginTop: 20,
    backgroundColor: colors.primary,
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 24,
  },
  retryText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 15,
  },
  brandCard: {
    marginBottom: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  brandLogoContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.backgroundAlt,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    marginBottom: 8,
  },
  brandLogoImage: {
    width: 48,
    height: 48,
  },
  brandLogoFallback: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textMuted,
  },
  brandName: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.textPrimary,
    textAlign: 'center',
    paddingHorizontal: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
  },
  modalHandle: {
    width: 48,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.border,
    alignSelf: 'center',
    marginTop: 12,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  modalBody: {
    flex: 1,
    paddingHorizontal: 24,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    color: colors.textMuted,
    marginTop: 16,
    marginBottom: 8,
  },
  chipGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterChip: {
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterChipInactive: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
  },
  filterChipText: {
    fontSize: 14,
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: colors.surface,
  },
  filterChipTextInactive: {
    color: colors.textSecondary,
  },
  modalFooter: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    padding: 24,
  },
  showResultsButton: {
    width: '100%',
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderRadius: 24,
    paddingVertical: 16,
  },
  showResultsText: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.surface,
  },
  clearFiltersLink: {
    marginTop: 16,
    alignItems: 'center',
  },
  clearFiltersText: {
    fontWeight: '600',
    color: colors.textMuted,
  },
});
