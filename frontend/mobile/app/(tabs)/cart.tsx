import React, { useCallback, useState } from 'react';
import { CartScreenSkeleton } from '../../src/components/SkeletonLoader';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  StyleSheet,
  StatusBar,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api, { getImageUrl } from '../../src/api/client';
import { colors, shadows, borderRadius } from '../../src/theme';
import Toast from 'react-native-toast-message';
import { useAuth } from '../../src/hooks/useAuth';
import {
  getGuestCart,
  updateGuestCartQty,
  removeGuestCartItem,
  addGuestCartItem,
  saveGuestCart,
} from '../../src/services/guestStore';

interface CartItem {
  _id?: string;
  productId?: string;
  product?: any;
  quantity?: number;
  price?: number;
  subtotal?: number;
}

export default function Cart() {
  const [items, setItems] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [giftWrap, setGiftWrap] = useState<any[]>([]);
  const [wishlist, setWishlist] = useState<any[]>([]);
  const [impulse, setImpulse] = useState<any[]>([]);
  const { user } = useAuth();
  const router = useRouter();

  const fetchCart = useCallback(async () => {
    setLoading(true);
    setFetchError(false);
    try {
      if (user) {
        const res = await api.get('/cart');
        // API returns { items: [...], subtotal, itemCount } — extract items array
        const data = res.data;
        setItems(Array.isArray(data) ? data : (data?.items ?? []));
      } else {
        const guestCart = await getGuestCart();
        const refreshedCart = await Promise.all(
          guestCart.map(async (g) => {
            try {
              const res = await api.get(`/products/public/${g.productId}`, {
                params: { role: 'customer' },
              });
              return {
                ...g,
                product: res.data,
              };
            } catch (err) {
              if (__DEV__) console.log(`Failed to refresh price for product ${g.productId}`, err);
              return g;
            }
          })
        );
        await saveGuestCart(refreshedCart);

        const mapped: CartItem[] = refreshedCart.map((g) => {
          const itemPrice = g.product?.price || 0;
          const itemQty = g.quantity || 1;
          return {
            _id: g.productId,
            productId: g.productId,
            product: g.product || { name: 'Product', price: 0 },
            quantity: itemQty,
            price: itemPrice,
            subtotal: itemPrice * itemQty,
          };
        });
        setItems(mapped);
      }
    } catch {
      setFetchError(true);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [user]);

  const fetchExtras = useCallback(async () => {
    try {
      const collectionsRes = await api.get('/collections/public', {
        params: { visiblePage: 'Cart', pageType: 'Cart', userRole: user?.role || 'guest' },
      });
      const cols = collectionsRes.data || [];

      const gCol = cols.find((c: any) => c.name === 'Gift Wrap');
      if (gCol?._id) {
        const pgRes = await api.get(`/collections/${gCol._id}/products`);
        setGiftWrap((pgRes.data || []).slice(0, 5));
      } else {
        setGiftWrap([]);
      }

      const ib = cols.find((c: any) => c.name === 'Impulse Buy');
      if (ib?._id) {
        const pRes = await api.get(`/collections/${ib._id}/products`);
        setImpulse((pRes.data || []).slice(0, 5));
      }

      if (user) {
        const wRes = await api.get('/wishlist').catch(() => null);
        if (wRes) setWishlist((wRes.data.items || []).slice(0, 5));
      }
    } catch (e) {
      if (__DEV__) console.log('Fetch Extras Error:', e);
    }
  }, [user]);

  useFocusEffect(
    useCallback(() => {
      fetchCart();
      fetchExtras();
      const interval = setInterval(() => {
        fetchCart();
        fetchExtras();
      }, 5000);
      return () => clearInterval(interval);
    }, [fetchCart, fetchExtras])
  );

  const updateQty = async (item: CartItem, newQty: number) => {
    if (newQty < 1) return;
    if (user) {
      if (!item._id) return;
      try {
        await api.put(`/cart/${item._id}`, { quantity: newQty });
        fetchCart();
      } catch {
        Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to update quantity' });
      }
    } else {
      if (!item.productId) return;
      await updateGuestCartQty(item.productId, newQty);
      fetchCart();
    }
  };

  const removeItem = async (item: CartItem) => {
    Alert.alert('Remove Item', 'Are you sure you want to remove this item?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          if (user) {
            if (!item._id) return;
            try {
              await api.delete(`/cart/${item._id}`);
              fetchCart();
            } catch {
              Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to remove item' });
            }
          } else {
            if (!item.productId) return;
            await removeGuestCartItem(item.productId);
            fetchCart();
          }
        },
      },
    ]);
  };

  const addToCart = async (productId: string, product?: any) => {
    try {
      if (user) {
        await api.post('/cart', { productId, quantity: 1 });
      } else {
        await addGuestCartItem(productId, 1, product);
      }
      fetchCart();
    } catch {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Could not add to cart' });
    }
  };

  const totalPrice = items.reduce((sum, item) => {
    const subtotal = item.subtotal !== undefined ? item.subtotal : (item.product?.price || 0) * (item.quantity || 1);
    return sum + subtotal;
  }, 0);

  const itemCount = items.reduce((sum, item) => sum + (item.quantity || 1), 0);

  const renderCartItem = ({ item }: { item: CartItem }) => {
    const name = item?.product?.name || 'Item';
    const qty = item?.quantity || 1;
    const price = item?.price !== undefined ? item.price : (item?.product?.price || 0);
    const itemSubtotal = item?.subtotal !== undefined ? item.subtotal : (price * qty);
    const rawImg = item?.product?.displayImage || item?.product?.images?.[0];
    const img = rawImg ? getImageUrl(rawImg) : null;

    return (
      <View style={[styles.cartItem, shadows.card]}>
        <TouchableOpacity
          style={styles.cartItemImage}
          onPress={() =>
            item?.product?._id &&
            router.push({ pathname: '/products/[id]', params: { id: item.product._id } })
          }
        >
          {img ? (
            <Image source={{ uri: img }} style={styles.itemImage} resizeMode="cover" />
          ) : (
            <View style={styles.itemImagePlaceholder}>
              <Ionicons name="cube-outline" size={24} color={colors.neutral[300]} />
            </View>
          )}
        </TouchableOpacity>

        <View style={styles.cartItemInfo}>
          <Text style={styles.itemName} numberOfLines={2}>
            {name}
          </Text>
          <Text style={styles.itemPrice}>₹{price.toLocaleString()}</Text>

          <View style={styles.quantityRow}>
            <View style={styles.quantityControls}>
              <TouchableOpacity
                style={styles.quantityButton}
                onPress={() => updateQty(item, Math.max(1, qty - 1))}
                activeOpacity={0.7}
              >
                <Ionicons name="remove" size={16} color={colors.textPrimary} />
              </TouchableOpacity>
              <Text style={styles.quantityText}>{qty}</Text>
              <TouchableOpacity
                style={styles.quantityButton}
                onPress={() => updateQty(item, qty + 1)}
                activeOpacity={0.7}
              >
                <Ionicons name="add" size={16} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.removeButton}
              onPress={() => removeItem(item)}
              activeOpacity={0.7}
            >
              <Ionicons name="trash-outline" size={18} color={colors.error} />
            </TouchableOpacity>
          </View>
        </View>

        <Text style={styles.itemTotal}>₹{itemSubtotal.toLocaleString()}</Text>
      </View>
    );
  };

  const UpsellCard = ({ item, onAdd }: { item: any; onAdd: () => void }) => (
    <TouchableOpacity
      style={[styles.upsellCard, shadows.sm]}
      activeOpacity={0.9}
      onPress={() =>
        item._id && router.push({ pathname: '/products/[id]', params: { id: item._id } })
      }
    >
      <Image
        source={{ uri: getImageUrl(item.images?.[0] || item.displayImage) }}
        style={styles.upsellImage}
        resizeMode="cover"
      />
      <View style={styles.upsellInfo}>
        <Text style={styles.upsellName} numberOfLines={2}>
          {item.name}
        </Text>
        <View style={styles.upsellPriceRow}>
          <Text style={styles.upsellPrice}>₹{item.price || item.mrp}</Text>
          <TouchableOpacity style={styles.upsellAddButton} onPress={onAdd}>
            <Ionicons name="add" size={16} color={colors.surface} />
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Shopping Cart</Text>
          <Text style={styles.headerSubtitle}>
            {itemCount} {itemCount === 1 ? 'item' : 'items'} in your cart
          </Text>
        </View>
      </View>

      {loading ? (
        <CartScreenSkeleton />
      ) : fetchError ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="cloud-offline-outline" size={48} color={colors.neutral[300]} />
          </View>
          <Text style={styles.emptyTitle}>Could not load cart</Text>
          <Text style={styles.emptySubtitle}>Please check your connection and try again</Text>
          <TouchableOpacity
            style={styles.browseButton}
            onPress={fetchCart}
            activeOpacity={0.8}
          >
            <Text style={styles.browseButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : items.length === 0 ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="cart-outline" size={48} color={colors.neutral[300]} />
          </View>
          <Text style={styles.emptyTitle}>Your cart is empty</Text>
          <Text style={styles.emptySubtitle}>Add items to your cart to get started</Text>
          <TouchableOpacity
            style={styles.browseButton}
            onPress={() => router.push('/products')}
            activeOpacity={0.8}
          >
            <Text style={styles.browseButtonText}>Browse Products</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          <FlatList
            data={items}
            keyExtractor={(item, idx) => item._id || item.productId || String(idx)}
            renderItem={renderCartItem}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            ListHeaderComponent={
              <View style={styles.noticeContainer}>
                <Ionicons name="information-circle-outline" size={14} color="#1E40AF" style={{ marginRight: 6 }} />
                <Text style={styles.noticeText}>Final prices will be calculated on Checkout</Text>
              </View>
            }
            ListFooterComponent={
              <View style={styles.upsellSections}>
                {/* Wishlist Link */}
                {user && (
                  <TouchableOpacity
                    style={[styles.wishlistLink, shadows.sm]}
                    onPress={() => router.push('/wishlist')}
                    activeOpacity={0.8}
                  >
                    <View style={styles.wishlistLinkContent}>
                      <View style={styles.wishlistIconContainer}>
                        <Ionicons name="heart" size={20} color="#EF4444" />
                      </View>
                      <View>
                        <Text style={styles.wishlistLinkTitle}>Your Wishlist</Text>
                        <Text style={styles.wishlistLinkSubtitle}>Move items to cart</Text>
                      </View>
                    </View>
                    <Ionicons name="chevron-forward" size={18} color={colors.neutral[400]} />
                  </TouchableOpacity>
                )}

                {/* Gift Wrap Section */}
                {giftWrap.length > 0 && (
                  <View style={styles.upsellSection}>
                    <View style={styles.upsellHeader}>
                      <Ionicons name="gift-outline" size={18} color={colors.accent} />
                      <Text style={styles.upsellTitle}>Make it a Gift</Text>
                    </View>
                    <FlatList
                      horizontal
                      data={giftWrap}
                      showsHorizontalScrollIndicator={false}
                      keyExtractor={(item) => item._id}
                      renderItem={({ item }) => (
                        <UpsellCard item={item} onAdd={() => addToCart(item._id, item)} />
                      )}
                    />
                  </View>
                )}

                {/* Wishlist Products */}
                {wishlist.length > 0 && (
                  <View style={styles.upsellSection}>
                    <View style={styles.upsellHeader}>
                      <Ionicons name="heart-outline" size={18} color="#EF4444" />
                      <Text style={styles.upsellTitle}>From Your Wishlist</Text>
                    </View>
                    <FlatList
                      horizontal
                      data={wishlist}
                      showsHorizontalScrollIndicator={false}
                      keyExtractor={(item) => item.product?._id}
                      renderItem={({ item }) => (
                        <UpsellCard
                          item={item.product}
                          onAdd={() => addToCart(item.product?._id, item.product)}
                        />
                      )}
                    />
                  </View>
                )}

                {/* Impulse Buy */}
                {impulse.length > 0 && (
                  <View style={styles.upsellSection}>
                    <View style={styles.upsellHeader}>
                      <Ionicons name="sparkles-outline" size={18} color={colors.primary} />
                      <Text style={styles.upsellTitle}>You Might Also Like</Text>
                    </View>
                    <FlatList
                      horizontal
                      data={impulse}
                      showsHorizontalScrollIndicator={false}
                      keyExtractor={(item) => item._id}
                      renderItem={({ item }) => (
                        <UpsellCard item={item} onAdd={() => addToCart(item._id, item)} />
                      )}
                    />
                  </View>
                )}
              </View>
            }
          />

          {/* Order Summary Footer */}
          <View style={[styles.footer, shadows.lg]}>
            <View style={styles.footerContent}>
              <View style={styles.footerSummary}>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Subtotal</Text>
                  <Text style={styles.summaryValue}>₹{totalPrice.toLocaleString()}</Text>
                </View>

                <View style={[styles.summaryRow, { borderTopWidth: 1, borderTopColor: colors.border, marginTop: 8, paddingTop: 8 }]}>
                  <Text style={styles.footerLabel}>
                    Total ({itemCount} {itemCount === 1 ? 'item' : 'items'})
                  </Text>
                  <Text style={styles.footerTotal}>₹{totalPrice.toLocaleString()}</Text>
                </View>
              </View>
              <TouchableOpacity
                style={styles.checkoutButton}
                onPress={() => router.push('/checkout')}
                activeOpacity={0.9}
              >
                <View style={styles.checkoutGradient}>
                  <Text style={styles.checkoutButtonText}>Proceed to Checkout</Text>
                  <Ionicons name="arrow-forward" size={18} color={colors.surface} />
                </View>
              </TouchableOpacity>
            </View>
          </View>
        </>
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
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
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
    fontSize: 20,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 24,
  },
  browseButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: borderRadius.full,
  },
  browseButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.surface,
  },
  listContent: {
    padding: 16,
    paddingBottom: 200,
  },
  cartItem: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: 12,
    marginBottom: 12,
  },
  cartItemImage: {
    width: 80,
    height: 80,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    backgroundColor: colors.backgroundAlt,
  },
  itemImage: {
    width: '100%',
    height: '100%',
  },
  itemImagePlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cartItemInfo: {
    flex: 1,
    marginLeft: 12,
    justifyContent: 'space-between',
  },
  itemName: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
    lineHeight: 18,
  },
  itemPrice: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.primary,
    marginTop: 4,
  },
  quantityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  quantityControls: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.backgroundAlt,
    borderRadius: borderRadius.md,
    padding: 4,
  },
  quantityButton: {
    width: 28,
    height: 28,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 6,
  },
  quantityText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginHorizontal: 12,
    minWidth: 20,
    textAlign: 'center',
  },
  removeButton: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  itemTotal: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textPrimary,
    position: 'absolute',
    top: 12,
    right: 12,
  },
  upsellSections: {
    marginTop: 16,
  },
  wishlistLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: 14,
    marginBottom: 20,
  },
  wishlistLinkContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  wishlistIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FEE2E2',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  wishlistLinkTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  wishlistLinkSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  upsellSection: {
    marginBottom: 24,
  },
  upsellHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  upsellTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginLeft: 8,
  },
  upsellCard: {
    width: 140,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    marginRight: 10,
    overflow: 'hidden',
  },
  upsellImage: {
    width: '100%',
    height: 100,
    backgroundColor: colors.backgroundAlt,
  },
  upsellInfo: {
    padding: 10,
  },
  upsellName: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.textPrimary,
    lineHeight: 15,
    height: 30,
  },
  upsellPriceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  upsellPrice: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
  },
  upsellAddButton: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
  },
  footerContent: {
    padding: 20,
    paddingBottom: 28,
  },
  footerSummary: {
    marginBottom: 14,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  summaryLabel: {
    fontSize: 13,
    color: colors.textMuted,
  },
  summaryValue: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  footerLabel: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  footerTotal: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.primary,
  },
  checkoutButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
  },
  checkoutGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    backgroundColor: colors.primary,
  },
  checkoutButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.surface,
    marginRight: 8,
  },
  noticeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EFF6FF',
    borderColor: '#DBEAFE',
    borderWidth: 1,
    borderRadius: 8,
    padding: 8,
    marginBottom: 12,
  },
  noticeText: {
    fontSize: 11,
    fontWeight: '500',
    color: '#1E40AF',
    flex: 1,
  },
});
