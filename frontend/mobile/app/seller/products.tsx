import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, FlatList, ActivityIndicator, StyleSheet,
  TouchableOpacity, Alert, TextInput, Modal, ScrollView,
} from 'react-native';
import api from '../../src/api/client';
import { colors, shadows } from '../../src/theme';
import Toast from 'react-native-toast-message';

interface SellerEntry {
  sellerId: string;
  stock: number;
  isActive: boolean;
  requestStatus: string;
  notes?: string;
}

interface Product {
  _id: string;
  name: string;
  sku?: string;
  category?: string;
  mrp?: number;
  stock?: number;
  isActive?: boolean;
  sellers?: SellerEntry[];
}

export default function SellerProducts() {
  const [activeTab, setActiveTab] = useState<'mine' | 'all'>('mine');
  const [myProducts, setMyProducts] = useState<Product[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [allLoading, setAllLoading] = useState(false);
  const [myId, setMyId] = useState<string>('');

  // Stock editing state
  const [editingStock, setEditingStock] = useState<{ id: string; value: string } | null>(null);
  const [savingStock, setSavingStock] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  // Request modal
  const [requestModal, setRequestModal] = useState<Product | null>(null);
  const [reqStock, setReqStock] = useState('');
  const [reqNotes, setReqNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const res = await api.get('/users/me');
        setMyId(res.data?._id || '');
      } catch {}
      fetchMyProducts();
    };
    init();
  }, []);

  useEffect(() => {
    if (activeTab === 'all' && allProducts.length === 0) fetchAllProducts();
  }, [activeTab]);

  const fetchMyProducts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/products?limit=200');
      const all: Product[] = res.data?.products || res.data || [];
      setMyProducts(all.filter(p =>
        (p.sellers || []).some((s: SellerEntry) => s.requestStatus === 'approved')
      ));
    } catch {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to load products' });
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAllProducts = async () => {
    setAllLoading(true);
    try {
      const res = await api.get('/products?limit=200');
      setAllProducts(res.data?.products || res.data || []);
    } catch {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to load products' });
    } finally {
      setAllLoading(false);
    }
  };

  const getMyEntry = (product: Product): SellerEntry | undefined =>
    (product.sellers || []).find(s => s.sellerId === myId);

  const getRequestStatus = (product: Product): string | null =>
    getMyEntry(product)?.requestStatus || null;

  const handleSaveStock = async (productId: string) => {
    if (!editingStock || editingStock.id !== productId) return;
    setSavingStock(true);
    try {
      await api.put(`/products/${productId}/sellers/me`, { stock: parseInt(editingStock.value) || 0 });
      Toast.show({ type: 'success', text1: 'Stock Updated' });
      setEditingStock(null);
      fetchMyProducts();
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Error', text2: e?.response?.data?.detail || 'Failed to update stock' });
    } finally {
      setSavingStock(false);
    }
  };

  const handleToggleActive = async (product: Product) => {
    const entry = getMyEntry(product);
    if (!entry) return;
    const newVal = !entry.isActive;
    Alert.alert(
      newVal ? 'Activate Product?' : 'Mark Inactive?',
      `This will ${newVal ? 'show' : 'hide'} "${product.name}" for your pincodes.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          onPress: async () => {
            setTogglingId(product._id);
            try {
              await api.put(`/products/${product._id}/sellers/me`, { isActive: newVal });
              Toast.show({ type: 'success', text1: newVal ? 'Activated' : 'Deactivated' });
              fetchMyProducts();
            } catch (e: any) {
              Toast.show({ type: 'error', text1: 'Error', text2: e?.response?.data?.detail || 'Failed' });
            } finally {
              setTogglingId(null);
            }
          },
        },
      ]
    );
  };

  const handleSubmitRequest = async () => {
    if (!requestModal) return;
    setSubmitting(true);
    try {
      await api.post(`/products/${requestModal._id}/seller-requests`, {
        stock: reqStock ? parseInt(reqStock) : undefined,
        notes: reqNotes || undefined,
      });
      Toast.show({ type: 'success', text1: 'Request Submitted', text2: 'Admin will review your request' });
      setRequestModal(null);
      setReqStock(''); setReqNotes('');
      fetchAllProducts(); fetchMyProducts();
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Error', text2: e?.response?.data?.detail || 'Failed to submit' });
    } finally {
      setSubmitting(false);
    }
  };

  const updateStockInline = async (product: Product, change: number) => {
    const entry = getMyEntry(product);
    if (!entry) return;
    const newStock = Math.max(0, entry.stock + change);
    try {
      await api.put(`/products/${product._id}/sellers/me`, { stock: newStock });
      fetchMyProducts();
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Error', text2: 'Failed to update stock' });
    }
  };

  const renderMyProduct = ({ item }: { item: Product }) => {
    const entry = getMyEntry(item);
    const isEditing = editingStock?.id === item._id;
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.productName} numberOfLines={2}>{item.name}</Text>
          <View style={[styles.badge, { backgroundColor: entry?.isActive ? '#D1FAE5' : '#FEE2E2' }]}>
            <Text style={[styles.badgeText, { color: entry?.isActive ? '#065F46' : '#991B1B' }]}>
              {entry?.isActive ? 'ACTIVE' : 'INACTIVE'}
            </Text>
          </View>
        </View>

        <Text style={styles.sku}>SKU: {item.sku || 'N/A'} · MRP: ₹{item.mrp || 0}</Text>

        {/* Stock edit row */}
        <View style={styles.stockRow}>
          <Text style={styles.stockLabel}>My Stock:</Text>
          {isEditing ? (
            <View style={styles.stockEditRow}>
              <TextInput
                value={editingStock!.value}
                onChangeText={v => setEditingStock({ id: item._id, value: v })}
                keyboardType="numeric"
                style={styles.stockInput}
                autoFocus
              />
              <TouchableOpacity
                style={[styles.smallBtn, { backgroundColor: '#D1FAE5' }]}
                onPress={() => handleSaveStock(item._id)}
                disabled={savingStock}
              >
                <Text style={[styles.smallBtnText, { color: '#065F46' }]}>{savingStock ? '...' : 'Save'}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.smallBtn, { backgroundColor: '#F3F4F6' }]}
                onPress={() => setEditingStock(null)}
              >
                <Text style={[styles.smallBtnText, { color: '#6B7280' }]}>✕</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.stockStepper}>
              <TouchableOpacity 
                style={styles.stepBtn} 
                onPress={() => updateStockInline(item, -1)}
                disabled={(entry?.stock ?? 0) <= 0}
              >
                <Text style={[styles.stepText, (entry?.stock ?? 0) <= 0 && { color: '#D1D5DB' }]}>-</Text>
              </TouchableOpacity>
              
              <Text style={[styles.stockValue, { color: (entry?.stock ?? 0) < 5 ? '#EF4444' : '#111827', width: 36, textAlign: 'center' }]}>
                {entry?.stock ?? item.stock ?? 0}
              </Text>

              <TouchableOpacity style={styles.stepBtn} onPress={() => updateStockInline(item, 1)}>
                <Text style={styles.stepText}>+</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.smallBtn, { backgroundColor: '#EDE9FE', marginLeft: 12 }]}
                onPress={() => setEditingStock({ id: item._id, value: String(entry?.stock ?? 0) })}
              >
                <Text style={[styles.smallBtnText, { color: '#6D28D9' }]}>Set</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Toggle active */}
        <TouchableOpacity
          style={[styles.toggleBtn, { backgroundColor: entry?.isActive ? '#FEE2E2' : '#D1FAE5' }]}
          onPress={() => handleToggleActive(item)}
          disabled={togglingId === item._id}
        >
          <Text style={[styles.toggleBtnText, { color: entry?.isActive ? '#DC2626' : '#16A34A' }]}>
            {togglingId === item._id ? 'Updating...' : (entry?.isActive ? 'Mark Inactive' : 'Mark Active')}
          </Text>
        </TouchableOpacity>
      </View>
    );
  };

  const renderAllProduct = ({ item }: { item: Product }) => {
    const status = getRequestStatus(item);
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.productName} numberOfLines={2}>{item.name}</Text>
          {status === 'approved' && (
            <View style={[styles.badge, { backgroundColor: '#D1FAE5' }]}>
              <Text style={[styles.badgeText, { color: '#065F46' }]}>✓ Yours</Text>
            </View>
          )}
          {status === 'pending' && (
            <View style={[styles.badge, { backgroundColor: '#FEF9C3' }]}>
              <Text style={[styles.badgeText, { color: '#A16207' }]}>⏳ Pending</Text>
            </View>
          )}
          {status === 'rejected' && (
            <View style={[styles.badge, { backgroundColor: '#FEE2E2' }]}>
              <Text style={[styles.badgeText, { color: '#991B1B' }]}>Rejected</Text>
            </View>
          )}
        </View>
        <Text style={styles.sku}>{item.sku ? `SKU: ${item.sku} · ` : ''}₹{item.mrp || 0} MRP</Text>
        {(!status || status === 'rejected') && (
          <TouchableOpacity
            style={styles.requestBtn}
            onPress={() => { setRequestModal(item); setReqStock(''); setReqNotes(''); }}
          >
            <Text style={styles.requestBtnText}>
              {status === 'rejected' ? '↺ Re-request' : '+ Request to Sell'}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Tabs */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'mine' && styles.tabActive]}
          onPress={() => setActiveTab('mine')}
        >
          <Text style={[styles.tabText, activeTab === 'mine' && styles.tabTextActive]}>My Products</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'all' && styles.tabActive]}
          onPress={() => setActiveTab('all')}
        >
          <Text style={[styles.tabText, activeTab === 'all' && styles.tabTextActive]}>All Products</Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'mine' && (
        loading ? (
          <ActivityIndicator size="large" color="#4f46e5" style={{ flex: 1, marginTop: 40 }} />
        ) : (
          <FlatList
            data={myProducts}
            keyExtractor={item => item._id}
            contentContainerStyle={styles.list}
            renderItem={renderMyProduct}
            ListEmptyComponent={
              <View style={styles.empty}>
                <Text style={styles.emptyText}>No products yet.</Text>
                <Text style={styles.emptySubText}>Go to All Products to request products to sell.</Text>
              </View>
            }
          />
        )
      )}

      {activeTab === 'all' && (
        allLoading ? (
          <ActivityIndicator size="large" color="#4f46e5" style={{ flex: 1, marginTop: 40 }} />
        ) : (
          <FlatList
            data={allProducts}
            keyExtractor={item => item._id}
            contentContainerStyle={styles.list}
            renderItem={renderAllProduct}
            ListEmptyComponent={
              <View style={styles.empty}><Text style={styles.emptyText}>No products available.</Text></View>
            }
          />
        )
      )}

      {/* Request Modal */}
      <Modal visible={!!requestModal} transparent animationType="slide" onRequestClose={() => setRequestModal(null)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Request to Sell</Text>
            {requestModal && <Text style={styles.modalSubTitle}>{requestModal.name}</Text>}

            <Text style={styles.modalLabel}>Stock Quantity (optional)</Text>
            <TextInput
              placeholder="How many units do you have?"
              value={reqStock}
              onChangeText={setReqStock}
              keyboardType="numeric"
              style={styles.modalInput}
            />

            <Text style={styles.modalLabel}>Note to Admin (optional)</Text>
            <TextInput
              placeholder="Any notes..."
              value={reqNotes}
              onChangeText={setReqNotes}
              multiline
              numberOfLines={3}
              style={[styles.modalInput, { height: 80, textAlignVertical: 'top' }]}
            />

            <View style={styles.modalBtns}>
              <TouchableOpacity
                style={[styles.modalBtn, { backgroundColor: '#F3F4F6' }]}
                onPress={() => setRequestModal(null)}
              >
                <Text style={{ color: '#374151', fontWeight: '600' }}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalBtn, { backgroundColor: '#4f46e5' }]}
                onPress={handleSubmitRequest}
                disabled={submitting}
              >
                <Text style={{ color: '#fff', fontWeight: '700' }}>{submitting ? 'Submitting...' : 'Submit Request'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  tabBar: { flexDirection: 'row', backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#E5E7EB' },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  tabActive: { borderBottomWidth: 2, borderBottomColor: '#4f46e5' },
  tabText: { fontSize: 14, fontWeight: '600', color: '#6B7280' },
  tabTextActive: { color: '#4f46e5' },
  list: { padding: 16 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12,
    ...shadows.sm,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 },
  productName: { flex: 1, fontSize: 15, fontWeight: '600', color: '#111827', marginRight: 8 },
  sku: { fontSize: 12, color: '#6B7280', marginBottom: 10 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 12, flexShrink: 0 },
  badgeText: { fontSize: 10, fontWeight: '700' },
  stockRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  stockLabel: { fontSize: 13, color: '#374151', fontWeight: '600', marginRight: 8 },
  stockEditRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  stockStepper: { flexDirection: 'row', alignItems: 'center' },
  stepBtn: { backgroundColor: '#F3F4F6', width: 28, height: 28, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  stepText: { fontSize: 16, fontWeight: '700', color: '#374151' },
  stockValue: { fontSize: 14, fontWeight: '700', marginRight: 8 },
  stockInput: {
    borderWidth: 1, borderColor: '#D1D5DB', borderRadius: 7,
    paddingHorizontal: 10, paddingVertical: 5, fontSize: 14, width: 70,
  },
  smallBtn: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6 },
  smallBtnText: { fontSize: 12, fontWeight: '600' },
  toggleBtn: { borderRadius: 8, paddingVertical: 8, alignItems: 'center' },
  toggleBtnText: { fontSize: 13, fontWeight: '600' },
  requestBtn: {
    backgroundColor: '#4f46e5', borderRadius: 8, paddingVertical: 8,
    alignItems: 'center', marginTop: 8,
  },
  requestBtnText: { color: '#fff', fontSize: 13, fontWeight: '700' },
  empty: { flex: 1, alignItems: 'center', paddingTop: 60 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#374151' },
  emptySubText: { fontSize: 13, color: '#9CA3AF', marginTop: 8, textAlign: 'center' },
  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.45)', justifyContent: 'flex-end' },
  modalCard: {
    backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20,
    padding: 24, paddingBottom: 36,
  },
  modalTitle: { fontSize: 18, fontWeight: '700', color: '#111827', marginBottom: 2 },
  modalSubTitle: { fontSize: 13, color: '#6B7280', marginBottom: 20 },
  modalLabel: { fontSize: 13, fontWeight: '600', color: '#374151', marginBottom: 6 },
  modalInput: {
    borderWidth: 1, borderColor: '#D1D5DB', borderRadius: 9,
    paddingHorizontal: 12, paddingVertical: 9, fontSize: 14, marginBottom: 16,
  },
  modalBtns: { flexDirection: 'row', gap: 10 },
  modalBtn: { flex: 1, paddingVertical: 12, borderRadius: 9, alignItems: 'center' },
});
