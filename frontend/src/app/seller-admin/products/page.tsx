'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { useAuth } from '@/context/AuthContext';
import { logger } from '@/utils/logger';

interface Product {
  _id: string;
  name: string;
  sku?: string;
  category?: string;
  stock?: number;
  mrp?: number;
  isActive?: boolean;
  sellers?: SellerEntry[];
}

interface SellerEntry {
  sellerId: string;
  stock: number;
  isActive: boolean;
  requestStatus: string;
  notes?: string;
}

function RequestModal({
  product,
  onClose,
  onSuccess,
}: {
  product: Product;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [stock, setStock] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await api.post(`/products/${product._id}/seller-requests`, {
        stock: stock ? parseInt(stock) : undefined,
        notes: notes || undefined,
      });
      toast.success('Request submitted! Admin will review it.');
      onSuccess();
      onClose();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to submit request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div style={{ background: '#fff', borderRadius: 16, width: '100%', maxWidth: 440, padding: 28, boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
        <h2 style={{ margin: '0 0 4px', fontSize: 18, fontWeight: 700 }}>Request to Sell</h2>
        <p style={{ margin: '0 0 20px', fontSize: 13, color: '#6b7280' }}>{product.name}</p>
        <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 6 }}>Stock Quantity (optional)</label>
        <input
          type="number"
          placeholder="How many units do you have?"
          value={stock}
          onChange={e => setStock(e.target.value)}
          style={{ width: '100%', padding: '9px 14px', borderRadius: 9, border: '1px solid #e5e7eb', fontSize: 14, marginBottom: 16, boxSizing: 'border-box' }}
        />
        <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 6 }}>Note to Admin (optional)</label>
        <textarea
          placeholder="Any notes for the admin…"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          rows={3}
          style={{ width: '100%', padding: '9px 14px', borderRadius: 9, border: '1px solid #e5e7eb', fontSize: 14, resize: 'vertical', boxSizing: 'border-box', marginBottom: 20 }}
        />
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '9px 18px', borderRadius: 9, border: '1px solid #e5e7eb', background: '#fff', fontSize: 14, cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            style={{ padding: '9px 20px', borderRadius: 9, border: 'none', background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Submitting…' : 'Submit Request'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SellerProductsPage() {
  const [activeTab, setActiveTab] = useState<'mine' | 'all'>('mine');
  const [myProducts, setMyProducts] = useState<Product[]>([]);
  const [myLoading, setMyLoading] = useState(true);
  const [editingStock, setEditingStock] = useState<{ id: string; value: string } | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [allLoading, setAllLoading] = useState(false);
  const [allSearch, setAllSearch] = useState('');
  const [requestModal, setRequestModal] = useState<Product | null>(null);
  const [mySearch, setMySearch] = useState('');
  const { user } = useAuth();
  const myId = user?._id || '';

  useEffect(() => {
    fetchMyProducts();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeTab === 'all' && allProducts.length === 0) fetchAllProducts();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const fetchMyProducts = useCallback(async () => {
    setMyLoading(true);
    try {
      const res = await api.get('/products?limit=200');
      const all: Product[] = res.data?.products || res.data || [];
      setMyProducts(all.filter(p =>
        (p.sellers || []).some((s: SellerEntry) => s.requestStatus === 'approved')
      ));
    } catch (e) {
      logger.error(e);
    } finally {
      setMyLoading(false);
    }
  }, []);

  const fetchAllProducts = async () => {
    setAllLoading(true);
    try {
      const res = await api.get('/products?limit=200');
      setAllProducts(res.data?.products || res.data || []);
    } catch (e) {
      logger.error(e);
    } finally {
      setAllLoading(false);
    }
  };

  const getMyEntry = (product: Product): SellerEntry | undefined =>
    (product.sellers || []).find((s: SellerEntry) => s.sellerId === myId);

  const getRequestStatus = (product: Product): string | null => {
    const entry = getMyEntry(product);
    return entry?.requestStatus || null;
  };

  const handleToggleMyActive = async (product: Product) => {
    const entry = getMyEntry(product);
    if (!entry) return;
    setTogglingId(product._id);
    try {
      await api.put(`/products/${product._id}/sellers/me`, { isActive: !entry.isActive });
      toast.success(`Product ${!entry.isActive ? 'activated' : 'deactivated'} for your store`);
      fetchMyProducts();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to update');
    } finally {
      setTogglingId(null);
    }
  };

  const handleSaveStock = async (productId: string) => {
    if (!editingStock || editingStock.id !== productId) return;
    try {
      await api.put(`/products/${productId}/sellers/me`, { stock: parseInt(editingStock.value) || 0 });
      toast.success('Stock updated');
      fetchMyProducts();
      setEditingStock(null);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to update stock');
    }
  };

  const filteredMy = myProducts.filter(p =>
    !mySearch ||
    p.name?.toLowerCase().includes(mySearch.toLowerCase()) ||
    p.sku?.toLowerCase().includes(mySearch.toLowerCase())
  );

  const filteredAll = allProducts.filter(p =>
    !allSearch ||
    p.name?.toLowerCase().includes(allSearch.toLowerCase()) ||
    p.sku?.toLowerCase().includes(allSearch.toLowerCase()) ||
    p.category?.toLowerCase().includes(allSearch.toLowerCase())
  );

  const tabStyle = (tab: 'mine' | 'all') => ({
    padding: '10px 24px',
    borderRadius: '10px 10px 0 0',
    border: 'none',
    cursor: 'pointer',
    fontWeight: 700,
    fontSize: 14,
    background: activeTab === tab ? '#fff' : 'transparent',
    color: activeTab === tab ? '#6366f1' : '#6b7280',
    borderBottom: activeTab === tab ? '2px solid #6366f1' : '2px solid transparent',
    transition: 'all 0.15s',
  } as React.CSSProperties);

  return (
    <div style={{ padding: '28px 24px' }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#111827', margin: 0 }}>Products</h1>
        <p style={{ color: '#6b7280', fontSize: 14, marginTop: 4 }}>Manage your product catalog</p>
      </div>

      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #e5e7eb', marginBottom: 0 }}>
        <button style={tabStyle('mine')} onClick={() => setActiveTab('mine')}>My Products</button>
        <button style={tabStyle('all')} onClick={() => setActiveTab('all')}>All Products</button>
      </div>

      {activeTab === 'mine' && (
        <div style={{ background: '#fff', borderRadius: '0 12px 12px 12px', boxShadow: '0 1px 4px rgba(0,0,0,0.07)', padding: 20 }}>
          <div style={{ marginBottom: 16 }}>
            <input type="text" placeholder="Search my products…" value={mySearch} onChange={e => setMySearch(e.target.value)}
              style={{ padding: '9px 14px', borderRadius: 9, border: '1px solid #e5e7eb', fontSize: 14, width: '100%', maxWidth: 360, boxSizing: 'border-box' }} />
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['Product', 'SKU', 'Category', 'My Stock', 'MRP', 'Status', 'Actions'].map(h => (
                    <th key={h} style={{ padding: '11px 14px', textAlign: 'left', fontWeight: 600, color: '#374151', borderBottom: '1px solid #f0f0f0', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {myLoading ? (
                  <tr><td colSpan={7} style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>Loading…</td></tr>
                ) : filteredMy.length === 0 ? (
                  <tr><td colSpan={7} style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>No products yet. Go to the &apos;All Products&apos; tab to request products.</td></tr>
                ) : filteredMy.map(p => {
                  const entry = getMyEntry(p);
                  return (
                    <tr key={p._id} style={{ borderBottom: '1px solid #f9fafb' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 600, color: '#111827', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</td>
                      <td style={{ padding: '12px 14px', color: '#6b7280', fontFamily: 'monospace' }}>{p.sku || '—'}</td>
                      <td style={{ padding: '12px 14px', color: '#374151' }}>{p.category || '—'}</td>
                      <td style={{ padding: '12px 14px' }}>
                        {editingStock?.id === p._id ? (
                          <div style={{ display: 'flex', gap: 6 }}>
                            <input type="number" value={editingStock.value} onChange={e => setEditingStock({ id: p._id, value: e.target.value })}
                              style={{ width: 70, padding: '4px 8px', borderRadius: 7, border: '1px solid #e5e7eb', fontSize: 13 }} />
                            <button onClick={() => handleSaveStock(p._id)} style={{ padding: '4px 10px', borderRadius: 7, border: 'none', background: '#dcfce7', color: '#15803d', fontWeight: 600, fontSize: 12, cursor: 'pointer' }}>Save</button>
                            <button onClick={() => setEditingStock(null)} style={{ padding: '4px 8px', borderRadius: 7, border: 'none', background: '#f9fafb', color: '#6b7280', fontSize: 12, cursor: 'pointer' }}>✕</button>
                          </div>
                        ) : (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontWeight: 600, color: (entry?.stock ?? 0) < 5 ? '#ef4444' : '#111827' }}>{entry?.stock ?? p.stock ?? 0}</span>
                            <button onClick={() => setEditingStock({ id: p._id, value: String(entry?.stock ?? 0) })} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 6, border: '1px solid #e5e7eb', background: '#fff', cursor: 'pointer', color: '#6b7280' }}>Edit</button>
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '12px 14px' }}>₹{Number(p.mrp || 0).toFixed(2)}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600, background: entry?.isActive ? '#dcfce7' : '#fee2e2', color: entry?.isActive ? '#15803d' : '#b91c1c' }}>
                          {entry?.isActive ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <button onClick={() => handleToggleMyActive(p)} disabled={togglingId === p._id}
                          style={{ padding: '5px 12px', borderRadius: 7, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600, background: entry?.isActive ? '#fef2f2' : '#f0fdf4', color: entry?.isActive ? '#dc2626' : '#16a34a', opacity: togglingId === p._id ? 0.5 : 1 }}>
                          {entry?.isActive ? 'Mark Inactive' : 'Mark Active'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'all' && (
        <div style={{ background: '#fff', borderRadius: '0 12px 12px 12px', boxShadow: '0 1px 4px rgba(0,0,0,0.07)', padding: 20 }}>
          <div style={{ marginBottom: 16 }}>
            <input type="text" placeholder="Search all products…" value={allSearch} onChange={e => setAllSearch(e.target.value)}
              style={{ padding: '9px 14px', borderRadius: 9, border: '1px solid #e5e7eb', fontSize: 14, width: '100%', maxWidth: 360, boxSizing: 'border-box' }} />
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['Product', 'SKU', 'Category', 'MRP', 'Action'].map(h => (
                    <th key={h} style={{ padding: '11px 14px', textAlign: 'left', fontWeight: 600, color: '#374151', borderBottom: '1px solid #f0f0f0', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allLoading ? (
                  <tr><td colSpan={5} style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>Loading…</td></tr>
                ) : filteredAll.length === 0 ? (
                  <tr><td colSpan={5} style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>No products found</td></tr>
                ) : filteredAll.map(p => {
                  const status = getRequestStatus(p);
                  return (
                    <tr key={p._id} style={{ borderBottom: '1px solid #f9fafb' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 600, color: '#111827', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</td>
                      <td style={{ padding: '12px 14px', color: '#6b7280', fontFamily: 'monospace' }}>{p.sku || '—'}</td>
                      <td style={{ padding: '12px 14px', color: '#374151' }}>{p.category || '—'}</td>
                      <td style={{ padding: '12px 14px' }}>₹{Number(p.mrp || 0).toFixed(2)}</td>
                      <td style={{ padding: '12px 14px' }}>
                        {status === 'approved' && <span style={{ padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: '#dcfce7', color: '#15803d' }}>✓ Your product</span>}
                        {status === 'pending' && <span style={{ padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: '#fef9c3', color: '#a16207' }}>⏳ Pending approval</span>}
                        {status === 'rejected' && <button onClick={() => setRequestModal(p)} style={{ padding: '5px 14px', borderRadius: 20, border: 'none', fontSize: 12, fontWeight: 700, background: '#fee2e2', color: '#b91c1c', cursor: 'pointer' }}>↺ Re-request</button>}
                        {!status && <button onClick={() => setRequestModal(p)} style={{ padding: '5px 14px', borderRadius: 20, border: 'none', background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>+ Request to Sell</button>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {requestModal && (
        <RequestModal
          product={requestModal}
          onClose={() => setRequestModal(null)}
          onSuccess={() => { fetchAllProducts(); fetchMyProducts(); }}
        />
      )}
    </div>
  );
}
