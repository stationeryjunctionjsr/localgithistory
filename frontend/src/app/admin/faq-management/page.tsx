'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQSection {
  _id?: string;
  title: string;
  icon: string;
  displayOrder: number;
  items: FAQItem[];
}

const ICON_OPTIONS = [
  { value: 'cube-outline', label: 'Orders & Delivery' },
  { value: 'card-outline', label: 'Payments' },
  { value: 'person-outline', label: 'Account' },
  { value: 'business-outline', label: 'Business' },
  { value: 'swap-horizontal-outline', label: 'Returns' },
  { value: 'help-circle-outline', label: 'General Help' },
  { value: 'shield-checkmark-outline', label: 'Security' },
  { value: 'pricetags-outline', label: 'Pricing' },
  { value: 'gift-outline', label: 'Offers' },
  { value: 'call-outline', label: 'Contact' },
];

export default function FAQManagement() {
  const { user } = useAuth();
  const [sections, setSections] = useState<FAQSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSection, setEditingSection] = useState<FAQSection | null>(null);
  const [formData, setFormData] = useState<Omit<FAQSection, '_id'>>({
    title: '',
    icon: 'help-circle-outline',
    displayOrder: 0,
    items: [],
  });

  useEffect(() => {
    if (user?.role === 'super_admin') fetchSections();
  }, [user]);

  const fetchSections = async () => {
    try {
      const res = await api.get('/content/faq');
      setSections(res.data || []);
    } catch {
      toast.error('Failed to fetch FAQ sections');
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => {
    setEditingSection(null);
    setFormData({ title: '', icon: 'help-circle-outline', displayOrder: sections.length, items: [] });
    setShowModal(true);
  };

  const openEdit = (section: FAQSection) => {
    setEditingSection(section);
    setFormData({
      title: section.title,
      icon: section.icon,
      displayOrder: section.displayOrder,
      items: [...section.items],
    });
    setShowModal(true);
  };

  const addItem = () => {
    setFormData((p) => ({ ...p, items: [...p.items, { question: '', answer: '' }] }));
  };

  const removeItem = (idx: number) => {
    setFormData((p) => ({ ...p, items: p.items.filter((_, i) => i !== idx) }));
  };

  const updateItem = (idx: number, field: 'question' | 'answer', value: string) => {
    setFormData((p) => ({
      ...p,
      items: p.items.map((item, i) => (i === idx ? { ...item, [field]: value } : item)),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      toast.error('Section title is required');
      return;
    }
    const validItems = formData.items.filter((i) => i.question.trim() && i.answer.trim());
    const payload = { ...formData, items: validItems };
    try {
      if (editingSection?._id) {
        await api.put(`/content/faq/${editingSection._id}`, payload);
        toast.success('Section updated');
      } else {
        await api.post('/content/faq', payload);
        toast.success('Section created');
      }
      setShowModal(false);
      fetchSections();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this FAQ section and all its questions?')) return;
    try {
      await api.delete(`/content/faq/${id}`);
      toast.success('Section deleted');
      fetchSections();
    } catch {
      toast.error('Failed to delete section');
    }
  };

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;
  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="rounded-lg bg-white p-6 shadow-md">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="inline-flex items-center gap-3 text-2xl font-bold">
          FAQ Management <RefreshButton onRefresh={fetchSections} />
        </h2>
        <div className="flex gap-2">
          <button
            onClick={openCreate}
            className="rounded px-4 py-2 text-white"
            style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
          >
            Add Section
          </button>
        </div>
      </div>

      {sections.length === 0 ? (
        <p className="py-12 text-center text-gray-500">
          No FAQ sections yet. Click &quot;Add Section&quot; to get started.
        </p>
      ) : (
        <div className="space-y-4">
          {sections.map((section) => (
            <div key={section._id} className="rounded-xl border border-gray-200 p-5">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">{section.title}</h3>
                  <p className="text-sm text-gray-500">
                    {section.items.length} question{section.items.length !== 1 ? 's' : ''} &middot; Order: {section.displayOrder}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => openEdit(section)} className="rounded bg-amber-400 px-3 py-1 text-sm text-white">
                    Edit
                  </button>
                  <button onClick={() => section._id && handleDelete(section._id)} className="rounded bg-red-500 px-3 py-1 text-sm text-white">
                    Delete
                  </button>
                </div>
              </div>
              {section.items.length > 0 && (
                <div className="space-y-2 border-t border-gray-100 pt-3">
                  {section.items.map((item, idx) => (
                    <div key={idx} className="rounded-lg bg-gray-50 px-4 py-2">
                      <p className="text-sm font-medium text-gray-700">Q: {item.question}</p>
                      <p className="mt-1 text-sm text-gray-500">A: {item.answer}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50 p-4" onClick={() => setShowModal(false)}>
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="mb-4 text-xl font-bold">{editingSection ? 'Edit Section' : 'Add Section'}</h3>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Section info */}
              <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <h4 className="text-sm font-bold text-slate-700">Section Details</h4>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-600">Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData((p) => ({ ...p, title: e.target.value }))}
                    className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                    placeholder="e.g. Orders & Delivery"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-600">Icon</label>
                    <select
                      value={formData.icon}
                      onChange={(e) => setFormData((p) => ({ ...p, icon: e.target.value }))}
                      className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                    >
                      {ICON_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label} ({opt.value})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-600">Display Order</label>
                    <input
                      type="number"
                      value={formData.displayOrder}
                      onChange={(e) => setFormData((p) => ({ ...p, displayOrder: parseInt(e.target.value) || 0 }))}
                      className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                    />
                  </div>
                </div>
              </div>

              {/* Q&A Items */}
              <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-slate-700">Questions & Answers</h4>
                  <button type="button" onClick={addItem} className="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600">
                    + Add Question
                  </button>
                </div>
                {formData.items.length === 0 && (
                  <p className="py-4 text-center text-sm text-gray-400">
                    No questions yet. Click &quot;Add Question&quot; above.
                  </p>
                )}
                {formData.items.map((item, idx) => (
                  <div key={idx} className="relative rounded-lg border border-gray-200 bg-white p-4">
                    <button
                      type="button"
                      onClick={() => removeItem(idx)}
                      className="absolute right-2 top-2 text-red-400 hover:text-red-600"
                      title="Remove"
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    <div className="mb-3">
                      <label className="mb-1 block text-xs font-medium text-slate-500">Question {idx + 1}</label>
                      <input
                        type="text"
                        value={item.question}
                        onChange={(e) => updateItem(idx, 'question', e.target.value)}
                        className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                        placeholder="Enter the question"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-500">Answer</label>
                      <textarea
                        value={item.answer}
                        onChange={(e) => updateItem(idx, 'answer', e.target.value)}
                        rows={3}
                        className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                        placeholder="Enter the answer"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setShowModal(false)} className="rounded bg-gray-300 px-6 py-2 text-gray-700 hover:bg-gray-400">
                  Cancel
                </button>
                <button type="submit" className="rounded px-6 py-2 text-white" style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}>
                  {editingSection ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
