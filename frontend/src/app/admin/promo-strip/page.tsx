'use client';

import React, { useState, useEffect } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';

interface PromoStrip {
  _id: string;
  text: string;
  isActive: boolean;
  createdAt: string;
}

export default function PromoStripManagement() {
  const [strips, setStrips] = useState<PromoStrip[]>([]);
  const [loading, setLoading] = useState(true);
  const [newText, setNewText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  useEffect(() => {
    fetchStrips();
  }, []);

  const fetchStrips = async () => {
    try {
      const response = await api.get('/promo-strips/');
      setStrips(response.data);
    } catch (error) {
      console.error('Error fetching promo strips:', error);
      toast.error('Failed to fetch promo strips');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newText.trim()) return;

    setIsSubmitting(true);
    try {
      if (editingId) {
        const response = await api.put(`/promo-strips/${editingId}`, { text: newText.trim() });
        setStrips(strips.map((s) => (s._id === editingId ? response.data : s)));
        setEditingId(null);
        toast.success('Promo strip updated successfully');
      } else {
        const response = await api.post('/promo-strips/', { text: newText.trim() });
        setStrips([...strips, response.data]);
        toast.success('Promo strip added successfully');
      }
      setNewText('');
    } catch (error) {
      console.error('Error saving promo strip:', error);
      toast.error('Failed to save promo strip');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (strip: PromoStrip) => {
    setEditingId(strip._id);
    setNewText(strip.text);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setNewText('');
  };

  const handleToggleStatus = async (id: string) => {
    try {
      const response = await api.patch(`/promo-strips/${id}/toggle`);
      setStrips(strips.map((s) => (s._id === id ? response.data : s)));
      toast.success('Status updated');
    } catch (error) {
      console.error('Error toggling status:', error);
      toast.error('Failed to update status');
    }
  };

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 p-6">
        <div>
          <h1 className="inline-flex items-center gap-3 text-xl font-bold text-slate-800">
            Promo Strip Management <RefreshButton onRefresh={fetchStrips} />
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage rotating messages at the top of the header.
          </p>
        </div>
      </div>

      <div className="p-6">
        <form onSubmit={handleSubmit} className="mb-8 flex gap-3">
          <input
            type="text"
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
            placeholder="Enter promotional message (e.g., Free delivery on orders above ₹499)"
            className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            disabled={isSubmitting}
          />
          <div className="flex gap-2">
            {editingId && (
              <button
                type="button"
                onClick={handleCancelEdit}
                className="rounded-lg bg-slate-200 px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-300"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={isSubmitting || !newText.trim()}
              className="min-w-[120px] rounded-lg bg-indigo-600 px-6 py-2 font-medium text-white transition-colors hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : editingId ? 'Update Message' : 'Add Message'}
            </button>
          </div>
        </form>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600"></div>
          </div>
        ) : strips.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 py-12 text-center">
            <span className="mb-4 block text-4xl">📢</span>
            <p className="text-slate-500">No promo strips found. Add your first message above.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {strips.map((strip) => (
              <div
                key={strip._id}
                className={`flex items-center justify-between rounded-xl border p-4 transition-all ${
                  strip.isActive
                    ? 'border-slate-200 bg-white'
                    : 'border-slate-200 bg-slate-50 opacity-60'
                }`}
              >
                <div className="mr-4 flex-1">
                  <p
                    className={`font-medium ${strip.isActive ? 'text-slate-800' : 'text-slate-500'}`}
                  >
                    {strip.text}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Added on {formatDateIST(strip.createdAt)}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleToggleStatus(strip._id)}
                    className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition-all ${
                      strip.isActive
                        ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                        : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                    }`}
                  >
                    {strip.isActive ? 'Disable' : 'Enable'}
                  </button>

                  <button
                    onClick={() => handleEdit(strip)}
                    className="rounded-lg bg-indigo-50 px-4 py-1.5 text-sm font-semibold text-indigo-600 transition-all hover:bg-indigo-100"
                  >
                    Edit
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
