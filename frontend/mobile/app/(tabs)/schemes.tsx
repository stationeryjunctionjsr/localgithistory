import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import { useAuth } from '../../src/hooks/useAuth';
import api from '../../src/api/client';
import { colors, spacing, borderRadius, shadows, typography } from '../../src/theme';
import { formatDateIST } from '../../src/utils/dateUtils';

interface Scheme {
  _id: string;
  name: string;
  description?: string;
  discountType: string;
  discountValue: number;
  typeOfDiscount?: string;
  buyXGetYCustomerGetsQuantity?: number;
  buyXGetYCustomerGetsDiscountType?: string;
  buyXGetYCustomerGetsDiscountValue?: number;
  minRequirementType?: string;
  minQuantityOfEligibleItems?: number;
  minOrderValue?: number;
  validFrom?: string;
  validUntil?: string;
  code?: string;
}

export default function SchemesScreen() {
  const { user } = useAuth();
  const router = useRouter();
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isWholesaler = user?.role === 'wholesaler';

  const fetchSchemes = useCallback(async () => {
    if (!isWholesaler) return;
    try {
      setError(null);
      const res = await api.get<Scheme[]>('/schemes');
      setSchemes(Array.isArray(res.data) ? res.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.detail?.message || e?.message || 'Failed to load schemes');
      setSchemes([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isWholesaler]);

  useEffect(() => {
    if (isWholesaler) {
      setLoading(true);
      fetchSchemes();
    } else {
      setLoading(false);
      setSchemes([]);
    }
  }, [isWholesaler, fetchSchemes]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchSchemes();
  };

  const formatDate = (d?: string) => {
    return formatDateIST(d);
  };

  const formatOfferName = (scheme: Scheme) => {
    if (scheme.typeOfDiscount === 'buy_x_get_y') {
      const getQty = scheme.buyXGetYCustomerGetsQuantity || 1;
      let getDesc = 'Free';
      if (scheme.buyXGetYCustomerGetsDiscountType === 'percentage') {
        getDesc = `${scheme.buyXGetYCustomerGetsDiscountValue}% off`;
      } else if (scheme.buyXGetYCustomerGetsDiscountType === 'amount_off') {
        getDesc = `₹${scheme.buyXGetYCustomerGetsDiscountValue} off`;
      }

      const buyPart =
        scheme.minRequirementType === 'min_quantity'
          ? `Buy ${scheme.minQuantityOfEligibleItems}`
          : 'Buy';

      return `${buyPart} Get ${getQty} ${getDesc}`;
    } else {
      if (scheme.discountType === 'percentage') {
        return `${scheme.discountValue}% off`;
      } else {
        return `₹${scheme.discountValue} off`;
      }
    }
  };

  const renderScheme = ({ item }: { item: Scheme }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.schemeName}>{item.name}</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>
            {formatOfferName(item)}
          </Text>
        </View>
      </View>
      {item.description ? (
        <Text style={styles.description} numberOfLines={2}>
          {item.description}
        </Text>
      ) : null}
      {item.minOrderValue != null && item.minOrderValue > 0 && (
        <Text style={styles.meta}>Min. order: ₹{item.minOrderValue.toLocaleString()}</Text>
      )}
      {(item.validFrom || item.validUntil) && (
        <Text style={styles.meta}>
          {item.validFrom && `From ${formatDate(item.validFrom)}`}
          {item.validFrom && item.validUntil && ' • '}
          {item.validUntil && `Until ${formatDate(item.validUntil)}`}
        </Text>
      )}
      {item.code ? (
        <View style={styles.codeRow}>
          <Text style={styles.codeLabel}>Code: </Text>
          <Text style={styles.codeValue} selectable>
            {item.code}
          </Text>
          <TouchableOpacity
            style={styles.copyButton}
            onPress={async () => {
              await Clipboard.setStringAsync(item.code!);
              Alert.alert('Copied', 'Discount code copied to clipboard');
            }}
          >
            <Ionicons name="copy-outline" size={16} color={colors.primary} />
          </TouchableOpacity>
        </View>
      ) : null}
    </View>
  );

  if (!user) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.centered}>
          <Ionicons name="lock-closed" size={48} color={colors.neutral[400]} />
          <Text style={styles.emptyTitle}>Sign in required</Text>
          <Text style={styles.emptySubtitle}>Schemes are available for Business accounts.</Text>
          <TouchableOpacity style={styles.button} onPress={() => router.replace('/login')}>
            <Text style={styles.buttonText}>Sign in</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (!isWholesaler) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.centered}>
          <Ionicons name="briefcase-outline" size={48} color={colors.neutral[400]} />
          <Text style={styles.emptyTitle}>Business only</Text>
          <Text style={styles.emptySubtitle}>
            Discount schemes are available for Business Segment accounts.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Schemes</Text>
        <Text style={styles.subtitle}>Discount schemes for your business</Text>
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading schemes…</Text>
        </View>
      ) : error ? (
        <View style={styles.centered}>
          <Ionicons name="alert-circle-outline" size={48} color={colors.error} />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.button}
            onPress={() => {
              setLoading(true);
              fetchSchemes();
            }}
          >
            <Text style={styles.buttonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : schemes.length === 0 ? (
        <View style={styles.centered}>
          <Ionicons name="pricetag-outline" size={48} color={colors.neutral[400]} />
          <Text style={styles.emptyTitle}>No schemes yet</Text>
          <Text style={styles.emptySubtitle}>
            Discount schemes added for Business users will appear here.
          </Text>
        </View>
      ) : (
        <FlatList
          data={schemes}
          keyExtractor={(item) => item._id}
          renderItem={renderScheme}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              colors={[colors.primary]}
            />
          }
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
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  title: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 4,
  },
  listContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
    ...shadows.sm,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  schemeName: {
    ...typography.h3,
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },
  badge: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: borderRadius.sm,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textOnPrimary,
  },
  description: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  meta: {
    ...typography.caption,
    color: colors.textMuted,
    marginTop: 2,
  },
  codeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  codeLabel: {
    ...typography.caption,
    color: colors.textMuted,
  },
  codeValue: {
    ...typography.bodySmall,
    fontWeight: '600',
    color: colors.primary,
  },
  copyButton: {
    marginLeft: spacing.sm,
    padding: spacing.xs,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  emptyTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginTop: spacing.md,
    textAlign: 'center',
  },
  emptySubtitle: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    textAlign: 'center',
  },
  loadingText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  errorText: {
    ...typography.bodySmall,
    color: colors.error,
    marginTop: spacing.md,
    textAlign: 'center',
  },
  button: {
    marginTop: spacing.lg,
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.full,
  },
  buttonText: {
    ...typography.bodySmall,
    fontWeight: '600',
    color: colors.textOnPrimary,
  },
});
