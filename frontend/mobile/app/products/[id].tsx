import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ProductDetailSkeleton } from '../../src/components/SkeletonLoader';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Image,
  Dimensions,
  Share,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons, Feather } from '@expo/vector-icons';
import { CoachMark, useCoachMarks } from '../../src/components/CoachMark';
import api, { getImageUrl, SESSION_KEY } from '../../src/api/client';
import * as SecureStore from 'expo-secure-store';
import { colors } from '../../src/theme';
import Toast from 'react-native-toast-message';
import { useAuth } from '../../src/hooks/useAuth';
import { usePincode } from '../../src/context/PincodeContext';
import { trackRecommendationEvent } from '../../src/utils/analytics';
import { trackProductView, trackEvent } from '../../src/utils/mobileAnalytics';
import {
  addGuestCartItem,
  getGuestCart,
  updateGuestCartQty,
  addGuestWishlistItem,
  removeGuestWishlistItem,
  isInGuestWishlist,
} from '../../src/services/guestStore';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const COACH_MARK_IDS = ['product_add_cart'];

interface QuantityTier {
  quantity: number;
  discount: number;
}

interface Product {
  _id?: string;
  id?: string;
  name?: string;
  sku?: string;
  description?: string;
  category?: string;
  brand?: string;
  type?: string;
  value?: string;
  mrp?: number;
  price?: number;
  gst?: number;
  discountPercentage?: number;
  stock?: number;
  displayImage?: string;
  images?: string[];
  quantityTiers?: QuantityTier[];
  quantityItemType?: 'units' | 'cases';
  quantityPerCase?: number;
  isExclusive?: boolean;
  tags?: string[];
  rating?: number;
  reviews?: number;
  salesCount?: number;
  variantAttributes?: string[];
  variantCombinations?: any[];
}

import Animated, { useAnimatedStyle, withTiming } from 'react-native-reanimated';

const AnimatedDot = ({ active }: { active: boolean }) => {
  const animatedStyle = useAnimatedStyle(() => {
    return {
      width: withTiming(active ? 24 : 6, { duration: 300 }),
      backgroundColor: withTiming(active ? '#ffffff' : 'rgba(255, 255, 255, 0.5)', {
        duration: 300,
      }),
    };
  }, [active]);

  return <Animated.View style={[{ height: 6, borderRadius: 3 }, animatedStyle]} />;
};

