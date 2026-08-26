import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator, Alert, Linking, StyleSheet, Switch } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Toast from 'react-native-toast-message';
import api from '../../src/api/client';
import { useAuth } from '../../src/hooks/useAuth';
import { colors } from '../../src/theme';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export default function ValetDashboard() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'All' | 'Pending' | 'Delivered'>('All');
  const [isOnDuty, setIsOnDuty] = useState((user as any)?.isOnDuty || false);

  useEffect(() => {
    if (user && 'isOnDuty' in user) {
      setIsOnDuty((user as any).isOnDuty);
    }
  }, [user]);

  const userId = (user as any)?.id || user?._id;

  // -- FETCH ASSIGNED --
  const { data: ordersData, isLoading: ordersLoading, refetch: refetchOrders, isRefetching: isRefetchingOrders } = useQuery({
    queryKey: ['valet-orders', userId],
    queryFn: async () => {
      if (!userId) return [];
      const res = await api.get(`/orders?assignedValet=${userId}&limit=100`);
      return res.data?.items || res.data || [];
    },
    enabled: !!userId,
  });

  const { data: returnsData, isLoading: returnsLoading, refetch: refetchReturns, isRefetching: isRefetchingReturns } = useQuery({
    queryKey: ['valet-returns', userId],
    queryFn: async () => {
      if (!userId) return [];
      try {
        const res = await api.get('/returns/valet/assigned');
        return res.data?.items || res.data || [];
      } catch {
        return [];
      }
    },
    enabled: !!userId,
  });

  // -- FETCH PENDING (New Assignments) --
  const { data: pendingOrdersData, refetch: refetchPendingOrders } = useQuery({
    queryKey: ['valet-pending-orders', userId],
    queryFn: async () => {
      if (!userId) return [];
      try {
        const res = await api.get('/orders', { params: { status: 'pending_valet' } });
        const list = res.data?.items || res.data || [];
        return list.filter((o: any) => o.pendingValetId === userId || o.pendingValetId?._id === userId);
      } catch {
        return [];
      }
    },
    enabled: !!userId,
  });

  const { data: pendingReturnsData, refetch: refetchPendingReturns } = useQuery({
    queryKey: ['valet-pending-returns', userId],
    queryFn: async () => {
      if (!userId) return [];
      try {
        const res = await api.get('/returns/valet/pending');
        return res.data?.items || res.data || [];
      } catch {
        return [];
      }
    },
    enabled: !!userId,
  });

  // -- MUTATIONS --
  const toggleDutyMutation = useMutation({
    mutationFn: async (dutyStatus: boolean) => {
      const res = await api.put('/users/me/duty-status', { isOnDuty: dutyStatus });
      return res.data;
    },
    onSuccess: (data) => {
      setIsOnDuty(data.isOnDuty);
      Toast.show({ type: 'success', text1: 'Duty Status Updated', text2: data.message });
    },
    onError: () => {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to update duty status' });
    }
  });

  const respondOrderMutation = useMutation({
    mutationFn: async ({ orderId, action }: { orderId: string, action: 'accept' | 'decline' }) => {
      await api.put(`/orders/${orderId}/valet-response`, { action });
    },
    onSuccess: (_, variables) => {
      Toast.show({ type: 'success', text1: 'Success', text2: `Order ${variables.action}ed!` });
      refetchPendingOrders();
      refetchOrders();
    },
    onError: () => Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to respond' })
  });

  const respondReturnMutation = useMutation({
    mutationFn: async ({ returnId, action }: { returnId: string, action: 'accept' | 'decline' }) => {
      await api.put(`/returns/${returnId}/valet-response`, { action });
    },
    onSuccess: (_, variables) => {
      Toast.show({ type: 'success', text1: 'Success', text2: `Return pickup ${variables.action}ed!` });
      refetchPendingReturns();
      refetchReturns();
    },
    onError: () => Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to respond' })
  });

  const markDeliveredMutation = useMutation({
    mutationFn: async (orderId: string) => {
      try {
        await api.put(`/orders/${orderId}/mark-delivered`);
      } catch (e: any) {
        if (e.response?.status === 404) {
          await api.patch(`/orders/${orderId}`, { status: 'delivered' });
        } else {
          throw e;
        }
      }
    },
    onSuccess: () => {
      Toast.show({ type: 'success', text1: 'Success', text2: 'Order marked as delivered' });
      refetchOrders();
    },
    onError: (error: any) => {
      Toast.show({ type: 'error', text1: 'Error', text2: error?.response?.data?.message || 'Failed to update order status' });
    }
  });

  const markCollectedMutation = useMutation({
    mutationFn: async (returnId: string) => {
      await api.put(`/returns/valet/${returnId}/collect`);
    },
    onSuccess: () => {
      Toast.show({ type: 'success', text1: 'Success', text2: 'Return marked as collected' });
      refetchReturns();
    },
    onError: (error: any) => {
      Toast.show({ type: 'error', text1: 'Error', text2: error?.response?.data?.message || 'Failed to mark return as collected' });
    }
  });

  const isLoading = ordersLoading || returnsLoading;
  const isRefetching = isRefetchingOrders || isRefetchingReturns;

  const onRefresh = () => {
    refetchOrders();
    refetchReturns();
    refetchPendingOrders();
    refetchPendingReturns();
  };

  const handleLogout = async () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', onPress: () => {
        logout();
        router.replace('/(auth)/login');
      }, style: 'destructive' }
    ]);
  };

  const openInMaps = (addressStr: string) => {
    Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(addressStr));
  };

  const orders = Array.isArray(ordersData) ? ordersData : [];
  const returns = Array.isArray(returnsData) ? returnsData : [];
  const pendingOrdersList = Array.isArray(pendingOrdersData) ? pendingOrdersData : [];
  const pendingReturnsList = Array.isArray(pendingReturnsData) ? pendingReturnsData : [];

  const pendingOrders = orders.filter((o: any) => o.status !== 'delivered' && o.status !== 'cancelled' && o.status !== 'returned');
  const deliveredOrders = orders.filter((o: any) => o.status === 'delivered');
  
  const totalAssigned = orders.length;
  const totalPending = pendingOrders.length;
  const totalToCollect = pendingOrders.reduce((sum: number, o: any) => {
    if (o.paymentMethod === 'cod' || o.paymentMethod === 'cash_on_delivery') {
      return sum + (o.totalAmount || o.total || 0);
    }
    return sum;
  }, 0);

  const filteredOrders = filter === 'All' 
    ? orders 
    : filter === 'Pending' 
      ? pendingOrders 
      : deliveredOrders;

  const formatAddress = (addr: any) => {
    if (!addr) return 'No address provided';
    if (typeof addr === 'string') return addr;
    return `${addr.street1 || addr.addressLine1 || ''} ${addr.city || ''} ${addr.state || ''} ${addr.zipCode || addr.pincode || ''}`.trim();
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={styles.headerTitle}>Delivery Dashboard</Text>
          <Text style={styles.headerSubtitle}>Hello, {user?.name || (user as any)?.firstName || 'Valet'}</Text>
        </View>
        <View style={styles.dutyContainer}>
          <Text style={styles.dutyText}>{isOnDuty ? 'On Duty' : 'Off Duty'}</Text>
          <Switch 
            value={isOnDuty} 
            onValueChange={(val) => toggleDutyMutation.mutate(val)} 
            disabled={toggleDutyMutation.isPending}
            trackColor={{ false: '#D1D5DB', true: '#A7F3D0' }}
            thumbColor={isOnDuty ? '#059669' : '#9CA3AF'}
          />
        </View>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
          <Ionicons name="log-out-outline" size={24} color="#EF4444" />
        </TouchableOpacity>
      </View>

      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={onRefresh} />}
      >
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Total Assigned</Text>
            <Text style={styles.statValue}>{totalAssigned}</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Pending</Text>
            <Text style={[styles.statValue, { color: '#D97706' }]}>{totalPending}</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>To Collect</Text>
            <Text style={[styles.statValue, { color: '#DC2626' }]}>₹{totalToCollect}</Text>
          </View>
        </View>

        {/* NEW ASSIGNMENTS SECTION */}
        {(pendingOrdersList.length > 0 || pendingReturnsList.length > 0) && (
          <View style={styles.newAssignmentsSection}>
            <Text style={[styles.sectionTitle, { color: '#B45309' }]}>New Assignments!</Text>
            
            {pendingOrdersList.map((order: any) => {
              const addrStr = formatAddress(order.shippingAddress || order.address);
              return (
                <View key={order._id || order.id} style={styles.pendingCard}>
                  <View style={styles.orderHeader}>
                    <Text style={styles.orderId}>Delivery #{order.orderNumber || order._id?.substring(0, 8)}</Text>
                    <View style={[styles.statusChip, { backgroundColor: '#FEE2E2' }]}>
                      <Text style={[styles.statusText, { color: '#B91C1C' }]}>ACTION REQUIRED</Text>
                    </View>
                  </View>
                  <View style={styles.addressRow}>
                    <Ionicons name="location-outline" size={16} color="#6B7280" />
                    <Text style={styles.addressText}>{addrStr}</Text>
                  </View>
                  <View style={styles.actionRow}>
                    <TouchableOpacity 
                      style={[styles.actionBtnRow, { backgroundColor: '#EF4444' }]} 
                      onPress={() => respondOrderMutation.mutate({ orderId: order._id || order.id, action: 'decline' })}
                    >
                      <Text style={styles.actionBtnText}>Decline</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.actionBtnRow, { backgroundColor: '#10B981' }]} 
                      onPress={() => respondOrderMutation.mutate({ orderId: order._id || order.id, action: 'accept' })}
                    >
                      <Text style={styles.actionBtnText}>Accept</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}

            {pendingReturnsList.map((ret: any) => {
              const addrStr = formatAddress(ret.pickupAddress || ret.address);
              return (
                <View key={ret._id || ret.id} style={styles.pendingCard}>
                  <View style={styles.orderHeader}>
                    <Text style={styles.orderId}>Return Pickup #{ret.returnNumber || ret._id?.substring(0, 8)}</Text>
                    <View style={[styles.statusChip, { backgroundColor: '#FEE2E2' }]}>
                      <Text style={[styles.statusText, { color: '#B91C1C' }]}>ACTION REQUIRED</Text>
                    </View>
                  </View>
                  <View style={styles.addressRow}>
                    <Ionicons name="location-outline" size={16} color="#6B7280" />
                    <Text style={styles.addressText}>{addrStr}</Text>
                  </View>
                  <View style={styles.actionRow}>
                    <TouchableOpacity 
                      style={[styles.actionBtnRow, { backgroundColor: '#EF4444' }]} 
                      onPress={() => respondReturnMutation.mutate({ returnId: ret._id || ret.id, action: 'decline' })}
                    >
                      <Text style={styles.actionBtnText}>Decline</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.actionBtnRow, { backgroundColor: '#10B981' }]} 
                      onPress={() => respondReturnMutation.mutate({ returnId: ret._id || ret.id, action: 'accept' })}
                    >
                      <Text style={styles.actionBtnText}>Accept</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
          </View>
        )}

        <View style={styles.filterRow}>
          {['All', 'Pending', 'Delivered'].map(f => (
            <TouchableOpacity 
              key={f}
              style={[styles.filterChip, filter === f && styles.filterChipActive]}
              onPress={() => setFilter(f as any)}
            >
              <Text style={[styles.filterChipText, filter === f && styles.filterChipTextActive]}>{f}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {isLoading ? (
          <ActivityIndicator size="large" color="#1a4d33" style={{ marginTop: 40 }} />
        ) : (
          <>
            {filteredOrders.length === 0 ? (
              <View style={styles.emptyState}>
                <Ionicons name="cube-outline" size={48} color="#9CA3AF" />
                <Text style={styles.emptyStateText}>No orders found.</Text>
              </View>
            ) : (
              filteredOrders.map((order: any) => {
                const isPending = order.status !== 'delivered' && order.status !== 'cancelled' && order.status !== 'returned';
                const isDelivered = order.status === 'delivered';
                const isCod = order.paymentMethod === 'cod' || order.paymentMethod === 'cash_on_delivery';
                const addrStr = formatAddress(order.shippingAddress || order.address);
                const amount = order.totalAmount || order.total || 0;
                
                return (
                  <View key={order._id || order.id} style={styles.orderCard}>
                    <View style={styles.orderHeader}>
                      <Text style={styles.orderId}>Order #{order.orderNumber || order._id?.substring(0, 8)}</Text>
                      <View style={[styles.statusChip, isDelivered ? styles.statusDelivered : isPending ? styles.statusPending : {}]}>
                        <Text style={[styles.statusText, isDelivered ? styles.statusTextDelivered : isPending ? styles.statusTextPending : {}]}>
                          {order.status?.toUpperCase() || 'UNKNOWN'}
                        </Text>
                      </View>
                    </View>

                    <Text style={styles.customerName}>{order.user?.name || order.customerName || 'Customer'}</Text>
                    
                    <View style={styles.addressRow}>
                      <Ionicons name="location-outline" size={16} color="#6B7280" />
                      <Text style={styles.addressText}>{addrStr}</Text>
                    </View>
                    
                    <TouchableOpacity onPress={() => openInMaps(addrStr)} style={styles.mapBtn}>
                      <Ionicons name="map-outline" size={14} color="#1a4d33" />
                      <Text style={styles.mapBtnText}>Open in Maps</Text>
                    </TouchableOpacity>

                    <View style={styles.itemsList}>
                      {(order.items || []).map((item: any, idx: number) => (
                        <Text key={idx} style={styles.itemText}>
                          • {item.product?.name || item.name} × {item.quantity}
                        </Text>
                      ))}
                    </View>

                    <View style={styles.amountRow}>
                      <Text style={styles.amountLabel}>Amount to Collect:</Text>
                      <Text style={[styles.amountValue, isCod && isPending ? styles.amountCod : {}]}>
                        {isCod ? `₹${amount} (COD)` : 'Prepaid'}
                      </Text>
                    </View>

                    {isPending && (
                      <TouchableOpacity 
                        style={styles.actionBtn}
                        onPress={() => markDeliveredMutation.mutate(order._id || order.id)}
                        disabled={markDeliveredMutation.isPending}
                      >
                        {markDeliveredMutation.isPending ? (
                          <ActivityIndicator size="small" color="#fff" />
                        ) : (
                          <Text style={styles.actionBtnText}>Mark as Delivered</Text>
                        )}
                      </TouchableOpacity>
                    )}
                  </View>
                );
              })
            )}

            {returns.length > 0 && filter !== 'Delivered' && (
              <View style={styles.returnsSection}>
                <Text style={styles.sectionTitle}>Assigned Returns</Text>
                {returns.map((ret: any) => {
                  const addrStr = formatAddress(ret.pickupAddress || ret.address);
                  const isCollected = ret.valetStatus === 'collected' || ret.status === 'collected'; // Assume it might have a collected status

                  return (
                    <View key={ret._id || ret.id} style={styles.orderCard}>
                      <View style={styles.orderHeader}>
                        <Text style={styles.orderId}>Return #{ret.returnNumber || ret._id?.substring(0, 8)}</Text>
                        <View style={[styles.statusChip, isCollected ? styles.statusDelivered : styles.statusPending]}>
                          <Text style={isCollected ? styles.statusTextDelivered : styles.statusTextPending}>
                            {isCollected ? 'COLLECTED' : 'PICKUP PENDING'}
                          </Text>
                        </View>
                      </View>

                      <View style={styles.addressRow}>
                        <Ionicons name="location-outline" size={16} color="#6B7280" />
                        <Text style={styles.addressText}>{addrStr}</Text>
                      </View>
                      
                      <TouchableOpacity onPress={() => openInMaps(addrStr)} style={styles.mapBtn}>
                        <Ionicons name="map-outline" size={14} color="#1a4d33" />
                        <Text style={styles.mapBtnText}>Open in Maps</Text>
                      </TouchableOpacity>

                      {!isCollected && (
                        <TouchableOpacity 
                          style={[styles.actionBtn, { marginTop: 12 }]}
                          onPress={() => markCollectedMutation.mutate(ret._id || ret.id)}
                          disabled={markCollectedMutation.isPending}
                        >
                          {markCollectedMutation.isPending ? (
                            <ActivityIndicator size="small" color="#fff" />
                          ) : (
                            <Text style={styles.actionBtnText}>Mark as Collected</Text>
                          )}
                        </TouchableOpacity>
                      )}
                    </View>
                  );
                })}
              </View>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  dutyContainer: {
    alignItems: 'center',
    marginRight: 12,
  },
  dutyText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#4B5563',
    marginBottom: 4,
  },
  logoutBtn: {
    padding: 8,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    flex: 1,
    marginHorizontal: 4,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  statLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
    textAlign: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  newAssignmentsSection: {
    backgroundColor: '#FEF3C7',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  pendingCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  actionBtnRow: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  filterRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#E5E7EB',
    marginRight: 8,
  },
  filterChipActive: {
    backgroundColor: '#1a4d33',
  },
  filterChipText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#4B5563',
  },
  filterChipTextActive: {
    color: '#fff',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6B7280',
  },
  orderCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  orderId: {
    fontSize: 14,
    fontWeight: '700',
    color: '#374151',
  },
  statusChip: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
  },
  statusPending: {
    backgroundColor: '#FEF3C7',
  },
  statusDelivered: {
    backgroundColor: '#D1FAE5',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#4B5563',
  },
  statusTextPending: {
    color: '#D97706',
  },
  statusTextDelivered: {
    color: '#059669',
  },
  customerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 6,
  },
  addressRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  addressText: {
    fontSize: 13,
    color: '#4B5563',
    marginLeft: 6,
    flex: 1,
  },
  mapBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#F0FDF4',
    alignSelf: 'flex-start',
    marginBottom: 12,
  },
  mapBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1a4d33',
    marginLeft: 4,
  },
  itemsList: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  itemText: {
    fontSize: 13,
    color: '#4B5563',
    marginBottom: 4,
  },
  amountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  amountLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  amountValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  amountCod: {
    color: '#DC2626',
  },
  actionBtn: {
    backgroundColor: '#1a4d33',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  actionBtnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
  },
  returnsSection: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
});
