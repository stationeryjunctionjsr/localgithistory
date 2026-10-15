'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'react-toastify';
import { QRCodeSVG } from 'qrcode.react';

import { useAuth } from '@/context/AuthContext';
import { usePincode } from '@/context/PincodeContext';
import { useCartStore } from '@/store/cartStore';
import api from '@/utils/api';
import { getImageUrl } from '@/utils/imageUrl';
import { trackEcommerceEvent } from '@/utils/analytics';
import SearchableSelect from '@/components/SearchableSelect';
import ck from './checkout.module.css';

// Web UPI App launch schemes
const WEB_UPI_APPS = [
  { name: 'PhonePe', scheme: 'phonepe://pay', bg: '#6739B7', color: '#fff', icon: '🟣' },
  { name: 'BHIM', scheme: 'bhim://pay', bg: '#00796B', color: '#fff', icon: '🇮🇳' },
  { name: 'Google Pay', scheme: 'tez://upi/pay', bg: '#1A73E8', color: '#fff', icon: '🌐' },
  { name: 'Paytm', scheme: 'paytmmp://pay', bg: '#00BAF2', color: '#fff', icon: '💳' },
  { name: 'CRED', scheme: 'credpay://pay', bg: '#121212', color: '#fff', icon: '💎' },
];

export default function CheckoutPage() {
  const router = useRouter();
  const { user, login, loginWithTokens, fetchUser } = useAuth();
  const { activeMode } = usePincode();

  // Cart from global store
  const cart = useCartStore((s) => s.cart);
  const fetchCart = useCartStore((s) => s.fetchCart);

  // Stepper state: 1 = Address/Contact, 2 = Delivery Slot, 3 = Payment, 4 = Review
  const [checkoutStep, setCheckoutStep] = useState<1 | 2 | 3 | 4>(1);

  // Guest / Contact state
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [showSignInModal, setShowSignInModal] = useState(false);
  const [authPassword, setAuthPassword] = useState('');
  const [authBusy, setAuthBusy] = useState(false);
  const [isExistingAccount, setIsExistingAccount] = useState<boolean | null>(null);
  const [otpSent, setOtpSent] = useState(false);
  const [otpValue, setOtpValue] = useState('');
  const [otpVerified, setOtpVerified] = useState(false);

  // Delivery Address state
  const [selectedAddress, setSelectedAddress] = useState<any>({
    name: '',
    street: '',
    city: '',
    state: '',
    district: '',
    zipCode: '',
    country: 'India',
    addressLine2: '',
    landmark: '',
  });

  // Add Address Modal state
  const [showAddressModal, setShowAddressModal] = useState(false);
  const [newAddress, setNewAddress] = useState({
    name: '',
    street: '',
    city: '',
    state: '',
    district: '',
    zipCode: '',
    country: 'India',
    addressLine2: '',
    landmark: '',
    saveToProfile: true,
  });
  const [newAddrDistricts, setNewAddrDistricts] = useState<string[]>([]);
  const [checkoutStates, setCheckoutStates] = useState<string[]>([]);

  // Serviceability & Delivery Slot state
  const [checkingServiceability, setCheckingServiceability] = useState(false);
  const [pincodeServiceable, setPincodeServiceable] = useState<boolean | null>(null);
  const [deliveryOptions, setDeliveryOptions] = useState<{
    slotBookingAvailable: boolean;
    availableDates: string[];
    urgentAvailable?: boolean;
    urgentCharge?: number;
  } | null>(null);
  const [selectedDeliveryType, setSelectedDeliveryType] = useState<'standard' | 'urgent'>('standard');
  const [selectedSlotDate, setSelectedSlotDate] = useState('');
  const [availableSlots, setAvailableSlots] = useState<any[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<any | null>(null);
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Delivery charge calculation
  const [deliveryChargeInfo, setDeliveryChargeInfo] = useState<{
    charge: number;
    gstAmount: number;
    gstPercentage: number;
    totalCharge: number;
  } | null>(null);
  const [fetchingDeliveryCharge, setFetchingDeliveryCharge] = useState(false);

  // Payment state
  const [paymentMethod, setPaymentMethod] = useState<'upi' | 'cod' | 'credit'>('upi');
  const [upiPaymentConfirmed, setUpiPaymentConfirmed] = useState(false);
  const [upiTxnRef, setUpiTxnRef] = useState('');
  const [upiAppUsed, setUpiAppUsed] = useState('');
  const [upiModalTab, setUpiModalTab] = useState<'qr' | 'apps'>('qr');
  const [upiUtr, setUpiUtr] = useState('');
  const [showManualUtr, setShowManualUtr] = useState(false);
  const [upiPaymentScreenshot, setUpiPaymentScreenshot] = useState<string | null>(null);

  // Order notes & options
  const [printedBill, setPrintedBill] = useState(false);
  const [orderNotes, setOrderNotes] = useState('');
  const [placingOrder, setPlacingOrder] = useState(false);

  // Coupons & Referrals
  const [couponInput, setCouponInput] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState<{ code: string; discount: number } | null>(null);
  const [couponError, setCouponError] = useState('');
  const [verifyingCoupon, setVerifyingCoupon] = useState(false);

  const [referralCodeInput, setReferralCodeInput] = useState('');
  const [appliedReferralCode, setAppliedReferralCode] = useState<string | null>(null);
  const [referralDiscountInfo, setReferralDiscountInfo] = useState<any>(null);
  const [referralError, setReferralError] = useState('');
  const [verifyingReferral, setVerifyingReferral] = useState(false);

  // Segment flags for payment options
  const [enabledFlags, setEnabledFlags] = useState<string[]>([]);

  // ── 1. Load initial user / guest details & location master ──
  useEffect(() => {
    // Fetch feature flags
    api.get('/super-admin/features')
      .then((res) => {
        if (Array.isArray(res.data?.features)) {
          setEnabledFlags(res.data.features.filter((f: any) => f.isEnabled).map((f: any) => f.flagKey));
        }
      })
      .catch(() => {});

    // Fetch checkout states for address selection
    api.get('/locations/states')
      .then((res) => {
        if (Array.isArray(res.data)) {
          setCheckoutStates(res.data.map((s: any) => s.name || s));
        }
      })
      .catch(() => {});

    // Auto-fill from localStorage if guest
    if (typeof window !== 'undefined') {
      try {
        const cached = localStorage.getItem('sj_checkout_guest_info');
        if (cached) {
          const parsed = JSON.parse(cached);
          if (parsed.name) setContactName(parsed.name);
          if (parsed.phone) setContactPhone(parsed.phone);
          if (parsed.email) setContactEmail(parsed.email);
        }
      } catch {}
    }
  }, []);

  // ── 2. Sync logged-in user profile details ──
  useEffect(() => {
    if (user) {
      if (user.name && !contactName) setContactName(user.name);
      if (user.phone && !contactPhone) setContactPhone(user.phone);
      if (user.email && !contactEmail) setContactEmail(user.email);
    }
  }, [user]);

  // ── 3. Manage Multiple Saved Addresses ──
  const userAddresses = useMemo(() => {
    const list: any[] = [];
    if (user?.address && (user.address.street || user.address.pincode)) {
      list.push({
        ...user.address,
        is_primary: true,
        name: user.address.name || user.name || '',
      });
    }
    if (Array.isArray(user?.savedAddresses)) {
      user.savedAddresses.forEach((sa: any) => {
        const isDup = list.some(
          (a) =>
            a.street === sa.street &&
            (a.zipCode || a.pincode) === (sa.zipCode || sa.pincode)
        );
        if (!isDup) {
          list.push({
            ...sa,
            is_primary: false,
            name: sa.name || user?.name || '',
          });
        }
      });
    }
    return list;
  }, [user]);

  // Auto-select primary address if not yet selected
  useEffect(() => {
    if (userAddresses.length > 0 && !selectedAddress.street) {
      const primary = userAddresses.find((a) => a.is_primary) || userAddresses[0];
      handleSelectAddress(primary);
    }
  }, [userAddresses]);

  // Select an address card
  const handleSelectAddress = (addr: any) => {
    const zip = addr.zipCode || addr.pincode || '';
    const updated = {
      name: addr.name || contactName || user?.name || '',
      street: addr.street || '',
      city: addr.city || '',
      state: addr.state || '',
      district: addr.district || '',
      zipCode: zip,
      country: addr.country || 'India',
      addressLine2: addr.addressLine2 || '',
      landmark: addr.landmark || '',
    };
    setSelectedAddress(updated);
    if (zip.length === 6) {
      checkServiceability(zip);
    }
  };

  // ── 4. India Post Pincode Lookup ──
  const fetchAddressByPincode = (pincode: string, isModal = false) => {
    if (pincode.length !== 6 || !/^\d{6}$/.test(pincode)) return;
    fetch(`https://api.postalpincode.in/pincode/${pincode}`)
      .then((res) => res.json())
      .then((data) => {
        if (data?.[0]?.Status === 'Success' && data[0].PostOffice?.length > 0) {
          const po = data[0].PostOffice[0];
          const autoCity = po.District || po.Block || po.Name || '';
          const autoState = po.State || '';
          const autoDistrict = po.District || '';

          if (isModal) {
            setNewAddress((prev) => ({
              ...prev,
              city: prev.city || autoCity,
              state: prev.state || autoState,
              district: prev.district || autoDistrict,
            }));
            if (autoState) fetchDistricts(autoState, setNewAddrDistricts);
          } else {
            setSelectedAddress((prev: any) => ({
              ...prev,
              city: prev.city || autoCity,
              state: prev.state || autoState,
              district: prev.district || autoDistrict,
            }));
          }
        }
      })
      .catch(() => {});
  };

  const fetchDistricts = async (stateName: string, setter: (d: string[]) => void) => {
    try {
      const res = await api.get('/locations/districts', { params: { state: stateName } });
      if (Array.isArray(res.data)) {
        setter(res.data.map((d: any) => d.name || d));
      }
    } catch {
      setter([]);
    }
  };

  // ── 5. Check Pincode Serviceability & Delivery Slots ──
  const checkServiceability = async (pincode: string) => {
    if (!pincode || pincode.length !== 6) {
      setPincodeServiceable(null);
      setDeliveryOptions(null);
      return;
    }
    setCheckingServiceability(true);
    try {
      const role = (user as any)?.role || 'customer';
      const res = await api.get('/delivery-charges/check-serviceability', {
        params: { pincode, userRole: role },
      });
      const data = res.data;
      setPincodeServiceable(data.isServiceable);
      setDeliveryOptions({
        slotBookingAvailable: data.slotBookingAvailable ?? false,
        availableDates: data.availableDates ?? [],
        urgentAvailable: data.urgentDeliveryAvailable ?? false,
        urgentCharge: data.urgentDeliveryCharge ?? 0,
      });

      // Default slot date if available
      if (data.availableDates && data.availableDates.length > 0) {
        const first = data.availableDates[0];
        setSelectedSlotDate(first);
        loadSlotsForDate(first, pincode);
      }
    } catch {
      setPincodeServiceable(null);
      setDeliveryOptions(null);
    } finally {
      setCheckingServiceability(false);
    }
  };

  const loadSlotsForDate = async (dateStr: string, pincode?: string) => {
    const pin = pincode || selectedAddress.zipCode;
    if (!dateStr || !pin) return;
    setLoadingSlots(true);
    setSelectedSlot(null);
    try {
      const segment = (user as any)?.role === 'wholesaler' ? 'wholesale' : 'retail';
      const res = await api.get('/delivery-slots/available', {
        params: { date: dateStr, pincode: pin, segment },
      });
      setAvailableSlots(res.data || []);
      // Auto-select "anytime" as friendly default
      setSelectedSlot({ slotId: 'anytime', isFullDay: true, isUrgent: false });
    } catch {
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  // Calculate delivery charge whenever address or subtotal updates
  useEffect(() => {
    if (selectedAddress.zipCode?.length === 6 && pincodeServiceable) {
      fetchDeliveryFee();
    }
  }, [selectedAddress.zipCode, pincodeServiceable, activeMode]);

  const fetchDeliveryFee = async () => {
    setFetchingDeliveryCharge(true);
    try {
      const role = (user as any)?.role || 'customer';
      const res = await api.get('/delivery-charges/calculate', {
        params: {
          pincode: selectedAddress.zipCode,
          state: selectedAddress.state,
          city: selectedAddress.city,
          district: selectedAddress.district,
          userRole: role,
          orderAmount: cartSubtotal,
          fulfillment_type: activeMode === 'pan_india' ? 'courier' : 'hyperlocal',
        },
      });
      setDeliveryChargeInfo({
        charge: res.data.charge || 0,
        gstAmount: res.data.gstAmount || 0,
        gstPercentage: res.data.gstPercentage || 18,
        totalCharge: res.data.totalCharge || 0,
      });
    } catch {
      setDeliveryChargeInfo(null);
    } finally {
      setFetchingDeliveryCharge(false);
    }
  };

  // ── 6. Save New Address & Persist to MySQL User Profile ──
  const handleSaveNewAddress = async () => {
    if (!newAddress.street || !newAddress.city || !newAddress.state || !newAddress.zipCode) {
      toast.error('Please fill in Street, City, State, and Pincode');
      return;
    }

    const addrToUse = {
      ...newAddress,
      name: newAddress.name || contactName || user?.name || '',
    };

    handleSelectAddress(addrToUse);
    setShowAddressModal(false);

    // If logged in, persist to backend user saved_addresses
    if (user?.id && newAddress.saveToProfile) {
      try {
        const existing = Array.isArray(user.savedAddresses) ? [...user.savedAddresses] : [];
        const isDup = existing.some(
          (a) => a.street === addrToUse.street && (a.zipCode || a.pincode) === addrToUse.zipCode
        );
        if (!isDup) {
          const updated = [...existing, { ...addrToUse, pincode: addrToUse.zipCode }];
          await api.put(`/users/${user.id}`, { savedAddresses: updated });
          if (fetchUser) await fetchUser();
          toast.success('Address saved to your address book');
        }
      } catch (err) {
        console.warn('Could not persist address to profile:', err);
      }
    }
  };

  // Delete saved address
  const handleDeleteAddress = async (e: React.MouseEvent, addr: any) => {
    e.stopPropagation();
    if (!user?.id) return;
    try {
      const existing = Array.isArray(user.savedAddresses) ? [...user.savedAddresses] : [];
      const updated = existing.filter(
        (a) => !(a.street === addr.street && (a.zipCode || a.pincode) === (addr.zipCode || addr.pincode))
      );
      await api.put(`/users/${user.id}`, { savedAddresses: updated });
      if (fetchUser) await fetchUser();
      toast.success('Address removed');
    } catch {
      toast.error('Failed to remove address');
    }
  };

  // ── 7. Price Calculations ──
  const cartSubtotal = useMemo(() => {
    if (!cart?.items) return 0;
    return cart.items.reduce(
      (sum: number, item: any) => sum + (Number(item.price) || 0) * (Number(item.quantity) || 1),
      0
    );
  }, [cart]);

  const referralDiscountAmount = referralDiscountInfo?.discountAmount || 0;
  const couponDiscountAmount = appliedCoupon?.discount || 0;
  const deliveryFee = deliveryChargeInfo?.totalCharge || 0;
  const grandTotal = Math.max(0, cartSubtotal - referralDiscountAmount - couponDiscountAmount + deliveryFee);

  // ── 8. NPCI UPI URI with 0% Commission & Dynamic QR ──
  const ensureUpiRef = () => {
    if (!upiTxnRef) {
      const generated = `SJ${Date.now()}${Math.floor(100 + Math.random() * 900)}`;
      setUpiTxnRef(generated);
      return generated;
    }
    return upiTxnRef;
  };

  const dynamicUpiUri = useMemo(() => {
    const payeeVpa = 'stationeryjunction@icici';
    const payeeName = 'Stationery Junction';
    const ref = upiTxnRef || 'SJORDER';
    const amountStr = grandTotal.toFixed(2);
    const note = `Order ${ref}`;
    return `upi://pay?pa=${encodeURIComponent(payeeVpa)}&pn=${encodeURIComponent(payeeName)}&am=${encodeURIComponent(amountStr)}&cu=INR&tr=${encodeURIComponent(ref)}&tn=${encodeURIComponent(note)}`;
  }, [grandTotal, upiTxnRef]);

  const handleLaunchUpiApp = (scheme: string, appName: string) => {
    ensureUpiRef();
    setUpiAppUsed(appName);
    const deepLink = `${scheme}?pa=stationeryjunction@icici&pn=Stationery%20Junction&am=${grandTotal.toFixed(2)}&cu=INR&tr=${ensureUpiRef()}&tn=Order%20${ensureUpiRef()}`;
    window.location.href = deepLink;
  };

  // ── 9. Guest Phone Verification / Silent Sign Up ──
  const handleCheckPhone = async () => {
    const raw = contactPhone.replace(/\D/g, '');
    if (raw.length < 10) {
      toast.error('Please enter a valid 10-digit mobile number');
      return;
    }
    setAuthBusy(true);
    try {
      const res = await api.post('/auth/check-phone', { phone: raw });
      setIsExistingAccount(res.data.exists);
      if (!res.data.exists) {
        // Send OTP
        await api.post('/auth/send-otp', { phone: raw, purpose: 'register' });
        setOtpSent(true);
        toast.info('OTP sent to your phone');
      }
    } catch {
      toast.error('Could not verify mobile number. Try again.');
    } finally {
      setAuthBusy(false);
    }
  };

  const handleQuickRegister = async () => {
    const raw = contactPhone.replace(/\D/g, '');
    if (!authPassword || authPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setAuthBusy(true);
    try {
      const payload: any = {
        phone: raw,
        password: authPassword,
        name: contactName,
        email: contactEmail || undefined,
        role: 'customer',
        otp: otpValue,
        address: selectedAddress.street ? selectedAddress : undefined,
      };
      const res = await api.post('/auth/register', payload);
      const { token, refreshToken, sessionId, user: userData } = res.data;
      await loginWithTokens({ token, refreshToken, sessionId, user: userData });
      toast.success('Account created successfully!');
      setShowSignInModal(false);
      if (fetchCart) fetchCart();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Registration failed');
    } finally {
      setAuthBusy(false);
    }
  };

  const handleQuickLogin = async () => {
    if (!authPassword) {
      toast.error('Enter your password');
      return;
    }
    setAuthBusy(true);
    try {
      await login(contactPhone.replace(/\D/g, ''), authPassword);
      toast.success('Logged in successfully!');
      setShowSignInModal(false);
      if (fetchCart) fetchCart();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Invalid credentials');
    } finally {
      setAuthBusy(false);
    }
  };

  // ── 10. Place Order ──
  const handlePlaceOrder = async () => {
    if (!user) {
      setShowSignInModal(true);
      toast.info('Please sign in or create an account to finalize your order');
      return;
    }

    if (!selectedAddress.street || !selectedAddress.zipCode) {
      toast.error('Please select or enter a valid delivery address');
      setCheckoutStep(1);
      return;
    }

    if (pincodeServiceable === false) {
      toast.error('Selected delivery pincode is not serviceable');
      return;
    }

    setPlacingOrder(true);
    try {
      let finalNotes = orderNotes.trim();
      if (paymentMethod === 'upi') {
        finalNotes = `${finalNotes} | [UPI via ${upiAppUsed || 'Dynamic QR'} | Ref: ${upiTxnRef || 'SJORDER'}${upiUtr ? ` | UTR: ${upiUtr}` : ''}${upiPaymentConfirmed ? ' | Status: Customer Confirmed' : ''}]`.trim();
      }

      const payload = {
        shippingAddress: selectedAddress,
        billingAddress: selectedAddress,
        paymentMethod: paymentMethod,
        upiPaymentScreenshot: upiPaymentScreenshot || undefined,
        notes: finalNotes || undefined,
        couponCode: appliedCoupon?.code || undefined,
        referralCode: appliedReferralCode || undefined,
        discount: referralDiscountAmount + couponDiscountAmount,
        printedBill: printedBill,
        fulfillmentType: activeMode === 'pan_india' ? 'courier' : 'hyperlocal',
        isUrgentDelivery: activeMode === 'pan_india' ? false : selectedDeliveryType === 'urgent',
        deliverySlotId: activeMode === 'pan_india' ? null : (selectedDeliveryType === 'standard' ? (selectedSlot?.slotId ?? null) : null),
        deliverySlotConfigId: activeMode === 'pan_india' ? null : (selectedDeliveryType === 'standard' ? (selectedSlot?.configId ?? null) : null),
        deliverySlotDate: activeMode === 'pan_india' ? null : (selectedDeliveryType === 'urgent' ? null : (selectedSlot ? selectedSlotDate : null)),
      };

      const res = await api.post('/orders', payload);
      toast.success('Order placed successfully!');

      // Save contact info to localStorage for next time
      try {
        localStorage.setItem(
          'sj_checkout_guest_info',
          JSON.stringify({ name: contactName, phone: contactPhone, email: contactEmail })
        );
      } catch {}

      if (fetchCart) await fetchCart();
      router.push('/customer/orders');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || 'Failed to place order';
      toast.error(msg);
    } finally {
      setPlacingOrder(false);
    }
  };

  // ── Render ──
  return (
    <div className={ck.checkoutContainer}>
      {/* ── Minimal Checkout Header ── */}
      <header className={ck.checkoutHeader}>
        <div className={ck.checkoutHeaderInner}>
          <Link href="/" className={ck.headerBrand}>
            <span className={ck.headerLogo}>Stationery Junction</span>
          </Link>
          <div className={ck.secureBadge}>
            <span>🔒</span>
            <span>256-bit SSL Secure Checkout</span>
          </div>
          <Link href="/customer/cart" className={ck.backToCart}>
            <span>←</span>
            <span>Return to Cart</span>
          </Link>
        </div>
      </header>

      {/* ── Main Layout (Left: Steps, Right: Summary) ── */}
      <main className={ck.checkoutMain}>
        <div>
          {/* Stepper Navigation */}
          <div className={ck.stepperContainer}>
            <div className={ck.stepper}>
              <div
                className={`${ck.stepItem} ${checkoutStep === 1 ? ck.active : ''} ${checkoutStep > 1 ? ck.completed : ''}`}
                onClick={() => setCheckoutStep(1)}
              >
                <div className={ck.stepCircle}>{checkoutStep > 1 ? '✓' : '1'}</div>
                <span className={ck.stepLabel}>Address</span>
              </div>
              <div className={`${ck.stepSeparator} ${checkoutStep > 1 ? ck.done : ''}`} />

              <div
                className={`${ck.stepItem} ${checkoutStep === 2 ? ck.active : ''} ${checkoutStep > 2 ? ck.completed : ''}`}
                onClick={() => {
                  if (selectedAddress.street && selectedAddress.zipCode) setCheckoutStep(2);
                }}
              >
                <div className={ck.stepCircle}>{checkoutStep > 2 ? '✓' : '2'}</div>
                <span className={ck.stepLabel}>Delivery Slot</span>
              </div>
              <div className={`${ck.stepSeparator} ${checkoutStep > 2 ? ck.done : ''}`} />

              <div
                className={`${ck.stepItem} ${checkoutStep === 3 ? ck.active : ''} ${checkoutStep > 3 ? ck.completed : ''}`}
                onClick={() => {
                  if (selectedAddress.street) setCheckoutStep(3);
                }}
              >
                <div className={ck.stepCircle}>{checkoutStep > 3 ? '✓' : '3'}</div>
                <span className={ck.stepLabel}>Payment</span>
              </div>
              <div className={`${ck.stepSeparator} ${checkoutStep > 3 ? ck.done : ''}`} />

              <div
                className={`${ck.stepItem} ${checkoutStep === 4 ? ck.active : ''}`}
                onClick={() => {
                  if (selectedAddress.street) setCheckoutStep(4);
                }}
              >
                <div className={ck.stepCircle}>4</div>
                <span className={ck.stepLabel}>Review</span>
              </div>
            </div>
          </div>

          {/* ═══════════════════════════════════════════════════════
             STEP 1: Contact & Delivery Address
             ═══════════════════════════════════════════════════════ */}
          {checkoutStep === 1 && (
            <div className={ck.stepContentBox}>
              <h2 className={ck.stepHeading}>
                <span>📍</span>
                <span>Delivery Address &amp; Contact</span>
              </h2>
              <p className={ck.stepSubheading}>Where should we deliver your order?</p>

              {/* Guest Contact Information & Autofill */}
              <div className={ck.contactBox}>
                <div className={ck.contactHeader}>
                  <span className={ck.contactTitle}>Contact Information</span>
                  {!user && (
                    <button
                      type="button"
                      className={ck.contactToggleLink}
                      onClick={() => setShowSignInModal(true)}
                    >
                      Already have an account? Sign In
                    </button>
                  )}
                </div>
                <div className={ck.contactGrid}>
                  <div>
                    <label className={ck.formLabel}>Full Name *</label>
                    <input
                      type="text"
                      className={ck.formInput}
                      placeholder="Your full name"
                      autoComplete="name"
                      value={contactName}
                      onChange={(e) => setContactName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className={ck.formLabel}>Mobile Number *</label>
                    <input
                      type="tel"
                      className={ck.formInput}
                      placeholder="10-digit mobile number"
                      autoComplete="tel"
                      maxLength={10}
                      value={contactPhone}
                      onChange={(e) => setContactPhone(e.target.value.replace(/\D/g, ''))}
                    />
                  </div>
                </div>
              </div>

              {/* Saved Addresses (Logged in) */}
              {user && userAddresses.length > 0 && (
                <div>
                  <label className={ck.formLabel} style={{ marginBottom: 12 }}>
                    Saved Addresses ({userAddresses.length})
                  </label>
                  <div className={ck.addressGrid}>
                    {userAddresses.map((addr, idx) => {
                      const isSelected =
                        selectedAddress.street === addr.street &&
                        selectedAddress.zipCode === (addr.zipCode || addr.pincode);
                      return (
                        <div
                          key={idx}
                          className={`${ck.addressCard} ${isSelected ? ck.selected : ''}`}
                          onClick={() => handleSelectAddress(addr)}
                        >
                          {addr.is_primary && <span className={ck.addressBadge}>Primary</span>}
                          <div className={ck.addressName}>{addr.name || user.name}</div>
                          <div className={ck.addressStreet}>
                            {addr.street}
                            {addr.addressLine2 ? `, ${addr.addressLine2}` : ''}
                          </div>
                          <div className={ck.addressCityState}>
                            {addr.city}, {addr.state} — <strong>{addr.zipCode || addr.pincode}</strong>
                          </div>
                          <div className={ck.addressCardFooter}>
                            <span className={ck.addressSelectIndicator}>
                              {isSelected ? '✓ Selected' : 'Tap to Select'}
                            </span>
                            {!addr.is_primary && (
                              <button
                                type="button"
                                className={ck.addressDeleteBtn}
                                onClick={(e) => handleDeleteAddress(e, addr)}
                              >
                                Remove
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}

                    {/* Add New Address Card */}
                    <div className={ck.addNewAddressCard} onClick={() => setShowAddressModal(true)}>
                      <div className={ck.addNewIcon}>+</div>
                      <div className={ck.addNewLabel}>Add New Address</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Direct Address Input (Guests or Users with no saved address) */}
              {(!user || userAddresses.length === 0) && (
                <div style={{ marginTop: 16 }}>
                  <div className={ck.formGroup}>
                    <label className={ck.formLabel}>Street Address *</label>
                    <input
                      type="text"
                      className={ck.formInput}
                      placeholder="House/Flat number, building name, street"
                      autoComplete="street-address"
                      value={selectedAddress.street}
                      onChange={(e) => setSelectedAddress({ ...selectedAddress, street: e.target.value })}
                    />
                  </div>
                  <div className={ck.formRow}>
                    <div className={ck.formGroup}>
                      <label className={ck.formLabel}>Postal Pin Code *</label>
                      <input
                        type="text"
                        className={ck.formInput}
                        placeholder="6-digit pincode"
                        maxLength={6}
                        autoComplete="postal-code"
                        value={selectedAddress.zipCode}
                        onChange={(e) => {
                          const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                          setSelectedAddress({ ...selectedAddress, zipCode: val });
                          if (val.length === 6) {
                            fetchAddressByPincode(val, false);
                            checkServiceability(val);
                          }
                        }}
                      />
                    </div>
                    <div className={ck.formGroup}>
                      <label className={ck.formLabel}>City *</label>
                      <input
                        type="text"
                        className={ck.formInput}
                        placeholder="City"
                        autoComplete="address-level2"
                        value={selectedAddress.city}
                        onChange={(e) => setSelectedAddress({ ...selectedAddress, city: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className={ck.formRow}>
                    <div className={ck.formGroup}>
                      <label className={ck.formLabel}>State *</label>
                      <input
                        type="text"
                        className={ck.formInput}
                        placeholder="State"
                        autoComplete="address-level1"
                        value={selectedAddress.state}
                        onChange={(e) => setSelectedAddress({ ...selectedAddress, state: e.target.value })}
                      />
                    </div>
                    <div className={ck.formGroup}>
                      <label className={ck.formLabel}>District / Area</label>
                      <input
                        type="text"
                        className={ck.formInput}
                        placeholder="District"
                        value={selectedAddress.district}
                        onChange={(e) => setSelectedAddress({ ...selectedAddress, district: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Serviceability Badge */}
              {selectedAddress.zipCode?.length === 6 && (
                <div style={{ marginTop: 12 }}>
                  {checkingServiceability && (
                    <div style={{ fontSize: 13, color: '#64748b' }}>⏳ Verifying delivery serviceability...</div>
                  )}
                  {pincodeServiceable === true && !checkingServiceability && (
                    <div style={{ fontSize: 13, color: '#16a34a', fontWeight: 600 }}>
                      ✓ Delivery available to {selectedAddress.zipCode}
                    </div>
                  )}
                  {pincodeServiceable === false && !checkingServiceability && (
                    <div style={{ fontSize: 13, color: '#dc2626', fontWeight: 600 }}>
                      ⚠️ Delivery is not currently available for this pincode
                    </div>
                  )}
                </div>
              )}

              {/* Stepper Footer */}
              <div className={ck.stepFooter}>
                <Link href="/customer/cart" className={ck.btnSecondary}>
                  ← Back to Cart
                </Link>
                <button
                  type="button"
                  className={ck.btnPrimary}
                  disabled={
                    !selectedAddress.street ||
                    !selectedAddress.zipCode ||
                    selectedAddress.zipCode.length !== 6 ||
                    pincodeServiceable === false
                  }
                  onClick={() => setCheckoutStep(2)}
                >
                  Continue to Delivery Slot →
                </button>
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════════════════════
             STEP 2: Delivery Slot (in Checkout Step Only!)
             ═══════════════════════════════════════════════════════ */}
          {checkoutStep === 2 && (
            <div className={ck.stepContentBox}>
              <h2 className={ck.stepHeading}>
                <span>🚚</span>
                <span>Select Delivery Option &amp; Slot</span>
              </h2>
              <p className={ck.stepSubheading}>Choose when you would like to receive your delivery</p>

              {/* Pan-India Courier Mode */}
              {activeMode === 'pan_india' ? (
                <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 12, padding: 20 }}>
                  <div style={{ fontWeight: 700, color: '#1e40af', fontSize: 15, marginBottom: 4 }}>
                    📦 Pan-India Standard Courier Delivery
                  </div>
                  <div style={{ color: '#3b82f6', fontSize: 13, lineHeight: 1.5 }}>
                    Your items will be dispatched via express 3PL surface courier. Estimated delivery in 3 to 5 business days. Tracking details will be shared via SMS.
                  </div>
                </div>
              ) : (
                /* Hyperlocal Mode */
                <div className={ck.slotSection}>
                  <div className={ck.slotTypeGrid}>
                    <div
                      className={`${ck.slotTypeCard} ${selectedDeliveryType === 'standard' ? ck.selected : ''}`}
                      onClick={() => {
                        setSelectedDeliveryType('standard');
                        if (deliveryOptions?.availableDates?.length) {
                          const first = deliveryOptions.availableDates[0];
                          setSelectedSlotDate(first);
                          loadSlotsForDate(first);
                        }
                      }}
                    >
                      <div className={ck.slotTypeTitle}>
                        <span>🛵</span>
                        <span>Standard Delivery</span>
                      </div>
                      <div className={ck.slotTypeDesc}>Select your preferred date &amp; time slot</div>
                    </div>

                    {deliveryOptions?.urgentAvailable && (
                      <div
                        className={`${ck.slotTypeCard} ${selectedDeliveryType === 'urgent' ? ck.selected : ''}`}
                        onClick={() => setSelectedDeliveryType('urgent')}
                      >
                        <div className={ck.slotTypeTitle}>
                          <span>⚡</span>
                          <span>Express Urgent Delivery</span>
                        </div>
                        <div className={ck.slotTypeDesc}>
                          Delivered within 60–90 mins (+₹{deliveryOptions.urgentCharge || 49})
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Standard Slot Date & Time Selector */}
                  {selectedDeliveryType === 'standard' && (
                    <div>
                      {deliveryOptions?.availableDates && deliveryOptions.availableDates.length > 0 && (
                        <div>
                          <label className={ck.formLabel}>Select Delivery Date</label>
                          <div className={ck.datesRow}>
                            {deliveryOptions.availableDates.map((dateStr) => (
                              <button
                                key={dateStr}
                                type="button"
                                className={`${ck.dateChip} ${selectedSlotDate === dateStr ? ck.selected : ''}`}
                                onClick={() => {
                                  setSelectedSlotDate(dateStr);
                                  loadSlotsForDate(dateStr);
                                }}
                              >
                                {dateStr}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Time Slot Chips */}
                      {selectedSlotDate && (
                        <div>
                          <label className={ck.formLabel}>Select Time Window</label>
                          {loadingSlots ? (
                            <div style={{ fontSize: 13, color: '#64748b', padding: '12px 0' }}>Loading available slots...</div>
                          ) : (
                            <div className={ck.slotGrid}>
                              <button
                                type="button"
                                className={`${ck.slotChip} ${selectedSlot?.slotId === 'anytime' ? ck.selected : ''}`}
                                onClick={() => setSelectedSlot({ slotId: 'anytime', isFullDay: true, isUrgent: false })}
                              >
                                Anytime (Full Day)
                              </button>
                              {availableSlots
                                .filter((s) => !s.isUrgent)
                                .map((slot) => (
                                  <button
                                    key={slot.slotId}
                                    type="button"
                                    className={`${ck.slotChip} ${selectedSlot?.slotId === slot.slotId ? ck.selected : ''}`}
                                    onClick={() => setSelectedSlot(slot)}
                                  >
                                    {slot.isFullDay ? 'Full Day' : `${slot.startTime} – ${slot.endTime}`}
                                  </button>
                                ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Stepper Footer */}
              <div className={ck.stepFooter}>
                <button type="button" className={ck.btnSecondary} onClick={() => setCheckoutStep(1)}>
                  ← Back to Address
                </button>
                <button
                  type="button"
                  className={ck.btnPrimary}
                  disabled={
                    activeMode !== 'pan_india' &&
                    selectedDeliveryType === 'standard' &&
                    deliveryOptions?.slotBookingAvailable &&
                    !selectedSlot
                  }
                  onClick={() => {
                    ensureUpiRef();
                    setCheckoutStep(3);
                  }}
                >
                  Continue to Payment →
                </button>
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════════════════════
             STEP 3: Payment (0% Commission Direct UPI Flow)
             ═══════════════════════════════════════════════════════ */}
          {checkoutStep === 3 && (
            <div className={ck.stepContentBox}>
              <h2 className={ck.stepHeading}>
                <span>💳</span>
                <span>Payment Method</span>
              </h2>
              <p className={ck.stepSubheading}>Select how you would like to pay for your order</p>

              <div className={ck.paymentGrid}>
                {/* Direct UPI */}
                <div
                  className={`${ck.paymentOption} ${paymentMethod === 'upi' ? ck.selected : ''}`}
                  onClick={() => {
                    setPaymentMethod('upi');
                    ensureUpiRef();
                  }}
                >
                  <div className={ck.paymentIcon} style={{ background: '#ede9fe' }}>
                    ⚡
                  </div>
                  <div className={ck.paymentTitle}>UPI Payment</div>
                  <div className={ck.paymentDesc}>PhonePe, BHIM, GPay, Paytm (0% fee)</div>
                </div>

                {/* Cash on Delivery */}
                <div
                  className={`${ck.paymentOption} ${paymentMethod === 'cod' ? ck.selected : ''}`}
                  onClick={() => setPaymentMethod('cod')}
                >
                  <div className={ck.paymentIcon} style={{ background: '#fef3c7' }}>
                    💵
                  </div>
                  <div className={ck.paymentTitle}>Cash on Delivery</div>
                  <div className={ck.paymentDesc}>Pay cash upon delivery</div>
                </div>

                {/* B2B Credit (Wholesalers only) */}
                {(user as any)?.role === 'wholesaler' && (
                  <div
                    className={`${ck.paymentOption} ${paymentMethod === 'credit' ? ck.selected : ''}`}
                    onClick={() => setPaymentMethod('credit')}
                  >
                    <div className={ck.paymentIcon} style={{ background: '#e0f2fe' }}>
                      🏢
                    </div>
                    <div className={ck.paymentTitle}>Credit (B2B)</div>
                    <div className={ck.paymentDesc}>Net-30 business account</div>
                  </div>
                )}
              </div>

              {/* UPI Payment Card */}
              {paymentMethod === 'upi' && (
                <div className={ck.upiCard}>
                  <div className={ck.upiTabs}>
                    <button
                      type="button"
                      className={`${ck.upiTab} ${upiModalTab === 'qr' ? ck.active : ''}`}
                      onClick={() => setUpiModalTab('qr')}
                    >
                      📷 Scan Dynamic QR Code
                    </button>
                    <button
                      type="button"
                      className={`${ck.upiTab} ${upiModalTab === 'apps' ? ck.active : ''}`}
                      onClick={() => setUpiModalTab('apps')}
                    >
                      🚀 Open Installed UPI App
                    </button>
                  </div>

                  {/* Tab 1: Dynamic QR Code */}
                  {upiModalTab === 'qr' && (
                    <div className={ck.qrContainer}>
                      <div style={{ padding: 12, background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0' }}>
                        <QRCodeSVG value={dynamicUpiUri} size={200} level="M" />
                      </div>
                      <div className={ck.amountBadge}>₹{grandTotal.toFixed(2)}</div>
                      <div style={{ fontSize: 13, color: '#64748b', marginTop: 10, textAlign: 'center' }}>
                        Scan with PhonePe, BHIM, Google Pay, or Paytm. Payee and exact total are already embedded!
                      </div>
                      <div style={{ fontSize: 12, color: '#7c3aed', marginTop: 4 }}>
                        Reference Code: <strong style={{ fontFamily: 'monospace' }}>{ensureUpiRef()}</strong>
                      </div>
                    </div>
                  )}

                  {/* Tab 2: 1-Tap App Launcher */}
                  {upiModalTab === 'apps' && (
                    <div>
                      <p style={{ fontSize: 13, color: '#64748b', marginBottom: 14 }}>
                        Tap your preferred UPI app to open and pay instantly:
                      </p>
                      <div className={ck.upiAppList}>
                        {WEB_UPI_APPS.map((app) => (
                          <button
                            key={app.name}
                            type="button"
                            className={ck.upiAppBtn}
                            onClick={() => handleLaunchUpiApp(app.scheme, app.name)}
                          >
                            <span style={{ fontSize: 22 }}>{app.icon}</span>
                            <div>
                              <div style={{ fontWeight: 700, fontSize: 14 }}>Pay via {app.name}</div>
                              <div style={{ fontSize: 11, color: '#64748b' }}>Exact ₹{grandTotal.toFixed(2)}</div>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 1-Tap Payment Confirmation Card */}
                  <div className={ck.confirmCard}>
                    <div>
                      <div style={{ fontWeight: 700, color: '#065f46', fontSize: 14 }}>
                        {upiPaymentConfirmed ? '✓ Payment Confirmed' : 'Completed your payment in the UPI app?'}
                      </div>
                      <div style={{ fontSize: 12, color: '#047857', marginTop: 2 }}>
                        {upiPaymentConfirmed
                          ? `Ready to place order with reference ${ensureUpiRef()}`
                          : 'Tap below to mark payment done. No screenshot required!'}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setUpiPaymentConfirmed(!upiPaymentConfirmed)}
                      style={{
                        background: upiPaymentConfirmed ? '#10b981' : '#047857',
                        color: '#fff',
                        padding: '8px 18px',
                        borderRadius: 8,
                        fontWeight: 700,
                        fontSize: 13,
                        border: 'none',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {upiPaymentConfirmed ? '✓ Confirmed' : '✓ I Have Paid'}
                    </button>
                  </div>
                </div>
              )}

              {/* Stepper Footer */}
              <div className={ck.stepFooter}>
                <button type="button" className={ck.btnSecondary} onClick={() => setCheckoutStep(2)}>
                  ← Back to Delivery Slot
                </button>
                <button type="button" className={ck.btnPrimary} onClick={() => setCheckoutStep(4)}>
                  Review Order →
                </button>
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════════════════════
             STEP 4: Review & Place Order
             ═══════════════════════════════════════════════════════ */}
          {checkoutStep === 4 && (
            <div className={ck.stepContentBox}>
              <h2 className={ck.stepHeading}>
                <span>📋</span>
                <span>Review Your Order</span>
              </h2>
              <p className={ck.stepSubheading}>Please review your order details before placing</p>

              {/* Address Summary */}
              <div className={ck.reviewBox}>
                <div className={ck.reviewBoxHeader}>
                  <span className={ck.reviewBoxTitle}>📍 Delivery Address</span>
                  <button type="button" className={ck.reviewChangeBtn} onClick={() => setCheckoutStep(1)}>
                    Change
                  </button>
                </div>
                <div style={{ fontSize: 14, color: '#334155', lineHeight: 1.5 }}>
                  <strong>{contactName || selectedAddress.name || user?.name}</strong>
                  {contactPhone ? ` • ${contactPhone}` : ''}
                  <br />
                  {selectedAddress.street}
                  {selectedAddress.addressLine2 ? `, ${selectedAddress.addressLine2}` : ''}
                  <br />
                  {selectedAddress.city}, {selectedAddress.state} — {selectedAddress.zipCode}
                </div>
              </div>

              {/* Delivery Slot Summary */}
              <div className={ck.reviewBox}>
                <div className={ck.reviewBoxHeader}>
                  <span className={ck.reviewBoxTitle}>🚚 Delivery Option</span>
                  <button type="button" className={ck.reviewChangeBtn} onClick={() => setCheckoutStep(2)}>
                    Change
                  </button>
                </div>
                <div style={{ fontSize: 14, color: '#334155' }}>
                  {activeMode === 'pan_india' ? (
                    'Pan-India Courier Delivery (3–5 business days)'
                  ) : selectedDeliveryType === 'urgent' ? (
                    '⚡ Urgent Delivery (60–90 mins)'
                  ) : (
                    <>
                      Standard Delivery on <strong>{selectedSlotDate || 'Scheduled date'}</strong>
                      {selectedSlot ? ` (${selectedSlot.isFullDay ? 'Anytime' : `${selectedSlot.startTime} – ${selectedSlot.endTime}`})` : ''}
                    </>
                  )}
                </div>
              </div>

              {/* Payment Summary */}
              <div className={ck.reviewBox}>
                <div className={ck.reviewBoxHeader}>
                  <span className={ck.reviewBoxTitle}>💳 Payment Method</span>
                  <button type="button" className={ck.reviewChangeBtn} onClick={() => setCheckoutStep(3)}>
                    Change
                  </button>
                </div>
                <div style={{ fontSize: 14, color: '#334155' }}>
                  {paymentMethod === 'cod' ? (
                    'Cash on Delivery'
                  ) : paymentMethod === 'credit' ? (
                    'B2B Credit Account'
                  ) : (
                    <>
                      Direct UPI {upiAppUsed ? `(${upiAppUsed})` : ''} • Ref: <strong>{ensureUpiRef()}</strong>
                      {upiPaymentConfirmed && <span style={{ color: '#059669', marginLeft: 8 }}>✓ Confirmed</span>}
                    </>
                  )}
                </div>
              </div>

              {/* Printed bill checkbox */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14, color: '#334155' }}>
                  <input
                    type="checkbox"
                    checked={printedBill}
                    onChange={(e) => setPrintedBill(e.target.checked)}
                    style={{ width: 16, height: 16 }}
                  />
                  <span>I would like a printed paper invoice during delivery</span>
                </label>
              </div>

              {/* Order Notes */}
              <div style={{ marginBottom: 20 }}>
                <label className={ck.formLabel}>Order Notes (Optional)</label>
                <input
                  type="text"
                  className={ck.formInput}
                  placeholder="Special instructions for delivery (e.g. call upon arrival)"
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                />
              </div>

              {/* Final Place Order Action */}
              <div className={ck.stepFooter}>
                <button type="button" className={ck.btnSecondary} onClick={() => setCheckoutStep(3)}>
                  ← Back to Payment
                </button>
                <button
                  type="button"
                  className={ck.btnPrimary}
                  disabled={placingOrder}
                  onClick={handlePlaceOrder}
                  style={{ padding: '14px 36px', fontSize: 16 }}
                >
                  {placingOrder ? 'Placing Order...' : `Place Order (₹${grandTotal.toFixed(2)})`}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════════
           RIGHT COLUMN: Sticky Order Summary & Promos
           ═══════════════════════════════════════════════════════ */}
        <aside className={ck.summarySidebar}>
          <div className={ck.summaryCard}>
            <h3 className={ck.summaryTitle}>Order Summary ({cart?.items?.length || 0} items)</h3>

            {/* Cart Items List */}
            <div className={ck.itemList}>
              {cart?.items?.map((item: any) => (
                <div key={item._id || item.id} className={ck.itemRow}>
                  <img
                    src={getImageUrl(item.product?.image || item.product?.images?.[0]) || ''}
                    alt={item.product?.name || 'Item'}
                    className={ck.itemImg}
                  />
                  <div className={ck.itemInfo}>
                    <div className={ck.itemName}>{item.product?.name || 'Product'}</div>
                    <div className={ck.itemQtyPrice}>
                      Qty: {item.quantity} × ₹{Number(item.price || 0).toFixed(2)}
                    </div>
                  </div>
                  <div className={ck.itemSubtotal}>
                    ₹{((Number(item.price) || 0) * (Number(item.quantity) || 1)).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>

            {/* Promo Code Input */}
            <div className={ck.promoBox}>
              {!appliedCoupon ? (
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="text"
                    placeholder="Promo code"
                    className={ck.formInput}
                    style={{ textTransform: 'uppercase', padding: '8px 12px' }}
                    value={couponInput}
                    onChange={(e) => {
                      setCouponInput(e.target.value);
                      setCouponError('');
                    }}
                  />
                  <button
                    type="button"
                    className={ck.btnSecondary}
                    style={{ padding: '8px 16px', fontSize: 13 }}
                    onClick={async () => {
                      if (!couponInput) return;
                      setVerifyingCoupon(true);
                      try {
                        const res = await api.post('/coupons/validate', {
                          code: couponInput.trim().toUpperCase(),
                          cartTotal: cartSubtotal,
                        });
                        setAppliedCoupon({ code: couponInput.trim().toUpperCase(), discount: res.data.discount || 0 });
                        toast.success(`Coupon applied! Save ₹${res.data.discount}`);
                      } catch (e: any) {
                        setCouponError(e?.response?.data?.detail || 'Invalid coupon code');
                      } finally {
                        setVerifyingCoupon(false);
                      }
                    }}
                  >
                    Apply
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#ecfdf5', padding: '8px 12px', borderRadius: 8 }}>
                  <span style={{ fontSize: 13, color: '#047857', fontWeight: 600 }}>
                    🏷️ &quot;{appliedCoupon.code}&quot; applied (-₹{appliedCoupon.discount.toFixed(2)})
                  </span>
                  <button
                    type="button"
                    onClick={() => setAppliedCoupon(null)}
                    style={{ background: 'none', border: 'none', color: '#dc2626', fontSize: 12, cursor: 'pointer', fontWeight: 700 }}
                  >
                    Remove
                  </button>
                </div>
              )}
              {couponError && <div style={{ color: '#dc2626', fontSize: 12, marginTop: 4 }}>{couponError}</div>}
            </div>

            {/* Price Calculations */}
            <div className={ck.calcRow}>
              <span>Items Subtotal</span>
              <span>₹{cartSubtotal.toFixed(2)}</span>
            </div>

            {couponDiscountAmount > 0 && (
              <div className={ck.calcRow} style={{ color: '#059669', fontWeight: 600 }}>
                <span>Coupon Discount</span>
                <span>-₹{couponDiscountAmount.toFixed(2)}</span>
              </div>
            )}

            {referralDiscountAmount > 0 && (
              <div className={ck.calcRow} style={{ color: '#059669', fontWeight: 600 }}>
                <span>Referral Discount</span>
                <span>-₹{referralDiscountAmount.toFixed(2)}</span>
              </div>
            )}

            <div className={ck.calcRow}>
              <span>Delivery Charges</span>
              <span>{deliveryFee > 0 ? `₹${deliveryFee.toFixed(2)}` : 'FREE'}</span>
            </div>

            <div className={ck.calcTotal}>
              <span>Total Payable</span>
              <span>₹{grandTotal.toFixed(2)}</span>
            </div>
          </div>
        </aside>
      </main>

      {/* ── Add Address Modal ── */}
      {showAddressModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 16,
          }}
          onClick={() => setShowAddressModal(false)}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 16,
              maxWidth: 540,
              width: '100%',
              padding: 24,
              boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>Add New Address</h3>
              <button
                type="button"
                onClick={() => setShowAddressModal(false)}
                style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#64748b' }}
              >
                ✕
              </button>
            </div>

            <div className={ck.formGroup}>
              <label className={ck.formLabel}>Recipient Name</label>
              <input
                type="text"
                className={ck.formInput}
                placeholder="Full name"
                value={newAddress.name}
                onChange={(e) => setNewAddress({ ...newAddress, name: e.target.value })}
              />
            </div>

            <div className={ck.formGroup}>
              <label className={ck.formLabel}>Street Address *</label>
              <input
                type="text"
                className={ck.formInput}
                placeholder="House/flat no, street, locality"
                value={newAddress.street}
                onChange={(e) => setNewAddress({ ...newAddress, street: e.target.value })}
              />
            </div>

            <div className={ck.formRow}>
              <div className={ck.formGroup}>
                <label className={ck.formLabel}>Postal Pin Code *</label>
                <input
                  type="text"
                  className={ck.formInput}
                  placeholder="6-digit pincode"
                  maxLength={6}
                  value={newAddress.zipCode}
                  onChange={(e) => {
                    const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                    setNewAddress((prev) => ({ ...prev, zipCode: val }));
                    if (val.length === 6) fetchAddressByPincode(val, true);
                  }}
                />
              </div>
              <div className={ck.formGroup}>
                <label className={ck.formLabel}>City *</label>
                <input
                  type="text"
                  className={ck.formInput}
                  placeholder="City"
                  value={newAddress.city}
                  onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })}
                />
              </div>
            </div>

            <div className={ck.formRow}>
              <div className={ck.formGroup}>
                <label className={ck.formLabel}>State *</label>
                <input
                  type="text"
                  className={ck.formInput}
                  placeholder="State"
                  value={newAddress.state}
                  onChange={(e) => setNewAddress({ ...newAddress, state: e.target.value })}
                />
              </div>
              <div className={ck.formGroup}>
                <label className={ck.formLabel}>District</label>
                <input
                  type="text"
                  className={ck.formInput}
                  placeholder="District"
                  value={newAddress.district}
                  onChange={(e) => setNewAddress({ ...newAddress, district: e.target.value })}
                />
              </div>
            </div>

            {user && (
              <div style={{ marginTop: 10, marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: '#334155' }}>
                  <input
                    type="checkbox"
                    checked={newAddress.saveToProfile}
                    onChange={(e) => setNewAddress({ ...newAddress, saveToProfile: e.target.checked })}
                  />
                  <span>Save this address to my profile for future orders</span>
                </label>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button type="button" className={ck.btnSecondary} onClick={() => setShowAddressModal(false)}>
                Cancel
              </button>
              <button type="button" className={ck.btnPrimary} onClick={handleSaveNewAddress}>
                Save &amp; Use Address
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Sign In / Quick Account Modal ── */}
      {showSignInModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 16,
          }}
          onClick={() => setShowSignInModal(false)}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 16,
              maxWidth: 420,
              width: '100%',
              padding: 24,
              boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>
                {isExistingAccount ? 'Sign In' : isExistingAccount === false ? 'Create Account' : 'Account Verification'}
              </h3>
              <button
                type="button"
                onClick={() => setShowSignInModal(false)}
                style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#64748b' }}
              >
                ✕
              </button>
            </div>

            <div className={ck.formGroup}>
              <label className={ck.formLabel}>Mobile Number</label>
              <input
                type="tel"
                className={ck.formInput}
                placeholder="10-digit mobile number"
                maxLength={10}
                value={contactPhone}
                onChange={(e) => {
                  setContactPhone(e.target.value.replace(/\D/g, ''));
                  setIsExistingAccount(null);
                  setOtpSent(false);
                }}
              />
            </div>

            {isExistingAccount === null ? (
              <button
                type="button"
                className={ck.btnPrimary}
                style={{ width: '100%' }}
                disabled={authBusy || contactPhone.length < 10}
                onClick={handleCheckPhone}
              >
                {authBusy ? 'Checking...' : 'Continue'}
              </button>
            ) : isExistingAccount ? (
              <div>
                <div className={ck.formGroup}>
                  <label className={ck.formLabel}>Password</label>
                  <input
                    type="password"
                    className={ck.formInput}
                    placeholder="Enter your password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                  />
                </div>
                <button
                  type="button"
                  className={ck.btnPrimary}
                  style={{ width: '100%' }}
                  disabled={authBusy}
                  onClick={handleQuickLogin}
                >
                  {authBusy ? 'Logging in...' : 'Log In & Continue'}
                </button>
              </div>
            ) : (
              <div>
                {otpSent && (
                  <div className={ck.formGroup}>
                    <label className={ck.formLabel}>Enter SMS OTP</label>
                    <input
                      type="text"
                      className={ck.formInput}
                      placeholder="6-digit OTP"
                      value={otpValue}
                      onChange={(e) => setOtpValue(e.target.value)}
                    />
                  </div>
                )}
                <div className={ck.formGroup}>
                  <label className={ck.formLabel}>Set Account Password</label>
                  <input
                    type="password"
                    className={ck.formInput}
                    placeholder="Min 6 characters"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                  />
                </div>
                <button
                  type="button"
                  className={ck.btnPrimary}
                  style={{ width: '100%' }}
                  disabled={authBusy}
                  onClick={handleQuickRegister}
                >
                  {authBusy ? 'Creating account...' : 'Create Account & Continue'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
