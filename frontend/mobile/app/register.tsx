import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../src/api/client';
import { colors, shadows } from '../src/theme';
import Toast from 'react-native-toast-message';

interface InputFieldProps {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder: string;
  keyboardType?: 'default' | 'email-address' | 'phone-pad' | 'number-pad';
  secureTextEntry?: boolean;
  showToggle?: boolean;
  isVisible?: boolean;
  onToggle?: () => void;
}

const InputField = ({
  icon,
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType = 'default',
  secureTextEntry = false,
  showToggle = false,
  isVisible = false,
  onToggle = () => {},
}: InputFieldProps) => (
  <View className="mb-4">
    <Text className="mb-2 font-medium text-slate-700">{label}</Text>
    <View className="flex-row items-center rounded-xl bg-slate-100 px-4 py-3">
      <Ionicons name={icon} size={18} color="#64748B" />
      <TextInput
        className="ml-3 flex-1 text-slate-800"
        placeholder={placeholder}
        placeholderTextColor="#94A3B8"
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType}
        secureTextEntry={secureTextEntry && !isVisible}
        autoCapitalize={keyboardType === 'email-address' ? 'none' : 'sentences'}
      />
      {showToggle && (
        <TouchableOpacity onPress={onToggle}>
          <Ionicons
            name={isVisible ? 'eye-off-outline' : 'eye-outline'}
            size={18}
            color="#64748B"
          />
        </TouchableOpacity>
      )}
    </View>
  </View>
);

