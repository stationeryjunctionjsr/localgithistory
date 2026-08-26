import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, ActivityIndicator, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import api from '../../src/api/client';
import { colors, shadows } from '../../src/theme';
import Toast from 'react-native-toast-message';

export default function SellerOrders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchOrders = useCallback(async () => {
    try {
      const res = await api.get('/orders/seller-orders?page=1&limit=50');
      setOrders(res.data?.subOrders || []);
    } catch (error) {
      console.error('Failed to fetch seller orders:', error);
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to load orders' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const updateStatus = async (id: string, newStatus: string) => {
    try {
      await api.put(`/orders/seller-orders/${id}/status`, { status: newStatus });
      Toast.show({ type: 'success', text1: 'Success', text2: 'Status updated' });
      fetchOrders();
    } catch (error: any) {
      Toast.show({ type: 'error', text1: 'Update Failed', text2: error?.response?.data?.detail || 'Failed to update status' });
    }
  };

  const showStatusOptions = (order: any) => {
    const options = [
      { text: 'Mark as Processing', onPress: () => updateStatus(order._id, 'processing') },
      { text: 'Mark as Shipped', onPress: () => updateStatus(order._id, 'shipped') },
      { text: 'Cancel Order', onPress: () => updateStatus(order._id, 'cancelled'), style: 'destructive' as any },
      { text: 'Close', style: 'cancel' as any },
    ];
    
    Alert.alert(
      'Update Order Status',
      `Select new status for Sub-Order #${order.subOrderNumber}`,
      options
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered': return '#10B981';
      case 'shipped': return '#3B82F6';
      case 'cancelled': return '#EF4444';
      case 'pending': return '#F59E0B';
      case 'processing': return '#8B5CF6';
      case 'pending_valet': return '#F59E0B';
      default: return '#6B7280';
    }
  };

  if (loading) {
    return <ActivityIndicator size="large" color="#4f46e5" style={{ flex: 1 }} />;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={orders}
        keyExtractor={(item) => item._id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <TouchableOpacity 
            style={styles.card}
            onPress={() => showStatusOptions(item)}
          >
            <View style={styles.header}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Text style={styles.orderId}>{item.subOrderNumber}</Text>
                {item.isUrgentDelivery && <Text style={{ marginLeft: 6, fontSize: 12 }}>⚡</Text>}
              </View>
              <View style={[styles.badge, { backgroundColor: getStatusColor(item.status) + '20' }]}>
                <Text style={[styles.badgeText, { color: getStatusColor(item.status) }]}>
                  {item.status.replace(/_/g, ' ').toUpperCase()}
                </Text>
              </View>
            </View>
            
            <View style={styles.details}>
              <Text style={styles.date}>{new Date(item.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })}</Text>
              <Text style={styles.total}>₹{(item.total || 0).toLocaleString('en-IN')}</Text>
            </View>
            
            <View style={styles.customerInfo}>
              <Text style={styles.customerText}>Items: {item.items?.length || 0}</Text>
              <Text style={styles.actionText}>Tap to update status</Text>
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
  orderId: { fontSize: 15, fontWeight: '700', color: '#4f46e5' },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
  badgeText: { fontSize: 10, fontWeight: '700' },
  details: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  date: { fontSize: 13, color: '#6B7280' },
  total: { fontSize: 15, fontWeight: '700', color: '#111827' },
  customerInfo: { flexDirection: 'row', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: '#F3F4F6', paddingTop: 8, marginTop: 4 },
  customerText: { fontSize: 12, color: '#4B5563', fontWeight: '500' },
  actionText: { fontSize: 12, color: '#4f46e5', fontWeight: '600' },
});
