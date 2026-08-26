'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { useAuth } from '@/context/AuthContext';

interface SellerProduct { _id: string; name: string; sku?: string; category?: string; }
interface Coupon {
  _id: string; typeOfDiscount: string; code?: string | null; method: string;
  discountType: string; discountValue: number; minPurchaseAmount?: number;
  minRequirementType?: string; minQuantityOfEligibleItems?: number;
  validFrom?: string; validUntil?: string; isActive: boolean;
  appliesToType?: string; appliesToValueIds?: string[];
  buyXGetYCustomerGetsQuantity?: number; buyXGetYCustomerGetsDiscountType?: string;
  buyXGetYCustomerGetsDiscountValue?: number;
  buyXGetYCustomerGetsAppliesToType?: string; buyXGetYCustomerGetsAppliesToValueIds?: string[];
  usedCount?: number; usageLimit?: number;
}

const TYPE_LABELS: Record<string, string> = {
  product_discount: 'Amount off Product',
  buy_x_get_y: 'Buy X Get Y',
  total_order_discount: 'Total Order Discount',
};

const inp = { padding: '8px 10px', borderRadius: 7, border: '1px solid #d1d5db', fontSize: 13, width: '100%', boxSizing: 'border-box' as const };
const lbl = { fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 4, display: 'block' } as const;

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 14 }}>
      <label style={lbl}>{label}</label>
      {children}
    </div>
  );
}

function ProductPicker({ label, products, selected, onChange }: {
  label: string; products: SellerProduct[];
  selected: string[]; onChange: (ids: string[]) => void;
}) {
  const [search, setSearch] = useState('');
  const filtered = products.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.sku || '').toLowerCase().includes(search.toLowerCase())
  );
  const toggle = (id: string) =>
    onChange(selected.includes(id) ? selected.filter(x => x !== id) : [...selected, id]);
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={lbl}>{label}</label>
      <input
        placeholder="Search products…"
        value={search} onChange={e => setSearch(e.target.value)}
        style={{ ...inp, marginBottom: 8 }}
      />
      <div style={{ maxHeight: 180, overflowY: 'auto', border: '1px solid #e5e7eb', borderRadius: 7 }}>
        {filtered.length === 0 ? (
          <div style={{ padding: '10px 12px', fontSize: 12, color: '#9ca3af' }}>No products found</div>
        ) : filtered.map(p => (
          <label key={p._id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 12px', cursor: 'pointer', borderBottom: '1px solid #f3f4f6', background: selected.includes(p._id) ? '#ede9fe' : '#fff' }}>
            <input type="checkbox" checked={selected.includes(p._id)} onChange={() => toggle(p._id)} />
            <span style={{ fontSize: 12, fontWeight: 500 }}>{p.name}</span>
            {p.sku && <span style={{ fontSize: 11, color: '#9ca3af', fontFamily: 'monospace' }}>{p.sku}</span>}
          </label>
        ))}
      </div>
      {selected.length > 0 && (
        <div style={{ fontSize: 11, color: '#6d28d9', marginTop: 4 }}>{selected.length} product(s) selected</div>
      )}
    </div>
  );
}

const EMPTY_FORM = {
  typeOfDiscount: 'product_discount',
  method: 'automatic',
  code: '',
  discountType: 'percentage' as 'percentage' | 'fixed',
  discountValue: '',
  minRequirementType: 'none',
  minPurchaseAmount: '',
  minQuantityOfEligibleItems: '',
  validFrom: new Date().toISOString().split('T')[0],
  validUntil: '',
  usageLimit: '',
  isActive: true,
  // Applies to (Buy X)
  appliesToType: 'all' as 'all' | 'products',
  appliesToValueIds: [] as string[],
  // BXGY Get Y
  buyXGetYCustomerGetsQuantity: '',
  buyXGetYCustomerGetsDiscountType: 'percentage',
  buyXGetYCustomerGetsDiscountValue: '',
  buyXGetYCustomerGetsAppliesToType: 'all' as 'all' | 'products',
  buyXGetYCustomerGetsAppliesToValueIds: [] as string[],
};