export default function ProductDetail() {
  const { id, refSlot, refStrategy } = useLocalSearchParams();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const productId = typeof id === 'string' ? id : '';
  const slot = typeof refSlot === 'string' ? refSlot : undefined;
  const strategy = typeof refStrategy === 'string' ? refStrategy : undefined;
  const coachMarks = useCoachMarks(COACH_MARK_IDS);

  // ── React Query: fetch product with caching ──
  const { data: product, isLoading: loading } = useQuery<Product | null>({
    queryKey: ['product', productId],
    queryFn: async () => {
      if (!productId) return null;
      try {
        const res = await api.get(`/products/${productId}`);
        return res.data || null;
      } catch {
        try {
          const res = await api.get(`/products/public/${productId}`);
          return res.data || null;
        } catch {
          return null;
        }
      }
    },
    enabled: !!productId,
  });

  // Fetch bundles containing this product
  const { data: bundlesData } = useQuery<{ bundles: any[] }>(
    {
      queryKey: ['product-bundles', productId],
      queryFn: async () => {
        if (!productId) return { bundles: [] };
        try {
          const res = await api.get(`/bundles/product/${productId}`);
          return res.data || { bundles: [] };
        } catch {
          return { bundles: [] };
        }
      },
      enabled: !!productId,
      staleTime: 5 * 60 * 1000,
    }
  );
  const productBundles = bundlesData?.bundles?.filter(b => b.isAvailable !== false) || [];

  const { user } = useAuth();
  const [adding, setAdding] = useState(false);
  const [wishlisting, setWishlisting] = useState(false);
  const [addedToCart, setAddedToCart] = useState(false);
  const [addedToWishlist, setAddedToWishlist] = useState(false);
  const [showGoToCart, setShowGoToCart] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [selectedVariant, setSelectedVariant] = useState<Record<string, string>>({});
  const [quantity, setQuantity] = useState(1);
  const [existingCartItem, setExistingCartItem] = useState<any>(null);
  const [addingBundleId, setAddingBundleId] = useState<string | null>(null);
  const [cartItemsState, setCartItemsState] = useState<any[]>([]);

  // Pincode Availability
  const { pincode, serviceableSellers } = usePincode();
  const [requestAdded, setRequestAdded] = useState(false);
  const [notifyAdded, setNotifyAdded] = useState(false);
  const [pincodeActionLoading, setPincodeActionLoading] = useState<'request' | 'notify' | null>(null);

  const isAvailableAtPincode = React.useMemo(() => {
    if (!pincode) return true; // No pincode set -> optimistic
    if (!serviceableSellers || serviceableSellers.length === 0) return false;
    const productSellers: any[] = (product as any)?.sellers || [];
    if (productSellers.length === 0) return true;
    const serviceableIds = new Set(serviceableSellers.map((s: any) => String(s.id)));
    return productSellers.some(
      (s: any) =>
        s.isActive &&
        (s.stock ?? 0) > 0 &&
        (s.requestStatus === 'approved' || !s.requestStatus) &&
        serviceableIds.has(String(s.sellerId))
    );
  }, [pincode, serviceableSellers, product]);

  useEffect(() => {
    if (coachMarks.isReady && !loading && product) {
      setTimeout(() => coachMarks.startTour(), 800);
    }
  }, [coachMarks.isReady, loading, product]);

  // ── Tracking: fire product view to backend when product loads ──
  useEffect(() => {
    if (!product || !productId) return;
    const name = product.name || '';
    // Send to /tracking/view so it feeds Most-Viewed Products report
    api.post('/tracking/view', { productId, productName: name }).catch((e: any) => console.warn('Background task failed', e));
    // Also send via mobileAnalytics for GA4 Measurement Protocol
    trackProductView(productId, name, product.price).catch((e: any) => console.warn('Background task failed', e));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId, !!product]);

  // Check wishlist status on mount
  useEffect(() => {
    if (!productId) return;
    if (user) {
      api.get('/wishlist').then((res) => {
        const ids: string[] = (res.data || []).map((item: any) => item.productId || item._id || item.product?._id);
        if (ids.includes(productId)) setAddedToWishlist(true);
      }).catch((e) => { if (__DEV__) console.warn('[PDP] wishlist prefetch failed', e); });
    } else {
      isInGuestWishlist(productId).then((inWl) => {
        if (inWl) setAddedToWishlist(true);
      });
    }
  }, [user, productId]);

  // Track recommendation view on product load if referred from a recommendation section
  useEffect(() => {
    if (productId && product && slot) {
      trackRecommendationEvent({
        eventType: 'product_view',
        slot: slot,
        productId: productId,
        productName: product.name,
        strategy: strategy,
      });
    }
  }, [productId, product, slot, strategy]);

  const fetchCartStatus = async () => {
    if (!productId) return;
    try {
      let cartItems = [];
      if (user) {
        const res = await api.get('/cart');
        cartItems = res.data || [];
      } else {
        cartItems = await getGuestCart();
      }
      setCartItemsState(cartItems);
      const found = cartItems.find(
        (item: any) => String(item.productId || item._id) === String(productId)
      );
      if (found) {
        setExistingCartItem(found);
        setQuantity(found.quantity || 1);
        setShowGoToCart(true);
      }
    } catch (err) {
      if (__DEV__) console.warn('[PDP] cart fetch failed', err);
    }
  };

  // Check cart status on mount
  useEffect(() => {
    fetchCartStatus();
  }, [user, productId]);

  const addToCart = async () => {
    if (!productId) return;
    setAdding(true);
    try {
      const hasVariants = Object.keys(selectedVariant).length > 0;
      if (existingCartItem) {
        if (user) {
          await api.put(`/cart/${existingCartItem._id || productId}`, { quantity });
        } else {
          await updateGuestCartQty(productId, quantity);
        }
        setExistingCartItem({ ...existingCartItem, quantity });
      } else {
        if (user) {
          const sessionId = await SecureStore.getItemAsync(SESSION_KEY);
          await api.post('/cart', {
            productId,
            quantity,
            sessionId,
            ...(hasVariants ? { variantAttributes: selectedVariant } : {}),
          });
        } else {
          await addGuestCartItem(productId, quantity, product);
        }
      }

      // Track recommendation cart-add if this product was clicked from a recommendation card
      if (slot) {
        await trackRecommendationEvent({
          eventType: 'add_to_cart',
          slot: slot,
          productId: productId,
          productName: product?.name,
          strategy: strategy,
        });
      }

      // Track cart-add to backend tracking table (feeds cart abandonment & conversion reports)
      api.post('/tracking/cart-add', { productId, quantity }).catch((e: any) => console.warn('Background task failed', e));
      trackAddToCart(productId, product?.name || '', quantity, product?.price || 0).catch((e: any) => console.warn('Background task failed', e));

      setAddedToCart(true);
      setTimeout(() => {
        setAddedToCart(false);
        setShowGoToCart(true);
        if (!existingCartItem) {
          setExistingCartItem({ productId, quantity });
        }
      }, 1500);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Could not update cart';
      Toast.show({ type: 'error', text1: 'Error', text2: msg });
    }
    setAdding(false);
  };

  const toggleWishlist = async () => {
    if (!productId) return;
    setWishlisting(true);
    try {
      if (addedToWishlist) {
        if (user) {
          await api.delete(`/wishlist/${productId}`);
        } else {
          await removeGuestWishlistItem(productId);
        }
        setAddedToWishlist(false);
      } else {
        if (user) {
          const sessionId = await SecureStore.getItemAsync(SESSION_KEY);
          await api.post('/wishlist', { productId, sessionId });
        } else {
          await addGuestWishlistItem(productId, product);
        }
        setAddedToWishlist(true);
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Could not update wishlist';
      Toast.show({ type: 'error', text1: 'Error', text2: msg });
    }
    setWishlisting(false);
  };

  const shareProduct = async () => {
    if (!product?.name) return;
    const message = `${product.name} - ₹${Math.round(effectivePrice).toLocaleString()}`;
    const webOrigin = (process as any).env?.EXPO_PUBLIC_WEB_URL || 'https://www.stationeryjunction.com';
    const url = `${webOrigin.replace(/\/$/, '')}/customer/product/${productId}`;
    try {
      await Share.share({
        message: `${message}\n${url}`,
        title: product.name,
        url: url,
      });
    } catch (e) {
      if (__DEV__) console.warn('[PDP] share failed', e);
    }
  };

  const handleQuantityChange = (increment: boolean) => {
    setShowGoToCart(false);
    if (increment) {
      if (product?.stock && quantity >= product.stock) {
        Toast.show({ type: 'info', text1: 'Note', text2: 'Max quantity reached' });
        return;
      }
      setQuantity((prev) => prev + 1);
    } else {
      if (quantity > 1) setQuantity((prev) => prev - 1);
    }
  };

  const rawImages = product?.images?.length
    ? product.images
    : product?.displayImage
      ? [product.displayImage]
      : [];
  const images = rawImages.map((img) => getImageUrl(img));

  // Resolve the matching variant combination when all attributes are selected
  const selectedCombination = (() => {
    if (!product?.variantAttributes?.length || !product?.variantCombinations?.length) return null;
    const allSelected = product.variantAttributes.every((attr) => selectedVariant[attr]);
    if (!allSelected) return null;
    return product.variantCombinations.find((vc) =>
      product.variantAttributes!.every((attr) => String(vc.attributes?.[attr]) === String(selectedVariant[attr]))
    ) || null;
  })();

  const effectivePrice = selectedCombination?.price ?? product?.price ?? 0;
  const effectiveMrp = selectedCombination?.mrp ?? product?.mrp;
  const hasDiscount = effectiveMrp && effectiveMrp > effectivePrice;
  const discountPct =
    (hasDiscount ? Math.round(((effectiveMrp! - effectivePrice) / effectiveMrp!) * 100) : 0) ||
    product?.discountPercentage || 0;
  const gstValue = Number(product?.gst ?? 0);
  const stockCount = selectedCombination?.stock ?? product?.stock ?? 0;
  const inStock = stockCount > 0;

  // Stock messaging
  const getStockMessage = () => {
    if (stockCount <= 0)
      return { text: 'Out of Stock', color: '#DC2626', bgColor: '#FEE2E2', dotColor: '#EF4444' };
    if (stockCount === 1)
      return { text: 'Last one!', color: '#DC2626', bgColor: '#FEE2E2', dotColor: '#EF4444' };
    if (stockCount <= 4)
      return {
        text: `Only ${stockCount} left!`,
        color: '#EA580C',
        bgColor: '#FFEDD5',
        dotColor: '#F97316',
      };
    if (stockCount <= 10)
      return { text: 'Low stock', color: '#D97706', bgColor: '#FEF3C7', dotColor: '#F59E0B' };
    return null;
  };
  const stockMessage = product ? getStockMessage() : null;

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: '#FAFAFA' }}>
        <ProductDetailSkeleton />
      </View>
    );
  }

  if (!product) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center bg-white px-8">
        <Text className="text-lg font-semibold text-gray-900">Product not found</Text>
        <TouchableOpacity
          className="mt-6 rounded-full bg-gray-900 px-6 py-3"
          onPress={() => router.back()}
          activeOpacity={0.8}
        >
          <Text className="font-medium text-white">Go Back</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <View className="flex-1 bg-white">
      {/* Header */}
      <View
        className="absolute left-0 right-0 z-10 flex-row items-center justify-between px-4"
        style={{ top: insets.top + 8 }}
      >
        <TouchableOpacity
          onPress={() => router.back()}
          className="h-10 w-10 items-center justify-center rounded-full bg-white/90 shadow-sm backdrop-blur-md"
        >
          <Ionicons name="arrow-back" size={22} color="#111827" />
        </TouchableOpacity>

        <View className="flex-row gap-2">
          <TouchableOpacity
            onPress={shareProduct}
            className="h-10 w-10 items-center justify-center rounded-full bg-white/90 shadow-sm backdrop-blur-md"
          >
            <Ionicons name="share-social-outline" size={22} color="#111827" />
          </TouchableOpacity>
          <TouchableOpacity
            onPress={toggleWishlist}
            disabled={wishlisting}
            className="h-10 w-10 items-center justify-center rounded-full bg-white/90 shadow-sm backdrop-blur-md"
          >
            <Ionicons
              name={addedToWishlist ? 'heart' : 'heart-outline'}
              size={22}
              color={addedToWishlist ? '#EF4444' : '#111827'}
            />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        className="flex-1"
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 100 }}
      >
        {/* Image Gallery */}
        <View
          style={{ width: SCREEN_WIDTH, height: SCREEN_WIDTH * 1.1, backgroundColor: '#f9fafb' }}
        >
          {images.length > 0 ? (
            <ScrollView
              horizontal
              pagingEnabled
              showsHorizontalScrollIndicator={false}
              onScroll={(e) => {
                const idx = Math.round(e.nativeEvent.contentOffset.x / SCREEN_WIDTH);
                setCurrentImageIndex(idx);
              }}
              scrollEventThrottle={16}
            >
              {images.map((img, idx) => (
                <Image
                  key={idx}
                  source={{ uri: img }}
                  style={{ width: SCREEN_WIDTH, height: SCREEN_WIDTH * 1.1 }}
                  resizeMode="cover"
                />
              ))}
            </ScrollView>
          ) : (
            <View className="flex-1 items-center justify-center">
              <Ionicons name="image-outline" size={64} color="#D1D5DB" />
            </View>
          )}

          {/* Image Indicators */}
          {images.length > 1 && (
            <View className="absolute bottom-4 left-0 right-0 flex-row justify-center space-x-2">
              {images.map((_, idx) => (
                <AnimatedDot key={idx} active={currentImageIndex === idx} />
              ))}
            </View>
          )}
        </View>

        {/* Product Details Wrapper */}
        <View className="-mt-6 min-h-[500px] rounded-t-[32px] bg-white px-6 pb-4 pt-8 shadow-lg">
          {/* Brand & SKU */}
          <View className="mb-2 flex-row items-center justify-between">
            {product.brand && (
              <Text
                className="text-sm font-bold uppercase tracking-widest"
                style={{ color: colors.primary }}
              >
                {product.brand}
              </Text>
            )}
          </View>

          {/* Product Name */}
          <Text className="mb-2 font-serif text-2xl font-bold leading-tight text-gray-900">
            {product.name}
          </Text>
          
          {/* Rating & Sales */}
          <View className="mb-4 flex-row items-center flex-wrap gap-y-2">
            {product.rating ? product.rating > 0 && (
              <View className="flex-row items-center mr-4">
                <View className="flex-row gap-0.5">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Ionicons
                      key={s}
                      name={s <= Math.floor(product.rating || 0) ? 'star' : s <= Math.ceil(product.rating || 0) && (product.rating || 0) % 1 > 0 ? 'star-half' : 'star-outline'}
                      size={16}
                      color="#FBBF24"
                    />
                  ))}
                </View>
                <Text className="ml-2 text-sm font-bold text-gray-900">
                  {(product.rating || 0).toFixed(1)}
                </Text>
                <Text className="ml-1 text-sm text-gray-400">
                  ({product.reviews || 0} reviews)
                </Text>
              </View>
            ) : null}

            {product.salesCount ? product.salesCount > 0 && (
              <View className="flex-row items-center rounded-full bg-blue-50 px-3 py-1 border border-blue-100">
                <Ionicons name="bag-check" size={14} color="#2563EB" />
                <Text className="ml-1.5 text-xs font-bold text-blue-700">
                  Bought {product.salesCount > 1000 ? `${(product.salesCount / 1000).toFixed(1)}k+` : product.salesCount} times
                </Text>
              </View>
            ) : null}
          </View>

          {/* Price & Discount */}
          <View className="mb-6 flex-row items-baseline">
            <Text className="text-3xl font-bold text-gray-900">
              ₹{Math.round(effectivePrice).toLocaleString()}
            </Text>
            {hasDiscount && (
              <>
                <Text className="ml-3 text-lg text-gray-400 line-through">
                  ₹{effectiveMrp?.toLocaleString()}
                </Text>
                <View className="ml-3 rounded-full border border-red-100 bg-red-50 px-2.5 py-1">
                  <Text className="text-xs font-bold text-red-600">{discountPct}% OFF</Text>
                </View>
              </>
            )}
          </View>

          {/* GST & Stock Info */}
          <View className="mb-6 flex-row flex-wrap items-center gap-2">
            {gstValue > 0 ? (
              <View className="rounded-lg bg-gray-100 px-3 py-1.5">
                <Text className="text-[10px] font-bold text-gray-600">
                  GST {gstValue}% Included
                </Text>
              </View>
            ) : (
              <View className="rounded-lg bg-gray-100 px-3 py-1.5">
                <Text className="text-[10px] font-bold text-gray-600">
                  inclusive of all taxes
                </Text>
              </View>
            )}
          </View>

          <View className="mb-6 h-[1px] w-full bg-gray-100" />

          {/* Variants Selection */}
          {product.variantAttributes && product.variantAttributes.length > 0 && (
            <View className="mb-6">
              {product.variantAttributes.map((attr) => {
                const uniqueValues = Array.from(
                  new Set(
                    product.variantCombinations!.map((vc) => vc.attributes?.[attr]).filter(Boolean)
                  )
                );
                if (uniqueValues.length === 0) return null;
                return (
                  <View key={attr} className="mb-4">
                    <Text className="mb-3 text-sm font-bold capitalize text-gray-900">{attr}</Text>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                      {uniqueValues.map((val) => {
                        const isSelected = selectedVariant[attr] === val;
                        return (
                          <TouchableOpacity
                            key={String(val)}
                            onPress={() => {
                              setSelectedVariant({ ...selectedVariant, [attr]: String(val) });
                              setShowGoToCart(false);
                            }}
                            className="mr-3 rounded-xl border px-5 py-2.5"
                            style={isSelected
                              ? { borderColor: colors.primary, backgroundColor: colors.primary }
                              : { borderColor: '#E5E7EB', backgroundColor: '#FFFFFF' }
                            }
                          >
                            <Text
                              className={`font-semibold ${isSelected ? 'text-white' : 'text-gray-700'}`}
                            >
                              {String(val)}
                            </Text>
                          </TouchableOpacity>
                        );
                      })}
                    </ScrollView>
                  </View>
                );
              })}
            </View>
          )}

          {/* Description */}
          {product.description && (
            <View className="mb-8">
              <Text className="mb-3 text-sm font-bold text-gray-900">Description</Text>
              <Text className="text-sm leading-6 text-gray-600">{product.description}</Text>
            </View>
          )}

          {/* Available in Bundles */}
          {productBundles.length > 0 && (
            <View style={{ marginBottom: 32 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
                <Ionicons name="gift-outline" size={18} color="#1a4d33" />
                <Text style={{ marginLeft: 8, fontSize: 14, fontWeight: '700', color: '#111827' }}>
                  Available in Bundle Deals
                </Text>
              </View>
              {productBundles.map((bundle) => {
                const addBundleToCart = async (bundleId: string, bundleName: string) => {
                  if (!user) {
                    Toast.show({ type: 'info', text1: 'Sign in required', text2: 'Please sign in to add bundles to cart.' });
                    return;
                  }
                  setAddingBundleId(bundleId);
                  try {
                    await api.post(`/bundles/${bundleId}/add-to-cart`, {});
                    Toast.show({ type: 'success', text1: '🎁 Bundle added!', text2: `${bundleName} has been added to your cart.` });
                    await fetchCartStatus();
                  } catch (err: any) {
                    Toast.show({ type: 'error', text1: 'Error', text2: err?.response?.data?.detail || 'Could not add bundle to cart.' });
                  }
                  setAddingBundleId(null);
                };
                
                const addingBundle = addingBundleId === bundle._id;

                return (
                  <View
                    key={bundle._id}
                    style={{
                      borderWidth: 1,
                      borderColor: '#D1FAE5',
                      borderRadius: 16,
                      backgroundColor: '#F0FDF4',
                      padding: 16,
                      marginBottom: 12,
                    }}
                  >
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                      <Text style={{ fontSize: 15, fontWeight: '700', color: '#111827', flex: 1, marginRight: 8 }}>
                        {bundle.name}
                      </Text>
                      {bundle.savingsPercent > 0 && (
                        <View style={{ backgroundColor: '#059669', borderRadius: 20, paddingHorizontal: 8, paddingVertical: 3 }}>
                          <Text style={{ color: '#fff', fontSize: 11, fontWeight: '700' }}>{bundle.savingsPercent}% OFF</Text>
                        </View>
                      )}
                    </View>
                    {bundle.description ? (
                      <Text style={{ fontSize: 13, color: '#6B7280', marginBottom: 8 }}>{bundle.description}</Text>
                    ) : null}
                    {/* Included Items List - matches web implementation */}
                    <View style={{ marginBottom: 12, borderTopWidth: 1, borderTopColor: '#D1FAE5', paddingTop: 8 }}>
                      <Text style={{ fontSize: 10, fontWeight: '700', color: '#9CA3AF', letterSpacing: 0.5, marginBottom: 6 }}>
                        INCLUDED ITEMS
                      </Text>
                      {bundle.items?.map((bItem: any, idx: number) => (
                        <View key={idx} style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 3 }}>
                          <Text style={{ fontSize: 12, color: '#374151', flex: 1, paddingRight: 8 }} numberOfLines={1}>
                            • {bItem.product?.name || 'Product'}
                          </Text>
                          <Text style={{ fontSize: 12, color: '#6B7280', fontWeight: '600' }}>×{bItem.quantity}</Text>
                        </View>
                      ))}
                    </View>
                    <View style={{ flexDirection: 'row', alignItems: 'baseline', marginBottom: 12 }}>
                      <Text style={{ fontSize: 18, fontWeight: '800', color: '#111827' }}>
                        ₹{Math.round(bundle.price).toLocaleString()}
                      </Text>
                      {bundle.savings > 0 && (
                        <Text style={{ marginLeft: 8, fontSize: 13, color: '#6B7280', textDecorationLine: 'line-through' }}>
                          ₹{Math.round(bundle.totalMrp).toLocaleString()}
                        </Text>
                      )}
                      {bundle.savings > 0 && (
                        <Text style={{ marginLeft: 8, fontSize: 12, color: '#059669', fontWeight: '600' }}>
                          Save ₹{Math.round(bundle.savings).toLocaleString()}
                        </Text>
                      )}
                    </View>
                    
                    {(() => {
                      const bundleCount = cartItemsState.find((item: any) => item.isBundle && item.bundleId === bundle._id)?.quantity || 0;
                      
                      const handleBundleDecrement = async () => {
                        if (!user) return;
                        setAddingBundleId(bundle._id);
                        try {
                          const bundleItem = cartItemsState.find((item: any) => item.isBundle && item.bundleId === bundle._id);
                          if (bundleItem) {
                            if (bundleItem.quantity > 1) {
                              await api.put(`/cart/${bundleItem._id}`, { quantity: bundleItem.quantity - 1 });
                            } else {
                              await api.delete(`/cart/${bundleItem._id}`);
                            }
                            await fetchCartStatus();
                          }
                        } catch (err: any) {
                          Toast.show({ type: 'error', text1: 'Error', text2: 'Could not update bundle quantity' });
                        }
                        setAddingBundleId(null);
                      };

                      if (bundleCount > 0) {
                        return (
                          <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: 'white', borderRadius: 12, borderWidth: 2, borderColor: '#111827', overflow: 'hidden' }}>
                            <TouchableOpacity
                              onPress={handleBundleDecrement}
                              disabled={addingBundle}
                              style={{ flex: 1, paddingVertical: 12, alignItems: 'center', backgroundColor: 'white' }}
                            >
                              <Text style={{ fontSize: 20, fontWeight: '700', color: '#111827' }}>−</Text>
                            </TouchableOpacity>
                            <View style={{ paddingHorizontal: 20, paddingVertical: 12, borderLeftWidth: 2, borderRightWidth: 2, borderColor: '#111827' }}>
                              <Text style={{ fontSize: 14, fontWeight: '700', color: '#111827' }}>{bundleCount}</Text>
                            </View>
                            <TouchableOpacity
                              onPress={() => addBundleToCart(bundle._id, bundle.name)}
                              disabled={addingBundle}
                              style={{ flex: 1, paddingVertical: 12, alignItems: 'center', backgroundColor: 'white' }}
                            >
                              <Text style={{ fontSize: 20, fontWeight: '700', color: '#111827' }}>+</Text>
                            </TouchableOpacity>
                          </View>
                        );
                      }

                      return (
                        <TouchableOpacity
                          onPress={() => addBundleToCart(bundle._id, bundle.name)}
                          disabled={addingBundle || !bundle.isAvailable}
                          style={{
                            backgroundColor: (addingBundle || !bundle.isAvailable) ? '#9CA3AF' : '#111827',
                            borderRadius: 12,
                            paddingVertical: 10,
                            alignItems: 'center',
                            flexDirection: 'row',
                            justifyContent: 'center',
                          }}
                        >
                          <Ionicons name="cart-outline" size={16} color="white" />
                          <Text style={{ color: 'white', fontWeight: '700', marginLeft: 6, fontSize: 14 }}>
                            {addingBundle ? 'Adding...' : bundle.isAvailable ? 'Add Bundle to Cart' : 'Out of Stock'}
                          </Text>
                        </TouchableOpacity>
                      );
                    })()}
                  </View>
                );
              })}
            </View>
          )}

          {/* Quantity Discounts */}
          {product.quantityTiers && product.quantityTiers.length > 0 && (
            <View className="mb-8 rounded-2xl border border-rose-100 bg-rose-50/30 p-4">
              <View className="mb-3 flex-row items-center">
                <Ionicons name="gift-outline" size={18} color="#E11D48" />
                <Text className="ml-2 text-sm font-bold text-rose-600">📊 Tiered Quantity Discounts ({product.quantityItemType || 'units'})</Text>
              </View>
              <View className="flex-col gap-2">
                {(() => {
                  const role = (user as any)?.effectiveRole || (user as any)?.role || 'customer';
                  const qtyToUse = (role === 'wholesaler' && product.quantityItemType === 'cases' && product.quantityPerCase)
                    ? Math.floor(quantity / product.quantityPerCase)
                    : quantity;
                  const sortedTiers = [...product.quantityTiers].sort((a, b) => a.quantity - b.quantity);
                  const activeTier = [...sortedTiers].reverse().find((t) => qtyToUse >= t.quantity);

                  return sortedTiers.map((tier, idx) => {
                    const isActive = activeTier && activeTier.quantity === tier.quantity;
                    const unitPrice = (product.price || product.mrp || 0) * (1 - tier.discount / 100);
                    const label = product.quantityItemType === 'cases' ? 'cases' : 'units';
                    const perItemLabel = product.quantityItemType === 'cases' ? 'case' : 'pc';

                    return (
                      <View
                        key={idx}
                        className={`flex-row items-center justify-between rounded-xl px-3 py-2.5 border transition-all ${
                          isActive
                            ? 'bg-emerald-50 border-emerald-500/20'
                            : 'bg-white border-gray-100'
                        }`}
                      >
                        <View className="flex-row items-center gap-2">
                          {isActive ? (
                            <Ionicons name="checkmark-circle" size={16} color="#059669" />
                          ) : (
                            <View className="h-1.5 w-1.5 rounded-full bg-gray-300" style={{ marginRight: 6 }} />
                          )}
                          <Text className={`text-xs font-semibold ${isActive ? 'text-emerald-700' : 'text-gray-600'}`}>
                            Buy {tier.quantity}+ {label}
                          </Text>
                        </View>

                        <View className="flex-row items-center gap-4">
                          <Text className={`text-xs font-bold ${isActive ? 'text-emerald-700' : 'text-gray-500'}`}>
                            {tier.discount}% OFF {isActive && '✓ ACTIVE'}
                          </Text>
                          <Text className={`text-xs ${isActive ? 'text-emerald-700 font-bold' : 'text-gray-400'}`}>
                            ₹{Math.round(unitPrice)}/{perItemLabel}
                          </Text>
                        </View>
                      </View>
                    );
                  });
                })()}
              </View>
            </View>
          )}

          {/* Tags */}
          {/* Tags removed as requested */}
        </View>

        {/* Pincode Unavailability Banner */}
        {pincode && !isAvailableAtPincode && (
          <View className="mx-4 mb-32 rounded-xl border border-amber-200 bg-amber-50 p-4">
            <View className="flex-row items-start">
              <Ionicons name="location-outline" size={20} color="#b45309" style={{ marginTop: 2 }} />
              <View className="ml-3 flex-1">
                <Text className="text-sm font-bold text-amber-800">
                  Not available at your pincode ({pincode})
                </Text>
                <Text className="mt-1 text-xs text-amber-700">
                  This product is currently not delivered to your area.
                </Text>
                
                <View className="mt-4 flex-row flex-wrap gap-2">
                  <TouchableOpacity
                    onPress={async () => {
                      if (requestAdded || pincodeActionLoading) return;
                      setPincodeActionLoading('request');
                      try {
                        await api.post('/availability-requests', {
                          productId: product._id || product.id,
                          productName: product.name,
                          pincode,
                        });
                        setRequestAdded(true);
                        Toast.show({ type: 'success', text1: 'Requested', text2: 'We\'ll work on bringing this to your pincode.' });
                      } catch {
                        Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to submit request.' });
                      } finally {
                        setPincodeActionLoading(null);
                      }
                    }}
                    disabled={requestAdded || pincodeActionLoading !== null}
                    className="flex-row items-center justify-center rounded-lg bg-amber-600 px-4 py-2"
                    style={{ opacity: (requestAdded || pincodeActionLoading !== null) ? 0.6 : 1 }}
                  >
                    <Text className="text-sm font-bold text-white">
                      {pincodeActionLoading === 'request' ? 'Requesting...' : requestAdded ? '✓ Requested' : '+ Request Addition'}
                    </Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    onPress={async () => {
                      if (notifyAdded || pincodeActionLoading) return;
                      setPincodeActionLoading('notify');
                      try {
                        await api.post('/tracking/notify-pincode', {
                          productId: product._id || product.id,
                          productName: product.name,
                          pincode,
                        });
                        setNotifyAdded(true);
                        Toast.show({ type: 'success', text1: 'Notified', text2: 'We\'ll notify you when available.' });
                      } catch {
                        Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to set notification.' });
                      } finally {
                        setPincodeActionLoading(null);
                      }
                    }}
                    disabled={notifyAdded || pincodeActionLoading !== null}
                    className="flex-row items-center justify-center rounded-lg border border-amber-600 px-4 py-2"
                    style={{ opacity: (notifyAdded || pincodeActionLoading !== null) ? 0.6 : 1 }}
                  >
                    <Ionicons name="notifications-outline" size={16} color="#d97706" style={{ marginRight: 6 }} />
                    <Text className="text-sm font-bold text-amber-700">
                      {pincodeActionLoading === 'notify' ? 'Setting...' : notifyAdded ? '✓ Notified' : 'Notify Me'}
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Bottom Action Bar */}
      <View
        className="absolute bottom-0 left-0 right-0 flex-row items-center justify-between border-t border-gray-100 bg-white px-6 pb-8 pt-4"
        style={{
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -4 },
          shadowOpacity: 0.05,
          shadowRadius: 8,
          elevation: 10,
        }}
      >
        {/* Quantity Selector */}
        <View className="mr-4 h-12 flex-row items-center rounded-full bg-gray-100 px-2">
          <TouchableOpacity
            onPress={() => handleQuantityChange(false)}
            className="h-8 w-8 items-center justify-center rounded-full bg-white shadow-sm"
          >
            <Feather name="minus" size={16} color="#374151" />
          </TouchableOpacity>
          <Text className="w-12 px-4 text-center text-lg font-bold text-gray-900">{quantity}</Text>
          <TouchableOpacity
            onPress={() => handleQuantityChange(true)}
            className="h-8 w-8 items-center justify-center rounded-full bg-white shadow-sm"
          >
            <Feather name="plus" size={16} color="#374151" />
          </TouchableOpacity>
        </View>

        {/* Add to Cart / Go to Cart Button */}
        {showGoToCart ? (
          <TouchableOpacity
            onPress={() => router.push('/cart')}
            className="h-12 flex-1 transform flex-row items-center justify-center rounded-full shadow-lg transition-transform active:scale-95"
            style={{
              backgroundColor: colors.accent,
            }}
          >
            <Ionicons name="cart" size={20} color="white" />
            <Text className="ml-2 text-base font-bold text-white">Go to Cart</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            onPress={addToCart}
            disabled={adding || !inStock || !isAvailableAtPincode}
            className="h-12 flex-1 transform flex-row items-center justify-center rounded-full shadow-lg transition-transform active:scale-95"
            style={{
              backgroundColor: (!inStock || !isAvailableAtPincode) ? '#D1D5DB' : addedToCart ? '#16A34A' : colors.primary,
            }}
          >
            {addedToCart ? (
              <>
                <Ionicons name="checkmark-circle" size={20} color="white" />
                <Text className="ml-2 text-base font-bold text-white">{existingCartItem ? 'Updated' : 'Added'}</Text>
              </>
            ) : (
              <>
                <Ionicons name={existingCartItem ? 'refresh-outline' : 'cart-outline'} size={20} color="white" />
                <Text className="ml-2 text-base font-bold text-white">
                  {adding ? (existingCartItem ? 'Updating...' : 'Adding...') : !isAvailableAtPincode ? 'Unavailable at Pincode' : inStock ? (existingCartItem ? 'Update Quantity' : 'Add to Cart') : 'Out of Stock'}
                </Text>
              </>
            )}
          </TouchableOpacity>
        )}
      </View>

      {/* Coach Mark Overlay */}
      {coachMarks.isActive && coachMarks.currentMarkId === 'product_add_cart' && (
        <CoachMark
          id="product_add_cart"
          title="Add to Cart"
          description="Tap here to add this product to your shopping cart."
          onDismiss={coachMarks.dismiss}
          isLast={true}
        />
      )}
    </View>
  );
}
