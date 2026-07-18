import React, { useEffect, useState, useCallback, useRef } from 'react';
import { OrdersListSkeleton } from '../../src/components/SkeletonLoader';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../../src/api/client';
import { colors, shadows } from '../../src/theme';
import { formatDateIST } from '../../src/utils/dateUtils';

const PAGE_SIZE = 10;

interface Order {
  _id?: string;
  status?: string;
  total?: number;
  createdAt?: string;
  paymentMethod?: string;
}

const statusColors: { [key: string]: { bg: string; text: string; icon: string } } = {
  pending: { bg: 'bg-amber-100', text: 'text-amber-700', icon: 'time-outline' },
  processing: { bg: 'bg-blue-100', text: 'text-blue-700', icon: 'reload-outline' },
  shipped: { bg: 'bg-purple-100', text: 'text-purple-700', icon: 'airplane-outline' },
  delivered: { bg: 'bg-emerald-100', text: 'text-emerald-700', icon: 'checkmark-circle-outline' },
  cancelled: { bg: 'bg-red-100', text: 'text-red-700', icon: 'close-circle-outline' },
  default: { bg: 'bg-slate-100', text: 'text-slate-700', icon: 'receipt-outline' },
};

export default function OrdersList() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [fetchError, setFetchError] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const isFetchingRef = useRef(false);

  const fetchOrders = useCallback(async (pageNum: number, replace: boolean) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    setFetchError(false);
    try {
      const res = await api.get('/orders', { params: { page: pageNum, limit: PAGE_SIZE } });
      const data = res.data;
      // Backend returns { orders, total, hasMore } when paginated.
      // Guard against undefined/null payloads to avoid runtime crashes.
      const payload = data && typeof data === 'object' ? data : null;
      const list: Order[] = Array.isArray(payload)
        ? payload
        : Array.isArray((payload as any)?.orders)
          ? (payload as any).orders
          : [];
      const more: boolean = Boolean((payload as any)?.hasMore);
      setOrders((prev) => (replace ? list : [...prev, ...list]));
      setHasMore(more);
      setPage(pageNum);
    } catch {
      setFetchError(true);
      if (replace) setOrders([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
      isFetchingRef.current = false;
    }
  }, []);

  useEffect(() => {
    fetchOrders(1, true);
  }, [fetchOrders]);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    fetchOrders(1, true);
  }, [fetchOrders]);

  const handleLoadMore = useCallback(() => {
    if (!hasMore || loadingMore || loading || isFetchingRef.current) return;
    setLoadingMore(true);
    fetchOrders(page + 1, false);
  }, [hasMore, loadingMore, loading, page, fetchOrders]);

  const handleRetry = useCallback(() => {
    setLoading(true);
    setOrders([]);
    fetchOrders(1, true);
  }, [fetchOrders]);

  const getStatusStyle = (status: string) => {
    const key = status?.toLowerCase() || 'default';
    return statusColors[key] || statusColors.default;
  };

  const renderItem = ({ item }: { item: Order }) => {
    const style = getStatusStyle(item.status || '');
    return (
      <TouchableOpacity
        className="mb-3 overflow-hidden rounded-2xl bg-white"
        style={shadows.md}
        onPress={() => router.push({ pathname: '/orders/[id]', params: { id: item._id } })}
      >
        <View className="p-4">
          <View className="mb-3 flex-row items-center justify-between">
            <Text className="font-bold text-slate-800">
              Order #{item._id?.slice(-6).toUpperCase() || '—'}
            </Text>
            <View className={`flex-row items-center rounded-full px-3 py-1 ${style.bg}`}>
              <Ionicons name={style.icon as any} size={14} color={colors.textPrimary} />
              <Text className={`ml-1 text-xs font-semibold capitalize ${style.text}`}>
                {item.status || 'Unknown'}
              </Text>
            </View>
          </View>

          <View className="flex-row items-center justify-between">
            <View>
              <Text className="text-xs text-slate-500">Payment</Text>
              <Text className="font-medium capitalize text-slate-700">
                {item.paymentMethod || '—'}
              </Text>
            </View>
            <View className="items-end">
              <Text className="text-xs text-slate-500">Total</Text>
              <Text className="text-lg font-bold text-purple-600">₹{item.total || 0}</Text>
            </View>
          </View>
        </View>

        <View className="flex-row items-center justify-between bg-slate-50 px-4 py-2">
          <Text className="text-xs text-slate-400">
            {item.createdAt ? formatDateIST(item.createdAt) : '—'}
          </Text>
          <View className="flex-row items-center">
            <Text className="mr-1 text-xs font-medium text-indigo-600">View Details</Text>
            <Ionicons name="chevron-forward" size={14} color={colors.primary} />
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View className="py-4 items-center">
        <ActivityIndicator size="small" color={colors.primary} />
      </View>
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-slate-50">

      {/* Header */}
      <View
        className="flex-row items-center border-b border-slate-100 bg-white px-4 py-4"
        style={shadows.sm}
      >
        <TouchableOpacity
          className="mr-3 h-10 w-10 items-center justify-center rounded-xl bg-slate-100"
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={20} color={colors.textPrimary} />
        </TouchableOpacity>
        <Ionicons name="receipt" size={24} color={colors.primary} />
        <Text className="ml-3 text-xl font-bold text-slate-800">My Orders</Text>
      </View>

      {loading ? (
        <OrdersListSkeleton />
      ) : fetchError ? (
        <View className="flex-1 items-center justify-center px-8">
          <View className="mb-6 h-24 w-24 items-center justify-center rounded-full bg-neutral-100">
            <Ionicons name="cloud-offline-outline" size={48} color={colors.textSecondary} />
          </View>
          <Text className="text-center text-lg font-bold text-slate-800">Could not load orders</Text>
          <Text className="mb-6 mt-2 text-center text-slate-500">
            Please check your connection and try again.
          </Text>
          <TouchableOpacity className="rounded-xl bg-neutral-900 px-6 py-3" onPress={handleRetry}>
            <Text className="font-semibold text-white">Retry</Text>
          </TouchableOpacity>
        </View>
      ) : orders.length === 0 ? (
        <View className="flex-1 items-center justify-center px-8">
          <View className="mb-6 h-24 w-24 items-center justify-center rounded-full bg-neutral-100">
            <Ionicons name="receipt-outline" size={48} color={colors.textSecondary} />
          </View>
          <Text className="text-center text-lg font-bold text-slate-800">No orders yet</Text>
          <Text className="mb-6 mt-2 text-center text-slate-500">
            Your order history will appear here once you make a purchase.
          </Text>
          <TouchableOpacity
            className="rounded-xl bg-neutral-900 px-6 py-3"
            onPress={() => router.push('/products')}
          >
            <Text className="font-semibold text-white">Start Shopping</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={orders}
          keyExtractor={(item, idx) => item._id || String(idx)}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16 }}
          showsVerticalScrollIndicator={false}
          onEndReached={handleLoadMore}
          onEndReachedThreshold={0.3}
          ListFooterComponent={renderFooter}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={colors.primary}
              colors={[colors.primary]}
            />
          }
        />
      )}
    </SafeAreaView>
  );
}
