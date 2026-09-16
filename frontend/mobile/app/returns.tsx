import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../src/api/client';
import { colors, spacing, borderRadius, shadows, typography } from '../src/theme';

interface ReturnRequest {
  _id: string;
  orderId: string;
  createdAt: string;
  status: string;
  deliveryCharge?: number;
  paymentMethod?: string;
  notes?: string;
  items?: any[];
  valet?: { name: string };
}

export default function ReturnsScreen() {
  const router = useRouter();
  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReturns = async () => {
    setLoading(true);
    try {
      const res = await api.get('/returns/my-returns');
      setReturns(res.data || []);
    } catch (err) {
      if (__DEV__) console.warn('Failed to fetch returns history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReturns();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pending':
      case 'pending_valet':
        return '#B45309'; // amber-700
      case 'assigned':
        return '#1D4ED8'; // blue-700
      case 'collected':
        return '#6D28D9'; // purple-700
      case 'returned':
        return '#15803D'; // green-700
      case 'rejected':
        return '#B91C1C'; // red-700
      default:
        return colors.textSecondary;
    }
  };

  const getStatusBg = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pending':
      case 'pending_valet':
        return '#FEF3C7'; // amber-100
      case 'assigned':
        return '#DBEAFE'; // blue-100
      case 'collected':
        return '#F3E8FF'; // purple-100
      case 'returned':
        return '#DCFCE7'; // green-100
      case 'rejected':
        return '#FEE2E2'; // red-100
      default:
        return colors.neutral[100];
    }
  };

  const renderReturnItem = ({ item }: { item: ReturnRequest }) => {
    const dateStr = new Date(item.createdAt).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View>
            <Text style={styles.idLabel}>RETURN ID</Text>
            <Text style={styles.idValue}>#{item._id?.slice(-8)}</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: getStatusBg(item.status) }]}>
            <Text style={[styles.badgeText, { color: getStatusColor(item.status) }]}>
              {item.status?.toUpperCase()}
            </Text>
          </View>
        </View>

        <View style={styles.cardBody}>
          <Text style={styles.metaText}>Requested: {dateStr}</Text>
          <Text style={styles.metaText}>Order ID: #{item.orderId?.slice(-8)}</Text>

          <View style={styles.divider} />

          <Text style={styles.sectionTitle}>Items:</Text>
          {item.items?.map((it, idx) => (
            <View key={idx} style={styles.productRow}>
              <Text style={styles.productName} numberOfLines={1}>
                {it.product?.name || 'Product'}
              </Text>
              <Text style={styles.productQty}>Qty: {it.quantity}</Text>
            </View>
          ))}

          {item.deliveryCharge !== undefined && (
            <View style={styles.chargeRow}>
              <Text style={styles.chargeLabel}>Pickup Charge ({item.paymentMethod?.toUpperCase()}):</Text>
              <Text style={styles.chargeValue}>₹{item.deliveryCharge}</Text>
            </View>
          )}

          {item.valet && (
            <View style={styles.valetBox}>
              <Text style={styles.valetText}>🚚 Assigned Valet: {item.valet.name}</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>My Returns</Text>
        <TouchableOpacity onPress={fetchReturns} style={styles.refreshBtn}>
          <Ionicons name="refresh" size={20} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : returns.length === 0 ? (
        <View style={styles.center}>
          <Ionicons name="arrow-undo-outline" size={48} color={colors.neutral[300]} />
          <Text style={styles.emptyText}>No return requests found</Text>
        </View>
      ) : (
        <FlatList
          data={returns}
          keyExtractor={(item) => item._id}
          renderItem={renderReturnItem}
          contentContainerStyle={{ padding: spacing.md }}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backBtn: { padding: 4 },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  refreshBtn: { padding: 4 },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  emptyText: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.neutral[50],
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  idLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.textMuted,
  },
  idValue: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textPrimary,
    fontFamily: 'monospace',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: borderRadius.sm,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '700',
  },
  cardBody: {
    padding: spacing.md,
  },
  metaText: {
    fontSize: 11,
    color: colors.textSecondary,
    marginBottom: 4,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: spacing.sm,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textMuted,
    marginBottom: spacing.xs,
  },
  productRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  productName: {
    fontSize: 12,
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },
  productQty: {
    fontSize: 11,
    color: colors.textSecondary,
  },
  chargeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
    paddingTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: colors.neutral[100],
  },
  chargeLabel: {
    fontSize: 11,
    color: colors.textSecondary,
  },
  chargeValue: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  valetBox: {
    backgroundColor: '#EFF6FF',
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  valetText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#1E40AF',
  },
});
