import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  Modal,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { usePincode } from '../context/PincodeContext';
import { useAuth } from '../hooks/useAuth';
import { colors, borderRadius, shadows } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export const PincodeModal: React.FC = () => {
  const {
    isModalOpen,
    isMandatory,
    pincode: currentPincode,
    city: currentCity,
    state: currentState,
    sellerCount,
    isLoading,
    error,
    checkAndSetPincode,
    closeModal,
  } = usePincode();

  const { user } = useAuth();
  const [enteredPin, setEnteredPin] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{
    city?: string | null;
    state?: string | null;
    sellerCount?: number;
    pincode?: string;
  } | null>(null);

  const inputRef = useRef<TextInput>(null);

  useEffect(() => {
    if (isModalOpen) {
      setEnteredPin(currentPincode || '');
      setLocalError(null);
      setSuccessInfo(null);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 150);
    }
  }, [isModalOpen, currentPincode]);

  if (!isModalOpen) return null;

  const handleSubmit = async () => {
    setLocalError(null);
    setSuccessInfo(null);

    const clean = enteredPin.replace(/\D/g, '').slice(0, 6);
    if (clean.length !== 6) {
      setLocalError('Please enter a valid 6-digit PIN code.');
      return;
    }

    const role = (user as any)?.role || 'customer';
    const result = await checkAndSetPincode(clean, role);

    if (result.success && result.isServiceable) {
      setSuccessInfo({
        city: result.data?.city,
        state: result.data?.state,
        sellerCount: result.data?.sellerCount,
        pincode: clean,
      });
    } else {
      setLocalError(
        result.message ||
          `Sorry, we do not currently service pincode ${clean}. Please try another pincode.`
      );
    }
  };

  const handleChangeText = (text: string) => {
    const clean = text.replace(/\D/g, '').slice(0, 6);
    setEnteredPin(clean);
    setLocalError(null);
    setSuccessInfo(null);
  };

  return (
    <Modal
      visible={isModalOpen}
      transparent={true}
      animationType="fade"
      onRequestClose={() => {
        if (!isMandatory) {
          closeModal();
        }
      }}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.overlay}
      >
        <View style={styles.card}>
          {/* Top Decorative Bar */}
          <View style={styles.topAccentBar} />

          {/* Close button if voluntary */}
          {!isMandatory && currentPincode ? (
            <TouchableOpacity
              style={styles.closeButton}
              onPress={closeModal}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Ionicons name="close" size={22} color={colors.textSecondary} />
            </TouchableOpacity>
          ) : null}

          {/* Icon and Header */}
          <View style={styles.header}>
            <View style={styles.iconCircle}>
              <Ionicons name="location-sharp" size={32} color="#1a4d33" />
            </View>
            <Text style={styles.title}>
              {isMandatory ? 'Select Delivery Location' : 'Change Delivery Location'}
            </Text>
            <Text style={styles.subtitle}>
              We operate hyperlocally to deliver fast service from verified local sellers. Enter your 6-digit PIN code to start shopping.
            </Text>
          </View>

          {/* Input Box */}
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Enter 6-Digit Pincode *</Text>
            <View style={styles.inputWrapper}>
              <TextInput
                ref={inputRef}
                style={styles.input}
                value={enteredPin}
                onChangeText={handleChangeText}
                placeholder="e.g. 831001"
                placeholderTextColor="#9CA3AF"
                keyboardType="number-pad"
                maxLength={6}
                autoFocus={true}
              />
              {enteredPin.length > 0 && (
                <TouchableOpacity
                  style={styles.clearBtn}
                  onPress={() => {
                    setEnteredPin('');
                    setLocalError(null);
                  }}
                >
                  <Ionicons name="close-circle" size={20} color="#9CA3AF" />
                </TouchableOpacity>
              )}
            </View>
          </View>

          {/* Error Message */}
          {(localError || error) && (
            <View style={styles.errorContainer}>
              <Ionicons name="alert-circle" size={18} color="#DC2626" style={styles.errorIcon} />
              <Text style={styles.errorText}>{localError || error}</Text>
            </View>
          )}

          {/* Success Info Card */}
          {successInfo && (
            <View style={styles.successContainer}>
              <Ionicons name="checkmark-circle" size={20} color="#059669" style={styles.successIcon} />
              <View style={styles.successTextWrapper}>
                <Text style={styles.successTitle}>
                  Serviceable in {successInfo.city || 'your location'} ({successInfo.pincode})
                </Text>
                <Text style={styles.successSubtitle}>
                  {successInfo.sellerCount && successInfo.sellerCount > 0
                    ? `🎉 ${successInfo.sellerCount} seller(s) available to deliver to you!`
                    : '🎉 Platform delivery is available!'}
                </Text>
              </View>
            </View>
          )}

          {/* Action Button */}
          <TouchableOpacity
            style={[
              styles.submitButton,
              (isLoading || enteredPin.length !== 6) && styles.submitButtonDisabled,
            ]}
            onPress={handleSubmit}
            disabled={isLoading || enteredPin.length !== 6}
            activeOpacity={0.8}
          >
            {isLoading ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator color="#FFFFFF" size="small" />
                <Text style={styles.submitButtonText}>Verifying Location...</Text>
              </View>
            ) : (
              <Text style={styles.submitButtonText}>Check & Continue</Text>
            )}
          </TouchableOpacity>

          {/* Current set pincode reminder */}
          {currentPincode && !isMandatory ? (
            <Text style={styles.footerText}>
              Currently delivering to:{' '}
              <Text style={styles.footerBold}>
                {currentCity ? `${currentCity} (${currentPincode})` : currentPincode}
              </Text>
            </Text>
          ) : null}
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  card: {
    width: SCREEN_WIDTH - 40,
    maxWidth: 400,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    padding: 24,
    overflow: 'hidden',
    ...shadows.lg,
  },
  topAccentBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 4,
    backgroundColor: '#1a4d33',
  },
  closeButton: {
    position: 'absolute',
    top: 14,
    right: 14,
    zIndex: 10,
    padding: 4,
  },
  header: {
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 20,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 13,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 8,
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#374151',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  inputWrapper: {
    position: 'relative',
    justifyContent: 'center',
  },
  input: {
    height: 52,
    borderWidth: 1.5,
    borderColor: '#D1D5DB',
    borderRadius: borderRadius.lg,
    paddingHorizontal: 16,
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: 6,
    textAlign: 'center',
    color: '#111827',
    backgroundColor: '#F9FAFB',
  },
  clearBtn: {
    position: 'absolute',
    right: 12,
    padding: 4,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: borderRadius.md,
    padding: 10,
    marginBottom: 14,
  },
  errorIcon: {
    marginRight: 8,
    marginTop: 1,
  },
  errorText: {
    flex: 1,
    fontSize: 12,
    color: '#B91C1C',
    lineHeight: 16,
  },
  successContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: borderRadius.md,
    padding: 10,
    marginBottom: 14,
  },
  successIcon: {
    marginRight: 8,
  },
  successTextWrapper: {
    flex: 1,
  },
  successTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#065F46',
  },
  successSubtitle: {
    fontSize: 11,
    color: '#047857',
    marginTop: 2,
  },
  submitButton: {
    height: 48,
    backgroundColor: '#1a4d33',
    borderRadius: borderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#1a4d33',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  footerText: {
    marginTop: 12,
    fontSize: 11,
    color: '#6B7280',
    textAlign: 'center',
  },
  footerBold: {
    fontWeight: '700',
    color: '#374151',
  },
});

export default PincodeModal;
