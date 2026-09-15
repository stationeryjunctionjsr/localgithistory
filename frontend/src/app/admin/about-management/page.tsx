import { logger } from "@/utils/logger";
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

interface ContentSection {
  title: string;
  body: string;
}

interface AboutData {
  brandName: string;
  tagline: string;
  mission: string;
  offerings: string[];
  contactEmail: string;
  contactWebsite: string;
  sections: ContentSection[];
}

const defaultData: AboutData = {
  brandName: 'Stationery Junction',
  tagline: 'Premium Stationery at Wholesale Prices',
  mission: '',
  offerings: [],
  contactEmail: 'support@stationeryjunction.com',
  contactWebsite: 'https://www.stationeryjunction.com',
  sections: [],
};

export default function AboutManagement() {
  const { user } = useAuth();
  const [data, setData] = useState<AboutData>(defaultData);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user?.role === 'super_admin') fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const res = await api.get('/content/about');
      if (res.data && Object.keys(res.data).length > 0) {
        setData({ ...defaultData, ...res.data });
      }
    } catch (e: any) { logger.warn("Background task failed", e); } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/content/about', data);
      toast.success('About Us page saved');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const addOffering = () => setData((p) => ({ ...p, offerings: [...p.offerings, ''] }));
  const removeOffering = (idx: number) => setData((p) => ({ ...p, offerings: p.offerings.filter((_, i) => i !== idx) }));
  const updateOffering = (idx: number, value: string) =>
    setData((p) => ({ ...p, offerings: p.offerings.map((o, i) => (i === idx ? value : o)) }));

  const addSection = () => setData((p) => ({ ...p, sections: [...p.sections, { title: '', body: '' }] }));
  const removeSection = (idx: number) => setData((p) => ({ ...p, sections: p.sections.filter((_, i) => i !== idx) }));
  const updateSection = (idx: number, field: 'title' | 'body', value: string) =>
    setData((p) => ({ ...p, sections: p.sections.map((s, i) => (i === idx ? { ...s, [field]: value } : s)) }));

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;
  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="rounded-lg bg-white p-6 shadow-md">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="inline-flex items-center gap-3 text-2xl font-bold">
          About Us Page <RefreshButton onRefresh={fetchData} />
        </h2>
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded px-6 py-2 text-white disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Brand Info */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-bold text-slate-700">Brand Information</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Brand Name</label>
              <input
                type="text"
                value={data.brandName}
                onChange={(e) => setData((p) => ({ ...p, brandName: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Tagline</label>
              <input
                type="text"
                value={data.tagline}
                onChange={(e) => setData((p) => ({ ...p, tagline: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Contact Email</label>
              <input
                type="email"
                value={data.contactEmail}
                onChange={(e) => setData((p) => ({ ...p, contactEmail: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Website URL</label>
              <input
                type="url"
                value={data.contactWebsite}
                onChange={(e) => setData((p) => ({ ...p, contactWebsite: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
              />
            </div>
          </div>
        </div>

        {/* Mission */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-bold text-slate-700">Mission Statement</h3>
          <textarea
            value={data.mission}
            onChange={(e) => setData((p) => ({ ...p, mission: e.target.value }))}
            rows={4}
            className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
            placeholder="Describe your company's mission..."
          />
        </div>

        {/* Offerings */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-700">What We Offer</h3>
            <button type="button" onClick={addOffering} className="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600">
              + Add
            </button>
          </div>
          {data.offerings.length === 0 && <p className="py-4 text-center text-sm text-gray-400">No offerings added yet.</p>}
          {data.offerings.map((item, idx) => (
            <div key={idx} className="mb-2 flex items-center gap-2">
              <input
                type="text"
                value={item}
                onChange={(e) => updateOffering(idx, e.target.value)}
                className="flex-1 rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                placeholder={`Offering ${idx + 1}`}
              />
              <button type="button" onClick={() => removeOffering(idx)} className="text-red-400 hover:text-red-600">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* Custom Sections */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-700">Additional Sections</h3>
            <button type="button" onClick={addSection} className="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600">
              + Add Section
            </button>
          </div>
          {data.sections.length === 0 && <p className="py-4 text-center text-sm text-gray-400">No additional sections.</p>}
          {data.sections.map((section, idx) => (
            <div key={idx} className="relative mb-3 rounded-lg border border-gray-200 bg-white p-4">
              <button
                type="button"
                onClick={() => removeSection(idx)}
                className="absolute right-2 top-2 text-red-400 hover:text-red-600"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <div className="mb-3">
                <label className="mb-1 block text-xs font-medium text-slate-500">Section Title</label>
                <input
                  type="text"
                  value={section.title}
                  onChange={(e) => updateSection(idx, 'title', e.target.value)}
                  className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Content</label>
                <textarea
                  value={section.body}
                  onChange={(e) => updateSection(idx, 'body', e.target.value)}
                  rows={3}
                  className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
