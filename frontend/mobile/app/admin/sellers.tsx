import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, ActivityIndicator, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import api from '../../src/api/client';
import { colors, shadows } from '../../src/theme';
import Toast from 'react-native-toast-message';

export default function AdminSellers() {
  const [sellers, setSellers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSellers = useCallback(async () => {
    try {
      // Trying the /commission/sellers endpoint or /users endpoint depending on the backend routes
      const res = await api.get('/users/sellers').catch(() => api.get('/users?role=seller'));
      if (res.data) {
        setSellers(Array.isArray(res.data) ? res.data : (res.data.users || []));
      }
    } catch (error) {
      console.error('Failed to fetch sellers:', error);
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to load sellers' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSellers();
  }, [fetchSellers]);

  const toggleStatus = async (id: string, currentStatus: boolean) => {
    try {
      await api.put(`/users/${id}/status`, { isActive: !currentStatus });
      Toast.show({ type: 'success', text1: 'Success', text2: 'Seller status updated' });
      fetchSellers();
    } catch (e) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Could not update seller' });
    }
  };

  const confirmToggle = (id: string, name: string, currentStatus: boolean) => {
    Alert.alert(
      `${currentStatus ? 'Deactivate' : 'Activate'} Seller?`,
      `Are you sure you want to ${currentStatus ? 'deactivate' : 'activate'} ${name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Confirm', onPress: () => toggleStatus(id, currentStatus), style: 'destructive' }
      ]
    );
  };

  if (loading) {
    return <ActivityIndicator size="large" color={colors.primary} style={{ flex: 1 }} />;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={sellers}
        keyExtractor={(item) => item.id || item._id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.info}>
              <Text style={styles.name}>{item.companyName || item.name || 'Unnamed Seller'}</Text>
              <Text style={styles.email}>{item.email}</Text>
              <Text style={styles.phone}>{item.phone || 'No phone provided'}</Text>
              <View style={[styles.badge, { backgroundColor: item.isActive ? '#D1FAE5' : '#FEE2E2' }]}>
                <Text style={[styles.badgeText, { color: item.isActive ? '#065F46' : '#991B1B' }]}>
                  {item.isActive ? 'ACTIVE' : 'INACTIVE'}
                </Text>
              </View>
            </View>
            <TouchableOpacity 
              style={[styles.btn, { backgroundColor: item.isActive ? '#DC2626' : '#10B981' }]}
              onPress={() => confirmToggle(item.id || item._id, item.companyName || item.name, item.isActive)}
            >
              <Text style={styles.btnText}>{item.isActive ? 'Deactivate' : 'Activate'}</Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F3F4F6' },
  list: { padding: 16 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...shadows.sm,
  },
  info: { flex: 1, marginRight: 12 },
  name: { fontSize: 16, fontWeight: '600', color: '#111827', marginBottom: 2 },
  email: { fontSize: 13, color: '#6B7280', marginBottom: 2 },
  phone: { fontSize: 13, color: '#6B7280', marginBottom: 6 },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 12 },
  badgeText: { fontSize: 10, fontWeight: '700' },
  btn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 6 },
  btnText: { color: '#fff', fontSize: 13, fontWeight: '600' }
});
