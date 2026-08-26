import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, ScrollView, RefreshControl, ActivityIndicator, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../../src/api/client';
import { colors, shadows } from '../../src/theme';
import { useAuth } from '../../src/hooks/useAuth';

export default function SellerDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ total: 0, pending: 0, delivered: 0, revenue: 0 });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get('/orders/seller-orders?page=1&limit=100');
      const orders = res.data?.subOrders || [];
      const total = res.data?.totalCount || orders.length;
      const pending = orders.filter((o: any) => o.status === 'pending').length;
      const delivered = orders.filter((o: any) => o.status === 'delivered').length;
      const revenue = orders.filter((o: any) => o.status !== 'cancelled').reduce((s: number, o: any) => s + (o.total || 0), 0);
      
      setStats({ total, pending, delivered, revenue });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4f46e5" />
      </View>
    );
  }

  const cards = [
    { label: 'Total Orders', value: stats.total, icon: 'cube', color: '#6366f1' },
    { label: 'Pending', value: stats.pending, icon: 'time', color: '#f59e0b' },
    { label: 'Delivered', value: stats.delivered, icon: 'checkmark-circle', color: '#22c55e' },
    { label: 'Revenue (est.)', value: `₹${Math.round(stats.revenue).toLocaleString('en-IN')}`, icon: 'cash', color: '#3b82f6' },
  ];

  return (
    <ScrollView 
      style={styles.container} 
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Welcome back, {user?.companyName || user?.name || 'Seller'} 👋</Text>
        <Text style={styles.subtitle}>Here's a snapshot of your store performance</Text>
      </View>
      
      <View style={styles.grid}>
        {cards.map((card, idx) => (
          <View key={idx} style={[styles.card, { borderLeftColor: card.color, borderLeftWidth: 4 }]}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
              <Ionicons name={card.icon as any} size={22} color={card.color} />
            </View>
            <Text style={styles.cardValue}>{card.value}</Text>
            <Text style={styles.cardLabel}>{card.label}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: { padding: 20, paddingBottom: 10 },
  title: { fontSize: 20, fontWeight: '700', color: colors.neutral[900] },
  subtitle: { fontSize: 13, color: colors.neutral[500], marginTop: 4 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', padding: 10 },
  card: {
    width: '45%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    margin: '2.5%',
    ...shadows.sm,
  },
  cardValue: { fontSize: 22, fontWeight: '700', color: colors.neutral[900], marginBottom: 4 },
  cardLabel: { fontSize: 13, color: colors.neutral[600], fontWeight: '500' },
});
