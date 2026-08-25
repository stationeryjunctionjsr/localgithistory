import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Animated,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../src/hooks/useAuth';
import api from '../src/api/client';
import { colors, animation } from '../src/theme';
import Toast from 'react-native-toast-message';

const InputField = ({
  icon,
  placeholder,
  value,
  onChangeText,
  secureTextEntry = false,
  showToggle = false,
  isVisible = false,
  onToggle = () => {},
  keyboardType = 'default' as any,
}: {
  icon: string;
  placeholder: string;
  value: string;
  onChangeText: (v: string) => void;
  secureTextEntry?: boolean;
  showToggle?: boolean;
  isVisible?: boolean;
  onToggle?: () => void;
  keyboardType?: any;
}) => (
  <View className="mb-4">
    <View className="flex-row items-center rounded-xl bg-neutral-100 px-4 py-3.5">
      <Ionicons name={icon as any} size={18} color="#9CA3AF" />
      <TextInput
        className="ml-3 flex-1 text-neutral-900"
        placeholder={placeholder}
        placeholderTextColor="#9CA3AF"
        value={value}
        onChangeText={onChangeText}
        secureTextEntry={secureTextEntry && !isVisible}
        autoCapitalize="none"
        keyboardType={keyboardType}
      />
      {showToggle && (
        <TouchableOpacity onPress={onToggle} activeOpacity={0.7}>
          <Ionicons
            name={isVisible ? 'eye-off-outline' : 'eye-outline'}
            size={18}
            color="#9CA3AF"
          />
        </TouchableOpacity>
      )}
    </View>
  </View>
);

