import React, { useCallback, useState, useRef } from 'react';
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
  AppState,
  AppStateStatus,
  Modal,
  TextInput,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
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
  addGuestWishlistItem,
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
  const [savingForLaterId, setSavingForLaterId] = useState<string | null>(null);
  const { user } = useAuth();
  const router = useRouter();

  const [duesInfo, setDuesInfo] = useState<any>(null);
  const [showDuesModal, setShowDuesModal] = useState(false);
  const [duesSettleAmount, setDuesSettleAmount] = useState('');
  const [duesSettleImage, setDuesSettleImage] = useState<string | null>(null);
  const [settlingDuesPayment, setSettlingDuesPayment] = useState(false);
  const [selectedBillForSettle, setSelectedBillForSettle] = useState<any>(null);

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

        if ((user as any).role === 'wholesaler' || (user as any).effectiveRole === 'wholesaler') {
          const duesRes = await api.get('/payments/dues').catch(() => null);
          if (duesRes) setDuesInfo(duesRes.data);
        } else {
          setDuesInfo(null);
        }
      }
    } catch (e) {
      if (__DEV__) console.log('Fetch Extras Error:', e);
    }
  }, [user]);

  // Track current interval so AppState listener can clear/restart it
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useFocusEffect(
    useCallback(() => {
      fetchCart();
      fetchExtras();
      // 60s interval (was 5s). useFocusEffect stops this when the screen loses focus.
      intervalRef.current = setInterval(() => {
        fetchCart();
        fetchExtras();
      }, 60_000);

      // AppState guard: pause polling when app is backgrounded
      const handleAppStateChange = (nextState: AppStateStatus) => {
        if (nextState === 'active') {
          fetchCart();
          fetchExtras();
          if (!intervalRef.current) {
            intervalRef.current = setInterval(() => { fetchCart(); fetchExtras(); }, 60_000);
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

  const saveForLater = async (item: CartItem) => {
    const productId = item?.product?._id || item?.productId;
    const cartItemId = item._id;
    if (!productId) return;

    const key = cartItemId || productId;
    setSavingForLaterId(key);
    try {
      if (user) {
        // Save to wishlist via backend endpoint, then remove from cart
        await api.post('/cart/save-for-later', { productId });
        if (cartItemId) await api.delete(`/cart/${cartItemId}`);
      } else {
        // Guest: add to local wishlist + remove from local cart
        await addGuestWishlistItem(productId, item.product);
        await removeGuestCartItem(productId);
      }
      Toast.show({
        type: 'success',
        text1: 'Saved for Later ♥',
        text2: `${item.product?.name || 'Item'} moved to your Wishlist`,
      });
      fetchCart();
    } catch {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Could not save for later. Please try again.' });
    } finally {
      setSavingForLaterId(null);
    }
  };

  const totalPrice = items.reduce((sum, item) => {
    const subtotal = item.subtotal !== undefined ? item.subtotal : (item.product?.price || 0) * (item.quantity || 1);
    return sum + subtotal;
  }, 0);

  // MRP total for discount savings line (matches web cart)
  const totalMrp = items.reduce((sum, item) => {
    const mrp = item.product?.mrp || item.product?.price || item.price || 0;
    return sum + mrp * (item.quantity || 1);
  }, 0);
  const totalSavings = Math.max(0, totalMrp - totalPrice);

  const itemCount = items.reduce((sum, item) => sum + (item.quantity || 1), 0);

  // Items with no stock — block checkout
  const hasOOSItems = items.some(
    (item) => (item.product?.stock ?? 1) <= 0 || item.product?.outOfStock === true
  );

  const renderCartItem = ({ item }: { item: CartItem }) => {
    const name = item?.product?.name || 'Item';
    const qty = item?.quantity || 1;
    const price = item?.price !== undefined ? item.price : (item?.product?.price || 0);
    const mrp = item?.product?.mrp || price;
    const itemSubtotal = item?.subtotal !== undefined ? item.subtotal : (price * qty);
    const rawImg = item?.product?.displayImage || item?.product?.images?.[0];
    const img = rawImg ? getImageUrl(rawImg) : null;
    const isOOS = (item.product?.stock ?? 1) <= 0 || item.product?.outOfStock === true;

    return (
      <View style={[styles.cartItem, shadows.card, isOOS && { opacity: 0.7 }]}>
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
          {/* Out-of-stock overlay on image */}
          {isOOS && (
            <View style={{
              position: 'absolute', inset: 0, backgroundColor: 'rgba(0,0,0,0.35)',
              borderRadius: borderRadius.md, alignItems: 'center', justifyContent: 'center',
            }}>
              <Text style={{ color: '#fff', fontSize: 9, fontWeight: '800', letterSpacing: 0.5 }}>OUT OF STOCK</Text>
            </View>
          )}
        </TouchableOpacity>

        <View style={styles.cartItemInfo}>
          <View style={{ flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 4 }}>
            <Text style={styles.itemName} numberOfLines={2}>
              {name}
            </Text>
            {isOOS && (
              <View style={{ backgroundColor: '#FEE2E2', borderRadius: 4, paddingHorizontal: 6, paddingVertical: 2 }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: '#DC2626' }}>OUT OF STOCK</Text>
              </View>
            )}
          </View>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 }}>
            <Text style={styles.itemPrice}>₹{price.toLocaleString()}</Text>
            {mrp > price && (
              <Text style={{ fontSize: 12, color: colors.textMuted, textDecorationLine: 'line-through' }}>
                ₹{mrp.toLocaleString()}
              </Text>
            )}
          </View>

          <View style={styles.quantityRow}>
            <View style={[styles.quantityControls, isOOS && { opacity: 0.4 }]}>
              <TouchableOpacity
                style={styles.quantityButton}
                onPress={() => !isOOS && updateQty(item, Math.max(1, qty - 1))}
                activeOpacity={isOOS ? 1 : 0.7}
                disabled={isOOS}
              >
                <Ionicons name="remove" size={16} color={colors.textPrimary} />
              </TouchableOpacity>
              <Text style={styles.quantityText}>{qty}</Text>
              <TouchableOpacity
                style={styles.quantityButton}
                onPress={() => !isOOS && updateQty(item, qty + 1)}
                activeOpacity={isOOS ? 1 : 0.7}
                disabled={isOOS}
              >
                <Ionicons name="add" size={16} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>

            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
              {/* Save for Later — heart icon, moves item to wishlist */}
              <TouchableOpacity
                style={styles.saveForLaterButton}
                onPress={() => saveForLater(item)}
                disabled={savingForLaterId === (item._id || item.productId)}
                activeOpacity={0.7}
              >
                {savingForLaterId === (item._id || item.productId) ? (
                  <ActivityIndicator size="small" color="#EC4899" />
                ) : (
                  <Ionicons name="heart-outline" size={18} color="#EC4899" />
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.removeButton}
                onPress={() => removeItem(item)}
                activeOpacity={0.7}
              >
                <Ionicons name="trash-outline" size={18} color={colors.error} />
              </TouchableOpacity>
            </View>
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

  const handleDuesFileUpload = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.7,
        base64: true,
      });
      if (!result.canceled && result.assets && result.assets.length > 0) {
        setDuesSettleImage(`data:image/jpeg;base64,${result.assets[0].base64}`);
      }
    } catch (e) {
      if (__DEV__) console.warn('Image picker error', e);
    }
  };

  const handleSettleDues = async () => {
    const settleAmt = parseFloat(duesSettleAmount);
    if (!selectedBillForSettle) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Please select a bill to settle.' });
      return;
    }
    if (isNaN(settleAmt) || settleAmt <= 0 || settleAmt > selectedBillForSettle.amountRemaining) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Enter a valid amount to settle.' });
      return;
    }
    if (!duesSettleImage) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Please upload a payment screenshot.' });
      return;
    }
    setSettlingDuesPayment(true);
    try {
      await api.post(`/orders/${selectedBillForSettle.orderId}/settle-credit`, {
        amount: settleAmt,
        paymentImage: duesSettleImage,
        upiPaymentScreenshot: duesSettleImage,
      });
      Toast.show({ type: 'success', text1: 'Success', text2: 'Dues payment submitted successfully! Awaiting admin verification.' });
      setShowDuesModal(false);
      setDuesSettleAmount('');
      setDuesSettleImage(null);
      setSelectedBillForSettle(null);
      fetchExtras(); // Refresh dues
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.response?.data?.error || 'Failed to submit dues settlement.';
      Toast.show({ type: 'error', text1: 'Error', text2: msg });
    } finally {
      setSettlingDuesPayment(false);
    }
  };

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
                {/* MRP Subtotal row — only when there are savings (matches web) */}
                {totalSavings > 0 && (
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Price (MRP)</Text>
                    <Text style={[styles.summaryValue, { textDecorationLine: 'line-through', color: colors.textMuted }]}>
                      ₹{totalMrp.toLocaleString()}
                    </Text>
                  </View>
                )}
                {totalSavings > 0 && (
                  <View style={styles.summaryRow}>
                    <Text style={[styles.summaryLabel, { color: '#059669' }]}>Discount</Text>
                    <Text style={[styles.summaryValue, { color: '#059669' }]}>-₹{totalSavings.toLocaleString()}</Text>
                  </View>
                )}
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

              {/* OOS warning banner */}
              {hasOOSItems && (
                <View style={{
                  flexDirection: 'row', alignItems: 'center',
                  backgroundColor: '#FEF2F2', borderColor: '#FECACA',
                  borderWidth: 1, borderRadius: 8, padding: 10, marginBottom: 10,
                }}>
                  <Ionicons name="alert-circle-outline" size={16} color="#DC2626" style={{ marginRight: 6 }} />
                  <Text style={{ fontSize: 12, color: '#DC2626', fontWeight: '600', flex: 1 }}>
                    Some items are out of stock. Please remove them before checkout.
                  </Text>
                </View>
              )}

              <TouchableOpacity
                style={[styles.checkoutButton, hasOOSItems && { opacity: 0.5 }]}
                onPress={() => {
                  if (hasOOSItems) {
                    Toast.show({ type: 'error', text1: 'Out of stock items', text2: 'Remove out-of-stock items before proceeding.' });
                    return;
                  }
                  if (user && ((user as any).role === 'wholesaler' || (user as any).effectiveRole === 'wholesaler') && duesInfo?.hasOverdueBills) {
                    setShowDuesModal(true);
                    return;
                  }
                  router.push('/checkout');
                }}
                activeOpacity={hasOOSItems ? 1 : 0.9}
              >
                <View style={[styles.checkoutGradient, duesInfo?.hasOverdueBills && { backgroundColor: '#EF4444' }]}>
                  <Text style={styles.checkoutButtonText}>
                    {duesInfo?.hasOverdueBills ? 'Clear Dues to Checkout' : 'Proceed to Checkout'}
                  </Text>
                  <Ionicons name="arrow-forward" size={18} color={colors.surface} />
                </View>
              </TouchableOpacity>
            </View>
          </View>
        </>
      )}

      {/* Dues Modal */}
      <Modal visible={showDuesModal} transparent={true} animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Outstanding Dues</Text>
              <TouchableOpacity onPress={() => setShowDuesModal(false)} style={styles.modalClose}>
                <Ionicons name="close" size={24} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.modalScroll}>
              <View style={styles.duesWarningBox}>
                <Ionicons name="alert-circle" size={20} color="#DC2626" />
                <Text style={styles.duesWarningText}>
                  You have overdue bills. Please clear a minimum of ₹{duesInfo?.minimumAmountToUnblock?.toLocaleString()} to proceed to checkout.
                </Text>
              </View>

              <Text style={styles.modalSubtitle}>Select Bill to Settle</Text>
              {duesInfo?.bills?.filter((b: any) => b.status === 'overdue').map((bill: any) => (
                <TouchableOpacity
                  key={bill.orderId}
                  style={[
                    styles.billCard,
                    selectedBillForSettle?.orderId === bill.orderId && styles.billCardSelected,
                  ]}
                  onPress={() => setSelectedBillForSettle(bill)}
                >
                  <View style={styles.billHeader}>
                    <Text style={styles.billOrderRef}>{bill.orderRef}</Text>
                    <Text style={styles.billOverdueBadge}>OVERDUE</Text>
                  </View>
                  <Text style={styles.billAmount}>Remaining: ₹{bill.amountRemaining?.toLocaleString()}</Text>
                  <Text style={styles.billDueDate}>Due Date: {new Date(bill.dueDate).toLocaleDateString()}</Text>
                </TouchableOpacity>
              ))}

              {selectedBillForSettle && (
                <View style={styles.settleForm}>
                  <Text style={styles.formLabel}>Amount to Settle (₹)</Text>
                  <TextInput
                    style={styles.inputField}
                    keyboardType="numeric"
                    placeholder="Enter amount"
                    value={duesSettleAmount}
                    onChangeText={setDuesSettleAmount}
                  />

                  <Text style={styles.formLabel}>Payment Screenshot</Text>
                  <TouchableOpacity style={styles.uploadButton} onPress={handleDuesFileUpload}>
                    <Ionicons name="cloud-upload-outline" size={20} color={colors.primary} />
                    <Text style={styles.uploadButtonText}>
                      {duesSettleImage ? 'Change Screenshot' : 'Upload Screenshot'}
                    </Text>
                  </TouchableOpacity>
                  {duesSettleImage && (
                    <Image source={{ uri: duesSettleImage }} style={styles.uploadedImagePreview} />
                  )}

                  <TouchableOpacity
                    style={styles.submitButton}
                    onPress={handleSettleDues}
                    disabled={settlingDuesPayment}
                  >
                    {settlingDuesPayment ? (
                      <ActivityIndicator color={colors.surface} />
                    ) : (
                      <Text style={styles.submitButtonText}>Submit Settlement</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
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
  saveForLaterButton: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FDF2F8',
    borderRadius: borderRadius.md,
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    height: '80%',
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  modalClose: {
    padding: 4,
  },
  modalScroll: {
    flex: 1,
  },
  duesWarningBox: {
    flexDirection: 'row',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 8,
    padding: 12,
    marginBottom: 20,
  },
  duesWarningText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 13,
    color: '#DC2626',
    fontWeight: '500',
  },
  modalSubtitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 12,
  },
  billCard: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    backgroundColor: colors.surface,
  },
  billCardSelected: {
    borderColor: colors.primary,
    backgroundColor: '#EFF6FF',
  },
  billHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  billOrderRef: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  billOverdueBadge: {
    fontSize: 10,
    fontWeight: '700',
    color: '#DC2626',
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  billAmount: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textSecondary,
    marginBottom: 4,
  },
  billDueDate: {
    fontSize: 13,
    color: colors.textMuted,
  },
  settleForm: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingBottom: 40,
  },
  formLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  inputField: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    marginBottom: 20,
    backgroundColor: colors.backgroundAlt,
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.primary,
    borderStyle: 'dashed',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  uploadButtonText: {
    marginLeft: 8,
    fontSize: 15,
    fontWeight: '500',
    color: colors.primary,
  },
  uploadedImagePreview: {
    width: '100%',
    height: 150,
    borderRadius: 8,
    marginBottom: 20,
  },
  submitButton: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.surface,
  },
});
