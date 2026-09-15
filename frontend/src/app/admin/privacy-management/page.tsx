import { logger } from "@/utils/logger";
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

interface PolicySection {
  title: string;
  body: string;
}

interface PrivacyData {
  lastUpdated: string;
  sections: PolicySection[];
}

const defaultData: PrivacyData = {
  lastUpdated: new Date().toISOString().split('T')[0],
  sections: [],
};

export default function PrivacyManagement() {
  const { user } = useAuth();
  const [data, setData] = useState<PrivacyData>(defaultData);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user?.role === 'super_admin') fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const res = await api.get('/content/privacy');
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
      await api.put('/content/privacy', data);
      toast.success('Privacy Policy saved');
    } catch (_err: any) {
      toast.error(_err.response?.data?.detail || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const addSection = () => setData((p) => ({ ...p, sections: [...p.sections, { title: '', body: '' }] }));
  const removeSection = (idx: number) => setData((p) => ({ ...p, sections: p.sections.filter((_, i) => i !== idx) }));
  const updateSection = (idx: number, field: 'title' | 'body', value: string) =>
    setData((p) => ({ ...p, sections: p.sections.map((s, i) => (i === idx ? { ...s, [field]: value } : s)) }));

  const moveSection = (idx: number, direction: 'up' | 'down') => {
    const newIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (newIdx < 0 || newIdx >= data.sections.length) return;
    setData((p) => {
      const arr = [...p.sections];
      [arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]];
      return { ...p, sections: arr };
    });
  };

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;
  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="rounded-lg bg-white p-6 shadow-md">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="inline-flex items-center gap-3 text-2xl font-bold">
          Privacy Policy <RefreshButton onRefresh={fetchData} />
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
        {/* Meta */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-bold text-slate-700">Policy Information</h3>
          <div className="max-w-xs">
            <label className="mb-1 block text-sm font-medium text-slate-600">Last Updated</label>
            <input
              type="text"
              value={data.lastUpdated}
              onChange={(e) => setData((p) => ({ ...p, lastUpdated: e.target.value }))}
              className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
              placeholder="e.g. April 2026"
            />
          </div>
        </div>

        {/* Sections */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-700">Policy Sections ({data.sections.length})</h3>
            <button type="button" onClick={addSection} className="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600">
              + Add Section
            </button>
          </div>
          {data.sections.length === 0 && (
            <p className="py-8 text-center text-sm text-gray-400">
              No sections yet. Click &quot;Add Section&quot; to start building your privacy policy.
            </p>
          )}
          {data.sections.map((section, idx) => (
            <div key={idx} className="relative mb-4 rounded-lg border border-gray-200 bg-white p-5">
              <div className="absolute right-2 top-2 flex gap-1">
                <button
                  type="button"
                  onClick={() => moveSection(idx, 'up')}
                  disabled={idx === 0}
                  className="rounded p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                  title="Move up"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={() => moveSection(idx, 'down')}
                  disabled={idx === data.sections.length - 1}
                  className="rounded p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                  title="Move down"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={() => removeSection(idx)}
                  className="rounded p-1 text-red-400 hover:text-red-600"
                  title="Remove"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="mb-3">
                <label className="mb-1 block text-xs font-medium text-slate-500">Section {idx + 1} Title</label>
                <input
                  type="text"
                  value={section.title}
                  onChange={(e) => updateSection(idx, 'title', e.target.value)}
                  className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                  placeholder="e.g. Information We Collect"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Content (supports line breaks)</label>
                <textarea
                  value={section.body}
                  onChange={(e) => updateSection(idx, 'body', e.target.value)}
                  rows={5}
                  className="w-full rounded border px-3 py-2 text-sm focus:ring-1 focus:ring-green-500"
                  placeholder="Write the section content here. Use new lines for bullet points starting with • or -"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
