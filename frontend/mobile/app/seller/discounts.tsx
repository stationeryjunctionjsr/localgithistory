import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator } from 'react-native';
import api from '../../src/api/client';
import { shadows } from '../../src/theme';

export default function SellerDiscounts() {
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/coupons')
      .then(res => setCoupons(res.data || []))
      .catch((e: any) => console.warn('Background task failed', e))
      .finally(() => setLoading(false));
  }, []);

  const renderItem = ({ item }: { item: any }) => (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.type}>
          {item.typeOfDiscount === 'product_discount' ? 'Product Discount' : item.typeOfDiscount === 'buy_x_get_y' ? 'Buy X Get Y' : item.typeOfDiscount}
        </Text>
        <View style={[styles.badge, { backgroundColor: item.isActive ? '#D1FAE5' : '#F3F4F6' }]}>
          <Text style={[styles.badgeText, { color: item.isActive ? '#065F46' : '#6B7280' }]}>
            {item.isActive ? 'ACTIVE' : 'INACTIVE'}
          </Text>
        </View>
      </View>
      <Text style={styles.value}>
        {item.discountType === 'percentage' ? `${item.discountValue}% OFF` : `₹${item.discountValue} OFF`}
      </Text>
      <Text style={styles.note}>Manage details from the Seller Web Portal.</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      {loading ? (
        <ActivityIndicator size="large" color="#4f46e5" style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={coupons}
          keyExtractor={c => c._id}
          contentContainerStyle={styles.list}
          renderItem={renderItem}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyText}>No discounts yet</Text>
              <Text style={styles.emptySubText}>Create discounts from the Seller Web Portal.</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  list: { padding: 16 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12,
    ...shadows.sm,
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  type: { fontSize: 14, fontWeight: '700', color: '#111827' },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
  badgeText: { fontSize: 10, fontWeight: '700' },
  value: { fontSize: 18, fontWeight: '800', color: '#4f46e5', marginBottom: 8 },
  note: { fontSize: 12, color: '#6B7280' },
  empty: { alignItems: 'center', paddingTop: 60 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#374151' },
  emptySubText: { fontSize: 13, color: '#9CA3AF', marginTop: 8 },
});
