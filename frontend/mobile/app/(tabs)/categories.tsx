import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  TextInput,
  ScrollView,
  Dimensions,
  StyleSheet,
  StatusBar,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api, { getImageUrl } from '../../src/api/client';
import { colors, shadows, borderRadius } from '../../src/theme';
import { useAuth } from '../../src/hooks/useAuth';
import { BannerCarousel } from '../../src/components/BannerCarousel';
import { CategoriesScreenSkeleton } from '../../src/components/SkeletonLoader';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const GRID_GAP = 12;
const ITEM_WIDTH = (SCREEN_WIDTH - 32 - GRID_GAP) / 2;

interface CategoryItem {
  _id?: string;
  name: string;
  slug?: string;
  images?: string[];
  categoryTags?: string[];
  subCategories?: string[];
}

interface CategoryTag {
  _id?: string;
  name?: string;
}

const categoryColors = [
  { bg: '#FEE2E2', accent: '#EF4444' },
  { bg: '#FEF3C7', accent: '#F59E0B' },
  { bg: '#D1FAE5', accent: '#10B981' },
  { bg: '#DBEAFE', accent: '#3B82F6' },
  { bg: '#E9D5FF', accent: '#A855F7' },
  { bg: '#FCE7F3', accent: '#EC4899' },
  { bg: '#F0FDFA', accent: '#14B8A6' },
  { bg: '#FDF2F8', accent: '#DB2777' },
];