export default function Login() {
  const router = useRouter();
  const { login } = useAuth();
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgot, setForgot] = useState({
    phone: '',
    otp: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [sendingOTP, setSendingOTP] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [canResend, setCanResend] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [verifyingOTP, setVerifyingOTP] = useState(false);
  const resendTimerRef = useRef<NodeJS.Timeout | null>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    return () => {
      if (resendTimerRef.current) clearTimeout(resendTimerRef.current);
    };
  }, []);

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: animation.normal,
      useNativeDriver: true,
    }).start();
  }, [fadeAnim]);

  const onLogin = async () => {
    if (!emailOrPhone || !password) {
      Toast.show({ type: 'error', text1: 'Missing info', text2: 'Please enter email/phone and password' });
      return;
    }
    setLoading(true);
    try {
      const user = await login(emailOrPhone, password);
      
      if (user?.role === 'admin' || user?.role === 'super_admin') {
        router.replace('/admin');
      } else if (user?.role === 'seller') {
        router.replace('/seller');
      } else if (user?.role === 'valet') {
        router.replace('/valet');
      } else {
        router.replace('/(tabs)/home');
      }
    } catch (e: any) {
      const data = e?.response?.data;
      const errorMsg =
        (Array.isArray(data?.detail) ? data.detail[0]?.msg : null) ||
        'Please check your credentials';
      Toast.show({ type: 'error', text1: 'Login failed', text2: errorMsg });
    }
    setLoading(false);
  };

  const sendForgotOTP = async () => {
    const cleanPhone = forgot.phone.replace(/\D/g, '');
    if (!cleanPhone || cleanPhone.length !== 10) {
      Toast.show({ type: 'error', text1: 'Invalid phone', text2: 'Enter a valid 10-digit phone number' });
      return;
    }
    setSendingOTP(true);
    try {
      await api.post('/auth/send-otp', { phone: cleanPhone, purpose: 'forgot_password' });
      setOtpSent(true);
      setCanResend(false);
      if (resendTimerRef.current) clearTimeout(resendTimerRef.current);
      resendTimerRef.current = setTimeout(() => {
        setCanResend(true);
      }, 30000);

      Toast.show({ type: 'success', text1: 'OTP sent', text2: 'Check your phone for the verification code' });
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Failed', text2: e?.response?.data?.message || 'Could not send OTP' });
    }
    setSendingOTP(false);
  };

  const verifyForgotOTP = async () => {
    if (!forgot.otp) {
      Toast.show({ type: 'error', text1: 'Missing OTP', text2: 'Please enter the verification code' });
      return;
    }
    setVerifyingOTP(true);
    try {
      await api.post('/auth/verify-otp', { phone: forgot.phone, otp: forgot.otp });
      setOtpVerified(true);
      if (resendTimerRef.current) clearTimeout(resendTimerRef.current);
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Invalid OTP', text2: e?.response?.data?.message || 'Please try again' });
    }
    setVerifyingOTP(false);
  };

  const resetPassword = async () => {
    if (!forgot.newPassword || forgot.newPassword !== forgot.confirmPassword) {
      Toast.show({ type: 'error', text1: 'Password mismatch', text2: 'Passwords do not match' });
      return;
    }
    if (forgot.newPassword.length < 6) {
      Toast.show({ type: 'error', text1: 'Weak password', text2: 'Password must be at least 6 characters' });
      return;
    }
    setLoading(true);
    try {
      await api.post('/auth/forgot-password', {
        phone: forgot.phone,
        newPassword: forgot.newPassword,
        otp: forgot.otp,
      });
      Toast.show({ type: 'success', text1: 'Password reset', text2: 'You can now login with your new password' });
      setShowForgot(false);
      setForgot({ phone: '', otp: '', newPassword: '', confirmPassword: '' });
      setOtpSent(false);
      setOtpVerified(false);
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Failed', text2: e?.response?.data?.message || 'Could not reset password' });
    }
    setLoading(false);
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#ffffff' }}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={{ flexGrow: 1, padding: 24 }}
          keyboardShouldPersistTaps="handled"
        >
          <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
            {/* Back button */}
            <TouchableOpacity
              className="-ml-2 mb-8 h-10 w-10 items-center justify-center"
              onPress={() => router.back()}
              activeOpacity={0.7}
            >
              <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
            </TouchableOpacity>

            {/* Title */}
            <Text className="mb-2 text-2xl font-semibold text-neutral-900">
              {showForgot ? 'Reset Password' : 'Welcome back'}
            </Text>
            <Text className="mb-8 text-neutral-500">
              {showForgot ? 'Enter your phone to reset' : 'Sign in to your account'}
            </Text>

            {!showForgot ? (
              <>
                <InputField
                  icon="person-outline"
                  placeholder="Email or phone"
                  value={emailOrPhone}
                  onChangeText={setEmailOrPhone}
                />

                <InputField
                  icon="lock-closed-outline"
                  placeholder="Password"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  showToggle
                  isVisible={showPassword}
                  onToggle={() => setShowPassword(!showPassword)}
                />

                <TouchableOpacity
                  className="mt-4 items-center rounded-xl bg-neutral-900 py-4"
                  onPress={onLogin}
                  disabled={loading}
                  activeOpacity={0.8}
                >
                  {loading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text className="font-semibold text-white">Sign In</Text>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  className="items-center py-4"
                  onPress={() => setShowForgot(true)}
                  activeOpacity={0.7}
                >
                  <Text className="text-neutral-500">Forgot password?</Text>
                </TouchableOpacity>

                <View className="flex-1" />

                <View className="items-center pb-4">
                  <Text className="text-neutral-500">
                    Don&apos;t have an account?{' '}
                    <Text
                      className="font-medium text-neutral-900"
                      onPress={() => router.push('/register')}
                    >
                      Sign up
                    </Text>
                  </Text>
                </View>
              </>
            ) : (
              <>
                <InputField
                  icon="call-outline"
                  placeholder="Phone number"
                  value={forgot.phone}
                  onChangeText={(v) => setForgot({ ...forgot, phone: v })}
                  keyboardType="phone-pad"
                />

                <View className="mb-4 flex-row gap-3">
                  <View className="flex-1">
                    <View className="flex-row items-center rounded-xl bg-neutral-100 px-4 py-3.5">
                      <TextInput
                        className="flex-1 text-neutral-900"
                        placeholder="OTP"
                        placeholderTextColor="#9CA3AF"
                        keyboardType="number-pad"
                        value={forgot.otp}
                        onChangeText={(v) => setForgot({ ...forgot, otp: v })}
                      />
                    </View>
                  </View>
                  <TouchableOpacity
                    className={`justify-center rounded-xl px-5 py-3 ${otpVerified ? 'bg-emerald-500' : 'bg-neutral-900'}`}
                    onPress={otpSent ? verifyForgotOTP : sendForgotOTP}
                    disabled={sendingOTP || verifyingOTP || otpVerified}
                    activeOpacity={0.8}
                  >
                    {sendingOTP || verifyingOTP ? (
                      <ActivityIndicator color="#fff" size="small" />
                    ) : otpVerified ? (
                      <Ionicons name="checkmark" size={18} color="#fff" />
                    ) : (
                      <Text className="text-sm font-medium text-white">
                        {otpSent ? 'Verify' : 'Send'}
                      </Text>
                    )}
                  </TouchableOpacity>
                </View>

                {otpSent && !otpVerified && (
                  <TouchableOpacity
                    className="mb-4 items-center"
                    onPress={sendForgotOTP}
                    disabled={sendingOTP || !canResend}
                    activeOpacity={0.7}
                  >
                    <Text
                      style={{
                        color: canResend ? colors.textPrimary : '#9CA3AF',
                        fontWeight: '500',
                      }}
                    >
                      {canResend ? 'Resend OTP' : 'Resend available in 30s'}
                    </Text>
                  </TouchableOpacity>
                )}

                {otpVerified && (
                  <>
                    <InputField
                      icon="lock-closed-outline"
                      placeholder="New password"
                      value={forgot.newPassword}
                      onChangeText={(v) => setForgot({ ...forgot, newPassword: v })}
                      secureTextEntry
                    />
                    <InputField
                      icon="lock-closed-outline"
                      placeholder="Confirm password"
                      value={forgot.confirmPassword}
                      onChangeText={(v) => setForgot({ ...forgot, confirmPassword: v })}
                      secureTextEntry
                    />
                  </>
                )}

                <TouchableOpacity
                  className={`mt-4 items-center rounded-xl py-4 ${otpVerified ? 'bg-neutral-900' : 'bg-neutral-300'}`}
                  onPress={resetPassword}
                  disabled={loading || !otpVerified}
                  activeOpacity={0.8}
                >
                  {loading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text className="font-semibold text-white">Reset Password</Text>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  className="items-center py-4"
                  onPress={() => setShowForgot(false)}
                  activeOpacity={0.7}
                >
                  <Text className="text-neutral-500">Back to login</Text>
                </TouchableOpacity>
              </>
            )}
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
