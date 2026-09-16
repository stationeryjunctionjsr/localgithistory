import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Modal,
  TextInput,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, shadows, typography, spacing } from '../src/theme';
import { useAuth } from '../src/hooks/useAuth';
import { useAuthStore } from '../src/store/authStore';
import api from '../src/api/client';
import SearchablePicker from '../src/components/SearchablePicker';

interface Address {
  name?: string;
  street?: string;
  addressLine2?: string;
  landmark?: string;
  city?: string;
  district?: string;
  state?: string;
  country?: string;
  pincode?: string;
  zipCode?: string;
  mobileNumber?: string;
}

const emptyAddress: Address = {
  name: '',
  street: '',
  addressLine2: '',
  landmark: '',
  city: '',
  district: '',
  state: '',
  country: 'India',
  pincode: '',
  mobileNumber: '',
};

export default function Addresses() {
  const router = useRouter();
  const { user } = useAuth();
  const { setUser } = useAuthStore();

  const [modalVisible, setModalVisible] = useState(false);
  const [editIndex, setEditIndex] = useState<number | null>(null);
  const [form, setForm] = useState<Address>(emptyAddress);
  const [saving, setSaving] = useState(false);
  const [addrStates, setAddrStates] = useState<string[]>([]);
  const [addrDistricts, setAddrDistricts] = useState<string[]>([]);
  const [checkingPin, setCheckingPin] = useState(false);

  const savedAddresses: Address[] = (user as any)?.savedAddresses || [];

  const fetchAddrStates = useCallback(async () => {
    try {
      const res = await api.get('/pincodes/states');
      setAddrStates(res.data || []);
    } catch {
      setAddrStates([]);
    }
  }, []);

  const fetchAddrDistricts = useCallback(async (state: string) => {
    if (!state) {
      setAddrDistricts([]);
      return;
    }
    try {
      const res = await api.get(`/pincodes/districts?state=${encodeURIComponent(state)}`);
      setAddrDistricts(res.data || []);
    } catch {
      setAddrDistricts([]);
    }
  }, []);

  useEffect(() => {
    fetchAddrStates();
  }, [fetchAddrStates]);

  useEffect(() => {
    if (modalVisible && form.state) {
      fetchAddrDistricts(form.state);
    } else if (modalVisible && !form.state) {
      setAddrDistricts([]);
    }
  }, [modalVisible, form.state, fetchAddrDistricts]);

  const openAdd = () => {
    setEditIndex(null);
    setForm(emptyAddress);
    setAddrDistricts([]);
    setModalVisible(true);
  };

  const openEdit = (idx: number) => {
    setEditIndex(idx);
    const addr = savedAddresses[idx];
    const pin = (addr.pincode || addr.zipCode || '').toString().replace(/\D/g, '').slice(0, 6);
    setForm({
      name: addr.name || '',
      street: addr.street || '',
      addressLine2: addr.addressLine2 || '',
      landmark: addr.landmark || '',
      city: addr.city || '',
      district: addr.district || '',
      state: addr.state || '',
      country: addr.country || 'India',
      pincode: pin,
      mobileNumber: addr.mobileNumber || '',
    });
    if (addr.state) fetchAddrDistricts(addr.state);
    setModalVisible(true);
  };

  const checkPincode = async () => {
    const pin = (form.pincode || '').replace(/\D/g, '').slice(0, 6);
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

  const saveAddress = async () => {
    const pin = (form.pincode || '').replace(/\D/g, '').slice(0, 6);
    if (
      !form.street?.trim() ||
      !form.city?.trim() ||
      !form.state?.trim() ||
      !form.district?.trim() ||
      pin.length !== 6
    ) {
      Alert.alert(
        'Required Fields',
        'Please fill in Street, City, State, District, and a valid 6-digit Pincode.'
      );
      return;
    }
    setSaving(true);
    try {
      const newAddress: Address = { ...form, pincode: pin, zipCode: pin };
      let updated: Address[];
      if (editIndex !== null) {
        updated = savedAddresses.map((a, i) => (i === editIndex ? newAddress : a));
      } else {
        updated = [...savedAddresses, newAddress];
      }
      const res = await api.put(`/users/${(user as any)?._id}`, { savedAddresses: updated });
      setUser(res.data);
      setModalVisible(false);
    } catch (err: any) {
      Alert.alert('Error', err?.response?.data?.detail || 'Could not save address.');
    } finally {
      setSaving(false);
    }
  };

  const deleteAddress = (idx: number) => {
    Alert.alert('Delete Address', 'Are you sure you want to remove this address?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            const updated = savedAddresses.filter((_, i) => i !== idx);
            const res = await api.put(`/users/${(user as any)?._id}`, { savedAddresses: updated });
            setUser(res.data);
          } catch {
            Alert.alert('Error', 'Could not delete address.');
          }
        },
      },
    ]);
  };

  const renderAddress = ({ item, index }: { item: Address; index: number }) => (
    <View style={[styles.card, shadows.sm]}>
      <View style={styles.cardHeader}>
        <View style={styles.iconContainer}>
          <Ionicons name="location" size={20} color={colors.primary} />
        </View>
        <Text style={styles.cardTitle}>Address {index + 1}</Text>
        <View style={styles.cardActions}>
          <TouchableOpacity onPress={() => openEdit(index)} style={styles.actionBtn}>
            <Ionicons name="pencil-outline" size={18} color={colors.textSecondary} />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => deleteAddress(index)} style={styles.actionBtn}>
            <Ionicons name="trash-outline" size={18} color={colors.error} />
          </TouchableOpacity>
        </View>
      </View>
      <View style={styles.addressDetails}>
        {item.name ? <Text style={[styles.addressText, { fontWeight: 'bold' }]}>{item.name}</Text> : null}
        <Text style={styles.addressText}>{item.street}</Text>
        {item.addressLine2 ? <Text style={styles.addressText}>{item.addressLine2}</Text> : null}
        {item.landmark ? <Text style={styles.addressText}>Landmark: {item.landmark}</Text> : null}
        <Text style={styles.addressText}>
          {[item.city, item.district, item.state].filter(Boolean).join(', ')}
        </Text>
        <Text style={styles.addressText}>
          {item.country || 'India'} - {item.pincode || item.zipCode}
        </Text>
      </View>
      {item.mobileNumber ? (
        <View style={styles.phoneContainer}>
          <Ionicons name="call-outline" size={16} color={colors.textSecondary} />
          <Text style={styles.phoneText}>{item.mobileNumber}</Text>
        </View>
      ) : null}
    </View>
  );

  const field = (label: string, key: keyof Address, opts?: { keyboardType?: any; maxLength?: number }) => (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        style={styles.fieldInput}
        value={form[key] as string}
        onChangeText={(v) => setForm((f) => ({ ...f, [key]: v }))}
        placeholder={label}
        placeholderTextColor={colors.textMuted}
        keyboardType={opts?.keyboardType || 'default'}
        maxLength={opts?.maxLength}
      />
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />

      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Saved Addresses</Text>
        <TouchableOpacity style={styles.addBtn} onPress={openAdd}>
          <Ionicons name="add" size={24} color={colors.primary} />
        </TouchableOpacity>
      </View>

      {savedAddresses.length === 0 ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="map-outline" size={48} color={colors.primary} />
          </View>
          <Text style={styles.emptyTitle}>No Saved Addresses</Text>
          <Text style={styles.emptySubtitle}>
            Add an address to speed up checkout.
          </Text>
          <TouchableOpacity style={styles.addAddressBtn} onPress={openAdd}>
            <Ionicons name="add-circle-outline" size={18} color={colors.surface} />
            <Text style={styles.addAddressBtnText}>Add Address</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={savedAddresses}
          keyExtractor={(_, idx) => String(idx)}
          renderItem={renderAddress}
          contentContainerStyle={styles.listContent}
        />
      )}

      {/* Add / Edit Modal */}
      <Modal visible={modalVisible} animationType="slide" onRequestClose={() => setModalVisible(false)}>
        <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setModalVisible(false)} style={styles.backBtn}>
              <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>{editIndex !== null ? 'Edit Address' : 'Add Address'}</Text>
            <View style={{ width: 40 }} />
          </View>
          <ScrollView contentContainerStyle={styles.modalBody}>
            {field('Full Name', 'name')}
            {field('Street / House No.', 'street')}
            {field('Address Line 2 (Optional)', 'addressLine2')}
            {field('Landmark (Optional)', 'landmark')}
            {field('City', 'city')}
            <SearchablePicker
              label="State *"
              options={addrStates}
              value={form.state || ''}
              onChange={(val) => setForm((f) => ({ ...f, state: val, district: '' }))}
              placeholder="Select State"
              icon="location-outline"
            />
            <SearchablePicker
              label="District *"
              options={addrDistricts}
              value={form.district || ''}
              onChange={(val) => setForm((f) => ({ ...f, district: val }))}
              placeholder="Select District"
              disabled={!form.state}
              icon="map-outline"
            />
            {field('Country', 'country')}
            <View style={styles.fieldWrap}>
              <Text style={styles.fieldLabel}>Pincode *</Text>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                <TextInput
                  style={[styles.fieldInput, { flex: 1 }]}
                  value={form.pincode as string}
                  onChangeText={(v) =>
                    setForm((f) => ({ ...f, pincode: v.replace(/\D/g, '').slice(0, 6) }))
                  }
                  placeholder="6-digit PIN"
                  placeholderTextColor={colors.textMuted}
                  keyboardType="number-pad"
                  maxLength={6}
                />
                <TouchableOpacity
                  style={{
                    paddingHorizontal: 14,
                    paddingVertical: 11,
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
            </View>
            {field('Mobile Number', 'mobileNumber', { keyboardType: 'phone-pad', maxLength: 10 })}

            <TouchableOpacity
              style={[styles.saveBtn, saving && { opacity: 0.6 }]}
              onPress={saveAddress}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color={colors.surface} size="small" />
              ) : (
                <Text style={styles.saveBtnText}>{editIndex !== null ? 'Save Changes' : 'Add Address'}</Text>
              )}
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.backgroundAlt },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
  },
  backBtn: { padding: spacing.xs, marginLeft: -spacing.xs },
  addBtn: { padding: spacing.xs },
  headerTitle: { ...typography.h3, color: colors.textPrimary },
  emptyContainer: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32 },
  emptyIcon: {
    width: 88, height: 88, borderRadius: 44, backgroundColor: '#E8F5E9',
    alignItems: 'center', justifyContent: 'center', marginBottom: 20,
  },
  emptyTitle: { ...typography.h2, color: colors.textPrimary, marginBottom: 8 },
  emptySubtitle: { ...typography.body, color: colors.textMuted, textAlign: 'center', marginBottom: 24 },
  addAddressBtn: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.primary,
    paddingVertical: 12, paddingHorizontal: 24, borderRadius: 24, gap: 8,
  },
  addAddressBtnText: { color: colors.surface, fontWeight: '700', fontSize: 15 },
  listContent: { padding: spacing.md },
  card: {
    backgroundColor: colors.surface, borderRadius: 12, padding: spacing.md,
    marginBottom: spacing.md, borderWidth: 1, borderColor: colors.border,
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
  iconContainer: {
    width: 32, height: 32, borderRadius: 16, backgroundColor: '#E8F5E9',
    alignItems: 'center', justifyContent: 'center', marginRight: 10,
  },
  cardTitle: { ...typography.h3, color: colors.textPrimary, flex: 1 },
  cardActions: { flexDirection: 'row', gap: 4 },
  actionBtn: { padding: 6 },
  addressDetails: { borderLeftWidth: 2, borderLeftColor: colors.border, paddingLeft: 12, marginLeft: 15 },
  addressText: { ...typography.body, color: colors.textSecondary, marginBottom: 4, lineHeight: 20 },
  phoneContainer: { flexDirection: 'row', alignItems: 'center', marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: colors.border },
  phoneText: { ...typography.body, fontWeight: '600', color: colors.textPrimary, marginLeft: 8 },
  modalHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.md, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border, backgroundColor: colors.surface,
  },
  modalBody: { padding: spacing.md, paddingBottom: 48 },
  fieldWrap: { marginBottom: spacing.md },
  fieldLabel: { ...typography.label, color: colors.textSecondary, marginBottom: 6 },
  fieldInput: {
    borderWidth: 1, borderColor: colors.border, borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 11, fontSize: 15,
    color: colors.textPrimary, backgroundColor: colors.surface,
  },
  saveBtn: {
    backgroundColor: colors.primary, borderRadius: 14, paddingVertical: 15,
    alignItems: 'center', marginTop: spacing.lg,
  },
  saveBtnText: { color: colors.surface, fontWeight: '700', fontSize: 16 },
});