export default function Register() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [canResend, setCanResend] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [sendingOTP, setSendingOTP] = useState(false);
  const [verifyingOTP, setVerifyingOTP] = useState(false);
  const resendTimerRef = useRef<NodeJS.Timeout | null>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    return () => {
      if (resendTimerRef.current) clearTimeout(resendTimerRef.current);
    };
  }, []);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 400, useNativeDriver: true }),
    ]).start();
  }, [fadeAnim, slideAnim]);

  const sendOTP = async () => {
    const cleanPhone = phone.replace(/\D/g, '');
    if (!cleanPhone || cleanPhone.length !== 10) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Enter a valid 10-digit phone number' });
      return;
    }
    setSendingOTP(true);
    try {
      await api.post('/auth/send-otp', { phone: cleanPhone, purpose: 'register' });
      setOtpSent(true);
      setCanResend(false);
      if (resendTimerRef.current) clearTimeout(resendTimerRef.current);
      resendTimerRef.current = setTimeout(() => {
        setCanResend(true);
      }, 30000);

      Toast.show({ type: 'success', text1: 'Success', text2: 'OTP sent to phone' });
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Error', text2: e?.response?.data?.message || 'Failed to send OTP' });
    }
    setSendingOTP(false);
  };

  const verifyOTP = async () => {
    if (!otp) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Enter OTP' });
      return;
    }
    setVerifyingOTP(true);
    const cleanPhone = phone.replace(/\D/g, '');
    try {
      await api.post('/auth/verify-otp', { phone: cleanPhone, otp });
      setOtpVerified(true);
      if (resendTimerRef.current) clearTimeout(resendTimerRef.current);
      Toast.show({ type: 'success', text1: 'Success', text2: 'Phone verified' });
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Error', text2: e?.response?.data?.message || 'Invalid OTP' });
    }
    setVerifyingOTP(false);
  };

  const onRegister = async () => {
    if (!name.trim()) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Full name is required' });
      return;
    }
    if (!email.trim() || !/\S+@\S+\.\S+/.test(email.trim())) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'A valid email address is required' });
      return;
    }
    if (!otpVerified) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Please verify OTP first' });
      return;
    }
    if (!password || password !== confirmPassword) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Passwords do not match' });
      return;
    }
    if (password.length < 6) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Password must be at least 6 characters' });
      return;
    }
    setLoading(true);
    const cleanPhone = phone.replace(/\D/g, '');
    try {
      await api.post('/auth/register', {
        name,
        email,
        phone: cleanPhone,
        password,
        role: 'customer',
        otp,
      });
      Toast.show({
        type: 'success',
        text1: 'Success',
        text2: 'Registered successfully! Please login.',
      });
      setTimeout(() => router.push('/login'), 2000);
    } catch (e: any) {
      const data = e?.response?.data;
      const errorMsg =
        (typeof data?.detail === 'string' ? data.detail : null) ||
        data?.message ||
        (Array.isArray(data?.detail) ? data.detail[0]?.msg : null) ||
        'Please check details';
      Toast.show({ type: 'error', text1: 'Registration failed', text2: errorMsg });
    }
    setLoading(false);
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F8FAFC' }}>
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ flexGrow: 1, padding: 20 }}
        keyboardShouldPersistTaps="handled"
      >
        <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
          {/* Back Button */}
          <TouchableOpacity
            className="-ml-2 mb-4 h-10 w-10 items-center justify-center"
            onPress={() => router.back()}
            activeOpacity={0.7}
          >
            <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
          </TouchableOpacity>

          {/* Logo/Brand */}
          <View className="mb-6 items-center">
            <View
              className="mb-4 h-20 w-20 items-center justify-center rounded-2xl"
              style={[shadows.lg, { backgroundColor: colors.primary }]}
            >
              <Ionicons name="person-add" size={40} color="#fff" />
            </View>
            <Text className="text-2xl font-bold text-slate-800">Create Account</Text>
            <Text className="mt-1 text-slate-500">Join us and start shopping</Text>
          </View>

          {/* Card */}
          <View className="rounded-3xl bg-white p-6" style={shadows.lg}>
            <InputField
              icon="person-outline"
              label="Full Name"
              value={name}
              onChangeText={setName}
              placeholder="John Doe"
            />

            <InputField
              icon="mail-outline"
              label="Email"
              value={email}
              onChangeText={setEmail}
              placeholder="john@example.com"
              keyboardType="email-address"
            />

            <InputField
              icon="call-outline"
              label="Phone"
              value={phone}
              onChangeText={(v) => setPhone(v.replace(/\D/g, '').slice(0, 10))}
              placeholder="10-digit phone"
              keyboardType="phone-pad"
            />

            {/* OTP Section */}
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
                  />
                </View>
              </View>
              <View className="justify-end">
                <TouchableOpacity
                  className={`rounded-xl px-4 py-3 ${otpVerified ? 'bg-emerald-500' : otpSent ? 'bg-amber-500' : ''}`}
                  style={!otpVerified && !otpSent ? { backgroundColor: colors.primary } : {}}
                  onPress={otpSent ? verifyOTP : sendOTP}
                  disabled={sendingOTP || verifyingOTP || otpVerified}
                >
                  {sendingOTP || verifyingOTP ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : otpVerified ? (
                    <Ionicons name="checkmark" size={20} color="#fff" />
                  ) : (
                    <Text className="text-sm font-semibold text-white">
                      {otpSent ? 'Verify' : 'Send'}
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>

            {otpSent && !otpVerified && (
              <TouchableOpacity
                className="mb-4 items-center"
                onPress={sendOTP}
                disabled={sendingOTP || !canResend}
              >
                <Text
                  style={{
                    color: canResend ? colors.primary : '#94A3B8',
                    fontWeight: '500',
                    fontSize: 13,
                  }}
                >
                  {canResend ? 'Resend OTP' : 'Resend available in 30s'}
                </Text>
              </TouchableOpacity>
            )}

            <InputField
              icon="lock-closed-outline"
              label="Password"
              value={password}
              onChangeText={setPassword}
              placeholder="Min 6 characters"
              secureTextEntry
              showToggle
              isVisible={showPassword}
              onToggle={() => setShowPassword(!showPassword)}
            />

            <InputField
              icon="lock-closed-outline"
              label="Confirm Password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="Re-enter password"
              secureTextEntry
              showToggle
              isVisible={showConfirm}
              onToggle={() => setShowConfirm(!showConfirm)}
            />

            {/* Register Button */}
            <TouchableOpacity
              className="mt-2 items-center rounded-2xl py-4"
              style={otpVerified ? [shadows.lg, { backgroundColor: colors.primary }] : { backgroundColor: '#cbd5e1' }}
              onPress={onRegister}
              disabled={loading || !otpVerified}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text className="text-base font-bold text-white">Create Account</Text>
              )}
            </TouchableOpacity>

            {/* Login Link */}
            <TouchableOpacity className="items-center py-4" onPress={() => router.push('/login')}>
              <Text className="text-slate-500">
                Already have an account?{' '}
                <Text className="font-semibold" style={{ color: colors.primary }}>Login</Text>
              </Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}
