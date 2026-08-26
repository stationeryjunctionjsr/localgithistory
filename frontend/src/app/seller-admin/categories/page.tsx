'use client';

import { useState, useEffect } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { logger } from '@/utils/logger';

interface Category { _id: string; name: string; description?: string; isActive?: boolean; }

export default function SellerCategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });
  const [saving, setSaving] = useState(false);

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await api.get('/categories/admin');
      setCategories(res.data || []);
    } catch (e) { logger.warn("Silent catch block:", e);  } finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, []);

  const handleCreate = async () => {
    if (!form.name.trim()) { toast.error('Category name is required'); return; }
    setSaving(true);
    try {
      await api.post('/categories', form);
      toast.success('Category created');
      setForm({ name: '', description: '' });
      setShowForm(false);
      fetch();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to create category');
    } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this category?')) return;
    try {
      await api.delete(`/categories/${id}`);
      toast.success('Category deleted');
      fetch();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to delete category');
    }
  };

  return (
    <div style={{ padding: '28px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#111827', margin: 0 }}>My Categories</h1>
          <p style={{ color: '#6b7280', fontSize: 14, marginTop: 4 }}>Manage categories for your products</p>
        </div>
        <button onClick={() => setShowForm(s => !s)}
          style={{ padding: '9px 18px', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 9, cursor: 'pointer', fontWeight: 600, fontSize: 14 }}>
          {showForm ? 'Cancel' : '+ New Category'}
        </button>
      </div>

      {showForm && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
          <div style={{ display: 'grid', gap: 12 }}>
            <input placeholder="Category name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              style={{ padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: 8, fontSize: 14 }} />
            <input placeholder="Description (optional)" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              style={{ padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: 8, fontSize: 14 }} />
            <button onClick={handleCreate} disabled={saving}
              style={{ padding: '9px 18px', background: saving ? '#9ca3af' : '#4f46e5', color: '#fff', border: 'none', borderRadius: 8, cursor: saving ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: 14, alignSelf: 'start' }}>
              {saving ? 'Creating…' : 'Create Category'}
            </button>
          </div>
        </div>
      )}

      <div style={{ background: '#fff', borderRadius: 14, boxShadow: '0 1px 4px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>Loading…</div>
        ) : categories.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center', color: '#9ca3af' }}>No categories yet. Create your first one above.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#f9fafb' }}>
                {['Name', 'Description', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '11px 16px', textAlign: 'left', fontWeight: 600, color: '#374151', borderBottom: '1px solid #f0f0f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {categories.map(c => (
                <tr key={c._id} style={{ borderBottom: '1px solid #f9fafb' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#111827' }}>{c.name}</td>
                  <td style={{ padding: '12px 16px', color: '#6b7280' }}>{c.description || '—'}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <button onClick={() => handleDelete(c._id)}
                      style={{ padding: '5px 12px', background: '#fef2f2', color: '#dc2626', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
