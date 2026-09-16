import React, { useEffect, useState, useMemo, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../src/api/client';
import { useAuth } from '../src/hooks/useAuth';
import { colors, shadows } from '../src/theme';
import SearchablePicker from '../src/components/SearchablePicker';
import Toast from 'react-native-toast-message';

const InputField = ({
  label,
  value,
  onChangeText,
  placeholder,
  disabled,
  keyboardType,
  autoCapitalize,
  maxLength,
}: {
  label: string;
  value: string;
  onChangeText?: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
  keyboardType?: 'default' | 'email-address' | 'phone-pad' | 'url';
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  maxLength?: number;
}) => (
  <View style={styles.fieldContainer}>
    <Text style={styles.fieldLabel}>{label}</Text>
    <TextInput
      style={[styles.fieldInput, disabled && styles.fieldInputDisabled]}
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor={colors.textMuted}
      editable={!disabled}
      keyboardType={keyboardType}
      autoCapitalize={autoCapitalize}
      maxLength={maxLength}
    />
    {disabled && (
      <View style={styles.lockIcon}>
        <Ionicons name="lock-closed" size={14} color={colors.textMuted} />
      </View>
    )}
  </View>
);

export default function EditProfile() {
  const router = useRouter();
  const { user, fetchUser, logout } = useAuth();

  // Email verification state
  const [sendingVerificationCode, setSendingVerificationCode] = useState(false);
  const [verifyingEmail, setVerifyingEmail] = useState(false);
  const [showOtpInput, setShowOtpInput] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [emailVerificationCooldown, setEmailVerificationCooldown] = useState(0);

  useEffect(() => {
    if (emailVerificationCooldown > 0) {
      const timer = setTimeout(() => {
        setEmailVerificationCooldown((prev) => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [emailVerificationCooldown]);

  const handleRequestVerification = async () => {
    if (!formData.email) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Please enter an email address first.' });
      return;
    }
    try {
      setSendingVerificationCode(true);
      const response = await api.post('/users/request-email-verification');
      Toast.show({ type: 'success', text1: 'Code sent', text2: 'Check your email for the 6-digit code.' });
      setShowOtpInput(true);
      setEmailVerificationCooldown(60);
      if (response.data?.code) {
        // Dev/Test mode
        Alert.alert('Dev Mode', `Verification code: ${response.data.code}`);
      }
    } catch (error: any) {
      Toast.show({ type: 'error', text1: 'Error', text2: error.response?.data?.detail || 'Failed to send verification code.' });
    } finally {
      setSendingVerificationCode(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Please enter a valid 6-digit code.' });
      return;
    }
    try {
      setVerifyingEmail(true);
      await api.post('/users/verify-email', { code: verificationCode });
      Toast.show({ type: 'success', text1: 'Verified!', text2: 'Your email has been verified.' });
      setShowOtpInput(false);
      setVerificationCode('');
      await fetchUser?.();
    } catch (error: any) {
      Toast.show({ type: 'error', text1: 'Invalid code', text2: error.response?.data?.detail || 'Invalid or expired verification code.' });
    } finally {
      setVerifyingEmail(false);
    }
  };


  useEffect(() => {
    if (!user) {
      router.replace('/login' as any);
    }
  }, [user, router]);

  const [saving, setSaving] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [showPasswordSection, setShowPasswordSection] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    alternatePhone: '',
    companyName: '',
    gstin: '',
    locationLink: '',
    address: {
      name: '',
      street: '',
      addressLine2: '',
      landmark: '',
      city: '',
      district: '',
      state: '',
      pincode: '',
      country: '',
    },
  });

  const [initialData, setInitialData] = useState<typeof formData | null>(null);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [profileStates, setProfileStates] = useState<string[]>([]);
  const [profileDistricts, setProfileDistricts] = useState<string[]>([]);
  const [checkingPin, setCheckingPin] = useState(false);

  const fetchProfileStates = useCallback(async () => {
    try {
      const res = await api.get('/pincodes/states');
      setProfileStates(res.data || []);
    } catch {
      setProfileStates([]);
    }
  }, []);

  const fetchProfileDistricts = useCallback(async (state: string) => {
    if (!state) {
      setProfileDistricts([]);
      return;
    }
    try {
      const res = await api.get(`/pincodes/districts?state=${encodeURIComponent(state)}`);
      setProfileDistricts(res.data || []);
    } catch {
      setProfileDistricts([]);
    }
  }, []);

  useEffect(() => {
    fetchProfileStates();
  }, [fetchProfileStates]);

  useEffect(() => {
    if (user) {
      const pin = (user.address?.pincode || '').replace(/\D/g, '').slice(0, 6);
      const data = {
        name: user.name || '',
        email: user.email || '',
        phone: user.phone || '',
        alternatePhone: (user as any).alternatePhone || '',
        companyName: user.companyName || '',
        gstin: user.gstin || '',
        locationLink: user.locationLink || '',
        address: {
          name: user.address?.name || '',
          street: user.address?.street || '',
          addressLine2: user.address?.addressLine2 || '',
          landmark: user.address?.landmark || '',
          city: user.address?.city || '',
          district: user.address?.district || '',
          state: user.address?.state || '',
          pincode: pin,
          country: user.address?.country || 'India',
        },
      };
      setFormData(data);
      setInitialData(data);
      if (data.address.state) fetchProfileDistricts(data.address.state);
      else setProfileDistricts([]);
    }
  }, [user, fetchProfileDistricts]);

  const isChanged = useMemo(() => {
    if (!initialData) return false;
    return JSON.stringify(formData) !== JSON.stringify(initialData);
  }, [formData, initialData]);

  const updateField = (key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const updateAddress = (key: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      address: { ...prev.address, [key]: value },
    }));
  };

  const checkPincode = async () => {
    const pin = (formData.address.pincode || '').replace(/\D/g, '').slice(0, 6);
    if (pin.length !== 6) {
      Alert.alert('Error', 'Enter a valid 6-digit pincode');
      return;
    }
    setCheckingPin(true);
    try {
      const res = await api.get('/delivery-charges/check-serviceability', {
        params: { pincode: pin, userRole: (user as any)?.role || 'customer' },
      });
      if (!res.data?.isServiceable) {
        Alert.alert('Not serviceable', 'This pincode is not serviceable for delivery.');
      } else {
        Alert.alert('Serviceable', 'We deliver to this pincode.');
      }
    } catch {
      Alert.alert('Error', 'Failed to verify pincode.');
    } finally {
      setCheckingPin(false);
    }
  };

  const handleSave = async () => {
    if (!isChanged) return;
    const pin = (formData.address.pincode || '').replace(/\D/g, '').slice(0, 6);
    if (!formData.address.state?.trim() || !formData.address.district?.trim()) {
      Alert.alert('Required', 'Please select state and district.');
      return;
    }
    if (pin.length !== 6) {
      Alert.alert('Required', 'Please enter a valid 6-digit pincode.');
      return;
    }
    setSaving(true);
    try {
      const payload = { ...formData, address: { ...formData.address, pincode: pin } };
      await api.put(`/users/${user?._id}`, payload);
      Alert.alert('Success', 'Profile updated successfully');
      setFormData(payload);
      setInitialData(payload);
    } catch (error: any) {
      const msg = error.response?.data?.message || error.response?.data?.detail || 'Failed to update profile';
      Alert.alert('Error', msg);
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      Alert.alert('Error', 'New passwords do not match');
      return;
    }
    if (passwordData.newPassword.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters');
      return;
    }
    setChangingPassword(true);
    try {
      await api.put(`/users/${user?._id}/password`, {
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword,
      });
      Alert.alert('Success', 'Password changed successfully');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setShowPasswordSection(false);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.message || 'Failed to change password');
    } finally {
      setChangingPassword(false);
    }
  };

  const handleDeactivate = async () => {
    Alert.alert(
      'Deactivate Account?',
      'Are you sure? This action will restrict your access to the platform until support re-activates it.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Yes, Deactivate',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.put('/users/me/deactivate');
              Toast.show({ type: 'success', text1: 'Success', text2: 'Account deactivated successfully.' });
              await logout?.();
              router.replace('/login' as any);
            } catch (error: any) {
              const msg = error.response?.data?.message || 'Failed to deactivate account';
              Alert.alert('Error', msg);
            }
          },
        },
      ]
    );
  };

  const handleDeleteAccount = async () => {
    Alert.alert(
      'Permanently Delete Account?',
      'Are you absolutely sure? This will delete all your personal data, order histories, and login credentials permanently. This action is irreversible.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Permanently Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete('/auth/me');
              Toast.show({ type: 'success', text1: 'Success', text2: 'Your account has been deleted.' });
              await logout?.();
              router.replace('/login' as any);
            } catch (error: any) {
              const msg = error.response?.data?.message || 'Failed to delete account';
              Alert.alert('Error', msg);
            }
          },
        },
      ]
    );
  };

  const isWholesaler = user?.role === 'wholesaler';

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={[styles.header, shadows.sm]}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={20} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Edit Profile</Text>
        <TouchableOpacity
          style={[styles.saveButton, !isChanged && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={!isChanged || saving}
        >
          {saving ? (
            <ActivityIndicator size="small" color={colors.surface} />
          ) : (
            <Text style={[styles.saveButtonText, !isChanged && styles.saveButtonTextDisabled]}>Save</Text>
          )}
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Personal Details */}
          <View style={[styles.section, shadows.sm]}>
            <Text style={styles.sectionTitle}>Personal Details</Text>
            <InputField label="Name" value={formData.name} onChangeText={(v) => updateField('name', v)} placeholder="Full name" />

            {/* Email field with verification */}
            <View style={styles.fieldContainer}>
              <View style={styles.emailLabelRow}>
                <Text style={styles.fieldLabel}>Email</Text>
                {user?.email && (
                  <View style={[
                    styles.verifiedBadge,
                    (user as any).isEmailVerified ? styles.verifiedBadgeGreen : styles.verifiedBadgeYellow,
                  ]}>
                    {(user as any).isEmailVerified && (
                      <Ionicons name="checkmark" size={10} color="#15803d" />
                    )}
                    <Text style={[
                      styles.verifiedBadgeText,
                      (user as any).isEmailVerified ? styles.verifiedBadgeTextGreen : styles.verifiedBadgeTextYellow,
                    ]}>
                      {(user as any).isEmailVerified ? 'Verified' : 'Unverified'}
                    </Text>
                  </View>
                )}
              </View>
              <View style={styles.emailInputRow}>
                <TextInput
                  style={[styles.fieldInput, styles.emailInput]}
                  value={formData.email}
                  onChangeText={(v) => updateField('email', v)}
                  placeholder="Email address"
                  placeholderTextColor={colors.textMuted}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
                {user?.email && !(user as any).isEmailVerified && (
                  <TouchableOpacity
                    style={[
                      styles.verifyButton,
                      (sendingVerificationCode || emailVerificationCooldown > 0) && styles.verifyButtonDisabled,
                    ]}
                    onPress={handleRequestVerification}
                    disabled={sendingVerificationCode || emailVerificationCooldown > 0}
                  >
                    <Text style={styles.verifyButtonText}>
                      {emailVerificationCooldown > 0
                        ? `${emailVerificationCooldown}s`
                        : sendingVerificationCode
                        ? '...'
                        : 'Verify'}
                    </Text>
                  </TouchableOpacity>
                )}
              </View>
              {showOtpInput && (
                <View style={styles.otpContainer}>
                  <Text style={styles.otpLabel}>Enter 6-digit verification code</Text>
                  <View style={styles.otpRow}>
                    <TextInput
                      style={styles.otpInput}
                      value={verificationCode}
                      onChangeText={(v) => setVerificationCode(v.replace(/\D/g, '').slice(0, 6))}
                      placeholder="000000"
                      placeholderTextColor={colors.textMuted}
                      keyboardType="number-pad"
                      maxLength={6}
                    />
                    <TouchableOpacity
                      style={[
                        styles.otpSubmitButton,
                        (verifyingEmail || verificationCode.length !== 6) && styles.otpSubmitButtonDisabled,
                      ]}
                      onPress={handleVerifyCode}
                      disabled={verifyingEmail || verificationCode.length !== 6}
                    >
                      {verifyingEmail ? (
                        <ActivityIndicator size="small" color={colors.surface} />
                      ) : (
                        <Text style={styles.otpSubmitButtonText}>Submit</Text>
                      )}
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>

            <InputField label="Phone" value={formData.phone} disabled placeholder="Phone number" />
            <InputField label="Alternate Phone" value={formData.alternatePhone} onChangeText={(v) => updateField('alternatePhone', v)} placeholder="Optional alternate phone" keyboardType="phone-pad" />
          </View>

          {/* Business Details */}
          {isWholesaler && (
            <View style={[styles.section, shadows.sm]}>
              <Text style={styles.sectionTitle}>Business Details</Text>
              <InputField label="Company Name" value={formData.companyName} onChangeText={(v) => updateField('companyName', v)} placeholder="Company name" />
              <InputField label="GSTIN" value={formData.gstin} onChangeText={(v) => updateField('gstin', v.toUpperCase())} placeholder="15-digit GSTIN (Optional)" maxLength={15} autoCapitalize="characters" />
              <InputField label="Location Link" value={formData.locationLink} onChangeText={(v) => updateField('locationLink', v)} placeholder="Google Maps link" keyboardType="url" autoCapitalize="none" />
            </View>
          )}

          {/* Address */}
          <View style={[styles.section, shadows.sm]}>
            <Text style={styles.sectionTitle}>Address</Text>
            <InputField label="Recipient Name" value={formData.address.name} onChangeText={(v) => updateAddress('name', v)} placeholder="Recipient name" />
            <InputField label="Street" value={formData.address.street} onChangeText={(v) => updateAddress('street', v)} placeholder="Street address" />
            <InputField label="Address Line 2" value={formData.address.addressLine2} onChangeText={(v) => updateAddress('addressLine2', v)} placeholder="Apt, suite, etc." />
            <InputField label="Landmark" value={formData.address.landmark} onChangeText={(v) => updateAddress('landmark', v)} placeholder="Near landmark" />
            <InputField label="City *" value={formData.address.city} onChangeText={(v) => updateAddress('city', v)} placeholder="City" />
            <SearchablePicker
              label="State *"
              options={profileStates}
              value={formData.address.state}
              onChange={(val) => {
                setFormData((p) => ({
                  ...p,
                  address: { ...p.address, state: val, district: '' },
                }));
                fetchProfileDistricts(val);
              }}
              placeholder="Select State"
              icon="location-outline"
            />
            <SearchablePicker
              label="District *"
              options={profileDistricts}
              value={formData.address.district}
              onChange={(val) => setFormData((p) => ({ ...p, address: { ...p.address, district: val } }))}
              placeholder="Select District"
              disabled={!formData.address.state}
              icon="map-outline"
            />
            <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 12, marginBottom: 14 }}>
              <View style={{ flex: 1 }}>
                <Text style={styles.fieldLabel}>PIN Code *</Text>
                <TextInput
                  style={styles.fieldInput}
                  value={formData.address.pincode}
                  onChangeText={(v) =>
                    updateAddress('pincode', v.replace(/\D/g, '').slice(0, 6))
                  }
                  placeholder="6-digit PIN"
                  placeholderTextColor={colors.textMuted}
                  keyboardType="number-pad"
                  maxLength={6}
                />
              </View>
              <TouchableOpacity
                style={{
                  marginBottom: 2,
                  paddingHorizontal: 16,
                  paddingVertical: 12,
                  borderRadius: 10,
                  backgroundColor: colors.neutral[100],
                }}
                onPress={checkPincode}
                disabled={checkingPin}
              >
                {checkingPin ? (
                  <ActivityIndicator size="small" color={colors.primary} />
                ) : (
                  <Text style={{ fontWeight: '600', color: colors.primary }}>Check</Text>
                )}
              </TouchableOpacity>
            </View>
            <InputField label="Country" value={formData.address.country} onChangeText={(v) => updateAddress('country', v)} placeholder="Country" />
          </View>

          {/* Password Section */}
          <View style={[styles.section, shadows.sm]}>
            <TouchableOpacity
              style={styles.passwordToggle}
              onPress={() => setShowPasswordSection(!showPasswordSection)}
            >
              <View style={styles.passwordToggleLeft}>
                <Ionicons name="key-outline" size={20} color={colors.primary} />
                <Text style={styles.sectionTitle}>Change Password</Text>
              </View>
              <Ionicons name={showPasswordSection ? 'chevron-up' : 'chevron-down'} size={20} color={colors.textSecondary} />
            </TouchableOpacity>

            {showPasswordSection && (
              <View style={styles.passwordFields}>
                <InputField label="Current Password" value={passwordData.currentPassword} onChangeText={(v) => setPasswordData((p) => ({ ...p, currentPassword: v }))} placeholder="Enter current password" autoCapitalize="none" />
                <InputField label="New Password" value={passwordData.newPassword} onChangeText={(v) => setPasswordData((p) => ({ ...p, newPassword: v }))} placeholder="Enter new password" autoCapitalize="none" />
                <InputField label="Confirm New Password" value={passwordData.confirmPassword} onChangeText={(v) => setPasswordData((p) => ({ ...p, confirmPassword: v }))} placeholder="Confirm new password" autoCapitalize="none" />
                <TouchableOpacity
                  style={styles.changePasswordButton}
                  onPress={handlePasswordChange}
                  disabled={changingPassword}
                >
                  {changingPassword ? (
                    <ActivityIndicator size="small" color={colors.surface} />
                  ) : (
                    <Text style={styles.changePasswordButtonText}>Update Password</Text>
                  )}
                </TouchableOpacity>
              </View>
            )}
          </View>

          {/* Danger Zone */}
          <View style={[styles.section, shadows.sm, { borderColor: '#fee2e2', borderWidth: 1 }]}>
            <Text style={[styles.sectionTitle, { color: colors.error }]}>Danger Zone</Text>
            
            <View style={styles.dangerItem}>
              <Text style={styles.dangerTitle}>Deactivate Account</Text>
              <Text style={styles.dangerDesc}>
                Temporarily pause your account. You will not be able to log in until support re-activates it.
              </Text>
              <TouchableOpacity
                style={styles.deactivateButton}
                onPress={handleDeactivate}
              >
                <Text style={styles.deactivateButtonText}>Deactivate My Account</Text>
              </TouchableOpacity>
            </View>

            <View style={[styles.dangerItem, { marginTop: 20, borderTopWidth: 1, borderTopColor: '#fecaca', paddingTop: 20 }]}>
              <Text style={styles.dangerTitle}>Permanently Delete Account</Text>
              <Text style={styles.dangerDesc}>
                GDPR Right-to-Erasure. This will permanently delete your account, order history, and personal data. This action is irreversible.
              </Text>
              <TouchableOpacity
                style={styles.deleteButton}
                onPress={handleDeleteAccount}
              >
                <Text style={styles.deleteButtonText}>Permanently Delete My Account</Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.backgroundAlt },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: colors.neutral[100],
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: colors.textPrimary },
  saveButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 10,
    minWidth: 70,
    alignItems: 'center',
  },
  saveButtonDisabled: { backgroundColor: colors.neutral[200] },
  saveButtonText: { color: colors.surface, fontWeight: '600', fontSize: 14 },
  saveButtonTextDisabled: { color: colors.textMuted },
  scrollContent: { padding: 16 },
  section: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 16,
  },
  fieldContainer: { marginBottom: 14 },
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: 6,
  },
  fieldInput: {
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
  },
  fieldInputDisabled: {
    backgroundColor: colors.neutral[100],
    color: colors.textMuted,
  },
  lockIcon: {
    position: 'absolute',
    right: 14,
    top: 38,
  },
  // Email verification styles
  emailLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  emailInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  emailInput: {
    flex: 1,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    borderRadius: 20,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderWidth: 1,
  },
  verifiedBadgeGreen: {
    backgroundColor: '#f0fdf4',
    borderColor: '#bbf7d0',
  },
  verifiedBadgeYellow: {
    backgroundColor: '#fefce8',
    borderColor: '#fde68a',
  },
  verifiedBadgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  verifiedBadgeTextGreen: {
    color: '#15803d',
  },
  verifiedBadgeTextYellow: {
    color: '#a16207',
  },
  verifyButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 10,
  },
  verifyButtonDisabled: {
    backgroundColor: colors.neutral[200],
  },
  verifyButtonText: {
    color: colors.surface,
    fontWeight: '700',
    fontSize: 13,
  },
  otpContainer: {
    marginTop: 10,
    backgroundColor: '#eff6ff',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#bfdbfe',
    padding: 12,
  },
  otpLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1d4ed8',
    marginBottom: 8,
  },
  otpRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  otpInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.borderMedium,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 4,
    textAlign: 'center',
    color: colors.textPrimary,
    backgroundColor: colors.surface,
  },
  otpSubmitButton: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  otpSubmitButtonDisabled: {
    backgroundColor: colors.neutral[200],
  },
  otpSubmitButtonText: {
    color: colors.surface,
    fontWeight: '700',
    fontSize: 13,
  },
  passwordToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  passwordToggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  passwordFields: { marginTop: 16 },
  changePasswordButton: {
    backgroundColor: colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  changePasswordButtonText: {
    color: colors.surface,
    fontWeight: '600',
    fontSize: 15,
  },
  dangerItem: {
    width: '100%',
  },
  dangerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  dangerDesc: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 16,
    marginBottom: 12,
  },
  deactivateButton: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.error,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deactivateButtonText: {
    color: colors.error,
    fontWeight: '600',
    fontSize: 14,
  },
  deleteButton: {
    backgroundColor: colors.error,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteButtonText: {
    color: colors.surface,
    fontWeight: '600',
    fontSize: 14,
  },
});
