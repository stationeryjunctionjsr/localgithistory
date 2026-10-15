import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Switch,
  KeyboardAvoidingView,
  Platform,
  Image,
  BackHandler,
  Animated,
  AppState,
  AppStateStatus,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as StoreReview from 'expo-store-review';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import * as Clipboard from 'expo-clipboard';
import * as Linking from 'expo-linking';
import api from '../src/api/client';
import { colors, shadows } from '../src/theme';
import Toast from 'react-native-toast-message';
import { useAuth } from '../src/hooks/useAuth';
import SearchablePicker from '../src/components/SearchablePicker';
import { getGuestCart } from '../src/services/guestStore';

// ─── Shared Input ────────────────────────────────────────────────────
const InputField = ({
  label,
  placeholder,
  value,
  onChangeText,
  keyboardType = 'default' as any,
  multiline = false,
  secureTextEntry = false,
  icon,
  error,
  editable = true,
  rightElement,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChangeText: (t: string) => void;
  keyboardType?: any;
  multiline?: boolean;
  secureTextEntry?: boolean;
  icon?: string;
  error?: string;
  editable?: boolean;
  rightElement?: React.ReactNode;
}) => (
  <View className="mb-4">
    <Text className="mb-2 font-medium text-slate-700">{label}</Text>
    <View
      className={`flex-row items-center rounded-xl px-4 py-3 ${error ? 'border border-red-400 bg-red-50' : 'bg-slate-100'}`}
    >
      {icon && <Ionicons name={icon as any} size={18} color={error ? colors.error : '#64748B'} style={{ marginRight: 8 }} />}
      <TextInput
        className={`flex-1 text-slate-800 ${multiline ? 'h-24 pt-0' : ''}`}
        placeholder={placeholder}
        placeholderTextColor="#94A3B8"
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType}
        multiline={multiline}
        textAlignVertical={multiline ? 'top' : 'center'}
        secureTextEntry={secureTextEntry}
        autoCapitalize={keyboardType === 'email-address' ? 'none' : 'sentences'}
        editable={editable}
      />
      {rightElement}
    </View>
    {!!error && <Text className="mt-1 text-xs text-red-500">{error}</Text>}
  </View>
);

// ─── Payment pill ────────────────────────────────────────────────────
const PaymentOption = ({ value, label, icon, currentMethod, onPress }: any) => {
  const active = currentMethod === value;
  return (
    <TouchableOpacity
      className={`flex-1 items-center rounded-2xl border py-4 ${active ? 'border-neutral-900 bg-neutral-900' : 'border-neutral-200 bg-white'}`}
      onPress={() => onPress(value)}
      activeOpacity={0.7}
    >
      <Ionicons name={icon} size={22} color={active ? colors.surface : '#64748B'} />
      <Text className={`mt-1 text-xs font-medium ${active ? 'text-white' : 'text-neutral-500'}`}>
        {label}
      </Text>
    </TouchableOpacity>
  );
};

export interface UpiAppConfig {
  id: string;
  name: string;
  scheme: string;
  bgColor: string;
  textColor: string;
  iconName: any;
  subtext: string;
  badge?: string;
}

export const SUPPORTED_UPI_APPS: UpiAppConfig[] = [
  { id: 'phonepe', name: 'Pay via PhonePe', scheme: 'phonepe://pay', bgColor: '#5f259f', textColor: '#ffffff', iconName: 'flash', subtext: 'Open PhonePe app & pay', badge: 'Popular' },
  { id: 'bhim', name: 'Pay via BHIM', scheme: 'bhim://pay', bgColor: '#005b9f', textColor: '#ffffff', iconName: 'shield-checkmark', subtext: 'Official NPCI BHIM UPI', badge: 'NPCI' },
  { id: 'gpay', name: 'Pay via Google Pay', scheme: 'tez://upi/pay', bgColor: '#1a73e8', textColor: '#ffffff', iconName: 'logo-google', subtext: 'Open Google Pay & pay' },
  { id: 'paytm', name: 'Pay via Paytm', scheme: 'paytmmp://pay', bgColor: '#002970', textColor: '#ffffff', iconName: 'wallet', subtext: 'Open Paytm UPI & pay' },
  { id: 'cred', name: 'Pay via CRED', scheme: 'cred://pay', bgColor: '#111111', textColor: '#ffffff', iconName: 'card', subtext: 'Open CRED app & pay' },
  { id: 'other', name: 'All Other UPI Apps', scheme: 'upi://pay', bgColor: '#1a4d33', textColor: '#ffffff', iconName: 'apps-outline', subtext: 'Choose any installed UPI app', badge: 'All Apps' },
];

