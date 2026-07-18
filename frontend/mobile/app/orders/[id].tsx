import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  Modal,
  Image,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useAuth } from '../../src/hooks/useAuth';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import * as SecureStore from 'expo-secure-store';
import api, { TOKEN_KEY } from '../../src/api/client';
import { colors, spacing, typography } from '../../src/theme';
import { formatDateTimeIST } from '../../src/utils/dateUtils';

interface Order {
  _id?: string;
  status?: string;
  total?: number;
  paymentMethod?: string;
  createdAt?: string;
  items?: { product?: any; quantity?: number; price?: number }[];
  shippingAddress?: any;
  deliverySlot?: {
    slotId?: string;
    isUrgent?: boolean;
    date?: string;
    startTime?: string;
    endTime?: string;
  };
}

export default function OrderDetail() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const orderId = typeof id === 'string' ? id : '';
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [classifications, setClassifications] = useState<any[]>([]);
  const [reviewProduct, setReviewProduct] = useState<{ id: string; name: string } | null>(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewClassification, setReviewClassification] = useState('');
  const [reviewComment, setReviewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);

  // Returns state
  const { user } = useAuth();
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [eligibleItems, setEligibleItems] = useState<any[]>([]);
  const [returnCharge, setReturnCharge] = useState(0);
  const [selectedReturnItems, setSelectedReturnItems] = useState<Record<string, { quantity: number; reason: string }>>({});
  const [returnPaymentMethod, setReturnPaymentMethod] = useState<'cod' | 'upi'>('cod');
  const [returnUpiScreenshot, setReturnUpiScreenshot] = useState<string | null>(null);
  const [returnNotes, setReturnNotes] = useState('');
  const [submittingReturn, setSubmittingReturn] = useState(false);
  const [loadingEligibility, setLoadingEligibility] = useState(false);
  const [upiDetails, setUpiDetails] = useState<any>(null);

  const fetchUPIDetails = async () => {
    try {
      const res = await api.get('/upi/details');
      setUpiDetails(res.data);
    } catch (err) {
      if (__DEV__) console.warn('Failed to fetch UPI details', err);
    }
  };

  const handleOpenReturnModal = async () => {
    setLoadingEligibility(true);
    setSelectedReturnItems({});
    setReturnPaymentMethod('cod');
    setReturnUpiScreenshot(null);
    setReturnNotes('');
    
    try {
      const res = await api.get(`/returns/order/${orderId}/eligibility`);
      const data = res.data || {};
      if (data.reason) {
        Alert.alert('Not Eligible', data.reason);
        return;
      }
      setEligibleItems(data.eligibleItems || []);
      setReturnCharge(data.returnDeliveryCharge || 0);
      await fetchUPIDetails();
      setShowReturnModal(true);
    } catch (err: any) {
      Alert.alert('Error', err.response?.data?.detail || 'Failed to check eligibility');
    } finally {
      setLoadingEligibility(false);
    }
  };

  const pickScreenshot = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setReturnUpiScreenshot(`data:image/jpeg;base64,${result.assets[0].base64}`);
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to pick image.');
    }
  };

  const handleReturnSubmit = async () => {
    const itemsToSubmit = Object.entries(selectedReturnItems)
      .filter(([_, details]) => details.quantity > 0)
      .map(([productId, details]) => ({
        productId,
        quantity: details.quantity,
        reason: details.reason || 'No reason specified',
      }));

    if (itemsToSubmit.length === 0) {
      Alert.alert('Error', 'Please select at least one item to return.');
      return;
    }

    if (returnPaymentMethod === 'upi' && !returnUpiScreenshot) {
      Alert.alert('Error', 'Please upload a screenshot of your UPI payment.');
      return;
    }

    setSubmittingReturn(true);
    try {
      await api.post('/returns/request', {
        orderId,
        items: itemsToSubmit,
        paymentMethod: returnPaymentMethod,
        upiPaymentScreenshot: returnUpiScreenshot,
        notes: returnNotes,
      });
      Alert.alert('Success', 'Return request submitted successfully.');
      setShowReturnModal(false);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Failed to request return';
      Alert.alert('Error', msg);
    } finally {
      setSubmittingReturn(false);
    }
  };

  useEffect(() => {
    const fetchClassifications = async () => {
      try {
        const response = await api.get('/reviews/classifications');
        setClassifications(response.data || []);
        if (response.data && response.data.length > 0) {
          setReviewClassification(response.data[0].name);
        }
      } catch (err) {
        if (__DEV__) console.warn('Failed to fetch review classifications', err);
      }
    };
    fetchClassifications();
  }, []);

  const handleOpenReviewModal = (productId: string, productName: string) => {
    setReviewProduct({ id: productId, name: productName });
    setReviewRating(5);
    if (classifications.length > 0) {
      setReviewClassification(classifications[0].name);
    } else {
      setReviewClassification('');
    }
    setReviewComment('');
    setShowReviewModal(true);
  };

  const handleReviewSubmit = async () => {
    if (!reviewProduct) return;
    if (!reviewComment.trim()) {
      Alert.alert('Required', 'Please enter a comment.');
      return;
    }
    if (!reviewClassification) {
      Alert.alert('Required', 'Please select a classification.');
      return;
    }

    setSubmittingReview(true);
    try {
      await api.post('/reviews/', {
        productId: reviewProduct.id,
        rating: reviewRating,
        comment: reviewComment.trim(),
        classification: reviewClassification,
      });
      Alert.alert('Success', 'Review submitted successfully and is pending admin approval.');
      setShowReviewModal(false);
      setReviewProduct(null);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Failed to submit review';
      Alert.alert('Error', msg);
    } finally {
      setSubmittingReview(false);
    }
  };

  useEffect(() => {
    const load = async () => {
      if (!orderId) return;
      setLoading(true);
      try {
        const res = await api.get(`/orders/${orderId}`);
        setOrder(res.data || null);
      } catch (e) {
        setOrder(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [orderId]);

  if (loading) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Order Details</Text>
        </View>
        <View style={styles.loaderWrap}>
          <ActivityIndicator size="large" color={colors.textPrimary} />
        </View>
      </SafeAreaView>
    );
  }

  if (!order) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Order Details</Text>
        </View>
        <View style={styles.loaderWrap}>
          <Text style={styles.text}>Order not found.</Text>
        </View>
      </SafeAreaView>
    );
  }

  const items = order.items || [];
  const paymentEntries = (order as any)?.paymentEntries || [];
  const shipping = order.shippingAddress || {};

  const formatAddress = () => {
    const parts = [
      shipping.street,
      shipping.city,
      shipping.state,
      shipping.zipCode,
      shipping.country,
    ].filter(Boolean);
    return parts.join(', ');
  };



  const downloadInvoice = async () => {
    if (!orderId) return;
    setDownloading(true);
    try {
      const base = (api as any)?.defaults?.baseURL || '';
      const url = `${base}/orders/${orderId}/invoice`;
      const token = await SecureStore.getItemAsync(TOKEN_KEY);
      const cacheDir = (FileSystem as any).cacheDirectory || (FileSystem as any).documentDirectory || '';
      const localUri = `${cacheDir}invoice-${orderId}.pdf`;

      const { status } = await FileSystem.downloadAsync(url, localUri, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (status !== 200) {
        Alert.alert('Error', 'Could not download invoice. Please try again.');
        return;
      }

      const canShare = await Sharing.isAvailableAsync();
      if (canShare) {
        await Sharing.shareAsync(localUri, {
          mimeType: 'application/pdf',
          dialogTitle: `Invoice #${orderId.slice(-6)}`,
          UTI: 'com.adobe.pdf',
        });
      } else {
        Alert.alert('Error', 'Sharing is not available on this device.');
      }
    } catch {
      Alert.alert('Error', 'Failed to download invoice. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Order Details</Text>
      </View>
      <ScrollView style={styles.container} contentContainerStyle={{ padding: spacing.md }}>
        <Text style={styles.title}>Order #{order._id?.slice(-6) || '—'}</Text>
        <Text style={styles.sub}>Status: {order.status || '—'}</Text>
        <Text style={styles.sub}>Payment: {order.paymentMethod || '—'}</Text>
        {order.total ? <Text style={styles.total}>₹{order.total}</Text> : null}
        {order.createdAt ? (
          <Text style={styles.meta}>Placed: {formatDateTimeIST(order.createdAt)}</Text>
        ) : null}

        {/* Delivery slot info */}
        {order.deliverySlot?.slotId && (
          <View
            style={[
              styles.section,
              {
                borderWidth: 1,
                borderColor: order.deliverySlot?.isUrgent ? '#FCD34D' : '#BAE6FD',
                backgroundColor: order.deliverySlot?.isUrgent ? '#FFFBEB' : '#EFF6FF',
              },
            ]}
          >
            <Text style={[styles.sectionTitle, { color: order.deliverySlot?.isUrgent ? '#92400E' : '#1E40AF' }]}>
              {order.deliverySlot?.isUrgent ? '⚡ Urgent Delivery Slot' : '🕐 Scheduled Delivery Slot'}
            </Text>
            {order.deliverySlot?.date ? (
              <Text style={[styles.text, { marginBottom: 4 }]}>
                <Text style={{ fontWeight: '600' }}>Date: </Text>{order.deliverySlot.date}
              </Text>
            ) : null}
            {order.deliverySlot?.startTime && order.deliverySlot?.endTime ? (
              <Text style={styles.text}>
                <Text style={{ fontWeight: '600' }}>Time: </Text>
                {order.deliverySlot.startTime} – {order.deliverySlot.endTime}
              </Text>
            ) : null}
          </View>
        )}

        <View style={styles.section}>
          <TouchableOpacity
            style={[styles.primaryBtn, downloading && { opacity: 0.7 }]}
            onPress={downloadInvoice}
            disabled={downloading}
          >
            {downloading ? (
              <ActivityIndicator color={colors.textOnPrimary} />
            ) : (
              <Text style={styles.primaryText}>Download Invoice</Text>
            )}
          </TouchableOpacity>

          {order.status === 'delivered' && user?.role === 'customer' && (
            <TouchableOpacity
              style={[styles.secondaryBtn, { marginTop: 10, borderColor: colors.error }]}
              onPress={handleOpenReturnModal}
              disabled={loadingEligibility}
            >
              {loadingEligibility ? (
                <ActivityIndicator color={colors.error} />
              ) : (
                <Text style={[styles.secondaryText, { color: colors.error }]}>Return Items</Text>
              )}
            </TouchableOpacity>
          )}
        </View>

        {items.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Items</Text>
            {items.map((it, idx) => (
              <View key={idx} style={styles.itemRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.itemTitle}>{it.product?.name || 'Item'}</Text>
                  <Text style={styles.itemMeta}>Qty: {it.quantity || 1}</Text>
                  {order.status === 'delivered' && it.product?._id && (
                    <TouchableOpacity
                      style={styles.reviewBtn}
                      onPress={() => handleOpenReviewModal(it.product._id, it.product.name)}
                    >
                      <Ionicons name="star-outline" size={12} color={colors.primary} />
                      <Text style={styles.reviewBtnText}>Review Product</Text>
                    </TouchableOpacity>
                  )}
                </View>
                {it.price ? <Text style={styles.itemPrice}>₹{it.price}</Text> : null}
              </View>
            ))}
          </View>
        )}

        {order.shippingAddress ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Shipping Address</Text>
            <Text style={styles.text}>{formatAddress() || '—'}</Text>
          </View>
        ) : null}

        {paymentEntries.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Payment Entries</Text>
            {paymentEntries.map((pe: any, idx: number) => (
              <View key={idx} style={styles.itemRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.itemTitle}>
                    #{pe.entryId || idx + 1} — ₹{pe.amount}
                  </Text>
                  <Text style={styles.itemMeta}>
                    Method: {pe.paymentMethod || order.paymentMethod || 'N/A'}
                  </Text>
                  {pe.notes ? <Text style={styles.itemMeta}>{pe.notes}</Text> : null}
                </View>
                <Text style={[styles.badge, pe.verified ? styles.badgeOk : styles.badgeWarn]}>
                  {pe.verified ? 'Verified' : 'Pending'}
                </Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      {/* Review Modal */}
      <Modal visible={showReviewModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalHeaderTitle}>Write a Review</Text>
              <TouchableOpacity onPress={() => setShowReviewModal(false)}>
                <Ionicons name="close" size={24} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalForm} contentContainerStyle={{ paddingBottom: 40 }}>
              <Text style={styles.productNameLabel}>{reviewProduct?.name}</Text>

              {/* Star Rating */}
              <Text style={styles.filterLabel}>Rating</Text>
              <View style={styles.starsRow}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <TouchableOpacity key={star} onPress={() => setReviewRating(star)}>
                    <Ionicons
                      name={star <= reviewRating ? 'star' : 'star-outline'}
                      size={36}
                      color={star <= reviewRating ? '#EAB308' : '#D1D5DB'}
                    />
                  </TouchableOpacity>
                ))}
              </View>

              {/* Classification */}
              {classifications.length > 0 && (
                <>
                  <Text style={styles.filterLabel}>Classification</Text>
                  <View style={styles.pickerContainer}>
                    {classifications.map((cls) => (
                      <TouchableOpacity
                        key={cls._id}
                        style={[
                          styles.chip,
                          reviewClassification === cls.name && styles.activeChip,
                        ]}
                        onPress={() => setReviewClassification(cls.name)}
                      >
                        <Text
                          style={[
                            styles.chipText,
                            reviewClassification === cls.name && styles.activeChipText,
                          ]}
                        >
                          {cls.name}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </>
              )}

              {/* Comment */}
              <Text style={styles.filterLabel}>Comment</Text>
              <TextInput
                placeholder="Write your review here..."
                value={reviewComment}
                onChangeText={setReviewComment}
                multiline
                numberOfLines={4}
                style={styles.commentInput}
                placeholderTextColor={colors.textMuted}
              />
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity onPress={() => setShowReviewModal(false)} style={styles.clearBtn} disabled={submittingReview}>
                <Text style={styles.clearBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={handleReviewSubmit} style={styles.applyBtn} disabled={submittingReview}>
                {submittingReview ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <Text style={styles.applyBtnText}>Submit Review</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Return Modal */}
      <Modal visible={showReturnModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { height: '80%' }]}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalHeaderTitle}>Return Items</Text>
              <TouchableOpacity onPress={() => setShowReturnModal(false)}>
                <Ionicons name="close" size={24} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalForm} contentContainerStyle={{ paddingBottom: 40 }}>
              <Text style={styles.filterLabel}>Select Items to Return</Text>
              {eligibleItems.map((item) => {
                const selection = selectedReturnItems[item.productId] || { quantity: 0, reason: '' };
                return (
                  <View key={item.productId} style={styles.returnItemCard}>
                    <View style={styles.returnItemRow}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.returnItemName} numberOfLines={1}>{item.name}</Text>
                        <Text style={styles.returnItemMeta}>Price: ₹{item.price} | Max: {item.maxQuantity}</Text>
                      </View>
                      <View style={styles.qtyContainer}>
                        <TouchableOpacity
                          style={styles.qtyBtn}
                          onPress={() => {
                            setSelectedReturnItems({
                              ...selectedReturnItems,
                              [item.productId]: {
                                ...selection,
                                quantity: Math.max(0, selection.quantity - 1),
                              },
                            });
                          }}
                        >
                          <Text style={styles.qtyBtnText}>-</Text>
                        </TouchableOpacity>
                        <Text style={styles.qtyValue}>{selection.quantity}</Text>
                        <TouchableOpacity
                          style={styles.qtyBtn}
                          onPress={() => {
                            setSelectedReturnItems({
                              ...selectedReturnItems,
                              [item.productId]: {
                                ...selection,
                                quantity: Math.min(item.maxQuantity, selection.quantity + 1),
                              },
                            });
                          }}
                        >
                          <Text style={styles.qtyBtnText}>+</Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                    {selection.quantity > 0 && (
                      <TextInput
                        placeholder="Reason for return"
                        value={selection.reason}
                        onChangeText={(text) => {
                          setSelectedReturnItems({
                            ...selectedReturnItems,
                            [item.productId]: { ...selection, reason: text },
                          });
                        }}
                        style={styles.reasonInput}
                        placeholderTextColor={colors.textMuted}
                      />
                    )}
                  </View>
                );
              })}

              <View style={styles.chargeBox}>
                <View>
                  <Text style={styles.chargeLabelText}>Return Pickup Fee</Text>
                  <Text style={styles.chargeSubtext}>Pickup fee for return delivery</Text>
                </View>
                <Text style={styles.chargeAmount}>₹{returnCharge}</Text>
              </View>

              {returnCharge > 0 && (
                <View style={{ marginTop: spacing.md }}>
                  <Text style={styles.filterLabel}>Payment Method for Pickup Fee</Text>
                  <View style={{ flexDirection: 'row', gap: 10, marginTop: 6 }}>
                    <TouchableOpacity
                      style={[styles.availBtn, returnPaymentMethod === 'cod' && styles.activeAvailBtn]}
                      onPress={() => setReturnPaymentMethod('cod')}
                    >
                      <Text style={[styles.availBtnText, returnPaymentMethod === 'cod' && styles.activeAvailBtnText]}>
                        Cash on Pickup (COD)
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.availBtn, returnPaymentMethod === 'upi' && styles.activeAvailBtn]}
                      onPress={() => setReturnPaymentMethod('upi')}
                    >
                      <Text style={[styles.availBtnText, returnPaymentMethod === 'upi' && styles.activeAvailBtnText]}>
                        Pay via UPI Now
                      </Text>
                    </TouchableOpacity>
                  </View>

                  {returnPaymentMethod === 'upi' && upiDetails && (
                    <View style={styles.upiDetailsBox}>
                      <Text style={styles.upiInfoText}>Scan QR code or send payment to UPI ID</Text>
                      {upiDetails.qrCodeUrl && (
                        <Image
                          source={{ uri: getImageUrl(upiDetails.qrCodeUrl) }}
                          style={styles.qrCodeImage}
                          resizeMode="contain"
                        />
                      )}
                      <Text style={styles.upiIdText}>UPI ID: {upiDetails.upiId}</Text>

                      <TouchableOpacity style={styles.uploadBtn} onPress={pickScreenshot}>
                        <Ionicons name="image-outline" size={16} color={colors.primary} />
                        <Text style={styles.uploadBtnText}>
                          {returnUpiScreenshot ? 'Change Screenshot' : 'Upload Screenshot'}
                        </Text>
                      </TouchableOpacity>
                      {returnUpiScreenshot && (
                        <Image
                          source={{ uri: returnUpiScreenshot }}
                          style={styles.screenshotPreview}
                          resizeMode="contain"
                        />
                      )}
                    </View>
                  )}
                </View>
              )}

              <Text style={styles.filterLabel}>Notes (Optional)</Text>
              <TextInput
                placeholder="Additional instructions..."
                value={returnNotes}
                onChangeText={setReturnNotes}
                multiline
                numberOfLines={2}
                style={styles.notesInput}
                placeholderTextColor={colors.textMuted}
              />
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity onPress={() => setShowReturnModal(false)} style={styles.clearBtn} disabled={submittingReturn}>
                <Text style={styles.clearBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={handleReturnSubmit} style={[styles.applyBtn, { backgroundColor: colors.error }]} disabled={submittingReturn}>
                {submittingReturn ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <Text style={styles.applyBtnText}>Submit Request</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.background,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backBtn: { marginRight: spacing.sm, padding: 4 },
  headerTitle: { ...typography.h3, color: colors.textPrimary, fontWeight: '600' },
  container: { flex: 1, backgroundColor: colors.background },
  loaderWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: spacing.md },
  title: { ...typography.h2, color: colors.textPrimary },
  sub: { ...typography.body, color: colors.textSecondary, marginTop: spacing.xs },
  total: { ...typography.h3, marginTop: spacing.sm, color: colors.textPrimary },
  meta: { ...typography.caption, color: colors.textSecondary, marginTop: spacing.xs },
  section: {
    marginTop: spacing.md,
    padding: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: 12,
    shadowColor: colors.textPrimary,
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  sectionTitle: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.sm },
  itemRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
  itemTitle: { ...typography.h3, color: colors.textPrimary },
  itemMeta: { ...typography.body, color: colors.textSecondary },
  itemPrice: { ...typography.h3, color: colors.textPrimary },
  text: { ...typography.body, color: colors.textSecondary },
  primaryBtn: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    borderRadius: 10,
    alignItems: 'center',
  },
  primaryText: { ...typography.h3, color: colors.textOnPrimary },
  badge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 12,
    fontWeight: '700',
    overflow: 'hidden',
  },
  badgeOk: { backgroundColor: colors.success, color: colors.textOnSuccess },
  badgeWarn: { backgroundColor: colors.warning, color: colors.textOnWarning },
  reviewBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 4,
    marginTop: 6,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  reviewBtnText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.primary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    height: '65%',
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    overflow: 'hidden',
  },
  modalHeader: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
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
    padding: spacing.md,
  },
  productNameLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  filterLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: spacing.md,
    marginBottom: spacing.xs,
  },
  starsRow: {
    flexDirection: 'row',
    gap: 8,
    marginVertical: spacing.xs,
  },
  pickerContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginVertical: spacing.xs,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: '#FFFFFF',
  },
  activeChip: {
    borderColor: colors.primary,
    backgroundColor: colors.background,
  },
  chipText: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  activeChipText: {
    color: colors.primary,
    fontWeight: '600',
  },
  commentInput: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    fontSize: 14,
    color: colors.textPrimary,
    minHeight: 80,
    textAlignVertical: 'top',
    marginTop: spacing.xs,
  },
  modalFooter: {
    flexDirection: 'row',
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    gap: 12,
    backgroundColor: '#FFFFFF',
  },
  clearBtn: {
    flex: 1,
    height: 44,
    borderRadius: 8,
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
    height: 44,
    borderRadius: 8,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  applyBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textOnPrimary,
  },
  secondaryBtn: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: colors.primary,
    paddingVertical: spacing.sm,
    borderRadius: 10,
    alignItems: 'center',
  },
  secondaryText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  returnItemCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.sm,
    marginBottom: 10,
  },
  returnItemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  returnItemName: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  returnItemMeta: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  qtyContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 6,
    backgroundColor: '#fff',
  },
  qtyBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  qtyBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  qtyValue: {
    paddingHorizontal: 10,
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  reasonInput: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 6,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    fontSize: 12,
    color: colors.textPrimary,
    marginTop: 8,
    backgroundColor: '#fff',
  },
  chargeBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FEF2F2',
    borderColor: '#FCA5A5',
    borderWidth: 1,
    borderRadius: 8,
    padding: spacing.sm,
    marginTop: spacing.md,
  },
  chargeLabelText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#991B1B',
  },
  chargeSubtext: {
    fontSize: 10,
    color: '#B91C1C',
    marginTop: 2,
  },
  chargeAmount: {
    fontSize: 16,
    fontWeight: '750',
    color: '#991B1B',
  },
  notesInput: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    fontSize: 13,
    color: colors.textPrimary,
    minHeight: 50,
    textAlignVertical: 'top',
    marginTop: spacing.xs,
  },
  availBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  activeAvailBtn: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  availBtnText: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  activeAvailBtnText: {
    color: '#FFFFFF',
  },
  upiDetailsBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.sm,
    marginTop: 10,
    alignItems: 'center',
  },
  upiInfoText: {
    fontSize: 11,
    color: colors.textSecondary,
    marginBottom: 8,
    textAlign: 'center',
  },
  qrCodeImage: {
    width: 140,
    height: 140,
    backgroundColor: '#fff',
    borderRadius: 6,
  },
  upiIdText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textPrimary,
    marginVertical: 8,
  },
  uploadBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1,
    borderColor: colors.primary,
    borderRadius: 6,
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#fff',
  },
  uploadBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
  },
  screenshotPreview: {
    width: '100%',
    height: 120,
    marginTop: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: colors.border,
  },
});