export default function Categories() {
  const router = useRouter();
  const { user } = useAuth();
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [categoryTags, setCategoryTags] = useState<CategoryTag[]>([]);
  const [banners, setBanners] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [catRes, tagRes, bannerRes] = await Promise.all([
          api.get('/categories/public'),
          api.get('/category-tags/active'),
          api.get('/banners/public', {
            params: {
              position: 'categories_mobile',
              pageType: 'all_categories',
              userRole: user?.role || 'guest',
            },
          }),
        ]);

        const data = Array.isArray(catRes.data)
          ? catRes.data
          : catRes.data?.data || catRes.data?.categories || [];

        const list: CategoryItem[] = (data || [])
          .filter((c: any) => c && (c.name || c.title))
          .map((c: any) => ({
            _id: c._id,
            name: c.name || c.title || '',
            slug: c.slug,
            images: c.images && Array.isArray(c.images) ? c.images : [],
            categoryTags: c.categoryTags || [],
            subCategories: c.subCategories || [],
          }));

        setCategories(list);

        const tags = Array.isArray(tagRes.data) ? tagRes.data : tagRes.data?.data || [];
        setCategoryTags(tags.filter((t: any) => t && t.name));

        setBanners((bannerRes.data || []).filter((b: any) => b.isActive));
      } catch (e) {
        if (__DEV__) console.error('Fetch Categories Error:', e);
        setCategories([]);
        setFetchError(true);
      } finally {
        setLoading(false);
      }
    };
    setFetchError(false);
    load();
  }, [user, retryCount]);

  const handleRefresh = React.useCallback(() => {
    setRefreshing(true);
    setRetryCount((c) => c + 1);
  }, []);

  const filteredCategories = useMemo(() => {
    let list = categories;
    const q = searchQuery.trim().toLowerCase();

    if (q) {
      list = list.filter((c) => c.name.toLowerCase().includes(q));
    }

    if (selectedTag) {
      list = list.filter((c) =>
        (c.categoryTags || []).some((t) => t.toLowerCase() === selectedTag.toLowerCase())
      );
    }

    return list;
  }, [categories, searchQuery, selectedTag]);

  const groupedCategories = useMemo(() => {
    if (selectedTag) {
      return [{ tag: selectedTag, categories: filteredCategories }];
    }

    const tags = categoryTags.map((t) => t.name || '').filter(Boolean);
    const used = new Set(tags.map((t) => t.toLowerCase()));

    const groups: { tag: string; categories: CategoryItem[] }[] = tags.map((tag) => ({
      tag,
      categories: filteredCategories.filter((c) =>
        (c.categoryTags || []).some((t) => t.toLowerCase() === tag.toLowerCase())
      ),
    }));

    const untagged = filteredCategories.filter(
      (c) => !(c.categoryTags || []).some((t) => used.has(t.toLowerCase()))
    );

    if (untagged.length > 0) {
      groups.push({ tag: 'Other', categories: untagged });
    }

    return groups.filter((g) => g.categories.length > 0);
  }, [filteredCategories, categoryTags, selectedTag]);

  const renderCategoryCard = (item: CategoryItem, index: number) => {
    const colorScheme = categoryColors[index % categoryColors.length];
    const hasImage = item.images && item.images.length > 0;
    const subCount = item.subCategories?.length || 0;

    return (
      <TouchableOpacity
        key={item._id || item.name}
        style={[styles.categoryCard, shadows.card]}
        activeOpacity={0.9}
        onPress={() =>
          router.push({
            pathname: '/categories/[slug]',
            params: { slug: item.slug || item.name },
          })
        }
      >
        <View style={[styles.categoryImageContainer, { backgroundColor: colorScheme.bg }]}>
          {hasImage ? (
            <Image
              source={{ uri: getImageUrl(item.images![0]) }}
              style={styles.categoryImage}
              resizeMode="cover"
            />
          ) : (
            <Ionicons name="layers-outline" size={32} color={colorScheme.accent} />
          )}
        </View>

        <View style={styles.categoryInfo}>
          <Text style={styles.categoryName} numberOfLines={2}>
            {item.name}
          </Text>
          {subCount > 0 && <Text style={styles.categorySubcount}>{subCount} subcategories</Text>}
        </View>

        <View style={[styles.categoryArrow, { backgroundColor: colorScheme.bg }]}>
          <Ionicons name="chevron-forward" size={14} color={colorScheme.accent} />
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.headerTitle}>Categories</Text>
            <Text style={styles.headerSubtitle}>{categories.length} categories to explore</Text>
          </View>
        </View>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <Ionicons name="search-outline" size={18} color={colors.neutral[400]} />
          <TextInput
            placeholder="Search categories..."
            placeholderTextColor={colors.neutral[400]}
            value={searchQuery}
            onChangeText={setSearchQuery}
            style={styles.searchInput}
          />
          {searchQuery ? (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={18} color={colors.neutral[400]} />
            </TouchableOpacity>
          ) : null}
        </View>

        {/* Category Tags Chips */}
        {categoryTags.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.tagsContainer}
          >
            <TouchableOpacity
              style={[styles.tagChip, !selectedTag && styles.tagChipActive]}
              onPress={() => setSelectedTag(null)}
            >
              <Text style={[styles.tagChipText, !selectedTag && styles.tagChipTextActive]}>
                All
              </Text>
            </TouchableOpacity>
            {categoryTags.map((tag) => (
              <TouchableOpacity
                key={tag._id || tag.name}
                style={[styles.tagChip, selectedTag === tag.name && styles.tagChipActive]}
                onPress={() => setSelectedTag(selectedTag === tag.name ? null : tag.name || null)}
              >
                <Text
                  style={[styles.tagChipText, selectedTag === tag.name && styles.tagChipTextActive]}
                >
                  {tag.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}
      </View>

      {loading ? (
        <CategoriesScreenSkeleton />
      ) : fetchError ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="wifi-outline" size={48} color={colors.neutral[300]} />
          </View>
          <Text style={styles.emptyTitle}>Could not load categories</Text>
          <Text style={styles.emptySubtitle}>Check your connection and try again.</Text>
          <TouchableOpacity
            onPress={() => setRetryCount((c) => c + 1)}
            style={styles.retryBtn}
          >
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : groupedCategories.length === 0 ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="grid-outline" size={48} color={colors.neutral[300]} />
          </View>
          <Text style={styles.emptyTitle}>No categories found</Text>
          <Text style={styles.emptySubtitle}>
            {searchQuery
              ? `No results for "${searchQuery}"`
              : 'Check back later for new categories'}
          </Text>
        </View>
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={colors.primary}
              colors={[colors.primary]}
            />
          }
        >
          {/* Banner Carousel */}
          {banners.length > 0 && <BannerCarousel banners={banners} height={160} />}

          {/* Category Groups */}
          {groupedCategories.map((group, groupIndex) => (
            <View key={group.tag} style={styles.groupSection}>
              <Text style={styles.groupTitle}>{group.tag}</Text>
              <View style={styles.categoryGrid}>
                {group.categories.map((cat, idx) => renderCategoryCard(cat, groupIndex * 10 + idx))}
              </View>
            </View>
          ))}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundAlt,
  },
  header: {
    backgroundColor: colors.surface,
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingTop: 8,
    marginBottom: 14,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: -0.3,
  },
  headerSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 2,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.backgroundAlt,
    borderRadius: borderRadius.lg,
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderWidth: 1,
    borderColor: colors.border,
  },
  searchInput: {
    flex: 1,
    marginLeft: 10,
    fontSize: 15,
    color: colors.textPrimary,
  },
  tagsContainer: {
    paddingTop: 12,
    paddingBottom: 4,
  },
  tagChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: borderRadius.full,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: 8,
  },
  tagChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  tagChipText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  tagChipTextActive: {
    color: colors.surface,
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
    paddingHorizontal: 32,
  },
  emptyIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.neutral[100],
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
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
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  bannerContainer: {
    height: 120,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    marginBottom: 20,
  },
  bannerImage: {
    width: '100%',
    height: '100%',
  },
  groupSection: {
    marginBottom: 24,
  },
  groupTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 14,
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: GRID_GAP,
  },
  categoryCard: {
    width: ITEM_WIDTH,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: 14,
    flexDirection: 'column',
  },
  categoryImageContainer: {
    width: 52,
    height: 52,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    marginBottom: 12,
  },
  categoryImage: {
    width: '100%',
    height: '100%',
  },
  categoryInfo: {
    flex: 1,
  },
  categoryName: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    lineHeight: 18,
  },
  categorySubcount: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 4,
  },
  categoryArrow: {
    position: 'absolute',
    top: 14,
    right: 14,
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