// ═════════════════════════════════════════════════════════════════════
export default function Checkout() {
  const router = useRouter();
  const { user, login, loginWithTokens } = useAuth();

  // ─── Steps: 0=auth  1=address  2=payment  3=review ───────────────
  const [step, setStep] = useState(user ? 1 : 0);
  const isValet = user && (user as any).role === 'valet';

  // Step 0 – Auth state
  const [phone, setPhone] = useState('');
  const [phoneChecked, setPhoneChecked] = useState(false);
  const [isExisting, setIsExisting] = useState(false);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);

  // Step 1 – Address
  const [savedAddresses, setSavedAddresses] = useState<any[]>([]);
  const [selectedAddressIdx, setSelectedAddressIdx] = useState<number | null>(null);
  const [showNewAddress, setShowNewAddress] = useState(false);
  const [shipping, setShipping] = useState({
    street: '',
    city: '',
    state: '',
    district: '',
    zipCode: '',
    country: 'India',
    phone: '',
    name: '',
    addressLine2: '',
    landmark: '',
  });
  const [checking, setChecking] = useState(false);
  // Location master data
  const [mobileStates, setMobileStates] = useState<string[]>([]);
  const [mobileDistricts, setMobileDistricts] = useState<string[]>([]);

  // Step 2 – Payment
  const [paymentMethod, setPaymentMethod] = useState<'cod' | 'credit' | 'upi'>('cod');
  const [upiScreenshot, setUpiScreenshot] = useState('');
  const [upiTxnRef, setUpiTxnRef] = useState('');
  const [upiAppUsed, setUpiAppUsed] = useState('');
  const [upiPaymentConfirmed, setUpiPaymentConfirmed] = useState(false);
  const [upiUtr, setUpiUtr] = useState('');
  const [showManualUtr, setShowManualUtr] = useState(false);
  const [showAdvancedUpi, setShowAdvancedUpi] = useState(false);
  const [availableUpiApps, setAvailableUpiApps] = useState<UpiAppConfig[]>(SUPPORTED_UPI_APPS);
  const [detectingUpiApps, setDetectingUpiApps] = useState(false);
  const [printedBill, setPrintedBill] = useState(false);

  // Step 3 – Review
  const [notes, setNotes] = useState('');
  const [placing, setPlacing] = useState(false);
  const [cartItems, setCartItems] = useState<any[]>([]);
  const [cartTotal, setCartTotal] = useState(0);
  const [deliveryCharge, setDeliveryCharge] = useState<number | null>(null);
  const [deliveryChargeInfo, setDeliveryChargeInfo] = useState<any>(null);
  const [fetchingDelivery, setFetchingDelivery] = useState(false);

  const scrollRef = useRef<ScrollView>(null);

  // Coupon / promo code (Step 3)
  const [couponCode, setCouponCode] = useState('');
  const [couponExpanded, setCouponExpanded] = useState(false);
  const [couponLoading, setCouponLoading] = useState(false);
  const [appliedCoupon, setAppliedCoupon] = useState<{
    code: string;
    discountType: string;
    discountValue: number;
    discount: number;
  } | null>(null);
  const [couponError, setCouponError] = useState('');

  // UPI features
  const [upiDetails, setUpiDetails] = useState<any>(null);

  const [useAccountPhone, setUseAccountPhone] = useState(true);

  // Step 1 – Save address checkbox
  const [saveAddress, setSaveAddress] = useState(true);
  // Step 1 – Address validation errors
  const [addrErrors, setAddrErrors] = useState<Record<string, string>>({});
  // Pincode lookup spinner (separate from serviceability check)
  const [pincodeLoading, setPincodeLoading] = useState(false);

  // ─── Delivery Option ─────────────────────────────────────────────
  const [deliveryOptions, setDeliveryOptions] = useState<{
    slotBookingAvailable: boolean;
    availableDates: string[];
    urgentAvailable?: boolean;
  } | null>(null);
  const [selectedDeliveryType, setSelectedDeliveryType] = useState<'standard' | 'urgent'>('standard');
  const [selectedSlotDate, setSelectedSlotDate] = useState('');
  const [availableSlots, setAvailableSlots] = useState<any[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<any | null>(null);
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Step 0 – Auth method toggle
  const [authMethod, setAuthMethod] = useState<'phone' | 'email'>('phone');
  const [emailInput, setEmailInput] = useState('');

  // Success overlay
  const [orderSuccess, setOrderSuccess] = useState(false);
  const successScale = useRef(new Animated.Value(0)).current;
  const successOpacity = useRef(new Animated.Value(0)).current;

  const fetchMobileStates = async () => {
    try {
      const res = await api.get('/pincodes/states');
      setMobileStates(res.data || []);
    } catch (e) {
      if (__DEV__) console.warn('[checkout] pincodes/states failed', e);
    }
  };
  const fetchMobileDistricts = async (state: string) => {
    if (!state) {
      setMobileDistricts([]);
      return;
    }
    try {
      const res = await api.get(`/pincodes/districts?state=${encodeURIComponent(state)}`);
      setMobileDistricts(res.data || []);
    } catch (e) {
      if (__DEV__) console.warn('[checkout] pincodes/districts failed', e);
      setMobileDistricts([]);
    }
  };

  // Android hardware back button → previous step
  useEffect(() => {
    const minStep = user ? 1 : 0;
    const onBack = () => {
      if (step > minStep) {
        setStep((s) => s - 1);
        return true;
      }
      return false;
    };
    const sub = BackHandler.addEventListener('hardwareBackPress', onBack);
    return () => sub.remove();
  }, [step, user]);

  // Sync account phone to shipping when useAccountPhone is toggled on
  useEffect(() => {
    if (useAccountPhone && user) {
      setShipping((prev) => ({ ...prev, phone: (user as any)?.phone || prev.phone }));
    }
  }, [user, useAccountPhone]);

  // Whenever user becomes available (login / token restore), skip auth step
  useEffect(() => {
    fetchMobileStates();
    if (user && step === 0) {
      loadSavedAddresses();
      setStep(1);
    }
  }, [user]);

  useEffect(() => {
    const fetchUPI = async () => {
      try {
        const r = await api.get('/upi/details');
        setUpiDetails(r.data);
      } catch (e) {
        if (__DEV__) console.warn('[checkout] UPI details fetch failed', e);
      }
    };
    fetchUPI();
  }, []);

  const finalPayableTotal = Math.max(
    0,
    cartTotal -
      (appliedCoupon?.discount || 0) +
      (deliveryChargeInfo?.totalCharge || 0),
  );

  // Auto-detect installed UPI apps on the device
  useEffect(() => {
    let isMounted = true;
    const detectApps = async () => {
      setDetectingUpiApps(true);
      try {
        const detected: UpiAppConfig[] = [];
        for (const app of SUPPORTED_UPI_APPS) {
          if (app.id === 'other') {
            detected.push(app);
            continue;
          }
          try {
            const canOpen = await Linking.canOpenURL(app.scheme);
            if (canOpen) {
              detected.push(app);
            }
          } catch {
            // Ignore scheme check failures
          }
        }
        if (isMounted) {
          if (detected.length <= 1) {
            setAvailableUpiApps(SUPPORTED_UPI_APPS);
          } else {
            setAvailableUpiApps(detected);
          }
        }
      } catch {
        if (isMounted) setAvailableUpiApps(SUPPORTED_UPI_APPS);
      } finally {
        if (isMounted) setDetectingUpiApps(false);
      }
    };
    detectApps();
    return () => {
      isMounted = false;
    };
  }, []);

  // Listen to AppState when user returns from UPI app
  useEffect(() => {
    const sub = AppState.addEventListener('change', (nextState: AppStateStatus) => {
      if (nextState === 'active' && upiTxnRef && !upiPaymentConfirmed) {
        Toast.show({
          type: 'info',
          text1: 'Back in checkout',
          text2: 'Confirm your payment to complete your order.',
        });
      }
    });
    return () => sub.remove();
  }, [upiTxnRef, upiPaymentConfirmed]);

  const handleOpenUpiApp = async (app: UpiAppConfig) => {
    if (!upiDetails?.upiId) {
      Toast.show({ type: 'error', text1: 'UPI Unavailable', text2: 'UPI payment details could not be loaded.' });
      return;
    }
    const pa = upiDetails.upiId;
    const pn = 'Stationery Junction';
    const am = finalPayableTotal.toFixed(2);
    const ref = `SJ${Date.now().toString().slice(-8)}`;
    const tn = `Order Payment SJ`;
    const cu = 'INR';

    setUpiTxnRef(ref);
    setUpiAppUsed(app.name);

    const callbackUrl = 'stationeryjunction://payment-callback';
    const query = `pa=${encodeURIComponent(pa)}&pn=${encodeURIComponent(pn)}&am=${encodeURIComponent(am)}&tr=${encodeURIComponent(ref)}&tn=${encodeURIComponent(tn)}&cu=${encodeURIComponent(cu)}&url=${encodeURIComponent(callbackUrl)}`;
    const targetUrl = app.scheme.includes('?') ? `${app.scheme}&${query}` : `${app.scheme}?${query}`;

    try {
      const supported = await Linking.canOpenURL(targetUrl);
      if (supported) {
        await Linking.openURL(targetUrl);
      } else {
        const fallbackUrl = `upi://pay?${query}`;
        await Linking.openURL(fallbackUrl);
      }
      Toast.show({
        type: 'info',
        text1: `Opening ${app.name}`,
        text2: `Completing payment of ₹${am}...`,
      });
    } catch {
      try {
        const fallbackUrl = `upi://pay?${query}`;
        await Linking.openURL(fallbackUrl);
      } catch {
        Toast.show({
          type: 'error',
          text1: 'Could not launch UPI app',
          text2: 'Please try another app or copy the UPI ID below.',
        });
      }
    }
  };

  useEffect(() => {
    const fetchCart = async () => {
      try {
        if (user) {
          const res = await api.get('/cart');
          // API returns { items: [...], subtotal: X } — extract items array
          const items: any[] = res.data?.items ?? (Array.isArray(res.data) ? res.data : []);
          setCartItems(items);
          setCartTotal(
            items.reduce((s: number, i: any) => {
              const subtotal = i.subtotal !== undefined ? i.subtotal : (i.product?.price || 0) * (i.quantity || 1);
              return s + subtotal;
            }, 0)
          );
        } else {
          const gc = await getGuestCart();
          const items = gc.map((g) => ({ product: g.product, quantity: g.quantity }));
          setCartItems(items);
          setCartTotal(
            items.reduce((s: number, i: any) => s + (i.product?.price || 0) * (i.quantity || 1), 0)
          );
        }
      } catch (e) {
        if (__DEV__) console.warn('[checkout] cart fetch failed', e);
      }
    };
    if (step === 3) fetchCart();
  }, [user, step]);

  const fetchDeliveryCharge = async () => {
    if (!shipping.state || !shipping.city || !shipping.district || !shipping.zipCode) {
      return;
    }
    setFetchingDelivery(true);
    try {
      const res = await api.get('/delivery-charges/location', {
        params: {
          state: shipping.state,
          city: shipping.city,
          district: shipping.district,
          pincode: shipping.zipCode,
          userRole: (user as any)?.role || 'customer',
          orderAmount: cartTotal,
        },
      });
      setDeliveryChargeInfo(res.data);
      if (res.data) {
        setDeliveryCharge(res.data.charge);
      }
    } catch (e) {
      if (__DEV__) console.warn('[checkout] fetch delivery charge failed', e);
      setDeliveryChargeInfo(null);
      setDeliveryCharge(null);
    } finally {
      setFetchingDelivery(false);
    }
  };

  useEffect(() => {
    if (step >= 1 && shipping.zipCode && shipping.state && shipping.city && shipping.district) {
      fetchDeliveryCharge();
    }
  }, [step, shipping.zipCode, shipping.state, shipping.city, shipping.district, cartTotal]);

  // Scroll to top whenever the user moves to a new step
  useEffect(() => {
    scrollRef.current?.scrollTo({ y: 0, animated: false });
  }, [step]);

  // ─── Coupon ───────────────────────────────────────────────────────
  const handleApplyCoupon = async () => {
    const trimmed = couponCode.trim().toUpperCase();
    if (!trimmed) {
      setCouponError('Enter a coupon code');
      return;
    }
    setCouponLoading(true);
    setCouponError('');
    try {
      const res = await api.get(`/coupons/validate/${trimmed}`, {
        params: { amount: cartTotal },
      });
      setAppliedCoupon({
        code: res.data.coupon.code,
        discountType: res.data.coupon.discountType,
        discountValue: res.data.coupon.discountValue,
        discount: res.data.discount,
      });
      Toast.show({ type: 'success', text1: 'Coupon Applied!', text2: `You save ₹${res.data.discount.toFixed(2)}` });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Invalid or expired coupon';
      setCouponError(msg);
      setAppliedCoupon(null);
    } finally {
      setCouponLoading(false);
    }
  };

  // ─── Address helpers ──────────────────────────────────────────────
  const loadSavedAddresses = () => {
    const addrs = (user as any)?.savedAddresses || [];
    setSavedAddresses(addrs);
    if (addrs.length > 0) {
      setSelectedAddressIdx(0);
      applyAddress(addrs[0]);
    } else {
      setShowNewAddress(true);
    }
  };

  const applyAddress = (addr: any) => {
    setShipping({
      street: addr.street || '',
      city: addr.city || '',
      state: addr.state || '',
      district: addr.district || '',
      zipCode: addr.zipCode || addr.pincode || '',
      country: addr.country || 'India',
      phone: addr.phone || (user as any)?.phone || '',
      name: addr.name || (user as any)?.name || '',
      addressLine2: addr.addressLine2 || '',
      landmark: addr.landmark || '',
    });
    setUseAccountPhone(!addr.phone || addr.phone === (user as any)?.phone);
    if (addr.state) fetchMobileDistricts(addr.state);
  };

  const updateField = (key: string, value: string) => setShipping((p) => ({ ...p, [key]: value }));

  // ═══════════════════════════════════════════════════════════════════
  //  STEP 0: AUTH ACTIONS
  // ═══════════════════════════════════════════════════════════════════
  const checkPhone = async () => {
    const clean = phone.replace(/\D/g, '');
    if (!clean || clean.length < 10) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Enter a valid 10-digit phone number' });
      return;
    }
    setAuthBusy(true);
    try {
      const res = await api.post('/auth/check-phone', { phone: clean });
      setIsExisting(res.data.exists);
      setPhoneChecked(true);
    } catch (err: any) {
      if (__DEV__) {
        console.error('[checkout] checkPhone failed:', err);
      }
      const msg = err?.response?.data?.detail || 'Could not verify phone. Please try again.';
      Toast.show({ type: 'error', text1: 'Error', text2: msg });
    }
    setAuthBusy(false);
  };

  const handleLogin = async () => {
    if (!password) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Enter your password' });
      return;
    }
    setAuthBusy(true);
    try {
      await login(phone, password);
      // syncGuestDataToBackend is called automatically inside useAuth.login
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Invalid credentials';
      Toast.show({ type: 'error', text1: 'Login Failed', text2: msg });
    }
    setAuthBusy(false);
  };

  const sendOTP = async () => {
    const clean = phone.replace(/\D/g, '');
    setAuthBusy(true);
    try {
      await api.post('/auth/send-otp', { phone: clean, purpose: 'register' });
      setOtpSent(true);
      Toast.show({ type: 'success', text1: 'OTP Sent', text2: 'Check your phone for the OTP' });
    } catch {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to send OTP' });
    }
    setAuthBusy(false);
  };

  const verifyOTP = async () => {
    if (!otp) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Enter the OTP' });
      return;
    }
    const clean = phone.replace(/\D/g, '');
    setAuthBusy(true);
    try {
      await api.post('/auth/verify-otp', { phone: clean, otp });
      setOtpVerified(true);
      Toast.show({ type: 'success', text1: 'Verified', text2: 'Phone number verified' });
    } catch (err: any) {
      Toast.show({ type: 'error', text1: 'Error', text2: err?.response?.data?.detail || 'Invalid OTP' });
    }
    setAuthBusy(false);
  };

  const handleRegister = async () => {
    if (!password || password.length < 6) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Password must be at least 6 characters' });
      return;
    }
    if (password !== confirmPassword) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Passwords do not match' });
      return;
    }
    const clean = phone.replace(/\D/g, '');
    setAuthBusy(true);
    try {
      const res = await api.post('/auth/register', {
        phone: clean,
        password,
        role: 'customer',
        otp,
      });
      const { token, refreshToken, sessionId, user: userData } = res.data;
      await loginWithTokens({ token, refreshToken, sessionId, user: userData });
      // sync happens inside loginWithTokens
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Registration failed';
      Toast.show({ type: 'error', text1: 'Error', text2: msg });
    }
    setAuthBusy(false);
  };

  // Auto-fill state/district from pincode when 6 digits are entered
  useEffect(() => {
    const zip = shipping.zipCode;
    if (zip.length !== 6) return;
    const lookup = async () => {
      setPincodeLoading(true);
      try {
        const res = await api.get(`/pincodes/${zip}`, { skipAccessToken: true } as any);
        if (res.data?.state) {
          setShipping((prev) => ({
            ...prev,
            state: res.data.state,
            district: res.data.district || prev.district,
            city: res.data.city || prev.city,
          }));
          if (res.data.state) fetchMobileDistricts(res.data.state);
        }
      } catch (e: any) { if (__DEV__) console.warn('Background task failed', e); } finally {
        setPincodeLoading(false);
      }
    };
    lookup();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shipping.zipCode]);

  // ═══════════════════════════════════════════════════════════════════
  //  STEP 1: PINCODE CHECK
  // ═══════════════════════════════════════════════════════════════════
  const checkPincode = async () => {
    if (!shipping.zipCode || shipping.zipCode.length !== 6) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Enter a valid 6-digit pincode' });
      return;
    }
    try {
      setChecking(true);
      const res = await api.get('/delivery-charges/check-serviceability', {
        params: { pincode: shipping.zipCode, userRole: (user as any)?.role || 'customer' },
      });
      if (!res.data?.isServiceable) {
        Toast.show({ type: 'error', text1: 'Not serviceable', text2: 'This pincode is not serviceable.' });
        setDeliveryCharge(null);
        setDeliveryChargeInfo(null);
        setDeliveryOptions(null);
        // Reset slot selection
        setSelectedDeliveryType('standard');
        setSelectedSlot(null);
        setSelectedSlotDate('');
        setAvailableSlots([]);
      } else {
        const locationRes = await api.get('/delivery-charges/location', {
          params: {
            state: shipping.state || 'State',
            city: shipping.city || 'City',
            district: shipping.district || shipping.city || 'District',
            pincode: shipping.zipCode,
            userRole: (user as any)?.role || 'customer',
            orderAmount: cartTotal,
          },
        });
        setDeliveryChargeInfo(locationRes.data);
        const charge = typeof locationRes.data?.charge === 'number' ? locationRes.data.charge : null;
        setDeliveryCharge(charge);
        const msg = charge !== null && charge > 0
          ? `We deliver to this pincode. Delivery charge: ₹${charge}`
          : 'We deliver to this pincode. Free delivery!';
        Toast.show({ type: 'success', text1: 'Serviceable', text2: msg });
        // Populate delivery options
        setDeliveryOptions({
          slotBookingAvailable: res.data.slotBookingAvailable ?? false,
          availableDates: res.data.availableDates ?? [],
          urgentAvailable: res.data.urgentDeliveryAvailable ?? false,
        });
        // Reset delivery selection when pincode changes
        setSelectedDeliveryType('standard');
        setSelectedSlot(null);
        setSelectedSlotDate('');
        setAvailableSlots([]);
      }
    } catch {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to verify pincode.' });
    } finally {
      setChecking(false);
    }
  };

  // ─── Fetch available slots for a selected date ───────────────────
  const fetchSlotsForDate = async (date: string) => {
    if (!date) return;
    const pincode = shipping.zipCode;
    const segment = (user as any)?.role === 'wholesaler' ? 'wholesale' : 'retail';
    setLoadingSlots(true);
    setSelectedSlot(null);
    try {
      const res = await api.get('/delivery-slots/available', {
        params: { date, pincode, segment },
      });
      setAvailableSlots(res.data || []);
    } catch {
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  // ═══════════════════════════════════════════════════════════════════
  //  STEP 3: PLACE ORDER
  // ═══════════════════════════════════════════════════════════════════
  const placeOrder = async () => {
    if (
      !shipping.name ||
      !shipping.phone ||
      !shipping.street ||
      !shipping.city ||
      !shipping.state ||
      !shipping.district ||
      !shipping.zipCode
    ) {
      Toast.show({ type: 'error', text1: 'Missing info', text2: 'Please fill all required address fields.' });
      return;
    }
    if (paymentMethod === 'upi' && !upiPaymentConfirmed && !upiScreenshot && !upiTxnRef) {
      Toast.show({ type: 'error', text1: 'Payment required', text2: 'Please select a UPI app to pay before placing your order.' });
      return;
    }
    try {
      setPlacing(true);
      const orderData: any = {
        shippingAddress: shipping,
        billingAddress: shipping,
        paymentMethod,
        notes: notes || null,
        printedBill,
        couponCode: appliedCoupon?.code || null,
        // Delivery option fields
        isUrgentDelivery: selectedDeliveryType === 'urgent',
        deliverySlotId: selectedDeliveryType === 'standard' ? (selectedSlot?.slotId ?? null) : null,
        deliverySlotConfigId: selectedDeliveryType === 'standard' ? (selectedSlot?.configId ?? null) : null,
        deliverySlotDate: selectedDeliveryType === 'urgent'
          ? new Date().toISOString().split('T')[0]
          : (selectedSlot ? selectedSlotDate : null),
      };
      if (paymentMethod === 'upi') {
        orderData.upiPaymentScreenshot = upiScreenshot || null;
        const refParts = [
          upiTxnRef ? `UPI-Ref: ${upiTxnRef}` : null,
          upiUtr ? `UTR: ${upiUtr}` : null,
          upiAppUsed ? `via ${upiAppUsed}` : null,
          notes || null,
        ].filter(Boolean);
        if (refParts.length > 0) {
          orderData.notes = refParts.join(' | ');
        }
      }
      // Save address to account if checkbox is checked and user is logged in
      if (user && saveAddress && showNewAddress) {
        try {
          const existing: any[] = (user as any)?.savedAddresses || [];
          const newAddr = {
            name: shipping.name,
            phone: shipping.phone,
            street: shipping.street,
            addressLine2: shipping.addressLine2 || '',
            landmark: shipping.landmark || '',
            city: shipping.city,
            district: shipping.district,
            state: shipping.state,
            zipCode: shipping.zipCode,
            country: shipping.country,
          };
          await api.put(`/users/${(user as any)?._id}`, {
            savedAddresses: [...existing, newAddr],
          });
        } catch (e) {
          if (__DEV__) console.warn('[checkout] save address failed', e);
        }
      }

      await api.post('/orders', orderData);
      try {
        if (await StoreReview.hasAction()) await StoreReview.requestReview();
      } catch (e) {
        if (__DEV__) console.warn('[checkout] store review request failed', e);
      }
      // Reset delivery state
      setSelectedDeliveryType('standard');
      setSelectedSlot(null);
      setSelectedSlotDate('');
      setAvailableSlots([]);
      // Show success animation
      setOrderSuccess(true);
      Animated.parallel([
        Animated.spring(successScale, { toValue: 1, useNativeDriver: true, friction: 6 }),
        Animated.timing(successOpacity, { toValue: 1, duration: 300, useNativeDriver: true }),
      ]).start();
    } catch (e: any) {
      Toast.show({
        type: 'error',
        text1: 'Order failed',
        text2: e?.response?.data?.detail || e?.response?.data?.message || 'Could not place order',
      });
    } finally {
      setPlacing(false);
    }
  };

  // ═══════════════════════════════════════════════════════════════════
  //  STEP LABEL
  // ═══════════════════════════════════════════════════════════════════
  const stepLabels = user
    ? ['Address', 'Payment', 'Review']
    : ['Sign In', 'Address', 'Payment', 'Review'];

  const getEffectiveAddress = () => {
    if (selectedAddressIdx !== null && savedAddresses[selectedAddressIdx]) {
      const a = savedAddresses[selectedAddressIdx];
      return `${a.name} (${shipping.phone})\n${a.street || ''}\n${a.city || ''}, ${a.district || ''}\n${a.state || ''} - ${a.zipCode || a.pincode || ''}\n${a.country || 'India'}`;
    }
    return `${shipping.name} (${shipping.phone})\n${shipping.street}\n${shipping.city}, ${shipping.district}\n${shipping.state} - ${shipping.zipCode}\n${shipping.country}`;
  };

  if (isValet) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: '#F8FAFC' }}>
        <View
          className="flex-row items-center border-b border-slate-100 bg-white px-4 py-4"
          style={shadows.sm}
        >
          <TouchableOpacity
            className="mr-3 h-10 w-10 items-center justify-center rounded-xl bg-slate-100"
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={20} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text className="flex-1 text-xl font-bold text-slate-800">Checkout</Text>
        </View>
        <View className="flex-1 items-center justify-center px-6">
          <Ionicons name="cart-outline" size={64} color="#94A3B8" />
          <Text className="mt-4 text-center text-lg font-semibold text-slate-800">
            Valets cannot place orders
          </Text>
          <Text className="mt-2 text-center text-slate-500">
            Delivery valets are not allowed to order. Use a customer or business account to
            checkout.
          </Text>
          <TouchableOpacity
            className="mt-6 rounded-xl bg-neutral-900 px-6 py-3"
            onPress={() => router.back()}
          >
            <Text className="font-semibold text-white">Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F8FAFC' }}>

      {/* Header */}
      <View
        className="flex-row items-center border-b border-slate-100 bg-white px-4 py-4"
        style={shadows.sm}
      >
        <TouchableOpacity
          className="mr-3 h-10 w-10 items-center justify-center rounded-xl bg-slate-100"
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={20} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text className="flex-1 text-xl font-bold text-slate-800">Checkout</Text>
      </View>

      {/* Progress Bar */}
      <View className="flex-row border-b border-slate-100 bg-white px-4 py-4">
        {stepLabels.map((_, idx) => {
          const isActive = step >= (user ? idx + 1 : idx);
          const isPast = step > (user ? idx + 1 : idx);
          return (
            <View key={idx} className="flex-1 flex-row items-center">
              <View
                className="h-8 w-8 items-center justify-center rounded-full"
                style={{ backgroundColor: isActive ? colors.primary : '#E2E8F0' }}
              >
                {isPast ? (
                  <Ionicons name="checkmark" size={16} color={colors.surface} />
                ) : (
                  <Text
                    className={`text-xs font-bold ${isActive ? 'text-white' : 'text-slate-500'}`}
                  >
                    {idx + 1}
                  </Text>
                )}
              </View>
              {idx < stepLabels.length - 1 && (
                <View
                  className="mx-1 h-1 flex-1"
                  style={{ backgroundColor: isPast ? colors.primary : '#E2E8F0' }}
                />
              )}
            </View>
          );
        })}
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          ref={scrollRef}
          style={{ flex: 1 }}
          contentContainerStyle={{ padding: 16 }}
          keyboardShouldPersistTaps="handled"
        >
          {/* ═══════════════════════════════════════════════════════════
              STEP 0: AUTH (only for guests)
          ═══════════════════════════════════════════════════════════ */}
          {step === 0 && (
            <View className="rounded-2xl bg-white p-5" style={shadows.md}>
              <Text className="mb-1 text-lg font-bold text-slate-800">Sign In to Continue</Text>
              <Text className="mb-4 text-sm text-slate-500">
                Sign in or create an account to proceed
              </Text>

              {/* Auth method tabs */}
              <View className="mb-4 flex-row rounded-xl bg-slate-100 p-1">
                <TouchableOpacity
                  className={`flex-1 items-center rounded-lg py-2 ${authMethod === 'phone' ? 'bg-white shadow-sm' : ''}`}
                  onPress={() => { setAuthMethod('phone'); setPhoneChecked(false); }}
                  activeOpacity={0.7}
                >
                  <Text className={`text-sm font-semibold ${authMethod === 'phone' ? 'text-slate-800' : 'text-slate-400'}`}>
                    Phone
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  className={`flex-1 items-center rounded-lg py-2 ${authMethod === 'email' ? 'bg-white shadow-sm' : ''}`}
                  onPress={() => { setAuthMethod('email'); setPhoneChecked(false); }}
                  activeOpacity={0.7}
                >
                  <Text className={`text-sm font-semibold ${authMethod === 'email' ? 'text-slate-800' : 'text-slate-400'}`}>
                    Email
                  </Text>
                </TouchableOpacity>
              </View>

              {authMethod === 'email' ? (
                /* ── Email + Password login ── */
                <View>
                  <InputField
                    icon="mail-outline"
                    label="Email Address"
                    placeholder="you@example.com"
                    value={emailInput}
                    onChangeText={setEmailInput}
                    keyboardType="email-address"
                  />
                  <InputField
                    icon="lock-closed-outline"
                    label="Password"
                    placeholder="Enter your password"
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry={!showPassword}
                  />
                  <TouchableOpacity onPress={() => setShowPassword(!showPassword)} className="mb-4">
                    <Text className="text-sm" style={{ color: colors.primary }}>
                      {showPassword ? 'Hide password' : 'Show password'}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    className="items-center rounded-2xl py-4"
                    style={[shadows.lg, { backgroundColor: colors.primary }]}
                    onPress={async () => {
                      if (!emailInput || !password) {
                        Toast.show({ type: 'error', text1: 'Error', text2: 'Enter email and password' });
                        return;
                      }
                      setAuthBusy(true);
                      try {
                        await login(emailInput, password);
                      } catch (err: any) {
                        const msg = err?.response?.data?.detail || 'Invalid credentials';
                        Toast.show({ type: 'error', text1: 'Login Failed', text2: msg });
                      }
                      setAuthBusy(false);
                    }}
                    disabled={authBusy}
                  >
                    {authBusy ? <ActivityIndicator color={colors.surface} /> : <Text className="font-bold text-white">Log In</Text>}
                  </TouchableOpacity>
                  <TouchableOpacity onPress={() => router.push('/login')} className="mt-3 items-center">
                    <Text className="text-sm text-slate-500">Forgot password?</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                /* ── Phone flow ── */
                <View>
                  <InputField
                    icon="call-outline"
                    label="Mobile Number"
                    placeholder="10-digit mobile number"
                    value={phone}
                    onChangeText={(t) => {
                      setPhone(t);
                      setPhoneChecked(false);
                      setOtpSent(false);
                      setOtpVerified(false);
                    }}
                    keyboardType="phone-pad"
                  />

              {!phoneChecked ? (
                <TouchableOpacity
                  className="mt-2 items-center rounded-2xl py-4"
                  style={[shadows.lg, { backgroundColor: colors.primary }]}
                  onPress={checkPhone}
                  disabled={authBusy}
                >
                  {authBusy ? (
                    <ActivityIndicator color={colors.surface} />
                  ) : (
                    <Text className="font-bold text-white">Continue</Text>
                  )}
                </TouchableOpacity>
              ) : isExisting ? (
                /* ── Existing user: password login ── */
                <View>
                  <InputField
                    icon="lock-closed-outline"
                    label="Password"
                    placeholder="Enter your password"
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry={!showPassword}
                  />
                  <TouchableOpacity onPress={() => setShowPassword(!showPassword)} className="mb-4">
                    <Text className="text-sm" style={{ color: colors.primary }}>
                      {showPassword ? 'Hide password' : 'Show password'}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    className="items-center rounded-2xl py-4"
                    style={[shadows.lg, { backgroundColor: colors.primary }]}
                    onPress={handleLogin}
                    disabled={authBusy}
                  >
                    {authBusy ? (
                      <ActivityIndicator color={colors.surface} />
                    ) : (
                      <Text className="font-bold text-white">Log In</Text>
                    )}
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => router.push('/login')}
                    className="mt-3 items-center"
                  >
                    <Text className="text-sm text-slate-500">Forgot password?</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                /* ── New user: OTP + set password ── */
                <View>
                  {/* OTP row */}
                  <View className="mb-4 flex-row gap-3">
                    <View className="flex-1">
                      <Text className="mb-2 font-medium text-slate-700">OTP Verification</Text>
                      <View className="flex-row items-center rounded-xl bg-slate-100 px-4 py-3">
                        <Ionicons name="key-outline" size={18} color="#64748B" />
                        <TextInput
                          className="ml-3 flex-1 text-slate-800"
                          placeholder="Enter OTP"
                          placeholderTextColor="#94A3B8"
                          keyboardType="number-pad"
                          value={otp}
                          onChangeText={setOtp}
                          editable={otpSent && !otpVerified}
                        />
                      </View>
                    </View>
                    <View className="justify-end">
                      <TouchableOpacity
                        className="rounded-xl px-4 py-3"
                        style={{ backgroundColor: otpVerified ? colors.success : otpSent ? colors.warning : colors.primary }}
                        onPress={otpVerified ? undefined : otpSent ? verifyOTP : sendOTP}
                        disabled={authBusy || otpVerified}
                      >
                        {authBusy ? (
                          <ActivityIndicator color={colors.surface} size="small" />
                        ) : otpVerified ? (
                          <Ionicons name="checkmark" size={20} color={colors.surface} />
                        ) : (
                          <Text className="text-sm font-semibold text-white">
                            {otpSent ? 'Verify' : 'Send'}
                          </Text>
                        )}
                      </TouchableOpacity>
                    </View>
                  </View>

                  {otpVerified && (
                    <>
                      <InputField
                        icon="lock-closed-outline"
                        label="Set Password"
                        placeholder="Min 6 characters"
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry={!showPassword}
                      />
                      <InputField
                        icon="lock-closed-outline"
                        label="Confirm Password"
                        placeholder="Re-enter password"
                        value={confirmPassword}
                        onChangeText={setConfirmPassword}
                        secureTextEntry={!showPassword}
                      />
                      <TouchableOpacity
                        onPress={() => setShowPassword(!showPassword)}
                        className="mb-4"
                      >
                        <Text className="text-sm" style={{ color: colors.primary }}>
                          {showPassword ? 'Hide password' : 'Show password'}
                        </Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        className="mt-4 items-center rounded-2xl py-4"
                        style={otpVerified ? [shadows.lg, { backgroundColor: colors.primary }] : { backgroundColor: '#cbd5e1' }}
                        onPress={handleRegister}
                        disabled={authBusy || !otpVerified}
                      >
                        {authBusy ? (
                          <ActivityIndicator color={colors.surface} />
                        ) : (
                          <Text className="font-bold text-white">Create Account & Continue</Text>
                        )}
                      </TouchableOpacity>
                    </>
                  )}
                </View>
              )}
                </View>
              )}
            </View>
          )}

          {/* ═══════════════════════════════════════════════════════════
              STEP 1: ADDRESS
          ═══════════════════════════════════════════════════════════ */}
          {step === 1 && (
            <View className="rounded-2xl bg-white p-5" style={shadows.md}>
              <Text className="mb-1 text-lg font-bold text-slate-800">Shipping Address</Text>

              {/* Saved addresses */}
              {savedAddresses.length > 0 && !showNewAddress && (
                <View className="mb-4">
                  <Text className="mb-2 text-sm font-medium text-slate-600">Saved Addresses</Text>
                  {savedAddresses.map((addr, idx) => (
                    <TouchableOpacity
                      key={idx}
                      className="mb-2 rounded-xl border p-4"
                    style={{
                      borderColor: selectedAddressIdx === idx ? colors.primary : '#E2E8F0',
                      backgroundColor: selectedAddressIdx === idx ? `${colors.primary}12` : colors.surface,
                    }}
                      onPress={() => {
                        setSelectedAddressIdx(idx);
                        applyAddress(addr);
                      }}
                      activeOpacity={0.7}
                    >
                      <View className="flex-row items-center">
                        <Ionicons
                          name={selectedAddressIdx === idx ? 'radio-button-on' : 'radio-button-off'}
                          size={18}
                          color={selectedAddressIdx === idx ? colors.primary : '#94A3B8'}
                        />
                        <View className="ml-3 flex-1">
                          {addr.name ? (
                            <Text className="mb-1 text-sm font-bold text-slate-800">
                              {addr.name}
                            </Text>
                          ) : null}
                          <Text className="text-sm font-medium text-slate-800">{addr.street}</Text>
                          {addr.addressLine2 ? (
                            <Text className="mt-0.5 text-xs text-slate-600">
                              {addr.addressLine2}
                            </Text>
                          ) : null}
                          {addr.landmark ? (
                            <Text className="mt-0.5 text-xs text-slate-600">
                              Landmark: {addr.landmark}
                            </Text>
                          ) : null}
                          <Text className="mt-0.5 text-xs text-slate-500">
                            {addr.city}, {addr.state} - {addr.zipCode || addr.pincode}
                          </Text>
                        </View>
                      </View>
                    </TouchableOpacity>
                  ))}
                  <TouchableOpacity
                    className="items-center rounded-xl border border-dashed border-slate-300 py-3"
                    onPress={() => {
                      setShowNewAddress(true);
                      setSelectedAddressIdx(null);
                      setShipping({
                        street: '',
                        city: '',
                        state: '',
                        district: '',
                        zipCode: '',
                        country: 'India',
                        phone: (user as any)?.phone || '',
                        name: (user as any)?.name || '',
                        addressLine2: '',
                        landmark: '',
                      });
                    }}
                  >
                    <Text className="text-sm font-semibold" style={{ color: colors.primary }}>+ Add New Address</Text>
                  </TouchableOpacity>
                </View>
              )}

              {/* New address form */}
              {(showNewAddress || savedAddresses.length === 0) && (
                <View>
                  {savedAddresses.length > 0 && (
                    <TouchableOpacity
                      onPress={() => {
                        setShowNewAddress(false);
                        if (savedAddresses.length) {
                          setSelectedAddressIdx(0);
                          applyAddress(savedAddresses[0]);
                        }
                      }}
                      className="mb-3"
                    >
                      <Text className="text-sm font-medium" style={{ color: colors.primary }}>
                        Back to saved addresses
                      </Text>
                    </TouchableOpacity>
                  )}
                  <InputField
                    label="Full Name"
                    placeholder="John Doe"
                    value={shipping.name}
                    onChangeText={(t) => { updateField('name', t); setAddrErrors((e) => ({ ...e, name: '' })); }}
                    error={addrErrors.name}
                  />
                  <View className="mb-4">
                    <View className="mb-2 flex-row items-center justify-between">
                      <Text className="font-medium text-slate-700">Mobile Number</Text>
                      {user && (
                        <View className="flex-row items-center">
                          <Switch
                            value={useAccountPhone}
                            onValueChange={(val) => {
                              setUseAccountPhone(val);
                              if (val) updateField('phone', (user as any)?.phone || '');
                              else updateField('phone', '');
                            }}
                            trackColor={{ false: '#E2E8F0', true: colors.accent }}
                            style={{ transform: [{ scaleX: 0.8 }, { scaleY: 0.8 }] }}
                          />
                          <Text className="ml-1 text-xs text-slate-500">Same as account</Text>
                        </View>
                      )}
                    </View>
                    <View className="flex-row items-center rounded-xl bg-slate-100 px-4 py-3">
                      <Ionicons
                        name="call-outline"
                        size={18}
                        color="#64748B"
                        style={{ marginRight: 8 }}
                      />
                      <TextInput
                        className="flex-1 text-slate-800"
                        placeholder="+91 98765 43210"
                        placeholderTextColor="#94A3B8"
                        keyboardType="phone-pad"
                        value={shipping.phone}
                        onChangeText={(t) => updateField('phone', t)}
                        editable={!useAccountPhone}
                      />
                    </View>
                  </View>
                  <InputField
                    label="Street Address *"
                    placeholder="123 Main Street"
                    value={shipping.street}
                    onChangeText={(t) => { updateField('street', t); setAddrErrors((e) => ({ ...e, street: '' })); }}
                    error={addrErrors.street}
                  />
                  <InputField
                    label="Address Line 2 (Optional)"
                    placeholder="Apartment, suite, unit, etc."
                    value={shipping.addressLine2 || ''}
                    onChangeText={(t) => updateField('addressLine2', t)}
                  />
                  <InputField
                    label="Landmark (Optional)"
                    placeholder="Near hospital, next to mall, etc."
                    value={shipping.landmark || ''}
                    onChangeText={(t) => updateField('landmark', t)}
                  />
                  <View className="flex-row gap-3">
                    <View className="flex-1">
                      <InputField
                        label="City *"
                        placeholder="City"
                        value={shipping.city}
                        onChangeText={(t) => { updateField('city', t); setAddrErrors((e) => ({ ...e, city: '' })); }}
                        error={addrErrors.city}
                      />
                    </View>
                  </View>
                  <SearchablePicker
                    label="State *"
                    options={mobileStates}
                    value={shipping.state}
                    onChange={(val) => {
                      setShipping((p) => ({ ...p, state: val, district: '' }));
                      fetchMobileDistricts(val);
                    }}
                    placeholder="Select State"
                    icon="location-outline"
                  />
                  <SearchablePicker
                    label="District *"
                    options={mobileDistricts}
                    value={shipping.district}
                    onChange={(val) => setShipping((p) => ({ ...p, district: val }))}
                    placeholder="Select District"
                    disabled={!shipping.state}
                    icon="map-outline"
                  />
                  <View className="flex-row items-end gap-3">
                    <View className="flex-1">
                      <InputField
                        label="Pincode *"
                        placeholder="400001"
                        value={shipping.zipCode}
                        onChangeText={(t) => { updateField('zipCode', t.replace(/\D/g, '')); setAddrErrors((e) => ({ ...e, zipCode: '' })); }}
                        keyboardType="number-pad"
                        error={addrErrors.zipCode}
                        rightElement={
                          pincodeLoading ? (
                            <ActivityIndicator size="small" color={colors.primary} style={{ marginLeft: 6 }} />
                          ) : null
                        }
                      />
                    </View>
                    <TouchableOpacity
                      className="mb-4 rounded-xl px-4 py-3"
                      style={{ backgroundColor: `${colors.primary}22` }}
                      onPress={checkPincode}
                      disabled={checking || pincodeLoading}
                    >
                      {checking ? (
                        <ActivityIndicator color={colors.primary} size="small" />
                      ) : (
                        <Text className="font-semibold" style={{ color: colors.primary }}>Check</Text>
                      )}
                    </TouchableOpacity>
                  </View>
                </View>
              )}

              {/* ── Delivery Option Selector ──────────────────────────────── */}
              {deliveryOptions && (
                <View className="mt-2 mb-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <Text className="mb-3 text-sm font-semibold text-slate-800">🚚 Delivery Option</Text>

                  {/* Standard Delivery */}
                  <TouchableOpacity
                    className={`mb-2 flex-row items-start rounded-xl border p-3 ${selectedDeliveryType === 'standard' ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200 bg-white'}`}
                    onPress={() => {
                      setSelectedDeliveryType('standard');
                      setSelectedSlot(null);
                      if (deliveryOptions.slotBookingAvailable && deliveryOptions.availableDates.length > 0) {
                        const firstDate = deliveryOptions.availableDates[0];
                        setSelectedSlotDate(firstDate);
                        fetchSlotsForDate(firstDate);
                      }
                    }}
                    activeOpacity={0.8}
                  >
                    <View
                      className={`mr-3 mt-0.5 h-5 w-5 items-center justify-center rounded-full border-2 ${selectedDeliveryType === 'standard' ? 'border-indigo-500' : 'border-slate-300'}`}
                    >
                      {selectedDeliveryType === 'standard' && (
                        <View className="h-2.5 w-2.5 rounded-full bg-indigo-500" />
                      )}
                    </View>
                    <View className="flex-1">
                      <Text className="text-sm font-medium text-slate-700">📅 Standard Delivery</Text>

                      {/* Slot picker — only shown when standard is selected and slots are available */}
                      {selectedDeliveryType === 'standard' && deliveryOptions.slotBookingAvailable && (
                        <View className="mt-3">
                          <Text className="mb-2 text-xs font-medium text-slate-600">Select Date</Text>
                          <View className="mb-3 flex-row flex-wrap gap-2">
                            {deliveryOptions.availableDates.map((d) => (
                              <TouchableOpacity
                                key={d}
                                onPress={() => {
                                  setSelectedSlotDate(d);
                                  fetchSlotsForDate(d);
                                }}
                                className={`rounded-lg border px-3 py-2 ${
                                  selectedSlotDate === d
                                    ? 'border-indigo-500 bg-indigo-500'
                                    : 'border-slate-300 bg-white'
                                }`}
                              >
                                <Text
                                  className={`text-xs font-semibold ${
                                    selectedSlotDate === d ? 'text-white' : 'text-slate-600'
                                  }`}
                                >
                                  {d}
                                </Text>
                              </TouchableOpacity>
                            ))}
                          </View>

                          {selectedSlotDate && (
                            <View>
                              <Text className="mb-2 text-xs font-medium text-slate-600">Select Time Slot</Text>
                              {loadingSlots ? (
                                <ActivityIndicator size="small" color={colors.primary} />
                              ) : availableSlots.filter(s => !s.isUrgent).length === 0 ? (
                                <Text className="text-xs text-slate-400">No standard slots available for this date.</Text>
                              ) : (
                                <View className="gap-2">
                                  {/* Anytime option */}
                                  <TouchableOpacity
                                    onPress={() => setSelectedSlot({ slotId: 'anytime', isFullDay: true, isUrgent: false })}
                                    className={`flex-row items-center justify-between rounded-xl border px-3 py-3 ${
                                      selectedSlot?.slotId === 'anytime'
                                        ? 'border-indigo-500 bg-indigo-50'
                                        : 'border-slate-200 bg-white'
                                    }`}
                                  >
                                    <Text className="text-sm font-medium text-slate-700">Anytime</Text>
                                    {selectedSlot?.slotId === 'anytime' && (
                                      <Ionicons name="checkmark-circle" size={18} color="#6366F1" />
                                    )}
                                  </TouchableOpacity>
                                  {availableSlots.filter(s => !s.isUrgent).map((slot) => (
                                    <TouchableOpacity
                                      key={slot.slotId}
                                      onPress={() => setSelectedSlot(slot)}
                                      className={`flex-row items-center justify-between rounded-xl border px-3 py-3 ${
                                        selectedSlot?.slotId === slot.slotId
                                          ? 'border-indigo-500 bg-indigo-50'
                                          : 'border-slate-200 bg-white'
                                      }`}
                                    >
                                      <Text className={`text-sm font-medium ${
                                        selectedSlot?.slotId === slot.slotId ? 'text-slate-800' : 'text-slate-700'
                                      }`}>
                                        {slot.isFullDay ? 'Full Day' : `${slot.startTime} – ${slot.endTime}`}
                                      </Text>
                                      {selectedSlot?.slotId === slot.slotId && (
                                        <Ionicons name="checkmark-circle" size={18} color="#6366F1" />
                                      )}
                                    </TouchableOpacity>
                                  ))}
                                </View>
                              )}
                            </View>
                          )}
                        </View>
                      )}
                    </View>
                  </TouchableOpacity>

                  {/* Urgent Delivery — only shown when available for this pincode */}
                  {deliveryOptions.urgentAvailable && (
                    <TouchableOpacity
                      className={`flex-row items-start rounded-xl border p-3 ${selectedDeliveryType === 'urgent' ? 'border-amber-400 bg-amber-50' : 'border-slate-200 bg-white'}`}
                      onPress={() => {
                        setSelectedDeliveryType('urgent');
                        setSelectedSlot(null);
                        setSelectedSlotDate(new Date().toISOString().split('T')[0]);
                      }}
                      activeOpacity={0.8}
                    >
                      <View
                        className={`mr-3 mt-0.5 h-5 w-5 items-center justify-center rounded-full border-2 ${selectedDeliveryType === 'urgent' ? 'border-amber-500' : 'border-slate-300'}`}
                      >
                        {selectedDeliveryType === 'urgent' && (
                          <View className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                        )}
                      </View>
                      <View className="flex-1">
                        <Text className="text-sm font-medium text-slate-700">⚡ Urgent Delivery</Text>
                        {selectedDeliveryType === 'urgent' && (
                          <View className="mt-2 rounded-lg border border-amber-200 bg-amber-100 px-3 py-2">
                            <Text className="text-xs text-amber-800">
                              Delivered as soon as possible. An{' '}
                              <Text className="font-bold">urgent surcharge</Text> will apply.
                            </Text>
                          </View>
                        )}
                      </View>
                    </TouchableOpacity>
                  )}
                </View>
              )}


              {/* Save address checkbox */}
              {user && showNewAddress && (
                <TouchableOpacity
                  className="mb-4 mt-1 flex-row items-center"
                  onPress={() => setSaveAddress((v) => !v)}
                  activeOpacity={0.7}
                >
                  <View
                    className={`mr-3 h-5 w-5 items-center justify-center rounded border-2 ${saveAddress ? 'border-transparent' : 'border-slate-300'}`}
                    style={saveAddress ? { backgroundColor: colors.primary } : undefined}
                  >
                    {saveAddress && <Ionicons name="checkmark" size={12} color={colors.surface} />}
                  </View>
                  <Text className="text-sm text-slate-600">Save this address to my account</Text>
                </TouchableOpacity>
              )}

              <TouchableOpacity
                className="mt-2 items-center rounded-2xl bg-neutral-900 py-4"
                style={shadows.lg}
                onPress={() => {
                  const errors: Record<string, string> = {};
                  if (!shipping.name) errors.name = 'Full name is required';
                  if (!shipping.phone || shipping.phone.replace(/\D/g, '').length < 10)
                    errors.phone = 'Valid 10-digit phone number is required';
                  if (!shipping.street) errors.street = 'Street address is required';
                  if (!shipping.city) errors.city = 'City is required';
                  if (!shipping.state) errors.state = 'State is required';
                  if (!shipping.district) errors.district = 'District is required';
                  if (!shipping.zipCode || shipping.zipCode.length !== 6)
                    errors.zipCode = 'Valid 6-digit pincode is required';
                  if (Object.keys(errors).length > 0) {
                    setAddrErrors(errors);
                    return;
                  }
                  setAddrErrors({});
                  setStep(2);
                }}
              >
                <Text className="font-bold text-white">Continue to Payment</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* ═══════════════════════════════════════════════════════════
              STEP 2: PAYMENT
          ═══════════════════════════════════════════════════════════ */}
          {step === 2 && (
            <View className="rounded-2xl bg-white p-5" style={shadows.md}>
              <Text className="mb-4 text-lg font-bold text-slate-800">Payment Method</Text>

              <View className="mb-6 flex-row gap-3">
                <PaymentOption
                  value="cod"
                  label="Cash"
                  icon="cash-outline"
                  currentMethod={paymentMethod}
                  onPress={setPaymentMethod}
                />
                <PaymentOption
                  value="upi"
                  label="UPI"
                  icon="phone-portrait-outline"
                  currentMethod={paymentMethod}
                  onPress={setPaymentMethod}
                />
                {(user as any)?.role === 'wholesaler' && (
                  <PaymentOption
                    value="credit"
                    label="Credit"
                    icon="wallet-outline"
                    currentMethod={paymentMethod}
                    onPress={setPaymentMethod}
                  />
                )}
              </View>

              {paymentMethod === 'upi' && upiDetails && (
                <View className="mb-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  {/* Total Payable Badge */}
                  <View className="mb-4 flex-row items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
                    <View>
                      <Text className="text-xs font-semibold text-emerald-800">Total Payable Amount</Text>
                      <Text className="text-xl font-black text-emerald-950">₹{finalPayableTotal.toFixed(2)}</Text>
                    </View>
                    <View className="rounded-full bg-emerald-600/15 px-3 py-1">
                      <Text className="text-xs font-bold text-emerald-700">0% Payment Fee</Text>
                    </View>
                  </View>

                  {/* Payment In-Progress / Confirmation Card */}
                  {upiTxnRef ? (
                    <View className="mb-4 rounded-xl border border-emerald-300 bg-white p-4 shadow-sm" style={shadows.sm}>
                      <View className="mb-2 flex-row items-center">
                        <Ionicons name="checkmark-circle" size={22} color="#16a34a" style={{ marginRight: 8 }} />
                        <Text className="text-base font-bold text-slate-800">
                          Payment Opened in {upiAppUsed || 'UPI App'}
                        </Text>
                      </View>
                      <Text className="mb-1 text-xs text-slate-600">
                        Order Ref: <Text className="font-bold text-slate-800">{upiTxnRef}</Text> (embedded in payment)
                      </Text>
                      <Text className="mb-4 text-xs text-slate-500">
                        Once you enter your UPI PIN in {upiAppUsed || 'your UPI app'}, tap below to proceed:
                      </Text>

                      <View className="flex-row gap-2">
                        <TouchableOpacity
                          className="flex-1 items-center justify-center rounded-xl bg-emerald-600 py-3.5"
                          onPress={() => {
                            setUpiPaymentConfirmed(true);
                            setStep(3);
                          }}
                        >
                          <Text className="font-bold text-white text-sm">Yes, Payment Done →</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          className="items-center justify-center rounded-xl border border-slate-300 bg-slate-100 px-4 py-3.5"
                          onPress={() => {
                            setUpiTxnRef('');
                            setUpiPaymentConfirmed(false);
                          }}
                        >
                          <Text className="text-xs font-semibold text-slate-700">Retry</Text>
                        </TouchableOpacity>
                      </View>

                      {/* Optional UTR entry */}
                      <TouchableOpacity
                        className="mt-3 items-center border-t border-slate-100 pt-2"
                        onPress={() => setShowManualUtr(!showManualUtr)}
                      >
                        <Text className="text-xs font-medium text-emerald-700">
                          {showManualUtr ? 'Hide UTR input' : '+ Have a 12-digit UPI UTR? (Optional)'}
                        </Text>
                      </TouchableOpacity>
                      {showManualUtr && (
                        <View className="mt-2">
                          <TextInput
                            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-800"
                            placeholder="e.g. 428901234567"
                            placeholderTextColor="#94A3B8"
                            value={upiUtr}
                            onChangeText={setUpiUtr}
                            keyboardType="numeric"
                            maxLength={16}
                          />
                        </View>
                      )}
                    </View>
                  ) : (
                    /* App Selection List */
                    <View className="mb-4">
                      <View className="mb-3 flex-row items-center justify-between">
                        <Text className="font-bold text-slate-800">Tap your UPI App to Pay</Text>
                        {detectingUpiApps && <ActivityIndicator size="small" color={colors.primary} />}
                      </View>
                      <View className="gap-2.5">
                        {availableUpiApps.map((app) => (
                          <TouchableOpacity
                            key={app.id}
                            className="flex-row items-center justify-between rounded-xl bg-white px-4 py-3.5 border border-slate-200 shadow-sm"
                            style={shadows.sm}
                            onPress={() => handleOpenUpiApp(app)}
                            activeOpacity={0.8}
                          >
                            <View className="flex-row items-center">
                              <View
                                className="h-10 w-10 items-center justify-center rounded-xl"
                                style={{ backgroundColor: app.bgColor }}
                              >
                                <Ionicons name={app.iconName} size={22} color={app.textColor} />
                              </View>
                              <View className="ml-3">
                                <Text className="font-bold text-slate-800 text-sm">{app.name}</Text>
                                <Text className="text-xs text-slate-500">{app.subtext}</Text>
                              </View>
                            </View>
                            <View className="flex-row items-center">
                              {app.badge && (
                                <View className="mr-2 rounded-full bg-slate-100 px-2 py-0.5">
                                  <Text className="text-[10px] font-bold text-slate-600">{app.badge}</Text>
                                </View>
                              )}
                              <View className="h-7 w-7 items-center justify-center rounded-full bg-slate-100">
                                <Ionicons name="arrow-forward" size={14} color="#64748B" />
                              </View>
                            </View>
                          </TouchableOpacity>
                        ))}
                      </View>
                    </View>
                  )}

                  {/* Expandable Manual / QR / Screenshot Accordion for edge cases */}
                  <TouchableOpacity
                    className="flex-row items-center justify-between border-t border-slate-200 pt-3"
                    onPress={() => setShowAdvancedUpi(!showAdvancedUpi)}
                  >
                    <Text className="text-xs font-semibold text-slate-600">
                      {showAdvancedUpi ? 'Hide manual QR & screenshot' : 'Trouble opening app? Show QR & UPI ID'}
                    </Text>
                    <Ionicons
                      name={showAdvancedUpi ? 'chevron-up' : 'chevron-down'}
                      size={16}
                      color="#64748B"
                    />
                  </TouchableOpacity>

                  {showAdvancedUpi && (
                    <View className="mt-4 border-t border-slate-100 pt-3">
                      <View className="mb-3 items-center">
                        {upiDetails.qrCodeUrl && (
                          <View className="mb-3 rounded-xl bg-white p-2 shadow-sm" style={shadows.sm}>
                            <Image
                              source={{
                                uri: api.defaults.baseURL?.replace('/api', '') + upiDetails.qrCodeUrl,
                              }}
                              style={{ width: 140, height: 140 }}
                              resizeMode="contain"
                            />
                          </View>
                        )}
                        <View
                          className="w-full flex-row items-center justify-between rounded-xl bg-white px-4 py-3"
                          style={shadows.sm}
                        >
                          <Text className="font-semibold text-xs" style={{ color: colors.primary }}>{upiDetails.upiId}</Text>
                          <TouchableOpacity
                            className="rounded-lg px-3 py-1.5"
                            style={{ backgroundColor: `${colors.primary}20` }}
                            onPress={async () => {
                              await Clipboard.setStringAsync(upiDetails.upiId);
                              Toast.show({ type: 'success', text1: 'Copied', text2: 'UPI ID copied to clipboard' });
                            }}
                          >
                            <Text className="text-xs font-bold" style={{ color: colors.primary }}>
                              Copy
                            </Text>
                          </TouchableOpacity>
                        </View>
                      </View>

                      <Text className="mb-2 text-xs font-medium text-slate-700">
                        Upload Screenshot (Optional)
                      </Text>
                      {upiScreenshot ? (
                        <View className="mt-2 rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
                          <Image
                            source={{ uri: upiScreenshot }}
                            style={{ width: '100%', height: 160, borderRadius: 8 }}
                            resizeMode="cover"
                          />
                          <TouchableOpacity
                            className="absolute right-4 top-4 h-8 w-8 items-center justify-center rounded-full bg-red-500"
                            onPress={() => setUpiScreenshot('')}
                          >
                            <Ionicons name="close" size={20} color={colors.surface} />
                          </TouchableOpacity>
                        </View>
                      ) : (
                        <TouchableOpacity
                          className="items-center rounded-xl border border-dashed border-slate-300 bg-white py-4 text-center"
                          onPress={async () => {
                            const result = await ImagePicker.launchImageLibraryAsync({
                              mediaTypes: ImagePicker.MediaTypeOptions.Images,
                              allowsEditing: true,
                              quality: 1,
                            });
                            if (!result.canceled && result.assets[0].uri) {
                              try {
                                const compressed = await ImageManipulator.manipulateAsync(
                                  result.assets[0].uri,
                                  [{ resize: { width: 1200 } }],
                                  { compress: 0.75, format: ImageManipulator.SaveFormat.JPEG, base64: true }
                                );
                                setUpiScreenshot('data:image/jpeg;base64,' + compressed.base64);
                              } catch {
                                const fallback = await ImagePicker.launchImageLibraryAsync({
                                  mediaTypes: ImagePicker.MediaTypeOptions.Images,
                                  allowsEditing: true,
                                  quality: 0.7,
                                  base64: true,
                                });
                                if (!fallback.canceled && fallback.assets[0].base64) {
                                  setUpiScreenshot('data:image/jpeg;base64,' + fallback.assets[0].base64);
                                }
                              }
                            }
                          }}
                        >
                          <Ionicons name="cloud-upload-outline" size={24} color="#94A3B8" />
                          <Text className="mt-1 text-xs font-medium" style={{ color: colors.primary }}>
                            Tap to attach screenshot (optional)
                          </Text>
                        </TouchableOpacity>
                      )}
                    </View>
                  )}
                </View>
              )}

              <View className="mt-2 flex-row items-center justify-between border-t border-slate-100 py-4">
                <Text className="font-medium text-slate-700">I need a printed bill</Text>
                <Switch
                  value={printedBill}
                  onValueChange={setPrintedBill}
                  trackColor={{ false: '#E2E8F0', true: colors.accent }}
                />
              </View>

              <View className="mt-4 flex-row gap-3">
                <TouchableOpacity
                  className="flex-1 items-center rounded-2xl bg-slate-100 py-4"
                  onPress={() => setStep(1)}
                >
                  <Text className="font-bold text-slate-600">Back</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  className="flex-1 items-center rounded-2xl bg-neutral-900 py-4"
                  style={shadows.lg}
                  onPress={() => setStep(3)}
                >
                  <Text className="font-bold text-white">Review Order</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* ═══════════════════════════════════════════════════════════
              STEP 3: REVIEW & PLACE
          ═══════════════════════════════════════════════════════════ */}
          {step === 3 && (
            <View className="rounded-2xl bg-white p-5" style={shadows.md}>
              <Text className="mb-4 text-lg font-bold text-slate-800">Review Order</Text>

              <TextInput
                className="h-24 rounded-xl bg-slate-100 px-4 py-3 text-slate-800"
                placeholder="Any special instructions..."
                placeholderTextColor="#94A3B8"
                value={notes}
                onChangeText={setNotes}
                multiline
                textAlignVertical="top"
              />

              {/* Coupon / promo code */}
              <View className="mt-4 overflow-hidden rounded-2xl border border-slate-100 bg-slate-50">
                <TouchableOpacity
                  className="flex-row items-center justify-between px-4 py-3"
                  onPress={() => setCouponExpanded(!couponExpanded)}
                  activeOpacity={0.7}
                >
                  <View className="flex-row items-center" style={{ gap: 8 }}>
                    <Ionicons
                      name="pricetag-outline"
                      size={18}
                      color={appliedCoupon ? colors.success : '#64748B'}
                    />
                    <Text
                      className="text-sm font-medium"
                      style={{ color: appliedCoupon ? colors.success : '#64748B' }}
                    >
                      {appliedCoupon
                        ? `"${appliedCoupon.code}" applied — save ₹${appliedCoupon.discount.toFixed(2)}`
                        : 'Have a promo code?'}
                    </Text>
                  </View>
                  <Ionicons
                    name={couponExpanded ? 'chevron-up' : 'chevron-down'}
                    size={16}
                    color="#94A3B8"
                  />
                </TouchableOpacity>

                {couponExpanded && (
                  <View className="border-t border-slate-100 px-4 pb-4 pt-3">
                    <View className="flex-row" style={{ gap: 8 }}>
                      <TextInput
                        className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800"
                        placeholder="Enter coupon code"
                        placeholderTextColor="#94A3B8"
                        value={couponCode}
                        onChangeText={(t) => {
                          setCouponCode(t);
                          setCouponError('');
                        }}
                        autoCapitalize="characters"
                        autoCorrect={false}
                      />
                      <TouchableOpacity
                        className="items-center justify-center rounded-xl px-5 py-3"
                        style={{ backgroundColor: colors.primary }}
                        onPress={handleApplyCoupon}
                        disabled={couponLoading}
                      >
                        {couponLoading ? (
                          <ActivityIndicator size="small" color={colors.surface} />
                        ) : (
                          <Text className="text-sm font-bold text-white">Apply</Text>
                        )}
                      </TouchableOpacity>
                    </View>
                    {!!couponError && (
                      <Text className="mt-2 text-xs text-red-500">{couponError}</Text>
                    )}
                    {appliedCoupon && (
                      <TouchableOpacity
                        className="mt-2 flex-row items-center"
                        onPress={() => {
                          setAppliedCoupon(null);
                          setCouponCode('');
                          setCouponError('');
                        }}
                      >
                        <Ionicons name="close-circle" size={14} color={colors.error} />
                        <Text className="ml-1 text-xs text-red-500">Remove coupon</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                )}
              </View>

              {/* Cart Items */}
              <View className="mt-6">
                <Text className="mb-3 font-bold text-slate-800">
                  Items ({cartItems.reduce((acc, i) => acc + i.quantity, 0)})
                </Text>
                {cartItems.map((item, idx) => {
                  const itemPrice = item.price !== undefined ? item.price : (item.product?.price || 0);
                  const itemSubtotal = item.subtotal !== undefined ? item.subtotal : (itemPrice * (item.quantity || 1));
                  return (
                    <View key={idx} className="flex-row items-center border-b border-slate-100 py-3">
                      <View className="flex-1 pr-4">
                        <Text className="font-medium text-slate-800" numberOfLines={2}>
                          {item.product?.name}
                        </Text>
                        <Text className="mt-1 text-xs text-slate-500">Qty: {item.quantity}</Text>
                      </View>
                      <Text className="font-bold text-slate-800">
                        ₹{itemSubtotal.toFixed(2)}
                      </Text>
                    </View>
                  );
                })}
                <View className="flex-row justify-between pt-4">
                  <Text className="font-bold text-slate-600">Subtotal</Text>
                  <Text className="text-lg font-bold text-slate-900">₹{cartTotal.toFixed(2)}</Text>
                </View>
                {appliedCoupon && (
                  <View className="flex-row justify-between pt-2">
                    <Text className="text-emerald-600">Coupon ({appliedCoupon.code})</Text>
                    <Text className="font-semibold text-emerald-600">
                      -₹{appliedCoupon.discount.toFixed(2)}
                    </Text>
                  </View>
                )}
                {deliveryChargeInfo && (
                  <View className="flex-row justify-between pt-2">
                    <Text className="text-slate-600">Delivery Charge</Text>
                    <Text className="font-semibold text-slate-900">
                      {deliveryChargeInfo.charge === 0 ? 'Free' : `₹${deliveryChargeInfo.charge.toFixed(2)}`}
                    </Text>
                  </View>
                )}
                {deliveryChargeInfo && deliveryChargeInfo.gstAmount > 0 && (
                  <View className="flex-row justify-between pt-2">
                    <Text className="text-slate-600">Delivery GST ({deliveryChargeInfo.gstPercentage}%)</Text>
                    <Text className="font-semibold text-slate-900">
                      ₹{deliveryChargeInfo.gstAmount.toFixed(2)}
                    </Text>
                  </View>
                )}
                <View className="mt-2 flex-row justify-between border-t border-slate-200 pt-3">
                  <Text className="font-bold text-slate-800">Total</Text>
                  <Text className="text-xl font-bold" style={{ color: colors.primary }}>
                    ₹{Math.max(
                      0,
                      cartTotal -
                        (appliedCoupon?.discount || 0) +
                        (deliveryChargeInfo?.totalCharge || 0),
                    ).toFixed(2)}
                  </Text>
                </View>
              </View>

              {/* Summary */}
              <View className="mt-4 rounded-2xl bg-neutral-50 p-4">
                <Text className="mb-3 font-bold text-neutral-900">Order Details</Text>

                <View className="mb-4 rounded-xl border border-neutral-100 bg-white p-3">
                  <View className="mb-2 flex-row items-center">
                    <Ionicons
                      name="location"
                      size={16}
                      color={colors.textSecondary}
                      style={{ marginRight: 6 }}
                    />
                    <Text className="text-sm font-semibold text-neutral-700">Delivery Address</Text>
                  </View>
                  <Text className="text-sm leading-relaxed text-neutral-800">
                    {getEffectiveAddress()}
                  </Text>
                </View>

                <View className="rounded-xl border border-neutral-100 bg-white p-3">
                  <View className="mb-2 flex-row items-center">
                    <Ionicons name="card" size={16} color={colors.textSecondary} style={{ marginRight: 6 }} />
                    <Text className="text-sm font-semibold text-neutral-700">Payment Method</Text>
                  </View>
                  <Text className="text-sm font-medium capitalize text-neutral-800">
                    {paymentMethod === 'cod'
                      ? 'Cash on Delivery'
                      : paymentMethod === 'upi'
                        ? 'UPI'
                        : 'Credit (B2B)'}
                  </Text>
                  {printedBill && (
                    <Text className="mt-1 text-xs font-medium text-emerald-600">
                      📄 Paper Bill Requested
                    </Text>
                  )}
                </View>
              </View>

              <View className="mt-6 flex-row gap-3">
                <TouchableOpacity
                  className="flex-1 items-center rounded-2xl bg-slate-100 py-4"
                  onPress={() => setStep(2)}
                >
                  <Text className="font-bold text-slate-600">Back</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  className="flex-1 items-center rounded-2xl py-4"
                  style={[shadows.lg, { backgroundColor: colors.primary }]}
                  onPress={placeOrder}
                  disabled={placing}
                >
                  {placing ? (
                    <ActivityIndicator color={colors.surface} />
                  ) : (
                    <Text className="font-bold text-white">Place Order</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>

      {/* ── Success overlay ── */}
      {orderSuccess && (
        <Animated.View
          style={[{ opacity: successOpacity }, { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255, 255, 255, 0.95)' }]}
        >
          <Animated.View
            style={[{ transform: [{ scale: successScale }] }, { alignItems: 'center', paddingHorizontal: 32 }]}
          >
            <View
              className="mb-6 h-24 w-24 items-center justify-center rounded-full"
              style={{ backgroundColor: `${colors.primary}20` }}
            >
              <Ionicons name="checkmark-circle" size={72} color={colors.primary} />
            </View>
            <Text className="mb-2 text-2xl font-bold text-slate-900">Order Placed!</Text>
            <Text className="mb-8 text-center text-slate-500">
              Your order has been placed successfully. We'll notify you when it ships.
            </Text>
            <TouchableOpacity
              className="w-full items-center rounded-2xl py-4"
              style={[shadows.lg, { backgroundColor: colors.primary }]}
              onPress={() => router.replace('/orders')}
            >
              <Text className="font-bold text-white">View My Orders</Text>
            </TouchableOpacity>
            <TouchableOpacity
              className="mt-3 w-full items-center rounded-2xl bg-slate-100 py-4"
              onPress={() => router.replace('/')}
            >
              <Text className="font-bold text-slate-600">Continue Shopping</Text>
            </TouchableOpacity>
          </Animated.View>
        </Animated.View>
      )}
    </SafeAreaView>
  );
}
