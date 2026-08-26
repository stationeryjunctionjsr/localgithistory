import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, ScrollView, RefreshControl, ActivityIndicator, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../../src/api/client';
import { colors, shadows } from '../../src/theme';

interface DashboardStats {
  totalProducts: number;
  totalWholesalers: number;
  totalCustomers: number;
  totalValets: number;
  totalOrders: number;
  totalRevenue: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = useCallback(async () => {
    try {
      const response = await api.get('/analytics/dashboard-data');
      if (response.data?.stats) {
        setStats(response.data.stats);
      }
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
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  const formatCurrency = (val: number) => `₹${(val || 0).toLocaleString('en-IN')}`;

  const cards = [
    { label: 'Revenue', value: formatCurrency(stats?.totalRevenue || 0), icon: 'cash', color: '#10B981' },
    { label: 'Orders', value: stats?.totalOrders || 0, icon: 'cart', color: '#3B82F6' },
    { label: 'Products', value: stats?.totalProducts || 0, icon: 'cube', color: '#F59E0B' },
    { label: 'Customers', value: stats?.totalCustomers || 0, icon: 'people', color: '#8B5CF6' },
    { label: 'Wholesalers', value: stats?.totalWholesalers || 0, icon: 'business', color: '#EC4899' },
    { label: 'Valets', value: stats?.totalValets || 0, icon: 'bicycle', color: '#14B8A6' },
  ];

  return (
    <ScrollView 
      style={styles.container} 
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Admin Overview</Text>
        <Text style={styles.subtitle}>All-time platform statistics</Text>
      </View>
      <View style={styles.grid}>
        {cards.map((card, idx) => (
          <View key={idx} style={styles.card}>
            <View style={[styles.iconWrapper, { backgroundColor: card.color + '20' }]}>
              <Ionicons name={card.icon as any} size={24} color={card.color} />
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
  title: { fontSize: 24, fontWeight: '700', color: colors.neutral[900] },
  subtitle: { fontSize: 14, color: colors.neutral[500], marginTop: 4 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', padding: 10 },
  card: {
    width: '45%',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    margin: '2.5%',
    ...shadows.sm,
  },
  iconWrapper: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardValue: { fontSize: 20, fontWeight: '700', color: colors.neutral[900], marginBottom: 4 },
  cardLabel: { fontSize: 13, color: colors.neutral[600], fontWeight: '500' },
});