export default function SellerDiscountsPage() {
  useAuth();
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [sellerProducts, setSellerProducts] = useState<SellerProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);

  const set = (key: keyof typeof EMPTY_FORM, value: any) =>
    setForm(f => ({ ...f, [key]: value }));

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [couponRes, productRes] = await Promise.all([
        api.get('/coupons'),
        api.get('/products', { params: { limit: 500 } }),
      ]);
      setCoupons(couponRes.data || []);
      // Only seller's own approved products
      const allProducts: any[] = productRes.data?.products || productRes.data || [];
      setSellerProducts(allProducts.map((p: any) => ({ _id: p._id, name: p.name, sku: p.sku, category: p.category })));
    } catch { toast.error('Failed to load data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const resetForm = () => { setForm({ ...EMPTY_FORM }); setEditingId(null); };

  const openCreate = () => { resetForm(); setShowModal(true); };

  const openEdit = (c: Coupon) => {
    setForm({
      typeOfDiscount: c.typeOfDiscount || 'product_discount',
      method: 'automatic',
      code: '',
      discountType: (c.discountType as any) || 'percentage',
      discountValue: String(c.discountValue),
      minRequirementType: c.minRequirementType || 'none',
      minPurchaseAmount: String(c.minPurchaseAmount || ''),
      minQuantityOfEligibleItems: String(c.minQuantityOfEligibleItems || ''),
      validFrom: c.validFrom?.split('T')[0] || '',
      validUntil: c.validUntil?.split('T')[0] || '',
      usageLimit: String(c.usageLimit || ''),
      isActive: c.isActive,
      appliesToType: (c.appliesToType as any) || 'all',
      appliesToValueIds: c.appliesToValueIds || [],
      buyXGetYCustomerGetsQuantity: String(c.buyXGetYCustomerGetsQuantity || ''),
      buyXGetYCustomerGetsDiscountType: c.buyXGetYCustomerGetsDiscountType || 'percentage',
      buyXGetYCustomerGetsDiscountValue: String(c.buyXGetYCustomerGetsDiscountValue || ''),
      buyXGetYCustomerGetsAppliesToType: (c.buyXGetYCustomerGetsAppliesToType as any) || 'all',
      buyXGetYCustomerGetsAppliesToValueIds: c.buyXGetYCustomerGetsAppliesToValueIds || [],
    });
    setEditingId(c._id);
    setShowModal(true);
  };

  const handleSubmit = async () => {
    if (!form.discountValue) { toast.error('Discount value is required'); return; }
    if (form.discountType === 'percentage' && parseFloat(form.discountValue) > 100) {
      toast.error('Percentage discount cannot exceed 100%'); return;
    }
    if (form.typeOfDiscount === 'buy_x_get_y' && !form.buyXGetYCustomerGetsQuantity) {
      toast.error('Please specify how many Y items the customer gets'); return;
    }
    const payload: any = {
      typeOfDiscount: form.typeOfDiscount,
      method: 'automatic',
      code: undefined,
      discountType: form.discountType,
      discountValue: parseFloat(form.discountValue),
      minRequirementType: form.minRequirementType,
      minPurchaseAmount: form.minRequirementType === 'min_amount' ? (parseFloat(form.minPurchaseAmount) || 0) : 0,
      minQuantityOfEligibleItems: form.minRequirementType === 'min_quantity' ? (parseInt(form.minQuantityOfEligibleItems) || null) : null,
      validFrom: form.validFrom || undefined,
      validUntil: form.validUntil || undefined,
      usageLimit: form.usageLimit ? parseInt(form.usageLimit) : undefined,
      isActive: form.isActive,
      appliesToType: form.appliesToType,
      appliesToValueIds: form.appliesToType === 'products' ? form.appliesToValueIds : [],
      applicableRoles: ['customer'],
      ...(form.typeOfDiscount === 'buy_x_get_y' ? {
        buyXGetYCustomerGetsQuantity: parseInt(form.buyXGetYCustomerGetsQuantity) || 1,
        buyXGetYCustomerGetsDiscountType: form.buyXGetYCustomerGetsDiscountType,
        buyXGetYCustomerGetsDiscountValue: parseFloat(form.buyXGetYCustomerGetsDiscountValue) || 100,
        buyXGetYCustomerGetsAppliesToType: form.buyXGetYCustomerGetsAppliesToType,
        buyXGetYCustomerGetsAppliesToValueIds: form.buyXGetYCustomerGetsAppliesToType === 'products' ? form.buyXGetYCustomerGetsAppliesToValueIds : [],
      } : {}),
    };
    setSaving(true);
    try {
      if (editingId) {
        await api.put(`/coupons/${editingId}`, payload);
        toast.success('Discount updated');
      } else {
        await api.post('/coupons', payload);
        toast.success('Discount created');
      }
      setShowModal(false); resetForm(); fetchData();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to save discount');
    } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this discount?')) return;
    try { await api.delete(`/coupons/${id}`); toast.success('Deleted'); fetchData(); }
    catch (e: any) { toast.error(e?.response?.data?.detail || 'Failed to delete'); }
  };

  const handleToggle = async (c: Coupon) => {
    try { await api.put(`/coupons/${c._id}`, { isActive: !c.isActive }); fetchData(); }
    catch { toast.error('Failed to toggle'); }
  };

  const isBXGY = form.typeOfDiscount === 'buy_x_get_y';

  return (
    <div style={{ padding: '24px 20px', maxWidth: 1000, fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#111827', margin: 0 }}>My Discounts</h1>
          <p style={{ fontSize: 13, color: '#6b7280', margin: '4px 0 0' }}>Discounts apply only to your products and are seller-scoped.</p>
        </div>
        <button
          onClick={openCreate}
          style={{ background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 9, padding: '10px 20px', fontWeight: 700, fontSize: 14, cursor: 'pointer', flexShrink: 0 }}
        >
          + Create Discount
        </button>
      </div>

      {loading ? <p style={{ color: '#9ca3af' }}>Loading…</p> : coupons.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#9ca3af' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🏷️</div>
          <p style={{ fontSize: 16, fontWeight: 600 }}>No discounts yet</p>
          <p style={{ fontSize: 13 }}>Create a discount to offer deals on your products</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, background: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                {['Type', 'Code / Method', 'Discount', 'Min Req', 'Valid Until', 'Used', 'Status', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '11px 14px', textAlign: 'left', fontWeight: 600, color: '#374151', fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.4 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {coupons.map(c => (
                <tr key={c._id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '11px 14px', fontWeight: 600, color: '#1f2937' }}>{TYPE_LABELS[c.typeOfDiscount] || c.typeOfDiscount}</td>
                  <td style={{ padding: '11px 14px' }}>
                    {c.method === 'discount_code'
                      ? <span style={{ fontFamily: 'monospace', color: '#4f46e5', background: '#ede9fe', padding: '2px 7px', borderRadius: 6, fontSize: 12 }}>{c.code || '—'}</span>
                      : <span style={{ color: '#059669', fontSize: 12, fontWeight: 600 }}>Auto</span>
                    }
                  </td>
                  <td style={{ padding: '11px 14px', fontWeight: 600 }}>{c.discountType === 'percentage' ? `${c.discountValue}%` : `₹${c.discountValue}`}</td>
                  <td style={{ padding: '11px 14px', color: '#6b7280' }}>
                    {c.minRequirementType === 'min_amount' ? `₹${c.minPurchaseAmount}` : c.minRequirementType === 'min_quantity' ? `Qty ${c.minQuantityOfEligibleItems}` : '—'}
                  </td>
                  <td style={{ padding: '11px 14px', color: '#6b7280' }}>{c.validUntil ? c.validUntil.split('T')[0] : '—'}</td>
                  <td style={{ padding: '11px 14px' }}>{c.usedCount || 0}{c.usageLimit ? `/${c.usageLimit}` : ''}</td>
                  <td style={{ padding: '11px 14px' }}>
                    <button onClick={() => handleToggle(c)} style={{ padding: '3px 11px', borderRadius: 12, border: 'none', cursor: 'pointer', fontSize: 11, fontWeight: 700, background: c.isActive ? '#d1fae5' : '#f3f4f6', color: c.isActive ? '#065f46' : '#6b7280' }}>
                      {c.isActive ? 'Active' : 'Off'}
                    </button>
                  </td>
                  <td style={{ padding: '11px 14px' }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button onClick={() => openEdit(c)} style={{ background: '#ede9fe', color: '#6d28d9', border: 'none', borderRadius: 6, padding: '4px 11px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>Edit</button>
                      <button onClick={() => handleDelete(c._id)} style={{ background: '#fee2e2', color: '#b91c1c', border: 'none', borderRadius: 6, padding: '4px 11px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
          <div style={{ background: '#fff', borderRadius: 16, padding: 28, width: '100%', maxWidth: 600, maxHeight: '92vh', overflowY: 'auto' }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 22px' }}>{editingId ? 'Edit Discount' : 'Create Discount'}</h2>

            {/* Discount type */}
            <Field label="Discount Type">
              <select value={form.typeOfDiscount} onChange={e => set('typeOfDiscount', e.target.value)} style={inp}>
                <option value="product_discount">Amount off each Product</option>
                <option value="buy_x_get_y">Buy X Get Y</option>
              </select>
            </Field>

            {/* Method: always Automatic for sellers */}
            <div style={{ marginBottom: 14, padding: '8px 12px', background: '#f0fdf4', borderRadius: 8, border: '1px solid #bbf7d0' }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: '#15803d' }}>✓ Automatic discount — no coupon code required</span>
            </div>

            {/* Discount value (for product_discount and total_order_discount) */}
            {!isBXGY && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <Field label="Value Type">
                  <select value={form.discountType} onChange={e => set('discountType', e.target.value as any)} style={inp}>
                    <option value="percentage">Percentage (%)</option>
                    <option value="fixed">Fixed (₹)</option>
                  </select>
                </Field>
                <Field label="Discount Value">
                  <input type="number" value={form.discountValue} onChange={e => set('discountValue', e.target.value)} placeholder={form.discountType === 'percentage' ? '20' : '100'} style={inp} />
                </Field>
              </div>
            )}

            {/* Applies to — Buy X part */}
            {!isBXGY ? (
              <>
                <div style={{ borderTop: '1px solid #e5e7eb', margin: '16px 0' }} />
                <div style={{ fontSize: 12, fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>Applies To</div>
                <Field label="Applies to">
                  <select value={form.appliesToType} onChange={e => set('appliesToType', e.target.value as any)} style={inp}>
                    <option value="all">All My Products</option>
                    <option value="products">Specific Products</option>
                  </select>
                </Field>
                {form.appliesToType === 'products' && (
                  <ProductPicker
                    label="Select Products"
                    products={sellerProducts}
                    selected={form.appliesToValueIds}
                    onChange={ids => set('appliesToValueIds', ids)}
                  />
                )}
              </>
            ) : (
              <>
                {/* BXGY — Buy X section */}
                <div style={{ borderTop: '1px solid #e5e7eb', margin: '16px 0' }} />
                <div style={{ fontSize: 12, fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>Customer Buys (X)</div>

                <Field label="Minimum Quantity to Buy">
                  <input type="number" value={form.minQuantityOfEligibleItems} onChange={e => set('minQuantityOfEligibleItems', e.target.value)} placeholder="e.g. 2" style={inp} />
                </Field>
                <Field label="From Products">
                  <select value={form.appliesToType} onChange={e => set('appliesToType', e.target.value as any)} style={inp}>
                    <option value="all">Any of My Products</option>
                    <option value="products">Specific Products</option>
                  </select>
                </Field>
                {form.appliesToType === 'products' && (
                  <ProductPicker
                    label="X — Select Products Customer Must Buy"
                    products={sellerProducts}
                    selected={form.appliesToValueIds}
                    onChange={ids => set('appliesToValueIds', ids)}
                  />
                )}

                {/* BXGY — Get Y section */}
                <div style={{ borderTop: '1px solid #e5e7eb', margin: '16px 0' }} />
                <div style={{ fontSize: 12, fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>Customer Gets (Y)</div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <Field label="Quantity of Y Items">
                    <input type="number" value={form.buyXGetYCustomerGetsQuantity} onChange={e => set('buyXGetYCustomerGetsQuantity', e.target.value)} placeholder="e.g. 1" style={inp} />
                  </Field>
                  <Field label="Discount on Y">
                    <select value={form.buyXGetYCustomerGetsDiscountType} onChange={e => set('buyXGetYCustomerGetsDiscountType', e.target.value)} style={inp}>
                      <option value="percentage">Percentage off</option>
                      <option value="free">Free (100% off)</option>
                    </select>
                  </Field>
                </div>

                {form.buyXGetYCustomerGetsDiscountType === 'percentage' && (
                  <Field label="Y Discount Value (%)">
                    <input type="number" value={form.buyXGetYCustomerGetsDiscountValue} onChange={e => set('buyXGetYCustomerGetsDiscountValue', e.target.value)} placeholder="e.g. 50" style={inp} />
                  </Field>
                )}

                <Field label="Y Items From">
                  <select value={form.buyXGetYCustomerGetsAppliesToType} onChange={e => set('buyXGetYCustomerGetsAppliesToType', e.target.value as any)} style={inp}>
                    <option value="all">Any of My Products</option>
                    <option value="products">Specific Products</option>
                  </select>
                </Field>
                {form.buyXGetYCustomerGetsAppliesToType === 'products' && (
                  <ProductPicker
                    label="Y — Select Products Customer Gets Discount On"
                    products={sellerProducts}
                    selected={form.buyXGetYCustomerGetsAppliesToValueIds}
                    onChange={ids => set('buyXGetYCustomerGetsAppliesToValueIds', ids)}
                  />
                )}
              </>
            )}

            {/* Minimum requirement */}
            <div style={{ borderTop: '1px solid #e5e7eb', margin: '16px 0' }} />
            <div style={{ fontSize: 12, fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>Minimum Requirement</div>
            {!isBXGY && (
              <Field label="Requirement Type">
                <select value={form.minRequirementType} onChange={e => set('minRequirementType', e.target.value)} style={inp}>
                  <option value="none">No minimum</option>
                  <option value="min_amount">Minimum purchase amount</option>
                  <option value="min_quantity">Minimum quantity of eligible items</option>
                </select>
              </Field>
            )}
            {form.minRequirementType === 'min_amount' && (
              <Field label="Minimum Purchase Amount (₹)">
                <input type="number" value={form.minPurchaseAmount} onChange={e => set('minPurchaseAmount', e.target.value)} placeholder="0" style={inp} />
              </Field>
            )}
            {form.minRequirementType === 'min_quantity' && !isBXGY && (
              <Field label="Minimum Quantity">
                <input type="number" value={form.minQuantityOfEligibleItems} onChange={e => set('minQuantityOfEligibleItems', e.target.value)} placeholder="1" style={inp} />
              </Field>
            )}

            {/* Validity + limits */}
            <div style={{ borderTop: '1px solid #e5e7eb', margin: '16px 0' }} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <Field label="Valid From"><input type="date" value={form.validFrom} onChange={e => set('validFrom', e.target.value)} style={inp} /></Field>
              <Field label="Valid Until"><input type="date" value={form.validUntil} onChange={e => set('validUntil', e.target.value)} style={inp} /></Field>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <Field label="Usage Limit"><input type="number" value={form.usageLimit} onChange={e => set('usageLimit', e.target.value)} placeholder="Unlimited" style={inp} /></Field>
              <Field label="">
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 22, cursor: 'pointer' }}>
                  <input type="checkbox" checked={form.isActive} onChange={e => set('isActive', e.target.checked)} />
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Active</span>
                </label>
              </Field>
            </div>

            {/* Buttons */}
            <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
              <button onClick={() => { setShowModal(false); resetForm(); }} style={{ flex: 1, padding: 11, background: '#f3f4f6', border: 'none', borderRadius: 9, fontWeight: 600, cursor: 'pointer', fontSize: 14 }}>Cancel</button>
              <button onClick={handleSubmit} disabled={saving} style={{ flex: 1, padding: 11, background: saving ? '#a5b4fc' : '#4f46e5', color: '#fff', border: 'none', borderRadius: 9, fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer', fontSize: 14 }}>
                {saving ? 'Saving…' : editingId ? 'Save Changes' : 'Create Discount'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
