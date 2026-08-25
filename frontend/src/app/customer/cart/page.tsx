'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { useCart } from '@/context/CartContext';
import api from '@/utils/api';
import {
  recordEvent,
  trackEcommerceEvent,
  trackAddToWishlist,
  trackRecommendationAddToCart,
  trackRecommendationProductClick,
  trackBackendCartRemove,
  trackBackendCartAdd,
  trackWebAdConversion,
  getSessionId,
} from '@/utils/analytics';
import { useRecommendationSectionView } from '@/hooks/useRecommendationSectionView';
import Link from 'next/link';
import {
  getGuestCart,
  addGuestCartItem,
  updateGuestCartQty,
  removeGuestCartItem,
  saveGuestCart,
  addGuestWishlistItem,
} from '@/utils/guestStore';
import { getImageUrl } from '@/utils/imageUrl';
import Header from '@/components/Header';
import ck from './checkout.module.css';
import SearchableSelect from '@/components/SearchableSelect';

export default function Cart() {
  const [cart, setCart] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [pendingRemoveItem, setPendingRemoveItem] = useState<{ itemId: string; item: any } | null>(null);
  const [cartError, setCartError] = useState(false);
  const [giftWrapItems, setGiftWrapItems] = useState<any[]>([]);
  const [wishlistItems, setWishlistItems] = useState<any[]>([]);
  const [impulseBuyItems, setImpulseBuyItems] = useState<any[]>([]);
  const [checkoutData, setCheckoutData] = useState({
    shippingAddress: {
      street: '',
      city: '',
      state: '',
      district: '',
      zipCode: '',
      country: '',
      addressLine2: '',
      landmark: '',
      name: '',
    },
    billingAddress: {
      street: '',
      city: '',
      state: '',
      district: '',
      zipCode: '',
      country: '',
      addressLine2: '',
      landmark: '',
      name: '',
    },
    paymentMethod: 'cod',
    printedBill: false,
    upiPaymentScreenshot: null as string | null,
    notes: '',
  });
  // Auth-in-checkout state
  const [authPhone, setAuthPhone] = useState('');
  const [authPhoneChecked, setAuthPhoneChecked] = useState(false);
  const [authIsExisting, setAuthIsExisting] = useState(false);
  const [authPassword, setAuthPassword] = useState('');
  const [authConfirmPassword, setAuthConfirmPassword] = useState('');
  const [authOtp, setAuthOtp] = useState('');
  const [authOtpSent, setAuthOtpSent] = useState(false);
  const [authOtpVerified, setAuthOtpVerified] = useState(false);
  const [authOtpToken, setAuthOtpToken] = useState(''); // Token from MSG91 SDK
  const [authCanResend, setAuthCanResend] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);

  const [showAddressDropdown, setShowAddressDropdown] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [upiDetails, setUpiDetails] = useState<any>(null);
  const [upiDetailsError, setUpiDetailsError] = useState(false);
  const [showUpiPayment, setShowUpiPayment] = useState(false);
  const [pincodeServiceable, setPincodeServiceable] = useState<boolean | null>(null);
  const [checkingServiceability, setCheckingServiceability] = useState(false);
  const [checkoutStep, setCheckoutStep] = useState(1);
  const [referralEligible, setReferralEligible] = useState(false);
  const [enabledFlags, setEnabledFlags] = useState<string[]>([]);
  const [referralCodeInput, setReferralCodeInput] = useState('');
  const [appliedReferralCode, setAppliedReferralCode] = useState('');
  const [referralDiscountInfo, setReferralDiscountInfo] = useState<{
    discountType: 'percentage' | 'fixed';
    discountValue: number;
    referrerName?: string;
  } | null>(null);
  const [referralError, setReferralError] = useState('');
  const [verifyingReferral, setVerifyingReferral] = useState(false);
  const [couponInput, setCouponInput] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState<{
    code: string;
    discountType: string;
    discountValue: number;
    discount: number;
  } | null>(null);
  const [couponError, setCouponError] = useState('');
  const [verifyingCoupon, setVerifyingCoupon] = useState(false);
  const [deliveryChargeInfo, setDeliveryChargeInfo] = useState<{charge: number, gstPercentage: number, gstAmount: number, totalCharge: number} | null>(null);
  const [fetchingDeliveryCharge, setFetchingDeliveryCharge] = useState(false);

  // Delivery slot state
  const [deliveryOptions, setDeliveryOptions] = useState<{ slotBookingAvailable: boolean; availableDates: string[] } | null>(null);
  const [selectedDeliveryType, setSelectedDeliveryType] = useState<'standard' | 'slot'>('standard');
  const [selectedSlotDate, setSelectedSlotDate] = useState('');
  const [availableSlots, setAvailableSlots] = useState<any[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<any | null>(null);
  const [loadingSlots, setLoadingSlots] = useState(false);

  const [showAddressModal, setShowAddressModal] = useState(false);
  const [newAddress, setNewAddress] = useState({
    street: '',
    city: '',
    state: '',
    district: '',
    zipCode: '',
    country: 'India',
    addressLine2: '',
    landmark: '',
    name: '',
  });
  // Location master data for checkout
  const [checkoutStates, setCheckoutStates] = useState<string[]>([]);
  const [checkoutDistricts, setCheckoutDistricts] = useState<string[]>([]);
  const [newAddrDistricts, setNewAddrDistricts] = useState<string[]>([]);
  const router = useRouter();
  const { user, login, loginWithTokens } = useAuth();
  const isValet = (user as any)?.role === 'valet';
  const { theme } = useTheme();
  const { duesInfo, fetchDuesInfo } = useCart();
  const [showDuesModal, setShowDuesModal] = useState(false);
  const [selectedBillForSettle, setSelectedBillForSettle] = useState<any>(null);
  const [duesSettleAmount, setDuesSettleAmount] = useState('');
  const [duesSettleImage, setDuesSettleImage] = useState<string | null>(null);
  const [settlingDuesPayment, setSettlingDuesPayment] = useState(false);

  useEffect(() => {
    // Check url parameter to show dues modal immediately if requested
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('showDues') === 'true') {
        setShowDuesModal(true);
      }
    }
  }, []);

  const handleDuesFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setDuesSettleImage(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleSettleDueBill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBillForSettle) return;
    const settleAmt = parseFloat(duesSettleAmount);
    if (isNaN(settleAmt) || settleAmt <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    if (!duesSettleImage) {
      toast.error('Please upload your UPI payment screenshot');
      return;
    }
    setSettlingDuesPayment(true);
    try {
      await api.post(`/orders/${selectedBillForSettle.orderId}/settle-credit`, {
        amount: settleAmt,
        paymentImage: duesSettleImage,
        upiPaymentScreenshot: duesSettleImage
      });
      toast.success('Dues payment submitted successfully! Awaiting admin verification.');
      setSelectedBillForSettle(null);
      setDuesSettleAmount('');
      setDuesSettleImage(null);
      fetchDuesInfo();
      fetchCart();
    } catch (err: any) {
      toast.error(err.response?.data?.message || err.response?.data?.detail || 'Failed to submit settlement');
    } finally {
      setSettlingDuesPayment(false);
    }
  };

  const MOBILE_ACCENT = theme.primary || '#1a4d33';
  const [isMobile, setIsMobile] = useState(false);
  const quickPicksSectionRef = useRecommendationSectionView('quick_picks');

  // Fetch location states on mount
  const fetchCheckoutStates = async () => {
    try {
      const res = await api.get('/pincodes/states', { skipAccessToken: true } as any);
      setCheckoutStates(res.data || []);
    } catch (_err) {
      console.error('Failed to fetch states:', _err);
    }
  };
  const fetchCheckoutDistricts = async (state: string, setter: (d: string[]) => void) => {
    if (!state) {
      setter([]);
      return;
    }
    try {
      const res = await api.get(`/pincodes/districts?state=${encodeURIComponent(state)}`, {
        skipAccessToken: true,
      } as any);
      setter(res.data || []);
    } catch (_err) {
      console.error('Failed to fetch districts:', _err);
      setter([]);
    }
  };

  useEffect(() => {
    fetchCart();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);


  const fetchFlags = async () => {
    try {
      const response = await api.get('/feature-flags/enabled');
      const flags = response.data || [];
      setEnabledFlags(flags.map((f: any) => f.id));
    } catch (err) {
      console.error('Failed to fetch enabled feature flags:', err);
    }
  };

  useEffect(() => {
    fetchUPIDetails();
    fetchGiftWrapItems();
    fetchImpulseBuy();
    fetchCheckoutStates();
    fetchFlags();
    if (user) {
      fetchWishlist();
      prefillAddress();
      checkReferralEligibility();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Auto-select valid payment method if current is disabled
  useEffect(() => {
    if (enabledFlags.length > 0) {
      const isWholesale = (user as any)?.role === 'wholesaler';
      const segmentPrefix = isWholesale ? 'wholesale' : 'retail';
      const isCod = enabledFlags.includes(`${segmentPrefix}_enable_cod`);
      const isUpi = enabledFlags.includes(`${segmentPrefix}_enable_upi`);
      const isCredit = isWholesale && enabledFlags.includes(`${segmentPrefix}_enable_credit`);
      
      const current = checkoutData.paymentMethod;
      if (current === 'cod' && !isCod) {
        if (isUpi) setCheckoutData(prev => ({ ...prev, paymentMethod: 'upi' }));
        else if (isCredit) setCheckoutData(prev => ({ ...prev, paymentMethod: 'credit' }));
      } else if (current === 'upi' && !isUpi) {
        if (isCod) setCheckoutData(prev => ({ ...prev, paymentMethod: 'cod' }));
        else if (isCredit) setCheckoutData(prev => ({ ...prev, paymentMethod: 'credit' }));
      } else if (current === 'credit' && !isCredit) {
        if (isCod) setCheckoutData(prev => ({ ...prev, paymentMethod: 'cod' }));
        else if (isUpi) setCheckoutData(prev => ({ ...prev, paymentMethod: 'upi' }));
      }
    }
  }, [enabledFlags, user, checkoutData.paymentMethod]);

  // Track checkout funnel steps automatically
  useEffect(() => {
    if (!showCheckout) return;
    
    const sid = getSessionId();
    const pagePath = `/checkout/step${checkoutStep}`;
    
    // 1. Log page view to database for funnel tracking
    if (sid) {
      api.post('/tracking/page-view', {
        page: pagePath,
        sessionId: sid,
      }).catch(() => {});
    }
    
    // 2. Dispatch GTM page view event
    recordEvent({ type: 'page_view', page: pagePath });
    
    // 3. Dispatch GA4 checkout step events
    const inStock = cart?.items?.filter((item: any) => !item.outOfStock) || [];
    const value = inStock.reduce((s: number, i: any) => s + (i.price || 0) * i.quantity, 0);
    const items = inStock.map((item: any) => ({
      item_id: item.product._id || item.product,
      item_name: item.product.name,
      price: item.price,
      item_brand: item.product.brand,
      item_category: item.product.category,
      quantity: item.quantity,
    }));
    
    if (checkoutStep === 2) {
      trackEcommerceEvent('add_shipping_info' as any, {
        value,
        currency: 'INR',
        items,
        shipping_tier: 'Standard',
      });
    } else if (checkoutStep === 3) {
      trackEcommerceEvent('add_payment_info' as any, {
        value,
        currency: 'INR',
        items,
        payment_type: checkoutData.paymentMethod || 'UPI',
      });
    }
  }, [showCheckout, checkoutStep, cart, checkoutData.paymentMethod]);

  useEffect(() => {
    const check = () => setIsMobile(typeof window !== 'undefined' && window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  // Track checkout step drop-off and cart abandonment on page unload or visibility change
  useEffect(() => {
    if (!showCheckout) return;

    const trackAbandonmentAndDropOff = () => {
      const sid = getSessionId();
      if (!sid) return;

      const pagePath = `/checkout/step${checkoutStep}`;
      const inStock = cart?.items?.filter((item: any) => !item.outOfStock) || [];

      // 1. Cart Abandonment Beacon
      if (inStock.length > 0) {
        const blob = new Blob([JSON.stringify({
          type: 'cart_abandonment',
          cartItems: inStock.map((item: any) => ({
            productId: item.product._id || item.product,
            productName: item.product.name,
            quantity: item.quantity,
            price: item.price,
          })),
          cartValue: inStock.reduce((s: number, i: any) => s + (i.price || 0) * i.quantity, 0),
          sessionId: sid,
        })], { type: 'application/json' });
        
        navigator.sendBeacon(
          `${process.env.NEXT_PUBLIC_API_URL}/tracking/beacon`,
          blob
        );
      }

      // 2. Checkout Step Drop-off Beacon
      const dropOffBlob = new Blob([JSON.stringify({
        type: 'drop_off',
        page: pagePath,
        reason: 'unload',
        sessionId: sid,
      })], { type: 'application/json' });
      
      navigator.sendBeacon(
        `${process.env.NEXT_PUBLIC_API_URL}/tracking/beacon`,
        dropOffBlob
      );
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        trackAbandonmentAndDropOff();
      }
    };

    window.addEventListener('beforeunload', trackAbandonmentAndDropOff);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', trackAbandonmentAndDropOff);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [showCheckout, checkoutStep, cart]);

  const prefillAddress = () => {
    if ((user as any)?.address) {
      const userAddress = (user as any).address;
      setCheckoutData((prev) => ({
        ...prev,
        shippingAddress: {
          street: userAddress.street || prev.shippingAddress.street,
          city: userAddress.city || prev.shippingAddress.city,
          state: userAddress.state || prev.shippingAddress.state,
          district: userAddress.district || prev.shippingAddress.district || '',
          zipCode: userAddress.pincode || userAddress.zipCode || prev.shippingAddress.zipCode,
          country: userAddress.country || prev.shippingAddress.country,
          addressLine2: userAddress.addressLine2 || prev.shippingAddress.addressLine2 || '',
          landmark: userAddress.landmark || prev.shippingAddress.landmark || '',
          name: userAddress.name || prev.shippingAddress.name || '',
        },
      }));
      const pincode = userAddress.pincode || userAddress.zipCode;
      if (pincode) checkPincodeServiceability(pincode);
      if (userAddress.state) fetchCheckoutDistricts(userAddress.state, setCheckoutDistricts);
    }
  };

  const checkReferralEligibility = async () => {
    if (!user) return;
    try {
      const res = await api.get('/referrals/check-eligibility');
      setReferralEligible(res.data.eligible);
    } catch (err) {
      console.error('Failed to check referral eligibility:', err);
      setReferralEligible(false);
    }
  };

  const handleApplyReferral = async () => {
    const code = referralCodeInput.trim().toUpperCase();
    if (!code) {
      setReferralError('Please enter a referral code');
      return;
    }
    try {
      setVerifyingReferral(true);
      setReferralError('');
      const res = await api.post('/referrals/verify', { code });
      setAppliedReferralCode(code);
      setReferralDiscountInfo({
        discountType: res.data.discountType,
        discountValue: res.data.discountValue,
        referrerName: res.data.referrerName,
      });
      toast.success(`Referral code "${code}" applied successfully!`);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Invalid referral code';
      setReferralError(msg);
      toast.error(msg);
    } finally {
      setVerifyingReferral(false);
    }
  };

  const handleRemoveReferral = () => {
    setAppliedReferralCode('');
    setReferralCodeInput('');
    setReferralDiscountInfo(null);
    setReferralError('');
    toast.info('Referral code removed');
  };

  const handleApplyCoupon = async () => {
    const code = couponInput.trim().toUpperCase();
    if (!code) {
      setCouponError('Please enter a coupon code');
      return;
    }
    try {
      setVerifyingCoupon(true);
      setCouponError('');
      const res = await api.get(`/coupons/validate/${code}`, {
        params: { amount: subtotalValue },
      });
      setAppliedCoupon({
        code: res.data.coupon.code,
        discountType: res.data.coupon.discountType,
        discountValue: res.data.coupon.discountValue,
        discount: res.data.discount,
      });
      toast.success(`Coupon "${code}" applied! You save ₹${res.data.discount.toFixed(2)}`);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Invalid or expired coupon';
      setCouponError(msg);
    } finally {
      setVerifyingCoupon(false);
    }
  };

  const handleRemoveCoupon = () => {
    setAppliedCoupon(null);
    setCouponInput('');
    setCouponError('');
    toast.info('Coupon removed');
  };

  const inStockItems = useMemo(() => {
    return cart?.items?.filter((item: any) => !item.outOfStock) || [];
  }, [cart?.items]);

  const inStockSubtotal = useMemo(() => {
    return inStockItems.reduce((s: number, i: any) => s + (i.subtotal || 0), 0);
  }, [inStockItems]);

  const subtotalValue = inStockSubtotal;
  
  const referralDiscountAmount = useMemo(() => {
    if (!referralDiscountInfo || subtotalValue <= 0) return 0;
    if (referralDiscountInfo.discountType === 'percentage') {
      return (subtotalValue * referralDiscountInfo.discountValue) / 100;
    } else {
      return Math.min(referralDiscountInfo.discountValue, subtotalValue);
    }
  }, [referralDiscountInfo, subtotalValue]);

  const couponDiscountAmount = appliedCoupon?.discount ?? 0;

  const finalTotalAmount = useMemo(() => {
    let total = Math.max(0, subtotalValue - referralDiscountAmount - couponDiscountAmount);
    if (deliveryChargeInfo?.totalCharge) {
      total += deliveryChargeInfo.totalCharge;
    }
    return total;
  }, [subtotalValue, referralDiscountAmount, couponDiscountAmount, deliveryChargeInfo]);

  useEffect(() => {
    if (checkoutStep === 3 && checkoutData.shippingAddress?.zipCode) {
      const fetchDeliveryInfo = async () => {
        try {
          setFetchingDeliveryCharge(true);
          const userRole = (user as any)?.role || 'customer';
          const orderAmount = Math.max(0, subtotalValue - referralDiscountAmount);
          const res = await api.get('/delivery-charges/location', {
            params: {
              state: checkoutData.shippingAddress.state,
              city: checkoutData.shippingAddress.city,
              district: checkoutData.shippingAddress.district || checkoutData.shippingAddress.city,
              pincode: checkoutData.shippingAddress.zipCode,
              userRole,
              orderAmount,
            }
          });
          setDeliveryChargeInfo(res.data);
        } catch (e) {
          console.error('Failed to fetch delivery charge', e);
        } finally {
          setFetchingDeliveryCharge(false);
        }
      };
      fetchDeliveryInfo();
    }
  }, [checkoutStep, checkoutData.shippingAddress, user, subtotalValue, referralDiscountAmount]);

  const checkPincodeServiceability = async (pincode: string) => {
    if (!pincode || pincode.length !== 6) {
      setPincodeServiceable(null);
      setDeliveryOptions(null);
      return;
    }
    try {
      setCheckingServiceability(true);
      const userRole = (user as any)?.role || 'customer';
      const response = await api.get('/delivery-charges/check-serviceability', {
        params: { pincode, userRole },
      });
      setPincodeServiceable(response.data.isServiceable);
      setDeliveryOptions({
        slotBookingAvailable: response.data.slotBookingAvailable ?? false,
        availableDates: response.data.availableDates ?? [],
      });
      // Reset slot selection when pincode changes
      setSelectedDeliveryType('standard');
      setSelectedSlot(null);
      setSelectedSlotDate('');
      setAvailableSlots([]);
    } catch {
      setPincodeServiceable(null);
      setDeliveryOptions(null);
    } finally {
      setCheckingServiceability(false);
    }
  };

  const fetchSlotsForDate = async (date: string) => {
    if (!date) return;
    const pincode = checkoutData.shippingAddress.zipCode;
    const segment = (user as any)?.role === 'wholesaler' ? 'wholesale' : 'retail';
    setLoadingSlots(true);
    setSelectedSlot(null);
    try {
      const res = await api.get('/delivery-slots/available', {
        params: { date, pincode, segment },
        skipAccessToken: true,
      } as any);
      setAvailableSlots(res.data || []);
    } catch {
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const fetchUPIDetails = async () => {
    try {
      const r = await api.get('/upi/details');
      setUpiDetails(r.data);
      setUpiDetailsError(false);
    } catch {
      setUpiDetailsError(true);
    }
  };


  const isSameCart = (c1: any, c2: any) => {
    if (!c1 || !c2) return c1 === c2;
    if (c1.subtotal !== c2.subtotal) return false;
    if (c1.items?.length !== c2.items?.length) return false;
    for (let i = 0; i < c1.items.length; i++) {
      const item1 = c1.items[i];
      const item2 = c2.items[i];
      const id1 = item1._id || item1.product?._id;
      const id2 = item2._id || item2.product?._id;
      if (id1 !== id2) return false;
      if (item1.quantity !== item2.quantity) return false;
      if (item1.price !== item2.price) return false;
      if (item1.outOfStock !== item2.outOfStock) return false;
      if (item1.subtotal !== item2.subtotal) return false;
      if (item1.product?.name !== item2.product?.name) return false;
      if (item1.product?.price !== item2.product?.price) return false;
      if (item1.product?.stock !== item2.product?.stock) return false;
      const img1 = item1.product?.displayImage || item1.product?.images?.[0];
      const img2 = item2.product?.displayImage || item2.product?.images?.[0];
      if (img1 !== img2) return false;
    }
    return true;
  };

  // ─── Cart fetching (backend or guest local storage) ───────────────
  const fetchCart = async () => {
    try {
      setCartError((prev) => prev ? false : prev);
      if (user) {
        const response = await api.get('/cart');
        setCart((prev: any) => {
          if (isSameCart(prev, response.data)) return prev;
          return response.data;
        });
      } else {
        // Build a cart-like structure from guest local storage
        const guestItems = getGuestCart();
        const refreshedItems = await Promise.all(
          guestItems.map(async (g) => {
            try {
              const res = await api.get(`/products/public/${g.productId}`, {
                params: { role: 'customer' },
              });
              return {
                ...g,
                product: res.data,
              };
            } catch (err) {
              console.error(`Failed to refresh price for product ${g.productId}`, err);
              return g;
            }
          })
        );
        saveGuestCart(refreshedItems);

        const refreshedSubtotal = refreshedItems.reduce(
          (s, g) => s + (g.product?.price || 0) * g.quantity,
          0
        );

        const newCart = {
          items: refreshedItems.map((g) => {
            const itemPrice = g.product?.price || 0;
            const itemQty = g.quantity || 1;
            return {
              _id: g.productId,
              product: g.product || { _id: g.productId, name: 'Product', price: 0 },
              price: itemPrice,
              quantity: itemQty,
              subtotal: itemPrice * itemQty,
            };
          }),
          subtotal: refreshedSubtotal,
        };

        setCart((prev: any) => {
          if (isSameCart(prev, newCart)) return prev;
          return newCart;
        });
      }
    } catch {
      setCartError(true);
      setCart(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchGiftWrapItems = async () => {
    try {
      const res = await api.get('/collections/public', {
        params: { visiblePage: 'Cart', pageType: 'Cart', userRole: (user as any)?.role || 'guest' },
      });
      const col = (res.data || []).find((c: any) => c.name === 'Gift Wrap');
      if (col?._id) {
        const r = await api.get(`/collections/${col._id}/products`);
        setGiftWrapItems(r.data || []);
      } else setGiftWrapItems([]);
    } catch {
      setGiftWrapItems([]);
    }
  };

  const fetchWishlist = async () => {
    if (!user) return;
    try {
      const r = await api.get('/wishlist');
      setWishlistItems(r.data.items || []);
    } catch {}
  };

  const fetchImpulseBuy = async () => {
    try {
      const res = await api.get('/collections/public', {
        params: { visiblePage: 'Cart', pageType: 'Cart', userRole: (user as any)?.role || 'guest' },
      });
      const col = (res.data || []).find((c: any) => c.name === 'Impulse Buy');
      if (col?._id) {
        const r = await api.get(`/collections/${col._id}/products`);
        setImpulseBuyItems(r.data || []);
      }
    } catch {}
  };

  const handleAddToCart = async (productId: string, product?: any) => {
    try {
      if (user) {
        await api.post('/cart', { productId, quantity: 1 });
      } else {
        addGuestCartItem(productId, 1, product);
        trackBackendCartAdd(productId, 1).catch(() => {});
      }
      toast.success('Added to cart');
      fetchCart();
      fetchWishlist();
    } catch {
      toast.error('Failed to add to cart');
    }
  };

  /** Add to cart from a cart section (tracks recommendation_add_to_cart with section slot) */
  const handleAddToCartFromRecommendation = async (
    productId: string,
    product: any,
    recommendationSlot: string
  ) => {
    trackRecommendationAddToCart({
      productId,
      productName: product?.name,
      recommendationSlot,
      strategy: product?._strategy,
    });
    await handleAddToCart(productId, product);
  };

  /** Navigate to product page from a cart section (tracks recommendation_product_click) */
  const handleRecommendationProductClick = (
    productId: string,
    productName: string | undefined,
    recommendationSlot: string,
    product?: any
  ) => {
    trackRecommendationProductClick({
      productId,
      productName,
      recommendationSlot,
      strategy: product?._strategy,
    });
    router.push(`/customer/product/${productId}`);
  };

  const handleQuantityChange = async (itemId: string, newQuantity: number) => {
    // Optimistic Update
    setCart((prevCart: any) => {
      if (!prevCart || !prevCart.items) return prevCart;
      const updatedItems = prevCart.items.map((item: any) => {
        const id = user ? item._id : item.product?._id || item._id;
        if (id === itemId) {
          const price = item.price ?? item.product?.price ?? 0;
          return {
            ...item,
            quantity: newQuantity,
            subtotal: price * newQuantity,
          };
        }
        return item;
      });
      const newSubtotal = updatedItems.reduce((acc: number, item: any) => acc + (item.subtotal || 0), 0);
      return {
        ...prevCart,
        items: updatedItems,
        subtotal: newSubtotal,
      };
    });

    try {
      if (user) {
        await api.put(`/cart/${itemId}`, { quantity: newQuantity });
      } else {
        updateGuestCartQty(itemId, newQuantity);
      }
      await fetchCart();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update cart');
      fetchCart();
    }
  };

  const selectSavedAddress = (addr: any) => {
    setCheckoutData({
      ...checkoutData,
      shippingAddress: {
        street: addr.street || '',
        city: addr.city || '',
        state: addr.state || '',
        zipCode: addr.zipCode || addr.pincode || '',
        district: addr.district || '',
        country: addr.country || 'India',
        addressLine2: addr.addressLine2 || '',
        landmark: addr.landmark || '',
        name: addr.name || '',
      },
    });
    setShowAddressDropdown(false);
    if (addr.state) fetchCheckoutDistricts(addr.state, setCheckoutDistricts);
    const pincode = addr.zipCode || addr.pincode;
    if (pincode) checkPincodeServiceability(pincode);
  };

  const handleRemoveItem = (itemId: string, item: any) => {
    if (user) {
      // Show inline confirmation bar instead of browser dialog
      setPendingRemoveItem({ itemId, item });
    } else {
      // Guest remove: optimistic update
      setCart((prevCart: any) => {
        if (!prevCart || !prevCart.items) return prevCart;
        const updatedItems = prevCart.items.filter((item: any) => {
          const id = item.product?._id || item._id;
          return id !== itemId;
        });
        const newSubtotal = updatedItems.reduce((acc: number, i: any) => acc + (i.subtotal || 0), 0);
        return {
          ...prevCart,
          items: updatedItems,
          subtotal: newSubtotal,
        };
      });
      removeGuestCartItem(itemId);
      fetchCart();
      trackBackendCartRemove(item.product?._id || item._id, item.quantity || 1);
    }
  };

  const confirmSaveForLater = async () => {
    if (!pendingRemoveItem) return;
    const { itemId, item } = pendingRemoveItem;
    const productId = item?.product?._id || item?.product || item?._id;
    setPendingRemoveItem(null);

    // Optimistic remove
    setCart((prevCart: any) => {
      if (!prevCart || !prevCart.items) return prevCart;
      const updatedItems = prevCart.items.filter((item: any) => {
        const id = user ? item._id : item.product?._id || item._id;
        return id !== itemId;
      });
      const newSubtotal = updatedItems.reduce((acc: number, i: any) => acc + (i.subtotal || 0), 0);
      return {
        ...prevCart,
        items: updatedItems,
        subtotal: newSubtotal,
      };
    });

    try {
      trackAddToWishlist({ productId, productName: item?.product?.name, source: 'cart' });
      await api.post('/cart/save-for-later', { productId });
      await api.delete(`/cart/${itemId}`);
      recordEvent({ type: 'cart_remove', payload: { productId, action: 'save_for_later' } });
      toast.success('Item saved for later');
      await fetchCart();
      fetchWishlist();
    } catch {
      toast.error('Failed to save for later');
      fetchCart();
    }
  };

  const confirmRemoveItem = async () => {
    if (!pendingRemoveItem) return;
    const { itemId, item } = pendingRemoveItem;
    const productId = item?.product?._id || item?.product || item?._id;
    setPendingRemoveItem(null);

    // Optimistic remove
    setCart((prevCart: any) => {
      if (!prevCart || !prevCart.items) return prevCart;
      const updatedItems = prevCart.items.filter((item: any) => {
        const id = user ? item._id : item.product?._id || item._id;
        return id !== itemId;
      });
      const newSubtotal = updatedItems.reduce((acc: number, i: any) => acc + (i.subtotal || 0), 0);
      return {
        ...prevCart,
        items: updatedItems,
        subtotal: newSubtotal,
      };
    });

    try {
      await api.delete(`/cart/${itemId}`);
      recordEvent({ type: 'cart_remove', payload: { productId, action: 'remove' } });
      trackBackendCartRemove(productId, item.quantity || 1);
      await fetchCart();
    } catch {
      toast.error('Failed to remove item');
      fetchCart();
    }
  };

  const handleMoveToWishlist = async (itemId: string, item: any) => {
    const productId = item?.product?._id || item?.product || item?._id;

    // Optimistic remove
    setCart((prevCart: any) => {
      if (!prevCart || !prevCart.items) return prevCart;
      const updatedItems = prevCart.items.filter((item: any) => {
        const id = user ? item._id : item.product?._id || item._id;
        return id !== itemId;
      });
      const newSubtotal = updatedItems.reduce((acc: number, i: any) => acc + (i.subtotal || 0), 0);
      return {
        ...prevCart,
        items: updatedItems,
        subtotal: newSubtotal,
      };
    });

    try {
      trackAddToWishlist({ productId, productName: item?.product?.name, source: 'cart' });
      if (user) {
        await api.post('/cart/save-for-later', { productId });
        await api.delete(`/cart/${itemId}`);
      } else {
        // Guest: add to guest wishlist and remove from guest cart
        addGuestWishlistItem(productId, item?.product);
        removeGuestCartItem(itemId);
      }
      recordEvent({ type: 'cart_remove', payload: { productId, action: 'save_for_later' } });
      toast.success('Item moved to wishlist');
      await fetchCart();
      fetchWishlist();
    } catch {
      toast.error('Failed to move to wishlist');
      fetchCart();
    }
  };

  // ═══════════════════════════════════════════════════════════════════
  //  AUTH-IN-CHECKOUT HANDLERS
  // ═══════════════════════════════════════════════════════════════════
  const handleCheckPhone = async () => {
    const clean = authPhone.replace(/\D/g, '');
    if (!clean || clean.length < 10) {
      toast.error('Enter a valid 10-digit phone number');
      return;
    }
    setAuthBusy(true);
    try {
      const res = await api.post('/auth/check-phone', { phone: clean });
      setAuthIsExisting(res.data.exists);
      setAuthPhoneChecked(true);
    } catch {
      toast.error('Could not verify phone. Please try again.');
    }
    setAuthBusy(false);
  };

  const handleAuthLogin = async () => {
    if (!authPassword) {
      toast.error('Enter your password');
      return;
    }
    setAuthBusy(true);
    try {
      await login(authPhone, authPassword);
      toast.success('Logged in');
      fetchCart();
    } catch {}
    setAuthBusy(false);
  };

  const handleSendOtp = async () => {
    const clean = authPhone.replace(/\D/g, '');
    if (clean.length < 10) {
      toast.error('Enter a valid 10-digit number');
      return;
    }

    setAuthBusy(true);
    try {
      // Use MSG91 Global Method if available
      if (typeof window !== 'undefined' && (window as any).sendOtp) {
        // MSG91 expects mobile with country code (91)
        (window as any).sendOtp(
          '91' + clean,
          // eslint-disable-next-line unused-imports/no-unused-vars
          (data: any) => {
            setAuthOtpSent(true);
            setAuthCanResend(false);
            setTimeout(() => setAuthCanResend(true), 30000);
            toast.success('OTP sent (MSG91)');
            setAuthBusy(false);
          },
          (error: any) => {
            console.error('MSG91 sendOtp error:', error);
            toast.error('Failed to send OTP');
            setAuthBusy(false);
          }
        );
      } else {
        await api.post('/auth/send-otp', { phone: clean, purpose: 'register' });
        setAuthOtpSent(true);
        setAuthCanResend(false);
        setTimeout(() => setAuthCanResend(true), 30000);
        toast.success('OTP sent');
        setAuthBusy(false);
      }
    } catch {
      toast.error('Failed to send OTP');
      setAuthBusy(false);
    }
  };

  const handleRetryOtp = async () => {
    if (typeof window !== 'undefined' && (window as any).retryOtp) {
      setAuthBusy(true);
      (window as any).retryOtp(
        null,
        // eslint-disable-next-line unused-imports/no-unused-vars
        (data: any) => {
          toast.info('OTP resent');
          setAuthBusy(false);
        },
        // eslint-disable-next-line unused-imports/no-unused-vars
        (error: any) => {
          toast.error('Failed to resend OTP');
          setAuthBusy(false);
        }
      );
    } else {
      handleSendOtp();
    }
  };

  const handleVerifyOtp = async () => {
    if (!authOtp) {
      toast.error('Enter the OTP');
      return;
    }
    const clean = authPhone.replace(/\D/g, '');
    setAuthBusy(true);
    try {
      if (typeof window !== 'undefined' && (window as any).verifyOtp) {
        (window as any).verifyOtp(
          authOtp,
          async (data: any) => {
            // data can be the token string or an object with a token
            const token = typeof data === 'string' ? data : data?.token || data?.jwt_token || data?.message;
            setAuthOtpVerified(true);
            setAuthOtpToken(token || '');
            toast.success('Phone verified');
            setAuthBusy(false);
          },
          (error: any) => {
            console.error('MSG91 verifyOtp error:', error);
            toast.error('Invalid OTP');
            setAuthBusy(false);
          }
        );
      } else {
        await api.post('/auth/verify-otp', { phone: clean, otp: authOtp });
        setAuthOtpVerified(true);
        toast.success('Phone verified');
        setAuthBusy(false);
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Invalid OTP');
      setAuthBusy(false);
    }
  };

  const handleAuthRegister = async () => {
    if (!authPassword || authPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    if (authPassword !== authConfirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    const clean = authPhone.replace(/\D/g, '');
    setAuthBusy(true);
    try {
      const payload: any = { phone: clean, password: authPassword, role: 'customer' };
      if (authOtpToken) payload.msg91Token = authOtpToken;
      if (!authOtpToken) payload.otp = authOtp;

      const res = await api.post('/auth/register', payload);
      const { token, refreshToken, sessionId, user: userData } = res.data;
      await loginWithTokens({ token, refreshToken, sessionId, user: userData });
      toast.success('Account created');
      fetchCart();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Registration failed');
    }
    setAuthBusy(false);
  };

  // ═══════════════════════════════════════════════════════════════════
  //  PLACE ORDER (requires login)
  // ═══════════════════════════════════════════════════════════════════
  const handleStartCheckout = () => {
    const inStock = cart?.items?.filter((item: any) => !item.outOfStock) || [];
    if (inStock.length === 0) {
      // For guests, cart?.items may not be populated yet — open checkout modal anyway
      // so they can sign in and see their cart
      if (!user) {
        setShowCheckout(true);
        setCheckoutStep(1);
        return;
      }
      toast.error('No in-stock items in your cart to checkout');
      return;
    }
    try {
      trackEcommerceEvent('begin_checkout', {
        value: inStock.reduce((s: number, i: any) => s + (i.price || 0) * i.quantity, 0),
        currency: 'INR',
        items: inStock
          .filter((item: any) => item.product)
          .map((item: any) => ({
            item_id: item.product?._id || item.product,
            item_name: item.product?.name || 'Product',
            price: item.price,
            item_brand: item.product?.brand,
            item_category: item.product?.category,
            quantity: item.quantity,
          })),
      });
    } catch {
      // Analytics failure should never block checkout
    }
    setShowCheckout(true);
    setCheckoutStep(1);
  };

  const handleCheckout = async () => {
    // Must be logged in
    if (!user) {
      setShowCheckout(true);
      return;
    }
    if ((user as any).role === 'valet') {
      toast.error('Valets cannot place orders. Use a customer or business account to checkout.');
      return;
    }

    const inStock = cart?.items?.filter((item: any) => !item.outOfStock) || [];
    if (inStock.length === 0) {
      toast.error('No in-stock items to checkout');
      return;
    }

    // Check serviceability
    if (checkoutData.shippingAddress.zipCode) {
      const pincode = checkoutData.shippingAddress.zipCode;
      if (pincode.length === 6) {
        try {
          const userRole = (user as any)?.role || 'customer';
          const response = await api.get('/delivery-charges/check-serviceability', {
            params: { pincode, userRole },
          });
          if (!response.data.isServiceable) {
            toast.error('Your pincode is not serviceable.');
            return;
          }
        } catch {
          toast.error('Failed to verify pincode serviceability.');
          return;
        }
      } else {
        toast.error('Please enter a valid 6-digit pincode');
        return;
      }
    } else {
      toast.error('Please enter your pincode');
      return;
    }

    // UPI payment screen
    if (checkoutData.paymentMethod === 'upi' && !checkoutData.upiPaymentScreenshot) {
      setShowUpiPayment(true);
      return;
    }

    try {
      const orderData: any = {
        shippingAddress: checkoutData.shippingAddress,
        billingAddress: checkoutData.billingAddress || checkoutData.shippingAddress,
        paymentMethod: checkoutData.paymentMethod,
        notes: checkoutData.notes || null,
        printedBill: checkoutData.printedBill || false,
        referralCode: appliedReferralCode || null,
        couponCode: appliedCoupon?.code || null,
        items: inStock.map((i: any) => ({
          productId: i.product?._id || i.product || i._id,
          quantity: i.quantity,
          sellAsCase: !!i.sellAsCase,
        })),
        // Delivery slot fields
        isUrgentDelivery: selectedSlot?.isUrgent ?? false,
        deliverySlotId: selectedSlot?.slotId ?? null,
        deliverySlotConfigId: selectedSlot?.configId ?? null,
        deliverySlotDate: selectedSlot ? selectedSlotDate : null,
      };
      if (checkoutData.paymentMethod === 'upi') {
        orderData.upiPaymentScreenshot = checkoutData.upiPaymentScreenshot || null;
      }

      const response = await api.post('/orders', orderData);
      // eslint-disable-next-line unused-imports/no-unused-vars
      const { isFirstOrder, order: newOrder } = response.data;

      trackEcommerceEvent('purchase', {
        transaction_id: newOrder._id || Date.now().toString(),
        value: finalTotalAmount,
        currency: 'INR',
        items: inStock.map((item: any) => ({
          item_id: item.product._id || item.product,
          item_name: item.product.name,
          price: item.price,
          item_brand: item.product.brand,
          item_category: item.product.category,
          quantity: item.quantity,
        })),
      });

      // Track ad conversion if attribution is present
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('sj_attribution');
        if (stored) {
          try {
            const attr = JSON.parse(stored);
            if (attr.adId) {
              const platform = attr.fbclid ? 'meta' : (attr.gclid ? 'google' : (attr.utmSource || 'unknown'));
              trackWebAdConversion(attr.adId, platform, finalTotalAmount);
            }
          // eslint-disable-next-line unused-imports/no-unused-vars
          } catch (e) {}
        }
      }

      // Reset slot state
      setSelectedDeliveryType('standard');
      setSelectedSlot(null);
      setSelectedSlotDate('');
      setAvailableSlots([]);
      toast.success('Order placed successfully!');
      router.push('/customer/orders');
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.detail || error.response?.data?.message || 'Failed to place order';
      toast.error(errorMsg);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () =>
        setCheckoutData({ ...checkoutData, upiPaymentScreenshot: reader.result as string });
      reader.readAsDataURL(file);
    }
  };

  // ─── Role label ───────────────────────────────────────────────────
  // eslint-disable-next-line unused-imports/no-unused-vars
  const roleLabel = (user as any)?.role === 'wholesaler' ? 'Business Customer' : 'Retail Customer';
  const segmentPrefix = (user as any)?.role === 'wholesaler' ? 'wholesale' : 'retail';
  const isCodEnabled = enabledFlags.length === 0 || enabledFlags.includes(`${segmentPrefix}_enable_cod`);
  const isUpiEnabled = enabledFlags.length === 0 || enabledFlags.includes(`${segmentPrefix}_enable_upi`);
  const isCreditEnabled = (user as any)?.role === 'wholesaler' && (enabledFlags.length === 0 || enabledFlags.includes('wholesale_enable_credit'));
  const hasNoPaymentMethods = !isCodEnabled && !isUpiEnabled && !isCreditEnabled;

  return (
    <div
      className={`w-full max-w-full overflow-x-hidden ${isMobile ? 'min-h-screen bg-neutral-50 pb-32' : 'pb-20'}`}
    >
      {/* Desktop Header – hidden on mobile via CSS (avoids SSR-hydration flash) */}
      <div className="hidden md:block">
        <Header />
      </div>

      {/* Mobile top-spacer so content never sits under the sticky global MobileHeader */}
      <div className="block h-0 md:hidden" />

      <div className={isMobile ? '' : 'container mx-auto px-4 py-8'}>


        {loading ? (
          <div className="flex min-h-[60vh] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-[#1a4d33]" />
          </div>
        ) : cartError ? (
          /* ── Error state: network/server failure ───────────────── */
          <div
            className={`flex flex-col items-center justify-center px-8 py-12 ${isMobile ? 'bg-neutral-50' : ''}`}
          >
            {isMobile ? (
              <>
                <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-50 text-red-400">
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-neutral-900">Could not load your cart</h2>
                <p className="mb-6 mt-2 text-center text-neutral-500">Something went wrong. Please try again.</p>
                <button
                  onClick={fetchCart}
                  className="rounded-full px-8 py-3 font-medium text-white"
                  style={{ backgroundColor: MOBILE_ACCENT }}
                >
                  Retry
                </button>
              </>
            ) : (
              <div className="w-full max-w-2xl rounded-lg bg-white p-8 text-center shadow">
                <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-red-50 text-red-400">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                </div>
                <h2 className="mb-4 text-2xl font-bold">Could Not Load Cart</h2>
                <p className="mb-8 text-gray-500">
                  There was a problem fetching your cart. Please check your connection and try again.
                </p>
                <button
                  onClick={fetchCart}
                  className="inline-block rounded-lg px-8 py-3 font-semibold text-white transition-colors"
                  style={{ backgroundColor: theme.primary }}
                >
                  Retry
                </button>
              </div>
            )}
          </div>
        ) : !cart || !cart.items || cart.items.length === 0 ? (
          /* ── Empty cart state ──────────────────────────────────── */
          <div
            className={`flex flex-col items-center justify-center px-8 py-12 ${isMobile ? 'bg-neutral-50' : ''}`}
          >
            {isMobile ? (
              <>
                <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-neutral-100 text-gray-400">
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
                    <line x1="3" y1="6" x2="21" y2="6" />
                    <path d="M16 10a4 4 0 0 1-8 0" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-neutral-900">Your cart is empty</h2>
                <p className="mb-6 mt-2 text-center text-neutral-500">Add items to get started</p>
                <Link
                  href="/customer"
                  className="rounded-full px-8 py-3 font-medium text-white"
                  style={{ backgroundColor: MOBILE_ACCENT }}
                >
                  Browse Products
                </Link>
              </>
            ) : (
              <div className="w-full max-w-2xl rounded-lg bg-white p-8 text-center shadow">
                <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-gray-100 text-gray-400">
                  <svg
                    width="48"
                    height="48"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
                    <line x1="3" y1="6" x2="21" y2="6" />
                    <path d="M16 10a4 4 0 0 1-8 0" />
                  </svg>
                </div>
                <h2 className="mb-4 text-2xl font-bold">Your Cart is Empty</h2>
                <p className="mb-8 text-gray-500">
                  Looks like you haven&apos;t added anything to your cart yet.
                </p>
                <Link
                  href="/customer"
                  className="inline-block rounded-lg px-8 py-3 font-semibold text-white transition-colors"
                  style={{ backgroundColor: theme.primary }}
                >
                  Continue Shopping
                </Link>
              </div>
            )}
          </div>
        ) : (
          /* Cart active state */
          <>
            {/* Desktop: card list */}
            {!isMobile && (
              <div className="flex flex-col gap-8 lg:flex-row">
                <div className="flex-1 space-y-6">
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900">Shopping Cart</h2>
                    <span className="font-medium text-gray-500">{cart.items.length} items</span>
                  </div>

                  <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
                    <div className="space-y-6 p-6">
                      {cart.items.map((item: any) => {
                        const itemId = user ? item._id : item.product?._id || item._id;
                        const qty = item.quantity || 1;
                        const price = item.price ?? item.product?.price ?? 0;
                        const img = item.product?.displayImage || item.product?.images?.[0];
                        const originalPrice = item.product?.mrp || item.price || 0;
                        const discountPercent =
                          originalPrice > price
                            ? Math.round(((originalPrice - price) / originalPrice) * 100)
                            : 0;

                        return (
                          <div
                            key={itemId}
                            className={`group relative flex gap-6 border-b border-gray-100 py-6 first:pt-0 last:border-0 last:pb-0 ${item.outOfStock ? 'opacity-60 bg-gray-50/50 p-4 rounded-xl' : ''}`}
                          >
                            <Link
                              href={`/customer/product/${item.product?._id}`}
                              className="block h-32 w-32 shrink-0 overflow-hidden rounded-xl border border-gray-100 bg-gray-50 transition-all group-hover:border-gray-200"
                            >
                              {img ? (
                                <img
                                  src={getImageUrl(img) || ''}
                                  alt=""
                                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                                />
                              ) : (
                                <div className="flex h-full w-full items-center justify-center text-gray-300">
                                  <svg
                                    width="32"
                                    height="32"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="1.5"
                                  >
                                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                                    <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                                    <line x1="12" y1="22.08" x2="12" y2="12" />
                                  </svg>
                                </div>
                              )}
                            </Link>

                            <div className="flex flex-1 flex-col justify-between">
                              <div className="flex items-start justify-between">
                                <div className="pr-4">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <Link
                                      href={`/customer/product/${item.product?._id}`}
                                      className="line-clamp-2 text-lg font-bold text-gray-900 transition-colors hover:text-indigo-600"
                                    >
                                      {item.product?.name}
                                    </Link>
                                    {item.outOfStock && (
                                      <span className="inline-flex items-center rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-semibold text-rose-800 animate-pulse shrink-0">
                                        Out of Stock
                                      </span>
                                    )}
                                    {item.bundleName && (
                                      <span className="inline-flex items-center gap-1 rounded-full bg-violet-100 px-2.5 py-0.5 text-xs font-semibold text-violet-700 shrink-0">
                                        🎁 {item.bundleName}
                                      </span>
                                    )}
                                  </div>
                                  {item.product?.brand && (
                                    <p className="mt-1 text-sm font-medium capitalize text-gray-400">
                                      {item.product.brand}
                                    </p>
                                  )}
                                  {item.variantAttributes &&
                                    Object.keys(item.variantAttributes).length > 0 && (
                                      <div className="mt-3 flex flex-wrap gap-2">
                                        {Object.entries(item.variantAttributes).map(([k, v]) => (
                                          <span
                                            key={k}
                                            className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs font-semibold text-gray-700"
                                          >
                                            <span className="mr-1 text-gray-400">{k}:</span>
                                            {v as string}
                                          </span>
                                        ))}
                                      </div>
                                    )}
                                </div>
                                <div className="pl-4 text-right">
                                  <p className="text-xl font-bold text-gray-900">
                                    ₹{price.toLocaleString()}
                                  </p>
                                  {discountPercent > 0 && (
                                    <div className="mt-1 flex items-center justify-end gap-1.5">
                                      <span className="text-xs font-medium text-gray-400 line-through">
                                        ₹{originalPrice.toLocaleString()}
                                      </span>
                                      <span className="text-xs font-bold text-emerald-600">
                                        {discountPercent}% OFF
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div className="mt-4 flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                  <span className="text-sm font-semibold text-gray-600">
                                    Quantity:
                                  </span>
                                  <div className="flex h-10 w-28 items-center overflow-hidden rounded-lg border border-gray-200 bg-gray-50 transition-colors hover:border-gray-300">
                                    <button
                                      disabled={item.outOfStock}
                                      onClick={() =>
                                        handleQuantityChange(itemId, Math.max(1, qty - 1))
                                      }
                                      className="flex h-full flex-1 items-center justify-center font-bold text-gray-600 transition-colors hover:bg-white hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                      −
                                    </button>
                                    <div className="flex h-full w-10 items-center justify-center border-x border-gray-200 bg-white text-sm font-bold">
                                      {qty}
                                    </div>
                                    <button
                                      disabled={item.outOfStock}
                                      onClick={() => handleQuantityChange(itemId, qty + 1)}
                                      className="flex h-full flex-1 items-center justify-center font-bold text-gray-600 transition-colors hover:bg-white hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                      +
                                    </button>
                                  </div>
                                </div>

                                <div className="flex items-center gap-2">
                                  {item.outOfStock && (
                                    <button
                                      onClick={async () => {
                                        try {
                                          const prodId = item.product?._id || item.product;
                                          if (user?.email) {
                                            await api.post(`/products/${prodId}/notify-me`, {});
                                            toast.success(`We will notify you at ${user.email} once restocked!`);
                                          } else {
                                            const email = window.prompt(`Enter your email to get notified when "${item.product?.name}" is back in stock:`);
                                            if (email === null) return;
                                            const trimmedEmail = email.trim();
                                            if (!trimmedEmail || !trimmedEmail.includes('@')) {
                                              toast.error('Please enter a valid email address.');
                                              return;
                                            }
                                            await api.post(`/products/${prodId}/notify-me`, { email: trimmedEmail });
                                            toast.success(`We will notify you at ${trimmedEmail} once restocked!`);
                                          }
                                        } catch (err: any) {
                                          toast.error(err.response?.data?.detail || 'Failed to register notification');
                                        }
                                      }}
                                      className="flex items-center gap-2 rounded-lg bg-pink-50 px-4 py-2 text-sm font-bold text-[#ff3f6c] transition-colors hover:bg-pink-100"
                                    >
                                      Notify Me
                                    </button>
                                  )}
                                  {user && (
                                    <button
                                      onClick={() => handleMoveToWishlist(itemId, item)}
                                      className="flex items-center gap-2 rounded-lg bg-blue-50 px-4 py-2 text-sm font-bold text-blue-600 transition-colors hover:bg-blue-100"
                                    >
                                      Move to Wishlist
                                    </button>
                                  )}
                                  <button
                                    onClick={() => handleRemoveItem(itemId, item)}
                                    className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold text-gray-400 transition-colors hover:bg-rose-50 hover:text-rose-500"
                                  >
                                    <svg
                                      className="h-4 w-4"
                                      viewBox="0 0 24 24"
                                      fill="none"
                                      stroke="currentColor"
                                      strokeWidth="2"
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                    >
                                      <polyline points="3 6 5 6 21 6"></polyline>
                                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                      <line x1="10" y1="11" x2="10" y2="17"></line>
                                      <line x1="14" y1="11" x2="14" y2="17"></line>
                                    </svg>
                                    Remove
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Subtotal / Order Summary Sidebar */}
                <div className="w-full shrink-0 lg:w-[380px]">
                  <div className="sticky top-24 max-h-[calc(100vh-120px)] overflow-y-auto rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
                    <h3 className="mb-6 border-b border-gray-100 pb-4 text-lg font-bold text-gray-900">
                      Order Summary
                    </h3>

                    <div className="mb-6 rounded-xl border border-blue-100 bg-blue-50/60 p-4 text-xs font-medium leading-relaxed text-blue-700">
                      <div className="flex gap-2">
                        <svg className="h-4 w-4 shrink-0 text-blue-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="16" x2="12" y2="12" />
                          <line x1="12" y1="8" x2="12.01" y2="8" />
                        </svg>
                        <span>
                          Final prices will be calculated on Checkout
                        </span>
                      </div>
                    </div>

                    <div className="mb-6 space-y-4 text-sm font-medium">
                      <div className="flex justify-between text-gray-600">
                        <span>Price ({cart.items.length} items)</span>
                        <span>
                          ₹
                          {cart.items
                            .reduce(
                              (s: number, i: any) =>
                                s +
                                (i.product?.mrp || i.product?.price || i.price || 0) * i.quantity,
                              0
                            )
                            .toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between text-emerald-600">
                        <span>Discount</span>
                        <span>
                          -₹
                          {cart.items
                            .reduce(
                              (s: number, i: any) =>
                                s +
                                ((i.product?.mrp || i.product?.price || i.price || 0) -
                                  (i.price || 0)) *
                                  i.quantity,
                              0
                            )
                            .toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between text-gray-600">
                        <span>Delivery Charges</span>
                        <span className="text-xs text-emerald-600">Calculated at checkout</span>
                      </div>
                    </div>

                    <div className="mb-8 flex h-10 items-center justify-between border-t border-gray-100 pt-4">
                      <span className="text-lg font-bold text-gray-900">Total Amount</span>
                      <span className="text-2xl font-black text-gray-900">
                        ₹
                        {cart.subtotal?.toLocaleString() ||
                          cart.items
                            .reduce((s: number, i: any) => s + i.price * i.quantity, 0)
                            .toLocaleString()}
                      </span>
                    </div>

                    {user && ((user as any).effectiveRole === 'wholesaler' || user.role === 'wholesaler') && duesInfo?.hasOverdueBills ? (
                      <button
                        onClick={() => setShowDuesModal(true)}
                        className="flex w-full items-center justify-center gap-2 rounded-xl p-4 text-lg font-bold text-white shadow-md transition-all hover:-translate-y-0.5"
                        style={{
                          background: 'linear-gradient(135deg, #d63031, #ff7675)',
                          boxShadow: '0 4px 12px rgba(214, 48, 49, 0.3)',
                        }}
                      >
                        🔴 Clear Dues to Order
                      </button>
                    ) : (
                      <button
                        onClick={handleStartCheckout}
                        className="flex w-full items-center justify-center gap-2 rounded-xl bg-gray-900 p-4 text-lg font-bold text-white shadow-md transition-all hover:-translate-y-0.5 hover:bg-gray-800 hover:shadow-lg"
                      >
                        Proceed to Checkout
                        <svg
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <line x1="5" y1="12" x2="19" y2="12"></line>
                          <polyline points="12 5 19 12 12 19"></polyline>
                        </svg>
                      </button>
                    )}

                    {/* Trust indicators */}
                    <div className="mt-6 flex items-center justify-center gap-4 text-xs font-semibold text-gray-400">
                      <div className="flex items-center gap-1.5">
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                          ></path>
                        </svg>
                        Secure payments
                      </div>
                      <div className="flex items-center gap-1.5">
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
                          ></path>
                        </svg>
                        Buyer protection
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Mobile: card list (match app) - contained to avoid horizontal scroll */}
            {isMobile && (
              <div className="min-w-0 space-y-3 px-4 py-4">
                <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-3 text-[11px] font-medium leading-normal text-blue-700 flex gap-2">
                  <svg className="h-4 w-4 shrink-0 text-blue-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="16" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12.01" y2="8" />
                  </svg>
                  <span>
                    Final prices will be calculated on Checkout
                  </span>
                </div>
                {cart.items.map((item: any) => {
                  const itemId = user ? item._id : item.product?._id || item._id;
                  const qty = item.quantity || 1;
                  const price = item.price ?? item.product?.price ?? 0;
                  const img = item.product?.displayImage || item.product?.images?.[0];
                  return (
                    <div
                      key={item._id}
                      className={`rounded-2xl border border-neutral-100 bg-white p-4 shadow-sm ${item.outOfStock ? 'opacity-60 bg-gray-50/50' : ''}`}
                    >
                      <div className="flex flex-row gap-4">
                        <div className="h-20 w-20 shrink-0 overflow-hidden rounded-xl bg-neutral-100">
                          {img ? (
                            <img
                              src={getImageUrl(img) || ''}
                              alt=""
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center text-neutral-300">
                              <svg
                                width="24"
                                height="24"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="1.5"
                              >
                                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                                <line x1="12" y1="22.08" x2="12" y2="12" />
                              </svg>
                            </div>
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className="line-clamp-2 text-sm font-medium text-neutral-900">
                              {item.product?.name}
                            </p>
                            {item.outOfStock && (
                              <span className="inline-flex items-center rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-semibold text-rose-800 animate-pulse shrink-0">
                                Out of Stock
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-base font-semibold text-neutral-900">₹{price}</p>
                           {/* Quantity row */}
                           <div className="mt-3 flex items-center gap-2">
                             <button
                               type="button"
                               disabled={item.outOfStock}
                               onClick={() => handleQuantityChange(itemId, Math.max(1, qty - 1))}
                               className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-100 font-medium text-neutral-900 disabled:opacity-50"
                             >
                               -
                             </button>
                             <span className="mx-2 font-medium text-neutral-900">{qty}</span>
                             <button
                               type="button"
                               disabled={item.outOfStock}
                               onClick={() => handleQuantityChange(itemId, qty + 1)}
                               className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-100 font-medium text-neutral-900 disabled:opacity-50"
                             >
                               +
                             </button>
                           </div>
                           {/* Action buttons row */}
                           <div className="mt-2 flex items-center gap-2 flex-wrap">
                             {item.outOfStock && (
                               <button
                                 type="button"
                                 onClick={async () => {
                                   try {
                                     const prodId = item.product?._id || item.product;
                                     if (user?.email) {
                                       await api.post(`/products/${prodId}/notify-me`, {});
                                       toast.success(`We will notify you at ${user.email} once restocked!`);
                                     } else {
                                       const email = window.prompt(`Enter your email to get notified when "${item.product?.name}" is back in stock:`);
                                       if (email === null) return;
                                       const trimmedEmail = email.trim();
                                       if (!trimmedEmail || !trimmedEmail.includes('@')) {
                                         toast.error('Please enter a valid email address.');
                                         return;
                                       }
                                       await api.post(`/products/${prodId}/notify-me`, { email: trimmedEmail });
                                       toast.success(`We will notify you at ${trimmedEmail} once restocked!`);
                                     }
                                   } catch (err: any) {
                                     toast.error(err.response?.data?.detail || 'Failed to register notification');
                                   }
                                 }}
                                 className="rounded-lg bg-pink-50 px-2.5 py-1 text-xs font-bold text-[#ff3f6c] transition-colors hover:bg-pink-100"
                               >
                                 Notify
                               </button>
                             )}
                             <button
                               type="button"
                               onClick={() => handleMoveToWishlist(itemId, item)}
                               className="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 transition-colors hover:bg-blue-100 whitespace-nowrap flex items-center gap-1"
                             >
                               <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" /></svg>
                               Wishlist
                             </button>
                             <button
                               type="button"
                               onClick={() => handleRemoveItem(itemId, item)}
                               className="ml-auto flex h-8 w-8 items-center justify-center text-gray-400 hover:text-rose-500"
                               aria-label="Remove"
                             >
                               <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                 <polyline points="3 6 5 6 21 6" />
                                 <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                 <line x1="10" y1="11" x2="10" y2="17" />
                                 <line x1="14" y1="11" x2="14" y2="17" />
                               </svg>
                             </button>
                           </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* Enhancements: Gift Wrap, Wishlist, Impulse Buy - show regardless of cart content if not loading */}
        {!loading && (
          <div className="mb-12 mt-12 space-y-12">
            {!isMobile && (
              <>
                {giftWrapItems.length > 0 && (
                  <div className="rounded-2xl border border-pink-100 bg-gradient-to-r from-pink-50 to-red-50 p-8 shadow-sm">
                    <div className="mb-6 flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-500 text-xl text-white">
                        🎁
                      </div>
                      <h3 className="text-2xl font-bold text-gray-800">Make it a Gift</h3>
                    </div>
                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                      {giftWrapItems.map((item) => (
                        <div
                          key={item._id}
                          className="flex items-center gap-4 rounded-xl border border-white bg-white p-4 shadow-sm transition-all hover:border-pink-200"
                        >
                          <button
                            type="button"
                            className="h-20 w-20 shrink-0 cursor-pointer overflow-hidden rounded-lg border border-gray-100 bg-gray-50 text-left"
                            onClick={() =>
                              handleRecommendationProductClick(item._id, item.name, 'gift_wrap')
                            }
                          >
                            <img
                              src={getImageUrl(item.images?.[0]) || item.images?.[0]}
                              alt={item.name}
                              className="h-full w-full object-cover"
                            />
                          </button>
                          <div className="min-w-0 flex-1">
                            <button
                              type="button"
                              className="block w-full truncate text-left font-bold text-gray-800 hover:text-pink-600"
                              onClick={() =>
                                handleRecommendationProductClick(item._id, item.name, 'gift_wrap')
                              }
                            >
                              {item.name}
                            </button>
                            <p className="mt-1 font-bold text-pink-600">₹{item.mrp}</p>
                            <button
                              onClick={() =>
                                handleAddToCartFromRecommendation(item._id, item, 'gift_wrap')
                              }
                              className="mt-2 text-xs font-bold uppercase tracking-wider text-pink-600 underline hover:text-pink-700"
                            >
                              Add to cart
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
                  {/* Wishlist Section */}
                  {wishlistItems.length > 0 && (
                    <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
                      <div className="mb-6 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500 text-white">
                            ❤️
                          </div>
                          <h3 className="text-xl font-bold text-gray-800">From Your Wishlist</h3>
                        </div>
                        {user && (
                          <Link
                            href="/customer/wishlist"
                            className="text-sm font-semibold text-blue-600 transition-all hover:underline"
                          >
                            View All
                          </Link>
                        )}
                      </div>
                      <div className="space-y-4">
                        {wishlistItems.slice(0, 3).map((item) => (
                          <div
                            key={item.product?._id}
                            className="flex items-center gap-4 rounded-xl border border-transparent p-3 transition-colors hover:border-gray-100 hover:bg-gray-50"
                          >
                            <button
                              type="button"
                              className="h-16 w-16 shrink-0 cursor-pointer overflow-hidden rounded-lg bg-gray-50 text-left"
                              onClick={() =>
                                item.product?._id &&
                                handleRecommendationProductClick(
                                  item.product._id,
                                  item.product?.name,
                                  'from_wishlist'
                                )
                              }
                            >
                              <img
                                src={item.product?.images?.[0]}
                                alt={item.product?.name}
                                className="h-full w-full object-cover"
                              />
                            </button>
                            <div className="min-w-0 flex-1">
                              <button
                                type="button"
                                className="block w-full truncate text-left font-semibold text-gray-800 hover:text-blue-600"
                                onClick={() =>
                                  item.product?._id &&
                                  handleRecommendationProductClick(
                                    item.product._id,
                                    item.product?.name,
                                    'from_wishlist'
                                  )
                                }
                              >
                                {item.product?.name}
                              </button>
                              <p className="font-bold text-gray-900">₹{item.product?.price}</p>
                            </div>
                            <button
                              onClick={() =>
                                item.product?._id &&
                                handleAddToCartFromRecommendation(
                                  item.product._id,
                                  item.product,
                                  'from_wishlist'
                                )
                              }
                              className="rounded-lg bg-blue-50 p-2 text-blue-600 transition-colors hover:bg-blue-100"
                              title="Add to cart"
                            >
                              <svg
                                width="20"
                                height="20"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              >
                                <circle cx="9" cy="21" r="1" />
                                <circle cx="20" cy="21" r="1" />
                                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                              </svg>
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Quick Picks (Impulse Buy collection from super admin) */}
                  {impulseBuyItems.length > 0 && (
                    <div
                      ref={quickPicksSectionRef}
                      className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-blue-50 p-8 shadow-sm"
                    >
                      <div className="mb-6 flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
                          ✨
                        </div>
                        <h3 className="text-xl font-bold text-gray-800">Quick Picks</h3>
                      </div>
                      <div className="space-y-4">
                        {impulseBuyItems.slice(0, 3).map((item) => (
                          <div
                            key={item._id}
                            className="flex items-center gap-4 rounded-xl border border-white/50 bg-white/60 p-3 shadow-sm backdrop-blur-sm transition-all hover:bg-white"
                          >
                            <button
                              type="button"
                              className="h-16 w-16 shrink-0 cursor-pointer overflow-hidden rounded-lg bg-gray-50 text-left"
                              onClick={() =>
                                handleRecommendationProductClick(item._id, item.name, 'quick_picks')
                              }
                            >
                              <img
                                src={item.images?.[0]}
                                alt={item.name}
                                className="h-full w-full object-cover"
                              />
                            </button>
                            <div className="min-w-0 flex-1">
                              <button
                                type="button"
                                className="block w-full truncate text-left font-semibold text-gray-800 hover:text-indigo-600"
                                onClick={() =>
                                  handleRecommendationProductClick(
                                    item._id,
                                    item.name,
                                    'quick_picks'
                                  )
                                }
                              >
                                {item.name}
                              </button>
                              <p className="font-bold text-indigo-600">₹{item.mrp}</p>
                            </div>
                            <button
                              onClick={() =>
                                handleAddToCartFromRecommendation(item._id, item, 'quick_picks')
                              }
                              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-indigo-700"
                            >
                              Add
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {isMobile && (
              <div className="space-y-8 px-4">
                {/* Mobile wishlist and other sections */}
                {giftWrapItems.length > 0 && (
                  <div className="min-w-0">
                    <div className="mb-4 flex items-center gap-2">
                      <span className="text-lg font-bold" style={{ color: MOBILE_ACCENT }}>
                        Make it a Gift
                      </span>
                    </div>
                    <div
                      className="-mx-4 flex min-h-0 gap-4 overflow-x-auto px-4 pb-2"
                      style={{ scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}
                    >
                      {giftWrapItems.map((item) => (
                        <div
                          key={item._id}
                          className="w-40 shrink-0 rounded-2xl border border-neutral-100 bg-white p-3 shadow-sm"
                        >
                          <button
                            type="button"
                            className="w-full text-left"
                            onClick={() =>
                              handleRecommendationProductClick(item._id, item.name, 'gift_wrap')
                            }
                          >
                            <img
                              src={getImageUrl(item.images?.[0]) || item.images?.[0] || ''}
                              alt={item.name}
                              className="mb-2 h-24 w-full rounded-xl object-cover"
                            />
                            <p className="line-clamp-2 h-8 text-xs font-medium text-neutral-900">
                              {item.name}
                            </p>
                          </button>
                          <div className="mt-2 flex items-center justify-between">
                            <span className="font-bold text-neutral-900">₹{item.mrp}</span>
                            <button
                              type="button"
                              onClick={() =>
                                handleAddToCartFromRecommendation(item._id, item, 'gift_wrap')
                              }
                              className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-100 font-medium"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {wishlistItems.length > 0 && (
                  <div className="min-w-0">
                    <div className="mb-4 flex items-center gap-2">
                      <span className="text-lg font-bold text-red-600">From Your Wishlist</span>
                    </div>
                    <div
                      className="-mx-4 flex min-h-0 gap-4 overflow-x-auto px-4 pb-2"
                      style={{ scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}
                    >
                      {wishlistItems.slice(0, 5).map((item) => (
                        <div
                          key={item.product?._id}
                          className="w-40 shrink-0 rounded-2xl border border-neutral-100 bg-white p-3 shadow-sm"
                        >
                          <button
                            type="button"
                            className="w-full text-left"
                            onClick={() =>
                              item.product?._id &&
                              handleRecommendationProductClick(
                                item.product._id,
                                item.product?.name,
                                'from_wishlist'
                              )
                            }
                          >
                            <img
                              src={
                                getImageUrl(item.product?.images?.[0]) ||
                                item.product?.images?.[0] ||
                                ''
                              }
                              alt=""
                              className="mb-2 h-24 w-full rounded-xl object-cover"
                            />
                            <p className="line-clamp-2 h-8 text-xs font-medium text-neutral-900">
                              {item.product?.name}
                            </p>
                          </button>
                          <div className="mt-2 flex items-center justify-between">
                            <span className="font-bold text-neutral-900">
                              ₹{item.product?.price}
                            </span>
                            <button
                              type="button"
                              onClick={() =>
                                item.product?._id &&
                                handleAddToCartFromRecommendation(
                                  item.product._id,
                                  item.product,
                                  'from_wishlist'
                                )
                              }
                              className="flex h-8 w-8 items-center justify-center rounded-lg text-white"
                              style={{ backgroundColor: MOBILE_ACCENT }}
                            >
                              +
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {impulseBuyItems.length > 0 && (
                  <div className="min-w-0">
                    <div className="mb-4 flex items-center gap-2">
                      <span className="text-lg font-bold text-indigo-600">Quick Picks</span>
                    </div>
                    <div
                      className="-mx-4 flex min-h-0 gap-4 overflow-x-auto px-4 pb-2"
                      style={{ scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}
                    >
                      {impulseBuyItems.slice(0, 5).map((item) => (
                        <div
                          key={item._id}
                          className="w-40 shrink-0 rounded-2xl border border-neutral-100 bg-white p-3 shadow-sm"
                        >
                          <button
                            type="button"
                            className="w-full text-left"
                            onClick={() =>
                              handleRecommendationProductClick(item._id, item.name, 'quick_picks')
                            }
                          >
                            <img
                              src={getImageUrl(item.images?.[0]) || item.images?.[0] || ''}
                              alt={item.name}
                              className="mb-2 h-24 w-full rounded-xl object-cover"
                            />
                            <p className="line-clamp-2 h-8 text-xs font-medium text-neutral-900">
                              {item.name}
                            </p>
                          </button>
                          <div className="mt-2 flex items-center justify-between">
                            <span className="font-bold text-neutral-900">₹{item.mrp}</span>
                            <button
                              type="button"
                              onClick={() =>
                                handleAddToCartFromRecommendation(item._id, item, 'quick_picks')
                              }
                              className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 font-medium text-white"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ─── Checkout Modal (Mobile) ──────────────────────────────────────────── */}
        {showCheckout && isMobile && (
          <div
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-50"
            onClick={() => setShowCheckout(false)}
          >
            <div
              className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-4 text-xl font-bold">Checkout</h3>
              {!user && (
                <div className="mb-6 rounded-lg border border-blue-100 bg-blue-50 p-4">
                  <h4 className="mb-3 text-sm font-semibold">Sign in to place your order</h4>
                  <input
                    type="tel"
                    placeholder="10-digit mobile number"
                    value={authPhone}
                    onChange={(e) => {
                      setAuthPhone(e.target.value);
                      setAuthPhoneChecked(false);
                      setAuthOtpSent(false);
                      setAuthOtpVerified(false);
                    }}
                    className="mb-2 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                  {!authPhoneChecked ? (
                    <button
                      onClick={handleCheckPhone}
                      disabled={authBusy}
                      className="w-full rounded bg-gray-900 px-4 py-2 text-sm font-semibold text-white"
                    >
                      {authBusy ? '...' : 'Continue'}
                    </button>
                  ) : authIsExisting ? (
                    <div className="space-y-2">
                      <input
                        type="password"
                        placeholder="Password"
                        value={authPassword}
                        onChange={(e) => setAuthPassword(e.target.value)}
                        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                      />
                      <button
                        onClick={handleAuthLogin}
                        disabled={authBusy}
                        className="w-full rounded bg-gray-900 px-4 py-2 text-sm font-semibold text-white"
                      >
                        {authBusy ? '...' : 'Log In'}
                      </button>
                      <button
                        onClick={() => {
                          window.open('/login', '_blank');
                        }}
                        className="text-xs text-gray-500 underline"
                      >
                        Forgot password?
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Enter OTP"
                          value={authOtp}
                          onChange={(e) => setAuthOtp(e.target.value)}
                          disabled={!authOtpSent || authOtpVerified}
                          className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
                        />
                        {!authOtpSent ? (
                          <button
                            onClick={handleSendOtp}
                            disabled={authBusy}
                            className="rounded bg-purple-600 px-4 py-2 text-sm font-semibold text-white"
                          >
                            {authBusy ? '...' : 'Send OTP'}
                          </button>
                        ) : !authOtpVerified ? (
                          <div className="flex flex-col items-center gap-1">
                            <button
                              onClick={handleVerifyOtp}
                              disabled={authBusy}
                              className="w-full rounded bg-amber-500 px-4 py-2 text-sm font-semibold text-white"
                            >
                              {authBusy ? '...' : 'Verify'}
                            </button>
                            <button
                              onClick={handleRetryOtp}
                              disabled={authBusy || !authCanResend}
                              className="text-[11px] font-medium transition-all disabled:opacity-50"
                              style={{ color: authCanResend ? '#2563eb' : '#9ca3af' }}
                            >
                              {authCanResend ? 'Resend OTP' : 'Wait 30s'}
                            </button>
                          </div>
                        ) : (
                          <span className="rounded bg-green-500 px-4 py-2 text-sm font-semibold text-white">
                            ✓
                          </span>
                        )}
                      </div>
                      {authOtpVerified && (
                        <>
                          <input
                            type="password"
                            placeholder="Set password (min 6 chars)"
                            value={authPassword}
                            onChange={(e) => setAuthPassword(e.target.value)}
                            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                          />
                          <input
                            type="password"
                            placeholder="Confirm password"
                            value={authConfirmPassword}
                            onChange={(e) => setAuthConfirmPassword(e.target.value)}
                            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                          />
                          <button
                            onClick={handleAuthRegister}
                            disabled={authBusy}
                            className="w-full rounded bg-gray-900 px-4 py-2 text-sm font-semibold text-white"
                          >
                            {authBusy ? '...' : 'Create Account & Continue'}
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
              {user && (
                <>
                  <div className="space-y-4">
                    <div className="relative">
                      <label className="mb-1 block flex items-center justify-between">
                        <span>Street Address *</span>
                        {(user as any).savedAddresses &&
                          (user as any).savedAddresses.length > 0 && (
                            <button
                              className="text-xs font-semibold text-blue-600"
                              onClick={() => setShowAddressDropdown(!showAddressDropdown)}
                            >
                              {showAddressDropdown ? 'Close' : 'Select Saved'}
                            </button>
                          )}
                      </label>
                      <input
                        type="text"
                        placeholder="Street address *"
                        value={checkoutData.shippingAddress.street}
                        onChange={(e) =>
                          setCheckoutData({
                            ...checkoutData,
                            shippingAddress: {
                              ...checkoutData.shippingAddress,
                              street: e.target.value,
                            },
                          })
                        }
                        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                        required
                      />
                      <input
                        type="text"
                        placeholder="Address Line 2 (Optional)"
                        value={checkoutData.shippingAddress.addressLine2 || ''}
                        onChange={(e) =>
                          setCheckoutData({
                            ...checkoutData,
                            shippingAddress: {
                              ...checkoutData.shippingAddress,
                              addressLine2: e.target.value,
                            },
                          })
                        }
                        className="mt-2 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                      />
                      <input
                        type="text"
                        placeholder="Landmark (Optional)"
                        value={checkoutData.shippingAddress.landmark || ''}
                        onChange={(e) =>
                          setCheckoutData({
                            ...checkoutData,
                            shippingAddress: {
                              ...checkoutData.shippingAddress,
                              landmark: e.target.value,
                            },
                          })
                        }
                        className="mt-2 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                      />
                      {showAddressDropdown && (user as any).savedAddresses && (
                        <div className="absolute left-0 right-0 z-[60] mt-1 max-h-48 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-xl">
                          {(user as any).savedAddresses.map((addr: any, idx: number) => (
                            <div
                              key={idx}
                              className="cursor-pointer border-b border-gray-100 p-3 text-xs hover:bg-gray-50"
                              onClick={() => selectSavedAddress(addr)}
                            >
                              <p className="font-bold">{addr.street}</p>
                              <p className="text-gray-500">
                                {addr.city}, {addr.state} - {addr.zipCode}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <div>
                      <label className="mb-1 block">State *</label>
                      <SearchableSelect
                        options={checkoutStates}
                        value={checkoutData.shippingAddress.state}
                        onChange={(val) => {
                          setCheckoutData({
                            ...checkoutData,
                            shippingAddress: {
                              ...checkoutData.shippingAddress,
                              state: val,
                              district: '',
                            },
                          });
                          fetchCheckoutDistricts(val, setCheckoutDistricts);
                        }}
                        placeholder="Select State"
                        required
                      />
                    </div>
                    <div>
                      <label className="mb-1 block">District *</label>
                      <SearchableSelect
                        options={checkoutDistricts}
                        value={checkoutData.shippingAddress.district || ''}
                        onChange={(val) =>
                          setCheckoutData({
                            ...checkoutData,
                            shippingAddress: { ...checkoutData.shippingAddress, district: val },
                          })
                        }
                        placeholder="Select District"
                        disabled={!checkoutData.shippingAddress.state}
                        required
                      />
                    </div>
                    <div>
                      <label className="mb-1 block">City *</label>
                      <input
                        type="text"
                        value={checkoutData.shippingAddress.city}
                        onChange={(e) =>
                          setCheckoutData({
                            ...checkoutData,
                            shippingAddress: {
                              ...checkoutData.shippingAddress,
                              city: e.target.value,
                            },
                          })
                        }
                        className="w-full rounded border border-gray-300 px-3 py-2"
                        required
                      />
                    </div>
                    <div>
                      <label className="mb-1 block">Pin Code</label>
                      <input
                        type="text"
                        value={checkoutData.shippingAddress.zipCode}
                        onChange={(e) => {
                          const v = e.target.value;
                          setCheckoutData({
                            ...checkoutData,
                            shippingAddress: { ...checkoutData.shippingAddress, zipCode: v },
                          });
                          if (v.length === 6) checkPincodeServiceability(v);
                          else setPincodeServiceable(null);
                        }}
                        className="w-full rounded border border-gray-300 px-3 py-2"
                        required
                        maxLength={6}
                        pattern="[0-9]{6}"
                      />
                      {checkingServiceability && (
                        <small className="mt-1 block text-xs text-gray-500">
                          Checking serviceability...
                        </small>
                      )}
                      {pincodeServiceable === false && !checkingServiceability && (
                        <div className="mt-2 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-800">
                          <strong>⚠️ Not serviceable.</strong>
                        </div>
                      )}
                      {pincodeServiceable === true && !checkingServiceability && (
                        <small className="mt-1 block text-xs text-green-600">✓ Serviceable</small>
                      )}
                    </div>
                    <div>
                      <label className="mb-1 block">Country</label>
                      <input
                        type="text"
                        value={checkoutData.shippingAddress.country}
                        onChange={(e) =>
                          setCheckoutData({
                            ...checkoutData,
                            shippingAddress: {
                              ...checkoutData.shippingAddress,
                              country: e.target.value,
                            },
                          })
                        }
                        className="w-full rounded border border-gray-300 px-3 py-2"
                        required
                      />
                    </div>

                    {/* ── Delivery Option Selector ─────────────────────────── */}
                    {pincodeServiceable === true && deliveryOptions && (
                      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
                        <p className="mb-3 text-sm font-semibold text-slate-800">🚚 Delivery Option</p>

                        {/* Standard */}
                        <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 bg-white p-3 mb-2 transition-all hover:border-indigo-300">
                          <input
                            type="radio"
                            name="deliveryType"
                            value="standard"
                            checked={selectedDeliveryType === 'standard'}
                            onChange={() => {
                              setSelectedDeliveryType('standard');
                              setSelectedSlot(null);
                            }}
                            className="accent-indigo-600"
                          />
                          <span className="text-sm font-medium text-slate-700">Standard Delivery (Free)</span>
                        </label>

                        {/* Schedule a slot */}
                        {deliveryOptions.slotBookingAvailable && (
                          <label className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-all ${selectedDeliveryType === 'slot' ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200 bg-white hover:border-indigo-300'}`}>
                            <input
                              type="radio"
                              name="deliveryType"
                              value="slot"
                              checked={selectedDeliveryType === 'slot'}
                              onChange={() => {
                                setSelectedDeliveryType('slot');
                                setSelectedSlot(null);
                                if (deliveryOptions.availableDates.length > 0) {
                                  const firstDate = deliveryOptions.availableDates[0];
                                  setSelectedSlotDate(firstDate);
                                  fetchSlotsForDate(firstDate);
                                }
                              }}
                              className="mt-0.5 accent-indigo-600"
                            />
                            <div className="flex-1">
                              <span className="text-sm font-medium text-slate-700">📅 Schedule a Delivery Slot</span>
                              {selectedDeliveryType === 'slot' && (
                                <div className="mt-3 space-y-3">
                                  {/* Date selector */}
                                  <div>
                                    <label className="mb-1 block text-xs font-medium text-slate-600">Select Date</label>
                                    <select
                                      value={selectedSlotDate}
                                      onChange={(e) => {
                                        setSelectedSlotDate(e.target.value);
                                        fetchSlotsForDate(e.target.value);
                                      }}
                                      className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                                    >
                                      <option value="">Choose a date…</option>
                                      {deliveryOptions.availableDates.map((d) => (
                                        <option key={d} value={d}>{d}</option>
                                      ))}
                                    </select>
                                  </div>

                                  {/* Slot list */}
                                  {selectedSlotDate && (
                                    <div>
                                      <label className="mb-2 block text-xs font-medium text-slate-600">Select Time Slot</label>
                                      {loadingSlots ? (
                                        <p className="text-xs text-slate-400">Loading slots…</p>
                                      ) : availableSlots.length === 0 ? (
                                        <p className="text-xs text-slate-400">No slots available for this date.</p>
                                      ) : (
                                        <div className="space-y-2">
                                          {availableSlots.map((slot) => (
                                            <button
                                              key={slot.slotId}
                                              type="button"
                                              onClick={() => setSelectedSlot(slot)}
                                              className={`flex w-full items-center justify-between rounded-lg border px-3 py-2.5 text-left text-sm transition-all ${
                                                selectedSlot?.slotId === slot.slotId
                                                  ? slot.isUrgent
                                                    ? 'border-amber-500 bg-amber-50 ring-1 ring-amber-400'
                                                    : 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-400'
                                                  : 'border-slate-200 bg-white hover:border-slate-300'
                                              }`}
                                            >
                                              <span className="flex items-center gap-2">
                                                {slot.isUrgent && (
                                                  <span className="rounded-full bg-amber-500 px-2 py-0.5 text-[10px] font-bold text-white">⚡ Urgent</span>
                                                )}
                                                <span className="font-medium">{slot.startTime} – {slot.endTime}</span>
                                              </span>
                                            </button>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  )}

                                  {selectedSlot?.isUrgent && (
                                    <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                                      ⚡ <strong>Urgent delivery surcharge</strong> will apply for this slot.
                                    </p>
                                  )}
                                </div>
                              )}
                            </div>
                          </label>
                        )}
                      </div>
                    )}

                    {referralEligible && (

                      <div className="rounded-lg border border-blue-100 bg-blue-50/50 p-4 mt-2">
                        <label className="mb-2 block text-sm font-semibold text-neutral-800">
                          Have a referral code?
                        </label>
                        {!appliedReferralCode ? (
                          <div className="flex gap-2">
                            <input
                              type="text"
                              placeholder="Enter referral code"
                              value={referralCodeInput}
                              onChange={(e) => setReferralCodeInput(e.target.value)}
                              className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm uppercase"
                            />
                            <button
                              type="button"
                              onClick={handleApplyReferral}
                              disabled={verifyingReferral}
                              className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                            >
                              {verifyingReferral ? '...' : 'Apply'}
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between rounded border border-green-200 bg-green-50 px-3 py-2">
                            <div className="text-sm text-green-800">
                              <span className="font-bold">{appliedReferralCode}</span> applied!
                              {referralDiscountInfo && (
                                <span className="block text-xs font-normal text-green-700 mt-0.5">
                                  Discount:{' '}
                                  {referralDiscountInfo.discountType === 'percentage'
                                    ? `${referralDiscountInfo.discountValue}%`
                                    : `₹${referralDiscountInfo.discountValue}`}
                                  {referralDiscountInfo.referrerName && ` (Referrer: ${referralDiscountInfo.referrerName})`}
                                </span>
                              )}
                            </div>
                            <button
                              type="button"
                              onClick={handleRemoveReferral}
                              className="text-xs font-bold text-red-600 hover:text-red-800"
                            >
                              Remove
                            </button>
                          </div>
                        )}
                        {referralError && (
                          <p className="mt-1 text-xs font-medium text-red-600">{referralError}</p>
                        )}
                      </div>
                    )}

                    {/* Coupon code (mobile web checkout) */}
                    <div className="rounded-lg border border-slate-100 bg-slate-50 mt-2">
                      <label className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-semibold text-neutral-700">
                        <span className="flex items-center gap-1.5">
                          🏷️
                          {appliedCoupon
                            ? <span className="text-emerald-600">&quot;{appliedCoupon.code}&quot; applied — save ₹{appliedCoupon.discount.toFixed(2)}</span>
                            : 'Have a promo code?'}
                        </span>
                      </label>
                      {!appliedCoupon ? (
                        <div className="border-t border-slate-100 px-4 pb-3 pt-2">
                          <div className="flex gap-2">
                            <input
                              type="text"
                              placeholder="Enter coupon code"
                              value={couponInput}
                              onChange={(e) => { setCouponInput(e.target.value); setCouponError(''); }}
                              className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm uppercase"
                            />
                            <button
                              type="button"
                              onClick={handleApplyCoupon}
                              disabled={verifyingCoupon}
                              className="rounded bg-neutral-900 px-4 py-2 text-sm font-semibold text-white hover:bg-neutral-700 disabled:opacity-50"
                            >
                              {verifyingCoupon ? '...' : 'Apply'}
                            </button>
                          </div>
                          {couponError && (
                            <p className="mt-1 text-xs font-medium text-red-600">{couponError}</p>
                          )}
                        </div>
                      ) : (
                        <div className="border-t border-slate-100 px-4 pb-3 pt-2 flex items-center justify-between rounded-b-lg bg-emerald-50">
                          <div className="text-sm text-emerald-800">
                            <span className="font-bold">{appliedCoupon.code}</span> applied!
                            <span className="block text-xs font-normal text-emerald-700 mt-0.5">
                              Saving ₹{appliedCoupon.discount.toFixed(2)} on this order
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={handleRemoveCoupon}
                            className="text-xs font-bold text-red-600 hover:text-red-800"
                          >
                            Remove
                          </button>
                        </div>
                      )}
                    </div>

                    <div>
                      <label className="mb-1 block">Payment Method</label>
                      <select
                        value={checkoutData.paymentMethod}
                        onChange={(e) => {
                          const m = e.target.value;
                          setCheckoutData({
                            ...checkoutData,
                            paymentMethod: m,
                            upiPaymentScreenshot:
                              m !== 'upi' ? null : checkoutData.upiPaymentScreenshot,
                          });
                          if (m === 'upi') setShowUpiPayment(true);
                        }}
                        className="w-full rounded border border-gray-300 px-3 py-2"
                      >
                        <option value="cod">Cash on Delivery</option>
                        <option value="upi">UPI</option>
                        {(user as any)?.role === 'wholesaler' && (
                          <option value="credit">Credit (B2B Only)</option>
                        )}
                      </select>
                    </div>
                    {checkoutData.paymentMethod === 'upi' && checkoutData.upiPaymentScreenshot && (
                      <div>
                        <label className="mb-1 block">Payment Screenshot</label>
                        <div className="mt-1 rounded bg-gray-50 p-2">
                          <img
                            src={checkoutData.upiPaymentScreenshot}
                            alt="Screenshot"
                            className="mb-2 block max-h-[200px] max-w-[200px]"
                          />
                          <button
                            type="button"
                            onClick={() =>
                              setCheckoutData({ ...checkoutData, upiPaymentScreenshot: null })
                            }
                            className="mt-2 rounded bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="mb-4 mt-4">
                    <label className="flex cursor-pointer items-center gap-2">
                      <input
                        type="checkbox"
                        checked={checkoutData.printedBill}
                        onChange={(e) =>
                          setCheckoutData({ ...checkoutData, printedBill: e.target.checked })
                        }
                        className="h-4 w-4 cursor-pointer"
                      />
                      <span>I want a printed bill during delivery</span>
                    </label>
                  </div>
                  {pincodeServiceable === false &&
                    checkoutData.shippingAddress.zipCode &&
                    checkoutData.shippingAddress.zipCode.length === 6 && (
                      <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                        <strong>⚠️ Not serviceable.</strong> Contact support.
                      </div>
                    )}
                  
                  {(appliedReferralCode || appliedCoupon) && (
                    <div className="mt-4 border-t border-neutral-100 pt-3 text-sm text-neutral-600">
                      <div className="flex justify-between py-1">
                        <span>Subtotal</span>
                        <span>₹{subtotalValue.toFixed(2)}</span>
                      </div>
                      {appliedReferralCode && referralDiscountInfo && (
                        <div className="flex justify-between py-1 text-green-600 font-medium">
                          <span>Referral Discount ({appliedReferralCode})</span>
                          <span>-₹{referralDiscountAmount.toFixed(2)}</span>
                        </div>
                      )}
                      {appliedCoupon && (
                        <div className="flex justify-between py-1 text-emerald-600 font-medium">
                          <span>Coupon ({appliedCoupon.code})</span>
                          <span>-₹{appliedCoupon.discount.toFixed(2)}</span>
                        </div>
                      )}
                      <div className="flex justify-between py-1 text-neutral-900 font-bold border-t border-neutral-100 mt-1 pt-1">
                        <span>Total</span>
                        <span>₹{finalTotalAmount.toFixed(2)}</span>
                      </div>
                    </div>
                  )}
                </>
              )}
              <div className="mt-6 flex justify-end gap-4">
                <button
                  onClick={() => setShowCheckout(false)}
                  className="rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
                >
                  Cancel
                </button>
                {user && !isValet && (
                  <button
                    onClick={handleCheckout}
                    disabled={
                      pincodeServiceable === false &&
                      !!checkoutData.shippingAddress.zipCode &&
                      checkoutData.shippingAddress.zipCode.length === 6
                    }
                    className={`rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 ${pincodeServiceable === false && checkoutData.shippingAddress.zipCode?.length === 6 ? 'cursor-not-allowed opacity-50' : ''}`}
                  >
                    Place Order
                  </button>
                )}
                {user && isValet && (
                  <p className="text-sm font-medium text-amber-700">Valets cannot place orders.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ═══ DESKTOP PREMIUM MULTI-STEP CHECKOUT ═══ */}
        {showCheckout && !isMobile && (
          <div className={ck.overlay} onClick={() => setShowCheckout(false)}>
            <div className={ck.panel} onClick={(e) => e.stopPropagation()}>
              {/* Stepper */}
              {user && (
                <div className={ck.stepper}>
                  {['Address', 'Payment', 'Review'].map((label, i) => {
                    const stepNum = i + 1;
                    const isActive = checkoutStep === stepNum;
                    const isCompleted = checkoutStep > stepNum;
                    return (
                      <React.Fragment key={label}>
                        {i > 0 && (
                          <div
                            className={`${ck.stepLine} ${isCompleted || isActive ? ck.done : ''}`}
                          />
                        )}
                        <div
                          className={`${ck.step} ${isActive ? ck.active : ''} ${isCompleted ? ck.completed : ''}`}
                        >
                          <div className={ck.stepCircle}>{isCompleted ? '✓' : stepNum}</div>
                          <span className={ck.stepLabel}>{label}</span>
                        </div>
                      </React.Fragment>
                    );
                  })}
                </div>
              )}

              <div className={ck.body}>
                {/* Auth section for guests */}
                {!user && (
                  <div className={ck.authBox}>
                    <div className={ck.authTitle}>🔐 Sign in to place your order</div>
                    <input
                      type="tel"
                      placeholder="10-digit mobile number"
                      value={authPhone}
                      onChange={(e) => {
                        setAuthPhone(e.target.value);
                        setAuthPhoneChecked(false);
                        setAuthOtpSent(false);
                        setAuthOtpVerified(false);
                      }}
                      className={ck.authInput}
                    />
                    {!authPhoneChecked ? (
                      <button
                        onClick={handleCheckPhone}
                        disabled={authBusy}
                        className={ck.btnPrimary}
                        style={{ width: '100%' }}
                      >
                        {authBusy ? '...' : 'Continue'}
                      </button>
                    ) : authIsExisting ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <input
                          type="password"
                          placeholder="Password"
                          value={authPassword}
                          onChange={(e) => setAuthPassword(e.target.value)}
                          className={ck.authInput}
                        />
                        <button
                          onClick={handleAuthLogin}
                          disabled={authBusy}
                          className={ck.btnPrimary}
                          style={{ width: '100%' }}
                        >
                          {authBusy ? '...' : 'Log In'}
                        </button>
                        <button
                          onClick={() => window.open('/login', '_blank')}
                          style={{
                            fontSize: 12,
                            color: '#64748b',
                            textDecoration: 'underline',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                          }}
                        >
                          Forgot password?
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <div style={{ display: 'flex', gap: 8 }}>
                          <input
                            type="text"
                            placeholder="Enter OTP"
                            value={authOtp}
                            onChange={(e) => setAuthOtp(e.target.value)}
                            disabled={!authOtpSent || authOtpVerified}
                            className={ck.authInput}
                            style={{ flex: 1, marginBottom: 0 }}
                          />
                          {!authOtpSent ? (
                            <button
                              onClick={handleSendOtp}
                              disabled={authBusy}
                              className={ck.btnPrimary}
                            >
                              {authBusy ? '...' : 'Send OTP'}
                            </button>
                          ) : !authOtpVerified ? (
                            <div
                              style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: 4,
                                alignItems: 'center',
                              }}
                            >
                              <button
                                onClick={handleVerifyOtp}
                                disabled={authBusy}
                                className={ck.btnPrimary}
                                style={{ padding: '8px 20px' }}
                              >
                                {authBusy ? '...' : 'Verify'}
                              </button>
                              <button
                                onClick={handleRetryOtp}
                                disabled={authBusy || !authCanResend}
                                style={{
                                  fontSize: 11,
                                  color: authCanResend ? '#2563eb' : '#9ca3af',
                                  background: 'none',
                                  border: 'none',
                                  cursor: authCanResend ? 'pointer' : 'default',
                                  fontWeight: 600,
                                  opacity: authCanResend ? 1 : 0.5,
                                }}
                              >
                                {authCanResend ? 'Resend OTP' : 'Wait 30s'}
                              </button>
                            </div>
                          ) : (
                            <span
                              style={{
                                padding: '12px 16px',
                                background: '#16a34a',
                                color: '#fff',
                                borderRadius: 12,
                                fontWeight: 700,
                              }}
                            >
                              ✓
                            </span>
                          )}
                        </div>
                        {authOtpVerified && (
                          <>
                            <input
                              type="password"
                              placeholder="Set password (min 6 chars)"
                              value={authPassword}
                              onChange={(e) => setAuthPassword(e.target.value)}
                              className={ck.authInput}
                            />
                            <input
                              type="password"
                              placeholder="Confirm password"
                              value={authConfirmPassword}
                              onChange={(e) => setAuthConfirmPassword(e.target.value)}
                              className={ck.authInput}
                            />
                            <button
                              onClick={handleAuthRegister}
                              disabled={authBusy}
                              className={ck.btnPrimary}
                              style={{ width: '100%' }}
                            >
                              {authBusy ? '...' : 'Create Account & Continue'}
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* ── STEP 1: Address ── */}
                {user && checkoutStep === 1 && (
                  <>
                    <h3 className={ck.sectionTitle}>📍 Delivery Address</h3>
                    {/* Saved addresses grid */}
                    <div className={ck.addressGrid}>
                      {((user as any).savedAddresses || []).map((addr: any, idx: number) => {
                        const isSelected =
                          checkoutData.shippingAddress.street === addr.street &&
                          checkoutData.shippingAddress.zipCode === (addr.zipCode || addr.pincode);
                        return (
                          <div
                            key={idx}
                            className={`${ck.addressCard} ${isSelected ? ck.selected : ''}`}
                            onClick={() => selectSavedAddress(addr)}
                          >
                            <div className={ck.addressCardStreet}>{addr.street}</div>
                            {addr.name && (
                              <div
                                className={ck.addressCardMeta}
                                style={{
                                  color: '#0f172a',
                                  fontSize: 13,
                                  fontWeight: 500,
                                  marginTop: 4,
                                }}
                              >
                                {addr.name}
                              </div>
                            )}
                            {addr.addressLine2 && (
                              <div
                                className={ck.addressCardMeta}
                                style={{ color: '#64748b', fontSize: 13, marginTop: 2 }}
                              >
                                {addr.addressLine2}
                              </div>
                            )}
                            {addr.landmark && (
                              <div
                                className={ck.addressCardMeta}
                                style={{ color: '#64748b', fontSize: 13, marginTop: 2 }}
                              >
                                Landmark: {addr.landmark}
                              </div>
                            )}
                            <div className={ck.addressCardMeta} style={{ marginTop: 4 }}>
                              {addr.city}
                              {addr.district ? `, ${addr.district}` : ''}
                              <br />
                              {addr.state} — {addr.zipCode || addr.pincode}
                              <br />
                              {addr.country || 'India'}
                            </div>
                          </div>
                        );
                      })}
                      {/* Add new address card */}
                      <div
                        className={ck.addNewAddressCard}
                        onClick={() => setShowAddressModal(true)}
                      >
                        <div className={ck.addNewIcon}>+</div>
                        <div className={ck.addNewLabel}>Add New Address</div>
                      </div>
                    </div>

                    {/* Current address summary if filled */}
                    {checkoutData.shippingAddress.street && (
                      <div className={ck.summaryBox}>
                        <div
                          style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: '#1a4d33',
                            marginBottom: 8,
                          }}
                        >
                          📦 Delivering to:
                        </div>
                        <div style={{ fontSize: 14, color: '#334155', lineHeight: 1.6 }}>
                          {checkoutData.shippingAddress.name && (
                            <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: 2 }}>
                              {checkoutData.shippingAddress.name}
                            </div>
                          )}
                          {checkoutData.shippingAddress.street}
                          {checkoutData.shippingAddress.addressLine2
                            ? `, ${checkoutData.shippingAddress.addressLine2}`
                            : ''}
                          {checkoutData.shippingAddress.landmark
                            ? `, Landmark: ${checkoutData.shippingAddress.landmark}`
                            : ''}
                          , {checkoutData.shippingAddress.city}
                          <br />
                          {checkoutData.shippingAddress.state} —{' '}
                          {checkoutData.shippingAddress.zipCode}
                        </div>
                        {checkingServiceability && (
                          <div className={ck.serviceableOk} style={{ color: '#64748b' }}>
                            ⏳ Checking serviceability...
                          </div>
                        )}
                        {pincodeServiceable === true && !checkingServiceability && (
                          <div className={ck.serviceableOk}>
                            ✓ Delivery available to this pincode
                          </div>
                        )}
                        {pincodeServiceable === false && !checkingServiceability && (
                          <div className={ck.serviceableBad}>
                            ⚠️ This pincode is not serviceable
                          </div>
                        )}
                      </div>
                    )}

                    <div className={ck.footer}>
                      <button className={ck.btnSecondary} onClick={() => setShowCheckout(false)}>
                        Cancel
                      </button>
                      <button
                        className={ck.btnPrimary}
                        disabled={
                          !checkoutData.shippingAddress.street ||
                          !checkoutData.shippingAddress.zipCode ||
                          !checkoutData.shippingAddress.state ||
                          !checkoutData.shippingAddress.city ||
                          !checkoutData.shippingAddress.district ||
                          pincodeServiceable === false
                        }
                        onClick={() => setCheckoutStep(2)}
                      >
                        Continue to Payment →
                      </button>
                    </div>
                  </>
                )}

                {/* ── STEP 2: Payment ── */}
                {user && checkoutStep === 2 && (
                  <>
                    <h3 className={ck.sectionTitle}>💳 Payment Method</h3>
                    <div className={ck.paymentGrid}>
                      {isCodEnabled && (
                        <div
                          className={`${ck.paymentOption} ${checkoutData.paymentMethod === 'cod' ? ck.selected : ''}`}
                          onClick={() =>
                            setCheckoutData({
                              ...checkoutData,
                              paymentMethod: 'cod',
                              upiPaymentScreenshot: null,
                            })
                          }
                        >
                          <div
                            className={ck.paymentIcon}
                            style={{ background: 'linear-gradient(135deg,#fef3c7,#fde68a)' }}
                          >
                            💵
                          </div>
                          <div className={ck.paymentLabel}>Cash on Delivery</div>
                          <div className={ck.paymentDesc}>Pay when you receive</div>
                        </div>
                      )}
                      {isUpiEnabled && (
                        <div
                          className={`${ck.paymentOption} ${checkoutData.paymentMethod === 'upi' ? ck.selected : ''}`}
                          onClick={() => {
                            setCheckoutData({ ...checkoutData, paymentMethod: 'upi' });
                            setShowUpiPayment(true);
                          }}
                        >
                          <div
                            className={ck.paymentIcon}
                            style={{ background: 'linear-gradient(135deg,#ede9fe,#ddd6fe)' }}
                          >
                            📱
                          </div>
                          <div className={ck.paymentLabel}>UPI Payment</div>
                          <div className={ck.paymentDesc}>GPay, PhonePe, Paytm</div>
                        </div>
                      )}
                      {isCreditEnabled && (
                        <div
                          className={`${ck.paymentOption} ${checkoutData.paymentMethod === 'credit' ? ck.selected : ''}`}
                          onClick={() =>
                            setCheckoutData({
                              ...checkoutData,
                              paymentMethod: 'credit',
                              upiPaymentScreenshot: null,
                            })
                          }
                        >
                          <div
                            className={ck.paymentIcon}
                            style={{ background: 'linear-gradient(135deg,#dbeafe,#bfdbfe)' }}
                          >
                            🏦
                          </div>
                          <div className={ck.paymentLabel}>Credit (B2B)</div>
                          <div className={ck.paymentDesc}>Pay on credit terms</div>
                        </div>
                      )}
                    </div>

                    {checkoutData.paymentMethod === 'upi' && checkoutData.upiPaymentScreenshot && (
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 12,
                          padding: 14,
                          background: '#f0fdf4',
                          borderRadius: 12,
                          border: '1px solid #bbf7d0',
                          marginBottom: 16,
                        }}
                      >
                        <img
                          src={checkoutData.upiPaymentScreenshot}
                          alt="Screenshot"
                          style={{
                            width: 60,
                            height: 60,
                            objectFit: 'cover',
                            borderRadius: 10,
                            border: '1px solid #e2e8f0',
                          }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, color: '#16a34a', fontSize: 14 }}>
                            ✓ Payment screenshot uploaded
                          </div>
                        </div>
                        <button
                          className={ck.btnSecondary}
                          style={{ padding: '8px 14px', fontSize: 12 }}
                          onClick={() =>
                            setCheckoutData({ ...checkoutData, upiPaymentScreenshot: null })
                          }
                        >
                          Remove
                        </button>
                      </div>
                    )}

                    {referralEligible && (
                      <div
                        style={{
                          background: '#f8fafc',
                          border: '1px dashed #cbd5e1',
                          borderRadius: 12,
                          padding: 16,
                          marginBottom: 20,
                        }}
                      >
                        <div
                          style={{
                            fontSize: 13,
                            fontWeight: 700,
                            color: '#1a4d33',
                            marginBottom: 8,
                          }}
                        >
                          🎁 Have a referral code?
                        </div>
                        {!appliedReferralCode ? (
                          <div style={{ display: 'flex', gap: 10 }}>
                            <input
                              type="text"
                              placeholder="Enter referral code"
                              value={referralCodeInput}
                              onChange={(e) => setReferralCodeInput(e.target.value)}
                              style={{
                                flex: 1,
                                padding: '8px 12px',
                                border: '1px solid #cbd5e1',
                                borderRadius: 8,
                                textTransform: 'uppercase',
                                outline: 'none',
                                fontSize: 14,
                              }}
                            />
                            <button
                              type="button"
                              onClick={handleApplyReferral}
                              disabled={verifyingReferral}
                              className={ck.btnPrimary}
                              style={{
                                padding: '8px 20px',
                                fontSize: 14,
                                height: 'auto',
                              }}
                            >
                              {verifyingReferral ? '...' : 'Apply'}
                            </button>
                          </div>
                        ) : (
                          <div
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              background: '#f0fdf4',
                              border: '1px solid #bbf7d0',
                              borderRadius: 8,
                              padding: '10px 14px',
                            }}
                          >
                            <div>
                              <div style={{ fontWeight: 700, color: '#16a34a', fontSize: 14 }}>
                                Code applied: {appliedReferralCode}
                              </div>
                              {referralDiscountInfo && (
                                <div style={{ fontSize: 12, color: '#15803d', marginTop: 2 }}>
                                  Discount:{' '}
                                  {referralDiscountInfo.discountType === 'percentage'
                                    ? `${referralDiscountInfo.discountValue}%`
                                    : `₹${referralDiscountInfo.discountValue}`}
                                  {referralDiscountInfo.referrerName && ` (Referrer: ${referralDiscountInfo.referrerName})`}
                                </div>
                              )}
                            </div>
                            <button
                              type="button"
                              onClick={handleRemoveReferral}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                color: '#dc2626',
                                fontWeight: 700,
                                cursor: 'pointer',
                                fontSize: 12,
                              }}
                            >
                              Remove
                            </button>
                          </div>
                        )}
                        {referralError && (
                          <div style={{ color: '#dc2626', fontSize: 12, fontWeight: 500, marginTop: 6 }}>
                            {referralError}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Coupon / promo code — desktop checkout */}
                    <div
                      style={{
                        border: '1px solid #e2e8f0',
                        borderRadius: 12,
                        overflow: 'hidden',
                        marginBottom: 8,
                      }}
                    >
                      <div
                        style={{
                          fontSize: 13,
                          fontWeight: 700,
                          color: appliedCoupon ? '#059669' : '#334155',
                          padding: '12px 16px',
                          background: appliedCoupon ? '#f0fdf4' : '#f8fafc',
                        }}
                      >
                        🏷️{' '}
                        {appliedCoupon
                          ? `"${appliedCoupon.code}" applied — you save ₹${appliedCoupon.discount.toFixed(2)}`
                          : 'Have a promo code?'}
                      </div>
                      {!appliedCoupon ? (
                        <div
                          style={{
                            borderTop: '1px solid #e2e8f0',
                            padding: '12px 16px',
                            display: 'flex',
                            gap: 10,
                          }}
                        >
                          <input
                            type="text"
                            placeholder="Enter coupon code"
                            value={couponInput}
                            onChange={(e) => { setCouponInput(e.target.value); setCouponError(''); }}
                            style={{
                              flex: 1,
                              padding: '8px 12px',
                              border: '1px solid #cbd5e1',
                              borderRadius: 8,
                              textTransform: 'uppercase',
                              outline: 'none',
                              fontSize: 14,
                            }}
                          />
                          <button
                            type="button"
                            onClick={handleApplyCoupon}
                            disabled={verifyingCoupon}
                            className={ck.btnPrimary}
                            style={{ padding: '8px 20px', fontSize: 14, height: 'auto' }}
                          >
                            {verifyingCoupon ? '...' : 'Apply'}
                          </button>
                        </div>
                      ) : (
                        <div
                          style={{
                            borderTop: '1px solid #bbf7d0',
                            padding: '10px 16px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            background: '#f0fdf4',
                          }}
                        >
                          <div style={{ fontSize: 13, color: '#15803d' }}>
                            Saving ₹{appliedCoupon.discount.toFixed(2)} on this order
                          </div>
                          <button
                            type="button"
                            onClick={handleRemoveCoupon}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: '#dc2626',
                              fontWeight: 700,
                              cursor: 'pointer',
                              fontSize: 12,
                            }}
                          >
                            Remove
                          </button>
                        </div>
                      )}
                      {couponError && (
                        <div
                          style={{
                            color: '#dc2626',
                            fontSize: 12,
                            fontWeight: 500,
                            padding: '4px 16px 10px',
                          }}
                        >
                          {couponError}
                        </div>
                      )}
                    </div>

                    <label className={ck.printedBillRow}>
                      <input
                        type="checkbox"
                        checked={checkoutData.printedBill}
                        onChange={(e) =>
                          setCheckoutData({ ...checkoutData, printedBill: e.target.checked })
                        }
                      />
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#334155' }}>
                        I want a printed bill during delivery
                      </span>
                    </label>

                    <div style={{ marginTop: 16 }}>
                      <label
                        style={{
                          fontSize: 12,
                          fontWeight: 600,
                          color: '#475569',
                          textTransform: 'uppercase',
                          letterSpacing: 0.5,
                          marginBottom: 6,
                          display: 'block',
                        }}
                      >
                        Order Notes (optional)
                      </label>
                      <textarea
                        className={ck.notesInput}
                        value={checkoutData.notes}
                        onChange={(e) =>
                          setCheckoutData({ ...checkoutData, notes: e.target.value })
                        }
                        placeholder="Any special instructions..."
                      />
                    </div>

                    <div className={ck.footer}>
                      <button className={ck.btnSecondary} onClick={() => setCheckoutStep(1)}>
                        ← Back
                      </button>
                      <button
                        className={ck.btnPrimary}
                        disabled={
                          checkoutData.paymentMethod === 'upi' && !checkoutData.upiPaymentScreenshot
                        }
                        onClick={() => setCheckoutStep(3)}
                      >
                        Review Order →
                      </button>
                    </div>
                  </>
                )}

                {/* ── STEP 3: Review ── */}
                {user && checkoutStep === 3 && (
                  <>
                    <h3 className={ck.sectionTitle}>📋 Review Your Order</h3>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: 20,
                        marginBottom: 24,
                      }}
                    >
                      <div className={ck.summaryBox}>
                        <div
                          style={{
                            fontSize: 13,
                            fontWeight: 700,
                            color: '#1a4d33',
                            marginBottom: 10,
                          }}
                        >
                          📍 Delivery Address
                        </div>
                        <div style={{ fontSize: 14, color: '#334155', lineHeight: 1.7 }}>
                          {checkoutData.shippingAddress.street}
                          {checkoutData.shippingAddress.addressLine2
                            ? `, ${checkoutData.shippingAddress.addressLine2}`
                            : ''}
                          {checkoutData.shippingAddress.landmark
                            ? `, Landmark: ${checkoutData.shippingAddress.landmark}`
                            : ''}
                          <br />
                          {checkoutData.shippingAddress.city}, {checkoutData.shippingAddress.state}
                          <br />
                          {checkoutData.shippingAddress.zipCode}
                        </div>
                        <button
                          className={ck.btnOutline}
                          style={{ marginTop: 12, padding: '6px 14px', fontSize: 12 }}
                          onClick={() => setCheckoutStep(1)}
                        >
                          Change
                        </button>
                      </div>
                      <div className={ck.summaryBox}>
                        <div
                          style={{
                            fontSize: 13,
                            fontWeight: 700,
                            color: '#1a4d33',
                            marginBottom: 10,
                          }}
                        >
                          💳 Payment
                        </div>
                        <div style={{ fontSize: 14, color: '#334155' }}>
                          {checkoutData.paymentMethod === 'cod'
                            ? 'Cash on Delivery'
                            : checkoutData.paymentMethod === 'upi'
                              ? 'UPI Payment'
                              : 'Credit (B2B)'}
                        </div>
                        {checkoutData.printedBill && (
                          <div style={{ fontSize: 12, color: '#64748b', marginTop: 6 }}>
                            📄 Printed bill requested
                          </div>
                        )}
                        <button
                          className={ck.btnOutline}
                          style={{ marginTop: 12, padding: '6px 14px', fontSize: 12 }}
                          onClick={() => setCheckoutStep(2)}
                        >
                          Change
                        </button>
                      </div>
                    </div>
                    <div className={ck.summaryBox}>
                      <div
                        style={{
                          fontSize: 13,
                          fontWeight: 700,
                          color: '#1a4d33',
                          marginBottom: 12,
                        }}
                      >
                        🛒 Items ({cart.items?.length || 0})
                      </div>
                      {cart.items?.slice(0, 5).map((item: any) => (
                        <div key={item._id} className={ck.summaryRow}>
                          <span style={{ flex: 1, color: '#334155' }}>
                            {item.product?.name} × {item.quantity}
                          </span>
                          <span style={{ fontWeight: 600, color: '#0f172a' }}>
                            ₹{((item.price || 0) * (item.quantity || 0)).toFixed(2)}
                          </span>
                        </div>
                      ))}
                      {(cart.items?.length || 0) > 5 && (
                        <div style={{ fontSize: 12, color: '#64748b', padding: '6px 0' }}>
                          + {cart.items.length - 5} more items
                        </div>
                      )}
                      {appliedReferralCode && referralDiscountInfo && (
                        <div className={ck.summaryRow} style={{ color: '#16a34a', fontWeight: 600, borderBottom: '1px solid #f1f5f9', paddingBottom: 8, marginBottom: 8 }}>
                          <span>Referral Discount ({appliedReferralCode})</span>
                          <span>-₹{referralDiscountAmount.toFixed(2)}</span>
                        </div>
                      )}
                      {appliedCoupon && (
                        <div className={ck.summaryRow} style={{ color: '#059669', fontWeight: 600, borderBottom: '1px solid #f1f5f9', paddingBottom: 8, marginBottom: 8 }}>
                          <span>Coupon ({appliedCoupon.code})</span>
                          <span>-₹{appliedCoupon.discount.toFixed(2)}</span>
                        </div>
                      )}
                      <div className={ck.summaryRow} style={{ borderTop: '1px solid #f1f5f9', paddingTop: 8, marginTop: 8 }}>
                        <span>Subtotal</span>
                        <span>₹{Math.max(0, subtotalValue - referralDiscountAmount - couponDiscountAmount).toFixed(2)}</span>
                      </div>
                      {deliveryChargeInfo && (
                        <>
                          <div className={ck.summaryRow}>
                            <span>Delivery Charge</span>
                            <span>₹{(deliveryChargeInfo.charge || 0).toFixed(2)}</span>
                          </div>
                          {deliveryChargeInfo.gstAmount > 0 && (
                            <div className={ck.summaryRow}>
                              <span>Delivery GST ({deliveryChargeInfo.gstPercentage}%)</span>
                              <span>₹{deliveryChargeInfo.gstAmount.toFixed(2)}</span>
                            </div>
                          )}
                        </>
                      )}
                      {fetchingDeliveryCharge && (
                        <div className={ck.summaryRow} style={{ color: '#64748b' }}>
                          <span>Calculating Delivery...</span>
                        </div>
                      )}
                      <div className={ck.summaryTotal}>
                        <span>Total</span>
                        <span>₹{finalTotalAmount.toFixed(2)}</span>
                      </div>
                    </div>

                    {isValet && (
                      <p
                        style={{
                          textAlign: 'center',
                          color: '#b45309',
                          fontWeight: 600,
                          padding: '12px 0',
                        }}
                      >
                        Valets cannot place orders. Use a customer or business account.
                      </p>
                    )}

                    <div className={ck.footer}>
                      <button className={ck.btnSecondary} onClick={() => setCheckoutStep(2)}>
                        ← Back
                      </button>
                      {!isValet && (
                        <button
                          className={ck.btnPrimary}
                          onClick={handleCheckout}
                          style={{ fontSize: 16, padding: '14px 36px' }}
                        >
                          🛍️ Place Order
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ─── Dues Modal ─── */}
        {showDuesModal && duesInfo && (
          <div className={ck.addrModalOverlay} onClick={() => setShowDuesModal(false)}>
            <div className={ck.addrModal} onClick={(e) => e.stopPropagation()} style={{ maxWidth: '650px' }}>
              <div className={ck.addrModalHeader}>
                <span className={ck.addrModalTitle} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#b91c1c' }}>
                  ⚠️ Outstanding Credit Dues
                </span>
                <button className={ck.addrModalClose} onClick={() => setShowDuesModal(false)}>
                  ✕
                </button>
              </div>
              <div className={ck.addrModalBody} style={{ padding: '20px' }}>
                <div style={{ marginBottom: '16px', padding: '16px', borderRadius: '12px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
                  {duesInfo.hasOverdueBills ? (
                    <div style={{ fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '6px', color: '#334155' }}>
                      <div>• <strong>Current overdue:</strong> ₹{duesInfo.currentOverdue.toLocaleString('en-IN')}</div>
                      <div>• <strong>Minimum overdue (date has crossed):</strong> ₹{duesInfo.minimumOverdue.toLocaleString('en-IN')}</div>
                      <div style={{ fontWeight: '600', color: '#dc2626' }}>• Pay the minimum amount to continue placing orders.</div>
                    </div>
                  ) : (
                    <div style={{ fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '6px', color: '#334155' }}>
                      <div>• <strong>Current overdue:</strong> ₹{duesInfo.currentOverdue.toLocaleString('en-IN')}</div>
                      <div>• <strong>Minimum overdue (cutoff date is nearest):</strong> ₹{duesInfo.minimumOverdue.toLocaleString('en-IN')}</div>
                      <div>• <strong>Cutoff date:</strong> {new Date(duesInfo.nearestDueDate).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} (before which minimum overdue has to be paid)</div>
                    </div>
                  )}
                </div>

                {/* Bill List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '300px', overflowY: 'auto', marginBottom: '20px' }}>
                  {duesInfo.bills && duesInfo.bills.length > 0 ? (
                    duesInfo.bills.map((bill: any) => (
                      <div
                        key={bill.paymentId}
                        style={{
                          border: '1px solid #e2e8f0',
                          borderRadius: '12px',
                          padding: '16px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          backgroundColor: bill.overdue ? '#fef2f2' : '#f8fafc',
                          borderColor: bill.overdue ? '#fca5a5' : '#cbd5e1',
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 'bold', color: '#1e293b', fontSize: '15px' }}>
                            Order: #{bill.orderNumber}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                            Ordered: {new Date(bill.orderDate).toLocaleDateString('en-IN')}
                          </div>
                          <div
                            style={{
                              display: 'inline-block',
                              fontSize: '12px',
                              fontWeight: '600',
                              color: bill.overdue ? '#dc2626' : '#2563eb',
                              marginTop: '8px',
                              backgroundColor: bill.overdue ? '#fee2e2' : '#dbeafe',
                              padding: '2px 8px',
                              borderRadius: '9999px',
                            }}
                          >
                            {bill.timeRemaining}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a' }}>
                            ₹{bill.amountRemaining.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </div>
                          <button
                            onClick={() => {
                              setSelectedBillForSettle(bill);
                              setDuesSettleAmount(bill.amountRemaining.toString());
                              setDuesSettleImage(null);
                            }}
                            style={{
                              marginTop: '8px',
                              padding: '6px 14px',
                              borderRadius: '8px',
                              backgroundColor: '#1e293b',
                              color: '#fff',
                              fontSize: '12px',
                              fontWeight: 'bold',
                              border: 'none',
                              cursor: 'pointer',
                            }}
                          >
                            Settle
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                      No due bills found!
                    </div>
                  )}
                </div>

                {/* Settle Form */}
                {selectedBillForSettle && (
                  <div style={{ borderTop: '2px dashed #e2e8f0', paddingTop: '20px', animation: 'fadeIn 0.2s' }}>
                    <h4 style={{ fontWeight: 'bold', fontSize: '15px', marginBottom: '12px', color: '#0f172a' }}>
                      Submit Settlement for Order #{selectedBillForSettle.orderNumber}
                    </h4>
                    
                    {/* Bank / UPI info */}
                    {upiDetails && (
                      <div style={{ backgroundColor: '#f0fdf4', padding: '12px', borderRadius: '8px', border: '1px solid #bbf7d0', marginBottom: '16px', fontSize: '13px' }}>
                        <div style={{ fontWeight: 'bold', color: '#166534' }}>UPI Account Details:</div>
                        <div style={{ color: '#14532d', marginTop: '4px' }}>
                          ID: <strong>{upiDetails.upiId}</strong> <br />
                          Name: <strong>{upiDetails.name}</strong>
                        </div>
                      </div>
                    )}

                    <form onSubmit={handleSettleDueBill}>
                      <div className={ck.formGroup}>
                        <label className={ck.formLabel}>Amount to Settle (₹) *</label>
                        <input
                          type="number"
                          className={ck.formInput}
                          value={duesSettleAmount}
                          onChange={(e) => setDuesSettleAmount(e.target.value)}
                          max={selectedBillForSettle.amountRemaining}
                          required
                        />
                      </div>
                      <div className={ck.formGroup}>
                        <label className={ck.formLabel}>Upload Payment Screenshot *</label>
                        <input
                          type="file"
                          accept="image/*"
                          className={ck.formInput}
                          onChange={handleDuesFileUpload}
                          required
                        />
                      </div>

                      {duesSettleImage && (
                        <div style={{ marginBottom: '16px' }}>
                          <img
                            src={duesSettleImage}
                            alt="Screenshot Preview"
                            style={{ maxHeight: '150px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                          />
                        </div>
                      )}

                      <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                        <button
                          type="button"
                          className={ck.btnSecondary}
                          onClick={() => setSelectedBillForSettle(null)}
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          className={ck.btnPrimary}
                          disabled={settlingDuesPayment}
                        >
                          {settlingDuesPayment ? 'Submitting...' : 'Submit Settlement'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ─── Add Address Modal ─── */}
        {showAddressModal && (
          <div className={ck.addrModalOverlay} onClick={() => setShowAddressModal(false)}>
            <div className={ck.addrModal} onClick={(e) => e.stopPropagation()}>
              <div className={ck.addrModalHeader}>
                <span className={ck.addrModalTitle}>Add New Address</span>
                <button className={ck.addrModalClose} onClick={() => setShowAddressModal(false)}>
                  ✕
                </button>
              </div>
              <div className={ck.addrModalBody}>
                <div className={ck.formGroup}>
                  <label className={ck.formLabel}>Recipient Name *</label>
                  <input
                    className={ck.formInput}
                    type="text"
                    placeholder="Full name of recipient"
                    value={newAddress.name || ''}
                    onChange={(e) => setNewAddress({ ...newAddress, name: e.target.value })}
                  />
                </div>
                <div className={ck.formGroup}>
                  <label className={ck.formLabel}>Street Address *</label>
                  <input
                    className={ck.formInput}
                    type="text"
                    placeholder="House no., Street, Locality"
                    value={newAddress.street}
                    onChange={(e) => setNewAddress({ ...newAddress, street: e.target.value })}
                  />
                </div>
                <div className={ck.formGroup}>
                  <label className={ck.formLabel}>Address Line 2 (Optional)</label>
                  <input
                    className={ck.formInput}
                    type="text"
                    placeholder="Apartment, suite, unit, etc."
                    value={newAddress.addressLine2 || ''}
                    onChange={(e) => setNewAddress({ ...newAddress, addressLine2: e.target.value })}
                  />
                </div>
                <div className={ck.formGroup}>
                  <label className={ck.formLabel}>Landmark (Optional)</label>
                  <input
                    className={ck.formInput}
                    type="text"
                    placeholder="Near hospital, next to mall, etc."
                    value={newAddress.landmark || ''}
                    onChange={(e) => setNewAddress({ ...newAddress, landmark: e.target.value })}
                  />
                </div>
                <div className={ck.formRow}>
                  <div className={ck.formGroup}>
                    <label className={ck.formLabel}>State *</label>
                    <SearchableSelect
                      options={checkoutStates}
                      value={newAddress.state}
                      onChange={(val) => {
                        setNewAddress({ ...newAddress, state: val, district: '' });
                        fetchCheckoutDistricts(val, setNewAddrDistricts);
                      }}
                      placeholder="Select State"
                      inputClassName={ck.formInput}
                      required
                    />
                  </div>
                  <div className={ck.formGroup}>
                    <label className={ck.formLabel}>District *</label>
                    <SearchableSelect
                      options={newAddrDistricts}
                      value={newAddress.district}
                      onChange={(val) => setNewAddress({ ...newAddress, district: val })}
                      placeholder="Select District"
                      disabled={!newAddress.state}
                      inputClassName={ck.formInput}
                      required
                    />
                  </div>
                </div>
                <div className={ck.formRow}>
                  <div className={ck.formGroup}>
                    <label className={ck.formLabel}>City *</label>
                    <input
                      className={ck.formInput}
                      type="text"
                      placeholder="City"
                      value={newAddress.city}
                      onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })}
                    />
                  </div>
                  <div className={ck.formGroup}>
                    <label className={ck.formLabel}>Pin Code *</label>
                    <input
                      className={ck.formInput}
                      type="text"
                      placeholder="6-digit pincode"
                      maxLength={6}
                      value={newAddress.zipCode}
                      onChange={(e) => setNewAddress({ ...newAddress, zipCode: e.target.value })}
                    />
                  </div>
                </div>
                <div className={ck.formGroup}>
                  <label className={ck.formLabel}>Country</label>
                  <input
                    className={ck.formInput}
                    type="text"
                    value={newAddress.country}
                    onChange={(e) => setNewAddress({ ...newAddress, country: e.target.value })}
                  />
                </div>
              </div>
              <div className={ck.addrModalFooter}>
                <button className={ck.btnSecondary} onClick={() => setShowAddressModal(false)}>
                  Cancel
                </button>
                <button
                  className={ck.btnPrimary}
                  onClick={() => {
                    if (
                      !newAddress.street ||
                      !newAddress.city ||
                      !newAddress.state ||
                      !newAddress.zipCode
                    ) {
                      toast.error('Fill required fields');
                      return;
                    }
                    selectSavedAddress(newAddress);
                    if (newAddress.zipCode) checkPincodeServiceability(newAddress.zipCode);
                    setShowAddressModal(false);
                    setNewAddress({
                      street: '',
                      city: '',
                      state: '',
                      district: '',
                      zipCode: '',
                      country: 'India',
                      addressLine2: '',
                      landmark: '',
                      name: '',
                    });
                  }}
                >
                  Use This Address
                </button>
              </div>
            </div>
          </div>
        )}

        {/* UPI Payment Modal */}
        {showUpiPayment && (
          <div className={ck.addrModalOverlay} onClick={() => setShowUpiPayment(false)}>
            <div className={ck.upiModal} onClick={(e) => e.stopPropagation()}>
              <div className={ck.upiHeader}>
                <h3 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>📱 UPI Payment</h3>
                <p style={{ margin: '6px 0 0', opacity: 0.85, fontSize: 14 }}>
                  Scan or use UPI ID to pay
                </p>
              </div>
              {!upiDetails && (
                <div style={{ padding: '24px 16px', textAlign: 'center' }}>
                  {upiDetailsError ? (
                    <>
                      <p style={{ color: '#dc2626', marginBottom: 12 }}>
                        UPI payment details could not be loaded. Please contact support or choose another payment method.
                      </p>
                      <button
                        className={ck.btnSecondary}
                        onClick={() => { setUpiDetailsError(false); fetchUPIDetails(); }}
                      >
                        Retry
                      </button>
                    </>
                  ) : (
                    <p style={{ color: '#6b7280' }}>Loading UPI details…</p>
                  )}
                </div>
              )}
              <div className={ck.upiBody} style={!upiDetails ? { display: 'none' } : undefined}>
                {upiDetails.qrCodeUrl && (
                  <img
                    src={upiDetails.qrCodeUrl}
                    alt="UPI QR Code"
                    className={ck.upiQr}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                )}
                <div className={ck.upiIdBox}>
                  <span style={{ fontWeight: 600, color: '#6d28d9' }}>{upiDetails.upiId}</span>
                  <button
                    className={ck.btnPrimary}
                    style={{
                      padding: '6px 14px',
                      fontSize: 12,
                      background: 'linear-gradient(135deg,#7c3aed,#6d28d9)',
                    }}
                    onClick={() => {
                      navigator.clipboard.writeText(upiDetails.upiId);
                      toast.success('UPI ID copied!');
                    }}
                  >
                    Copy
                  </button>
                </div>
                <div style={{ textAlign: 'left', marginTop: 16 }}>
                  <label className={ck.formLabel}>Upload Payment Screenshot *</label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className={ck.formInput}
                    style={{ marginTop: 6 }}
                  />
                </div>
              </div>
              <div className={ck.addrModalFooter}>
                <button
                  className={ck.btnSecondary}
                  onClick={() => {
                    setShowUpiPayment(false);
                    setCheckoutData({
                      ...checkoutData,
                      paymentMethod: 'cod',
                      upiPaymentScreenshot: null,
                    });
                  }}
                >
                  Cancel
                </button>
                <button
                  className={ck.btnPrimary}
                  style={{
                    background: checkoutData.upiPaymentScreenshot
                      ? 'linear-gradient(135deg,#1a4d33,#2d7a50)'
                      : '#94a3b8',
                  }}
                  onClick={() => {
                    if (checkoutData.upiPaymentScreenshot) {
                      setShowUpiPayment(false);
                    } else {
                      toast.error('Please upload payment screenshot');
                    }
                  }}
                  disabled={!checkoutData.upiPaymentScreenshot}
                >
                  Proceed
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Checkout Button at bottom - mobile: app-style summary bar above nav */}
        {!loading &&
          cart?.items?.length > 0 &&
          (isMobile ? (
            <div
              className="mt-6 border-t border-neutral-100 bg-white px-6 pb-6 pt-4"
              style={{ paddingBottom: 'calc(1.5rem + env(safe-area-inset-bottom))' }}
            >
              <div className="mb-4 flex items-center justify-between">
                <span className="text-neutral-500">Subtotal ({cart.items?.length || 0} items)</span>
                <span className="text-lg font-semibold text-neutral-900">
                  ₹{cart.subtotal?.toFixed(2) || '0.00'}
                </span>
              </div>
              {isValet ? (
                <p className="py-2 text-center text-sm font-medium text-amber-700">
                  Valets cannot place orders.
                </p>
              ) : user && ((user as any).effectiveRole === 'wholesaler' || user.role === 'wholesaler') && duesInfo?.hasOverdueBills ? (
                <button
                  onClick={() => setShowDuesModal(true)}
                  className="w-full rounded-xl py-4 font-semibold text-white"
                  style={{ backgroundColor: '#dc2626' }}
                >
                  🔴 Clear Dues
                </button>
              ) : (
                <button
                  onClick={handleStartCheckout}
                  className="w-full rounded-xl py-4 font-semibold text-white"
                  style={{ backgroundColor: MOBILE_ACCENT }}
                >
                  Checkout
                </button>
              )}
            </div>
          ) : (
            <div
              style={{
                marginTop: 32,
                background: '#fff',
                borderRadius: 16,
                boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
                padding: '24px 28px',
                border: '1px solid #f1f5f9',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 20,
                }}
              >
                <span style={{ fontSize: 16, fontWeight: 600, color: '#475569' }}>
                  Subtotal ({cart.items?.length || 0} items)
                </span>
                <span style={{ fontSize: 28, fontWeight: 700, color: '#0f172a' }}>
                  ₹{cart.subtotal?.toFixed(2) || '0.00'}
                </span>
              </div>
              {isValet ? (
                <p
                  style={{
                    textAlign: 'center',
                    color: '#b45309',
                    fontWeight: 600,
                    padding: '12px 0',
                  }}
                >
                  Valets cannot place orders. Use a customer or business account to checkout.
                </p>
              ) : user && ((user as any).effectiveRole === 'wholesaler' || user.role === 'wholesaler') && duesInfo?.hasOverdueBills ? (
                <button
                  onClick={() => setShowDuesModal(true)}
                  style={{
                    width: '100%',
                    padding: '16px',
                    borderRadius: 14,
                    border: 'none',
                    background: 'linear-gradient(135deg,#d63031,#ff7675)',
                    color: '#fff',
                    fontSize: 17,
                    fontWeight: 700,
                    cursor: 'pointer',
                    boxShadow: '0 6px 20px rgba(214, 48, 49, 0.3)',
                    transition: 'all 0.2s',
                    letterSpacing: 0.3,
                  }}
                >
                  🔴 Clear Dues to Order
                </button>
              ) : (
                <button
                  onClick={handleStartCheckout}
                  style={{
                    width: '100%',
                    padding: '16px',
                    borderRadius: 14,
                    border: 'none',
                    background: 'linear-gradient(135deg,#1a4d33,#2d7a50)',
                    color: '#fff',
                    fontSize: 17,
                    fontWeight: 700,
                    cursor: 'pointer',
                    boxShadow: '0 6px 20px rgba(26,77,51,0.3)',
                    transition: 'all 0.2s',
                    letterSpacing: 0.3,
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLElement).style.transform = 'translateY(-1px)';
                    (e.target as HTMLElement).style.boxShadow = '0 8px 28px rgba(26,77,51,0.4)';
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLElement).style.transform = 'none';
                    (e.target as HTMLElement).style.boxShadow = '0 6px 20px rgba(26,77,51,0.3)';
                  }}
                >
                  Proceed to Checkout →
                </button>
              )}
            </div>
          ))}
      </div>

      {/* ── Inline remove confirmation bar ─────────────────────────── */}
      {pendingRemoveItem && (
        <div
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="remove-confirm-title"
          className="fixed bottom-0 left-0 right-0 z-[500] flex items-center justify-between gap-4 border-t border-gray-200 bg-white px-6 py-4 shadow-[0_-4px_24px_rgba(0,0,0,0.10)] md:px-12"
        >
          <p id="remove-confirm-title" className="text-sm font-medium text-gray-800">
            <span className="font-semibold">
              {pendingRemoveItem.item?.product?.name || 'Item'}
            </span>
            {' '}— what would you like to do?
          </p>
          <div className="flex shrink-0 gap-3">
            <button
              onClick={confirmSaveForLater}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50"
            >
              Save for Later
            </button>
            <button
              onClick={confirmRemoveItem}
              className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-rose-700"
            >
              Remove
            </button>
            <button
              onClick={() => setPendingRemoveItem(null)}
              aria-label="Cancel"
              className="rounded-lg px-3 py-2 text-sm text-gray-400 transition-colors hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
