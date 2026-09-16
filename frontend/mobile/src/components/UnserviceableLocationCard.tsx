import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { usePincode } from '../context/PincodeContext';
import { colors } from '../theme';


export default function UnserviceableLocationCard() {
  const { pincode, city, state, openModal } = usePincode();

  return (
    <View style={styles.container}>
      <View style={styles.iconCircle}>
        <Ionicons name="location-outline" size={40} color="#b45309" />
      </View>

      <Text style={styles.title}>
        We are not in your city yet, but we will come soon!
      </Text>

      <Text style={styles.subtitle}>
        Delivery is currently unavailable for{' '}
        <Text style={styles.boldText}>
          PIN code {pincode || 'entered'}
          {city ? ` (${city}${state ? `, ${state}` : ''})` : ''}
        </Text>
        . We operate hyperlocally with local store partners and are launching in your area very soon!
      </Text>

      <TouchableOpacity
        style={styles.actionButton}
        onPress={() => openModal(false)}
        activeOpacity={0.8}
      >
        <Ionicons name="navigate-outline" size={18} color={colors.surface} style={styles.buttonIcon} />
        <Text style={styles.actionButtonText}>Check Another Pincode</Text>
      </TouchableOpacity>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>Local Store Partner?</Text>
        <Text style={styles.infoText}>
          Are you a stationery seller or retailer in this locality? Partner with us to serve customers in your neighborhood.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 24,
    paddingVertical: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#fef3c7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#fde68a',
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 28,
  },
  subtitle: {
    fontSize: 14,
    color: '#4b5563',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 28,
  },
  boldText: {
    fontWeight: '700',
    color: '#111827',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 14,
    shadowColor: colors.textPrimary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 4,
    marginBottom: 32,
  },
  buttonIcon: {
    marginRight: 8,
  },
  actionButtonText: {
    color: colors.surface,
    fontSize: 15,
    fontWeight: '700',
  },
  infoCard: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderStyle: 'dashed',
    borderRadius: 16,
    padding: 16,
    width: '100%',
  },
  infoTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
    marginBottom: 4,
  },
  infoText: {
    fontSize: 12,
    color: '#6b7280',
    lineHeight: 18,
  },
});
