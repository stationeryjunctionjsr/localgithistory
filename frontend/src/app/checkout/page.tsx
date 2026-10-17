'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { toast } from 'react-toastify';
import { QRCodeSVG } from 'qrcode.react';

import { useAuth } from '@/context/AuthContext';
import { usePincode } from '@/context/PincodeContext';
import { useCartStore } from '@/store/cartStore';
import api from '@/utils/api';
import { getImageUrl } from '@/utils/imageUrl';
import { trackEcommerceEvent } from '@/utils/analytics';
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

  // Stepper state: 1 = Address, 2 = Delivery Slot, 3 = Payment, 4 = Review
  const [checkoutStep, setCheckoutStep] = useState<1 | 2 | 3 | 4>(1);

  // ── Auth-in-Checkout State (Users MUST be logged in to order) ──
  const [authPhone, setAuthPhone] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authConfirmPassword, setAuthConfirmPassword] = useState('');
  const [authBusy, setAuthBusy] = useState(false);
  const [authPhoneChecked, setAuthPhoneChecked] = useState(false);
  const [authIsExisting, setAuthIsExisting] = useState(false);
  const [authOtpSent, setAuthOtpSent] = useState(false);
  const [authOtp, setAuthOtp] = useState('');
  const [authOtpVerified, setAuthOtpVerified] = useState(false);
  const [authOtpToken, setAuthOtpToken] = useState('');
  const [authCanResend, setAuthCanResend] = useState(false);

  // ── Delivery Address State (Myself vs Someone Else) ──
  const [deliverTo, setDeliverTo] = useState<'myself' | 'someone_else'>('myself');
  const [selectedAddress, setSelectedAddress] = useState<any>({
    name: '',
    phone: '',
    street: '',
    city: '',
    state: '',
    district: '',
    zipCode: '',
    country: 'India',
    addressLine2: '',
    landmark: '',
    deliverTo: 'myself',
  });

  // Add Address Modal state
  const [showAddressModal, setShowAddressModal] = useState(false);
  const [newAddress, setNewAddress] = useState({
    name: '',
    phone: '',
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
  const [upiAppLaunched, setUpiAppLaunched] = useState(false);   // true once any UPI app button is tapped
  const [upiConfirmCountdown, setUpiConfirmCountdown] = useState(0); // counts down from 5 after app launch
  const [upiTxnRef, setUpiTxnRef] = useState('');
  const [upiAppUsed, setUpiAppUsed] = useState('');
  // On mobile the QR code can't be scanned on the same device — default to app deep-links.
  // On desktop, QR is the right default (user scans with their phone).
  const [upiModalTab, setUpiModalTab] = useState<'qr' | 'apps'>('qr');
  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 768) {
      setUpiModalTab('apps');
    }
  }, []);

  // Tick the confirmation countdown down to 0 (started when user launches a UPI app)
  useEffect(() => {
    if (upiConfirmCountdown <= 0) return;
    const t = setTimeout(() => setUpiConfirmCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [upiConfirmCountdown]);

  const [upiUtr, setUpiUtr] = useState('');

  // Order notes & options
  const [printedBill, setPrintedBill] = useState(false);
  const [orderNotes, setOrderNotes] = useState('');
  const [placingOrder, setPlacingOrder] = useState(false);

  // Stable idempotency key for the current checkout session.
  // Generated once at mount (not on each click) so that if the network drops
  // and the user clicks "Place Order" again, the same key is sent and the
  // backend deduplicates the request instead of creating a duplicate order.
  // Reset to a fresh UUID after a successful order submission.
  const orderIdempotencyKey = useRef<string>(
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `chk-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  );

  // Coupons & Referrals
  const [couponInput, setCouponInput] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState<{ code: string; discount: number } | null>(null);
  const [couponError, setCouponError] = useState('');
  const [verifyingCoupon, setVerifyingCoupon] = useState(false);

  const [appliedReferralCode, setAppliedReferralCode] = useState<string | null>(null);
  const [referralDiscountInfo, setReferralDiscountInfo] = useState<any>(null);

  // Auto-fill from localStorage if user had previously typed phone
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const lastPhone = localStorage.getItem('sj_last_auth_phone');
        if (lastPhone && !authPhone) setAuthPhone(lastPhone);
      } catch {}
    }
  }, []);

  // ── 1. Consolidate & Manage Multiple Saved Addresses ──
  const userAddresses = useMemo(() => {
    const list: any[] = [];
    if (user?.address && (user.address.street || user.address.pincode || user.address.zipCode)) {
      list.push({
        ...user.address,
        zipCode: user.address.zipCode || user.address.pincode || '',
        is_primary: true,
        name: user.address.name || user.name || '',
        deliverTo: 'myself',
      });
    }
    if (Array.isArray(user?.savedAddresses)) {
      user.savedAddresses.forEach((sa: any) => {
        const zip = sa.zipCode || sa.pincode || '';
        const isDup = list.some(
          (a) =>
            a.street === sa.street &&
            (a.zipCode || a.pincode) === zip
        );
        if (!isDup) {
          list.push({
            ...sa,
            zipCode: zip,
            is_primary: false,
            name: sa.name || user?.name || '',
            deliverTo: sa.deliverTo || 'myself',
          });
        }
      });
    }
    return list;
  }, [user]);

  // Auto-select primary address when logged in and mode is 'myself'
  useEffect(() => {
    if (userAddresses.length > 0 && !selectedAddress.street && deliverTo === 'myself') {
      const primary = userAddresses.find((a) => a.is_primary) || userAddresses[0];
      handleSelectAddress(primary);
    }
  }, [userAddresses, deliverTo]);

  const handleSelectAddress = (addr: any) => {
    const zip = addr.zipCode || addr.pincode || '';
    const updated = {
      name: addr.name || (deliverTo === 'myself' ? (user?.name || '') : ''),
      phone: addr.phone || '',
      street: addr.street || '',
      city: addr.city || '',
      state: addr.state || '',
      district: addr.district || '',
      zipCode: zip,
      country: addr.country || 'India',
      addressLine2: addr.addressLine2 || '',
      landmark: addr.landmark || '',
      deliverTo: addr.deliverTo || deliverTo,
    };
    setSelectedAddress(updated);
    if (zip.length === 6) {
      checkServiceability(zip);
    }
  };

  const handleDeliverToChange = (mode: 'myself' | 'someone_else') => {
    setDeliverTo(mode);
    if (mode === 'myself') {
      // Auto-populate default address and user name
      const primary = userAddresses.find((a) => a.is_primary) || userAddresses[0];
      if (primary) {
        handleSelectAddress({
          ...primary,
          name: user?.name || primary.name || '',
          deliverTo: 'myself',
        });
      } else {
        setNewAddress((prev) => ({
          ...prev,
          name: user?.name || '',
          phone: user?.phone || '',
        }));
      }
    } else {
      // Mode is 'someone_else'
      setNewAddress((prev) => ({
        ...prev,
        name: '',
        phone: '',
      }));
      const someoneAddr = userAddresses.find((a) => a.deliverTo === 'someone_else');
      if (someoneAddr) {
        handleSelectAddress(someoneAddr);
      } else {
        setSelectedAddress({
          name: '',
          phone: '',
          street: '',
          city: '',
          state: '',
          district: '',
          zipCode: '',
          country: 'India',
          addressLine2: '',
          landmark: '',
          deliverTo: 'someone_else',
        });
        setShowAddressModal(true);
      }
    }
  };

  const openAddAddressModal = () => {
    setNewAddress({
      name: deliverTo === 'myself' ? (user?.name || '') : '',
      phone: deliverTo === 'myself' ? (user?.phone || '') : '',
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
    setShowAddressModal(true);
  };

  // ── 2. India Post Pincode Lookup ──
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

  // ── 3. Check Pincode Serviceability & Delivery Slots ──
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
      // Auto-select "anytime" as default
      setSelectedSlot({ slotId: 'anytime', isFullDay: true, isUrgent: false });
    } catch {
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  // Calculate delivery charge
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

  // ── 4. Save New Address & Persist to MySQL Profile ──
  const handleSaveNewAddress = async () => {
    if (!newAddress.street || !newAddress.city || !newAddress.state || !newAddress.zipCode) {
      toast.error('Please fill in Street, City, State, and Pincode');
      return;
    }
    if (!newAddress.name?.trim()) {
      toast.error(deliverTo === 'myself' ? 'Please enter your name' : "Please enter recipient's name");
      return;
    }

    const addrToUse = {
      ...newAddress,
      name: newAddress.name.trim(),
      deliverTo: deliverTo,
    };

    handleSelectAddress(addrToUse);
    setShowAddressModal(false);

    // If 'myself' and user's profile does not have a name yet, save it to their profile!
    if (deliverTo === 'myself' && user?.id && !user?.name && addrToUse.name) {
      try {
        await api.put(`/users/${user.id}`, { name: addrToUse.name });
        if (fetchUser) await fetchUser();
      } catch (err) {
        console.warn('Could not update profile name:', err);
      }
    }

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

  // ── 5. Price Calculations ──
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

  // ── 6. Direct NPCI UPI Flow (0% Commission) ──
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
    const ref = ensureUpiRef();
    setUpiAppUsed(appName);
    setUpiAppLaunched(true);
    setUpiPaymentConfirmed(false); // reset in case user is retrying
    // Disable "I Have Paid" for 5 seconds so the user can't accidentally
    // confirm before they've even seen the payment screen in the UPI app.
    setUpiConfirmCountdown(5);
    const deepLink = `${scheme}?pa=stationeryjunction@icici&pn=Stationery%20Junction&am=${grandTotal.toFixed(2)}&cu=INR&tr=${ref}&tn=Order%20${ref}`;
    window.location.href = deepLink;
  };

  // ── 7. Login & Registration Flow (Required to Order) ──
  const handleCheckPhone = async () => {
    const raw = authPhone.trim();
    const isEmail = raw.includes('@');
    let clean = raw;
    if (!isEmail) {
      clean = raw.replace(/\D/g, '');
      if (clean.length < 10) {
        toast.error('Enter a valid 10-digit mobile number or email');
        return;
      }
    } else {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw)) {
        toast.error('Enter a valid email address');
        return;
      }
    }

    setAuthBusy(true);
    try {
      const res = await api.post('/auth/check-phone', { phone: clean });
      setAuthIsExisting(res.data.exists);
      setAuthPhoneChecked(true);

      // Cache phone in localStorage for browser autofill ease
      try {
        localStorage.setItem('sj_last_auth_phone', clean);
      } catch {}

      if (!res.data.exists && !isEmail) {
        // Send OTP for new mobile users
        handleSendOtp(clean);
      }
    } catch {
      toast.error('Could not verify phone. Please try again.');
    } finally {
      setAuthBusy(false);
    }
  };

  const handleSendOtp = async (cleanPhone?: string) => {
    const phone = cleanPhone || authPhone.replace(/\D/g, '');
    setAuthBusy(true);
    try {
      await api.post('/auth/send-otp', { phone, purpose: 'register' });
      setAuthOtpSent(true);
      setAuthCanResend(false);
      setTimeout(() => setAuthCanResend(true), 30000);
      toast.success('OTP sent to your mobile');
    } catch {
      toast.error('Failed to send OTP');
    } finally {
      setAuthBusy(false);
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
      await api.post('/auth/verify-otp', { phone: clean, otp: authOtp });
      setAuthOtpVerified(true);
      toast.success('Phone verified');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Invalid OTP');
    } finally {
      setAuthBusy(false);
    }
  };

  const handleAuthLogin = async () => {
    if (!authPassword) {
      toast.error('Enter your password');
      return;
    }
    setAuthBusy(true);
    try {
      await login(authPhone, authPassword);
      toast.success('Logged in successfully!');
      if (fetchCart) await fetchCart();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Invalid credentials');
    } finally {
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
      const payload: any = {
        phone: clean,
        password: authPassword,
        role: 'customer',
        otp: authOtp,
      };
      if (authOtpToken) payload.msg91Token = authOtpToken;

      const res = await api.post('/auth/register', payload);
      const { token, refreshToken, sessionId, user: userData } = res.data;
      await loginWithTokens({ token, refreshToken, sessionId, user: userData });
      toast.success('Account created successfully!');
      if (fetchCart) await fetchCart();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Registration failed');
    } finally {
      setAuthBusy(false);
    }
  };

  // ── 8. Place Order (Strictly Authenticated) ──
  const handlePlaceOrder = async () => {
    if (!user) {
      toast.error('You must be signed in to place an order');
      return;
    }

    if (!selectedAddress.street || !selectedAddress.zipCode) {
      toast.error('Please select or add a delivery address');
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

      const fullStreet = [
        selectedAddress.street,
        selectedAddress.addressLine2,
        selectedAddress.landmark ? `Landmark: ${selectedAddress.landmark}` : '',
      ]
        .filter(Boolean)
        .join(', ');

      const cleanAddress = {
        name: selectedAddress.name || (deliverTo === 'myself' ? (user?.name || '') : ''),
        phone: selectedAddress.phone || user?.phone || '',
        street: fullStreet || selectedAddress.street,
        city: selectedAddress.city,
        state: selectedAddress.state,
        district: selectedAddress.district || '',
        zipCode: selectedAddress.zipCode || selectedAddress.pincode || '',
        country: selectedAddress.country || 'India',
        address: fullStreet || selectedAddress.street,
      };

      const payload = {
        shippingAddress: cleanAddress,
        billingAddress: cleanAddress,
        paymentMethod: paymentMethod,
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

      const res = await api.post('/orders', payload, {
        headers: { 'Idempotency-Key': orderIdempotencyKey.current },
      });
      const createdOrder = res.data;

      // Rotate the key immediately after a confirmed success so that a
      // subsequent order in the same checkout session gets a fresh key.
      orderIdempotencyKey.current =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : `chk-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

      // Track purchase conversion event for GA4 / GTM
      trackEcommerceEvent('purchase', {
        transaction_id: createdOrder?.orderNumber || createdOrder?.id || Date.now().toString(),
        value: grandTotal,
        currency: 'INR',
        items: (cart?.items || []).map((item: any) => ({
          item_id: item.product?.id || item.product_id,
          item_name: item.product?.name || item.name,
          price: item.price,
          quantity: item.quantity,
        })),
      });

      toast.success('Order placed successfully!');
      if (fetchCart) await fetchCart();
      router.push('/customer/orders');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || 'Failed to place order';
      toast.error(msg);
    } finally {
      setPlacingOrder(false);
    }
  };

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

      {/* ── Main Layout ── */}
      <main className={ck.checkoutMain}>
        <div>
          {/* ═══════════════════════════════════════════════════════
             AUTH GATE: Users must be logged in to order (No guest delivery)
             ═══════════════════════════════════════════════════════ */}
          {!user ? (
            <div className={ck.authBox}>
              <h2 className={ck.authTitle}>
                <span>🔐</span>
                <span>Sign in to complete order</span>
              </h2>
              <p className={ck.authSubtitle}>
                We deliver to registered accounts. Please sign in or create an account to proceed to checkout.
              </p>

              {/* Step 0A: Enter mobile or email */}
              <div className={ck.formGroup}>
                <label className={ck.formLabel}>Mobile Number or Email</label>
                <input
                  type="text"
                  className={ck.formInput}
                  placeholder="10-digit mobile number or email"
                  autoComplete="username tel"
                  value={authPhone}
                  onChange={(e) => {
                    setAuthPhone(e.target.value);
                    setAuthPhoneChecked(false);
                    setAuthOtpSent(false);
                    setAuthOtpVerified(false);
                  }}
                />
              </div>

              {!authPhoneChecked ? (
                <button
                  type="button"
                  className={ck.btnPrimary}
                  style={{ width: '100%' }}
                  disabled={authBusy || !authPhone.trim()}
                  onClick={handleCheckPhone}
                >
                  {authBusy ? 'Checking...' : 'Continue to Checkout →'}
                </button>
              ) : authIsExisting ? (
                /* Step 0B: Existing User - Password Login */
                <div>
                  <div className={ck.formGroup}>
                    <label className={ck.formLabel}>Password</label>
                    <input
                      type="password"
                      className={ck.formInput}
                      placeholder="Enter your password"
                      autoComplete="current-password"
                      value={authPassword}
                      onChange={(e) => setAuthPassword(e.target.value)}
                    />
                  </div>
                  <button
                    type="button"
                    className={ck.btnPrimary}
                    style={{ width: '100%', marginBottom: 12 }}
                    disabled={authBusy}
                    onClick={handleAuthLogin}
                  >
                    {authBusy ? 'Logging in...' : 'Log In & Continue'}
                  </button>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <button
                      type="button"
                      onClick={() => setAuthPhoneChecked(false)}
                      style={{ fontSize: 13, color: '#64748b', background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                      ← Use different number
                    </button>
                    <Link
                      href="/login"
                      target="_blank"
                      style={{ fontSize: 13, color: '#2563eb', textDecoration: 'none' }}
                    >
                      Forgot password?
                    </Link>
                  </div>
                </div>
              ) : (
                /* Step 0C: New User - Quick Registration (Phone + OTP + Password) */
                <div>
                  {/* OTP Verification */}
                  <div className={ck.formGroup}>
                    <label className={ck.formLabel}>SMS OTP Verification *</label>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input
                        type="text"
                        className={ck.formInput}
                        placeholder="Enter 6-digit OTP"
                        maxLength={6}
                        value={authOtp}
                        onChange={(e) => setAuthOtp(e.target.value)}
                        disabled={!authOtpSent || authOtpVerified}
                        style={{ flex: 1 }}
                      />
                      {!authOtpSent ? (
                        <button
                          type="button"
                          className={ck.btnSecondary}
                          style={{ whiteSpace: 'nowrap' }}
                          disabled={authBusy}
                          onClick={() => handleSendOtp()}
                        >
                          Send OTP
                        </button>
                      ) : !authOtpVerified ? (
                        <button
                          type="button"
                          className={ck.btnPrimary}
                          style={{ whiteSpace: 'nowrap' }}
                          disabled={authBusy || !authOtp}
                          onClick={handleVerifyOtp}
                        >
                          Verify
                        </button>
                      ) : (
                        <span style={{ padding: '10px 16px', background: '#ecfdf5', color: '#059669', borderRadius: 8, fontWeight: 700 }}>
                          ✓ Verified
                        </span>
                      )}
                    </div>
                  </div>

                  {authOtpVerified && (
                    <>
                      <div className={ck.formRow}>
                        <div className={ck.formGroup}>
                          <label className={ck.formLabel}>Set Password *</label>
                          <input
                            type="password"
                            className={ck.formInput}
                            placeholder="Min 6 characters"
                            autoComplete="new-password"
                            value={authPassword}
                            onChange={(e) => setAuthPassword(e.target.value)}
                          />
                        </div>
                        <div className={ck.formGroup}>
                          <label className={ck.formLabel}>Confirm Password *</label>
                          <input
                            type="password"
                            className={ck.formInput}
                            placeholder="Re-enter password"
                            autoComplete="new-password"
                            value={authConfirmPassword}
                            onChange={(e) => setAuthConfirmPassword(e.target.value)}
                          />
                        </div>
                      </div>
                      <button
                        type="button"
                        className={ck.btnPrimary}
                        style={{ width: '100%', marginTop: 8 }}
                        disabled={authBusy}
                        onClick={handleAuthRegister}
                      >
                        {authBusy ? 'Creating account...' : 'Create Account & Continue'}
                      </button>
                    </>
                  )}

                  <button
                    type="button"
                    onClick={() => setAuthPhoneChecked(false)}
                    style={{ fontSize: 13, color: '#64748b', background: 'none', border: 'none', cursor: 'pointer', marginTop: 14 }}
                  >
                    ← Use different number
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* ═══════════════════════════════════════════════════════
               LOGGED-IN CHECKOUT STEPPER (Steps 1–4)
               ═══════════════════════════════════════════════════════ */
            <>
              {/* Stepper Header */}
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

              {/* ── STEP 1: Delivery Address ── */}
              {checkoutStep === 1 && (
                <div className={ck.stepContentBox}>
                  <h2 className={ck.stepHeading}>
                    <span>📍</span>
                    <span>Select Delivery Address</span>
                  </h2>

                  {/* Delivering To Switcher: Myself vs Someone Else */}
                  <div className={ck.deliveryForBox}>
                    <button
                      type="button"
                      className={`${ck.deliveryForBtn} ${deliverTo === 'myself' ? ck.active : ''}`}
                      onClick={() => handleDeliverToChange('myself')}
                    >
                      <span>👤</span>
                      <span>Myself</span>
                    </button>
                    <button
                      type="button"
                      className={`${ck.deliveryForBtn} ${deliverTo === 'someone_else' ? ck.active : ''}`}
                      onClick={() => handleDeliverToChange('someone_else')}
                    >
                      <span>🎁</span>
                      <span>Someone Else (Gift / Friend)</span>
                    </button>
                  </div>

                  <p className={ck.stepSubheading}>
                    {deliverTo === 'myself' ? (
                      <>
                        Delivering to <strong>{user?.name || 'Yourself'}</strong> ({user?.phone}). Your delivery address:
                      </>
                    ) : (
                      <>
                        Delivering to <strong>Someone Else</strong>. Choose or enter recipient delivery address:
                      </>
                    )}
                  </p>

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
                          <div className={ck.addressName}>
                            {addr.name || (deliverTo === 'myself' ? (user.name || 'Your Address') : 'Recipient')}
                            {addr.phone ? ` • ${addr.phone}` : ''}
                          </div>
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
                    <div className={ck.addNewAddressCard} onClick={openAddAddressModal}>
                      <div className={ck.addNewIcon}>+</div>
                      <div className={ck.addNewLabel}>
                        {deliverTo === 'myself' ? '+ Add New Address' : "+ Add Recipient's Address"}
                      </div>
                    </div>
                  </div>

                  {/* Serviceability Notice */}
                  {selectedAddress.zipCode?.length === 6 && (
                    <div style={{ marginTop: 8, marginBottom: 8 }}>
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
                        pincodeServiceable === false
                      }
                      onClick={() => setCheckoutStep(2)}
                    >
                      Continue to Delivery Slot →
                    </button>
                  </div>
                </div>
              )}

              {/* ── STEP 2: Delivery Slot (in Checkout Step Only) ── */}
              {checkoutStep === 2 && (
                <div className={ck.stepContentBox}>
                  <h2 className={ck.stepHeading}>
                    <span>🚚</span>
                    <span>Delivery Option &amp; Slot</span>
                  </h2>
                  <p className={ck.stepSubheading}>Select when you would like to receive your items</p>

                  {activeMode === 'pan_india' ? (
                    <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 12, padding: 20 }}>
                      <div style={{ fontWeight: 700, color: '#1e40af', fontSize: 15, marginBottom: 4 }}>
                        📦 Pan-India Standard Courier Delivery
                      </div>
                      <div style={{ color: '#3b82f6', fontSize: 13, lineHeight: 1.5 }}>
                        Items dispatched via express surface courier across India. Estimated delivery in 3 to 5 business days. Tracking details sent via SMS.
                      </div>
                    </div>
                  ) : (
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

              {/* ── STEP 3: Payment Method (0% Commission Direct UPI Flow) ── */}
              {checkoutStep === 3 && (
                <div className={ck.stepContentBox}>
                  <h2 className={ck.stepHeading}>
                    <span>💳</span>
                    <span>Payment Method</span>
                  </h2>
                  <p className={ck.stepSubheading}>Choose how you want to pay</p>

                  <div className={ck.paymentGrid}>
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

                      <div className={ck.confirmCard}>
                        <div style={{ flex: 1 }}>
                          <div style={{
                            fontWeight: 700,
                            fontSize: 14,
                            color: upiPaymentConfirmed ? '#065f46' : '#334155',
                          }}>
                            {upiPaymentConfirmed
                              ? '✓ Payment Confirmed'
                              : upiAppLaunched
                              ? `Paid in ${upiAppUsed || 'the UPI app'}? Tap to confirm`
                              : 'Once you've paid, tap to confirm'}
                          </div>
                          <div style={{ fontSize: 12, marginTop: 2, color: upiPaymentConfirmed ? '#047857' : '#64748b' }}>
                            {upiPaymentConfirmed
                              ? `Ref: ${ensureUpiRef()} · Ready to place order`
                              : upiAppLaunched && upiConfirmCountdown > 0
                              ? `Button enables in ${upiConfirmCountdown}s — complete payment first`
                              : 'Works for QR payments too. No screenshot required.'}
                          </div>
                        </div>

                        {/* "I Have Paid" — always present, disabled for 5s after app launch */}
                        {!upiPaymentConfirmed && (
                          <button
                            type="button"
                            disabled={upiConfirmCountdown > 0}
                            onClick={() => setUpiPaymentConfirmed(true)}
                            style={{
                              background: upiConfirmCountdown > 0 ? '#94a3b8' : '#047857',
                              color: '#fff',
                              padding: '8px 18px',
                              borderRadius: 8,
                              fontWeight: 700,
                              fontSize: 13,
                              border: 'none',
                              cursor: upiConfirmCountdown > 0 ? 'not-allowed' : 'pointer',
                              whiteSpace: 'nowrap',
                              flexShrink: 0,
                              transition: 'background 0.3s',
                            }}
                          >
                            {upiConfirmCountdown > 0
                              ? `I Have Paid (${upiConfirmCountdown}s)`
                              : '✓ I Have Paid'}
                          </button>
                        )}
                        {upiPaymentConfirmed && (
                          <span style={{ fontSize: 22, flexShrink: 0 }}>✅</span>
                        )}
                      </div>

                      {/* Retry / try another app — visible after app launched, before confirm */}
                      {upiAppLaunched && !upiPaymentConfirmed && (
                        <div style={{ marginTop: 10, textAlign: 'center' }}>
                          <button
                            type="button"
                            onClick={() => {
                              setUpiAppLaunched(false);
                              setUpiConfirmCountdown(0);
                            }}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#7c3aed',
                              fontSize: 13,
                              fontWeight: 600,
                              cursor: 'pointer',
                              textDecoration: 'underline',
                              padding: 0,
                            }}
                          >
                            ↩ Retry or try another payment method
                          </button>
                        </div>
                      )}

                    </div>
                  )}

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

              {/* ── STEP 4: Review & Place Order ── */}
              {checkoutStep === 4 && (
                <div className={ck.stepContentBox}>
                  <h2 className={ck.stepHeading}>
                    <span>📋</span>
                    <span>Review Your Order</span>
                  </h2>
                  <p className={ck.stepSubheading}>Please review your order details before placing</p>

                  <div className={ck.reviewBox}>
                    <div className={ck.reviewBoxHeader}>
                      <span className={ck.reviewBoxTitle}>📍 Delivery Address</span>
                      <button type="button" className={ck.reviewChangeBtn} onClick={() => setCheckoutStep(1)}>
                        Change
                      </button>
                    </div>
                    <div style={{ fontSize: 14, color: '#334155', lineHeight: 1.5 }}>
                      <strong>{selectedAddress.name || user.name}</strong> • {user.phone}
                      <br />
                      {selectedAddress.street}
                      {selectedAddress.addressLine2 ? `, ${selectedAddress.addressLine2}` : ''}
                      <br />
                      {selectedAddress.city}, {selectedAddress.state} — {selectedAddress.zipCode}
                    </div>
                  </div>

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
            </>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════════
           RIGHT COLUMN: Sticky Order Summary & Promos
           ═══════════════════════════════════════════════════════ */}
        <aside className={ck.summarySidebar}>
          <div className={ck.summaryCard}>
            <h3 className={ck.summaryTitle}>Order Summary ({cart?.items?.length || 0} items)</h3>

            <div className={ck.itemList}>
              {cart?.items?.map((item: any) => (
                <div key={item._id || item.id} className={ck.itemRow}>
                  <Image
                    src={getImageUrl(item.product?.image || item.product?.images?.[0]) || '/placeholder.png'}
                    alt={item.product?.name || 'Item'}
                    width={50}
                    height={50}
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

      {/* ── Mobile Sticky Price Bar (hidden on desktop where sidebar is always visible) ── */}
      <div className={ck.mobilePriceBar}>
        <div className={ck.mobilePriceBarItems}>
          🛒 <span>{cart?.items?.length || 0} item{(cart?.items?.length || 0) !== 1 ? 's' : ''}</span>
        </div>
        <div className={ck.mobilePriceBarTotal}>
          Total: <strong>₹{grandTotal.toFixed(2)}</strong>
        </div>
      </div>

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
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>
                {deliverTo === 'myself' ? 'Add Delivery Address' : "Add Recipient's Address"}
              </h3>
              <button
                type="button"
                onClick={() => setShowAddressModal(false)}
                style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#64748b' }}
              >
                ✕
              </button>
            </div>

            {/* Delivering To Switcher inside Modal */}
            <div className={ck.deliveryForBox} style={{ marginBottom: 16, width: '100%', maxWidth: '100%' }}>
              <button
                type="button"
                className={`${ck.deliveryForBtn} ${deliverTo === 'myself' ? ck.active : ''}`}
                onClick={() => {
                  setDeliverTo('myself');
                  setNewAddress((prev) => ({ ...prev, name: user?.name || '' }));
                }}
              >
                <span>👤</span>
                <span>Myself</span>
              </button>
              <button
                type="button"
                className={`${ck.deliveryForBtn} ${deliverTo === 'someone_else' ? ck.active : ''}`}
                onClick={() => {
                  setDeliverTo('someone_else');
                  setNewAddress((prev) => ({ ...prev, name: '', phone: '' }));
                }}
              >
                <span>🎁</span>
                <span>Someone Else</span>
              </button>
            </div>

            <div className={ck.formGroup}>
              <label className={ck.formLabel}>
                {deliverTo === 'myself' ? 'Your Full Name *' : "Recipient's Full Name *"}
              </label>
              <input
                type="text"
                className={ck.formInput}
                placeholder={deliverTo === 'myself' ? 'Your full name' : "Recipient's full name"}
                autoComplete="name"
                value={newAddress.name}
                onChange={(e) => setNewAddress({ ...newAddress, name: e.target.value })}
              />
            </div>

            {deliverTo === 'someone_else' && (
              <div className={ck.formGroup}>
                <label className={ck.formLabel}>Recipient&apos;s Contact Phone (Optional)</label>
                <input
                  type="tel"
                  className={ck.formInput}
                  placeholder="10-digit mobile number for delivery updates"
                  maxLength={10}
                  value={newAddress.phone || ''}
                  onChange={(e) =>
                    setNewAddress({
                      ...newAddress,
                      phone: e.target.value.replace(/\D/g, '').slice(0, 10),
                    })
                  }
                />
              </div>
            )}

            <div className={ck.formGroup}>
              <label className={ck.formLabel}>Street Address *</label>
              <input
                type="text"
                className={ck.formInput}
                placeholder="House/flat no, street, locality"
                autoComplete="street-address"
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
                  autoComplete="postal-code"
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
                  autoComplete="address-level2"
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
                  autoComplete="address-level1"
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
    </div>
  );
}
