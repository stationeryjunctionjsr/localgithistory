import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, ActivityIndicator, StyleSheet, TouchableOpacity } from 'react-native';
import api from '../../src/api/client';
import { colors, shadows } from '../../src/theme';
import Toast from 'react-native-toast-message';
import { useRouter } from 'expo-router';

export default function AdminOrders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchOrders = useCallback(async () => {
    try {
      // Assuming /orders returns all orders for admin
      const res = await api.get('/orders?limit=50');
      setOrders(res.data?.orders || Array.isArray(res.data) ? res.data : []);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to load orders' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered': return '#10B981';
      case 'shipped': return '#3B82F6';
      case 'cancelled': return '#EF4444';
      case 'pending': return '#F59E0B';
      default: return '#6B7280';
    }
  };

  if (loading) {
    return <ActivityIndicator size="large" color={colors.primary} style={{ flex: 1 }} />;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={orders}
        keyExtractor={(item) => item.id || item._id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <TouchableOpacity 
            style={styles.card}
            onPress={() => router.push(`/orders/${item.id || item._id}`)}
          >
            <View style={styles.header}>
              <Text style={styles.orderId}>Order #{String(item.id || item._id).substring(0, 8).toUpperCase()}</Text>
              <View style={[styles.badge, { backgroundColor: getStatusColor(item.status) + '20' }]}>
                <Text style={[styles.badgeText, { color: getStatusColor(item.status) }]}>
                  {(item.status || 'UNKNOWN').toUpperCase()}
                </Text>
              </View>
            </View>
            
            <View style={styles.details}>
                <Text style={styles.date}>{new Date(item.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })}</Text>
              <Text style={styles.total}>₹{(item.totalAmount || 0).toLocaleString('en-IN')}</Text>
            </View>
            
            <View style={styles.customerInfo}>
              <Text style={styles.customerText}>Customer: {item.user?.name || item.userId || 'Guest'}</Text>
              <Text style={styles.itemsText}>{item.items?.length || 0} items</Text>
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  list: { padding: 16 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    ...shadows.sm,
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  orderId: { fontSize: 16, fontWeight: '700', color: '#111827' },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
  badgeText: { fontSize: 10, fontWeight: '700' },
  details: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  date: { fontSize: 13, color: '#6B7280' },
  total: { fontSize: 15, fontWeight: '600', color: colors.primary },
  customerInfo: { flexDirection: 'row', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: '#F3F4F6', paddingTop: 8 },
  customerText: { fontSize: 12, color: '#4B5563' },
  itemsText: { fontSize: 12, color: '#6B7280' },
});
