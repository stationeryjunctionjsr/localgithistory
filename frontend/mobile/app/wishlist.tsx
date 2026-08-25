import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Image,
  StyleSheet,
  StatusBar,
  Alert,
  AppState,
  AppStateStatus,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api, { getImageUrl, SESSION_KEY } from '../src/api/client';
import * as SecureStore from 'expo-secure-store';
import { colors, shadows, borderRadius } from '../src/theme';
import { useAuth } from '../src/hooks/useAuth';
import {
  getGuestWishlist,
  removeGuestWishlistItem,
  addGuestCartItem,
} from '../src/services/guestStore';
import Toast from 'react-native-toast-message';
import { WishlistScreenSkeleton } from '../src/components/SkeletonLoader';

interface WishlistItem {
  _id?: string;
  productId?: string;
  product?: any;
  addedAt?: string;
}

export default function Wishlist() {
  const router = useRouter();
  const { user } = useAuth();
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [addingId, setAddingId] = useState<string | null>(null);

  const fetchWishlist = useCallback(async () => {
    setLoading(true);
    setFetchError(false);
    try {
      if (user) {
        const res = await api.get('/wishlist');
        const data = res.data?.items || res.data || [];
        setItems(data);
      } else {
        const guestWishlist = await getGuestWishlist();
        const mapped: WishlistItem[] = guestWishlist.map((g) => ({
          _id: g.productId,
          productId: g.productId,
          product: g.product || { name: 'Product', price: 0 },
        }));
        setItems(mapped);
      }
    } catch (e) {
      setFetchError(true);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Track current interval so AppState listener can clear/restart it
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useFocusEffect(
    useCallback(() => {
      fetchWishlist();
      // 60s interval (was 5s). useFocusEffect stops this when the screen loses focus.
      intervalRef.current = setInterval(fetchWishlist, 60_000);

      // AppState guard: pause polling when app is backgrounded
      const handleAppStateChange = (nextState: AppStateStatus) => {
        if (nextState === 'active') {
          fetchWishlist(); // Immediately refresh when foregrounded
          if (!intervalRef.current) {
            intervalRef.current = setInterval(fetchWishlist, 60_000);
          }
        } else {
          if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
        }
      };

      const subscription = AppState.addEventListener('change', handleAppStateChange);
      return () => {
        subscription.remove();
        if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      };
    }, [fetchWishlist])
  );

  const removeItem = async (productId?: string) => {
    if (!productId) return;

    Alert.alert('Remove from Wishlist', 'Are you sure you want to remove this item?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          setRemovingId(productId);
          try {
            if (user) {
              await api.delete(`/wishlist/${productId}`);
            } else {
              await removeGuestWishlistItem(productId);
            }
            fetchWishlist();
          } catch {
            Toast.show({
              type: 'error',
              text1: 'Error',
              text2: 'Failed to remove item. Please try again.',
            });
          }
          setRemovingId(null);
        },
      },
    ]);
  };

  const addToCart = async (productId?: string, product?: any) => {
    if (!productId) return;
    setAddingId(productId);
    try {
      if (user) {
        const sessionId = await SecureStore.getItemAsync(SESSION_KEY);
        await api.post('/cart', { productId, quantity: 1, sessionId });
      } else {
        await addGuestCartItem(productId, 1, product);
      }
      Toast.show({
        type: 'success',
        text1: 'Added to Cart',
        text2: `${product?.name || 'Item'} added to cart successfully.`,
      });
    } catch (e: any) {
      const msg = e?.response?.data?.detail || 'Could not add to cart.';
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: msg,
      });
    }
    setAddingId(null);
  };

  const renderItem = ({ item }: { item: WishlistItem }) => {
    const name = item?.product?.name || 'Item';
    const price = item?.product?.price || 0;
    const mrp = item?.product?.mrp;
    const hasDiscount = mrp && mrp > price;
    const rawImg = item?.product?.displayImage || item?.product?.images?.[0];
    const img = rawImg ? getImageUrl(rawImg) : null;
    const productId = item?.product?._id || item?.productId;

    return (
      <View style={[styles.wishlistItem, shadows.card]}>
        <TouchableOpacity
          style={styles.itemImage}
          onPress={() =>
            productId && router.push({ pathname: '/products/[id]', params: { id: productId } })
          }
          activeOpacity={0.9}
        >
          {img ? (
            <Image source={{ uri: img }} style={styles.image} resizeMode="cover" />
          ) : (
            <View style={styles.imagePlaceholder}>
              <Ionicons name="heart" size={28} color="#EC4899" />
            </View>
          )}
        </TouchableOpacity>

        <View style={styles.itemInfo}>
          <Text style={styles.itemName} numberOfLines={2}>
            {name}
          </Text>
          <View style={styles.priceRow}>
            <Text style={styles.itemPrice}>₹{price.toLocaleString()}</Text>
            {hasDiscount && <Text style={styles.itemMrp}>₹{mrp.toLocaleString()}</Text>}
          </View>

          <View style={styles.actionRow}>
            <TouchableOpacity
              style={styles.addToCartButton}
              onPress={() => addToCart(productId, item.product)}
              disabled={addingId === productId}
              activeOpacity={0.9}
            >
              <View style={styles.addToCartGradient}>
                {addingId === productId ? (
                  <ActivityIndicator color={colors.surface} size="small" />
                ) : (
                  <>
                    <Ionicons name="cart-outline" size={14} color={colors.surface} />
                    <Text style={styles.addToCartText}>Add to Cart</Text>
                  </>
                )}
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.removeButton}
              onPress={() => removeItem(productId)}
              disabled={removingId === productId}
              activeOpacity={0.7}
            >
              {removingId === productId ? (
                <ActivityIndicator color={colors.error} size="small" />
              ) : (
                <Ionicons name="trash-outline" size={18} color={colors.error} />
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          activeOpacity={0.7}
        >
          <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={styles.headerTitle}>Wishlist</Text>
          {items.length > 0 && (
            <View style={styles.headerBadge}>
              <Text style={styles.headerBadgeText}>{items.length}</Text>
            </View>
          )}
        </View>
        <View style={{ width: 40 }} />
      </View>

      {loading ? (
        <WishlistScreenSkeleton />
      ) : fetchError ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="cloud-offline-outline" size={48} color={colors.neutral[300]} />
          </View>
          <Text style={styles.emptyTitle}>Could not load wishlist</Text>
          <Text style={styles.emptySubtitle}>Please check your connection and try again</Text>
          <TouchableOpacity
            style={styles.exploreButton}
            onPress={fetchWishlist}
            activeOpacity={0.9}
          >
            <View style={styles.exploreGradient}>
              <Text style={styles.exploreButtonText}>Retry</Text>
            </View>
          </TouchableOpacity>
        </View>
      ) : items.length === 0 ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="heart-outline" size={48} color="#EC4899" />
          </View>
          <Text style={styles.emptyTitle}>Your wishlist is empty</Text>
          <Text style={styles.emptySubtitle}>Save items you love and come back to them later</Text>
          <TouchableOpacity
            style={styles.exploreButton}
            onPress={() => router.push('/products')}
            activeOpacity={0.9}
          >
            <View style={styles.exploreGradient}>
              <Text style={styles.exploreButtonText}>Start Exploring</Text>
            </View>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item, idx) => item._id || item.productId || String(idx)}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    width: 40,
    height: 40,
    backgroundColor: colors.backgroundAlt,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  headerBadge: {
    marginLeft: 8,
    backgroundColor: '#FCE4EC',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: borderRadius.full,
  },
  headerBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#EC4899',
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
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: '#FCE4EC',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 28,
  },
  exploreButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
  },
  exploreGradient: {
    paddingVertical: 14,
    paddingHorizontal: 28,
    backgroundColor: colors.primary,
    alignItems: 'center',
  },
  exploreButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.surface,
  },
  listContent: {
    padding: 16,
    paddingBottom: 40,
  },
  wishlistItem: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: 12,
    marginBottom: 12,
  },
  itemImage: {
    width: 88,
    height: 88,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    backgroundColor: colors.backgroundAlt,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  imagePlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  itemInfo: {
    flex: 1,
    marginLeft: 14,
    justifyContent: 'space-between',
  },
  itemName: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
    lineHeight: 18,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  itemPrice: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.primary,
  },
  itemMrp: {
    fontSize: 12,
    color: colors.textMuted,
    textDecorationLine: 'line-through',
    marginLeft: 8,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    gap: 8,
  },
  addToCartButton: {
    flex: 1,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
  },
  addToCartGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    backgroundColor: colors.primary,
  },
  addToCartText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.surface,
    marginLeft: 6,
  },
  removeButton: {
    width: 40,
    height: 40,
    backgroundColor: '#FEE2E2',
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
